#!/usr/bin/env python3
"""Compare PI01 source identities with every other current leaf through the source index; no network.

The index (Fixtures/INDEX.csv) is generated from active manifests, source
catalogs and import maps, so a new publication audits all current collections
without naming them. The result is written once as a frozen record; nothing
re-resolves it later. Exact identity checks only: a different title, hash,
date or creator never establishes capture independence.
"""

from pathlib import Path as _LayoutPath
import sys as _layout_sys
_layout_root = next(p for p in _LayoutPath(__file__).resolve().parents if (p/'tools/fixture_layout.py').is_file())
_layout_sys.path.insert(0, str(_layout_root/'tools'))

import csv
import json
from urllib.parse import unquote
from common import ROOT, load_records

FIXTURES = _layout_root
LEAF = ROOT.resolve().relative_to(FIXTURES.resolve()).as_posix()

def normalized(title):
    return unquote(title).removeprefix('File:').replace('_',' ').casefold().strip()

def main():
    index=FIXTURES/'INDEX.csv'
    with index.open(newline='',encoding='utf-8') as stream:rows=[r for r in csv.DictReader(stream) if r['leaf']!=LEAF]
    previous={key:{} for key in ('title','pageid','original_sha1','byte_sha256')}
    def add(kind,value,where):
        if value is not None and str(value).strip():
            value=normalized(value) if kind=='title' else str(value)
            previous[kind].setdefault(value,set()).add(where)
    inventories={}
    for r in rows:
        where=r['leaf']+'/'+r['file'];inventories.setdefault(r['leaf'],dict(leaf=r['leaf'],fixture=r['fixture_id'],inputs=0))['inputs']+=1
        add('byte_sha256',r['byte_sha256'],where);add('title',r['title'],where);add('pageid',r['page_id'],where);add('original_sha1',r['original_sha1'],where)
    candidates=load_records();seen={key:{} for key in previous};collisions=[];within=[]
    for r in candidates:
        values=dict(title=r.get('commons_api_title') or r['commons_title'],pageid=r.get('commons_pageid'),original_sha1=r.get('original_sha1'),byte_sha256=r.get('acquired_sha256'))
        for kind,value in values.items():
            if value is None:continue
            value=normalized(value) if kind=='title' else str(value)
            if value in previous[kind]:collisions.append(dict(candidate_id=r['candidate_id'],decision=r['screening_status'],identity=kind,previous=sorted(previous[kind][value])))
            for other in seen[kind].get(value,[]):within.append(dict(candidate_ids=[other,r['candidate_id']],identity=kind))
            seen[kind].setdefault(value,[]).append(r['candidate_id'])
    accepted={r['candidate_id'] for r in candidates if r['screening_status']=='accept'}
    blockers=[r for r in collisions if r['candidate_id'] in accepted]+[r for r in within if set(r['candidate_ids'])<=accepted]
    selected=[r for r in candidates if r['candidate_id'] in accepted]
    output=dict(status='failed' if blockers else 'passed',index=str(index.relative_to(FIXTURES.parent)),inventories=list(inventories.values()),candidates=len(candidates),accepted=len(selected),acquired=sum(bool(r.get('acquired_path')) for r in selected),
        available_previous_identities={k:len(v) for k,v in previous.items()},collisions_with_previous=collisions,duplicate_candidate_identities=within,blocking_collisions=blockers,
        limitations='Exact identity checks only, against the source index as generated when this audit ran. Different titles, hashes, dates or creators do not establish capture independence. Visual and possible-sequence review is recorded separately in provenance/source-review.json.')
    (ROOT/'provenance/identity-audit.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
    if blockers:raise SystemExit(1)

if __name__=='__main__':main()
