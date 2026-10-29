# Capability handoff ledger

Initial evidence comes from the
[Apple Vision translation experiment](../../Experiments/AppleVisionTranslation/IMAGE-JOURNEY.md).
Every entry below is scoped to that implementation. On 2026-10-29, the relocated
experiment passed all 13 Swift tests and seven fixture-tool tests on macOS 26.7.1.
Its renamed CLI also completed the 16-pair multiview focused run, with fixture
bytes unchanged. No entry has been verified against an OpenCV or Linux
implementation. All port dispositions remain **investigate**.

| Capability | hazy owns in the experiment | Delegated work | Evidence and portability question |
|---|---|---|---|
| Input decoding and orientation | Accept one decodable image; reject invalid dimensions or orientation; default missing orientation to upright; report stored and oriented dimensions | ImageIO decoding, metadata extraction, and application of EXIF orientation | Mechanics check orientation once and reject invalid or multi-image input. Which input formats, metadata defaults, and error cases will the shared API promise? |
| Working image preparation | Longest side limited to 1,024; preserve aspect ratio; request 8-bit sRGB RGBA and flatten onto white; record actual prepared dimensions | ImageIO thumbnail resampling and Core Graphics color conversion and drawing | Resizing and transparency checks cover mechanics; supplied fixtures expose decoder differences. What rounding, color handling, alpha treatment, and pixel representation must be preserved? |
| Translation request | Fixed reference/floating roles; equal-prepared-dimension policy; revision 1; full image; finite translation validation; offsets map floating into reference, positive right/up | Vision chooses and executes the alignment algorithm and compute device | Known shifts and identity checks establish the current direction and units. Real-image estimates are observations, not matching truth. Can an alternative preserve the question and units while returning different estimates or no result? |
| Overlay rendering | Move floating by the estimated offset; show it at 50% opacity over reference; clip to reference bounds | Core Image translation, compositing, and rasterization | Mechanics test that the returned transform improves a controlled overlay. Which interpolation, boundary, and color differences are acceptable for an explanatory artifact? |
| Output and failure reporting | Read-only sources; new output directory; structured preparation and alignment report; distinct estimated, absent, failed, and unperformed analysis | ImageIO PNG encoding; Foundation serialization and filesystem operations | Round-trip report and overwrite checks cover current mechanics. The future API needs portable result meanings and explicit unsupported capabilities without adopting this experiment's schema unchanged. |

## Reading the evidence

The current carrier is `CGImage`, confined to the experiment's Apple implementation.
The public comparison result uses plain values, but includes a Vision method name
and request revision as evidence. Those facts are useful inputs to API research;
they are not a completed abstraction or a compatibility promise.

The seven self-contained mechanics tests and the local fixture checks exercise
this macOS implementation. They do not establish behavior on every declared
macOS version, algorithm parity on Linux, universal image similarity, or a useful
threshold. Unknowns must stay unknown until an experiment supplies evidence.

## Recording a future decision

Extend an entry when a concrete capability changes or a portability experiment
is explicitly selected. Record the input representation, ownership and delegation,
caller-visible contract candidate, environment and evidence, alternatives actually
investigated, disposition, and its rationale. Keep dated observations distinct
from accepted contract requirements. Do not add a wish list of future pathways.
