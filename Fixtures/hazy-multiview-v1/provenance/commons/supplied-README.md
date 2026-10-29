# hazy — quasi-multiview fixture v1

This is the **download-and-package kit**, not yet the complete image-bearing fixture. The runtime in which this kit was assembled could look up the Commons pages but could not transfer the nine original photo files. The script supplies the final, complete fixture on a network-connected Mac without third-party dependencies.

## One command

From the extracted `hazy-quasi-multiview-v1` folder, run:

```sh
python3 fetch_and_package.py
```

It downloads the **nine original, unmodified JPEGs**, checks their exact byte size and Wikimedia Commons SHA-1, writes `images/`, `manifest.csv`, `manifest.json`, `pairs.csv`, `SHA256SUMS.txt`, `image_paths.txt`, and `source_metadata.json`, then creates `hazy-quasi-multiview-v1-complete.zip` in the *parent directory*. It will not create a complete ZIP if a source fails to download or verify. Rerunning reuses intact originals.

There are four distinct scene groups, all under the category **`quasi-multiview`**:

| Scene group | Original exposures | Photographer | License |
|---|---:|---|---|
| `kumbh-mauni-amavasya` | 2 | Michael T Balonek | CC BY-SA 4.0 |
| `budapest-pride-1424` | 2 | Vauia Rex | CC0 1.0 |
| `budapest-pride-1428` | 2 | Vauia Rex | CC0 1.0 |
| `budapest-pride-1435` | 3 | Vauia Rex | CC0 1.0 |

`images/` is one flat directory with opaque filenames. Import only this directory to hazy. `manifest.csv` holds `category=quasi-multiview` for every image, and `scene_group` distinguishes the four photo sequences. `pairs.csv` lists the six within-sequence pairings (1+1+1+3), which are **human-supplied relationship labels**, not claims about Vision's feature distances or cluster threshold.

## Provenance and reproducibility

`fixtures.json` is the source of truth for the exact nine files, including the easily confused `...143521_1.jpg` and `...143521.jpg` sources. `source_manifest.csv` is a human-readable copy. `source_metadata.json` (generated only after fetching) records author and licensing as returned by the Wikimedia Commons API. All bytes are taken from Commons' `imageinfo.url`, **not a thumbnail**. There is no resizing, recompression, metadata removal, or synthetic transformation.

The author/license information above is taken from Commons' source pages; the fetcher also captures the current API data so the eventual ZIP has an independently recoverable provenance trail. The two Kumbh images require attribution and adherence to CC BY-SA 4.0 if redistributed; their photographer is Michael T Balonek. The Budapest images are documented on Commons as CC0, photographer Vauia Rex. See `SOURCES.md`.

The SHA-256 checksums are generated *after* the real bytes are retrieved. A repeatable fixture should retain the resulting full ZIP rather than silently redownload originals that Wikimedia Commons might later update.

## Validation

Run, from the completed fixture root:

```sh
shasum -a 256 -c SHA256SUMS.txt
```

The download step requires Python 3.9+ and working internet access. Its default destination is only the extracted folder; it does not modify your project or personal photo library.
