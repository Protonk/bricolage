#!/usr/bin/env python3
"""Offline BSP01 source pack integrity; makes no Wikimedia requests."""
import csv,hashlib,json
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]

def main():
    records=[json.loads(line) for line in (ROOT/'candidates.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(records)==185, f'Expected 185 candidate records, got {len(records)}'
    assert [r['candidate_id'] for r in records]==[f'bsp-{i:04d}' for i in range(1,186)]
    assert len({r['commons_title'].casefold() for r in records})==len(records)
    groups=json.loads((ROOT/'provenance/discovery_sources.json').read_text())['groups']
    by_url={g['discovery_url']:g for g in groups}
    assert len(groups)==13 and sum(g['candidate_count'] for g in groups)==185
    for r in records:
        assert r['screening_status']=='pending_visual_review' and r['visually_accepted'] is None
        assert r['image_downloaded'] is False and not r['preview_path'] and not r['acquired_path']
        assert r['source_independence_confirmed'] is None
        assert r['file_page'].startswith('https://commons.wikimedia.org/wiki/File:')
        assert unquote(r['file_page'].split('/wiki/File:',1)[1]).replace('_',' ')==r['commons_filename']
        assert r['discovery_url'] in by_url
        assert r['preview_acquisition_status']=='not_attempted' and r['source_acquisition_status']=='not_attempted'
    with (ROOT/'candidates.csv').open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;actual=list(reader)
    assert set(fields)=={k for row in records for k in row}, 'CSV columns missing JSONL fields'
    expected=[{k:'' if r.get(k) is None else str(r[k]) for k in fields} for r in records]
    assert actual==expected, 'CSV is not canonical JSONL derivation'
    prompt=json.loads((ROOT/'prompt.json').read_text())
    assert prompt['kind']=='prompt_heap' and prompt['heap']=='Similarity'
    assert prompt['minimum_viable_final_input_count']==30 and prompt['target_count']==65
    assert not any((ROOT/'sources').rglob('*.*')) and not any((ROOT/'previews').rglob('*.*'))
    expected_files={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name!='PACK_SHA256SUMS.txt' and '__pycache__' not in p.parts}
    got=set()
    for entry in (ROOT/'PACK_SHA256SUMS.txt').read_text().splitlines():
        sha,path=entry.split('  ',1);p=ROOT/path
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==sha, 'Corrupt package file: '+path
        got.add(path)
    assert got==expected_files, (got^expected_files)
    print(f'BSP01 source pack OK: {{len(records)}} unseen Commons leads; 30-image floor; {{len(got)}} verified text/evidence files.'.replace('{len(records)}',str(len(records))).replace('{len(got)}',str(len(got))))
if __name__=='__main__': main()
