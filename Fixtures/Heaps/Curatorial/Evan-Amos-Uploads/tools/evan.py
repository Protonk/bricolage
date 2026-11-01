#!/usr/bin/env python3
"""Exhaustive category intake: one rendition per included File identity, no curation."""
import argparse
import fcntl
import hashlib
import html
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from PIL import Image
import population
from transport import Client, dump, sha, safe, utc

ROOT=population.ROOT
read=population.read
require=population.require
EXT={'JPEG':'jpg','PNG':'png','GIF':'gif','WEBP':'webp','TIFF':'tif'}
SUPPORTED_MIME={'image/jpeg','image/png','image/gif','image/webp','image/tiff','image/svg+xml'}


def clean(value):
    if value is None:return None
    value=re.sub(r'<(style|script)\b[^>]*>.*?</\1>','',value,flags=re.I|re.S)
    return html.unescape(re.sub('<[^>]*>','',value)).strip()


def norm(title):return title.replace('_',' ').removeprefix('File:')
def candidates():return {r['candidate_id']:r for r in read(ROOT/'provenance/intake/inventory.json')['candidates']}
def order():return read(ROOT/'provenance/intake/ordering.json')['candidate_ids']
def selection():return population.selection(read(ROOT/'provenance/intake/inventory.json'))


def current_metadata(data):
    require(not any(k in data for k in ('error','warnings')), 'Failed metadata reply')
    pages=data.get('query',{}).get('pages',[])
    require(pages, 'Missing metadata pages')
    if 'continue' in data:
        c=data['continue']
        require(len(pages)==1 and set(c)=={'iistart','continue'} and c['continue']=='||revisions'
                and len(pages[0].get('imageinfo',[]))==1 and len(pages[0].get('revisions',[]))==1
                and c['iistart']<pages[0]['imageinfo'][0]['timestamp'],'Unresolved metadata continuation')


def metadata(start,end,edge):
    require(1<=start<=end<=len(order()),'Invalid rank interval')
    client=Client(ROOT);by=candidates()
    for first in range(start,end+1,10):
        last=min(first+9,end);key=f'metadata-{edge}-ranks-{first:04d}-{last:04d}'
        data=client.api(key,prop='imageinfo|revisions',titles='|'.join(by[c]['frozen_title'] for c in order()[first-1:last]),redirects=1,
                        iiprop='url|size|mime|sha1|extmetadata|timestamp|user',iiurlwidth=edge,iiurlheight=edge,
                        rvprop='ids|timestamp|content',rvslots='main')
        try:current_metadata(data)
        except ValueError as error:client.stop(dict(utc=utc(),kind='metadata-validation',error=str(error),metadata_path=f'provenance/api/{key}.json'))
        print(key,'cached',flush=True)


def evidence(edge=1600):
    out={};by=candidates()
    for path in sorted((ROOT/'provenance/api').glob(f'metadata-{edge}-ranks-*.json')):
        if path.name.endswith('.receipt.json'):continue
        data,_,params=population.api_receipt(path);current_metadata(data)
        start,end=map(int,path.stem.split('-')[-2:]);ids=order()[start-1:end]
        require(params['titles']==['|'.join(by[c]['frozen_title']for c in ids)] and params['redirects']==['1'],'Metadata titles differ')
        require(params['iiurlwidth']==params['iiurlheight']==[str(edge)],'Metadata size differs')
        pages={norm(p['title']):p for p in data['query']['pages']};redirects={norm(r['from']):norm(r['to'])for r in data['query'].get('redirects',[])}
        for cid in ids:
            title=norm(by[cid]['frozen_title']);original=title;seen=set()
            while title in redirects:
                require(title not in seen,'Redirect cycle');seen.add(title);title=redirects[title]
            require(title in pages and cid not in out,'Missing page or overlapping metadata ranges')
            out[cid]=dict(candidate_id=cid,page=pages[title],metadata_path=str(path.relative_to(ROOT)),metadata_sha256=sha(path),redirected=title!=original,requested_edge=edge)
    return out


def dimensions(path,edge):
    with Image.open(path)as im:
        require(getattr(im,'n_frames',1)==1 and im.format in EXT,'Unsupported decoded format or animation')
        im.load();require(max(im.size)<=edge*1.5,'Decoded rendition exceeds nominal edge by over 50%')
        return dict(width=im.width,height=im.height,format=im.format,mode=im.mode,has_alpha=('A'in im.getbands()or'transparency'in im.info),exif_orientation=im.getexif().get(274,1))


def media(start,end,edge,limit):
    require(limit>0,'Positive bounded acquisition limit required')
    ev=evidence(edge);base=evidence();reviews=read(ROOT/'provenance/rights-review.json');included=set(selection()['included']);by=candidates();client=Client(ROOT);count=0
    for rank,cid in enumerate(order(),1):
        if not start<=rank<=end or cid not in included:continue
        record=ROOT/f'provenance/source-receipts/{cid}.json'
        if record.exists():
            old=read(record)
            if sha(safe(ROOT,old['path']))!=old['sha256']:client.stop(dict(utc=utc(),kind='cache-validation',candidate_id=cid,error='Changed cached source',path=old['path']))
            continue
        if cid not in reviews or reviews[cid]['status']!='ready':
            print(rank,cid,'pending rights/identity',flush=True);continue
        require(cid in ev,'Rendition metadata missing');e=ev[cid];page=e['page'];ii=page['imageinfo'][0];prior=base[cid]['page']['imageinfo'][0]
        if not (ii['sha1']==prior['sha1'] and page['pageid']==base[cid]['page']['pageid'] and ii['extmetadata']==prior['extmetadata']):
            client.stop(dict(utc=utc(),kind='identity-validation',candidate_id=cid,error='Source identity or rights changed; reconcile explicitly',
                             metadata_path=e['metadata_path'],reviewed_metadata_path=base[cid]['metadata_path']))
        url=ii.get('thumburl');original=ii['url'];reason=None
        if ii['mime'] not in SUPPORTED_MIME:reason='Unsupported original; no arbitrary page/frame extraction.'
        if not url and ii['mime']!='image/svg+xml' and max(ii['width'],ii['height'])<=edge:url=original
        if not url:reason=reason or 'No supported API rendition returned.'
        unscaled=url is not None and unquote(urlsplit(url).path)==unquote(urlsplit(original).path)
        if unscaled and (ii['mime']=='image/svg+xml' or max(ii['width'],ii['height'])>edge):reason='API offered an SVG or oversized unscaled original; explicit smaller API rendition required.'
        if reason:
            dump(ROOT/f'provenance/unavailable/{cid}-{edge}.json',dict(candidate_id=cid,rank=rank,requested_edge=edge,metadata_path=e['metadata_path'],reason=reason,media_request_made=False));print(rank,cid,'unavailable',edge,flush=True);continue
        part,event=client.fetch(url,'source',cid,f'previews/partials/{cid}-{edge}.part')
        try:
            measured=dimensions(part,edge)
            require(ii['mime']!='image/svg+xml' or (not unscaled and measured['format']=='PNG'),'SVG must use API PNG')
            if unscaled:require(hashlib.sha1(part.read_bytes()).hexdigest()==ii['sha1'],'Unscaled original SHA-1 differs from API identity')
        except Exception as error:client.stop(dict(utc=utc(),kind='decode',candidate_id=cid,error=str(error),response_complete=True,partial_path=str(part.relative_to(ROOT)),sha256=sha(part),metadata_path=e['metadata_path']))
        dest=ROOT/'sources'/(cid+'.'+EXT[measured['format']]);dest.parent.mkdir(exist_ok=True);require(not dest.exists(),'Unreceipted source exists');part.replace(dest)
        dump(record,dict(candidate_id=cid,rank=rank,path=str(dest.relative_to(ROOT)),sha256=sha(dest),bytes=dest.stat().st_size,url=url,requested_edge=edge,
                         rendition='api_reported_unscaled_original'if unscaled else'api_returned_rendition',original_mime=ii['mime'],original_sha1=ii['sha1'],
                         pageid=page['pageid'],canonical_title=page['title'],metadata_path=e['metadata_path'],metadata_sha256=e['metadata_sha256'],
                         api_reported_width=ii['width']if unscaled else ii.get('thumbwidth'),api_reported_height=ii['height']if unscaled else ii.get('thumbheight'),
                         returned_mime=event['headers'].get('content-type'),response=event,**measured))
        count+=1;print(rank,cid,measured['format'],measured['width'],measured['height'],flush=True)
        if count>=limit:break


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['metadata','media','acknowledge']);p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int);p.add_argument('--edge',type=int,choices=[640,1280,1600],default=1600);p.add_argument('--limit',type=int,default=1);p.add_argument('--diagnosis');a=p.parse_args()
    lock=ROOT/'previews/intake.lock';lock.parent.mkdir(exist_ok=True)
    with lock.open('a')as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.command=='acknowledge':Client(ROOT).acknowledge(a.diagnosis)
        elif a.command=='metadata':metadata(a.start,a.end or len(order()),a.edge)
        else:media(a.start,a.end or len(order()),a.edge,a.limit)


if __name__=='__main__':main()
