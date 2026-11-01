#!/usr/bin/env python3
"""Assemble/check the reviewed RG01 starter heap from cached Commons bytes.

No network calls. Shared image/source columns, explicit prompt_heap kind,
no pair expectations. Publication refuses existing images or metadata.
"""
import argparse
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import zipfile
from PIL import Image,ImageDraw,ImageFont,ImageOps

ROOT=Path(__file__).resolve().parents[1]
FIELDS='file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
SOURCE_FIELDS='family_id source_filename scene_id subject credit_status source_sha256 width height exif_orientation source_url preprocessing view exposure_id original_path'.split()


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def safe(root,name):
    p=root/name
    if Path(name).is_absolute() or '..' in Path(name).parts or root.resolve() not in p.resolve().parents:
        raise ValueError(f'Outside fixture: {name}')
    if any(x.is_symlink() for x in [p,*p.parents] if x!=root.parent):raise ValueError(f'Symlink: {name}')
    return p


def dump(p,data):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def csv_write(p,rows,fields):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def check(root):
    manifest=json.loads(safe(root,'manifest.json').read_text()); rows=manifest['images']
    assert manifest['kind']=='prompt_heap' and manifest['schema_version']==1
    with safe(root,'manifest.csv').open(newline='') as f:assert list(csv.DictReader(f))==[{k:str(v) for k,v in r.items()} for r in rows]
    assert len(rows)==31 and len({r['file'] for r in rows})==31
    assert {r['file'] for r in rows}=={'images/'+p.name for p in (root/'images').iterdir()}
    sums={}
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        h,name=line.split('  ',1); assert name not in sums; sums[name]=h; assert sha(safe(root,name))==h,name
    assert set(sums)=={str(p.relative_to(root)) for directory in ['images','sources'] for p in (root/directory).iterdir()}
    with (root/'sources.csv').open(newline='') as f:sources={r['family_id']:r for r in csv.DictReader(f)}
    assert len(sources)==len(rows)
    for r in rows:
        assert r['byte_sha256']==sums[r['file']]
        assert r['origin_count']==1 and r['parents']==r['family_id'] and r['scene_id']==''
        assert r['relation_kind']=='prompt_selected' and r['transformation']=='source'
        s=sources[r['family_id']]; assert r['byte_sha256']==s['source_sha256']==sums['sources/'+s['source_filename']]
        with Image.open(safe(root,r['file'])) as im:
            im.load(); assert [im.width,im.height,im.getexif().get(274,1),im.format]==[r[k] for k in ('width','height','exif_orientation','format')]
    imports=json.loads((root/'provenance/import-map.json').read_text()); assert len(imports)==31
    assert len({r['original_sha1'] for r in imports})==31
    assert {r['final_file'] for r in imports}=={r['file'] for r in rows}
    for r in imports:assert r['sha256']==sums[r['final_file']]
    assert (root/'batches/batch-1.txt').read_text().splitlines()==[r['file'] for r in rows]
    assert json.loads((root/'selections.json').read_text())['pairs']==[]
    with (root/'probes.csv').open(newline='') as f:assert list(csv.DictReader(f))==[]
    return dict(images=len(rows),sources=len(sources),pairs=0,assets=len(sums),kind='prompt_heap')


def sheets(root,imports):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
    for offset in range(0,len(imports),16):
        page=imports[offset:offset+16]; canvas=Image.new('RGB',(1280,math.ceil(len(page)/4)*300),'#eeeeee'); d=ImageDraw.Draw(canvas)
        for i,r in enumerate(page):
            with Image.open(root/r['final_file']) as im:
                im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((310,250)); x=(i%4)*320; y=(i//4)*300
                canvas.paste(im,(x+(320-im.width)//2,y+(250-im.height)//2)); d.text((x+10,y+260),r['candidate_id'],font=font,fill='black')
        p=root/f'previews/selected-{offset//16+1:02d}.jpg'; p.parent.mkdir(parents=True,exist_ok=True); canvas.save(p,quality=90)


def assemble():
    stage=safe(ROOT,'previews/heap-build-v1'); stage.mkdir()
    reviews=json.loads((ROOT/'provenance/reviews.json').read_text()); selected=[r for r in reviews if r['decision']=='accept']
    rows=[]; sources=[]; imports=[]; credits=['# RG01 acquired sources','', 'Server-rendered Commons renditions, preserved byte-for-byte. Source licenses are reported from file-specific Commons metadata; no new license is assigned. The collection prompt is a selection judgment, not an assertion that these images match.','']
    try:
        for review in selected:
            cid=review['candidate_id']; receipt=json.loads((ROOT/f'provenance/downloads/{cid}-1600.json').read_text())
            assert receipt['status']=='downloaded' and receipt['original_sha1']==review['original_sha1']
            assert sha(safe(ROOT,receipt['file']))==receipt['sha256']
            family='rg-'+hashlib.sha256(f"{receipt['pageid']}:{receipt['original_sha1']}".encode()).hexdigest()[:16]
            suffix=Path(receipt['file']).suffix; filename='images/'+family[3:]+suffix
            for dest in [filename,receipt['file']]:
                p=safe(stage,dest); p.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/receipt['file'],p)
            with Image.open(stage/filename) as im:
                im.load(); row=dict(file=filename,batch='batch-1',family_id=family,scene_id='',parents=family,
                  transformation='source',relation_kind='prompt_selected',origin_count=1,width=im.width,height=im.height,
                  exif_orientation=im.getexif().get(274,1),format=im.format,byte_sha256=receipt['sha256'],pixels_rgb_sha256='')
            rows.append(row)
            url='https://commons.wikimedia.org/?curid='+str(receipt['pageid'])
            sources.append(dict(family_id=family,source_filename=Path(receipt['file']).name,scene_id='',subject=receipt['canonical_title'],
              credit_status=review['creator']+'; '+review['license'],source_sha256=receipt['sha256'],width=row['width'],height=row['height'],exif_orientation=row['exif_orientation'],source_url=url,
              preprocessing=f"Commons server-rendered rendition requested at max edge 1600; actual {row['width']}x{row['height']}; local byte copy only.",view='',exposure_id='',original_path=receipt['canonical_title']))
            imports.append(dict(**receipt,final_file=filename,family_id=family,visual_reason=review['visual_reason'],
              source_independence_confirmed=None,provenance_review=review['provenance_review'],license_review=review['license_review']))
            credits.extend([f"## {cid} — {receipt['canonical_title']}",f"- Input: `{filename}`; acquired source: `{receipt['file']}`",f"- Creator/credit: {review['creator']}",f"- License: {review['license']}"+(f" ([terms]({review['license_url']}))" if review['license_url'] else ''),f"- [Commons file page]({url}) · [acquired rendition]({receipt['url']})",f"- Requested max edge: 1600; actual: {row['width']} × {row['height']}; SHA-256: `{receipt['sha256']}`",''])
        manifest=dict(schema_version=1,fixture_id='hazy-rg01-v1',kind='prompt_heap',description='31 photographs selected by the red-accent / green-outdoor prompt. No similarity or membership ground truth.',images=rows)
        dump(stage/'manifest.json',manifest); csv_write(stage/'manifest.csv',rows,FIELDS); csv_write(stage/'sources.csv',sources,SOURCE_FIELDS)
        dump(stage/'provenance/import-map.json',imports); (stage/'SOURCES.md').write_text('\n'.join(credits)+'\n')
        dump(stage/'provenance/intake/prompt.json',dict(prompt='A salient red object within a predominantly green outdoor environment.',scale='Small warm-colored things in big green places.',human_presence='Incidental people allowed; people should not be primary subjects.',selection='Visual impression, retaining original framing and colors. No semantic core/border/outlier labels.',source_independence='Duplicate and shared-capture screening is an exclusion check, not a guide to similarity; independence is not proven.',requested_count='approximately 70, potentially 50–80',actual_count=31,shortfall='The supplied 107 leads yielded 31 visual selections, 69 rejections and 7 deferred warm-color fallbacks. No additional search was performed.'))
        csv_write(stage/'probes.csv',[],'file_a file_b relation interpretation'.split())
        dump(stage/'selections.json',dict(description='No predetermined pair judgments for this prompt-led heap.',pairs=[],known_shift_families=[]))
        (stage/'batches').mkdir(); (stage/'batches/batch-1.txt').write_text(''.join(r['file']+'\n' for r in rows))
        files=sorted([r['file'] for r in rows]+[r['file'] for r in imports]); (stage/'SHA256SUMS.txt').write_text(''.join(sha(stage/f)+'  '+f+'\n' for f in files))
        sheets(stage,imports); result=check(stage); dump(stage/'validation.json',dict(status='passed',**result))
        print(json.dumps(result,indent=2))
    except Exception as error:
        dump(stage/'FAILED.json',dict(status='incomplete',error=str(error))); raise


def publish():
    stage=ROOT/'previews/heap-build-v1'; check(stage)
    names=['images','manifest.json','manifest.csv','sources.csv','SOURCES.md','provenance/intake/prompt.json','probes.csv','selections.json','batches','SHA256SUMS.txt','provenance/import-map.json','previews/selected-01.jpg','previews/selected-02.jpg']
    for name in names:assert not safe(ROOT,name).exists(),f'Refusing existing output: {name}'
    for name in names:
        src=safe(stage,name); dest=safe(ROOT,name); dest.parent.mkdir(parents=True,exist_ok=True)
        if src.is_dir():shutil.copytree(src,dest)
        else:shutil.copyfile(src,dest)
    result=check(ROOT); dump(ROOT/'provenance/validation.json',dict(status='passed',**result))
    print(json.dumps(result,indent=2))


def archive():
    check(ROOT); target=ROOT/'previews/hazy-rg01-v1.zip'; assert not target.exists()
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            relative=p.relative_to(ROOT)
            if not p.is_file() or p.is_symlink():continue
            if 'previews' in relative.parts and str(relative) not in ('previews/selected-01.jpg','previews/selected-02.jpg'):continue
            if '__pycache__' in relative.parts or p.name.startswith('.'):continue
            z.write(p,arcname='hazy-rg01-v1/'+str(relative))
    dump(ROOT/'provenance/archive.json',dict(file=str(target.relative_to(ROOT)),sha256=sha(target),size_bytes=target.stat().st_size))
    print(target)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('command',choices=['assemble','publish','check','archive']); args=parser.parse_args()
    if args.command=='check':print(json.dumps(check(ROOT),indent=2))
    else:globals()[args.command]()
