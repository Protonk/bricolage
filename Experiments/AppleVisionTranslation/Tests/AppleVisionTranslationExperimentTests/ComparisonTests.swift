import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers
import XCTest
@testable import AppleVisionTranslationExperiment

final class ComparisonTests: XCTestCase {
    private var directory: URL!

    override func setUpWithError() throws {
        directory = FileManager.default.temporaryDirectory.appendingPathComponent("hazy-tests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
    }

    override func tearDownWithError() throws {
        try FileManager.default.removeItem(at: directory)
    }

    func testKnownShiftThroughWholeComparison() throws {
        let original = try pattern()
        let referenceURL = try write(original, name: "reference.png")
        let floatingURL = try write(shift(original, x: 17, y: -9), name: "floating.png")
        let referenceBytes = try Data(contentsOf: referenceURL)
        let floatingBytes = try Data(contentsOf: floatingURL)
        let output = directory.appendingPathComponent("result")

        let report = try comparePair(reference: referenceURL, floating: floatingURL, outputDirectory: output)
        XCTAssertEqual(report.alignment.status, .estimated, report.alignment.explanation)
        let translation = try XCTUnwrap(report.alignment.translation)
        // The image was moved right/down. Alignment must undo both movements.
        XCTAssertEqual(translation.x, -17, accuracy: 0.5)
        XCTAssertEqual(translation.y, 9, accuracy: 0.5)
        XCTAssertEqual(try Data(contentsOf: referenceURL), referenceBytes)
        XCTAssertEqual(try Data(contentsOf: floatingURL), floatingBytes)
        XCTAssertEqual(Set(try FileManager.default.contentsOfDirectory(atPath: output.path)),
                       ["reference.png", "floating.png", "overlay.png", "comparison.json"])
        let saved = try JSONDecoder().decode(ComparisonReport.self, from: Data(contentsOf: output.appendingPathComponent("comparison.json")))
        XCTAssertEqual(saved.alignment.translation?.x, translation.x)

        // Verify the rendered result too: applying the returned transform should
        // improve the overlap, catching a sign/origin mistake in the renderer.
        let preparation = ImagePreparation()
        let reference = try preparation.prepare(referenceURL)
        let floating = try preparation.prepare(floatingURL)
        let zeroOverlay = try Rendering().overlay(reference: reference, floating: floating, translation: Translation(x: 0, y: 0))
        let unalignedURL = directory.appendingPathComponent("unaligned.png")
        try zeroOverlay.write(to: unalignedURL)
        let aligned = try preparation.prepare(output.appendingPathComponent("overlay.png"))
        let unaligned = try preparation.prepare(unalignedURL)
        XCTAssertLessThan(try difference(reference.pixels, aligned.pixels), try difference(reference.pixels, unaligned.pixels) * 0.25)
    }

    func testIdentity() throws {
        let url = try write(pattern(), name: "identity.png")
        let image = try ImagePreparation().prepare(url)
        let result = Registration().align(reference: image, floating: image)
        let translation = try XCTUnwrap(result.translation, result.explanation)
        XCTAssertEqual(translation.x, 0, accuracy: 0.1)
        XCTAssertEqual(translation.y, 0, accuracy: 0.1)
    }

    func testOrientationIsAppliedOnce() throws {
        let original = try pattern(width: 240, height: 160)
        let tagged = try write(original, name: "tagged.tiff", type: .tiff, orientation: 6)
        let prepared = try ImagePreparation().prepare(tagged)
        XCTAssertEqual(prepared.description.exifOrientation, 6)
        XCTAssertEqual(prepared.description.preparedSize, PixelSize(width: 160, height: 240))
        // Independently rotate clockwise using Core Graphics, not ImageIO's
        // orientation option, then compare the actual prepared pixels.
        let rotatedContext = try context(width: 160, height: 240)
        rotatedContext.translateBy(x: 0, y: 240)
        rotatedContext.rotate(by: -.pi / 2)
        rotatedContext.draw(original, in: CGRect(x: 0, y: 0, width: 240, height: 160))
        let rotatedURL = try write(XCTUnwrap(rotatedContext.makeImage()), name: "rotated.png")
        let expected = try ImagePreparation().prepare(rotatedURL)
        XCTAssertLessThan(try difference(expected.pixels, prepared.pixels), 0.01)
        let alignment = Registration().align(reference: expected, floating: prepared)
        let translation = try XCTUnwrap(alignment.translation, alignment.explanation)
        XCTAssertEqual(translation.x, 0, accuracy: 0.1)
        XCTAssertEqual(translation.y, 0, accuracy: 0.1)
    }

    func testPreparationBoundsSizeAndFlattensTransparency() throws {
        let transparent = try context(width: 2048, height: 1024)
        let url = try write(XCTUnwrap(transparent.makeImage()), name: "transparent.png")
        let prepared = try ImagePreparation().prepare(url)
        XCTAssertEqual(prepared.description.preparedSize, PixelSize(width: 1024, height: 512))
        XCTAssertEqual(prepared.description.scaleX, 0.5)
        XCTAssertEqual(prepared.description.scaleY, 0.5)
        XCTAssertEqual(prepared.pixels.bitsPerComponent, 8)
        let bytes = try pixels(prepared.pixels)
        XCTAssertTrue(bytes.allSatisfy { $0 == 255 }, "Transparent pixels should become opaque white.")
    }

    func testDifferentDimensionsReportNotRunWithoutOverlay() throws {
        let reference = try write(pattern(), name: "reference.png")
        let floating = try write(pattern(width: 200, height: 160), name: "floating.png")
        let output = directory.appendingPathComponent("result")
        let result = try comparePair(reference: reference, floating: floating, outputDirectory: output)
        XCTAssertEqual(result.alignment.status, .notRun)
        XCTAssertNil(result.alignment.translation)
        XCTAssertNil(result.overlay)
        XCTAssertFalse(FileManager.default.fileExists(atPath: output.appendingPathComponent("overlay.png").path))
        let saved = try JSONDecoder().decode(ComparisonReport.self, from: Data(contentsOf: output.appendingPathComponent("comparison.json")))
        XCTAssertEqual(saved.alignment.status, .notRun)
    }

    func testBadInputAndExistingOutputDoNotOverwriteFiles() throws {
        let bad = directory.appendingPathComponent("bad.png")
        let contents = Data("not an image".utf8)
        try contents.write(to: bad)
        let output = directory.appendingPathComponent("result")
        XCTAssertThrowsError(try comparePair(reference: bad, floating: bad, outputDirectory: output))
        XCTAssertFalse(FileManager.default.fileExists(atPath: output.path))
        XCTAssertEqual(try Data(contentsOf: bad), contents)

        let input = try write(pattern(), name: "input.png")
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: false)
        let sentinel = output.appendingPathComponent("reference.png")
        try contents.write(to: sentinel)
        XCTAssertThrowsError(try comparePair(reference: input, floating: input, outputDirectory: output))
        XCTAssertEqual(try Data(contentsOf: sentinel), contents)
    }

    func testMultiImageInputIsExplicitlyRejected() throws {
        let url = directory.appendingPathComponent("animated.gif")
        let destination = try XCTUnwrap(CGImageDestinationCreateWithURL(url as CFURL, UTType.gif.identifier as CFString, 2, nil))
        let image = try pattern()
        CGImageDestinationAddImage(destination, image, nil)
        CGImageDestinationAddImage(destination, image, nil)
        XCTAssertTrue(CGImageDestinationFinalize(destination))
        XCTAssertThrowsError(try ImagePreparation().prepare(url)) { error in
            XCTAssertTrue(error.localizedDescription.contains("single-image"))
        }
    }

    private func context(width: Int, height: Int) throws -> CGContext {
        try XCTUnwrap(CGContext(
            data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: width * 4,
            space: XCTUnwrap(CGColorSpace(name: CGColorSpace.sRGB)),
            bitmapInfo: CGBitmapInfo.byteOrder32Big.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue
        ))
    }

    private func pattern(width: Int = 384, height: Int = 256) throws -> CGImage {
        let drawing = try context(width: width, height: height)
        drawing.setFillColor(gray: 0.35, alpha: 1)
        drawing.fill(CGRect(x: 0, y: 0, width: width, height: height))
        var seed: UInt64 = 17
        func next(_ limit: Int) -> Int {
            seed = seed &* 6364136223846793005 &+ 1442695040888963407
            return Int((seed >> 32) % UInt64(limit))
        }
        for _ in 0..<160 {
            drawing.setFillColor(red: CGFloat(next(256)) / 255, green: CGFloat(next(256)) / 255,
                                 blue: CGFloat(next(256)) / 255, alpha: 1)
            drawing.fill(CGRect(x: next(width - 30), y: next(height - 30), width: next(22) + 5, height: next(22) + 5))
        }
        return try XCTUnwrap(drawing.makeImage())
    }

    private func shift(_ image: CGImage, x: Int, y: Int) throws -> CGImage {
        let drawing = try context(width: image.width, height: image.height)
        drawing.setFillColor(gray: 0.35, alpha: 1)
        drawing.fill(CGRect(x: 0, y: 0, width: image.width, height: image.height))
        drawing.draw(image, in: CGRect(x: x, y: y, width: image.width, height: image.height))
        return try XCTUnwrap(drawing.makeImage())
    }

    private func write(_ image: CGImage, name: String, type: UTType = .png, orientation: Int = 1) throws -> URL {
        let url = directory.appendingPathComponent(name)
        let destination = try XCTUnwrap(CGImageDestinationCreateWithURL(url as CFURL, type.identifier as CFString, 1, nil))
        CGImageDestinationAddImage(destination, image, [kCGImagePropertyOrientation: orientation] as CFDictionary)
        XCTAssertTrue(CGImageDestinationFinalize(destination))
        return url
    }

    private func pixels(_ image: CGImage) throws -> [UInt8] {
        let drawing = try context(width: image.width, height: image.height)
        drawing.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
        let data = try XCTUnwrap(drawing.data)
        return Array(UnsafeBufferPointer(start: data.assumingMemoryBound(to: UInt8.self), count: image.width * image.height * 4))
    }

    private func difference(_ a: CGImage, _ b: CGImage) throws -> Double {
        XCTAssertEqual(a.width, b.width)
        XCTAssertEqual(a.height, b.height)
        let left = try pixels(a)
        let right = try pixels(b)
        // Ignore borders exposed by translation; check the shared interior.
        var sum = 0.0
        var count = 0
        for y in 24..<(a.height - 24) {
            for x in 24..<(a.width - 24) {
                for channel in 0..<3 {
                    let index = (y * a.width + x) * 4 + channel
                    sum += Double(abs(Int(left[index]) - Int(right[index])))
                    count += 1
                }
            }
        }
        return sum / Double(count)
    }
}
