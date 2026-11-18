# Arrow construction

The pattern in [materialize.py](../../tools/materialize.py) has sixteen columns
and ten rows. Each cell becomes a six-by-six square of cream (244, 236, 210),
teal (19, 85, 93) or ochre (240, 165, 54). The PNG stores 8-bit RGB,
non-interlaced, with filter zero on every scanline. Its IDAT contains a single
stored DEFLATE block. There are no timestamps or external assets.

| Input | Operation |
|---|---|
| `images/01.png` (A) | Encode the right-facing pattern as `sources/arrow.png` and copy its bytes. |
| `images/02.png` (A-copy) | Write A's exact bytes under a second path. |
| `images/03.png` (B) | Reverse the order of cells in every pattern row, then encode. |
| `images/04.png` (C) | Encode the original pattern and add one tEXt chunk before IDAT, with keyword `Description` and value `Same arrow, second encoding`. |

[SHA256SUMS.txt](../../SHA256SUMS.txt) pins the five files, including the
source. [manifest.csv](../../manifest.csv) pins each input's decoded RGB hash
over its row-major channel bytes, without headers or row filters.
