# Framework boundaries and API portability

This parallel research track turns understanding and teaching the boundary around
Apple Vision calls into evidence for implementation decisions. The target is an
eventual hazy implementation on macOS and another platform, such as Linux using
OpenCV, with the same caller-facing API. It must be possible to decide deliberately
which capabilities to hand off, reimplement, approximate, defer, or not port.

The [router track](../Router/README.md) studies useful routing behavior. This track
studies the guarantees and dependencies underneath that behavior. Neither track
must wait for a complete solution from the other. The current
[translation experiment](../../Experiments/AppleVisionTranslation/README.md)
provides initial evidence; its function and report types are not the settled
portable API. No Linux implementation or backend-switching layer exists today.

## The boundary we investigate

For an implemented capability, trace four stages:

1. The supplied input and its known upstream processing history.
2. Preparation and policy selected by hazy, including any work delegated to a
   decoder, resampler, color system, or renderer.
3. The framework request: exact inputs, settings, revision, and behavior left to
   the framework.
4. The returned observation and hazy's interpretation, validation, failures,
   units, coordinates, and exported evidence.

The boundary extends beyond Vision. Decoding, orientation, color conversion,
resampling, rendering, and encoding can affect a result before or after the
analysis request. A same-named operation in another library does not establish
identical behavior. Keep documented guarantees, observed behavior, and open
questions distinguishable.

## Meaning of the same API

The eventual aim is the same caller operations and structured contracts for
supported capabilities, with explicit conventions for inputs, results, errors,
and lineage. Callers should not need Apple request or observation types. Backend
identity and version must remain visible in evidence so differing outcomes can
be investigated without changing how a caller asks the question.

API compatibility does not require identical internal algorithms or identical
numerical estimates. It does require a stated meaning for each returned value
and a way to distinguish an unsupported capability from a failed request, missing
observation, or negative finding. A decision not to port a capability must remain
visible through the agreed API rather than silently substituting another question.
The exact API and representation of capabilities remain research decisions.

The current experiment's 1,024-pixel working limit, equal-dimension guard,
framework-specific method label, and `CGImage` carrier are observations about one
implementation. None is automatically a portable contract. Future shared types
and interfaces should follow concrete behavior, not speculation.

## Capability decisions

Use the [capability ledger](CAPABILITY-LEDGER.md) to record the following for each
implemented capability whose handoff matters:

- What the caller is asking, and what semantics hazy owns.
- What is delegated, including hidden dependencies and relevant revisions.
- What the available checks establish, on which environment, and what remains
  unverified.
- What a portable implementation would have to preserve or deliberately change.
- The current disposition: investigate, retain the delegation, implement an
  alternative, accept a documented difference, defer, or decline the port.

A possible OpenCV equivalent is a hypothesis until checked. Record an informed
reason for handing work to a framework or keeping it in hazy; do not equate
availability of a library call with compatibility. A capability can remain useful
on one platform even when its port is deferred or declined.

## Evidence and experiments

Keep experiments small enough to connect inputs, preparation, requests, and
outputs. Use known transformations to check mechanics and supplied real images
to examine usefulness. Compare intermediate representations when results differ,
so an analysis discrepancy is not automatically blamed on the registration step.

Tests should distinguish contract checks from algorithm-specific numerical
observations. Record method identity, environment, parameters, and lineage;
preserve source bytes. Unsupported behavior and missing evidence must stay
visible. Use the supplied fixtures without acquiring another corpus.

Explaining a handoff is part of producing research evidence and making an informed
porting decision. It does not turn the router product into a Vision tutorial, and
it does not require a general backend framework, implementation on Linux, or a
new analytical pathway in the current task.
