import Foundation

/// Runs one pair through preparation, Apple's request, and presentation.
/// The output directory must be new; source files are only opened for reading.
@discardableResult
public func comparePair(reference referenceURL: URL, floating floatingURL: URL, outputDirectory: URL) throws -> ComparisonReport {
    guard !FileManager.default.fileExists(atPath: outputDirectory.path) else {
        throw HazyError("Output already exists; choose a new directory: \(outputDirectory.path)")
    }
    let preparation = ImagePreparation()
    let reference = try preparation.prepare(referenceURL)
    let floating = try preparation.prepare(floatingURL)
    let alignment = Registration().align(reference: reference, floating: floating)
    let rendering = Rendering()
    var files: [(String, Data)] = [
        ("reference.png", try rendering.png(reference)),
        ("floating.png", try rendering.png(floating)),
    ]
    let overlayName = alignment.translation == nil ? nil : "overlay.png"
    if let translation = alignment.translation, let overlayName {
        files.append((overlayName, try rendering.overlay(reference: reference, floating: floating, translation: translation)))
    }
    let report = ComparisonReport(
        reference: reference.description, floating: floating.description, alignment: alignment,
        maximumDimension: ImagePreparation.maximumDimension, pixelFormat: ImagePreparation.pixelFormat,
        coordinates: "Prepared-image pixels; lower-left origin; x right, y up; floating maps into reference.",
        overlay: overlayName
    )
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
    files.append(("comparison.json", try encoder.encode(report)))
    do {
        try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: false)
        for (name, data) in files {
            try data.write(to: outputDirectory.appendingPathComponent(name), options: .withoutOverwriting)
        }
    } catch {
        throw HazyError("Could not write output to \(outputDirectory.path): \(error.localizedDescription). A partial output directory may remain.")
    }
    return report
}
