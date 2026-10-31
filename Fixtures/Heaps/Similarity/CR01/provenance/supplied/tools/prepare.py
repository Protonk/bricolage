#!/usr/bin/env python3
"""Pin and copy acquisition/review helpers from the *active* PS01 repo baseline.

Run inside a local hazy checkout after extracting this package to
Fixtures/hazy_cr01/. Does not touch the previous heap or the network; refuses
changed source blobs or preexisting output scripts.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
BASELINE=HERE.parent/'hazy_ps01'/'tools'
REPO=HERE.parent.parent
PIN=json.loads((HERE/'provenance'/'baseline.json').read_text())
# These scripts do not embed PS01's prompt or final fixture identity.
GENERIC=['common.py','acquire.py','review.py','status.py','test_acquire.py','chunks.py','receipt.py']

def blob_hash(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check-only',action='store_true',help='validate source scripts; do not copy')
    a=ap.parse_args()
    if not (REPO/'AGENTS.md').is_file():
        ap.error('Extract into <local hazy repo>/Fixtures/hazy_cr01 and run there.')
    if not BASELINE.is_dir():
        ap.error('Missing active Fixtures/hazy_ps01/tools/ in local repo; not falling back to archived originals.')
    copies=[]
    for name in GENERIC:
        source=BASELINE/name
        if not source.is_file():raise SystemExit(f'Missing active script: {source}')
        raw=source.read_bytes()
        expected=PIN['active_tool_git_blob_sha1'][name]
        actual=blob_hash(raw)
        if actual!=expected:
            raise SystemExit(f'Active {name} differs from pinned PS01 baseline: {actual} != {expected}. Inspect and adapt deliberately; no silent copying.')
        target=HERE/'tools'/name
        if target.exists():
            if target.read_bytes()!=raw:
                raise SystemExit(f'Existing {target} differs from baseline; refusing overwrite.')
        else:copies.append((source,target))
    if a.check_only:
        print(f'{len(GENERIC)} matching PS01 source scripts verified; {len(copies)} not yet copied.')
        return
    for source,target in copies:
        shutil.copyfile(source,target)
        print(f'Copied {target.name} from active PS01 tool directory.')
    print('Ready for local preview pilot. Next run tests, then acquire one small preview.')
    print('integrate.py and audit.py are intentionally NOT copied unchanged: adapt them for CR01 and current prior inventories.')

if __name__=='__main__':main()
