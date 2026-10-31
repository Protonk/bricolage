#!/usr/bin/env python3
"""Make a review CSV from candidate IDs, or apply a filled review CSV."""
import argparse,csv,json,sys
from pathlib import Path
from acquire import ROOT,jsonlines,save_records

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--template',action='store_true',help='create blank review worksheet (default)')
    ap.add_argument('--apply',type=Path,help='apply filled CSV decisions; never infer labels')
    args=ap.parse_args()
    records=jsonlines(ROOT/'candidates.jsonl')
    if args.apply:
        rows=list(csv.DictReader(args.apply.open(encoding='utf-8-sig',newline='')))
        ids={r['candidate_id']:r for r in records}
        if len(rows)!=len(set(r['candidate_id'] for r in rows)):raise SystemExit('duplicate ID in decisions CSV')
        touched=0
        for r in rows:
            id=r['candidate_id'];decision=r.get('decision','').strip().lower()
            if not decision:continue
            if id not in ids:raise SystemExit(f'unknown ID {id}')
            if decision not in ('accept','reject','defer'):raise SystemExit(f'invalid decision for {id}: {decision}')
            reason=r.get('visual_reason','').strip()
            if not reason:raise SystemExit(f'missing visual reason for {id}')
            d=ids[id]
            if decision in ('accept','reject') and not (d.get('preview_path') and (ROOT/d['preview_path']).is_file()):
                raise SystemExit(f'{id}: cannot {decision} without bundled preview bytes')
            d['screening_status']=decision
            d['visually_accepted']=decision=='accept' if decision!='defer' else None
            d['visual_reason']=reason
            d['review_notes']=r.get('review_notes') or d.get('review_notes')
            if r.get('source_independence_notes'):d['source_independence_notes']=r['source_independence_notes']
            flag=r.get('source_independence_confirmed','').strip().lower()
            if flag in ('yes','true'):d['source_independence_confirmed']=True
            elif flag in ('no','false'):d['source_independence_confirmed']=False
            touched+=1
        save_records(records)
        print(f'Applied {touched} decisions; CSV regenerated from the JSONL records.')
    else:
        path=ROOT/'provenance'/'review_template.csv'
        with path.open('w',newline='',encoding='utf8') as f:
            fields=['candidate_id','decision','visual_reason','review_notes','source_independence_confirmed','source_independence_notes']
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
            for r in records:w.writerow({'candidate_id':r['candidate_id'],'decision':'','visual_reason':'','review_notes':'','source_independence_confirmed':'','source_independence_notes':''})
        print('Created',path)

if __name__=='__main__':main()
