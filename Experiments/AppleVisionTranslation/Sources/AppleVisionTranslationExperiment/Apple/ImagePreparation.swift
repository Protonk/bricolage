import CoreGraphics
import Foundation
import ImageIO

// The current implementation owns a CGImage. A future implementation can change
// this carrier without changing the dimensions and coordinate contract in reports.
struct PreparedImage {
    let pixels: CGImage
    let description: ImageDescription
}

struct ImagePreparation {
    static let maximumDimension = 1024
    static let pixelFormat = "8-bit sRGB RGBA, alpha flattened onto white"

    func prepare(_ url: URL, id suppliedID: String? = nil) throws -> PreparedImage {
        let id: String
        do { id = try suppliedID ?? imageIdentity(at: url) }
        catch { throw HazyError("Cannot read image bytes.") }
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
            throw HazyError("Cannot open image: \(id)")
        }
        guard CGImageSourceGetCount(source) == 1 else {
            throw HazyError("Expected a single-image file: \(id)")
        }
        guard let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
              let width = properties[kCGImagePropertyPixelWidth] as? Int,
              let height = properties[kCGImagePropertyPixelHeight] as? Int,
              width > 0, height > 0 else {
            throw HazyError("Cannot read image dimensions: \(id)")
        }
        let orientation = (properties[kCGImagePropertyOrientation] as? UInt32) ?? 1
        guard (1...8).contains(orientation) else {
            throw HazyError("Unsupported EXIF orientation \(orientation): \(id)")
        }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: Self.maximumDimension,
        ]
        // ImageIO applies EXIF orientation here. Vision later receives .up.
        guard let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary),
              let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
              let context = CGContext(
                data: nil, width: thumbnail.width, height: thumbnail.height,
                bitsPerComponent: 8, bytesPerRow: thumbnail.width * 4,
                space: colorSpace,
                bitmapInfo: CGBitmapInfo.byteOrder32Big.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue
              ) else {
            throw HazyError("Cannot prepare image: \(id)")
        }
        let bounds = CGRect(x: 0, y: 0, width: thumbnail.width, height: thumbnail.height)
        context.setFillColor(red: 1, green: 1, blue: 1, alpha: 1)
        context.fill(bounds)
        context.draw(thumbnail, in: bounds)
        guard let pixels = context.makeImage() else {
            throw HazyError("Cannot finish preparing image: \(id)")
        }
        let swapsAxes = orientation >= 5
        return PreparedImage(
            pixels: pixels,
            description: ImageDescription(
                id: id,
                storedSize: PixelSize(width: width, height: height),
                exifOrientation: orientation,
                orientedSize: PixelSize(width: swapsAxes ? height : width, height: swapsAxes ? width : height),
                preparedSize: PixelSize(width: pixels.width, height: pixels.height),
                bytesPerRow: pixels.bytesPerRow
            )
        )
    }
}
