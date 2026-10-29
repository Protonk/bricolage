# Backwards Induction

**hazy router design intent and research stance**

hazy is intended to become an experimental image-similarity router. It will
direct attention toward relationships within a batch, assemble inspectable
evidence, and support provisional organization whose meaning remains free to
float. Designing that router is a research problem.

[Horizontal Gene Transfer](HORIZONTAL-GENE-TRANSFER.md) defines the MVP requirements.
[the experiment image journey](../../Experiments/AppleVisionTranslation/IMAGE-JOURNEY.md) describes the current pair comparator. The comparator is a useful
channel example, not the architecture from which the router must be derived.
The earlier ensemble vision is incorporated here.

## Goals

Make a batch of images investigable through multiple views of similarity. Some
information channels can come from perceptual hashes or other resilient measures;
others can come from analysis pathways assembled within hazy. Present their
contributions together while preserving their individual meanings.

Use coarse, overlapping neighborhoods to direct richer pair investigations.
Make candidate generation and selection visible so a person can understand both
why a pair was examined and what its results mean. One-to-many investigation need
not wait for a complete account of every relationship inside the batch.

Keep the router's evidence explainable from source input through interpretation.
Understanding and teaching framework boundaries is a parallel
[portability research track](../Portability/README.md), aimed at informed decisions
about an eventual shared API on macOS and Linux. Preserve source bytes and expose
failures, unavailable results, and unexamined relationships.

Allow empirical findings to change the design. A useful experiment may show that
a measure is redundant, a selection rule misses valuable pairs, or a proposed
extension does not help. The research purpose is to learn which choices make
investigation useful, not to accumulate mechanisms.

## Categories must be allowed to float

A neighborhood is a working guess about similarity among images in the current
batch under the current methods and settings. Membership does not declare a
semantic category, common identity, interchangeability, or a permanent fact about
the images. Neighborhoods can overlap and leave images unresolved or alone.

Semantic cluster names are an enduring anti-goal. Identifiers and historical
handles are useful for tracing an experiment; they must not become labels for
what the contents inherently mean. An unchanged identifier is not a guarantee of
unchanged membership or meaning across experiments.

This freedom does not remove the need for operational rules. Each proposal must
have an inspectable basis, and an experiment must state what usefulness it is
investigating. Historical records preserve what hazy did even when interpretations
and later arrangements change.

## Channels and the ensemble

A channel contributes information about a comparison. A pathway is a procedure
that asks a defined question and assembles evidence for an answer. It may combine
Vision requests with hazy's own processing; it need not correspond to one request.
The ensemble can contain measurements, explanations, and visual evidence.

Retain native units, scales, direction, method identity, preparation, and relevant
settings. Measurements and conclusions have distinct meanings. A common numeric
range does not make channels comparable or calibrate their values as probabilities.
Confidence requires a defined claim and evidence about the method's behavior.

Disagreement can be informative. Channels may describe different aspects of a
relationship, and an additional result need not imply a membership change. Failed,
unavailable, inconclusive, and unattempted work must remain distinguishable from
evidence against a claim. No combined score or final judgment is mandatory.

Channels may share work or depend on one another. Those dependencies must remain
visible: repeated use of the same evidence is not independent confirmation.
Preparation should suit the question a channel asks while retaining traceability
to the untouched source.

## Baselines and marginal information

Multiple hashes can reveal a response profile for a pair rather than only one
distance. Their research value is the additional useful distinction a method
contributes after the existing responses are known. That can include recovering
overlooked relationships, separating ambiguous cases, or responding differently
and usefully to a change in the images.

Algorithm names and parameter variants do not count as independent perspectives
by themselves. Low correlation alone is insufficient; irrelevant variation can
also be uncorrelated. Conversely, a mostly redundant method may be valuable in a
small but important set of cases. Examine these effects among plausible neighbors
and difficult comparisons as well as across the batch.

The exploratory discussion suggested about eight deliberately different designs,
possibly expanding toward twelve. Those numbers are working hypotheses, not
requirements, an optimum, or a ceiling. The MVP starts with a smaller panel.
Select concrete methods separately; this document records no algorithm roster.
Adding measurements remains useful only insofar as they contribute information
for the investigation. No collection of measures is assumed to supply a universal
notion of image similarity.

## Routing and possible later feedback

The proposed general flow is baseline neighborhood construction, richer
within-neighborhood investigation, and potentially revision of the working
arrangement. Initial similarity is a reason to investigate a pair, not proof that
every channel is applicable or that other pairs would be uninformative.

Routing must account for what it has not examined. Restricting all future work
to initial neighborhoods can preserve initial blind spots. Overlap, alternative
candidate contributions, and exploration across boundaries are possibilities to
study, not guarantees of coverage. Groups and hierarchies are interpretations of
recorded relationships; a fixed tree or exclusive partition is not assumed.

An image-to-group answer must state how member-level evidence was summarized and
which members were examined. A group has no inherent single hash distance. A
summary of its nearest member, its broader distribution, or a representative
answers different questions and must preserve that distinction.

Exhaustive comparison of n images has n(n-1)/2 unordered pairs before accounting
for multiple methods or direction. Overlapping groups can repeatedly propose the
same pair, so reuse matters. Candidate selection and explicit budgets limit the
work performed, with corresponding limits on coverage. Choosing fewer pairs does
not make the unexplored relationships known.

Automatic membership refinement is outside MVP. A future refinement rule would
need to explain how particular evidence supports a membership change, continued
overlap, abstention, or no change. Receiving a result from a framework does not
by itself justify an update. The connection between evidence and membership is
research work, not an automatic consequence of having channels.

Optional automatic churn is also outside MVP. It could investigate sensitivity
by adding or withholding images, perturbing proposed memberships or execution
order, or directing new comparisons. These operations test different things:
batch sensitivity, sensitivity to initialization or order, and the effect of new
evidence. Reorganizing existing evidence must not be counted as acquiring more.

Stability under tested perturbations would describe sensitivity, not certify a
true organization. Persistent ambiguity and fragile boundaries can be useful
outputs. Neither refinement nor churn is designated as the next task.

## Scratch lineage and accountability

hazy must be a scratch lineage builder during a call. It must carry the history
of working transformations and derived results, then save enough of that history
to explain the run. That includes source identities, representations, operations,
parameters, parent relationships, outcomes, and the evidence used in routing
decisions. Temporary working data may be discarded without erasing the account
of what actually happened.

Lineage makes provisional interpretation compatible with accountability. It
separates an observed value from an interpretation, shared evidence from independent
evidence, and a completed transformation from an attempted one. It records the
history hazy can know, without inventing upstream editing history.

The requirement is run-scoped traceability. It does not imply a permanent photo
catalog, a graph database, or a general workflow engine. The MVP specifies the
minimum records needed to inspect a call.

## Anti-goals

These are product and design anti-goals, not a list of postponed features:

- A graphical application. CLI and structured text are the product surface;
  saved visual evidence can still be inspected with existing tools.
- Permanent photo-library organization or a persistent semantic taxonomy.
- Semantic cluster names or category meanings that harden into assertions about
  the images. Category meaning must always be allowed to float.
- Automatic source-file movement, deletion, or destructive deduplication.
- A speculative general framework for arbitrary pathways, designed before
  concrete working behaviors reveal a need for shared structure.

Automatic refinement and churn are different: they remain possible research
directions outside MVP. They are not promised extensions or a scheduled roadmap.

## Reservations and their consequences

**Floating meaning can weaken accountability.** Resolve this through required
scratch lineage and preserved experiment identity. Interpretations may change;
the record of which inputs, transformations, evidence, and rules produced a
result must remain inspectable.

**Research can accumulate mechanisms without learning whether they help.** This
reservation remains active. Experiments need stated local questions, comparison
with simpler alternatives, and room for negative findings. Removing a measure
or changing a selection rule should make it possible to inspect its contribution.
Increasing agreement, stability, or the number of outputs is not by itself success.

**Automatic refinement can force an unsupported membership rule.** Resolve the
MVP pressure by excluding automatic refinement. Pair evidence can be valuable
while baseline memberships remain unchanged. A future update rule must earn its
role through evidence; the current comparator's estimate is not such a rule.

## Research discipline

Use small, reviewed batch experiments to expose retained and missed relationships,
unhelpful comparisons, coverage limits, and the work spent. Exhaustive examination
can provide a comparison baseline at small scale; it does not automatically supply
ground truth about what relationships are useful. Human review must state the
local question being judged without turning it into a permanent cluster category.

Keep enough configuration and lineage to compare calls meaningfully. A changed
input set, method, representation, or policy changes the experiment. Reproducible
records do not promise identical framework outputs across environments.

Use the supplied fixtures without acquiring another corpus. Generated inputs
can test mechanics; limited fixture evidence cannot establish general usefulness.
Detailed research questions, experimental protocols, and success thresholds remain
to be specified in their own context. This design is not a completed research plan.

## Architectural insistences

Swift and Apple frameworks remain the present implementation direction. Keep the
boundary between input, hazy's preparation, Apple's requests, and returned evidence
explicit. Keep framework request and observation types inside their implementation.
The parallel [portability track](../Portability/README.md) records capability
handoffs and their evidence. It aims at an eventual implementation with the same
caller API on Linux, potentially using OpenCV, while allowing informed decisions
to defer or decline individual capabilities. A port is not a router MVP dependency.

Treat today's translation comparator as one worked example of a channel. Its
particular preparation, restrictions, orchestration, and reports do not define a
universal channel interface or router structure. The next concrete behavior we
choose should reveal what structure is useful to share.

Do not seed repository guidance or planning with speculative named pathways,
candidate rankings, or an implied next pathway. Preserve the open choice for a
task that explicitly selects it. The MVP requirements define observable behavior;
they do not authorize implementing every possible future direction described here.
