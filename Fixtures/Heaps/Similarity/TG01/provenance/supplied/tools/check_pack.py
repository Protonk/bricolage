#!/usr/bin/env python3
"""Offline sourcing-package integrity check; makes no Commons requests."""
import csv,hashlib,json
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]

def main():
    records=[json.loads(l) for l in (ROOT/'candidates.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    assert len(records)==152, f'Expected 152 leads, got {len(records)}'
    assert [r['candidate_id'] for r in records]==[f'tg-{i:04d}' for i in range(1,153)]
    assert len({r['commons_title'] for r in records})==len(records)
    groups=json.loads((ROOT/'provenance/discovery_sources.json').read_text())['groups']
    by_url={g['discovery_url']:g for g in groups}
    assert sum(g['candidate_count'] for g in groups)==152
    for r in records:
        assert r['screening_status']=='pending_visual_review' and r['visually_accepted'] is None
        assert not r['image_downloaded'] and not r['preview_path'] and not r['acquired_path']
        assert r['source_independence_confirmed'] is None
        assert r['file_page'].startswith('https://commons.wikimedia.org/wiki/File:')
        assert unquote(r['file_page'].split('/wiki/File:',1)[1]).replace('_',' ')==r['commons_filename']
        assert r['discovery_url'] in by_url
        assert r['preview_acquisition_status']=='not_attempted'
    with (ROOT/'candidates.csv').open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;actual=list(reader)
    assert set(fields)=={k for row in records for k in row}, 'CSV columns miss a JSONL key'
    expected=[{k:'' if r.get(k) is None else str(r[k]) for k in fields} for r in records]
    assert actual==expected, 'JSONL/CSV records differ'
    prompt=json.loads((ROOT/'prompt.json').read_text())
    assert prompt['kind']=='prompt_heap' and prompt['heap']=='Similarity'
    assert prompt['minimum_viable_final_input_count']==30 and prompt['target_count']==65
    assert not any((ROOT/'sources').rglob('*.*')) and not any((ROOT/'previews').rglob('*.*'))
    expected_files={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name!='PACK_SHA256SUMS.txt' and '__pycache__' not in p.parts}
    got=set()
    for entry in (ROOT/'PACK_SHA256SUMS.txt').read_text().splitlines():
        sha,path=entry.split('  ',1)
        file=ROOT/path
        assert file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest()==sha, 'Corrupt package file '+path
        got.add(path)
    assert got==expected_files, (got^expected_files)
    print(f'TG01 source pack OK: {len(records)} unviewed Commons leads, 30-image floor, {len(got)} text/evidence files verified.')
if __name__=='__main__':main()
