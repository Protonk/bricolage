# Commons import provenance

Nine user-downloaded JPEGs were ingested from `hazy-quasi-multiview-v1` on
2026-10-29. They are the Commons thumbnail versions listed in the verification
record, not the full-resolution originals anticipated by the supplied download kit.
The user confirmed that Commons access blocks prevented the intended full-resolution
downloads. All supplied image bytes were preserved.

- `supplied-*` files retain the kit's README, source notes, JSON, and CSV unchanged.
  They describe the intended download process and planned local filenames.
- `import-map.csv` connects manual download names, Commons titles, planned kit
  filenames, preserved sources, canonical inputs, and measured dimensions.
- `thumbnail-verification.json` records the reference URLs, check times, response
  content types and byte counts, SHA-256 hashes, and matched manual filenames.
  All nine downloaded files exactly matched the named reference thumbnail bytes.
  Verification fetched only these named thumbnails for hashing; the fixture uses
  the files supplied by the user.

`image-08.jpg` maps to `Budapest_pride_20250628_143521_1.jpg`; `image-09.jpg`
maps to `Budapest_pride_20250628_143521.jpg`. The mapping does not rely on download
order or a visual guess. Full-resolution original hashes were not validated.

The kit's referenced downloader and generated source metadata were not present
in the supplied folder. The archived files are planning provenance; the set's root
manifest and source catalog describe the actual inputs. Author and license details
are retained from the kit with links to the individual source pages in
[SOURCES.md](../../SOURCES.md).
