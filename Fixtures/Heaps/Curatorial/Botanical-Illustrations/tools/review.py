#!/usr/bin/env python3
"""Record explicit rank decisions from stdin JSON; optional inspected evidence path.

Usage: python3 tools/review.py [previews/evidence.jpg] < decisions.json
Existing decisions are never silently overwritten. Unknown roles stay null.
"""
import sys,json
from pathlib import Path
import botanical as b
p=b.ROOT
v=json.load(sys.stdin);f=p/'provenance/work-review.json';records=b.read(f) if f.exists() else {};ev=b.evidence();ids=[]
label_path=p/'provenance/source-publication-labels.json'
labels=b.read(label_path)['work_key_prefix_labels'] if label_path.exists() else {}
for n,value in v.items():
 rank=int(n);cid=b.order()[rank-1];assert cid not in records,cid;e=ev[cid];ii=e['page'].get('imageinfo',[{}])[0];m=ii.get('extmetadata',{});get=lambda k:b.clean(m.get(k,{}).get('value'))
 r=dict(candidate_id=cid,rank=rank,reviewed_at=b.utc(),decision=value['decision'],work_key=value.get('work_key'),work_basis=value['basis'],reason=value.get('reason') or value['basis'],metadata_path=e['metadata_path'],metadata_sha256=e['metadata_sha256'],reported_artist=get('Artist'),original_artist=None,engraver_lithographer=None,publisher=None,digitizer=None,uploader_current_file_revision=ii.get('user'),credit=get('Credit'),license=get('LicenseShortName'),license_url=get('LicenseUrl'),restrictions=get('Restrictions'),rights_basis=None,creator_basis='Reported Artist/author retained; original illustrator versus book author, engraver, publisher and digitizer not assigned without explicit role evidence.')
 for key in ['original_artist','engraver_lithographer','publisher','digitizer','creator_basis','conflicts_with']:
  if key in value:r[key]=value[key]
 matches=[label for prefix,label in labels.items() if (r['work_key'] or '').startswith(prefix)]
 b.require(len(matches)<=1,'Ambiguous publication label')
 r['source_publication_or_collection']=matches[0] if matches else None
 r['source_publication_basis']='Named source in retained work_basis and its bound Commons metadata; abbreviated titles normalize only publication/collection counting.' if matches else 'No publication/collection label assigned; see file-specific work and source evidence.'
 if r['decision']=='eligible':
  assert r['license'] and (r['license_url'] or r['license']=='Public domain')
  r['rights_basis']='File-specific Commons metadata and retained license templates: '+r['license']+'; terms '+(r['license_url'] or 'no URL supplied; retained public-domain claim')+'. Claims are recorded, not independently authenticated; no blanket collection license.'
 if len(sys.argv)>1:
  path=sys.argv[1];r['inspection_evidence']=path;r['inspection_sha256']=b.sha(p/path);ids.append(cid)
 records[cid]=r
b.dump(f,records)
if ids:b.append(p/'provenance/inspection-log.jsonl',dict(utc=b.utc(),candidate_ids=ids,evidence=sys.argv[1],sha256=b.sha(p/sys.argv[1]),purpose='Botanical illustration scope and distinct work/plate identity only; no aesthetic or similarity selection.'))
print('Recorded',len(v),'reviews;',b.selection()['counts'])
