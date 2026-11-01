#!/usr/bin/env python3
"""The three scoped Commons-category additions: offline evidence and bounded intake.

Transport and media/thumbnail mechanics adapted from active Evan-Amos/Botanical
intakes. This module serves only the three handoff leaves; it is not heap discovery.
"""
import argparse, csv, fcntl, hashlib, html, json, math, re, shutil, sys, tempfile
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs
from PIL import Image, ImageDraw, ImageFont, ImageOps
from transport import Client, StopAcquisition, dump, append, sha, safe, utc
ROOT = None
EXT = {'JPEG':'jpg','PNG':'png','GIF':'gif','WEBP':'webp','TIFF':'tif'}
TARGET = 50
SUPPORTED_MIME = {'image/jpeg','image/png','image/gif','image/webp','image/tiff','image/svg+xml'}
SLUGS = ('Rocks-in-Thin-Section', 'Stone-Hand-Axes', 'Ex-Libris')

def read(p):return json.loads(p.read_text())

def require(ok,message):
 if not ok:raise ValueError(message)

def clean(v):
 if v is None:return None
 v=re.sub(r'<(style|script)\b[^>]*>.*?</\1>', '', v, flags=re.I|re.S)
 return html.unescape(re.sub('<[^>]*>','',v)).strip()

def norm(s):return s.replace('_',' ').removeprefix('File:')

def order():return read(ROOT/'provenance/intake/ordering.json')['candidate_ids']

def candidates():return {r['candidate_id']:r for r in read(ROOT/'provenance/intake/inventory.json')['candidates']}

def metadata_path(stage,edge,start,end):return f'provenance/api/{stage}-{edge}-ranks-{start:04d}-{end:04d}.json'

def metadata(stage,start,end,edge):
 ids=order();by=candidates();client=Client(ROOT)
 require(1<=start<=end<=len(ids),'Invalid rank interval')
 for first in range(start,end+1,10):
  last=min(first+9,end);batch=ids[first-1:last]
  key=Path(metadata_path(stage,edge,first,last)).stem
  data=client.api(key,prop='imageinfo|revisions',titles='|'.join(by[c]['frozen_title'] for c in batch),redirects=1,iiprop='url|size|mime|sha1|extmetadata|timestamp|user',iiurlwidth=edge,iiurlheight=edge,rvprop='ids|timestamp|content',rvslots='main')
  try:current_metadata(data)
  except ValueError as error:client.stop(dict(utc=utc(),kind='metadata-validation',error=str(error),metadata_path=metadata_path(stage,edge,first,last)))
  print(key,'cached',flush=True)

def evidence(stage='preview',edge=480):
 by=candidates();out={}
 for path in sorted((ROOT/'provenance/api').glob(f'{stage}-{edge}-ranks-*.json')):
  if path.name.endswith('.receipt.json'):continue
  data,_,_=api_receipt(path);current_metadata(data);q=data['query'];pages={norm(p['title']):p for p in q['pages']};redirects={norm(r['from']):norm(r['to']) for r in q.get('redirects',[])}
  start,end=map(int,path.stem.split('-')[-2:])
  for cid in order()[start-1:end]:
   original=norm(by[cid]['frozen_title']);title=original;seen=set()
   while title in redirects:
    require(title not in seen,'Redirect loop');seen.add(title);title=redirects[title]
   require(title in pages,'Unresolved title '+title);page=pages[title]
   require(cid not in out,'Overlapping metadata batches for '+cid)
   out[cid]=dict(candidate_id=cid,page=page,metadata_path=str(path.relative_to(ROOT)),metadata_sha256=sha(path),original_title=by[cid]['frozen_title'],redirected=title!=original,stage=stage,requested_edge=edge)
 return out

def dimensions(path,edge):
 with Image.open(path) as im:
  require(getattr(im,'n_frames',1)==1,'Animated media unsupported');require(im.format in EXT,'Unsupported decoded format');im.load();require(max(im.size)<=edge*1.5,'Decoded rendition exceeds nominal edge by over 50%')
  return dict(width=im.width,height=im.height,format=im.format,mode=im.mode,has_alpha=('A' in im.getbands() or 'transparency' in im.info),exif_orientation=im.getexif().get(274,1))

def media(stage,start,end,edge,limit,unreviewed_only=False):
 require(not unreviewed_only or stage=='preview','Unreviewed-only applies to previews')
 reviewed=read(ROOT/'provenance/work-review.json') if unreviewed_only and (ROOT/'provenance/work-review.json').exists() else {}
 ev=evidence(stage,edge);client=Client(ROOT);selected=set(selection()['selected']) if stage=='source' else None;count=0
 for rank,cid in enumerate(order(),1):
  if not start<=rank<=end or cid in reviewed or (selected is not None and cid not in selected):continue
  receipt_path=ROOT/f'provenance/{stage}-receipts/{cid}.json'
  if receipt_path.exists():
   r=read(receipt_path)
   if sha(safe(ROOT,r['path']))!=r['sha256']:client.stop(dict(utc=utc(),kind='cache-validation',candidate_id=cid,error='Cached media changed',path=r['path']))
   continue
  require(cid in ev,'Metadata missing for '+cid);e=ev[cid];page=e['page'];require('imageinfo' in page,'Missing imageinfo: '+cid);ii=page['imageinfo'][0];url=ii.get('thumburl');original=ii['url']
  if ii['mime'] not in SUPPORTED_MIME:
   dump(ROOT/f'provenance/unavailable/{cid}-{stage}-{edge}.json',dict(candidate_id=cid,stage=stage,requested_edge=edge,metadata_path=e['metadata_path'],reason='Unsupported original MIME outside single-image scope; no arbitrary page/frame extraction or media request.'));print(cid,'unsupported original',ii['mime'],flush=True);continue
  if not url and ii['mime']!='image/svg+xml' and max(ii['width'],ii['height'])<=edge:url=original
  require(url,'No API rendition: '+cid)
  unscaled=unquote(urlsplit(url).path)==unquote(urlsplit(original).path)
  if unscaled and (ii['mime']=='image/svg+xml' or max(ii['width'],ii['height'])>edge):
   dump(ROOT/f'provenance/unavailable/{cid}-{stage}-{edge}.json',dict(candidate_id=cid,stage=stage,requested_edge=edge,metadata_path=e['metadata_path'],reason='API offered an SVG or oversized unscaled original; no media request made. Explicit alternate API rendition required.'));print(cid,'unavailable at',edge,flush=True);continue
  if stage=='source':
   pe=evidence()[cid];pi=pe['page']['imageinfo'][0];require(ii['sha1']==pi['sha1'] and page['pageid']==pe['page']['pageid'],'Identity changed after review');require(ii['extmetadata']==pi['extmetadata'],'Rights/description metadata changed after review')
  reused=None
  preview_receipt=ROOT/f'provenance/preview-receipts/{cid}.json'
  if stage=='source' and preview_receipt.exists():
   cached=read(preview_receipt)
   if cached['url']==url:
    part=safe(ROOT,cached['path']);event=cached['response']
    if sha(part)!=cached['sha256'] or event.get('sha256')!=cached['sha256'] or not event.get('response_complete'):
     client.stop(dict(utc=utc(),kind='cache-validation',candidate_id=cid,error='Cached preview bytes/receipt changed',path=cached['path']))
    reused=str(preview_receipt.relative_to(ROOT))
  if reused is None:part,event=client.fetch(url,stage,cid,f'previews/partials/{cid}-{stage}-{edge}.part')
  try:
   measured=dimensions(part,edge)
   if unscaled:require(hashlib.sha1(part.read_bytes()).hexdigest()==ii['sha1'],'Unscaled original SHA-1 differs')
   require(ii['mime']!='image/svg+xml' or (not unscaled and measured['format']=='PNG'),'SVG must use API-provided PNG rendition')
  except Exception as error:
   client.stop(dict(utc=utc(),kind='decode',candidate_id=cid,stage=stage,error=str(error),response_complete=True,partial_path=str(part.relative_to(ROOT)),sha256=sha(part),metadata_path=e['metadata_path']))
  dest=ROOT/('sources' if stage=='source' else 'previews/tiles')/(cid+'.'+EXT[measured['format']]);dest.parent.mkdir(parents=True,exist_ok=True);require(not dest.exists(),'Unreceipted media already exists')
  if reused:shutil.copyfile(part,dest)
  else:part.replace(dest)
  dump(receipt_path,dict(candidate_id=cid,rank=rank,path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=dest.stat().st_size,url=url,requested_edge=edge,rendition='api_reported_unscaled_original' if unscaled else 'api_returned_rendition',original_mime=ii['mime'],original_sha1=ii['sha1'],pageid=page['pageid'],canonical_title=page['title'],metadata_path=e['metadata_path'],metadata_sha256=e['metadata_sha256'],api_reported_width=ii['width'] if unscaled else ii.get('thumbwidth'),api_reported_height=ii['height'] if unscaled else ii.get('thumbheight'),returned_mime=event['headers'].get('content-type'),response=event,**({'reused_preview_receipt':reused} if reused else {}),**measured));count+=1;print(rank,cid,stage,measured['format'],measured['width'],measured['height'],flush=True)
  if count>=limit:break

def sheets(start,end):
 rows=[];by=candidates()
 for rank,cid in enumerate(order(),1):
  path=ROOT/f'provenance/preview-receipts/{cid}.json'
  if start<=rank<=end and path.exists():rows.append((rank,cid,read(path)))
 require(rows,'No preview receipts');font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
 for offset in range(0,len(rows),20):
  group=rows[offset:offset+20];canvas=Image.new('RGB',(1280,math.ceil(len(group)/4)*285),'#e8e8e8');draw=ImageDraw.Draw(canvas)
  for i,(rank,cid,r) in enumerate(group):
   with Image.open(ROOT/r['path']) as im:
    im=ImageOps.exif_transpose(im).convert('RGBA');im.thumbnail((300,237));x=(i%4)*320;y=(i//4)*285;canvas.paste(im,(x+(320-im.width)//2,y+(240-im.height)//2),im)
   title=norm(by[cid]['frozen_title']);draw.text((x+5,y+242),f'{rank:04d}  {cid[:8]}',fill='black',font=font);draw.text((x+5,y+263),title[:32],fill='black',font=font)
  name=f'previews/review-evidence/ranks-{group[0][0]:04d}-{group[-1][0]:04d}.jpg';path=ROOT/name;require(not path.exists(),'Preserve existing sheet');path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path,quality=92);dump(ROOT/f'provenance/inspection-sheets/{path.stem}.json',dict(path=name,sha256=sha(path),candidate_ids=[cid for _,cid,_ in group],preview_sha256={cid:r['sha256']for _,cid,r in group}));print(name)

def config():
 return next(r for r in read(ROOT/'provenance/supplied/CATEGORIES.json')['leaves']if r['leaf_directory']==ROOT.name)

def cid_for(slug,title):
 return hashlib.sha256(('hazy-curatorial-triplet-v1\n'+slug+'\n'+title).encode('utf-8')).hexdigest()[:20]

def ordered(rows,seed):
 return sorted([r['candidate_id']for r in rows],key=lambda cid:(hashlib.sha256((seed+'\n'+cid).encode('utf-8')).hexdigest(),cid))

def current_metadata(data):
 require(not any(k in data for k in ('error','warnings')),'Failed metadata reply')
 pages=data.get('query',{}).get('pages',[]);require(pages,'Missing metadata pages')
 if 'continue'in data:
  c=data['continue'];require(len(pages)==1 and set(c)=={'iistart','continue'}and c['continue']=='||revisions' and len(pages[0].get('imageinfo',[]))==1 and len(pages[0].get('revisions',[]))==1 and c['iistart']<pages[0]['imageinfo'][0]['timestamp'],'Unresolved metadata continuation')

def api_receipt(path,expected=None):
 receipt=read(path.with_suffix('.receipt.json'));require(receipt['status']==200 and receipt['response_complete'],'Incomplete API receipt')
 require(receipt['sha256']==sha(path) and receipt['bytes_received']==path.stat().st_size,'API bytes changed')
 u=urlsplit(receipt['url']);require(u.scheme=='https'and u.netloc=='commons.wikimedia.org'and u.path=='/w/api.php','Unexpected API URL')
 params=parse_qs(u.query);require(all(params.get(k)==[v]for k,v in dict(action='query',format='json',formatversion='2',maxlag='5').items()),'API convention differs')
 if expected is not None:require(params=={k:[str(v)]for k,v in dict(action='query',format='json',formatversion=2,maxlag=5,**expected).items()},'API query differs')
 data=read(path);require(not any(k in data for k in ('error','warnings')),'Failed API response')
 return data,receipt,params

def category_query(category):
 return dict(list='categorymembers',cmtitle=category,cmtype='file',cmprop='ids|title|type',cmsort='sortkey',cmlimit=500)

def population(fetch=False):
 conf=config();by_id={};titles={};responses=[];counts={};client=Client(ROOT)
 for cat_no,cat in enumerate(conf['categories'],1):
  continuation={};seen=set();n=1;rows=[]
  while True:
   key=f'category-{cat_no}-{n:04d}';query=dict(**category_query(cat['title']),**continuation)
   if fetch:client.api(key,**query)
   path=ROOT/f'provenance/api/{key}.json';data,receipt,_=api_receipt(path,query)
   require('categorymembers'in data.get('query',{}),'Missing category result');batch=data['query']['categorymembers'];rows.extend(batch)
   responses.append(dict(category=cat['title'],path=str(path.relative_to(ROOT)),sha256=sha(path),url=receipt['url'],utc=receipt['utc'],rows=len(batch),continuation=data.get('continue')))
   if 'continue'not in data:break
   continuation=data['continue'];require(set(continuation)=={'continue','cmcontinue'},'Unexpected continuation');token=json.dumps(continuation,sort_keys=True);require(token not in seen,'Repeated continuation');seen.add(token);n+=1
  require(len({r['pageid']for r in rows})==len(rows),'Repeated category page ID');counts[cat['title']]=len(rows)
  for r in rows:
   require(r['ns']==6 and r['title'].startswith('File:')and r['type']=='file','Non-File category member')
   pid=r['pageid'];title=r['title'];require(title not in titles or titles[title]==pid,'One title maps to multiple IDs');titles[title]=pid
   if pid not in by_id:by_id[pid]=dict(candidate_id=cid_for(ROOT.name,title),frozen_title=title,category_pageid=pid,memberships=[],raw_rows=[])
   require(by_id[pid]['frozen_title']==title,'One ID has inconsistent titles');by_id[pid]['memberships'].append(cat['title']);by_id[pid]['raw_rows'].append(dict(category=cat['title'],row=r))
 rows=sorted(by_id.values(),key=lambda r:r['category_pageid']);require(len({r['candidate_id']for r in rows})==len(rows),'Candidate ID collision')
 return dict(leaf=ROOT.name,depth=0,method='Direct categorymembers File union by page ID; all continuations exhausted',categories=[r['title']for r in conf['categories']],category_counts=counts,actual_count=len(rows),responses=responses,candidate_id_algorithm='First 20 hex SHA-256 of UTF-8 hazy-curatorial-triplet-v1 + LF + leaf slug + LF + exact frozen File title',candidates=rows)

def freeze():
 require(not(ROOT/'provenance/intake/inventory.json').exists(),'Population already frozen')
 try:inventory=population(True)
 except ValueError as error:Client(ROOT).stop(dict(utc=utc(),kind='population-validation',error=str(error)))
 dump(ROOT/'provenance/intake/inventory.json',inventory);seed=config()['seed'];dump(ROOT/'provenance/intake/ordering.json',dict(seed=seed,algorithm='Ascending SHA-256 of UTF-8 seed + LF + candidate ID; tie-break candidate ID',candidate_ids=ordered(inventory['candidates'],seed)))
 dump(ROOT/'provenance/intake/selection.json',selection());print(ROOT.name,inventory['category_counts'],'unique',inventory['actual_count'],flush=True)

def selection():
 technical=read(ROOT/'provenance/technical-exclusions.json')if(ROOT/'provenance/technical-exclusions.json').exists()else{}
 reviews=read(ROOT/'provenance/work-review.json')if(ROOT/'provenance/work-review.json').exists()else{};ev=evidence();chosen=[];ledger=[];works={};identities={};blocked=False;unresolved=[];provisional=[]
 for rank,cid in enumerate(order(),1):
  r=reviews.get(cid);state='unreviewed';reason='pending_visual_review';conflicts=[]
  if len(chosen)>=TARGET:state='reserve';reason='target_reached'
  elif blocked:reason='earlier_candidate_unreviewed'
  elif cid in technical:state='excluded';reason=technical[cid]['reason']
  elif not r:blocked=True
  elif 'reject'in(r['visual_decision'],r['provenance_decision'],r['rights_decision']):state='excluded';reason=r['reason'];conflicts=r.get('conflicts_with',[])
  elif r['visual_decision']=='defer'or r['provenance_decision']=='defer'or r['rights_decision']=='defer':state='deferred';reason=r['reason'];unresolved.append(cid)
  else:
   require(r['visual_decision']=='accept'and r['provenance_decision']=='accept'and r['rights_decision']=='accept','Incomplete acceptance')
   page=ev[cid]['page'];ii=page['imageinfo'][0];keys=[('pageid',page['pageid']),('sha1',ii['sha1'])];conflicts=sorted({identities[k]for k in keys if k in identities})
   if conflicts:state='excluded';reason='duplicate_source_identity'
   elif r.get('work_key')and r['work_key']in works:state='excluded';reason='known_work_or_specimen_already_selected';conflicts=[works[r['work_key']]]
   else:
    state='selected';reason='next_eligible_in_fixed_order';chosen.append(cid)
    if r.get('work_key'):works[r['work_key']]=cid
    if unresolved:provisional.append(cid)
    for k in keys:identities[k]=cid
  ledger.append(dict(candidate_id=cid,rank=rank,decision=state,reason=reason,conflicts_with=conflicts,provisional=cid in provisional))
 return dict(target=TARGET,seed=config()['seed'],inventory_sha256=sha(ROOT/'provenance/intake/inventory.json'),pending_policy='Explicit defer advances provisionally; unreviewed gaps block selection; source transfer failures never replace selections.',selected=chosen,unresolved_prior_candidates=unresolved,provisional_selected=provisional,decisions=ledger,counts={s:sum(r['decision']==s for r in ledger)for s in ['selected','excluded','deferred','reserve','unreviewed']})

def record_reviews(sheet,values):
 records=read(ROOT/'provenance/work-review.json')if(ROOT/'provenance/work-review.json').exists()else{};ev=evidence();ids=[];sheet_path=safe(ROOT,sheet);require(sheet_path.is_file(),'Missing inspected sheet')
 for number,v in values.items():
  rank=int(number);cid=order()[rank-1];require(cid not in records,'Review already exists; preserve corrections explicitly')
  e=ev[cid];page=e['page'];ii=page.get('imageinfo',[{}])[0];m=ii.get('extmetadata',{});get=lambda k:clean(m.get(k,{}).get('value'))
  receipt=read(ROOT/f'provenance/preview-receipts/{cid}.json');require(sha(ROOT/receipt['path'])==receipt['sha256'],'Changed inspected preview')
  r=dict(candidate_id=cid,rank=rank,reviewed_at=utc(),visual_decision=v['visual_decision'],visual_reason=v['visual_reason'],provenance_decision=v['provenance_decision'],rights_decision=v['rights_decision'],reason=v['reason'],work_key=v.get('work_key'),work_basis=v['work_basis'],conflicts_with=v.get('conflicts_with',[]),preview_path=receipt['path'],preview_sha256=receipt['sha256'],inspection_evidence=sheet,inspection_sha256=sha(sheet_path),metadata_path=e['metadata_path'],metadata_sha256=e['metadata_sha256'],pageid=page.get('pageid'),canonical_title=page['title'],original_sha1=ii.get('sha1'),file_timestamp=ii.get('timestamp'),file_page_revision=page.get('revisions',[{}])[0].get('revid'),reported_artist=get('Artist'),original_creator=v.get('original_creator'),photographer=v.get('photographer'),digitizer=v.get('digitizer'),creator_basis=v.get('creator_basis','Reported Commons Artist retained; original maker, photographer and digitizer not separated without role evidence.'),uploader_current_file_revision=ii.get('user'),credit=get('Credit'),license=get('LicenseShortName'),license_url=get('LicenseUrl'),restrictions=get('Restrictions'),rights_basis=v['rights_basis'])
  for axis in ['visual_decision','provenance_decision','rights_decision']:require(r[axis]in('accept','reject','defer'),'Unknown review decision')
  if r['rights_decision']=='accept':require(r['license']and(r['license_url']or r['license']in('Public domain','No restrictions')),'Missing rights evidence')
  require(page.get('pageid')==candidates()[cid]['category_pageid'],'Frozen/resolved identity differs; explicit reconciliation needed')
  records[cid]=r;ids.append(cid)
 dump(ROOT/'provenance/work-review.json',records);append(ROOT/'provenance/inspection-log.jsonl',dict(utc=utc(),candidate_ids=ids,evidence=sheet,sha256=sha(sheet_path),purpose='Thumbnail scope and documented object/work repetition only; no aesthetic or similarity screening.'))
 dump(ROOT/'provenance/intake/selection.json',selection());print('Recorded',len(ids),'reviews;',selection()['counts'])

def network_action(function,*args):
 try:return function(*args)
 except (ValueError,OSError)as error:Client(ROOT).stop(dict(utc=utc(),kind='intake-validation',operation=function.__name__,error=f'{type(error).__name__}: {error}'))

def main(root=None):
 global ROOT
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['freeze','metadata','media','sheets','review','select','acknowledge','check','build','audit']);p.add_argument('--leaf',choices=SLUGS);p.add_argument('--stage',choices=['preview','source'],default='preview');p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=10);p.add_argument('--edge',type=int,choices=[320,480,640,1280,1600],default=480);p.add_argument('--limit',type=int,default=1);p.add_argument('--sheet');p.add_argument('--diagnosis');a=p.parse_args();ROOT=root or Path(__file__).resolve().parents[1]/a.leaf
 require(ROOT.name in SLUGS,'Expected one of the three scoped leaves')
 lock=ROOT.parent/'previews/three-category-intake.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 with lock.open('a')as stream:
  fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if a.command in('freeze','metadata','media'):
   require(not any((ROOT.parent/s/'provenance/last_transport_error.json').exists()for s in SLUGS),'Unacknowledged transport failure in triplet; network stopped')
  if a.command=='freeze':freeze()
  elif a.command=='metadata':network_action(metadata,a.stage,a.start,a.end,a.edge)
  elif a.command=='media':require(a.limit>0,'Positive bounded media limit');network_action(media,a.stage,a.start,a.end,a.edge,a.limit)
  elif a.command=='sheets':sheets(a.start,a.end)
  elif a.command=='review':record_reviews(a.sheet,json.load(sys.stdin))
  elif a.command=='acknowledge':Client(ROOT).acknowledge(a.diagnosis)
  elif a.command=='select':dump(ROOT/'provenance/intake/selection.json',selection());print(selection()['counts'])
  else:
   import three_category_publish as publish
   publish.run(sys.modules[__name__],a.command)

if __name__=='__main__':main()
