import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers
import XCTest
@testable import AppleVisionTranslationExperiment

final class FixtureTests: XCTestCase {
    private struct Manifest: Decodable {
        let images: [Entry]
    }

    private struct Entry: Decodable {
        let file: String
        let family_id: String
        let scene_id: String
        let transformation: String
        let width: Int
        let height: Int
        let exif_orientation: UInt32
    }

    private struct Focus: Decodable {
        let known_shift_families: [String]
    }

    // Fixtures are repository test inputs, not resources shipped in the library or CLI.
    private let fixtures = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .appendingPathComponent("../../Fixtures").standardizedFileURL
    private var corpus: URL { fixtures.appendingPathComponent("Relationships/Derivatives") }
    private var entries: [Entry] = []
    private var directory: URL!

    override func setUpWithError() throws {
        entries = try JSONDecoder().decode(Manifest.self, from: Data(contentsOf:
            corpus.appendingPathComponent("manifest.json"))).images
        directory = FileManager.default.temporaryDirectory.appendingPathComponent("hazy-fixtures-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
    }

    override func tearDownWithError() throws {
        if let directory { try FileManager.default.removeItem(at: directory) }
    }

    func testAllFixtureInputsPrepareWithManifestDimensions() throws {
        XCTAssertEqual(entries.count, 183)
        for entry in entries {
            let image = try ImagePreparation().prepare(corpus.appendingPathComponent(entry.file))
            XCTAssertEqual(image.description.storedSize, PixelSize(width: entry.width, height: entry.height), entry.file)
            XCTAssertEqual(image.description.exifOrientation, entry.exif_orientation, entry.file)
            XCTAssertLessThanOrEqual(max(image.pixels.width, image.pixels.height), 1024, entry.file)
            if entry.family_id == "retina" && entry.transformation == "source" {
                XCTAssertEqual(image.description.storedSize, PixelSize(width: 1411, height: 1411))
                XCTAssertEqual(image.description.preparedSize, PixelSize(width: 1024, height: 1024))
            }
        }
    }

    func testMultiviewInputsKeepSceneGroupsAndApplyOrientation() throws {
        let root = fixtures.appendingPathComponent("Relationships/Multiviews")
        let images = try JSONDecoder().decode(Manifest.self, from: Data(contentsOf:
            root.appendingPathComponent("manifest.json"))).images
        XCTAssertEqual(images.count, 20)
        XCTAssertEqual(Set(images.map(\.family_id)).count, 20, "Each capture is its own source family.")
        let groups = Dictionary(grouping: images, by: \.scene_id)
        XCTAssertEqual(groups.values.map(\.count).sorted(), [2, 2, 2, 2, 3, 3, 3, 3])
        XCTAssertFalse(groups.keys.contains(""))
        XCTAssertEqual(images.filter { $0.exif_orientation == 6 }.count, 3)
        let expectedSizes = [
            "middlebury2014-motorcycle": PixelSize(width: 741, height: 500),
            "personal-playground-rail": PixelSize(width: 768, height: 1024),
            "personal-water-feature": PixelSize(width: 1024, height: 768),
            "personal-tent-table": PixelSize(width: 1024, height: 768),
            "kumbh-mauni-amavasya": PixelSize(width: 1024, height: 681),
            "budapest-pride-1424": PixelSize(width: 1024, height: 576),
            "budapest-pride-1428": PixelSize(width: 1024, height: 576),
            "budapest-pride-1435": PixelSize(width: 576, height: 1024),
        ]
        for entry in images {
            let url = root.appendingPathComponent(entry.file)
            let original = try Data(contentsOf: url)
            let prepared = try ImagePreparation().prepare(url)
            XCTAssertEqual(prepared.description.storedSize, PixelSize(width: entry.width, height: entry.height), entry.file)
            XCTAssertEqual(prepared.description.exifOrientation, entry.exif_orientation, entry.file)
            let expected = try XCTUnwrap(expectedSizes[entry.scene_id], entry.scene_id)
            XCTAssertEqual(prepared.description.preparedSize, expected, entry.file)
            XCTAssertEqual(try Data(contentsOf: url), original, entry.file)
        }
        // Same-scene labels deliberately carry no expected numerical Vision result.
    }

    func testAllByteCopiesAlignAtZeroAndPreserveInputs() throws {
        let originals = entries.filter { $0.transformation == "source" }
        XCTAssertEqual(originals.count, 12)
        for original in originals {
            let reference = corpus.appendingPathComponent(original.file)
            let floating = try url(family: original.family_id, variant: "byte_copy")
            let referenceBytes = try Data(contentsOf: reference)
            let floatingBytes = try Data(contentsOf: floating)
            XCTAssertEqual(referenceBytes, floatingBytes, original.family_id)
            let report = try comparePair(reference: reference, floating: floating,
                                         outputDirectory: directory.appendingPathComponent(original.family_id))
            XCTAssertEqual(report.alignment.status, .estimated, report.alignment.explanation)
            let translation = try XCTUnwrap(report.alignment.translation, original.family_id)
            XCTAssertEqual(translation.x, 0, accuracy: 0.1, original.family_id)
            XCTAssertEqual(translation.y, 0, accuracy: 0.1, original.family_id)
            XCTAssertEqual(try Data(contentsOf: reference), referenceBytes, original.family_id)
            XCTAssertEqual(try Data(contentsOf: floating), floatingBytes, original.family_id)
        }
    }

    func testPNGReencodesPreservePreparedPixels() throws {
        // The corpus's RGB hashes describe Pillow. The nine PNG-source pairs also
        // preserve Apple's prepared pixels; JPEG-source pairs need not do so.
        let originals = entries.filter { $0.transformation == "source" && $0.file.hasSuffix(".png") }
        XCTAssertEqual(originals.count, 9)
        for original in originals {
            let source = try ImagePreparation().prepare(corpus.appendingPathComponent(original.file))
            let reencoded = try ImagePreparation().prepare(url(family: original.family_id, variant: "reencode_png"))
            XCTAssertEqual(source.description.preparedSize, reencoded.description.preparedSize, original.family_id)
            XCTAssertEqual(try bytes(source.pixels), try bytes(reencoded.pixels), original.family_id)
        }
    }

    func testKnownShiftsOnFocusedPreparedImages() throws {
        let focus = try JSONDecoder().decode(Focus.self, from: Data(contentsOf:
            corpus.appendingPathComponent("selections.json")))
        for family in focus.known_shift_families {
            let sourceURL = try url(family: family, variant: "source")
            let sourceBytes = try Data(contentsOf: sourceURL)
            let source = try ImagePreparation().prepare(sourceURL)
            let pixels = source.pixels
            let drawing = try XCTUnwrap(CGContext(
                data: nil, width: pixels.width, height: pixels.height, bitsPerComponent: 8,
                bytesPerRow: pixels.width * 4, space: XCTUnwrap(CGColorSpace(name: CGColorSpace.sRGB)),
                bitmapInfo: CGBitmapInfo.byteOrder32Big.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue
            ))
            drawing.setFillColor(gray: 1, alpha: 1)
            drawing.fill(CGRect(x: 0, y: 0, width: pixels.width, height: pixels.height))
            // Right 17, down 9 in working pixels. This deliberately happens AFTER
            // source preparation, so retina's reduction does not rescale the shift.
            drawing.draw(pixels, in: CGRect(x: 17, y: -9, width: pixels.width, height: pixels.height))
            let reference = try write(pixels, name: "\(family)-reference.png")
            let floating = try write(XCTUnwrap(drawing.makeImage()), name: "\(family)-shifted.png")
            let report = try comparePair(reference: reference, floating: floating,
                                         outputDirectory: directory.appendingPathComponent("\(family)-result"))
            XCTAssertEqual(report.alignment.status, .estimated, report.alignment.explanation)
            let translation = try XCTUnwrap(report.alignment.translation, family)
            XCTAssertEqual(translation.x, -17, accuracy: 0.5, family)
            XCTAssertEqual(translation.y, 9, accuracy: 0.5, family)
            XCTAssertNotNil(report.overlay, family)
            XCTAssertEqual(try Data(contentsOf: sourceURL), sourceBytes, family)
        }
    }

    func testUnequalFixtureDimensionsRemainNotRun() throws {
        let output = directory.appendingPathComponent("crop")
        let report = try comparePair(reference: url(family: "astronaut", variant: "source"),
                                     floating: url(family: "astronaut", variant: "center_crop_85"),
                                     outputDirectory: output)
        XCTAssertEqual(report.alignment.status, .notRun)
        XCTAssertNil(report.alignment.translation)
        XCTAssertNil(report.overlay)
        XCTAssertFalse(FileManager.default.fileExists(atPath: output.appendingPathComponent("overlay.png").path))
        let saved = try JSONDecoder().decode(ComparisonReport.self, from: Data(contentsOf:
            output.appendingPathComponent("comparison.json")))
        XCTAssertEqual(saved.alignment.status, .notRun)
    }

    private func url(family: String, variant: String) throws -> URL {
        let entry = try XCTUnwrap(entries.first { $0.family_id == family && $0.transformation == variant },
                                 "Missing fixture: \(family)/\(variant)")
        return corpus.appendingPathComponent(entry.file)
    }

    private func bytes(_ image: CGImage) throws -> Data {
        // ImagePreparation owns tightly packed sRGB RGBA bytes, not source-file bytes.
        try XCTUnwrap(image.dataProvider?.data) as Data
    }

    private func write(_ image: CGImage, name: String) throws -> URL {
        let result = directory.appendingPathComponent(name)
        let destination = try XCTUnwrap(CGImageDestinationCreateWithURL(
            result as CFURL, UTType.png.identifier as CFString, 1, nil))
        CGImageDestinationAddImage(destination, image, nil)
        XCTAssertTrue(CGImageDestinationFinalize(destination))
        return result
    }
}
