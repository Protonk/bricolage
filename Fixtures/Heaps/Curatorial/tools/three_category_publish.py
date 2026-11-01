"""Offline staging and validation for the three scoped category contributions."""
import csv, hashlib, json, re, shutil, tempfile
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from collections import Counter
import math
from PIL import Image, ImageDraw, ImageOps
from transport import dump, sha, safe
import three_category_audit as audit

IMAGE_FIELDS='file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
SOURCE_FIELDS='family_id source_filename scene_id subject credit_status source_sha256 width height exif_orientation source_url preprocessing view exposure_id original_path'.split()
PROBE_FIELDS='file_a file_b relation interpretation'.split()
e=None

def require(ok,msg):
 if not ok:raise ValueError(msg)
def read(path):return json.loads(path.read_text())
def csv_write(path,rows,fields):
 with path.open('w',newline='')as stream:
  w=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def csv_read(path):
 with path.open(newline='')as stream:return list(csv.DictReader(stream))

def imports():
 out=[];members=e.candidates();evidence=e.evidence();reviews=read(e.ROOT/'provenance/work-review.json')
 for cid in e.selection()['selected']:
  path=e.ROOT/f'provenance/source-receipts/{cid}.json'
  if not path.exists():continue
  r=read(path);page=evidence[cid]['page'];ii=page['imageinfo'][0];review=reviews[cid]
  out.append(dict(**r,source_path=r['path'],final_file='images/'+Path(r['path']).name,family_id=e.ROOT.name.lower()+'-'+cid,frozen_title=members[cid]['frozen_title'],category_pageid=members[cid]['category_pageid'],category_memberships=members[cid]['memberships'],source_url='https://commons.wikimedia.org/wiki/'+quote(page['title'].replace(' ','_'),safe=':/'),file_timestamp=ii['timestamp'],file_page_revision=page['revisions'][0]['revid'],source_independence_confirmed=None,review_metadata_path=review['metadata_path'],review_metadata_sha256=review['metadata_sha256'],**{k:review[k]for k in ['reported_artist','original_creator','photographer','digitizer','creator_basis','uploader_current_file_revision','credit','license','license_url','restrictions','rights_basis','work_key','work_basis','visual_reason','preview_path','preview_sha256']}))
 return out

def records(imported):
 images=[];sources=[]
 for r in imported:
  images.append(dict(file=r['final_file'],batch='batch-1',family_id=r['family_id'],scene_id='',parents=r['family_id'],transformation='source',relation_kind='curatorial_selected',origin_count=1,**{k:r[k]for k in('width','height','exif_orientation','format')},byte_sha256=r['sha256'],pixels_rgb_sha256=''))
  sources.append(dict(family_id=r['family_id'],source_filename=Path(r['source_path']).name,scene_id='',subject=r['canonical_title'],credit_status=f"{r['reported_artist']or'unknown artist'}; {r['license']}",source_sha256=r['sha256'],width=r['width'],height=r['height'],exif_orientation=r['exif_orientation'],source_url=r['source_url'],preprocessing=f"API request {r['requested_edge']}px; {r['rendition']}; decoded {r['width']}x{r['height']} {r['format']}; local byte copy only.",view='',exposure_id='',original_path=r['frozen_title']))
 return images,sources

def events():
 path=e.ROOT/'provenance/http_log.jsonl';return[json.loads(s)for s in path.read_text().splitlines()]if path.exists()else[]

def summary():
 chosen=e.selection();review=read(e.ROOT/'provenance/work-review.json');got={r['candidate_id']for r in imports()};pending=[cid for cid in chosen['selected']if cid not in got];failures=[r for r in events()if r.get('error')]
 return dict(status='complete_acquisition'if not pending and len(got)>=e.TARGET and not(e.ROOT/'provenance/last_transport_error.json').exists()else'partial',selection_status='provisional'if chosen['unresolved_prior_candidates']else'final_for_recorded_order',unique_enumerated=len(e.order()),technical_rejects=len(read(e.ROOT/'provenance/technical-exclusions.json'))if(e.ROOT/'provenance/technical-exclusions.json').exists()else 0,reviewed_previews=len(review),scope_rejects=sum(r['visual_decision']=='reject'for r in review.values()),provenance_or_rights_rejects=sum(r['visual_decision']!='reject'and'reject'in(r['provenance_decision'],r['rights_decision'])for r in review.values()),deferred_reviews=sum('defer'in(r['visual_decision'],r['provenance_decision'],r['rights_decision'])and'reject'not in(r['visual_decision'],r['provenance_decision'],r['rights_decision'])for r in review.values()),visually_eligible=sum(r['visual_decision']=='accept'for r in review.values()),selected=len(chosen['selected']),acquired=len(got),pending_acquisition=len(pending),pending_candidate_ids=pending,selection_exclusions=chosen['counts']['excluded'],pending_selection=chosen['counts']['deferred'],unreviewed=len(e.order())-len(review),unused_reserve=chosen['counts']['reserve'],target=e.TARGET,provisional_selected=len(chosen['provisional_selected']),transport_stops=len(failures),automatic_retries=0)

def credits(imported):
 lines=['# Sources and credits','', 'File-specific Commons metadata and raw file-page revisions are retained. These are source claims, not independent authentication or a blanket collection license. Unassigned roles remain unknown; uploader is separate from creator.','']
 for r in imported:
  lines += [f"## {r['candidate_id']} - {r['canonical_title']}",'',f"- [Source page]({r['source_url']}); [exact acquired rendition]({r['url']}).",f"- Frozen identity: {r['frozen_title']}; page ID {r['category_pageid']}; memberships: {'; '.join(r['category_memberships'])}.",f"- Reported Artist: {r['reported_artist']or'unknown'}; credit: {r['credit']or'unknown'}.",f"- Original creator: {r['original_creator']or'unknown'}; photographer: {r['photographer']or'unknown'}; digitizer: {r['digitizer']or'unknown'}; current file-version uploader: {r['uploader_current_file_revision']or'unknown'}.",f"- Roles: {r['creator_basis']}",f"- Rights claim: {r['license']}; terms: {r['license_url']or'no URL supplied'}; restrictions: {r['restrictions']or'none supplied'}. {r['rights_basis']}",f"- Scope: {r['visual_reason']} Work/specimen key: {r['work_key']or'unknown'}. {r['work_basis']}",f"- Original: {r['original_mime']}, SHA-1 `{r['original_sha1']}`, upload timestamp {r['file_timestamp']}; file-page revision {r['file_page_revision']}.",f"- Acquired: {r['format']}, {r['width']} x {r['height']}, orientation {r['exif_orientation']}, {r['bytes']} bytes; SHA-256 `{r['sha256']}`.",f"- Source `{r['source_path']}`; input `{r['final_file']}`; metadata `{r['metadata_path']}`; review `{r['review_metadata_path']}`.",'']
 return '\n'.join(line.rstrip()for line in '\n'.join(lines).split('\n'))

def related_evidence():
 out=[]
 for cid,item in e.evidence().items():
  page=item['page'];revisions=page.get('revisions',[])
  if not revisions:continue
  text=revisions[0]['slots']['main']['content'];lines=text.splitlines()
  passages=[line for line in lines if re.search(r'other[_ ]versions|other versions|derivative|retouch|original[_ ]file',line,re.I)]
  links=re.findall(r'\[\[(?:File|Image):([^\]|]+)',text,re.I)
  if passages or links:out.append(dict(candidate_id=cid,metadata_path=item['metadata_path'],metadata_sha256=item['metadata_sha256'],file_page_revision=revisions[0]['revid'],passages=passages,file_links=links,interpretation='Links are leads, not proof of the same specimen/work; explicit review decisions are in work-review.json.'))
 return out

def diagnostic_check():
 path=e.ROOT/'provenance/error_acknowledgements.jsonl';acks=[json.loads(s)for s in path.read_text().splitlines()]if path.exists()else[];latch=e.ROOT/'provenance/last_transport_error.json';active=read(latch)if latch.exists()else None;failures=[r for r in events()if r.get('error')]
 for ack in acks:require(ack['diagnosis'].strip()and ack['failure']in failures,'Acknowledgement lacks failure')
 for f in failures:
  require(f==active or any(a['failure']==f for a in acks),'Failure lacks acknowledgement or active latch')
  if f.get('partial_path'):
   path=safe(e.ROOT,f['partial_path']);require(path.exists()and sha(path)==(f.get('partial_sha256')or f.get('sha256')),'Changed failure body')


def check_reviews():
 root=e.ROOT;reviews=read(root/'provenance/work-review.json');evidence=e.evidence();logs=[json.loads(s)for s in(root/'provenance/inspection-log.jsonl').read_text().splitlines()]
 for cid,r in reviews.items():
  require(cid in e.order()and e.order()[r['rank']-1]==cid,'Review rank mismatch');require(r['metadata_path']==evidence[cid]['metadata_path']and r['metadata_sha256']==sha(root/r['metadata_path']),'Review metadata changed')
  require(sha(safe(root,r['preview_path']))==r['preview_sha256']and sha(safe(root,r['inspection_evidence']))==r['inspection_sha256'],'Visual evidence changed')
  sheet=read(root/f"provenance/inspection-sheets/{Path(r['inspection_evidence']).stem}.json");require(cid in sheet['candidate_ids']and sheet['sha256']==r['inspection_sha256']and sheet['preview_sha256'][cid]==r['preview_sha256'],'Preview absent from inspected sheet')
  require(any(cid in log['candidate_ids']and log['evidence']==r['inspection_evidence']and log['sha256']==r['inspection_sha256']for log in logs),'Missing inspection log')
  page=evidence[cid]['page'];ii=page['imageinfo'][0];require(r['pageid']==page['pageid']==e.candidates()[cid]['category_pageid']and r['original_sha1']==ii['sha1'],'Review identity differs')
  get=lambda k:e.clean(ii['extmetadata'].get(k,{}).get('value'))
  require(all(r[k]==get(api)for k,api in [('license','LicenseShortName'),('license_url','LicenseUrl'),('reported_artist','Artist'),('credit','Credit')]),'Review credit/license differs')
  require(all(r[k]in('accept','reject','defer')for k in('visual_decision','provenance_decision','rights_decision'))and all(r[k]for k in('visual_reason','reason','work_basis','rights_basis')),'Incomplete review')
  if r['rights_decision']=='accept':require(r['license']and(r['license_url']or r['license']in('Public domain','No restrictions')),'Rights not supported')
  require(all(x in e.order()and x!=cid for x in r['conflicts_with']),'Invalid related candidate')



# Active catalogs are checked separately from the preserved publication.
from pathlib import Path as _RemovalPath
import sys as _removal_sys
_removal_tools = next(p / 'tools' for p in _RemovalPath(__file__).resolve().parents if (p / 'tools/fixture_layout.py').is_file())
_removal_sys.path.insert(0, str(_removal_tools))
from fixture_removal import publication_artifacts

@publication_artifacts(lambda: e.ROOT)
def check(artifacts=None):
 root=e.ROOT;out=artifacts or root;require(read(root/'provenance/intake/inventory.json')==e.population(),'Population replay differs')
 conf=e.config();ordering=read(root/'provenance/intake/ordering.json');require(ordering['seed']==conf['seed']and ordering['candidate_ids']==e.ordered(read(root/'provenance/intake/inventory.json')['candidates'],conf['seed']),'Ordering differs')
 for name,digest in read(root/'provenance/intake.json')['source_files'].items():require(sha(root/'provenance/supplied'/name)==digest,'Changed handoff')
 require(read(root/'provenance/intake/selection.json')==e.selection(),'Selection differs');check_reviews();diagnostic_check()
 technical=read(root/'provenance/technical-exclusions.json')if(root/'provenance/technical-exclusions.json').exists()else{}
 for cid,r in technical.items():
  ev=e.evidence()[cid];require(r['metadata_path']==ev['metadata_path']and r['metadata_sha256']==sha(root/r['metadata_path']),'Technical evidence changed');require(r['original_mime']==ev['page']['imageinfo'][0]['mime'],'Unsupported-media MIME differs');require(r['visual_review']=='not_performed','Unviewed media has fabricated visual review')
  if r['original_mime']in e.SUPPORTED_MIME:
   body=safe(root,r['diagnostic_path']);require(sha(body)==r['diagnostic_sha256'],'Changed unsupported animation')
   require(any(f.get('candidate_id')==cid and f.get('partial_path')==r['diagnostic_path']and f.get('error')=='Animated media unsupported'for f in events()),'Animation lacks stopped acquisition evidence')
   with Image.open(body)as im:
    require(im.n_frames==r['frames']and im.n_frames>1,'Unsupported animation evidence differs')
    for frame in range(im.n_frames):im.seek(frame);im.load()
 for path in sorted((root/'provenance/api').glob('*.json')):
  if path.name.endswith('.receipt.json'):continue
  data,_,params=e.api_receipt(path)
  if 'imageinfo'in params.get('prop',[''])[0]:
   e.current_metadata(data);stage,edge,_,first,last=path.stem.split('-');first,last=int(first),int(last)
   require(params['titles']==['|'.join(e.candidates()[cid]['frozen_title']for cid in e.order()[first-1:last])]and params['iiurlwidth']==params['iiurlheight']==[edge],'Metadata request differs')
 for stage in('preview','source'):
  for path in sorted((root/f'provenance/{stage}-receipts').glob('*.json')):
   r=read(path);media=safe(root,r['path']);require(media.stat().st_size==r['bytes']and sha(media)==r['sha256'],'Media bytes changed');measured=e.dimensions(media,r['requested_edge']);require(all(r[k]==v for k,v in measured.items()),'Decoded attributes differ')
   evidence=e.evidence(stage,r['requested_edge'])[r['candidate_id']];page=evidence['page'];ii=page['imageinfo'][0]
   require(r['metadata_path']==evidence['metadata_path']and r['metadata_sha256']==sha(root/r['metadata_path']),'Media metadata changed')
   require(r['pageid']==page['pageid']and r['original_sha1']==ii['sha1']and r['canonical_title']==page['title']and r['original_mime']==ii['mime'],'Media identity differs')
   require(r['url']in(ii.get('thumburl'),ii['url'])and r['response']['status']==200 and r['response']['response_complete']and r['response']['sha256']==r['sha256'],'No complete API-linked media receipt')
   require(r['response']['url']==r['url']and r['response']['bytes_received']==r['bytes']and r['response']in events(),'Receipt lacks matching transfer event')
   unscaled=unquote(urlsplit(r['url']).path)==unquote(urlsplit(ii['url']).path);require((r['rendition']=='api_reported_unscaled_original')==unscaled,'Rendition classification differs')
   require((r['api_reported_width'],r['api_reported_height'])==((ii['width'],ii['height'])if unscaled else(ii['thumbwidth'],ii['thumbheight'])),'API dimensions differ')
   if unscaled:require(ii['mime']!='image/svg+xml'and max(ii['width'],ii['height'])<=r['requested_edge']and hashlib.sha1(media.read_bytes()).hexdigest()==ii['sha1'],'Unbounded or changed original')
   if ii['mime']=='image/svg+xml':require(not unscaled and r['format']=='PNG','SVG is not API raster')
   if stage=='source':
    reviewed=e.evidence()[r['candidate_id']]['page'];require(ii['sha1']==reviewed['imageinfo'][0]['sha1']and ii['extmetadata']==reviewed['imageinfo'][0]['extmetadata'],'Identity/rights changed after review')
 imported=imports();images,sources=records(imported);manifest=read(out/'manifest.json');require(manifest['schema_version']==1 and manifest['kind']=='curatorial_heap'and manifest['images']==images,'Manifest differs')
 require(not(out/'prompt.json').exists()and not(out/'provenance/intake/prompt.json').exists(),'Unexpected visual prompt');require(csv_read(out/'manifest.csv')==[{k:str(v)for k,v in r.items()}for r in images],'Manifest CSV differs');require(csv_read(out/'sources.csv')==[{k:str(v)for k,v in r.items()}for r in sources],'Source CSV differs')
 require(read(out/'provenance/import-map.json')==imported,'Import mapping differs');require((out/'SOURCES.md').read_text()==credits(imported),'Credits differ')
 require({str(p.relative_to(out))for p in(out/'images').iterdir()}=={r['final_file']for r in imported},'Image set differs');require({str(p.relative_to(root))for p in(root/'sources').iterdir()}=={r['source_path']for r in imported},'Source set differs')
 for r in imported:require(sha(out/r['final_file'])==sha(root/r['source_path'])==r['sha256'],'Source/input copies differ')
 expected=''.join(digest+'  '+name+'\n'for name,digest in sorted((name,r['sha256'])for r in imported for name in(r['source_path'],r['final_file'])));require((out/'SHA256SUMS.txt').read_text()==expected,'Checksum listing differs')
 for name,subset in [('batch-1',images),('smoke',images[:5]),('medium',images[:20])]:require((out/f'batches/{name}.txt').read_text().splitlines()==[r['file']for r in subset],'Batch differs')
 require({p.name for p in(out/'batches').iterdir()}=={'batch-1.txt','smoke.txt','medium.txt'},'Unexpected batches');pairs=read(out/'selections.json');require(pairs['pairs']==[]and pairs['known_shift_families']==[]and not csv_read(out/'probes.csv'),'Unexpected matching expectations')
 contacts=read(out/'provenance/contact-sheets.json');require([cid for r in contacts for cid in r['candidate_ids']]==[r['candidate_id']for r in imported],'Contact coverage differs')
 for r in contacts:
  require(sha(safe(out,r['path']))==r['sha256'],'Contact sheet changed')
  with Image.open(out/r['path'])as im:im.load();require(im.size==(r['width'],r['height']),'Contact dimensions differ')
 prior=read(out/'provenance/identity-audit.json');require(prior==audit.audit([r['fixture']for r in prior['inventories']], recorded_inventories=prior['inventories']),'Prior-identity audit differs');require(read(out/'provenance/related-file-evidence.json')==related_evidence(),'Related-file evidence differs');require(read(out/'provenance/acquisition.json')==summary(),'Acquisition status differs')
 return dict(validation='passed',kind='curatorial_heap',expected_pairs=0,**summary())

def build():
 root=e.ROOT;require(not(root/'manifest.json').exists(),'Publication exists; preserve before explicit repair');stage=Path(tempfile.mkdtemp(prefix='integration-stage-',dir=root/'previews'));imported=imports();images,sources=records(imported)
 for folder in('images','batches','provenance'):(stage/folder).mkdir()
 for r in imported:require(sha(root/r['source_path'])==r['sha256'],'Source changed');shutil.copyfile(root/r['source_path'],stage/r['final_file'])
 dump(stage/'manifest.json',dict(schema_version=1,fixture_id='hazy-'+root.name.lower()+'-v1',kind='curatorial_heap',description='Fixed-order sample of three direct Commons categories, with thumbnail scope and documented work/specimen exclusions. No expected matches.',images=images));csv_write(stage/'manifest.csv',images,IMAGE_FIELDS);csv_write(stage/'sources.csv',sources,SOURCE_FIELDS);csv_write(stage/'probes.csv',[],PROBE_FIELDS);dump(stage/'selections.json',dict(description='No pairwise correctness, matching labels or known-shift families.',pairs=[],known_shift_families=[]))
 dump(stage/'provenance/import-map.json',imported);dump(stage/'provenance/acquisition.json',summary());dump(stage/'provenance/identity-audit.json',audit.audit());dump(stage/'provenance/related-file-evidence.json',related_evidence())
 for name,subset in [('batch-1',images),('smoke',images[:5]),('medium',images[:20])]:(stage/f'batches/{name}.txt').write_text(''.join(r['file']+'\n'for r in subset))
 (stage/'SHA256SUMS.txt').write_text(''.join(digest+'  '+name+'\n'for name,digest in sorted((name,r['sha256'])for r in imported for name in(r['source_path'],r['final_file']))));(stage/'SOURCES.md').write_text(credits(imported));sheets(stage,imported);result=check(stage);dump(stage/'provenance/validation.json',result)
 generated=[p for p in stage.rglob('*')if p.is_file()];require(not any((root/p.relative_to(stage)).exists()for p in generated),'Publication destination exists')
 for p in generated:dest=root/p.relative_to(stage);dest.parent.mkdir(parents=True,exist_ok=True);p.replace(dest)
 shutil.rmtree(stage);print(json.dumps(check(),indent=2))

def run(core,command):
 global e
 e=core;audit.e=core
 if command=='build':build()
 elif command=='check':print(json.dumps(check(),indent=2))
 else:
  result=audit.audit();dump(e.ROOT/'provenance/prepublication-identity-audit.json',result);print({k:v for k,v in result.items()if k not in('checked','collisions_with_previous','inventories')})

def sheets(stage,imported):
    result=[];(stage/'previews').mkdir()
    for start in range(0,len(imported),20):
        group=imported[start:start+20];canvas=Image.new('RGB',(1280,math.ceil(len(group)/4)*280),'#eeeeee');draw=ImageDraw.Draw(canvas)
        for i,r in enumerate(group):
            with Image.open(stage/r['final_file'])as im:
                tile=ImageOps.exif_transpose(im).convert('RGBA');tile.thumbnail((304,240),Image.Resampling.LANCZOS)
                x,y=i%4*320,i//4*280;canvas.paste(tile,(x+(320-tile.width)//2,y+(240-tile.height)//2),tile);draw.text((x+8,y+250),r['candidate_id'],fill='black')
        name=f'previews/selected-{start//20+1:02d}.jpg';canvas.save(stage/name,quality=92)
        result.append(dict(path=name,sha256=sha(stage/name),width=canvas.width,height=canvas.height,candidate_ids=[r['candidate_id']for r in group]))
    dump(stage/'provenance/contact-sheets.json',result)
