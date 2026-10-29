import Darwin
import Foundation
import AppleVisionTranslationExperiment

let usage = """
Usage: hazy-vision-translation compare REFERENCE FLOATING --output DIRECTORY

Prepare two images, estimate a translation with Apple Vision, and save the
prepared images, comparison.json, and (when available) an alignment overlay.
DIRECTORY must not already exist; its parent must exist.

Exit codes: 0 alignment estimated; 1 input/output/usage error; 2 no alignment.
"""

let arguments = Array(CommandLine.arguments.dropFirst())
if arguments == ["--help"] || arguments == ["-h"] || arguments == ["compare", "--help"] {
    print(usage)
    exit(0)
}
guard arguments.count == 5, arguments[0] == "compare", arguments[3] == "--output",
      !arguments[1].isEmpty, !arguments[2].isEmpty, !arguments[4].isEmpty else {
    FileHandle.standardError.write(Data((usage + "\n").utf8))
    exit(1)
}

do {
    let output = URL(fileURLWithPath: arguments[4], isDirectory: true).standardizedFileURL
    let report = try comparePair(
        reference: URL(fileURLWithPath: arguments[1]).standardizedFileURL,
        floating: URL(fileURLWithPath: arguments[2]).standardizedFileURL,
        outputDirectory: output
    )
    print(report.summary)
    print("Saved to: \(output.path)")
    exit(report.alignment.status == .estimated ? 0 : 2)
} catch {
    FileHandle.standardError.write(Data(("hazy-vision-translation: \(error.localizedDescription)\n").utf8))
    exit(1)
}
