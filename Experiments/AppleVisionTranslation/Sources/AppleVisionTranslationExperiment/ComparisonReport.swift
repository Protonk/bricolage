import Foundation

public struct PixelSize: Codable, Equatable, Sendable {
    public let width: Int
    public let height: Int
}

public struct ImageDescription: Codable, Sendable {
    public let id: String
    public let storedSize: PixelSize
    public let exifOrientation: UInt32
    public let orientedSize: PixelSize
    public let preparedSize: PixelSize
    public let bytesPerRow: Int

    // Scaling follows EXIF orientation. Integer thumbnail dimensions can round.
    public var scaleX: Double { Double(preparedSize.width) / Double(orientedSize.width) }
    public var scaleY: Double { Double(preparedSize.height) / Double(orientedSize.height) }
}

/// Maps floating pixels into reference pixels by adding x and y offsets.
/// Both images use a lower-left origin, with positive x right and positive y up.
public struct Translation: Codable, Sendable {
    public let x: Double
    public let y: Double
}

public enum AlignmentStatus: String, Codable, Sendable {
    case estimated
    case noObservation
    case failed
    case notRun
}

public struct AlignmentResult: Codable, Sendable {
    public let status: AlignmentStatus
    public let method: String
    public let requestRevision: Int
    public let translation: Translation?
    public let explanation: String
}

public struct ComparisonReport: Codable, Sendable {
    public let worldID: String?
    public let reference: ImageDescription
    public let floating: ImageDescription
    public let alignment: AlignmentResult
    public let maximumDimension: Int
    public let pixelFormat: String
    public let coordinates: String
    public let overlay: String?

    public var summary: String {
        func describe(_ label: String, _ image: ImageDescription) -> String {
            "\(label): \(image.id)\n"
            + "  stored \(image.storedSize.width)×\(image.storedSize.height), EXIF orientation \(image.exifOrientation)"
            + " → prepared \(image.preparedSize.width)×\(image.preparedSize.height)"
        }
        var lines = [
            "World: \(worldID ?? "mechanics test")",
            describe("Reference", reference),
            describe("Floating", floating),
            "Preparation: \(pixelFormat); longest side at most \(maximumDimension) pixels.",
            "Request: \(alignment.method), revision \(alignment.requestRevision).",
            "Outcome: \(alignment.status.rawValue). \(alignment.explanation)",
        ]
        if let shift = alignment.translation {
            lines.append(String(format: "Floating → reference: x %+.3f px, y %+.3f px (right/up positive).", shift.x, shift.y))
        }
        if let overlay {
            lines.append("Overlay: \(overlay) — floating at 50% opacity over reference; clipped to reference bounds.")
        }
        return lines.joined(separator: "\n")
    }
}

public struct HazyError: LocalizedError {
    public let message: String
    public init(_ message: String) { self.message = message }
    public var errorDescription: String? { message }
}
