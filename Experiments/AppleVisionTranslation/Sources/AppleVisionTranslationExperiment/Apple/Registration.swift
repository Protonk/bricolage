import Foundation
import Vision

struct Registration {
    func align(reference: PreparedImage, floating: PreparedImage) -> AlignmentResult {
        let request = VNTranslationalImageRegistrationRequest(
            targetedCGImage: floating.pixels, orientation: .up, options: [:]
        )
        request.revision = VNTranslationalImageRegistrationRequestRevision1

        func result(_ status: AlignmentStatus, _ explanation: String, _ translation: Translation? = nil) -> AlignmentResult {
            AlignmentResult(
                status: status, method: "VNTranslationalImageRegistrationRequest",
                requestRevision: Int(request.revision), translation: translation, explanation: explanation
            )
        }

        // This is a deliberate first-slice restriction, not a claim about Vision.
        guard reference.description.preparedSize == floating.description.preparedSize else {
            return result(.notRun, "This slice requires equal prepared dimensions; it does not stretch images to match.")
        }
        let handler = VNImageRequestHandler(cgImage: reference.pixels, orientation: .up, options: [:])
        do {
            try handler.perform([request])
        } catch {
            return result(.failed, "Vision request failed: \(error.localizedDescription)")
        }
        guard let observation = request.results?.first else {
            return result(.noObservation, "Vision returned no alignment observation.")
        }
        let transform = observation.alignmentTransform
        guard [transform.a, transform.b, transform.c, transform.d, transform.tx, transform.ty].allSatisfy(\.isFinite),
              abs(transform.a - 1) < 0.000001, abs(transform.d - 1) < 0.000001,
              abs(transform.b) < 0.000001, abs(transform.c) < 0.000001 else {
            return result(.failed, "Vision returned an invalid or non-translational transform.")
        }
        return result(
            .estimated, "Vision estimated a translation. This does not establish that the images match.",
            Translation(x: Double(transform.tx), y: Double(transform.ty))
        )
    }
}
