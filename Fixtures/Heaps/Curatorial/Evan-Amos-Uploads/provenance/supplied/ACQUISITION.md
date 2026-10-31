# Local acquisition and integration

1. **Inspect and pin the active repo implementation.** Use
   `Fixtures/Heaps/Curatorial/POTY/tools/` and
   `Fixtures/Heaps/Curatorial/US-Army-SSI/tools/` as *reference* for conservative
   Commons transport, full-category records, `curatorial_heap` manifests,
   SVG/raster handling, validation, and provenance. Adapt instead of wholesale
   copying a workflow that caps creators, selects 150, or discards related
   images. This is an exhaustive member import.

2. **Freeze the population once.** Use `SCOPE.md`, preserve API response bytes,
   and construct `inventory.json`. Record a deterministic ordering of all
   direct File identities (e.g. by preserved title, with ID tie-breaker), but
   **do not sample**. Produce `selection.json` showing all members: exactly the
   three user exclusions and *every other member selected for acquisition*.
   Count, include, and preserve different angles, related captures, JPEG/PNG
   renditions, crops, motherboard pictures, console pictures, etc. Do not apply
   SSI's design deduplication or POTY's one-creator cap.

3. **Record individual Commons rights and identity evidence.** For included
   files, query `imageinfo` with original URL, size, MIME, SHA-1, timestamp,
   user, file-specific license/artist/credit information, and any source-page
   evidence relevant to provenance. Cache exact response bytes and compare
   resolved identities with frozen members. Keep unknown authors/null license
   URLs honest. A rights issue or unavailable supported rendition blocks that
   item; it does *not* silently remove it or authorize a substitute image.

4. **Pilot one small acquisition**, then proceed in paced serial chunks with
   truthful User-Agent identification, `maxlag=5`, cache/hash validation, no
   automatic redirects or retries, and an explicit stop latch on HTTP/API errors,
   incomplete bodies, and decode failures. HTTP 200 with a timed-out body is
   incomplete; preserve status, relevant headers, bytes/partial bodies and the
   failed identity. Resume only after deliberate diagnostic acknowledgement.
   Preserve category and metadata API replies in `provenance/`, media partials
   in `previews/partials/`, and completed rendition bytes in `sources/`.

5. **Download one bounded rendition per included File page.** Ask the Commons
   API for a nominal maximum edge around **1600px**, and use only its returned
   `thumburl` or a reported unscaled original *within bounds*. Record the
   requested size, API-reported size, real decoded dimensions, type, byte count,
   hash, and exact URL. Commons may return a different rendition bucket. If an
   unscaled original exceeds the requested bound, explicitly ask the API for a
   smaller rendition (e.g. 1280px) with a separate cache entry; do not construct
   a CDN URL or fetch huge originals as fallback. Fully decode and hash before
   marking complete; do not crop, reframe, upscale, color-adjust, or re-encode
   downloaded bytes. If the File source is SVG, use an API-returned PNG rendition,
   preserving the SVG's original identity in metadata.

6. **Build one leaf** at `Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/`.
   `images/` contains one opaque, byte-identical comparison input per successfully
   acquired included File page; `sources/` contains the matching downloaded
   bytes. Preserve `inventory.json`, `selection.json`, provenance and licenses,
   full source/import mapping, manifests, CSVs, hashes, contact sheets, batches,
   and receipts in the established leaf-relative layout. Use `kind=curatorial_heap`,
   `relation_kind=curatorial_selected`, empty `probes.csv`, and zero expected
   pairs or known-shift families. **No sub-heaps.**

7. **Report explicitly**: membership count, exactly-three excluded identities,
   total included, acquired, pending/blocked (by cause), and any source revisions,
   URL/identity discrepancies or previous-heap overlaps. A partial publication
   must not be called a complete all-members import. Do not add replacement
   files to compensate for missing inputs. Preserve old output if an explicit
   subsequent repair/publish is needed.

This acquisition is *not* visual curation. Contact sheets may be used to inspect
asset correctness, but not to select aesthetically representative examples.
