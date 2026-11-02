#!/usr/bin/env python3
"""Create the canonical candidate records from the supplied handoff CSV; no network.

Every supplied column is kept verbatim as a string. The added fields give the
acquisition and review tools their expected names and start every candidate as
unreviewed and unacquired. Refuses to overwrite existing records.
"""
import csv
from common import ROOT, CANON, save_records

SUPPLIED = ROOT / 'provenance/supplied/candidates.csv'


def main():
    if CANON.exists():
        raise SystemExit('Canonical candidates already exist; not overwriting')
    with SUPPLIED.open(newline='', encoding='utf-8') as stream:
        supplied = list(csv.DictReader(stream))
    records = []
    for row in supplied:
        title = row['exact_file_title']
        records.append(dict(row,
            commons_title='File:' + title, commons_filename=title, file_page=row['file_page_url'],
            discovery='category_listing', discovery_url=row['category_listing_url'],
            candidate_basis=row['reason_for_lead'],
            screening_status='pending_visual_review', visually_accepted=None, visual_reason=None,
            image_downloaded=False, source_independence_confirmed=None, contains_people=None,
            creator=None, license=None, license_url=None, license_review=None, provenance_review=None,
            review_notes=None, source_independence_notes=None))
    save_records(records)
    print(f'{len(records)} candidates written to {CANON.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
