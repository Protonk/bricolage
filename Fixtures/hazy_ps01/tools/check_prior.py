#!/usr/bin/env python3
"""Report possible cross-heap overlaps against SUPPLIED local prior inventories.

Does not claim independence when there is no match. Does not change review
status, because distinct filenames and credits do not prove distinct captures.
"""
import argparse,csv,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse,unquote
from common import ROOT,load_records,atomic_write

def identify_title(v):
    if not isinstance(v,str) or not v:return None
    if v.startswith('File:'):return v.replace('_',' ')
    if 'commons.wikimedia.org' in v and '/wiki/File:' in v:
        return unquote(v.split('/wiki/',1)[-1]).replace('_',' ')
    return None

def iter_rows(path):
    if path.suffix.lower()=='.csv':
        with path.open(newline='',encoding='utf-8-sig') as f:yield from csv.DictReader(f)
        return
    obj=path.read_text(encoding='utf-8')
    if path.suffix.lower()=='.jsonl':
        for line in obj.splitlines():
            if line.strip():
                d=json.loads(line)
                if isinstance(d,dict):yield d
        return
    if path.suffix.lower()=='.json':
        d=json.loads(obj)
        if isinstance(d,list):
            for x in d:
                if isinstance(x,dict):yield x
        if isinstance(d,dict):
            for key in ('images','sources','candidates','records'):
                if isinstance(d.get(key),list):
                    for x in d[key]:
                        if isinstance(x,dict):yield x
        return
    raise ValueError(f'Unsupported inventory format: {path}')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prior',action='append',type=Path,required=True,help='repeat for prior candidates.jsonl, sources.csv, manifest.json etc')
    args=p.parse_args()
    current=load_records()
    known={}
    for r in current:
        for prop in ('commons_title','file_page','source_origin_url','original_sha1','acquired_sha256','preview_sha256'):
            value=r.get(prop)
            normalized=identify_title(value) if prop in ('commons_title','file_page') else value
            if normalized:
                known.setdefault((prop,normalized),[]).append(r['candidate_id'])
    findings=[];total_rows=0
    for path in args.prior:
        for record in iter_rows(path):
            total_rows+=1
            title=None
            for prop in ('commons_title','file_page','commons_file_page','source_url','original_url'):
                x=identify_title(record.get(prop))
                if x:title=x;break
            for prop,value in [('commons_title',title),('source_origin_url',record.get('source_origin_url')),
                               ('original_sha1',record.get('original_sha1')),
                               ('acquired_sha256',record.get('acquired_sha256') or record.get('byte_sha256') or record.get('sha256'))]:
                if not value:continue
                for key in ((prop,value),):
                    if key in known:
                        findings.append({'inventory':str(path),'candidate_ids':known[key], 'match_field':prop,
                            'match_value':value,'prior_record_identifier':record.get('candidate_id') or record.get('file') or record.get('source_filename')})
    result={'utc':datetime.now(timezone.utc).isoformat(),
            'prior_inventories_supplied':[str(x) for x in args.prior],
            'prior_rows_read':total_rows,'flags':findings,
            'interpretation':'Matches require manual exclusion or provenance investigation. No matches never establish independence.'}
    output=ROOT/'provenance/cross_heap_checks.json'
    atomic_write(output,json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8'))
    print(f'{total_rows} earlier rows checked; {len(findings)} potential overlaps; report: {output}')
    if findings:
        for f in findings:print(f"  {','.join(f['candidate_ids'])}: {f['match_field']} matches {f['prior_record_identifier']}")

if __name__=='__main__':main()
