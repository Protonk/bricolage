# Contributing to bricolage

A fixture starts with something we want to try on images. The existing sets
include crops of known sources, photographs taken around the same scene, and
unrelated subjects with similar colors or shapes. Describe what a proposed
collection would let someone examine, with an image or a concrete example when
possible. That gives the selection a purpose and gives the next person something
to assess.

## Choosing images

The choice of images affects what a test can reveal. A set of edits from one
source lets us vary the edit while keeping the source fixed. Separate captures
introduce changes in viewpoint, lighting and motion. A collection chosen for
red accents against green backgrounds tests a different idea of resemblance.
These are useful reasons to collect images, and each needs its own account of
how the images were chosen.

For a new fixture, describe its scope, starting population, selection method and
any exclusions. Keep the candidate list and decisions so someone can understand
how the collection took shape. Record what was inspected: a source page, a
thumbnail and a downloaded image provide different information. Leave unknown
credits or relationships marked as unknown.

Use the [fixture template](Fixtures/Template/README.md) for the files and checks.
The [handoff guide](Fixtures/WEB-AGENT-GUIDE.md) explains what a sourcing partner
can supply. Existing leaf READMEs describe their selection methods and remaining
gaps. A target of fifty images can end at forty-three; a failed download remains
a failed download. Explain the gap rather than quietly changing the selection.

## Trying and changing a fixture

Start with the supplied images and use `Fixtures/sample` to record a draw.
For comparisons across software changes, republish the saved draw. Repeating a
seed against a changed collection can select different images. Put observations
in sampler annotations, where they remain separate from source records.

Look at the images when the question concerns their appearance. Hash checks can
establish that a crop is unchanged, but cannot establish that it is a useful crop
for the test. Likewise, a collection label explains why an image was selected;
the test still needs to say what result it is examining.

When changing a tool, show the input that prompted the change and the result
afterward. Add a focused test for a reproducible bug. Use the relevant fixture
validator for catalog or image changes, and report any incomplete checks. The
commands and storage rules are in [AGENTS.md](AGENTS.md) and
[Fixtures/AGENTS.md](Fixtures/AGENTS.md).

## Writing about the work

The root README introduces the project and gets a sample into someone's hands.
AGENTS holds instructions for working in the checkout. This file explains the
choices involved in making and changing fixtures. Detailed commands, formats
and recovery steps belong with the component that implements them.

Write about particular images, operations and results. Prefer “the crop removes
the sign” to a general claim about what the fixture proves. Give a limitation
where it helps someone use the fixture, and explain the failure an instruction
prevents. Avoid repeating the same caution in every section.

Current guides can be edited for clarity. Supplied documents, acquisition logs
and other provenance records keep their original wording and bytes. Link to them
when their history matters.
