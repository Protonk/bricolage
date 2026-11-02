#!/usr/bin/env python3
"""Record file-specific rights evidence and relationship decisions for accepted candidates; no network.

Reads the preserved preview API replies for every visually accepted candidate,
records the license statement Commons reports with the reply's hash, and
applies the hand-written relationship notes in provenance/relationship-notes.json.
A license outside the recognized free-license forms is reported and left
unreviewed; the acquisition tool then refuses that source. Visual decisions are
never changed here: a relationship deferral keeps `visually_accepted` and
records the deferral separately.
"""
import hashlib, json, re, sys
from datetime import datetime, timezone
from common import ROOT, load_records, save_records, append_jsonl, atomic_write
from acquire import html_plain

RECOGNIZED = [
    (re.compile(r'^CC BY(-SA)? \d\.\d( [a-z]{2})?$'), 'Creative Commons attribution license as reported by Commons'),
    (re.compile(r'^CC0$'), 'CC0 public-domain dedication as reported by Commons'),
    (re.compile(r'^Public domain$'), 'Commons public-domain statement; the collection does not independently establish term expiry'),
    (re.compile(r'^No (known )?(copyright )?restrictions$'), "Institutional 'no known copyright restrictions' statement; not an independent public-domain determination"),
]


def recognize(short_name):
    for pattern, basis in RECOGNIZED:
        if short_name and pattern.match(short_name):
            return basis
    return None


def main():
    records = load_records()
    notes_path = ROOT / 'provenance/relationship-notes.json'
    notes = json.loads(notes_path.read_text()) if notes_path.exists() else dict(relationship_reviews=[], attribution_requests={})
    deferred = {cid: review for review in notes['relationship_reviews'] for cid in review.get('defer', [])}
    now = datetime.now(timezone.utc).isoformat()
    license_reviews = []; problems = []
    for row in records:
        if row.get('visually_accepted') is not True:
            continue
        if row['candidate_id'] in deferred and row['screening_status'] == 'accept':
            old = row['screening_status']; row['screening_status'] = 'defer'
            row['provenance_decision'] = 'defer'; row['provenance_decision_reason'] = deferred[row['candidate_id']]['finding']
            append_jsonl(ROOT / 'provenance/review_log.jsonl', dict(utc=now, candidate_id=row['candidate_id'], old=old, new='defer', basis='relationship review', finding=deferred[row['candidate_id']]['finding']))
        if row['screening_status'] != 'accept':
            continue
        path = ROOT / row['api_preview_metadata_path']; raw = path.read_bytes()
        meta = json.loads(raw)['query']['pages'][0]['imageinfo'][0]['extmetadata']
        short = html_plain(meta.get('LicenseShortName', {}).get('value'))
        basis = recognize(short)
        if basis is None:
            problems.append((row['candidate_id'], short)); continue
        entry = dict(candidate_id=row['candidate_id'], metadata_path=row['api_preview_metadata_path'], metadata_sha256=hashlib.sha256(raw).hexdigest(),
                     license=short, license_url=html_plain(meta.get('LicenseUrl', {}).get('value')), creator=html_plain(meta.get('Artist', {}).get('value')),
                     copyrighted=html_plain(meta.get('Copyrighted', {}).get('value')), attribution_required=html_plain(meta.get('AttributionRequired', {}).get('value')),
                     attribution_text=html_plain(meta.get('Attribution', {}).get('value')), basis=basis)
        request = notes.get('attribution_requests', {}).get(row['candidate_id'])
        if request: entry['attribution_request'] = request
        license_reviews.append(entry)
        if row.get('license') != short:
            problems.append((row['candidate_id'], f'record license {row.get("license")!r} differs from metadata {short!r}')); continue
        row['license_review'] = f"File-specific Commons imageinfo extmetadata reports {short}; {basis}. Creator and terms URL retained when supplied; raw response bytes preserved at {row['api_preview_metadata_path']}. This records Commons' rights statement, not an independent legal determination."
        row['provenance_review'] = 'Compared the acquired previews, titles, creators, places and reported dates across the 45 supplied leads, and checked available identities against every other local leaf inventory (identity-audit.json). Siblings withheld by the sourcing partner are listed in provenance/supplied/preselected-rejects.md. No known shared capture retained; exhaustive upstream independence remains unverified. See source-review.json.'
        row['source_independence_reviewed_at'] = now
    if problems:
        for cid, what in problems: print(f'UNRESOLVED {cid}: {what}', file=sys.stderr)
    save_records(records)
    review = dict(review_basis='Actual acquired previews, file-specific Commons imageinfo/extmetadata for each accepted candidate, the supplied handoff notes, and the cross-leaf identity audit. Visual selection is distinct from source identity and rights checking.',
                  relationship_reviews=[{k: v for k, v in r.items()} for r in notes['relationship_reviews']],
                  license_reviews=license_reviews, unresolved=[dict(candidate_id=c, problem=w) for c, w in problems], source_independence_confirmed=None,
                  limitations='Commons license short names are recorded as reported; attribution requests on file pages are quoted where the handoff or metadata noted them. No claim of complete upstream capture-series investigation.')
    atomic_write(ROOT / 'provenance/source-review.json', (json.dumps(review, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    visual = [dict(candidate_id=r['candidate_id'], decision=r['screening_status'], visually_accepted=r.get('visually_accepted'), visual_reason=r.get('visual_reason'),
                   **({'provenance_decision_reason': r['provenance_decision_reason']} if r.get('provenance_decision') else {})) for r in records]
    atomic_write(ROOT / 'provenance/visual-review.json', (json.dumps(visual, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    print(f'license reviews: {len(license_reviews)}; deferred by relationship: {sum(1 for r in records if r.get("provenance_decision")=="defer")}; unresolved: {len(problems)}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
