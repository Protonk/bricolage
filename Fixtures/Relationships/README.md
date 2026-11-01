# Provenance relationships

These three sets were chosen for known relationships among their sources and
captures. Provenance determines the recorded relationship, not whether the
images must look similar to a particular algorithm.

| Set | Fixture ID | Inputs | Relationship | Focus / probes / full |
|---|---|---:|---|---:|
| [Derivatives](Derivatives/README.md) | `hazy-derivatives-v1` | 183 | Recorded transformations and composites from source images | 14 / 115 / 190 pairs |
| [Multiviews](Multiviews/README.md) | `hazy-multiview-v1` | 20 | Separate captures of scenes and short sequences | 16 / 44 / 44 pairs |
| [Variants](Variants/README.md) | `hazy-meme-fixtures-v0` | 42 | Constructed changes, donor replacements and supplied description-mediated generations | 15 / 54 / 54 pairs |

All use the [shared format](../FORMAT.md). Variants retains `kind=derivatives`;
its richer construction lineage is recorded in sidecars. Multiview scene labels
and source-family labels remain distinct. Neither is a similarity score.

From the repository root:

```sh
.venv/bin/python Fixtures/Relationships/Derivatives/tools/check.py
.venv/bin/python Fixtures/Relationships/Multiviews/tools/check.py
.venv/bin/python Fixtures/Relationships/Variants/tools/check.py
```

Derivatives remains the default. Use the individual README files for generation
checks, image-preservation limits and the existing experiment's comparison commands.
The [Similarity heap](../Heaps/Similarity/README.md) has a separate selection basis.
