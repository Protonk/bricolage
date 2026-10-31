# Scope: exact category membership, minus three exact titles

Category: `Category:Media uploaded by Evan Amos`

Canonical category page:
https://commons.wikimedia.org/wiki/Category:Media_uploaded_by_Evan_Amos

Use MediaWiki **`list=categorymembers`**, with `cmtitle` set to that exact
category, `cmtype=file` (File namespace), `cmlimit=max`, `cmprop=ids|title|timestamp`,
`format=json`, `formatversion=2`, and `maxlag=5`. **No recursive walk.**

Initial API request (the local client should construct arguments using URL
encoding, rather than string-concatenating a CDN/media URL):

https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&list=categorymembers&cmtitle=Category%3AMedia_uploaded_by_Evan_Amos&cmtype=file&cmprop=ids%7Ctitle%7Ctimestamp&cmlimit=max&maxlag=5

The observed category page reports 136 direct file pages; check for 133 after
subtracting the three exclusions. If the API responds with `continue`/
`cmcontinue`, follow it serially, even if the first response is shorter than
expected. A `200` response containing an API `error` (including `maxlag`) must
STOP with diagnostics rather than be interpreted as an empty category.

Freeze and retain raw API response bytes, request parameters, UTC retrieval
time, SHA-256 of each response, each File page ID/title, API continuation tokens,
and the final list. Do not rely on category-page textual counts alone for the
published snapshot. Report if the three exclusion titles are absent, renamed,
redirected, or no longer members; preserve their exact user-supplied spellings.
Exclude precisely the matching File identities, not other files because they
appear to be related.

For every member, keep the **supplied category-member title**, original page ID,
resolved Commons title/page ID (if different), file-page URL, original file
SHA-1, and acquired rendition SHA-256 separately. Make stable IDs from the
frozen File identity and check for collisions. Never recompute an identity
because an API response normalizes spaces or a title redirects.

The inventory should mark each of the three exclusions `excluded_by_user`, with
no other *selection* exclusion codes. Every other member stays `included`, with
independent acquisition/rights statuses such as `complete`, `pending`, or
`blocked` as justified. Keep exact external title matching explicit, rather
than overbroad prefix, substring, or object-level matching.

**Important distinction:** This category is titled “Media uploaded by Evan Amos,”
not “Every photograph authored by Evan Amos.” Do not infer that uploader,
photographer, copyright holder, or image creator are the same person. File-specific
Commons records are the evidence for those roles.
