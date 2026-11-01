#!/usr/bin/env python3
"""Build/check/publish PS01 from accepted, reviewed Commons bytes. No network."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import zipfile
from PIL import Image, ImageDraw, ImageFont, ImageOps
from common import ROOT, local
from acquire import html_plain as clean_text, same_media_url

def jsonlines(path):return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

IMAGE_FIELDS='file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
SOURCE_FIELDS='family_id source_filename scene_id subject credit_status source_sha256 width height exif_orientation source_url preprocessing view exposure_id original_path'.split()


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root,name):
    p=root/name
    require(not Path(name).is_absolute() and '..' not in Path(name).parts and root.resolve() in p.resolve().parents,f'Unsafe path: {name}')
    require(not any(q.is_symlink() for q in [p,*p.parents] if q!=root.parent),f'Symlink: {name}')
    return p


def dump(p,value):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def csv_write(p,rows,fields):
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def dimensions(p):
    with Image.open(p) as im:
        im.load();require(getattr(im,'n_frames',1)==1,'Multiple image frames')
        return dict(width=im.width,height=im.height,exif_orientation=im.getexif().get(274,1),format=im.format)


def check_evidence(root, check_imports=True):
    candidates=jsonlines(safe(root,'provenance/intake/candidates.jsonl'))
    original=jsonlines(safe(root,'provenance/supplied/candidates.jsonl'))
    require(len(candidates)==len(original),'Candidate count changed')
    require(len({r['candidate_id'] for r in candidates})==len(candidates),'Duplicate candidate ID')
    supplied={r['candidate_id']:r for r in original}
    with (root/'provenance/intake/candidates.csv').open(newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames
        expected=[{k:'' if r.get(k) is None else str(r[k]) for k in fields} for r in candidates]
        require(list(reader)==expected,'Candidate CSV/JSONL differ')
    reviews={r['candidate_id']:r for r in json.loads((root/'provenance/visual-review.json').read_text())}
    source_review=json.loads((root/'provenance/source-review.json').read_text())
    licenses={r['candidate_id']:r for r in source_review['license_reviews']}
    immutable='candidate_id family commons_title commons_filename discovery discovery_url candidate_basis priority accent_color'.split()
    events=jsonlines(root/'provenance/http_log.jsonl')
    transfers={(e['candidate_id'],e['kind'],e.get('sha256')):e for e in events if e.get('response_complete') is True and e.get('sha256')}
    def transfer(cid,kind,path,url=None):
        p=safe(root,path);event=transfers.get((cid,kind,sha(p)))
        require(event and event['bytes_received']==p.stat().st_size,'Missing complete transfer receipt: '+path)
        if url is not None:require(event['url']==url,'Transfer URL differs: '+path)
    selected=[];acquired=[];pending=[]
    for row in candidates:
        old=supplied[row['candidate_id']]
        require(set(old)<=set(row),'Supplied fields lost')
        require(all(row.get(k)==old.get(k) for k in immutable),'Supplied identity/discovery field changed')
        review=reviews[row['candidate_id']]
        require(row['screening_status']==review['decision'] and row['visual_reason']==review['visual_reason'],'Visual decision differs from review')
        require(row['screening_status'] in ('accept','reject','defer'),'Unreviewed candidate')
        transfer(row['candidate_id'],'preview',row['preview_path'],row['preview_url'])
        transfer(row['candidate_id'],'api',row['api_preview_metadata_path'])
        preview=safe(root,row['preview_path'])
        require(sha(preview)==row['preview_sha256'],'Preview bytes changed')
        size=dimensions(preview)
        require(size['width']==row['preview_width'] and size['height']==row['preview_height'],'Preview dimensions differ')
        meta=json.loads(safe(root,row['api_preview_metadata_path']).read_text())['query']['pages'][0]
        require(meta['pageid']==row['commons_pageid'] and meta['imageinfo'][0]['sha1']==row['preview_original_sha1'],'Preview source identity differs')
        if row['screening_status']!='accept':continue
        selected.append(row)
        require(row['source_independence_confirmed'] is None,'Unexpected independence assertion')
        license=licenses[row['candidate_id']]
        require(sha(safe(root,license['metadata_path']))==license['metadata_sha256'],'Reviewed license evidence changed')
        require(row['license']==license['license'],'License changed after review')
        if not row['image_downloaded']:
            require(not row.get('acquired_path') and not row.get('acquired_sha256'),'Incomplete source marked as acquired')
            pending.append(row['candidate_id']);continue
        require(row['acquired_path'] and sha(safe(root,row['acquired_path']))==row['acquired_sha256'],'Acquired source changed')
        transfer(row['candidate_id'],'source',row['acquired_path'],row['acquired_url'])
        transfer(row['candidate_id'],'api',row['api_source_metadata_path'])
        current=json.loads(safe(root,row['api_source_metadata_path']).read_text())['query']['pages'][0]
        require(current['pageid']==row['commons_pageid'],'Acquired page identity changed')
        info=current['imageinfo'][0]
        expected_kind='api_reported_unscaled_original' if same_media_url(row['acquired_url'],info.get('url')) else 'api_returned_rendition'
        require(row['acquired_rendition_kind']==expected_kind and row['source_requested_max_edge'] in (1280,1600),'Acquisition kind/size request differs')
        require(row['source_acquisition_status']=='complete','Acquired source has incomplete transport status')
        if expected_kind=='api_reported_unscaled_original':require(max(info['width'],info['height'])<=row['source_requested_max_edge'],'Oversized original')
        require(info['sha1']==row['original_sha1']==row['preview_original_sha1'],'Acquired upstream bytes changed after review')
        require(clean_text(info['extmetadata']['LicenseShortName']['value'])==license['license'],'Acquired license changed after review')
        acquired.append(row)
    require(set(licenses)=={r['candidate_id'] for r in selected},'License review coverage differs')
    audit=json.loads((root/'provenance/identity-audit.json').read_text())
    require(audit['status']=='passed' and audit['accepted']==len(selected) and audit['acquired']==len(acquired),'Identity audit incomplete or failed')
    receipt=json.loads((root/'provenance/acquisition.json').read_text())
    require(receipt['visually_selected']==len(selected) and receipt['acquired_count']==len(acquired) and receipt['pending_candidate_ids']==pending,'Acquisition receipt differs')
    if pending:
        require(receipt['status'] in ('stopped','partial'),'Missing explicit incomplete acquisition status')
        if receipt['status']=='stopped':
            require(sha(safe(root,receipt['stop_record']))==receipt['stop_record_sha256'],'Acquisition stop evidence changed')
        else:require(all(receipt['pending_statuses'][cid]=='unavailable_metadata' for cid in pending),'Unexplained pending source')
    else:require(receipt['status']=='complete' and not (root/'provenance/last_transport_error.json').exists(),'Unresolved transport failure')
    imports=json.loads((root/'provenance/import-map.json').read_text()) if check_imports and (root/'provenance/import-map.json').exists() else None
    if imports is not None:
        imported={r['candidate_id']:r for r in imports}
        require(set(imported)=={r['candidate_id'] for r in acquired},'Imported candidates differ')
        for row in acquired:require(all(imported[row['candidate_id']].get(k)==v for k,v in row.items()),'Import snapshot differs from canonical candidate')
    return dict(previews=len(candidates),visually_selected=len(selected),acquired=len(acquired),pending=len(pending),acquisition_status=receipt['status'],status='passed')


def check(root):
    manifest=json.loads(safe(root,'manifest.json').read_text());rows=manifest['images']
    require(manifest['kind']=='prompt_heap' and manifest['schema_version']==1,'Unsupported kind/schema')
    require(bool(rows) and len({r['file'] for r in rows})==len(rows),'Empty/duplicate inputs')
    with (root/'manifest.csv').open(newline='') as f:
        require(list(csv.DictReader(f))==[{k:str(v) for k,v in r.items()} for r in rows],'CSV/JSON differ')
    actual={'images/'+p.name for p in (root/'images').iterdir()}
    require(actual=={r['file'] for r in rows},'Input coverage mismatch')
    sums={}
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        expected,name=line.split('  ',1);require(name not in sums,'Duplicate checksum')
        p=safe(root,name);require(sha(p)==expected,f'Changed asset: {name}');sums[name]=expected
    require(set(sums)==actual|{'sources/'+p.name for p in (root/'sources').iterdir()},'Incomplete asset inventory')
    with (root/'sources.csv').open(newline='') as f:source_rows=list(csv.DictReader(f))
    sources={r['family_id']:r for r in source_rows}
    require(len(sources)==len(source_rows)==len(rows),'Source count/identity mismatch')
    imports=json.loads((root/'provenance/import-map.json').read_text())
    require(len(imports)==len(rows) and len({r['candidate_id'] for r in imports})==len(rows),'Import count/identity mismatch')
    require(len({r['original_sha1'] for r in imports})==len(rows),'Repeated upstream file')
    require({r['final_file'] for r in imports}==actual,'Import file coverage mismatch')
    by_file={r['file']:r for r in rows}
    for record in imports:
        row=by_file[record['final_file']];source=sources[row['family_id']]
        require(record['family_id']==row['family_id'],'Import family identity differs')
        require(row['origin_count']==1 and row['parents']==row['family_id'] and row['scene_id']=='','Invalid source relationship')
        require(row['transformation']=='source' and row['relation_kind']=='prompt_selected','Unexpected relationship')
        require(row['byte_sha256']==sums[row['file']]==sums['sources/'+source['source_filename']]==record['acquired_sha256']==source['source_sha256'],'Source/input bytes differ')
        require(all(row[k]==v for k,v in dimensions(root/row['file']).items()),'Measured input metadata differs')
        require(all(int(source[k])==row[k] for k in ('width','height','exif_orientation')),'Source dimensions differ')
        require(record['screening_status']=='accept' and record['visual_reason'] and record['license_review'] and record['provenance_review'],'Incomplete acceptance evidence')
    require((root/'batches/batch-1.txt').read_text().splitlines()==[r['file'] for r in rows],'Batch mismatch')
    require(json.loads((root/'selections.json').read_text())['pairs']==[],'Unexpected pair labels')
    with (root/'probes.csv').open(newline='') as f:require(list(csv.DictReader(f))==[],'Unexpected probes')
    require(json.loads((root/'provenance/intake/prompt.json').read_text())['actual_count']==len(rows),'Prompt count mismatch')
    return dict(status='passed',kind='prompt_heap',images=len(rows),sources=len(sources),assets=len(sums),pairs=0)


def contact_sheets(root,imports):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
    output=[]
    for offset in range(0,len(imports),20):
        group=imports[offset:offset+20];canvas=Image.new('RGB',(1280,math.ceil(len(group)/4)*285),'#eeeeee');draw=ImageDraw.Draw(canvas)
        for i,row in enumerate(group):
            with Image.open(root/row['final_file']) as im:
                im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((304,246),Image.Resampling.LANCZOS)
                x=(i%4)*320;y=(i//4)*285;canvas.paste(im,(x+(320-im.width)//2,y+(246-im.height)//2))
                draw.text((x+8,y+255),row['candidate_id'],font=font,fill='black')
        name=f'previews/selected-{offset//20+1:02d}.jpg';p=root/name;p.parent.mkdir(parents=True,exist_ok=True);canvas.save(p,quality=92)
        output.append(name)
    return output


def build(name):
    require(re.fullmatch(r'[a-zA-Z0-9_-]+',name),'Use a simple stage name')
    check_evidence(ROOT,check_imports=False)
    stage=local('previews/integration-'+name);stage.mkdir()
    try:
        candidates=jsonlines(ROOT/'provenance/intake/candidates.jsonl');selected=[r for r in candidates if r['screening_status']=='accept' and r['image_downloaded']]
        pending=[r['candidate_id'] for r in candidates if r['screening_status']=='accept' and not r['image_downloaded']]
        require(all(r['screening_status'] in ('accept','reject','defer') for r in candidates),'Unreviewed candidates remain')
        rows=[];sources=[];imports=[];credits=['# PS01 acquired sources','','Commons renditions and API-reported unscaled originals, preserved byte-for-byte. Licenses below come from file-specific metadata; the collection assigns no new license.','']
        for record in selected:
            require(record['image_downloaded'] and record['acquired_path'],'Accepted image missing')
            src=local(record['acquired_path']);require(sha(src)==record['acquired_sha256'],'Acquired bytes changed')
            require(record['original_sha1']==record['preview_original_sha1'],'Upstream changed after preview')
            token=hashlib.sha256(f"{record['commons_pageid']}:{record['original_sha1']}".encode()).hexdigest()[:16]
            family='ps-'+token;filename='images/'+token+src.suffix
            for name in (filename,record['acquired_path']):
                dest=safe(stage,name);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            row=dict(file=filename,batch='batch-1',family_id=family,scene_id='',parents=family,transformation='source',relation_kind='prompt_selected',origin_count=1,**dimensions(src),byte_sha256=record['acquired_sha256'],pixels_rgb_sha256='')
            rows.append(row);url='https://commons.wikimedia.org/?curid='+str(record['commons_pageid'])
            sources.append(dict(family_id=family,source_filename=src.name,scene_id='',subject=record.get('commons_api_title') or record['commons_title'],
                credit_status=(record.get('creator') or 'Creator not reported')+'; '+record['license'],source_sha256=record['acquired_sha256'],width=row['width'],height=row['height'],exif_orientation=row['exif_orientation'],source_url=url,
                preprocessing=f"Commons {record['acquired_rendition_kind']}, nominal max edge {record['source_requested_max_edge']}; actual {row['width']}x{row['height']}; local byte copy only.",view='',exposure_id='',original_path=record['commons_filename']))
            imports.append(dict(record,final_file=filename,family_id=family))
            credits.extend([f"## {record['candidate_id']} — {record['commons_title']}",f"- Input: `{filename}`; preserved rendition: `{record['acquired_path']}`",f"- Creator: {record.get('creator') or 'not reported'}",f"- License: {record['license']}"+(f" ([terms]({record['license_url']}))" if record.get('license_url') else ''),f"- [Commons file page]({url}) · [acquired rendition]({record['acquired_url']})",f"- Actual dimensions: {row['width']} × {row['height']}; SHA-256: `{record['acquired_sha256']}`",''])
        dump(stage/'manifest.json',dict(schema_version=1,fixture_id='hazy-ps01-v1',kind='prompt_heap',description='PS01 pale skies and dark lower halves: photographs with a pale quiet upper sky and a darker, detailed lower region. Visual curation, no pair or membership ground truth.',images=rows))
        csv_write(stage/'manifest.csv',rows,IMAGE_FIELDS);csv_write(stage/'sources.csv',sources,SOURCE_FIELDS)
        dump(stage/'provenance/import-map.json',imports);(stage/'SOURCES.md').write_text('\n'.join(credits)+'\n')
        dump(stage/'provenance/intake/prompt.json',dict(element='pale-skies-dark-lower-halves',prompt='Photographs with a comparatively pale, broadly continuous sky occupying a substantial upper region and a darker, more detailed or silhouetted lower region.',looseness='Horizon height, boundary sharpness, fog density, foreground texture and subject matter may vary; slightly blue or pink-gray skies are allowed.',exclusions='Known derivatives, crops, related captures/sequences, synthetic imagery, dominant close-up subjects, saturated sunsets, and fog/cloud subjects without the light-upper/dark-lower composition.',interpretation='Visual curation only. Discovery buckets and source identities are not similarity labels or expected clusters.',target_count=65,acceptable_range=[50,80],actual_count=len(rows),acquisition_status=json.loads((ROOT/'provenance/acquisition.json').read_text())['status'],pending_acquisition=pending,candidate_count=len(candidates),selection_counts={s:sum(r['screening_status']==s for r in candidates) for s in ['accept','reject','defer']}))
        csv_write(stage/'probes.csv',[],'file_a file_b relation interpretation'.split())
        dump(stage/'selections.json',dict(description='No predetermined pairs for this prompt-led heap element.',pairs=[],known_shift_families=[]))
        (stage/'batches').mkdir();(stage/'batches/batch-1.txt').write_text(''.join(r['file']+'\n' for r in rows))
        files=sorted([r['file'] for r in rows]+[r['acquired_path'] for r in selected]);(stage/'SHA256SUMS.txt').write_text(''.join(sha(stage/f)+'  '+f+'\n' for f in files))
        sheets=contact_sheets(stage,imports);validation=check(stage);dump(stage/'validation.json',dict(validation,contact_sheets=sheets));print(json.dumps(validation,indent=2))
    except Exception as error:
        dump(stage/'FAILED.json',dict(status='incomplete',error=str(error)));raise


def publish(name):
    require(re.fullmatch(r'[a-zA-Z0-9_-]+',name),'Use a simple stage name')
    check_evidence(ROOT,check_imports=False)
    stage=local('previews/integration-'+name);validation=check(stage)
    names=['images','manifest.json','manifest.csv','sources.csv','SOURCES.md','provenance/intake/prompt.json','probes.csv','selections.json','batches','SHA256SUMS.txt','provenance/import-map.json']
    names += [str(p.relative_to(stage)) for p in sorted((stage/'previews').glob('selected-*.jpg'))]
    for name in names:require(not local(name).exists(),f'Output already exists: {name}')
    created=[]
    try:
        for name in names:
            src=safe(stage,name);dest=local(name);dest.parent.mkdir(parents=True,exist_ok=True)
            if src.is_dir():shutil.copytree(src,dest)
            else:shutil.copyfile(src,dest)
            created.append(name)
        validation=check(ROOT);evidence=check_evidence(ROOT)
        dump(ROOT/'provenance/integration.json',dict(validation,evidence=evidence,stage=str(stage.relative_to(ROOT)),created=created));print(json.dumps(validation,indent=2))
    except Exception as error:
        dump(ROOT/'provenance/integration.json',dict(status='incomplete',created=created,error=str(error)));raise


def archive():
    check(ROOT);check_evidence(ROOT)
    p=local('previews/hazy-ps01-v1.zip');require(not p.exists(),'Archive exists')
    with zipfile.ZipFile(p,'x',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(ROOT.rglob('*')):
            rel=file.relative_to(ROOT)
            if not file.is_file() or file.is_symlink() or '__pycache__' in rel.parts or file.name.startswith('.'):continue
            if 'previews' in rel.parts:
                is_sheet = len(rel.parts)==2 and (file.name.startswith('selected-') or file.name.startswith('contact-')) and file.suffix=='.jpg'
                is_tile = len(rel.parts)==3 and rel.parts[:2]==('previews','tiles')
                is_partial = len(rel.parts)==3 and rel.parts[:2]==('previews','partials')
                if not (is_sheet or is_tile or is_partial):continue
            archive.write(file,'hazy-ps01-v1/'+str(rel))
    with zipfile.ZipFile(p) as archive:require(archive.testzip() is None,'Archive integrity failed')
    dump(ROOT/'provenance/archive.json',dict(file=str(p.relative_to(ROOT)),sha256=sha(p),size_bytes=p.stat().st_size));print(p)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for command in ['build','publish']:
        child=sub.add_parser(command);child.add_argument('--stage',required=True)
    sub.add_parser('check');sub.add_parser('archive');args=p.parse_args()
    if args.command=='check':print(json.dumps(dict(fixture=check(ROOT),evidence=check_evidence(ROOT)),indent=2))
    elif args.command=='archive':archive()
    else:globals()[args.command](args.stage)

if __name__=='__main__':main()
