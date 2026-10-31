#!/usr/bin/env python3
"""Generate a fixed, documented corpus of transformed public-domain example images.

Requires Pillow 10+. Input files are provided in the sources/ directory.
The output is reproducible for a given Pillow version. See manifest for hashes.
"""
from __future__ import annotations
import csv, hashlib, io, json, random, shutil, sys, zipfile
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / 'images'
SOURCE_DIR = ROOT / 'sources'
BATCH_DIR = ROOT / 'batches'

FAMILIES = [
    ('astronaut','astronaut.png','Astronaut Eileen Collins','NASA; public domain'),
    ('cat','chelsea.png','Chelsea the cat','Stefan van der Walt; CC0'),
    ('coffee','coffee.png','Coffee cup','Rachel Michetti; CC0'),
    ('rocket','rocket.jpg','SpaceX Falcon 9 launch','SpaceX; public domain'),
    ('galaxies','hubble_deep_field.jpg','Hubble eXtreme Deep Field','NASA; public domain'),
    ('photographer','camera.png','Photographer with camera','Lav Varshney; CC0'),
    ('brick','brick.png','Brick texture','CC0Textures; CC0'),
    ('grass','grass.png','Grass texture','Original at DeviantArt; CC0'),
    ('gravel','gravel.png','Gravel texture','CC0Textures; CC0'),
    ('retina','retina.jpg','Retina photo','Wikimedia Commons; CC0'),
    ('horse','horse.png','Horse silhouette','Andreas Preuss; CC0'),
    ('coins','coins.png','Greek coins','Brooklyn Museum Collection; no known copyright restrictions'),
]
SINGLETONS = [
    ('clock','clock_motion.png','Motion-blurred clock','Stefan van der Walt; public domain'),
    ('cell','cell.png','Cell microscopy','Quantitative phase data (qpformat); CC0'),
    ('microaneurysm','microaneurysms.png','Retina lesion crop','Andreas Maier; CC0'),
]
MIXES = [
    ('rocket','galaxies'), ('cat','coffee'), ('grass','gravel'),
    ('astronaut','photographer'), ('retina','coins'), ('brick','horse'),
]


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(path):
    return sha_bytes(path.read_bytes())

def pixel_hash(path):
    with Image.open(path) as pic:
        pic = ImageOps.exif_transpose(pic).convert('RGB')
        return sha_bytes(pic.width.to_bytes(4,'little')+pic.height.to_bytes(4,'little')+pic.tobytes())

def base_image(key):
    src = next(name for fid,name,_,_ in (FAMILIES+SINGLETONS) if fid==key)
    return Image.open(SOURCE_DIR/src).convert('RGB')

def named_bytes(key, transform):
    src_name = next(src for fid,src,_,_ in FAMILIES if fid==key)
    src_path = SOURCE_DIR / src_name
    src = Image.open(src_path)
    rgb = src.convert('RGB')
    w,h=rgb.size
    if transform == 'source':
        return src_path.read_bytes(), src_path.suffix.lower().lstrip('.')
    if transform == 'byte_copy':
        return src_path.read_bytes(), src_path.suffix.lower().lstrip('.')
    if transform == 'reencode_png':
        return encode(rgb,'PNG',compress_level=0), 'png'
    if transform == 'jpeg_q94':
        return encode(rgb,'JPEG',quality=94, subsampling=0), 'jpg'
    if transform == 'jpeg_q35':
        return encode(rgb,'JPEG',quality=35), 'jpg'
    if transform == 'scale_half':
        rgb=rgb.resize((max(1,w//2),max(1,h//2)),Image.Resampling.LANCZOS)
    elif transform == 'center_crop_85':
        box=(int(w*.075),int(h*.075),int(w*.925),int(h*.925))
        rgb=rgb.crop(box)
    elif transform == 'offcenter_crop_55':
        box=(int(w*.17),int(h*.27),int(w*.72),int(h*.82))
        rgb=rgb.crop(box)
    elif transform == 'rotate_90':
        rgb=rgb.transpose(Image.Transpose.ROTATE_90)
    elif transform == 'mirror':
        rgb=ImageOps.mirror(rgb)
    elif transform == 'warm_bright':
        rgb=ImageEnhance.Contrast(ImageEnhance.Brightness(rgb).enhance(1.17)).enhance(1.08)
        tone=Image.new('RGB',rgb.size,(244,174,76))
        rgb=Image.blend(rgb,tone,0.14)
    elif transform == 'letterbox':
        canvas=Image.new('RGB',(int(w*1.33),int(h*1.33)),(245,244,239))
        canvas.paste(rgb,((canvas.width-w)//2,(canvas.height-h)//2))
        rgb=canvas
    elif transform == 'ui_overlay':
        canvas=Image.new('RGB',(w, int(h*1.18)),(20,22,25))
        canvas.paste(rgb,(0,int(h*.18)))
        dr=ImageDraw.Draw(canvas)
        dr.text((max(6,int(w*.027)),max(3,int(h*.06))),'HAZY  /  IMAGE PREVIEW',fill=(245,245,245))
        rgb=canvas
    elif transform == 'blur_3':
        rgb=rgb.filter(ImageFilter.GaussianBlur(3.0))
    else:
        raise ValueError(transform)
    return encode(rgb, 'JPEG',quality=90,subsampling=0),'jpg'

def encode(im, fmt, **opts):
    buf=io.BytesIO()
    im.save(buf,format=fmt,**opts)
    return buf.getvalue()

TRANSFORMS=[
    ('source','unmodified'), ('byte_copy','exact_bytes'),
    ('reencode_png','same_pixels'), ('jpeg_q94','recompressed'),
    ('jpeg_q35','recompressed'), ('scale_half','rescaled'),
    ('center_crop_85','overlapping_crop'), ('offcenter_crop_55','overlapping_crop'),
    ('rotate_90','geometry'),('mirror','geometry'),
    ('warm_bright','color'),('letterbox','composition'),
    ('ui_overlay','composition'),('blur_3','blur'),
]

def save_source_credits():
    rows=[]
    for fam, name, subject, credit in FAMILIES + SINGLETONS:
        p=SOURCE_DIR/name
        with Image.open(p) as im:
            wh=im.size
            orientation=im.getexif().get(274,1)
        rows.append(dict(family_id=fam,source_filename=name,scene_id='',subject=subject,credit_status=credit,
                         source_sha256=sha_file(p),width=wh[0],height=wh[1],exif_orientation=orientation,
                         source_url='https://scikit-image.org/docs/stable/api/skimage.data.html',
                         preprocessing='Bundled scikit-image 0.26.0 sample, copied unchanged.',
                         view='',exposure_id='',original_path='hazy-fixtures-v1/sources/'+name))
    write_csv(ROOT/'sources.csv',rows)

def write_csv(path, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]))
        wr.writeheader();wr.writerows(rows)

def write_small_batches(by_family):
    # Recreate the supplied ordered subsets after main clears batches/.
    for name, variants in [
        ('smoke', ['source', 'byte_copy']),
        ('medium', ['source', 'byte_copy', 'reencode_png', 'jpeg_q94', 'center_crop_85']),
    ]:
        paths = [by_family[family][variant]['file']
                 for family in sorted(by_family) if 'source' in by_family[family]
                 for variant in variants]
        (BATCH_DIR / (name + '.txt')).write_text('\n'.join(paths) + '\n')

def main():
    for dr in [IMAGE_DIR,BATCH_DIR]:
        dr.mkdir(parents=True,exist_ok=True)
        for p in dr.glob('*'): p.unlink()
    save_source_credits()
    entries=[]
    for family_no,(family,src,subject,credit) in enumerate(FAMILIES):
        for trans_no,(tr,kind) in enumerate(TRANSFORMS):
            raw,ext=named_bytes(family,tr)
            entries.append(dict(family_id=family,parents=[family],source=src, transform=tr,
                                relation_kind=kind, source_count=1, content=raw,
                                extension=ext, batch_no=(family_no*3+trans_no)%4))
    for si,(family,src,subject,credit) in enumerate(SINGLETONS):
        raw=(SOURCE_DIR/src).read_bytes()
        entries.append(dict(family_id=family,parents=[family],source=src,transform='singleton',
                            relation_kind='distinct_source',source_count=1,content=raw,
                            extension=Path(src).suffix[1:],batch_no=si%4))
    for mi,(fam_a,fam_b) in enumerate(MIXES):
        im_a=base_image(fam_a);im_b=base_image(fam_b)
        side=(440,440)
        a=ImageOps.fit(im_a,side,method=Image.Resampling.LANCZOS)
        b=ImageOps.fit(im_b,side,method=Image.Resampling.LANCZOS)
        for variant in range(2):
            collage=Image.new('RGB',(880,440),'white')
            collage.paste(a if variant==0 else b,(0,0))
            collage.paste(b if variant==0 else a,(440,0))
            entries.append(dict(family_id='',parents=[fam_a,fam_b],source='',
                                transform='composite_'+str(variant+1),relation_kind='ambiguous_multi_origin',
                                source_count=2,content=encode(collage,'JPEG',quality=92),extension='jpg',
                                batch_no=(mi+variant*2)%4))
    # Filename hashing avoids leaking expected families through filenames or directory structure.
    for e in entries:
        idstr = f"{','.join(e['parents'])}:{e['transform']}"
        short=hashlib.sha256(('hazy-fixture-v1:'+idstr).encode()).hexdigest()[:12]
        e['filename']=f"hazy-{short}.{e['extension']}"
    assert len(set(e['filename'] for e in entries))==len(entries)
    assert len(entries)==12*14+3+6*2
    rng=random.Random(20261028)
    rng.shuffle(entries)
    batches=defaultdict(list)
    manifest=[]
    for e in entries:
        path=IMAGE_DIR/e['filename']
        path.write_bytes(e['content'])
        with Image.open(path) as im:
            im.load(); w,h=im.size
            orientation=im.getexif().get(274,1)
        p='images/'+e['filename']
        batch=f'batch-{e["batch_no"]+1}'
        batches[batch].append(p)
        manifest.append(dict(file=p, batch=batch, family_id=e['family_id'],scene_id='',parents='|'.join(e['parents']),
                             transformation=e['transform'],relation_kind=e['relation_kind'],
                             origin_count=e['source_count'],width=w,height=h,exif_orientation=orientation,format=e['extension'],
                             byte_sha256=sha_file(path),pixels_rgb_sha256=pixel_hash(path)))
    manifest.sort(key=lambda r:r['file'])
    write_csv(ROOT/'manifest.csv',manifest)
    with (ROOT/'manifest.json').open('w',encoding='utf-8') as f:
        json.dump({'schema_version':1,'fixture_id':ROOT.name,'kind':'derivatives',
                   'description':'Synthetic derivatives with source provenance; family_id is not an asserted matching cluster.',
                   'images':manifest},f,indent=2)
    for batch, paths in sorted(batches.items()):
        paths.sort(key=lambda s: hashlib.sha256((batch+s).encode()).hexdigest())
        (BATCH_DIR/(batch+'.txt')).write_text('\n'.join(paths)+'\n')
    # sampled pairwise relationships, with no guessed similarity score.
    by_family=defaultdict(dict)
    for r in manifest:
        if r['family_id']:
            by_family[r['family_id']][r['transformation']]=r
    write_small_batches(by_family)
    probes=[]
    for family in sorted(by_family):
        fs=by_family[family]
        if 'source' not in fs:continue
        for variant,relation in [('byte_copy','same_bytes'),('reencode_png','same_decoded_pixels'),
                                 ('jpeg_q94','same_origin_recompressed'),('scale_half','same_origin_resized'),
                                 ('center_crop_85','same_origin_cropped'),('offcenter_crop_55','same_origin_cropped_harder'),
                                 ('warm_bright','same_origin_recolored'),('rotate_90','same_origin_rotated'),
                                 ('ui_overlay','same_origin_overlayed')]:
            if variant in fs:
                probes.append(dict(file_a=fs['source']['file'],file_b=fs[variant]['file'],
                                   relation=relation,interpretation='known_provenance_not_asserted_cluster'))
    # Deliberate potentially confusing non-matches: share appearances, not original files.
    for a,b in [('grass','gravel'),('brick','gravel'),('retina','coins'),('astronaut','photographer'),
                ('rocket','galaxies'),('cat','horse'),('coins','cell')]:
        right=by_family[b].get('source') or by_family[b].get('singleton')
        probes.append(dict(file_a=by_family[a]['source']['file'],file_b=right['file'],
                           relation='distinct_origin',interpretation='candidate_false_friend_no_expected_score'))
    write_csv(ROOT/'probes.csv',probes)
    # Mix overview sheet (only contact sheet, never an app input).
    bases=[]
    for fid,src,label,_ in FAMILIES+SINGLETONS:
        with Image.open(SOURCE_DIR/src) as im:
            bas=im.convert('RGB'); bas.thumbnail((270,180),Image.Resampling.LANCZOS)
            bases.append((fid,bas.copy()))
    sheet=Image.new('RGB',(4*300,4*225),'white')
    dr=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(bases):
        x=i%4*300+(300-im.width)//2;y=i//4*225+7
        sheet.paste(im,(x,y));dr.text((i%4*300+12,i//4*225+196),name,fill='black')
    (ROOT/'previews').mkdir(exist_ok=True)
    sheet.save(ROOT/'previews/preview.jpg',quality=86)
    # Hashes for all images and source files: output sets stable across copies.
    with (ROOT/'SHA256SUMS.txt').open('w') as f:
        for p in sorted(p for p in list(IMAGE_DIR.iterdir())+list(SOURCE_DIR.iterdir()) if p.name != '.DS_Store'):
            f.write(f'{sha_file(p)}  {p.relative_to(ROOT).as_posix()}\n')
    counts=Counter(e['relation_kind'] for e in entries)
    print('Files',len(entries),'batches',{k:len(v) for k,v in batches.items()},'kinds',counts)
    print('Total bytes',sum(p.stat().st_size for p in IMAGE_DIR.iterdir()))
    return entries

if __name__=='__main__':
    main()
