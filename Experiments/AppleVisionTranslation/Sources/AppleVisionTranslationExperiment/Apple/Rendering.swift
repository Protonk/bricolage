import CoreGraphics
import CoreImage
import Foundation
import ImageIO
import UniformTypeIdentifiers

struct Rendering {
    func png(_ image: PreparedImage) throws -> Data {
        try png(image.pixels)
    }

    func overlay(reference: PreparedImage, floating: PreparedImage, translation: Translation) throws -> Data {
        let background = CIImage(cgImage: reference.pixels)
        let shifted = CIImage(cgImage: floating.pixels).transformed(by: CGAffineTransform(
            translationX: translation.x, y: translation.y
        ))
        let translucent = shifted.applyingFilter("CIColorMatrix", parameters: [
            "inputAVector": CIVector(x: 0, y: 0, z: 0, w: 0.5),
        ])
        let composite = translucent.composited(over: background).cropped(to: background.extent)
        guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
              let image = CIContext().createCGImage(
                composite, from: background.extent, format: .RGBA8, colorSpace: colorSpace
              ) else {
            throw HazyError("Core Image could not render the alignment overlay.")
        }
        return try png(image)
    }

    private func png(_ image: CGImage) throws -> Data {
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(data, UTType.png.identifier as CFString, 1, nil) else {
            throw HazyError("ImageIO could not create a PNG encoder.")
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else {
            throw HazyError("ImageIO could not finish encoding a PNG.")
        }
        return data as Data
    }
}
