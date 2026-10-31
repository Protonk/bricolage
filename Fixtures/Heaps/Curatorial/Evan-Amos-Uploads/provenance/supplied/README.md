# Evan-Amos category uploads — Curatorial heap handoff

**Task:** acquire **every direct File member** of the Wikimedia Commons category
[Media uploaded by Evan Amos](https://commons.wikimedia.org/wiki/Category:Media_uploaded_by_Evan_Amos),
**except exactly the three user-named File pages** in `EXCLUSIONS.txt`.

This replaces the earlier proposal to sample ~150 images from the much broader
Evan Amos photographic corpus. It does **not** authorize sourcing from
`Category:Evan_Amos`, his user page, or any descendant category. The source is
this one, exact, direct-membership category; it is not an authorship assertion.

As observed on 2026-10-31, the category page lists **136 direct files**, and
all three exclusions appear there. **133 eligible File pages** are therefore
expected for that snapshot. This is a *check*, not a hard-coded cap: if the
live category inventory differs, preserve the actual response and report the
difference rather than forcing 133 or silently discarding new members.

## Destination

```
Fixtures/Heaps/Curatorial/
  POTY/
  US-Army-SSI/
  Evan-Amos-Uploads/     # one leaf, NO sub-heaps
```

Create one `curatorial_heap` fixture with `relation_kind=curatorial_selected`.
There is no aesthetic selection, author quota, one-object-per-image constraint,
seeded sampling cutoff, visual prompt, similarity label, or 30-image minimum.
The three supplied File titles are the **only policy exclusions**.

All alternative angles, component photographs, transparent PNGs alongside JPEGs,
close-ups, repeated views, and even different file pages depicting the same
physical object belong in the collection. Preserve discoverable relatedness as
*provenance*, not as a reason to drop them. Cross-fixture matches should be
reported, not silently removed. File-level technical or rights problems remain
explicitly **pending/blocking**, not additional quiet exclusions.

The repository baseline inspected for this handoff is
[`Protonk/hazy` commit `20df8b0c6fbb2e95de9d67ff56bd6b6ae500ca93`](https://github.com/Protonk/hazy/commit/20df8b0c6fbb2e95de9d67ff56bd6b6ae500ca93).
Read the *then-current* `Fixtures/Heaps/Curatorial/README.md`,
`Fixtures/FORMAT.md`, `POTY/README.md`, and `US-Army-SSI/README.md` and active
tools before implementation. Do not use archived `provenance/supplied/tools/`
as the working baseline. The repo contains the textual tools and manifests but
not the Git-ignored media assets.

See `SCOPE.md` for exact membership and identity rules, `ACQUISITION.md` for the
transport/integration procedure, and `CHECKS.md` for completion criteria.
