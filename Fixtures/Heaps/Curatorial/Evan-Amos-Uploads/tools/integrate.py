#!/usr/bin/env python3
"""Publish one exhaustive-category leaf in a fresh stage and validate it offline."""
import argparse
from collections import Counter
import csv
import fcntl
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
from urllib.parse import quote
from PIL import Image,ImageDraw,ImageOps
import evan as e
import population
import review
import relationships
import audit
from transport import dump,sha,safe

IMAGE_FIELDS='file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
SOURCE_FIELDS='family_id source_filename scene_id subject credit_status source_sha256 width height exif_orientation source_url preprocessing view exposure_id original_path'.split()
PROBE_FIELDS='file_a file_b relation interpretation'.split()
require=e.require
read=e.read


def csv_write(path,rows,fields):
    with path.open('w',newline='')as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)


def csv_read(path):
    with path.open(newline='')as stream:return list(csv.DictReader(stream))


def imports():
    rows=[];members=e.candidates();evidence=e.evidence();reviews=read(e.ROOT/'provenance/rights-review.json')
    for cid in e.selection()['included']:
        path=e.ROOT/f'provenance/source-receipts/{cid}.json'
        if not path.exists():continue
        receipt=read(path);page=evidence[cid]['page'];info=page['imageinfo'][0];r=reviews[cid]
        rows.append(dict(**receipt,source_path=receipt['path'],final_file='images/'+Path(receipt['path']).name,family_id='evan-'+cid,
                         frozen_title=members[cid]['frozen_title'],category_pageid=members[cid]['category_pageid'],category_timestamp=members[cid]['category_timestamp'],
                         source_url='https://commons.wikimedia.org/wiki/'+quote(page['title'].replace(' ','_'),safe=':/'),original_url=info['url'],
                         file_timestamp=info['timestamp'],file_page_revision=page['revisions'][0]['revid'],file_page_revision_timestamp=page['revisions'][0]['timestamp'],
                         review_metadata_path=r['metadata_path'],review_metadata_sha256=r['metadata_sha256'],source_independence_confirmed=None,
                         **{k:r[k]for k in ('reported_artist','reported_author_wikitext','original_creator','digital_modifier','copyright_holder','uploader_current_file_revision','creator_basis','credit','license','license_url','usage_terms','rights_basis','rights_limit','restrictions')}))
    return rows


def records(imported):
    images=[];sources=[]
    for r in imported:
        images.append(dict(file=r['final_file'],batch='batch-1',family_id=r['family_id'],scene_id='',parents=r['family_id'],transformation='source',relation_kind='curatorial_selected',origin_count=1,
                           **{k:r[k]for k in ('width','height','exif_orientation','format')},byte_sha256=r['sha256'],pixels_rgb_sha256=''))
        sources.append(dict(family_id=r['family_id'],source_filename=Path(r['source_path']).name,scene_id='',subject=r['canonical_title'],credit_status=f"{r['reported_artist'] or 'unknown artist'}; {r['license']}",
                            source_sha256=r['sha256'],width=r['width'],height=r['height'],exif_orientation=r['exif_orientation'],source_url=r['source_url'],
                            preprocessing=f"API request {r['requested_edge']}px; {r['rendition']}; decoded {r['width']}x{r['height']} {r['format']}; local byte copy only.",view='',exposure_id='',original_path=r['frozen_title']))
    return images,sources


def events():
    path=e.ROOT/'provenance/http_log.jsonl'
    return [json.loads(line)for line in path.read_text().splitlines()]if path.exists()else[]


def summary():
    chosen=e.selection();imported=imports();acquired={r['candidate_id']for r in imported};metadata=e.evidence();reviews=read(e.ROOT/'provenance/rights-review.json');pending=[]
    failures=[r for r in events()if r.get('error')]
    unavailable=[read(p)for p in sorted((e.ROOT/'provenance/unavailable').glob('*.json'))]
    for cid in chosen['included']:
        if cid in acquired:continue
        record=dict(candidate_id=cid,frozen_title=e.candidates()[cid]['frozen_title'],status='pending',cause='not_acquired')
        if cid not in metadata:record['cause']='metadata_pending'
        elif cid not in reviews:record['cause']='rights_review_pending'
        elif reviews[cid]['status']!='ready':record.update(status='blocked',cause='rights_or_identity',details=reviews[cid]['blocking_reasons'])
        related=[r for r in failures if r.get('candidate_id',r.get('key'))==cid]
        sizes=[r for r in unavailable if r['candidate_id']==cid]
        if related:record.update(cause='acquisition_failure',failures=related)
        elif sizes:record.update(cause='unavailable_rendition',attempts=sizes)
        pending.append(record)
    active=(e.ROOT/'provenance/last_transport_error.json').exists()
    return dict(status='complete'if not pending and not active else'partial',category=population.CATEGORY,members=len(e.order()),included=len(chosen['included']),excluded_by_user=chosen['counts']['excluded_by_user'],
                absent_exclusion_titles=chosen['absent_exclusion_titles'],metadata_entries=len(metadata),resolved_page_ids=len({r['page'].get('pageid')for r in metadata.values()}),
                identity_discrepancies=[cid for cid,r in metadata.items()if r['redirected']or r['page'].get('pageid')!=e.candidates()[cid]['category_pageid']],
                acquired=len(acquired),pending=len(pending),pending_by_cause=dict(Counter(r['cause']for r in pending)),pending_items=pending,active_stop_latch=active,
                failed_transfers=sum(r.get('kind')in('source','api')for r in failures),post_transfer_validation_stops=sum(r.get('kind')=='decode'for r in failures),automatic_retries=0,
                acquired_formats=dict(Counter(r['format']for r in imported)),requested_edges=dict(Counter(str(r['requested_edge'])for r in imported)),alpha_inputs=sum(r['has_alpha']for r in imported),
                roles={role:dict(Counter(reviews[cid][role]or'unknown'for cid in chosen['included']if cid in reviews))for role in ('original_creator','digital_modifier','copyright_holder','uploader_current_file_revision')})


def credits(imported):
    text=['# Acquired Evan-Amos category members','',
          'The category is a membership source, not an authorship assertion. File-specific Commons claims are retained here and in raw API/file-page evidence. No blanket license or independent authentication is claimed. Related files and different formats remain included.','']
    for r in imported:
        text += [f"## {r['candidate_id']} — {r['canonical_title']}",'',
                 f"- [File page]({r['source_url']}); [exact rendition]({r['url']}).",
                 f"- Frozen category member: {r['frozen_title']}, page ID {r['category_pageid']}; category membership timestamp {r['category_timestamp']} (not a capture date).",
                 f"- Reported Artist: {r['reported_artist'] or 'unknown'}. Credit: {r['credit'] or 'unknown'}.",
                 f"- Original creator: {r['original_creator'] or 'unknown'}; digital modifier: {r['digital_modifier'] or 'unknown'}; copyright holder: {r['copyright_holder'] or 'unknown'}; current file-version uploader: {r['uploader_current_file_revision'] or 'unknown'}.",
                 f"- Role basis: {r['creator_basis']}",
                 f"- License claim: {r['license']}; terms URL: {r['license_url'] or 'not supplied; retained PD-self declaration'}. Restrictions: {r['restrictions'] or 'none supplied'}.",
                 f"- Rights evidence: {r['rights_basis']} {r['rights_limit']}",
                 f"- Original: {r['original_mime']}, SHA-1 `{r['original_sha1']}`, file revision {r['file_timestamp']}; file-page revision {r['file_page_revision']}.",
                 f"- Acquired: {r['format']}, {r['width']} × {r['height']}, mode {r['mode']}, alpha {r['has_alpha']}, {r['bytes']} bytes.",
                 f"- Source `{r['source_path']}`; input `{r['final_file']}`; SHA-256 `{r['sha256']}`.",
                 f"- Rights evidence `{r['review_metadata_path']}`; rendition evidence `{r['metadata_path']}`.",'']
    return '\n'.join(line.rstrip()for line in '\n'.join(text).splitlines()).rstrip()+'\n'


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


def diagnostic_check():
    path=e.ROOT/'provenance/error_acknowledgements.jsonl';acks=[json.loads(line)for line in path.read_text().splitlines()]if path.exists()else[]
    latch=e.ROOT/'provenance/last_transport_error.json';active=read(latch)if latch.exists()else None;failures=[r for r in events()if r.get('error')]
    for ack in acks:require(ack['diagnosis'].strip()and ack['failure']in failures,'Acknowledgement lacks matching failure')
    for failure in failures:
        require(failure==active or any(a['failure']==failure for a in acks),'Failure lacks acknowledgement or active latch')
        if failure.get('partial_path'):
            body=safe(e.ROOT,failure['partial_path']);require(sha(body)==(failure.get('partial_sha256')or failure['sha256']),'Diagnostic body changed')
            if 'bytes_received'in failure:require(body.stat().st_size==failure['bytes_received'],'Diagnostic byte count changed')



# Active catalogs are checked separately from the preserved publication.
from pathlib import Path as _RemovalPath
import sys as _removal_sys
_removal_tools = next(p / 'tools' for p in _RemovalPath(__file__).resolve().parents if (p / 'tools/fixture_layout.py').is_file())
_removal_sys.path.insert(0, str(_removal_tools))

def check(output=None):
    root=e.ROOT;output=output or root
    require(root.name=='Evan-Amos-Uploads'and root.parent.name=='Curatorial','Wrong leaf placement')
    require(not(root/'prompt.json').exists()and not(root/'provenance/intake/prompt.json').exists()and not[p for p in root.glob('*/manifest.json')if p.parent.name not in('provenance','previews')],'Unexpected prompt or child fixture')
    population.check();diagnostic_check();chosen=e.selection();reviews=read(root/'provenance/rights-review.json');metadata=e.evidence()
    require(reviews==review.records(),'Rights/identity review does not replay')
    # Validate every size-specific cache, including unneeded historical attempts.
    for edge in {int(p.stem.split('-')[1])for p in(root/'provenance/api').glob('metadata-*-ranks-*.json')if not p.name.endswith('.receipt.json')}:e.evidence(edge)
    imported=imports();ids={r['candidate_id']for r in imported}
    require(ids<=set(chosen['included']),'Excluded or unknown acquired identity')
    require({p.stem for p in(root/'provenance/source-receipts').glob('*.json')}==ids,'Receipt coverage differs')
    require(read(output/'provenance/import-map.json')==imported,'Import map differs')
    require(read(output/'provenance/acquisition.json')==summary(),'Acquisition state differs')
    require(read(output/'provenance/related-file-evidence.json')==relationships.evidence(),'Related-file evidence differs')
    historical=read(output/'provenance/identity-audit.json');require(historical['inventories'],'Recorded identity audit missing')  # frozen evidence, not recomputed
    rows,sources=records(imported);manifest=read(output/'manifest.json')
    require(manifest['schema_version']==1 and manifest['kind']=='curatorial_heap'and manifest['fixture_id']=='hazy-evan-amos-uploads-v1','Manifest identity/kind differs')
    require(manifest['images']==rows,'Manifest inputs differ')
    require(csv_read(output/'manifest.csv')==[{k:str(v)for k,v in r.items()}for r in rows],'Image CSV differs')
    require(csv_read(output/'sources.csv')==[{k:str(v)for k,v in r.items()}for r in sources],'Source CSV differs')
    require((output/'SOURCES.md').read_text()==credits(imported),'Readable credits differ')
    source_paths={r['source_path']for r in imported};input_paths={r['final_file']for r in imported}
    require({str(p.relative_to(root))for p in(root/'sources').rglob('*')if p.is_file()}==source_paths,'Source file coverage differs')
    require({str(p.relative_to(output))for p in(output/'images').rglob('*')if p.is_file()}==input_paths,'Input file coverage differs')
    sums={}
    for line in(output/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split('  ',1);require(name not in sums,'Repeated checksum path');sums[name]=digest
    require(set(sums)==source_paths|input_paths,'Checksum coverage differs')
    for r in imported:
        cid=r['candidate_id'];require(reviews[cid]['status']=='ready','Blocked identity acquired')
        source=safe(root,r['source_path']);image=safe(output,r['final_file'])
        require(source.read_bytes()==image.read_bytes(),'Source/input bytes differ')
        require(sha(source)==r['sha256']==sums[r['source_path']]==sums[r['final_file']],'Byte hash differs')
        require(source.stat().st_size==r['bytes'],'Byte count differs')
        require(all(r[k]==v for k,v in e.dimensions(source,r['requested_edge']).items()),'Decoded attributes differ')
        require(r['source_independence_confirmed']is None,'Unsupported independence claim')
        response=r['response'];require(response in events(),'Media transfer missing from log')
        require(response['status']==200 and response['response_complete']and response['url']==r['url'],'Incomplete source transfer')
        require(response['sha256']==r['sha256']and response['bytes_received']==r['bytes'],'Transfer receipt differs')
        require(sha(root/r['metadata_path'])==r['metadata_sha256'],'Rendition metadata changed')
        actual=e.evidence(r['requested_edge'])[cid];page=actual['page'];info=page['imageinfo'][0];prior=metadata[cid]['page']['imageinfo'][0]
        require(actual['metadata_path']==r['metadata_path'],'Wrong rendition metadata')
        require(page['title']==r['canonical_title']and page['pageid']==r['pageid']==r['category_pageid'],'Category/resolved page identity differs')
        require(info['sha1']==prior['sha1']==r['original_sha1']and info['mime']==r['original_mime'],'Original identity differs')
        require(info['extmetadata']==prior['extmetadata'],'Acquired rights evidence changed')
        require(r['url']in(info.get('thumburl'),info['url']),'Rendition URL not API-returned')
        original=r['rendition']=='api_reported_unscaled_original'
        require((r['api_reported_width'],r['api_reported_height'])==((info['width'],info['height'])if original else(info['thumbwidth'],info['thumbheight'])),'API dimensions differ')
        if original:
            require(info['mime']!='image/svg+xml'and max(info['width'],info['height'])<=r['requested_edge'],'Unbounded original')
            require(hashlib.sha1(source.read_bytes()).hexdigest()==r['original_sha1'],'Unscaled original SHA-1 differs')
        if info['mime']=='image/svg+xml':require(not original and r['format']=='PNG','SVG not API-served PNG')
    for name,subset in [('batch-1',rows),('smoke',rows[:5]),('medium',rows[:20])]:require((output/f'batches/{name}.txt').read_text().splitlines()==[r['file']for r in subset],'Batch differs')
    require({p.name for p in(output/'batches').iterdir()}=={'batch-1.txt','smoke.txt','medium.txt'},'Unexpected batch files')
    pairs=read(output/'selections.json');require(pairs['pairs']==[]and pairs['known_shift_families']==[]and not csv_read(output/'probes.csv'),'Unexpected expected pairs')
    contacts=read(output/'provenance/contact-sheets.json');require([cid for r in contacts for cid in r['candidate_ids']]==[r['candidate_id']for r in imported],'Contact coverage differs')
    for r in contacts:
        require(sha(safe(output,r['path']))==r['sha256'],'Contact sheet changed')
        with Image.open(output/r['path'])as im:im.load();require(im.size==(r['width'],r['height']),'Contact dimensions differ')
    result=summary();require(result['status']!='complete'or result['acquired']==result['included']and not result['pending'],'False completeness')
    return dict(validation='passed',kind='curatorial_heap',expected_pairs=0,**result)


def build():
    root=e.ROOT;require(not(root/'manifest.json').exists(),'Publication exists; preserve old output before an explicit repair')
    stage=Path(tempfile.mkdtemp(prefix='integration-stage-',dir=root/'previews'));imported=imports();rows,sources=records(imported)
    for name in ('images','batches','provenance'):(stage/name).mkdir()
    for r in imported:
        require(sha(root/r['source_path'])==r['sha256'],'Source changed');shutil.copyfile(root/r['source_path'],stage/r['final_file'])
    dump(stage/'manifest.json',dict(schema_version=1,fixture_id='hazy-evan-amos-uploads-v1',kind='curatorial_heap',description='Every frozen direct File member of Media uploaded by Evan Amos except three exact user exclusions; no sampling, deduplication or expected matches.',images=rows))
    csv_write(stage/'manifest.csv',rows,IMAGE_FIELDS);csv_write(stage/'sources.csv',sources,SOURCE_FIELDS);csv_write(stage/'probes.csv',[],PROBE_FIELDS)
    dump(stage/'selections.json',dict(description='No matching ground truth, expected pairs, similarity labels or known-shift families.',pairs=[],known_shift_families=[]))
    dump(stage/'provenance/import-map.json',imported);dump(stage/'provenance/acquisition.json',summary());dump(stage/'provenance/identity-audit.json',audit.audit());dump(stage/'provenance/related-file-evidence.json',relationships.evidence())
    for name,subset in [('batch-1',rows),('smoke',rows[:5]),('medium',rows[:20])]:(stage/f'batches/{name}.txt').write_text(''.join(r['file']+'\n'for r in subset))
    (stage/'SHA256SUMS.txt').write_text(''.join(digest+'  '+name+'\n'for name,digest in sorted((name,r['sha256'])for r in imported for name in(r['source_path'],r['final_file']))))
    (stage/'SOURCES.md').write_text(credits(imported));sheets(stage,imported);result=check(stage);dump(stage/'provenance/validation.json',result)
    generated=[p for p in stage.rglob('*')if p.is_file()]
    require(not any((root/p.relative_to(stage)).exists()for p in generated),'Publication destination already exists')
    for p in generated:
        dest=root/p.relative_to(stage);dest.parent.mkdir(parents=True,exist_ok=True);p.replace(dest)
    shutil.rmtree(stage);print(json.dumps(check(),indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','check','list']);a=p.parse_args()
    lock=e.ROOT/'previews/intake.lock';lock.parent.mkdir(exist_ok=True)
    with lock.open('a')as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.command=='build':build()
        elif a.command=='check':print(json.dumps(check(),indent=2))
        else:print('Evan-Amos-Uploads',read(e.ROOT/'manifest.json')['kind'])


if __name__=='__main__':main()
