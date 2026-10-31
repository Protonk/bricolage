#!/usr/bin/env python3
"""Create/apply a thumbnail-review worksheet, never infer visual labels."""
import argparse,csv,sys,fcntl
from datetime import datetime,timezone
from pathlib import Path
from common import ROOT,load_records,save_records,append_jsonl

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template',action='store_true',help='regenerate blank review worksheet')
    p.add_argument('--apply',type=Path,help='read decisions from CSV worksheet')
    args=p.parse_args()
    records=load_records()
    if args.apply:
        rows=list(csv.DictReader(args.apply.open('r',encoding='utf-8-sig',newline='')))
        ids={r['candidate_id']:r for r in records}
        if len(rows)!=len({r.get('candidate_id') for r in rows}):
            raise SystemExit('Duplicate candidate ID in review worksheet')
        updates=[]
        for rec in rows:
            cid=rec.get('candidate_id','').strip();decision=rec.get('decision','').strip().lower()
            if not decision:continue
            if cid not in ids:raise SystemExit(f'Unknown ID: {cid}')
            if decision not in ('accept','reject','defer'):
                raise SystemExit(f'Invalid decision for {cid}: {decision}')
            why=rec.get('visual_reason','').strip()
            if not why:raise SystemExit(f'{cid}: decision needs a short visual reason')
            row=ids[cid]
            if not row.get('preview_path') or not (ROOT/row['preview_path']).is_file():
                raise SystemExit(f'{cid}: cannot make visual decision without acquired preview bytes')
            updates.append((row,rec,decision,why))
        # Validate all before touching anything. A failed row must not partially apply.
        for row,rec,decision,why in updates:
            old=row.get('screening_status')
            row['screening_status']=decision
            row['visually_accepted']=True if decision=='accept' else False if decision=='reject' else None
            row['visual_reason']=why
            row['visual_reviewed_at']=datetime.now(timezone.utc).isoformat()
            row['visual_evidence']=row['preview_path']
            if rec.get('review_notes','').strip():row['review_notes']=rec['review_notes'].strip()
            if rec.get('source_independence_notes','').strip():row['source_independence_notes']=rec['source_independence_notes'].strip()
            # No automatic 'independent' status from an accepted visual review.
            append_jsonl(ROOT/'provenance/review_log.jsonl',{'utc':row['visual_reviewed_at'],
                'candidate_id':row['candidate_id'],'old':old,'new':decision,'visual_reason':why,
                'preview_path':row['preview_path']})
        save_records(records)
        print(f'Applied {len(updates)} visual decisions; acquisition statuses unchanged.')
    else:
        path=ROOT/'provenance/review_template.csv'
        with path.open('w',encoding='utf-8',newline='') as f:
            fields=['candidate_id','decision','visual_reason','review_notes','source_independence_notes']
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
            for row in records:w.writerow({'candidate_id':row['candidate_id'],'decision':'','visual_reason':'','review_notes':'','source_independence_notes':row.get('source_independence_notes') or ''})
        print('Generated',path)

if __name__=='__main__':
    lock=ROOT/'previews/acquisition.lock';lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as stream:
        try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Acquisition is running; review not applied.')
        sys.exit(main())
