# Horizontal Gene Transfer

**hazy router MVP requirements**

The MVP is a CLI batch experiment: ingest a directory, propose overlapping
similarity neighborhoods, investigate selected pairs through available channels,
and save inspectable results with the lineage of the work performed. It must let
a person understand where comparison effort went and what the evidence supports.

Automatic membership refinement and automatic churn are outside this MVP.
The neighborhoods remain the baseline proposals for the run; subsequent channel
results enrich the evidence without automatically changing membership.

[Backwards Induction](BACKWARDS-INDUCTION.md) carries the design intent, enduring
anti-goals, reservations, and research stance. These requirements describe work
to be implemented, not capabilities already present.

## Relationship to the current code

The existing pair comparator is a useful channel example. It prepares images,
asks Apple Vision for a translation, and returns an estimate or a visible reason
that an estimate is unavailable. Its output illustrates the distinction between
a measurement and a judgment that images match. [the experiment image journey](../../Experiments/AppleVisionTranslation/IMAGE-JOURNEY.md) documents that
implementation.

The comparator is not the router architecture. Its single pair entry point,
preparation choices, equal-dimension restriction, result types, and output layout
do not become requirements for every router channel. Reuse working behavior where
it fits. Shared structure must follow the behaviors actually implemented; no new
pathway is selected by these documents.

The parallel [portability track](../Portability/README.md) investigates framework
handoffs and an eventual shared API on macOS and Linux. The MVP's lineage and
method records supply evidence to that track; implementing a port is outside MVP.

## Batch input and experiment identity

Accept one user-supplied directory as a batch. Record its resolved input inventory,
the discovery policy, file identities and paths, and each input's acceptance or
failure status. Preserve all source bytes. Changes to batch contents or settings
must be visible when comparing experiments.

Each run must record its configuration, method identities and versions, relevant
framework and environment information, and any random seeds or order-sensitive
choices used. The initial working scale is a few hundred images; performance at
that scale must be measured rather than assumed.

Compute reusable image measurements once where their input representation and
settings are the same. Reuse must preserve the connection to the original
measurement. Persistent caching across calls is not required.

## Baseline similarity neighborhoods

Use a small panel of multiple, materially different perceptual hashes or other
resilient similarity measures. Three or four measures are the initial working
scope, not a claim about the optimal panel. Select the actual methods separately;
the MVP must support inspecting a run with one selected measure disabled.

Preserve each method's native comparison meaning, settings, and candidate
contributions. Do not turn differing numeric scales into a common confidence
merely by normalizing them. Candidate eligibility and neighborhood construction
must use an explicit, recorded policy whose parameters can be varied between runs.
No particular clustering algorithm is prescribed here.

Produce overlapping neighborhoods and allow singleton or unresolved images.
Membership must have an inspectable basis: contributing measurements, candidate
proposals, and the construction rule. Neighborhood identifiers are handles within
an experiment, not semantic category names. Membership expresses only a provisional
guess about similarity within this batch under these settings.

Do not require exhaustive channel analysis of every batch pair before proposing
neighborhoods. Baseline distance computation and expensive pair investigation
are distinct work. Report what the candidate process actually examined or
retrieved; absence from a candidate set must not be represented as a measured
negative relationship.

## Bounded pair investigation

Select pairs from the proposed neighborhoods under an explicit comparison budget
and selection policy. Preserve the neighborhood memberships and candidate reasons
that caused each pair to be considered. A pair proposed by several neighborhoods
must not incur duplicate equivalent analysis. Preserve direction whenever the
question or method is directional.

Run the available selected channels and keep their results individually
inspectable as an ensemble. The existing comparator can supply a channel for
this experiment. Its restrictions may produce unavailable results; membership in
a neighborhood does not establish that every channel is applicable.

Distinguish completed measurements, inconclusive interpretations, missing
observations, failed operations, inapplicable operations, and work not attempted
because of selection or budget. These distinctions need clear meanings, not
necessarily one shared enum. None may silently become a negative match decision.

Channel results must retain their units, direction, interpretation, dependencies,
and supporting artifact references. No universal similarity score, calibrated
confidence, or automatic membership update is required. An estimate alone is not
evidence that two images belong together.

## Scratch lineage is required

hazy must build scratch lineage during a call and retain it with the saved run.
The lineage explains how untouched source inputs led to working representations,
measurements, pair investigations, and neighborhood proposals. It must remain
readable after temporary working data has been discarded.

The saved record must support tracing:

- A working representation to its source image and the transformations actually
  performed, in order, including relevant parameters and resulting dimensions,
  orientation, color, or pixel conventions.
- A measurement to the exact representation, method, settings, and prior results
  it consumed, including whether an existing result was reused.
- A channel result or artifact to its inputs, attempted operations, outcome, and
  any failure that interrupted the chain.
- A candidate, pair selection, or neighborhood membership to its contributing
  evidence and the policy that produced it.

Record the operations performed by this call. Do not invent an image's processing
history before ingestion. Record attempted operations and partial completion as
such; planned work must not appear as completed work.

Derived objects need identifiers and parent references sufficient to follow
branches and shared inputs. This is a requirement on inspectable records, not a
mandate for a graph database, event-sourcing system, or generic execution engine.
Intermediate pixel buffers need not all be retained; their production and use
must be recorded, and missing artifacts must be distinguishable from missing
operations. Reconstructing the account of a call does not promise bit-identical
re-execution of framework algorithms.

Within the MVP, lineage covers initial neighborhood construction and channel
investigation. It does not imply an automatic refinement history that has not
occurred. Floating interpretations require reliable historical records.

## CLI and structured output

Provide a batch-run operation and a way to inspect a saved run, including the
position of one image in that experiment. Illustrative command shapes are:

```sh
hazy route ./photos --output ./runs/experiment-01
hazy inspect ./runs/experiment-01 --image IMG_1234.JPG
```

These commands are not implemented today; exact syntax and image selectors remain
implementation choices. Inspection must expose existing evidence without silently
starting new analysis.

The terminal account must summarize accepted and failed inputs, candidate and
examined pairs, neighborhood membership, channel outcomes, and budget coverage.
For an individual image, expose its memberships, the reasons for those memberships,
the pair evidence available, and the extent of unexamined relationships.

Saved structured text must cover the following records. Their physical layout
remains an implementation choice; the information and references are required.

| Record | Required information |
|---|---|
| Run | Input inventory, configuration, versions, budgets, completion state, counts, artifact references |
| Images | Source identities and paths, preparation references, baseline measurements, input failures |
| Pairs | Candidate and selection reasons, channel results, direction, execution status, evidence references |
| Neighborhoods | Memberships, contributing evidence, construction policy, batch scope |
| Lineage | Operation identities, parent and output references, transformation details, reuse, outcomes |

Use an identified schema so scripts can read the results without parsing terminal
prose. Preserve completed evidence if work fails or is interrupted, marking the
run incomplete. Protect existing outputs from silent replacement. A saved run
must distinguish budget completion from exhaustive examination of the batch.

Visual evidence may be saved and opened in existing tools. The graphical-interface
anti-goal does not prohibit prepared images or other useful inspection artifacts.

## Acceptance evidence

The MVP is ready when a reviewer can complete these checks:

1. Run a supplied batch and account for every discovered input, including failures,
   while verifying that source files remain unchanged.
2. Inspect overlapping memberships, singletons, and their measurement-based reasons
   without semantic category labels or forced assignments.
3. Trace a result through scratch lineage to its source inputs and actual working
   transformations, including shared or reused work and failed operations.
4. Verify that equivalent pair investigations are reused across overlapping
   neighborhoods and that budgets leave explicit coverage limits.
5. Inspect available channel evidence separately from membership proposals; verify
   that no automatic refinement or churn has occurred.
6. Change one setting or disable one measure in a separate run and explain the
   observed differences using the saved records. A built-in run-diff command is
   not required.
7. On a small reviewed batch, compare routed coverage with an exhaustive examination
   under a stated local review question. Record useful pairs retained or missed,
   unhelpful comparisons, and the work performed. Exhaustive measurement alone is
   not ground truth about usefulness.

Use the supplied fixtures for focused checks and review; their labels do not
establish universal matching quality. Negative findings are valid research
results. Functional acceptance requires that the experiment can reveal them,
not that a preferred routing policy wins.

## Scope boundaries and remaining choices

Automatic membership refinement and automatic churn are outside MVP. Separate
runs with a changed batch or setting can support manual experiments. Neither
automatic feature is implied as the next implementation task.

The enduring anti-goals in [Backwards Induction](BACKWARDS-INDUCTION.md#anti-goals)
apply here: no graphical application, permanent photo-library organization,
semantic cluster names, automatic source-file movement or deletion, or speculative
general framework for arbitrary pathways.

The baseline methods, neighborhood rule, pair-selection policy, budget defaults,
serialization details, and exact CLI remain choices to resolve through focused
work. No new named pathway, hash implementation roster, or execution architecture
is selected by these requirements.
