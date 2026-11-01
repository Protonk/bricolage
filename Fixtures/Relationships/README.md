# Related images

These sets contain images with recorded connections: edits of a common source,
separate photographs of a scene, and images generated from source descriptions.
They let a test examine how an image algorithm handles each relationship.

| Set | Fixture ID | Inputs | Relationship | Focus / probes / full |
|---|---|---:|---|---:|
| [Derivatives](Derivatives/README.md) | `hazy-derivatives-v1` | 183 | Recorded transformations and composites from source images | 14 / 115 / 190 pairs |
| [Multiviews](Multiviews/README.md) | `hazy-multiview-v1` | 20 | Separate captures of scenes and short sequences | 16 / 44 / 44 pairs |
| [Variants](Variants/README.md) | `hazy-meme-fixtures-v0` | 42 | Constructed changes, donor replacements and supplied description-mediated generations | 15 / 54 / 54 pairs |

All use the [shared format](../FORMAT.md). Variants retains `kind=derivatives`;
its construction steps are recorded in separate files. Multiview scene labels
and source-family labels remain distinct. Neither is a similarity score.

From the repository root:

```sh
Fixtures/.venv/bin/python Fixtures/Relationships/Derivatives/tools/check.py
Fixtures/.venv/bin/python Fixtures/Relationships/Multiviews/tools/check.py
Fixtures/.venv/bin/python Fixtures/Relationships/Variants/tools/check.py
```

The comparison runner defaults to Derivatives. Use the individual README files for generation
checks and image-preservation limits; the [shared tools](../tools/README.md) run
probe comparisons against a published world.
The [Similarity heap](../Heaps/Similarity/README.md) has a separate selection basis.
