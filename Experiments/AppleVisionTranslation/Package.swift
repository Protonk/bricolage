// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AppleVisionTranslationExperiment",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "hazy-vision-translation", targets: ["VisionTranslationCLI"]),
        .library(name: "AppleVisionTranslationExperiment", targets: ["AppleVisionTranslationExperiment"]),
    ],
    targets: [
        .executableTarget(name: "VisionTranslationCLI", dependencies: ["AppleVisionTranslationExperiment"]),
        .target(name: "AppleVisionTranslationExperiment"),
        .testTarget(name: "AppleVisionTranslationExperimentTests", dependencies: ["AppleVisionTranslationExperiment"]),
    ]
)
