import CoreGraphics
import CryptoKit
import Foundation
import ImageIO
import UniformTypeIdentifiers
import XCTest
@testable import AppleVisionTranslationExperiment

final class WorldTests: XCTestCase {
    private var directory: URL!
    private var worldDirectory: URL!

    override func setUpWithError() throws {
        directory = FileManager.default.temporaryDirectory.appendingPathComponent("hazy-world-tests-\(UUID().uuidString)")
        worldDirectory = directory.appendingPathComponent("world")
        try FileManager.default.createDirectory(at: worldDirectory, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws { try FileManager.default.removeItem(at: directory) }

    private func image(_ data: Data, ext: String = "png") throws -> [String: String] {
        let hash = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        let file = hash + "." + ext
        try data.write(to: worldDirectory.appendingPathComponent(file))
        return ["id": "sha256:" + hash, "file": file]
    }

    private func manifest(_ images: [[String: String]], version: Int = 1, id: String = "opaque-example", extra: Bool = false) throws {
        var value: [String: Any] = ["schema_version": version, "world_id": id,
                                   "images": images.sorted { $0["file"]! < $1["file"]! }]
        if extra { value["future"] = ["ignored": true] }
        try JSONSerialization.data(withJSONObject: value).write(to: worldDirectory.appendingPathComponent("world.json"))
    }

    private func png(width: Int, height: Int) throws -> Data {
        let context = try XCTUnwrap(CGContext(data: nil, width: width, height: height, bitsPerComponent: 8,
                                              bytesPerRow: width * 4, space: CGColorSpaceCreateDeviceRGB(),
                                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue))
        context.setFillColor(gray: 0.4, alpha: 1)
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        let data = NSMutableData()
        let destination = try XCTUnwrap(CGImageDestinationCreateWithData(data, UTType.png.identifier as CFString, 1, nil))
        CGImageDestinationAddImage(destination, try XCTUnwrap(context.makeImage()), nil)
        XCTAssertTrue(CGImageDestinationFinalize(destination))
        return data as Data
    }

    func testOpaqueIdentityEmptyWorldAndAdditiveFields() throws {
        try manifest([], id: "anything-opaque", extra: true)
        let world = try World(directory: worldDirectory)
        XCTAssertEqual(world.id, "anything-opaque")
        XCTAssertTrue(world.images.isEmpty)
        var entry = try image(Data("undecodable but hash-valid".utf8))
        entry["futureImageAttribute"] = "ignored"
        try manifest([entry], extra: true)
        XCTAssertEqual(try World(directory: worldDirectory).images.count, 1)
        try manifest([entry], version: 2)
        XCTAssertThrowsError(try World(directory: worldDirectory))
        try manifest([entry], id: "")
        XCTAssertThrowsError(try World(directory: worldDirectory))
    }

    func testRejectsUnsafeDuplicateAndMisnamedEntries() throws {
        let entry = try image(Data("one".utf8))
        try manifest([entry, entry])
        XCTAssertThrowsError(try World(directory: worldDirectory))
        for file in ["../outside.png", "/outside.png", "nested/file.png", "wrong.png", "..\\outside.png"] {
            try manifest([["id": entry["id"]!, "file": file]])
            XCTAssertThrowsError(try World(directory: worldDirectory), file)
        }
        try manifest([["id": entry["id"]!.uppercased(), "file": entry["file"]!]])
        XCTAssertThrowsError(try World(directory: worldDirectory))
    }

    func testRejectsMissingChangedExtraAndSymlinkedFiles() throws {
        let bytes = Data("one".utf8)
        let entry = try image(bytes)
        try manifest([entry])
        let file = worldDirectory.appendingPathComponent(entry["file"]!)
        try Data("changed".utf8).write(to: file)
        XCTAssertThrowsError(try World(directory: worldDirectory))
        try FileManager.default.removeItem(at: file)
        XCTAssertThrowsError(try World(directory: worldDirectory))
        let outside = directory.appendingPathComponent("outside")
        try bytes.write(to: outside)
        try FileManager.default.createSymbolicLink(at: file, withDestinationURL: outside)
        XCTAssertThrowsError(try World(directory: worldDirectory))
        try FileManager.default.removeItem(at: file)
        try bytes.write(to: file)
        let extra = worldDirectory.appendingPathComponent("unlisted")
        try bytes.write(to: extra)
        XCTAssertThrowsError(try World(directory: worldDirectory))
        try FileManager.default.removeItem(at: extra)
        let manifestURL = worldDirectory.appendingPathComponent("world.json")
        let saved = directory.appendingPathComponent("saved.json")
        try FileManager.default.moveItem(at: manifestURL, to: saved)
        try FileManager.default.createSymbolicLink(at: manifestURL, withDestinationURL: saved)
        XCTAssertThrowsError(try World(directory: worldDirectory))
    }

    func testReportsWorldAndImageIDsWithoutPathsAndPreservesBytes() throws {
        let first = try image(png(width: 20, height: 16))
        let second = try image(png(width: 17, height: 16))
        try manifest([first, second])
        let world = try World(directory: worldDirectory)
        let output = directory.appendingPathComponent("result")
        let result = try compareWorld(world, referenceID: first["id"]!, floatingID: second["id"]!, outputDirectory: output)
        XCTAssertEqual(result.worldID, world.id)
        XCTAssertEqual(result.reference.id, first["id"])
        XCTAssertEqual(result.floating.id, second["id"])
        XCTAssertEqual(result.alignment.status, .notRun)
        let json = try Data(contentsOf: output.appendingPathComponent("comparison.json"))
        let saved = try JSONDecoder().decode(ComparisonReport.self, from: json)
        XCTAssertEqual(saved.worldID, world.id)
        let text = try XCTUnwrap(String(data: json, encoding: .utf8))
        XCTAssertFalse(text.contains(directory.path))
        XCTAssertFalse(text.contains("\"path\""))
        XCTAssertFalse(result.summary.contains(directory.path))
        XCTAssertEqual(try World(directory: worldDirectory).images, world.images)
    }

    func testUnknownIDsAndOutputInsideWorldDoNotCreateFiles() throws {
        let entry = try image(png(width: 20, height: 16))
        try manifest([entry])
        let world = try World(directory: worldDirectory)
        let output = directory.appendingPathComponent("result")
        XCTAssertThrowsError(try compareWorld(world, referenceID: "unknown", floatingID: entry["id"]!, outputDirectory: output))
        XCTAssertFalse(FileManager.default.fileExists(atPath: output.path))
        let alias = directory.appendingPathComponent("world-link")
        try FileManager.default.createSymbolicLink(at: alias, withDestinationURL: worldDirectory)
        for parent in [worldDirectory!, alias] {
            XCTAssertThrowsError(try compareWorld(world, referenceID: entry["id"]!, floatingID: entry["id"]!,
                                                  outputDirectory: parent.appendingPathComponent("result")))
        }
        XCTAssertEqual(try World(directory: worldDirectory).images, world.images)
    }

    func testUndecodableInputNamesIdentitiesAndWritesNothing() throws {
        let entry = try image(Data("not an image".utf8))
        try manifest([entry])
        let world = try World(directory: worldDirectory)
        let output = directory.appendingPathComponent("result")
        XCTAssertThrowsError(try compareWorld(world, referenceID: entry["id"]!, floatingID: entry["id"]!, outputDirectory: output)) { error in
            XCTAssertTrue(error.localizedDescription.contains(world.id))
            XCTAssertTrue(error.localizedDescription.contains(entry["id"]!))
            XCTAssertFalse(error.localizedDescription.contains(self.worldDirectory.path))
        }
        XCTAssertFalse(FileManager.default.fileExists(atPath: output.path))
        XCTAssertEqual(try World(directory: worldDirectory).images, world.images)
    }

    func testSuppliedWorldUsesOnlyItsManifestAndBytes() throws {
        guard let path = ProcessInfo.processInfo.environment["HAZY_WORLD"], !path.isEmpty else {
            throw XCTSkip("Set HAZY_WORLD to exercise an externally published world.")
        }
        let source = URL(fileURLWithPath: path, isDirectory: true)
        let world = try World(directory: source)
        // No assumptions about count, provenance, decodability or expected alignment.
        if let first = world.images.first, let last = world.images.last {
            let output = directory.appendingPathComponent("external-result")
            do {
                let report = try compareWorld(world, referenceID: first.id, floatingID: last.id, outputDirectory: output)
                XCTAssertEqual(report.worldID, world.id)
                XCTAssertEqual(report.reference.id, first.id)
                XCTAssertEqual(report.floating.id, last.id)
            } catch {
                XCTAssertTrue(error.localizedDescription.contains(world.id))
                XCTAssertTrue(error.localizedDescription.contains(first.id))
                XCTAssertFalse(FileManager.default.fileExists(atPath: output.path))
            }
        }
        let after = try World(directory: source)
        XCTAssertEqual(after.id, world.id)
        XCTAssertEqual(after.images, world.images)
    }
}
