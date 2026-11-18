# The placement and alias experiments

## Predictions before the runs

A second reader received the four input definitions and the exercises before seeing any implementation, archive or command output. In this table H is the separate host image. A and A-copy name two paths for the same byte identity.

| Exercise | Independent prediction |
|---|---|
| Specimen under grouping directories beside the host | Two leaves and five listed paths. The host contributes H. The specimen contributes A twice, B once and C once, for four eligible identities across the archive. |
| Specimen under the host’s `tools/example/` | Direct validation passes with four paths and three identities. The enclosing inventory depends on whether a leaf ends discovery. The reader expected the host alone, identified recursive inclusion of both leaves as another possible rule, and considered a nesting error possible. |
| Draw three and keep | The world has three image files, one for each of A, B and C. A and C decode identically. The inventory records both paths to A. |
| Remove the first A path | A fresh draw of three still succeeds. The reader expected republication of the original draw to depend on a single recorded representative. Removing that path would fail, while removing the other would succeed. Successful publication after removing the representative would demonstrate alias fallback. |
| Remove the last A path | A fresh inventory contains just B and C. A new draw of three would exceed the population and a new draw of two would select B and C. Republishing the original draw would fail for A. |
| Replay and original world | At both stages the saved inventory and seed reproduce the original ordered selection. The original world remains readable with all three files. |

## Placement inventories

At commit `d846422`, the two archives contained identical host and specimen files. Only the specimen's location varied. Paths below are relative to the disposable archive's `Fixtures/Relationships/`. The host leaf was `Host/` in both.

| Placement | Discovered leaves | Listed paths | Eligible IDs |
|---|---|---:|---|
| Grouped sibling | `Host/`, `Groups/Level/Example/` | 5 | H, A, B, C |
| Nested | `Host/`, `Host/tools/example/` | 5 | H, A, B, C |

The following bindings were present in both saved populations. Each path is relative to the leaf named in its row. The hashes distinguish which four identities were counted.

| Leaf | Input paths | Identity | SHA-256 of the PNG |
|---|---|---|---|
| Host | `images/host.png` | H | `47da3f8d375ecb367104a17828b86d09bb86c6d8dfc04c1ebff20664e11cf45c` |
| Specimen | `images/01.png`, `images/02.png` | A | `5c9d836c99b38f0b1b823e5a3650f58a002663cabeaca6362aa658137f5f457b` |
| Specimen | `images/03.png` | B | `8cff43a23811126fa78a3303b0a593886df30ecb280456657581ee69f0ed6b7e` |
| Specimen | `images/04.png` | C | `39899b81a5b595e1e7bbd0f2a6842fbdff646722c3af0abb29db50b188c51405` |

The sibling inventory matched the prediction. The nested inventory showed recursive discovery, while the reader had expected only H. The nested specimen passed its own full validator. It could already serve as a worked example, but shipping it inside the host added three tickets to the enclosing archive.

**Decision.** Stop discovery at the first manifest on each branch. An author can place a working fixture under a leaf's `tools/example/` and direct readers to its validator. An author who wants both leaves in the population can place them under grouping directories.

After the change, the sibling inventory had the same paths and IDs. The nested inventory contained only `Host/images/host.png` (H). A direct full check of `Host/tools/example` still verified all four specimen paths and the two decoded RGB arrays. Both inventories reported zero problems. The existing archive had the same inventory ID before and after the change, `5ea0fe40ab6ca0b0227d3939edd7a5d6a0b011896f35ab35c05cf0bde1261086`, covering 19 leaves, 1,305 paths and 1,293 eligible identities.

To repeat both placements from the repository root, use the fixture Python environment described in the [walkthrough](README.md). The helper copies the same host and specimen into two new archives under `Fixtures/output/`.

```sh
placements=$(Fixtures/.venv/bin/python Fixtures/Template/Byte-Identities/prepare_placements.py)
Fixtures/sample --repo "$placements/sibling" inventory
Fixtures/.venv/bin/python "$placements/nested/Fixtures/Relationships/Host/tools/example/tools/check.py"
Fixtures/sample --repo "$placements/nested" inventory
```

Each inventory response names a JSON snapshot in `file`. Open `population.images` in that file to see each `image_id` alongside every `aliases[].path`.

## Removing the aliases

In a fresh disposable Git checkout the specimen was the only active leaf. Seed `arrow-aliases` drew B, A, C in that order. The original draw throughout was `draw-f83ba9a710384b1485d5d38deabca5e5`. Its kept inventory, `cabf8c77084fdc28bae9943388881b72052581bec40d7ad36e2299cf298c0214`, recorded both `images/01.png` and `images/02.png` for A.

| State | Fresh inventory | Publication of the original selection |
|---|---|---|
| Both A paths listed | 4 paths, 3 IDs (A, B, C) | Three files published. A came from `01.png`. |
| Removed `images/01.png` by path | 3 paths, 3 IDs (A, B, C) | Three files published again, now using `02.png` for A. Exit 1 reported `image-unavailable` for the old path and `metadata-changed` for its manifest. Both `published` and `receipt_recorded` were true. |
| Removed `images/02.png` by path | 2 paths, 2 IDs (B, C) | Exit 1, `published: false`, no new world. The `image-unlisted` problem named A's hash and both former paths. |

The first republication settled the reader's open question about the representative path. A saved inventory records all aliases. During publication the sampler could read the surviving listed copy and verify its bytes against A's hash. Once the last alias was removed, the other right-facing arrow at `04.png` still had C's hash.

After the last removal, a separate `verify` reproduced the ordered selection from the saved inventory and seed. It reported `original_draw_reproduced: true`, `images_available: 2` and `publication_ready: false`. The kept inventory and draw file were byte-identical to their initial copies. The three PNGs in the original world could still be decoded and matched their recorded hashes.
