#!/usr/bin/env python3
"""Offline structural checks for CR01 sourcing pack (no network or media access)."""
import csv, hashlib, io, json
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT=Path(__file__).resolve().parents[1]

def main():
    rs=[json.loads(line) for line in (ROOT/'candidates.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rs)==168, f'Unexpected candidate count: {len(rs)}'
    ids=[r['candidate_id'] for r in rs]
    assert ids==[f'cr-{i:04}' for i in range(1,len(rs)+1)]
    titles=[r['commons_title'] for r in rs]
    assert len(titles)==len(set(titles))
    with (ROOT/'candidates.csv').open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames
        assert set(fields)==set(k for r in rs for k in r), 'CSV header misses canonical JSONL fields'
        actual=list(reader)
    expected=[{k:'' if r.get(k) is None else str(r[k]) for k in fields} for r in rs]
    assert actual==expected,'JSONL/CSV mismatch'
    for r in rs:
        assert r['screening_status']=='pending_visual_review'
        assert r['visually_accepted'] is None and r['image_downloaded'] is False
        assert r['preview_path'] is None and r['acquired_path'] is None
        assert r['source_independence_confirmed'] is None
        assert r['file_page'].startswith('https://commons.wikimedia.org/wiki/File:')
        assert r['discovery_url'].startswith('https://commons.wikimedia.org/wiki/Category:')
        assert unquote(r['file_page'].split('/wiki/File:',1)[1]).replace('_',' ') == r['commons_filename']
    assert not any((ROOT/'previews').rglob('*.jpg'))
    # Textual evidence and tool files are checksummed without making any claim
    # about absent media; partial transfers can be added later by local tools.
    sums=[]
    for row in (ROOT/'PACK_SHA256SUMS.txt').read_text().splitlines():
        digest,name=row.split('  ',1)
        p=ROOT/name
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest, f'Checksum mismatch: {name}'
        sums.append(name)
    expected_files=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name != 'PACK_SHA256SUMS.txt' and not p.name.startswith('.') and '__pycache__' not in p.parts]
    assert set(expected_files)==set(sums), 'Textual sourcing-package checksum coverage mismatch'
    print(f'CR01 sourcing check passed: {len(rs)} title-level leads; zero viewed/acquired media; {len(sums)} checksummed evidence files.')

if __name__=='__main__': main()
