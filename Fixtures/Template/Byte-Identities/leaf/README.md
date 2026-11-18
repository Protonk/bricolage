# Byte identities

Open the four PNGs side by side. A dark teal arrow with two ochre tail stripes
points right in 01, 02 and 04. In 03 its point and stripes have switched sides.

| Label | Input | Bytes | Decoded RGB |
|---|---|---|---|
| A | `images/01.png` | Original PNG | Right arrow |
| A-copy | `images/02.png` | Exact copy of 01 | Right arrow |
| B | `images/03.png` | Reflected PNG | Left arrow |
| C | `images/04.png` | Original pixels with a PNG text chunk | Right arrow |

The four paths give three byte identities and two distinct RGB arrays.
The sampler gives one ticket to each distinct byte identity. Even when 01
and 02 have both left the collection, 04 still looks like the original.
Its extra PNG chunk gives it a different identity.

All four inputs were constructed for this example. Their hashes, source family
and transformations are in [manifest.csv](manifest.csv). The
[probes](probes.csv) compare the first input with each of the other three.
The [build record](provenance/construction/BUILD.md) gives the recipe.

<!-- collection-totals:start -->
<!-- collection-totals:end -->
