# hazy — three small Curatorial contributions

**Task:** Create three new leaf fixture sets of approximately **50 acquired images each**, all peers of POTY, US-Army-SSI, Botanical-Illustrations and Evan-Amos-Uploads under `Fixtures/Heaps/Curatorial/`.

```
Fixtures/Heaps/Curatorial/
  Rocks-in-Thin-Section/     # one leaf, ~50 images
  Stone-Hand-Axes/          # one leaf, ~50 images
  Ex-Libris/                # one leaf, ~50 images
```

No sub-heaps. Each leaf combines the **direct File members** of one parent category and the two specified related categories. The three source categories for a leaf are discovery/membership provenance, **not** three requested samples or matching clusters.

## Immediate assignment

1. Read this folder, then read the current repository `Fixtures/Heaps/Curatorial/README.md`, `Fixtures/FORMAT.md`, and the active tools and README for `POTY/`, `Botanical-Illustrations/`, and `US-Army-SSI/`. **Use current active tools, not archived `provenance/supplied/` versions.** At preparation the connected repository was at `c8874023df26167bda41f4a89fe80489a061cd6b`. If the head has moved, inspect changes and adapt rather than blindly copying.
2. Freeze all nine Commons **direct-category** file lists using `categorymembers`. The exact names and individually usable API URLs are in `CATEGORIES.json`. No PetScan, category recursion or external subject search is needed. Handle any API continuation and preserve original response bodies, parameters, hashes, and acquisition date.
3. Deduplicate within each leaf by Commons page ID, retaining every source-category membership. Create stable IDs and a fixed hash-based selection order before any visual reviews.
4. Traverse the order. Use small, bounded thumbnail-vision reviews to **reject actual out-of-scope material**, not to tune or diversify image similarity. Record `accept`, `reject`, or `defer` and concise evidence. Keep unviewed items unreviewed. Continue to approximately 50 eligible images per leaf, with honest shortfalls; **the target is not a quota**.
5. Record work/specimen identity and known duplicate or related representations; preserve uncertainties. Review rights per file. Acquire bounded API-served renditions using the existing conservative Commons transport, then integrate and validate three independent `curatorial_heap` leaves. No similarity tests or expected pairs.

The most important choice is deliberately small: **screen for category mistakes and obvious repeated source objects/works, not for whether the final 50 look alike**. Rocks may have several microscopy appearances; hand axes include both artifacts and drawings; ex libris includes different printing styles.

## Contents

- `CATEGORIES.json`: authoritative list of the nine scoped categories, their direct queries, and target leaf names. The counts are scouting observations, **not** claims about a newly downloaded snapshot.
- `WORKFLOW.md`: acquisition and integration sequence, reproducible ordering and failure semantics.
- `THUMBNAIL_REVIEW.md`: concise instructions for the local small-vision reviewer, with subject-specific scope checks.
- `CHECKS.md`: checks and completion report, keeping visual, rights, provenance and transport states independent.

**No image bytes, fetched Commons inventory, or sample selected images are included.** This handoff is an instruction package; the local agent must fetch, inspect and record actual data. Any missing source data stays unknown instead of being inferred.
