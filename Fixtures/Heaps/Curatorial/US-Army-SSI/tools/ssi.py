#!/usr/bin/env python3
"""Single-leaf SSI intake: cached metadata, ordered decisions and byte-preserved media."""
import argparse,csv,fcntl,hashlib,html,json,math,re,shutil
from pathlib import Path
from urllib.parse import urlsplit,unquote
from PIL import Image,ImageDraw,ImageFont,ImageOps
from transport import Client,StopAcquisition,dump,append,sha,safe,utc
ROOT=Path(__file__).resolve().parents[1]
EXT={'JPEG':'jpg','PNG':'png','GIF':'gif','WEBP':'webp','TIFF':'tif'}
TARGET=150

def read(p):return json.loads(p.read_text())
def require(ok,message):
 if not ok:raise ValueError(message)
def clean(v):return html.unescape(re.sub('<[^>]*>','',v)).strip() if v is not None else None
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
  client.api(key,prop='imageinfo|revisions',titles='|'.join(by[c]['frozen_title'] for c in batch),redirects=1,iiprop='url|size|mime|sha1|extmetadata|timestamp|user',iiurlwidth=edge,iiurlheight=edge,rvprop='ids|timestamp|content',rvslots='main')
  print(key,'cached',flush=True)


def evidence(stage='preview',edge=480):
 by=candidates();out={}
 for path in sorted((ROOT/'provenance/api').glob(f'{stage}-{edge}-ranks-*.json')):
  if path.name.endswith('.receipt.json'):continue
  data=read(path);q=data['query'];pages={norm(p['title']):p for p in q['pages']};redirects={norm(r['from']):norm(r['to']) for r in q.get('redirects',[])}
  start,end=map(int,path.stem.split('-')[-2:])
  for cid in order()[start-1:end]:
   original=norm(by[cid]['frozen_title']);title=original;seen=set()
   while title in redirects:
    require(title not in seen,'Redirect loop');seen.add(title);title=redirects[title]
   require(title in pages,'Unresolved title '+title);page=pages[title]
   require(cid not in out,'Overlapping metadata batches for '+cid)
   out[cid]=dict(candidate_id=cid,page=page,metadata_path=str(path.relative_to(ROOT)),metadata_sha256=sha(path),original_title=by[cid]['frozen_title'],redirected=title!=original,stage=stage,requested_edge=edge)
 return out

def selection():
 reviews=read(ROOT/'provenance/design-review.json') if (ROOT/'provenance/design-review.json').exists() else {};ev=evidence();selected=[];ledger=[];designs={};identities={};blocked=False;unresolved=[];provisional=[]
 for rank,cid in enumerate(order(),1):
  r=reviews.get(cid);state='pending';reason='design_or_rights_review_pending';conflicts=[]
  if blocked:reason='earlier_candidate_unreviewed'
  elif len(selected)>=TARGET:state='reserve';reason='target_reached'
  elif not r:blocked=True
  elif r['decision']=='pending':reason='explicit_pending_review';unresolved.append(cid)
  elif r['decision']=='exclude':state='excluded';reason=r['reason'];conflicts=r.get('conflicts_with',[])
  else:
   require(r['decision']=='eligible' and r['design_key'] and r['design_basis'] and r['rights_basis'],'Missing acceptance evidence')
   require(cid in ev,'Missing metadata');ii=ev[cid]['page']['imageinfo'][0];keys=[('pageid',ev[cid]['page']['pageid']),('sha1',ii['sha1'])]
   conflicts=sorted({identities[k] for k in keys if k in identities})
   if conflicts:state='excluded';reason='duplicate_source_identity'
   elif r['design_key'] in designs:state='excluded';reason='design_already_selected';conflicts=[designs[r['design_key']]]
   else:
    state='selected';reason='first_eligible_distinct_design_in_seeded_order';selected.append(cid);designs[r['design_key']]=cid
    if unresolved:provisional.append(cid)
    for k in keys:identities[k]=cid
  ledger.append(dict(candidate_id=cid,rank=rank,decision=state,reason=reason,conflicts_with=conflicts,provisional=cid in provisional))
 return dict(target=TARGET,seed=read(ROOT/'provenance/intake/ordering.json')['seed'],snapshot_sha256=read(ROOT/'provenance/intake/inventory.json')['snapshot_sha256'],pending_policy='Explicit pending decisions do not block later reviewed candidates; later selections remain provisional. Unreviewed gaps still require review.',unresolved_prior_candidates=unresolved,provisional_selected=provisional,selected=selected,decisions=ledger,counts={s:sum(r['decision']==s for r in ledger) for s in ['selected','excluded','reserve','pending']})

def dimensions(path,edge):
 with Image.open(path) as im:
  require(getattr(im,'n_frames',1)==1,'Animated media unsupported');require(im.format in EXT,'Unsupported decoded format');im.load();require(max(im.size)<=edge*1.5,'Decoded rendition exceeds nominal edge by over 50%')
  return dict(width=im.width,height=im.height,format=im.format,mode=im.mode,has_alpha=('A' in im.getbands() or 'transparency' in im.info),exif_orientation=im.getexif().get(274,1))

def media(stage,start,end,edge,limit):
 ev=evidence(stage,edge);client=Client(ROOT);selected=set(selection()['selected']) if stage=='source' else None;count=0
 for rank,cid in enumerate(order(),1):
  if not start<=rank<=end or (selected is not None and cid not in selected):continue
  receipt_path=ROOT/f'provenance/{stage}-receipts/{cid}.json'
  if receipt_path.exists():
   r=read(receipt_path)
   if sha(safe(ROOT,r['path']))!=r['sha256']:client.stop(dict(utc=utc(),kind='cache-validation',candidate_id=cid,error='Cached media changed',path=r['path']))
   continue
  require(cid in ev,'Metadata missing for '+cid);e=ev[cid];page=e['page'];require('imageinfo' in page,'Missing imageinfo: '+cid);ii=page['imageinfo'][0];url=ii.get('thumburl');original=ii['url']
  if not ii['mime'].startswith('image/'):
   dump(ROOT/f'provenance/unavailable/{cid}-{stage}-{edge}.json',dict(candidate_id=cid,stage=stage,requested_edge=edge,metadata_path=e['metadata_path'],reason='Non-image original outside supported single-image input scope; no media request made.'));print(cid,'unsupported original',ii['mime'],flush=True);continue
  if not url and ii['mime']!='image/svg+xml' and max(ii['width'],ii['height'])<=edge:url=original
  require(url,'No API rendition: '+cid)
  unscaled=unquote(urlsplit(url).path)==unquote(urlsplit(original).path)
  if unscaled and (ii['mime']=='image/svg+xml' or max(ii['width'],ii['height'])>edge):
   dump(ROOT/f'provenance/unavailable/{cid}-{stage}-{edge}.json',dict(candidate_id=cid,stage=stage,requested_edge=edge,metadata_path=e['metadata_path'],reason='API offered an SVG or oversized unscaled original; no media request made. Explicit alternate API rendition required.'));print(cid,'unavailable at',edge,flush=True);continue
  if stage=='source':
   pe=evidence()[cid];pi=pe['page']['imageinfo'][0];require(ii['sha1']==pi['sha1'] and page['pageid']==pe['page']['pageid'],'Identity changed after review');require(ii['extmetadata']==pi['extmetadata'],'Rights/description metadata changed after review')
  part,event=client.fetch(url,stage,cid,f'previews/partials/{cid}-{stage}-{edge}.part')
  try:
   measured=dimensions(part,edge)
   require(ii['mime']!='image/svg+xml' or (not unscaled and measured['format']=='PNG'),'SVG must use API-provided PNG rendition')
  except Exception as error:
   client.stop(dict(utc=utc(),kind='decode',candidate_id=cid,stage=stage,error=str(error),response_complete=True,partial_path=str(part.relative_to(ROOT)),sha256=sha(part),metadata_path=e['metadata_path']))
  dest=ROOT/('sources' if stage=='source' else 'previews/tiles')/(cid+'.'+EXT[measured['format']]);dest.parent.mkdir(parents=True,exist_ok=True);require(not dest.exists(),'Unreceipted media already exists');part.replace(dest)
  dump(receipt_path,dict(candidate_id=cid,rank=rank,path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=dest.stat().st_size,url=url,requested_edge=edge,rendition='api_reported_unscaled_original' if unscaled else 'api_returned_rendition',original_mime=ii['mime'],original_sha1=ii['sha1'],pageid=page['pageid'],canonical_title=page['title'],metadata_path=e['metadata_path'],metadata_sha256=e['metadata_sha256'],api_reported_width=ii['width'] if unscaled else ii.get('thumbwidth'),api_reported_height=ii['height'] if unscaled else ii.get('thumbheight'),returned_mime=event['headers'].get('content-type'),response=event,**measured));count+=1;print(rank,cid,stage,measured['format'],measured['width'],measured['height'],flush=True)
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
  name=f'previews/review-evidence/ranks-{group[0][0]:04d}-{group[-1][0]:04d}.jpg';path=ROOT/name;require(not path.exists(),'Preserve existing sheet');path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path,quality=92);print(name)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['metadata','media','sheets','select','acknowledge']);p.add_argument('--diagnosis');p.add_argument('--stage',choices=['preview','source'],default='preview');p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=10);p.add_argument('--edge',type=int,choices=[320,480,640,1280,1600],default=480);p.add_argument('--limit',type=int,default=1);a=p.parse_args()
 lock=ROOT/'previews/intake.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 with lock.open('a') as stream:
  fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if a.command=='metadata':metadata(a.stage,a.start,a.end,a.edge)
  elif a.command=='media':require(a.limit>0,'Bounded positive limit required');media(a.stage,a.start,a.end,a.edge,a.limit)
  elif a.command=='sheets':sheets(a.start,a.end)
  elif a.command=='acknowledge':Client(ROOT).acknowledge(a.diagnosis)
  else:
   value=selection();dump(ROOT/'provenance/intake/selection.json',value);print(value['counts'])
if __name__=='__main__':main()
