import CryptoKit
import Foundation

/// The public input boundary: identities and bytes, with no producer-specific fields.
public struct World {
    public struct Image: Codable, Equatable, Sendable {
        public let id: String
        public let file: String
    }

    private struct Manifest: Decodable {
        let schema_version: Int
        let world_id: String
        let images: [Image]
    }

    public let id: String
    public let images: [Image]
    let directory: URL

    public init(directory: URL) throws {
        let directory = directory.resolvingSymlinksInPath().standardizedFileURL
        let manifest: Manifest
        do {
            let url = directory.appendingPathComponent("world.json")
            guard try isRegularWorldFile(url) else { throw HazyError("Invalid manifest file") }
            manifest = try JSONDecoder().decode(Manifest.self, from: Data(contentsOf: url))
        } catch {
            throw HazyError("Cannot read or decode world.json as a world manifest.")
        }
        guard !manifest.world_id.isEmpty else { throw HazyError("World ID must not be empty.") }
        let context = "World \(manifest.world_id)"
        guard manifest.schema_version == 1 else { throw HazyError("\(context): unsupported schema version.") }
        var ids = Set<String>()
        var files = Set<String>()
        for image in manifest.images {
            let hash = String(image.id.dropFirst(7))
            guard image.id.hasPrefix("sha256:"), hash.utf8.count == 64,
                  hash.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }) else {
                throw HazyError("\(context): invalid image ID \(image.id).")
            }
            guard !image.file.contains("/"), !image.file.contains("\\"), !image.file.contains("\0"),
                  (image.file as NSString).deletingPathExtension == hash else {
                throw HazyError("\(context), image \(image.id): expected a flat hash-named file.")
            }
            guard ids.insert(image.id).inserted, files.insert(image.file).inserted else {
                throw HazyError("\(context): duplicate image ID or file for \(image.id).")
            }
            do {
                let url = directory.appendingPathComponent(image.file)
                guard try isRegularWorldFile(url) else { throw HazyError("Not a regular file") }
                guard try imageIdentity(at: url) == image.id else {
                    throw HazyError("Hash differs")
                }
            } catch {
                throw HazyError("\(context), image \(image.id): missing, non-regular, unreadable or checksum-mismatched file.")
            }
        }
        guard manifest.images.map(\.file) == manifest.images.map(\.file).sorted() else {
            throw HazyError("\(context): image files must be sorted by name.")
        }
        do {
            let names = try FileManager.default.contentsOfDirectory(atPath: directory.path)
            guard Set(names) == files.union(["world.json"]) else {
                throw HazyError("Coverage differs")
            }
        } catch {
            throw HazyError("\(context): directory contents differ from the world manifest or cannot be read.")
        }
        self.directory = directory
        self.id = manifest.world_id
        self.images = manifest.images
    }

    func file(for imageID: String) throws -> URL {
        guard let image = images.first(where: { $0.id == imageID }) else {
            throw HazyError("World \(id): unknown image ID \(imageID).")
        }
        return directory.appendingPathComponent(image.file)
    }
}

private func isRegularWorldFile(_ url: URL) throws -> Bool {
    let values = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
    return values.isRegularFile == true && values.isSymbolicLink != true
}

func imageIdentity(at url: URL) throws -> String {
    let handle = try FileHandle(forReadingFrom: url)
    defer { try? handle.close() }
    var hash = SHA256()
    while let data = try handle.read(upToCount: 1024 * 1024), !data.isEmpty { hash.update(data: data) }
    return "sha256:" + hash.finalize().map { String(format: "%02x", $0) }.joined()
}

/// Compare two explicit IDs; paths remain internal and outputs cannot enter the world.
@discardableResult
public func compareWorld(_ world: World, referenceID: String, floatingID: String,
                         outputDirectory: URL) throws -> ComparisonReport {
    do {
        // The destination is new, so resolve its existing parent explicitly.
        // Resolving a nonexistent URL as a whole can leave parent symlinks intact.
        let requested = outputDirectory.standardizedFileURL
        let output = requested.deletingLastPathComponent().resolvingSymlinksInPath()
            .appendingPathComponent(requested.lastPathComponent, isDirectory: true).standardizedFileURL
        guard !output.pathComponents.starts(with: world.directory.pathComponents) else {
            throw HazyError("Output must be outside the world directory.")
        }
        return try comparePair(reference: world.file(for: referenceID), floating: world.file(for: floatingID),
                               outputDirectory: output, worldID: world.id,
                               referenceID: referenceID, floatingID: floatingID)
    } catch {
        throw HazyError("World \(world.id), reference \(referenceID), floating \(floatingID): \(error.localizedDescription)")
    }
}
