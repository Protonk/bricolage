#!/usr/bin/env python3
"""Build, check, or publish the supplied 42-input variants fixture.

Builds always use a fresh previews/build-NAME directory. Publication refuses
existing outputs. No cleanup or network access is performed.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import sys
from PIL import Image, ImageChops, ImageCms, ImageDraw, ImageFont, ImageOps, features

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = 'hazy-meme-fixtures-v0'
COLS = 'file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
PAIR_COLS = 'file_a file_b relation interpretation'.split()
LANCZOS = Image.Resampling.LANCZOS


def require(ok, message):
    if not ok:
        raise ValueError(message)


def safe(root, name):
    parts = PurePosixPath(name).parts
    require(parts and not PurePosixPath(name).is_absolute() and all(p not in ('.', '..') for p in parts), f'Unsafe path: {name}')
    p = root.joinpath(*parts)
    require(root.resolve() in p.resolve().parents, f'Outside set: {name}')
    require(not any(q.is_symlink() for q in [p, *p.parents] if q != root.parent), f'Symlink: {name}')
    return p


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def checksum_file(root, filename):
    for line in safe(root, filename).read_text().splitlines():
        expected, name = line.split('  ', 1)
        require(digest(safe(root, name)) == expected, f'Changed supplied file: {name}')


def inspect(p):
    with Image.open(p) as im:
        im.load()
        require(getattr(im, 'n_frames', 1) == 1, f'Multiple frames: {p}')
        return dict(width=im.width, height=im.height, exif_orientation=im.getexif().get(274, 1), format=im.format)


def csv_write(p, rows, fields):
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def shared_check(root):
    script = ROOT.parents[1] / 'tools/relationship_fixtures.py'
    spec = importlib.util.spec_from_file_location('hazy_fixture_check', script)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.validate(root)




def verify(root):
    checksum_file(root, 'provenance/construction/SOURCE_SHA256SUMS.txt')
    checksum_file(root, 'provenance/construction/V06_SHA256SUMS.txt')
    rows, probes, summary = shared_check(root)
    require(len(rows) == 42 and len(probes) == 54, 'Expected 42 images and 54 probes')
    record = json.loads(safe(root, 'provenance/construction.json').read_text())
    require(digest(safe(root, record['recipes'])) == record['recipes_sha256'], 'Recipe changed since build')
    nodes = record['artifacts']
    seen = set()
    for node in nodes:
        name = node['file']; require(name not in seen, f'Duplicate artifact: {name}'); seen.add(name)
        p = safe(root, name)
        require(digest(p) == node['sha256'], f'Changed artifact: {name}')
        require(all(inspect(p)[k] == node[k] for k in ('width', 'height', 'exif_orientation', 'format')), f'Artifact dimensions changed: {name}')
        for dependency in node['inputs']:
            require(dependency in seen or safe(root, dependency).is_file(), f'Missing input: {dependency}')
    require(len(record['finals']) == 42 and len({(f['source_id'], f['variant_id']) for f in record['finals']}) == 42, 'Incomplete mappings')
    for final in record['finals']:
        require(digest(safe(root, final['file'])) == final['sha256'], 'Final hash changed')
        if final['variant_id'] == 'v03':
            prefix = f"previews/stages/{final['source_id']}/"
            base = Image.open(safe(root, prefix + 'prepared.png')).convert('RGB')
            edited = Image.open(safe(root, prefix + 'v03-replacement.png')).convert('RGB')
            mask = Image.open(safe(root, prefix + 'v03-allowed.png')).convert('L')
            outside = Image.composite(edited, base, ImageOps.invert(mask))
            require(ImageChops.difference(base, outside).getbbox() is None, 'Replacement changed pixels outside mask')
            require(ImageChops.difference(base, edited).getbbox() is not None, 'Replacement is empty')
            v02 = next(f for f in record['finals'] if f['source_id'] == final['source_id'] and f['variant_id'] == 'v02')
            require(v02['post_pipeline'] == final['post_pipeline'], 'v02/v03 processing differs')
        if final['variant_id'] == 'v06':
            require(final['spatial_correspondence'] is None and digest(safe(root, final['supplied_file'])) == final['sha256'], 'v06 import differs')
            require(digest(safe(root, final['prompt_file'])) == final['prompt_sha256'], 'v06 prompt differs')
    require({f['file'] for f in record['finals']} == {r['file'] for r in rows}, 'Final mapping differs from manifest')
    return dict(images=len(rows), sources=6, local_variants=30, supplied_generations=6, probes=len(probes), retained_artifacts=len(nodes), outside_mask_checks=6)


class Builder:
    def __init__(self, stage):
        self.stage = stage
        self.recipe = json.loads((ROOT / 'provenance/recipes.json').read_text())
        font = self.recipe['font']
        require(digest(Path(font['path'])) == font['sha256'], 'Font hash differs; no fallback')
        require(features.version('pil') == '12.0.0', 'Use pinned Pillow 12.0.0')
        self.sources = json.loads((ROOT / 'provenance/construction/source-manifest.json').read_text())['sources']
        self.imports = json.loads((ROOT / 'provenance/v06-imports.json').read_text())['items']
        self.artifacts = []; self.finals = []; self.rows = []; self.prepared = {}; self.mapping = {}
        self.record = dict(schema_version=1, fixture_id=FIXTURE, recipes='provenance/recipes.json',
                           recipes_sha256=digest(ROOT / 'provenance/recipes.json'),
                           generator_sha256=digest(Path(__file__)),
                           coordinate_frame=self.recipe['coordinate_frame'],
                           environment=dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                               libraries={name: features.version(name) for name in ('pil','jpg','zlib','littlecms2','freetype2')},
                               jpeg_codec=features.version_feature('libjpeg_turbo'), font=self.recipe['font']),
                           command=shlex.join([sys.executable, str(Path(__file__).relative_to(ROOT.parents[2])), *sys.argv[1:]]),
                           preparations=[], artifacts=self.artifacts, finals=self.finals)

    def font(self, size):
        return ImageFont.truetype(self.recipe['font']['path'], size, index=0)

    def save(self, name, im, inputs, operation, **parameters):
        p = safe(self.stage, name); p.parent.mkdir(parents=True, exist_ok=True)
        im.save(p, **self.recipe['png'])
        self.node(name, inputs, operation, parameters)
        return name

    def node(self, name, inputs, operation, parameters):
        p = safe(self.stage, name)
        self.artifacts.append(dict(file=name, sha256=digest(p), inputs=inputs, operation=operation,
                                   parameters=parameters, **inspect(p)))

    def copy(self, name, source, inputs, operation):
        p = safe(self.stage, name); p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, p); self.node(name, inputs, operation, dict(preprocessing='none'))

    def text(self, im, text, center, size, fill='white', stroke_width=0, stroke_fill=None):
        draw = ImageDraw.Draw(im); font = self.font(size)
        bounds = draw.textbbox(center, text, font=font, anchor='mm', stroke_width=stroke_width)
        require(0 <= bounds[0] < bounds[2] <= im.width and 0 <= bounds[1] < bounds[3] <= im.height, f'Clipped text: {text}')
        draw.text(center, text, font=font, anchor='mm', fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        return dict(text=text, center=center, size=size, bounds=bounds, fill=fill, anchor='mm', stroke_width=stroke_width, stroke_fill=stroke_fill)

    def crop(self, im, box):
        l,t,r,b = box
        require(0 <= l < r <= im.width and 0 <= t < b <= im.height, f'Invalid crop: {box} on {im.size}')
        return im.crop(box)

    def fit(self, canvas, piece, slot, crop=None):
        l,t,r,b = slot; factor = min((r-l)/piece.width, (b-t)/piece.height)
        size = (max(1,round(piece.width*factor)), max(1,round(piece.height*factor)))
        x,y = l+(r-l-size[0])//2, t+(b-t-size[1])//2
        canvas.paste(piece.resize(size, LANCZOS), (x,y))
        sx,sy = size[0]/piece.width, size[1]/piece.height
        box = crop or [0,0,piece.width,piece.height]
        return dict(crop=box, slot=slot, placement=[x,y,x+size[0],y+size[1]], resampler='LANCZOS',
                    forward_pixel_edge_transform=[[sx,0,x-sx*box[0]],[0,sy,y-sy*box[1]],[0,0,1]])

    def footprint(self, name, size, mapping, inputs):
        mask = Image.new('L', size, 0); box = mapping['placement']
        mask.paste(255, box)
        self.save(name, mask, inputs, 'geometric_source_footprint', mapping=mapping,
                  source_area_fraction=(box[2]-box[0])*(box[3]-box[1])/(size[0]*size[1]))
        return name

    def prepare(self):
        for s in self.sources:
            sid = s['source_id']; p = ROOT / s['file']
            require(digest(p) == s['byte_sha256'], f'Source mismatch: {sid}')
            with Image.open(p) as original:
                original.load(); profile = original.info.get('icc_profile'); oriented = ImageOps.exif_transpose(original)
                alpha = oriented.convert('RGBA').getchannel('A')
                rgb = oriented.convert('RGB')
                if profile:
                    rgb = ImageCms.profileToProfile(rgb, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                        ImageCms.createProfile('sRGB'), renderingIntent=0, outputMode='RGB', flags=0)
                white = Image.new('RGB', rgb.size, 'white'); white.paste(rgb, mask=alpha); rgb = white
                oriented_size = rgb.size
                if sid != 'm01':
                    rgb.thumbnail((1600,1600), LANCZOS)
                name = f'previews/stages/{sid}/prepared.png'
                self.save(name, rgb, [s['file']], 'prepare', apply_exif_once=s['exif_orientation'],
                    stored_dimensions=list(original.size), oriented_dimensions=list(oriented_size),
                    color_conversion='ICC to sRGB via LittleCMS, perceptual intent 0' if profile else 'assume sRGB',
                    icc_sha256=hashlib.sha256(profile).hexdigest() if profile else None,
                    flatten='alpha over white after color conversion', mode='RGB', max_edge=1600 if sid != 'm01' else None,
                    resampler='Pillow thumbnail LANCZOS reducing_gap=2.0', prepared_dimensions=list(rgb.size))
                self.record['preparations'].append(dict(source_id=sid, source=s['file'], prepared=name))
                self.prepared[sid] = rgb

    def template(self):
        r = self.recipe['post']; im = Image.new('RGB', r['canvas'], r['background']); d = ImageDraw.Draw(im)
        d.rounded_rectangle([45,35,1035,1045], radius=24, fill='white', outline='#d0d3d8', width=2)
        d.ellipse([90,70,165,145], fill='#b8c4cc'); d.ellipse([112,80,143,111], fill='#526572')
        d.rounded_rectangle([102,113,153,141],radius=16,fill='#526572')
        texts = []
        for text,center,size,fill in [(r['display_name'],[335,90],r['name_size'],'#17181b'),(r['handle'],[315,133],r['handle_size'],'#59636e'),(r['text'],[320,215],r['post_size'],'#17181b')]:
            texts.append(self.text(im,text,center,size,fill))
        d.rectangle(r['slot'], fill=r['padding']); d.line([90,925,990,925], fill='#dce0e4', width=2)
        for x in (140,445,750):
            d.ellipse([x,956,x+27,980], outline='#59636e', width=3)
        for label,x in [('Reply',225),('Share',530),('Save',835)]:
            texts.append(self.text(im,label,[x,970],r['footer_size'],'#59636e'))
        name = self.save('previews/stages/template.png', im, [], 'draw_fictional_post', recipe=r, texts=texts,
                         interface_rectangles=[[45,35,1035,1045],[90,70,165,145],[90,925,990,1005]])
        return im, name

    def finish(self, sid, variant, im=None, inputs=None, extra=None, supplied=None):
        source = next(s for s in self.sources if s['source_id'] == sid)
        ext = Path(source['file']).suffix if variant == 'source' else '.png'
        name = 'images/' + hashlib.sha256(f'{FIXTURE}:{sid}:{variant}'.encode()).hexdigest()[:20] + ext
        if supplied:
            self.copy(name, ROOT / supplied, inputs or [supplied], 'byte_copy')
        else:
            self.save(name, im, inputs, 'final_png', encoding=self.recipe['png'])
        parents = [sid]
        if variant == 'v03': parents.append(self.recipe['donors'][self.recipe['sources'][sid]['replacement']['donor']]['source'])
        transform = 'description_mediated_generation' if variant == 'v06' else variant
        relation = 'composite' if variant == 'v03' else ('description_mediated_generation' if variant == 'v06' else ('source' if variant == 'source' else 'pixel_derivative'))
        measured = inspect(self.stage / name)
        row = dict(file=name, batch='batch-1', family_id=sid if len(parents)==1 else '', scene_id='', parents='|'.join(parents),
                   transformation=transform, relation_kind=relation, origin_count=len(parents), **measured,
                   byte_sha256=digest(self.stage/name), pixels_rgb_sha256='')
        self.rows.append(row); self.mapping[sid,variant] = name
        final = dict(source_id=sid, variant_id=variant, source_parents=parents, file=name,
                     sha256=row['byte_sha256'], inputs=inputs or [supplied])
        final.update(extra or {}); self.finals.append(final)
        return name

    def wrapped(self, sid, variant, base, base_name, template, template_name):
        r = self.recipe['sources'][sid]; prefix = f'previews/stages/{sid}/{variant}-'
        box = r['post_crop']; crop = self.crop(base,box)
        cropped = self.save(prefix+'crop.png',crop,[base_name],'crop',box=box,coordinate_frame='prepared')
        clean = template.copy(); mapping = self.fit(clean,crop,self.recipe['post']['slot'],box)
        name = self.save(prefix+'wrapped.png',clean,[cropped,template_name],'fit_into_post',mapping=mapping)
        footprint = self.footprint(prefix+'footprint.png',clean.size,mapping,[cropped,name])
        low = clean.resize((540,540),LANCZOS); jpeg = safe(self.stage,prefix+'low.jpg')
        low.save(jpeg,format='JPEG',quality=35,subsampling=2,optimize=False,progressive=False)
        self.node(prefix+'low.jpg',[name],'downscale_and_jpeg',self.recipe['degradation'])
        with Image.open(jpeg) as decoded:
            final = decoded.convert('RGB').resize((1080,1080),Image.Resampling.BILINEAR)
        pipeline = dict(crop=box, template=template_name, mapping=mapping, degradation=self.recipe['degradation'], font=self.recipe['font'])
        return final, prefix+'low.jpg', dict(post_pipeline=pipeline, spatial_correspondence=dict(clean_footprint=footprint,
            note='Geometric coverage before global resize/JPEG; compression has no exact per-pixel correspondence.'))

    def variants(self,sid,template,template_name):
        base = self.prepared[sid]; r = self.recipe['sources'][sid]; prefix=f'previews/stages/{sid}/'; prepared=prefix+'prepared.png'
        # v01: selected source -> clockwise rotation -> grayscale frame -> text.
        rule=self.recipe['v01']; box=r['v01_crop'] or [0,0,base.width,base.height]; crop=self.crop(base,box)
        selected=self.save(prefix+'v01-crop.png',crop,[prepared],'crop',box=box,coordinate_frame='prepared')
        rotated=crop.rotate(-17,Image.Resampling.BICUBIC,expand=True,fillcolor=rule['corner_fill'])
        angle=math.radians(17); c=round(math.cos(angle),15); s=round(math.sin(angle),15)
        transform=[[c,-s,rotated.width/2-c*crop.width/2+s*crop.height/2],
                   [s,c,rotated.height/2-s*crop.width/2-c*crop.height/2],[0,0,1]]
        rotation=self.save(prefix+'v01-rotated.png',rotated,[selected],'rotate',angle_clockwise=17,resampler='BICUBIC',expand=True,
                          fill=rule['corner_fill'],forward_pixel_edge_transform=transform,coordinate_frame='selected crop')
        gray=ImageOps.grayscale(rotated).convert('RGB'); canvas=Image.new('RGB',rule['canvas'],rule['frame'])
        mapping=self.fit(canvas,gray,rule['slot'])
        framed=self.save(prefix+'v01-framed.png',canvas,[rotation],'grayscale_and_frame',conversion='Pillow RGB to L: 0.299R + 0.587G + 0.114B',mapping=mapping,frame_color=rule['frame'])
        footprint=Image.new('L',crop.size,255).rotate(-17,Image.Resampling.BICUBIC,expand=True,fillcolor=0)
        mask=Image.new('L',canvas.size,0); p=mapping['placement']; mask.paste(footprint.resize((p[2]-p[0],p[3]-p[1]),LANCZOS),p[:2])
        mask_name=self.save(prefix+'v01-footprint.png',mask,[selected,rotation,framed],'transform_source_footprint',rotation=transform,placement=mapping,
                            convention='Interpolated geometric coverage; corner fill and frame are zero, before stamp')
        overlay=Image.new('RGBA',canvas.size); text_record=self.text(overlay,rule['stamp'],rule['stamp_center'],rule['stamp_size'],rule['stamp_color'],rule['stroke_width'],rule['stroke_fill'])
        stamp=self.save(prefix+'v01-stamp.png',overlay,[],'draw_text',text=text_record)
        stamp_mask=self.save(prefix+'v01-stamp-mask.png',overlay.getchannel('A'),[stamp],'extract_alpha')
        final=Image.alpha_composite(canvas.convert('RGBA'),overlay).convert('RGB')
        self.finish(sid,'v01',final,[framed,stamp],dict(spatial_correspondence=dict(source_crop=box,rotation=transform,placement=mapping,footprint=mask_name,occlusion_mask=stamp_mask)))
        # v02 and v03 share crop/template/degradation exactly.
        out,inp,extra=self.wrapped(sid,'v02',base,prepared,template,template_name); self.finish(sid,'v02',out,[inp],extra)
        replacement=r['replacement']; donor_rule=self.recipe['donors'][replacement['donor']]; donor=self.prepared[donor_rule['source']]
        donor_crop=self.crop(donor,donor_rule['crop']); donor_name=self.save(prefix+'v03-donor.png',donor_crop,[f"previews/stages/{donor_rule['source']}/prepared.png"],'crop',box=donor_rule['crop'],coordinate_frame='donor prepared')
        alpha=Image.new('L',donor_crop.size,0); ImageDraw.Draw(alpha).polygon([tuple(p) for p in donor_rule['polygon']],fill=255)
        alpha_name=self.save(prefix+'v03-donor-mask.png',alpha,[donor_name],'polygon_mask',vertices=donor_rule['polygon'],coordinate_frame='donor crop',edge='hard')
        target=replacement['target']; l,t,rr,b=target; crop_box=r['post_crop']
        require(crop_box[0]<=l<rr<=crop_box[2] and crop_box[1]<=t<b<=crop_box[3],'Replacement outside retained crop')
        allowed=Image.new('L',base.size,0); allowed.paste(255,target)
        allowed_name=self.save(prefix+'v03-allowed.png',allowed,[prepared],'allowed_edit_region',box=target,coordinate_frame='base prepared')
        edited=base.copy(); edit_inputs=[prepared,donor_name,alpha_name,allowed_name]
        if replacement.get('patch_from'):
            patch=self.crop(base,replacement['patch_from']); require(patch.size==(rr-l,b-t),'Patch size mismatch'); edited.paste(patch,(l,t))
            patch_name=self.save(prefix+'v03-patched.png',edited,[prepared,allowed_name],'copy_background_patch',source_box=replacement['patch_from'],destination_box=target,coordinate_frame='base prepared')
            edit_inputs.append(patch_name)
        layer=Image.new('RGBA',base.size); cut=donor_crop.resize((rr-l,b-t),LANCZOS).convert('RGBA'); cut.putalpha(alpha.resize((rr-l,b-t),Image.Resampling.NEAREST)); layer.paste(cut,(l,t))
        dc=donor_rule['crop']; sx,sy=(rr-l)/donor_crop.width,(b-t)/donor_crop.height
        donor_transform=[[sx,0,l-sx*dc[0]],[0,sy,t-sy*dc[1]],[0,0,1]]
        layer_name=self.save(prefix+'v03-overlay.png',layer,[donor_name,alpha_name],'position_donor',target=target,color_resampler='LANCZOS',mask_resampler='NEAREST',coordinate_frame='base prepared',donor_crop=dc,forward_pixel_edge_transform=donor_transform)
        edited=Image.alpha_composite(edited.convert('RGBA'),layer).convert('RGB')
        outside=Image.composite(edited,base,ImageOps.invert(allowed)); require(ImageChops.difference(base,outside).getbbox() is None,'Outside-mask invariant failed')
        clean=self.save(prefix+'v03-replacement.png',edited,edit_inputs+[layer_name],'composite_inside_mask',outside_mask_equal=True,operation_order=['optional copied patch','positioned donor over base'])
        out,inp,extra=self.wrapped(sid,'v03',edited,clean,template,template_name)
        post_mapping=extra['post_pipeline']['mapping']; placement=post_mapping['placement']
        donor_coverage=Image.new('L',(1080,1080),0)
        donor_coverage.paste(layer.getchannel('A').crop(crop_box).resize((placement[2]-placement[0],placement[3]-placement[1]),LANCZOS),placement[:2])
        donor_footprint=self.save(prefix+'v03-donor-footprint.png',donor_coverage,[layer_name,prefix+'v03-wrapped.png'],'donor_coverage_before_jpeg',mapping=post_mapping)
        with Image.open(self.stage/(prefix+'v03-footprint.png')) as whole:
            base_coverage=ImageChops.subtract(whole,donor_coverage)
        base_footprint=self.save(prefix+'v03-base-footprint.png',base_coverage,[prefix+'v03-footprint.png',donor_footprint],'base_family_coverage_before_jpeg',note='Includes copied background patch from same base family when present')
        extra['replacement']=dict(donor=donor_rule,target=target,donor_to_prepared_transform=donor_transform,allowed_mask=allowed_name,positioned_overlay=layer_name,clean_stage=clean,outside_mask_equal=True,base_family_footprint=base_footprint,donor_family_footprint=donor_footprint)
        self.finish(sid,'v03',out,[inp],extra)
        # v04: reaction crop and two large caption bands.
        rule=self.recipe['v04']; box=r['reaction_crop']; crop=self.crop(base,box)
        cropped=self.save(prefix+'v04-crop.png',crop,[prepared],'crop',box=box,coordinate_frame='prepared',area_fraction=crop.width*crop.height/(base.width*base.height))
        canvas=Image.new('RGB',rule['canvas'],rule['background']); ImageDraw.Draw(canvas).rectangle(rule['slot'],fill=rule['padding'])
        mapping=self.fit(canvas,crop,rule['slot'],box); layout=self.save(prefix+'v04-layout.png',canvas,[cropped],'caption_layout',mapping=mapping,bands=rule['bands'])
        footprint=self.footprint(prefix+'v04-footprint.png',canvas.size,mapping,[cropped,layout])
        overlay=Image.new('RGBA',canvas.size); texts=[self.text(overlay,txt,[540,y],rule['font_size'],rule['text_color']) for txt,y in zip(rule['captions'],[125,955])]
        captions=self.save(prefix+'v04-captions.png',overlay,[],'draw_text',texts=texts)
        capmask=self.save(prefix+'v04-caption-mask.png',overlay.getchannel('A'),[captions],'extract_alpha')
        self.finish(sid,'v04',Image.alpha_composite(canvas.convert('RGBA'),overlay).convert('RGB'),[layout,captions],dict(spatial_correspondence=dict(mapping=mapping,footprint=footprint,caption_mask=capmask)))
        # v05: two independently mapped pieces, reversed order.
        rule=self.recipe['v05']; canvas=Image.new('RGB',rule['canvas'],rule['background']); pieces=[]; names=[]; maps=[]
        for i,box in enumerate(r['pieces']):
            crop=self.crop(base,box); pieces.append(crop); names.append(self.save(prefix+f'v05-piece-{i}.png',crop,[prepared],'crop',box=box,coordinate_frame='prepared'))
        a,b=r['pieces']; overlap=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
        for slot,index in zip(rule['slots'],rule['piece_order']):
            ImageDraw.Draw(canvas).rectangle(slot,fill=rule['padding']); mapping=self.fit(canvas,pieces[index],slot,r['pieces'][index]); mapping['piece']=index; maps.append(mapping)
        layout=self.save(prefix+'v05-layout.png',canvas,names,'reverse_two_pieces',mappings=maps,source_overlap_pixels=overlap,gutter=[520,170,560,650],padding=rule['padding'])
        footprints=[self.footprint(prefix+f'v05-footprint-{i}.png',canvas.size,m,[names[m['piece']],layout]) for i,m in enumerate(maps)]
        overlay=Image.new('RGBA',canvas.size); texts=[self.text(overlay,txt,[x,95],rule['font_size'],rule['text_color']) for txt,x in zip(rule['captions'],[280,800])]
        captions=self.save(prefix+'v05-captions.png',overlay,[],'draw_text',texts=texts,caption_rectangles=rule['caption_rectangles'])
        self.finish(sid,'v05',Image.alpha_composite(canvas.convert('RGBA'),overlay).convert('RGB'),[layout,captions],dict(spatial_correspondence=dict(piece_mappings=maps,footprints=footprints,source_overlap_pixels=overlap)))

    def metadata(self):
        manifest=dict(schema_version=1,fixture_id=FIXTURE,kind='derivatives',description='Variants: six originals, thirty constructed edits, six unchanged description-mediated generations. Provenance is not a similarity verdict.',images=self.rows)
        write_json(self.stage/'manifest.json',manifest); csv_write(self.stage/'manifest.csv',self.rows,COLS)
        probes=[]
        def pair(a,b,relation,note):
            probes.append(dict(file_a=self.mapping[a],file_b=self.mapping[b],relation=relation,interpretation=note+'; no expected score, alignment, or membership'))
        for sid in self.prepared:
            for variant in ('v01','v02','v03','v04','v05','v06'):
                note='source → description prompt → supplied generation; no asserted pixel correspondence' if variant=='v06' else f'source → constructed {variant}'
                pair((sid,'source'),(sid,variant),'diagnostic' if variant in ('v03','v06') else 'same_origin_'+variant,note)
            pair((sid,'v02'),(sid,'v03'),'diagnostic','same crop, fictional wrapper and degradation; local donor replacement differs')
            donor=self.recipe['donors'][self.recipe['sources'][sid]['replacement']['donor']]['source']
            pair((donor,'source'),(sid,'v03'),'diagnostic',f'{donor} supplied cutout pixels in two-parent composite')
        for a,b in [('m01','m02'),('m03','m04'),('m05','m06')]:
            for variant in ('v01','v02'):
                pair((a,variant),(b,variant),'diagnostic',f'distinct sources with shared {variant} treatment')
        csv_write(self.stage/'probes.csv',probes,PAIR_COLS)
        focus=probes[:8]+[probes[13],probes[21],probes[29],probes[37],probes[45],probes[48],probes[49]]
        write_json(self.stage/'selections.json',dict(description='Every treatment, all supplied generations, comic composite, donor and shared-wrapper diagnostics.',pairs=focus,known_shift_families=[]))
        batches=self.stage/'batches'; batches.mkdir()
        (batches/'batch-1.txt').write_text(''.join(r['file']+'\n' for r in self.rows))
        for name in ('smoke','medium'):
            (batches/f'{name}.txt').write_text(''.join(r['file']+'\n' for r in self.rows if r['transformation']=='source'))
        paths=sorted([r['file'] for r in self.rows]+[s['file'] for s in self.sources])
        (self.stage/'SHA256SUMS.txt').write_text(''.join(digest(self.stage/p)+'  '+p+'\n' for p in paths))
        write_json(self.stage/'provenance/construction.json',self.record)

    def sheets(self):
        for sid in self.prepared:
            entries=[(v,self.mapping[sid,v]) for v in ('source','v01','v02','v03','v04','v05','v06')]
            self.sheet(f'previews/review/{sid}-finals.jpg',entries,4,400,430)
            stages=[('prepared',f'previews/stages/{sid}/prepared.png'),('donor mask',f'previews/stages/{sid}/v03-donor-mask.png'),('allowed mask',f'previews/stages/{sid}/v03-allowed.png'),('replacement',f'previews/stages/{sid}/v03-replacement.png'),('clean post',f'previews/stages/{sid}/v02-wrapped.png'),('replacement post',f'previews/stages/{sid}/v03-wrapped.png'),('grayscale frame',f'previews/stages/{sid}/v01-framed.png'),('reordered panels',f'previews/stages/{sid}/v05-layout.png')]
            self.sheet(f'previews/review/{sid}-stages.jpg',stages,4,400,430)

    def sheet(self,name,entries,cols,w,h):
        sheet=Image.new('RGB',(cols*w,math.ceil(len(entries)/cols)*h),'#e5e5e5'); d=ImageDraw.Draw(sheet)
        for i,(label,file) in enumerate(entries):
            with Image.open(self.stage/file) as im:
                im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((w-20,h-55),LANCZOS)
                x,y=(i%cols)*w,(i//cols)*h; sheet.paste(im,(x+(w-im.width)//2,y+10+(h-55-im.height)//2)); d.text((x+12,y+h-35),label,font=self.font(23),fill='black')
        p=self.stage/name; p.parent.mkdir(parents=True,exist_ok=True); sheet.save(p,quality=90,subsampling=0)


def build(name):
    require(re.fullmatch(r'[a-zA-Z0-9_-]+',name),'Use a simple stage name')
    checksum_file(ROOT,'provenance/construction/SOURCE_SHA256SUMS.txt'); checksum_file(ROOT,'provenance/construction/V06_SHA256SUMS.txt')
    stage=safe(ROOT,'previews/build-'+name); require(not stage.exists(),'Stage exists; choose a fresh name'); stage.mkdir()
    try:
        b=Builder(stage)
        copy_names=['provenance/construction/SOURCE_SHA256SUMS.txt','provenance/construction/V06_SHA256SUMS.txt','sources.csv','SOURCES.md','provenance/construction/source-manifest.json','provenance/v06-imports.json','provenance/recipes.json']
        copy_names += [s['file'] for s in b.sources]
        copy_names += [i[k] for i in b.imports for k in ('supplied_image_file','prompt_file')]
        for file in copy_names:
            dest=safe(stage,file); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(safe(ROOT,file),dest)
        b.prepare(); template,template_name=b.template()
        for s in b.sources:
            sid=s['source_id']; b.finish(sid,'source',supplied=s['file']); b.variants(sid,template,template_name)
            imp=next(i for i in b.imports if i['source_id']==sid)
            b.finish(sid,'v06',supplied=imp['supplied_image_file'],inputs=[imp['source_file'],imp['prompt_file'],imp['supplied_image_file']],
                extra=dict(supplied_file=imp['supplied_image_file'],prompt_file=imp['prompt_file'],prompt_sha256=imp['prompt_sha256'],
                           lineage='source → exact supplied description → supplied generation; byte-copy import',
                           generation_metadata=imp['generation_metadata'],rights=imp['rights'],spatial_correspondence=None))
        b.metadata(); b.sheets(); report=verify(stage); write_json(stage/'validation.json',dict(status='structural_checks_passed',**report))
        print(json.dumps(dict(stage=str(stage.relative_to(ROOT)),**report),indent=2))
    except Exception as error:
        write_json(stage/'FAILED.json',dict(status='incomplete',error=str(error))); raise


def publish(name):
    stage=safe(ROOT,'previews/build-'+name); verify(stage)
    names=['images','batches','manifest.json','manifest.csv','probes.csv','selections.json','SHA256SUMS.txt','provenance/construction.json','previews/stages','previews/review']
    for name in names:
        require(not safe(ROOT,name).exists(),f'Publication refuses existing destination: {name}')
    created=[]
    try:
        for name in names:
            source=safe(stage,name); dest=safe(ROOT,name); dest.parent.mkdir(parents=True,exist_ok=True)
            if source.is_dir(): shutil.copytree(source,dest)
            else: shutil.copyfile(source,dest)
            created.append(name)
        result=verify(ROOT); write_json(ROOT/'provenance/publication.json',dict(status='complete',stage=str(stage.relative_to(ROOT)),created=created,validation=result))
        print(json.dumps(result,indent=2))
    except Exception as error:
        write_json(ROOT/'provenance/publication.json',dict(status='incomplete',created=created,error=str(error))); raise


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    for name in ('build','publish'):
        sp=sub.add_parser(name); sp.add_argument('--stage',required=True)
    sp=sub.add_parser('check'); sp.add_argument('--stage')
    args=p.parse_args()
    if args.command=='build': build(args.stage)
    elif args.command=='publish': publish(args.stage)
    else: print(json.dumps(verify(safe(ROOT,'previews/build-'+args.stage) if args.stage else ROOT),indent=2))


if __name__=='__main__':
    main()
