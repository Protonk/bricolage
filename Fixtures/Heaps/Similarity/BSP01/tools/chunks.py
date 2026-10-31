#!/usr/bin/env python3
"""Run a bounded number of 12-image chunks; stop on any unhealthy result."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stage',choices=['preview','source'],required=True)
p.add_argument('--chunks',type=int,required=True)
a=p.parse_args()
if not 1<=a.chunks<=12:p.error('chunks must be 1..12')
for n in range(a.chunks):
    if (ROOT/'provenance/last_transport_error.json').exists():raise SystemExit('Recorded failure: no new request')
    result=subprocess.run([sys.executable,str(ROOT/'tools/acquire.py'),'--stage',a.stage,'--limit','12','--preview-edge','480','--user-agent','HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'])
    if result.returncode:raise SystemExit(result.returncode)
    records=[json.loads(l) for l in (ROOT/'candidates.jsonl').read_text().splitlines()]
    key='preview_path' if a.stage=='preview' else 'acquired_path'
    pending=[r for r in records if not r.get(key) and (a.stage=='preview' or r['screening_status']=='accept') and r.get('preview_acquisition_status' if a.stage=='preview' else 'source_acquisition_status')!='unavailable_metadata']
    unavailable=[r for r in records if not r.get(key) and (a.stage=='preview' or r['screening_status']=='accept') and r.get('preview_acquisition_status' if a.stage=='preview' else 'source_acquisition_status')=='unavailable_metadata']
    print(f'Completed chunk {n+1}; {len(pending)} eligible candidates pending, {len(unavailable)} without a usable API rendition for {a.stage}.',flush=True)
    if not pending:break
    time.sleep(3)
