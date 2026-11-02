#!/usr/bin/env python3
"""Compare PI01 source identities with every other current local leaf; no network.

Prior leaves are discovered from their active manifests, so a new publication
audits all current collections. Exact identity checks only: a different title,
hash, date or creator never establishes capture independence.
"""

from pathlib import Path as _LayoutPath
import sys as _layout_sys
_layout_root = next(p for p in _LayoutPath(__file__).resolve().parents if (p/'tools/fixture_layout.py').is_file())
_layout_sys.path.insert(0, str(_layout_root/'tools'))
from fixture_layout import discover, evidence_path

import csv
import hashlib
import json
from urllib.parse import unquote, urlparse, parse_qs
from common import ROOT, load_records

FIXTURES = _layout_root

def normalized(title):
    return unquote(title).removeprefix('File:').replace('_',' ').casefold().strip()

def main():
    inventories=[]
    previous={key:{} for key in ('title','pageid','original_sha1','byte_sha256')}
    def add(kind,value,where):
        if value is not None and str(value).strip():
            value=normalized(value) if kind=='title' else str(value)
            previous[kind].setdefault(value,set()).add(where)
    for root in discover(FIXTURES):
        if root.resolve()==ROOT.resolve():continue
        manifest=json.loads((root/'manifest.json').read_text());name=manifest['fixture_id']
        with (root/'sources.csv').open(newline='') as f:sources=list(csv.DictReader(f))
        inventories.append(dict(fixture=name,leaf=root.relative_to(FIXTURES).as_posix(),inputs=len(manifest['images']),sources=len(sources),manifest_sha256=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()))
        for row in manifest['images']:add('byte_sha256',row['byte_sha256'],name+'/'+row['file'])
        for row in sources:
            where=name+'/sources/'+row['source_filename'];add('byte_sha256',row['source_sha256'],where)
            url=row['source_url']
            if 'commons.wikimedia.org' in url:
                if '/wiki/File:' in url:add('title',url.split('/wiki/',1)[1],where)
                if row['subject'].startswith('File:'):add('title',row['subject'],where)
                for pageid in parse_qs(urlparse(url).query).get('curid',[]):add('pageid',pageid,where)
        imports=root/'provenance/import-map.json'
        if imports.exists():
            records=json.loads(imports.read_text())
            if isinstance(records,list):
                for r in records:
                    if not isinstance(r,dict):continue
                    where=name+'/'+str(r.get('final_file') or r.get('file') or '?')
                    add('title',r.get('canonical_title') or r.get('commons_api_title') or r.get('commons_title'),where)
                    add('pageid',r.get('pageid') or r.get('commons_pageid'),where)
                    add('original_sha1',r.get('original_sha1'),where)
                    add('byte_sha256',r.get('acquired_sha256'),where)
        if name=='hazy-meme-fixtures-v0':
            for r in json.loads((evidence_path(root, 'source-manifest.json')).read_text())['sources']:
                add('title',r['upstream_title'],name+'/'+r['file'])
                if (root/r['file']).is_file():add('original_sha1',hashlib.sha1((root/r['file']).read_bytes()).hexdigest(),name+'/'+r['file'])
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
    output=dict(status='failed' if blockers else 'passed',inventories=inventories,candidates=len(candidates),accepted=len(selected),acquired=sum(bool(r.get('acquired_path')) for r in selected),
        available_previous_identities={k:len(v) for k,v in previous.items()},collisions_with_previous=collisions,duplicate_candidate_identities=within,blocking_collisions=blockers,
        limitations='Exact identity checks only. Different titles, hashes, dates or creators do not establish capture independence. Prior upstream SHA-1/page IDs are compared where locally available; no claim of complete upstream inventories. Visual and possible-sequence review is recorded separately in provenance/source-review.json.')
    (ROOT/'provenance/identity-audit.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
    if blockers:raise SystemExit(1)

if __name__=='__main__':main()
