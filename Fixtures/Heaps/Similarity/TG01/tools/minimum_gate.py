#!/usr/bin/env python3
"""TG01 minimum-count report. Advisory only: local integration must enforce count >= 30.

Visual acceptance is distinct from transport. A blocked download does not turn
an accepted candidate into a rejection or automatically abandon the contribution.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def classify(rows, root, minimum=30):
    pending=[r for r in rows if r.get('screening_status')=='pending_visual_review']
    accepted=[r for r in rows if r.get('screening_status')=='accept']
    acquired=[]
    for r in accepted:
        name=r.get('acquired_path');digest=r.get('acquired_sha256')
        if r.get('image_downloaded') and name and digest:
            p=(root/name).resolve()
            if root.resolve() not in p.parents or not p.is_file():continue
            if hashlib.sha256(p.read_bytes()).hexdigest()==digest:acquired.append(r)
    if pending:status='pending_visual_review'
    elif len(accepted)<minimum:status='abandon_below_floor'
    elif len(acquired)<minimum:status='acquisition_incomplete'
    else:status='count_gate_met_full_review_still_required'
    return dict(status=status,minimum=minimum,candidates=len(rows),pending_visual=len(pending),accepted=len(accepted),verified_acquired=len(acquired),deferrals=sum(r.get('screening_status')=='defer' for r in rows))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--strict-publish',action='store_true',help='exit nonzero unless verified acquired count >=30 and review closed')
    a=p.parse_args()
    rows=[json.loads(l) for l in (ROOT/'candidates.jsonl').read_text().splitlines() if l.strip()]
    result=classify(rows,ROOT)
    print(json.dumps(result,indent=2))
    if a.strict_publish and result['status']!='count_gate_met_full_review_still_required':return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
