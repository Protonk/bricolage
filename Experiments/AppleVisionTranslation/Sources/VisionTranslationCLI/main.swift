import Darwin
import Foundation
import AppleVisionTranslationExperiment

let usage = """
Usage: hazy-vision-translation compare --world WORLD --reference IMAGE_ID --floating IMAGE_ID --output DIRECTORY

Validate a world, prepare two images by ID, estimate a translation with Apple
Vision, and save comparison.json, prepared images and any alignment overlay.
DIRECTORY must be outside WORLD and new; its parent must exist.

Exit codes: 0 alignment estimated; 1 input/output/usage error; 2 no alignment.
"""

let arguments = Array(CommandLine.arguments.dropFirst())
if arguments == ["--help"] || arguments == ["-h"] || arguments == ["compare", "--help"] {
    print(usage)
    exit(0)
}
let flags: Set<String> = ["--world", "--reference", "--floating", "--output"]
var options: [String: String] = [:]
var valid = arguments.count == 9 && arguments.first == "compare"
if valid {
    for index in stride(from: 1, to: arguments.count, by: 2) {
        let flag = arguments[index]
        let value = arguments[index + 1]
        if !flags.contains(flag) || options[flag] != nil || value.isEmpty { valid = false; break }
        options[flag] = value
    }
}
guard valid, Set(options.keys) == flags else {
    FileHandle.standardError.write(Data((usage + "\n").utf8))
    exit(1)
}

do {
    let world = try World(directory: URL(fileURLWithPath: options["--world"]!, isDirectory: true))
    let output = URL(fileURLWithPath: options["--output"]!, isDirectory: true)
    let report = try compareWorld(world, referenceID: options["--reference"]!, floatingID: options["--floating"]!,
                                  outputDirectory: output)
    print(report.summary)
    print("Saved to: \(output.standardizedFileURL.path)")
    exit(report.alignment.status == .estimated ? 0 : 2)
} catch {
    FileHandle.standardError.write(Data(("hazy-vision-translation: \(error.localizedDescription)\n").utf8))
    exit(1)
}
