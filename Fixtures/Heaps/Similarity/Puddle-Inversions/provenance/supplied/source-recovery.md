# Source recovery and provenance notes

**Observed 2026-11-02** through a web-retrieved Wikimedia Commons category page (the page's crawl timestamp was about 3 weeks earlier):

- Name: `Category:Reflections in puddles`
- URL: https://commons.wikimedia.org/wiki/Category:Reflections_in_puddles
- Visible category page: first alphabetical page, **200 files shown out of 432 direct files**. These are observed **page-reported counts**, not a live independent API inventory.
- Category subcategories visible: `Reflections in puddles by country`; `Sunlight reflections from puddles`. **Neither was traversed for candidates.**
- Date range: **no restriction**. Geography: **no restriction**. Candidate extension gate: JPEG-family `.jpg`/`.JPG`/`.jpeg` only. No score, popularity or image-quality gate.
- Candidate selection: 45 named files manually picked from the first page, with heterogeneity as the motivation, not a systematic/random sample. All dimensions in the CSV are the displayed category-list dimensions, not inspected image headers.

For live enumeration, the local agent *may* use this ordinary MediaWiki Action API query (suggestion, **not executed or tested here**):

```
https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category%3AReflections_in_puddles&cmnamespace=6&cmlimit=max&format=json
```

`cmnamespace=6` means direct file pages only, excluding subcategory objects; page through `continue` / `cmcontinue` to cover any additional results. Wikimedia API parameters and responses may change; the local agent owns its query and source verification. If reproducing the exact candidate proposal, prefer `candidates.csv` over a new category enumeration, as category membership and ordering can change.

The browser available during research could open the category listing but could not fetch the JSON API query, and many individual Commons file-page attempts returned a cache miss. Therefore no machine-generated complete category export, automated licensing dataset, thumbnail contact sheet, or acquired media bytes are included. This is not concealment: the per-row evidence level records which pages were opened.

**Rights evidence rule:** The linked file page is the primary source for author/credit and applicable reuse information. The 19 rows marked `individual file page` have an observed textual license with a link to its terms; for the remaining 26, the license field reads `Not checked`, rather than assuming Commons hosts uniformly licensed photos. The National Media Museum historical image is a distinct no-known-restrictions case; it should not be silently rewritten as CC0 or public domain.

**Still-images rule:** The proposed filenames are JPEG-family and no motion files were selected. This is a title/type gate, not a downloaded-byte audit; local intake verifies MIME, dimensions, and content. All images should retain their native crop. Moving subjects are permissible in a still photograph.
