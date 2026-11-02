# Recovering ignored media

Git holds every record and no image. If the local `images/`, `sources/` and
`previews/` directories are lost, this page is the contract between the
repository and whoever fetches the bytes again. The repository describes each
input completely and reports what it finds; it does not fetch, retry or decide.

## What the records give you

[INDEX.csv](INDEX.csv) has one row per active input. For recovery the columns
that matter are `leaf`, `file`, `byte_sha256`, `width`, `height`, `format`,
`origin`, `page_id`, `original_sha1`, `acquired_url`, `requested_edge`,
`rendition_kind` and `recovery`:

- `commons-api`: the input came from Wikimedia Commons through the API. Query
  `action=query&prop=imageinfo&pageids=PAGE_ID&iiprop=url|sha1|size&iiurlwidth=EDGE&iiurlheight=EDGE`.
  If the reply's `sha1` equals `original_sha1`, the upstream file is unchanged;
  fetch `thumburl` for an `api_returned_rendition` or `url` for an
  `api_reported_unscaled_original`. The leaf's `provenance/api/` replies and
  `acquired_url` show exactly what was fetched before.
- `source-url`: only a page, dataset or download URL is recorded. Read the
  leaf's `sources.csv` and `SOURCES.md` and fetch by hand.
- `regenerate`: a derived input. Restore its family's source first, then run the
  leaf's generator (`tools/generate.py` or `tools/build.py`) as its README says.
- `none`: no upstream location is recorded. The preserved bytes were the only
  copy; a lost input of this kind is gone unless another local copy exists.

Each leaf's `acquire.py`, where it has one, is a worked example of a polite
fetch (identified user agent, `maxlag`, pacing, no retries). It is not a
required tool and may be out of date with the API.

## Four outcomes, and what each means here

Compare what you fetched with the row.

| Outcome | Test | What to do in the repository |
|---|---|---|
| identical | byte hash equals `byte_sha256` | Put the file at `leaf/file` (and at `sources/<source_filename>` when the row is a byte copy of its source). Nothing changes. |
| equivalent | upstream `sha1` equals `original_sha1`, decoded size and format match, bytes differ | Commons re-encodes renditions, so this is common. Accept it with `Fixtures/collection repin INPUT --from FILE --reason "..."`; the receipt records old and new hashes. |
| changed upstream | upstream `sha1` differs | The file was replaced or re-uploaded. Decide whether the current upstream still serves the fixture; if so re-pin with that reason, otherwise leave the input missing. |
| gone | page deleted or not found | Leave the input missing, or remove it with `Fixtures/collection remove` and the reason. |

`Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full` names every
missing or mismatched input. It is the only verdict the repository gives.

## What a re-pin changes

A re-pin keeps the input's path and replaces its bytes. The manifests, checksum
list and index take the new hash; the recorded width, height, orientation and
format must already match, or the command refuses. Decoded-pixel hashes are
cleared because they are unknown. Saved sampler draws that selected the old
bytes become unrepeatable for that image; their records still say what was
drawn. Acquisition records, API replies and import maps stay as published, and
the leaf's publication validator becomes historical.

## What this page does not promise

No script restores a tree. Nothing here handles rate limits, API changes or
partial downloads. The zips under `previews/` and any other local copies are
not part of the contract. A recovery can end with inputs still missing, and the
records are honest about that.
