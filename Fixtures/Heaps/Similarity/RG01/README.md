# RG01 — Small warm-colored things in big green places

Photographs with small red accents in predominantly green outdoor scenes.

Fixture ID: `hazy-rg01-v1`; kind: `prompt_heap`.
The manifest lists **31 inputs**.

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/RG01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/RG01/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Images and records

**Status: 31-image starter heap acquired and checked.** All 107 supplied Commons
leads were reviewed at thumbnail scale: 31 selected, 69 rejected, and seven
warm-color fallbacks deferred. The original target was roughly 70 photographs
(50–80); this first pass is smaller because many leads lacked the intended green
context. No additional search or expansion beyond the supplied leads was performed.

The prompt is **a salient red object within a predominantly green outdoor
environment**, with incidental people allowed. This is a visual impression, not
provenance-based similarity, ground-truth pairs, or a semantic router cluster.
Original framing and colors are retained. Some selected images have large accents,
muted reds, paths, sky or buildings; per-image choices remain inspectable judgments.

### Contents and lineage

- `images/`: 31 flat, opaque comparison inputs, copied unchanged from acquired bytes.
- `sources/`: 31 preserved Commons renditions, named by their original candidate IDs.
- `manifest.json` / `manifest.csv`: matching image records; stored dimensions,
  EXIF orientation, format and byte hashes are measured from the actual downloads.
- [SOURCES.md](SOURCES.md) / `sources.csv`: file-specific attribution, licenses,
  source pages, acquired URLs and processing notes.
- [provenance/intake/prompt.json](provenance/intake/prompt.json): selection intent, actual count and shortfall.
- [provenance/reviews.json](provenance/reviews.json): every decision, visual reason,
  preview hash, creator/license evidence and limits of the independence review.
- [provenance/import-map.json](provenance/import-map.json): candidate → Commons
  identity → acquired rendition → stable opaque input, including original SHA-1.
- `provenance/commons/`, `downloads/`, `status/`, and `requests.jsonl`: cached
  metadata, acquisition receipts and request history.
- `previews/candidates/` and `previews/contact-sheets/`: all 107 small previews;
  `previews/selected-01.jpg` and `selected-02.jpg`: final selected contact sheets.
- `previews/hazy-rg01-v1.zip`: local package with inputs, preserved renditions,
  manifests, credits, textual provenance and selected contact sheets.

`provenance/intake/candidates.csv` and `provenance/intake/candidates.jsonl` contain the updated screening/acquisition
state. Their supplied versions and the original source index/README are retained
under `provenance/supplied-*`. Candidate IDs identify lead rows. Stable input
identities derive from Commons page ID and original file SHA-1, not a subject label.
All image assets and the ZIP remain in Git-ignored asset directories.

### Similarity and compatibility

The image/source columns follow the other fixtures, but `kind=prompt_heap` is
explicit. Each image has its own source identity; `scene_id` is empty. Source
identities do not group similar images. `probes.csv` is header-only and
`selections.json` has no expected pairs. One numbered batch lists the 31 inputs.

The existing experiment checker accepts only `derivatives` and `multiview` and
requires a nonempty focused pair selection. RG01 therefore uses the local
validator below; it is not mislabeled as a derivative set to satisfy that checker.
No application, comparison, or router code was changed for this collection.

Selected original SHA-1s are distinct. Previews, titles, descriptions and creators
were compared to exclude apparent duplicates or related views. One of two
similar hibiscus images by the same creator was rejected. The two selected photos
by Graham Horn describe different scenes in Ireland and Wales. Independence is
not proven by a URL, differing hashes or this limited audit, so
`source_independence_confirmed` remains null. Licenses are recorded from Commons'
file-specific metadata, with the raw evidence retained.

### Commons acquisition

The downloader identifies itself as
`HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib`. It uses the
[imageinfo API](https://www.mediawiki.org/wiki/API:Imageinfo), requests one file's
metadata at a time with `maxlag=5`, and waits at least three seconds between
requests. It caches metadata and media, makes no concurrent requests, uses no
credentials, and never guesses media paths. A process lock prevents overlapping
runs. These choices follow the [API etiquette](https://www.mediawiki.org/wiki/API:Etiquette)
and [User-Agent guidance](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy).

Small previews precede review; larger renditions require a recorded acceptance,
visual reason, provenance review and license review. The first preview and first
larger rendition were piloted individually. Requests use only API-returned URLs.
Huge originals and responses over 12 MiB are refused. The nominal maximum edge
is 1600px, but Commons returned cached sizes: actual maximum edges range from
640 to 1920px. No image was locally resized to conceal this discrepancy.

Any HTTP/access/rate-limit, API, or transport error records a persistent
`provenance/STOP.json` and stops without retrying. HTTP failures retain status,
headers and `Retry-After`. Subsequent invocations refuse network access until the
stop record has been diagnosed. Completed files and receipts remain cached across
interruptions or machine sleep; an unreceipted partial file is not silently reused.

This acquisition completed **276 requests, all HTTP 200**, transferring 21,548,523
response-body bytes (metadata, 107 previews and 31 selected renditions). There
were no retries or access/rate-limit failures. This is a record of this run, not
a promised rate entitlement.

### Local checks and reproduction

Use an isolated Python environment with Pillow 12.0.0; it is the only third-party
dependency. From the repository root:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/RG01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/RG01/tools/heap.py check
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Similarity/RG01/tools -p test_commons.py
```

`commons.py previews --limit 1` and `commons.py acquire --limit 1` default to a
single-candidate pilot; `--limit 107` visits the supplied list, with cached results
reused. These commands do not discover new candidates or change review decisions.
`contact_sheets.py` renders cached previews locally. Contact sheets use macOS
Arial; this affects previews only, not input bytes.

`heap.py assemble` constructs a fresh `previews/heap-build-v1/` from cached accepted
renditions, validates it, and refuses an existing stage. `heap.py publish` refuses
existing published outputs. `heap.py archive` creates the ZIP without replacing
an existing one. No command removes assets or silently overwrites a completed heap.

[Validation](provenance/validation.json) covers 31 inputs / 62 image and source
files, hashes, decodability, measured dimensions, CSV/JSON agreement, source copies,
batch coverage, distinct original SHA-1s and empty pair expectations. All final
images were inspected on the selected contact sheets. Five offline downloader
tests cover cache use, failure stopping, URL/path restrictions, and oversized
original refusal. No similarity measurements were run.
