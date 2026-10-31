#!/usr/bin/env python3
"""Conservative Commons acquisition; no visual decisions and NO automatic retries.

Start with one 320px preview. Explicitly review that preview before acquiring
accepted source renditions. Source bytes go in sources/; previews and media
partials go in previews/. Unknown metadata is null, not guessed.

A network exception *after HTTP 200 headers* retains the status 200 and
records a failed/incomplete BODY read, with whatever partial bytes arrived.
"""
import argparse, fcntl, hashlib, html, json, os, re, socket, sys, time
from datetime import datetime,timezone
from email.message import Message
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode,urlparse
from urllib.request import Request,build_opener,HTTPRedirectHandler
from PIL import Image,ImageDraw,ImageOps,ImageFile
from common import ROOT,load_records,save_records,atomic_write,append_jsonl,local

API='https://commons.wikimedia.org/w/api.php'
EXT={'JPEG':'jpg','PNG':'png','WEBP':'webp','GIF':'gif','TIFF':'tif'}
RELEVANT_HEADERS={'content-type','content-length','retry-after','x-request-id','x-cache','server','etag','last-modified','cache-control','date'}
MAX_BYTES={'api':4_000_000,'preview':12_000_000,'source':12_000_000}

def iso():return datetime.now(timezone.utc).isoformat()
def digest(b):return hashlib.sha256(b).hexdigest()
def html_plain(val):
    if val is None:return None
    s=html.unescape(re.sub('<[^>]*>','',str(val))).strip()
    return s or None

class StopAcquisition(Exception):pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def same_media_url(a,b):
    a=urlparse(a or '');b=urlparse(b or '')
    return (a.scheme,a.hostname,a.path)==(b.scheme,b.hostname,b.path)

class Client:
    def __init__(self,agent,pace,timeout):
        self.agent=agent;self.pace=pace;self.timeout=timeout;self.last=None
        self.opener=build_opener(NoRedirect)
    def fetch(self,url,kind,candidate_id,tmp_path):
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname not in ('commons.wikimedia.org','upload.wikimedia.org','thumb.wikimedia.org'):raise StopAcquisition('Unexpected Wikimedia URL')
        local(str(Path(tmp_path).relative_to(ROOT)))
        if self.last is not None:
            delta=self.pace-(time.monotonic()-self.last)
            if delta>0:time.sleep(delta)
        self.last=time.monotonic()
        req=Request(url,headers={'User-Agent':self.agent,'Accept':'application/json' if kind=='api' else 'image/*'})
        headers={};status=None;received=0;hash_obj=hashlib.sha256()
        tmp_path=Path(tmp_path);tmp_path.parent.mkdir(parents=True,exist_ok=True)
        event={'utc':iso(),'candidate_id':candidate_id,'kind':kind,'url':url,'status':None,
               'response_complete':False,'bytes_received':0,'headers':None,'partial_path':None,'user_agent':self.agent}
        try:
            with self.opener.open(req,timeout=self.timeout) as response:
                status=response.status
                headers={k.lower():v for k,v in response.headers.items() if k.lower() in RELEVANT_HEADERS}
                event['status']=status;event['headers']=headers
                content_type=response.headers.get_content_type()
                if (kind=='api' and content_type!='application/json') or (kind!='api' and not content_type.startswith('image/')):raise StopAcquisition(f'Unexpected content type: {content_type}')
                try:
                    declared=int(headers.get('content-length','0'))
                except ValueError:declared=0
                if declared>MAX_BYTES[kind]:
                    raise StopAcquisition(f'Content-Length {declared} exceeds conservative {kind} limit')
                with tmp_path.open('wb') as fp:
                    while True:
                        try:
                            chunk=response.read(64*1024)
                        except IncompleteRead as e:
                            # http.client may expose valid partial bytes.
                            part=getattr(e,'partial',None)
                            if part:fp.write(part);received+=len(part);hash_obj.update(part)
                            raise
                        if not chunk:break
                        fp.write(chunk);received+=len(chunk);hash_obj.update(chunk)
                        if received>MAX_BYTES[kind]:
                            raise StopAcquisition(f'{kind} body exceeded conservative {MAX_BYTES[kind]} byte limit')
                if declared and declared!=received:
                    raise StopAcquisition(f'incomplete HTTP body: declared {declared}, received {received}')
                event.update(response_complete=True,bytes_received=received,sha256=hash_obj.hexdigest())
                append_jsonl(ROOT/'provenance/http_log.jsonl',event)
                self.last=time.monotonic()
                return tmp_path,headers
        except HTTPError as e:
            event['status']=e.code
            event['headers']={k.lower():v for k,v in e.headers.items() if k.lower() in RELEVANT_HEADERS}
            try:event['body_excerpt']=e.read(2048).decode('utf-8','replace')
            except Exception as read_e:event['body_error']=str(read_e)
            error=f'HTTP {e.code}'
        except (socket.timeout,TimeoutError,IncompleteRead,URLError,OSError,StopAcquisition) as e:
            # Crucial: status can be 200 if headers succeeded but BODY timed out.
            error=f'{type(e).__name__}: {e}'
        except Exception as e:
            error=f'Unexpected {type(e).__name__}: {e}'
        self.last=time.monotonic()
        if tmp_path.exists():
            received=tmp_path.stat().st_size
            event['partial_path']=str(tmp_path.relative_to(ROOT))
        event.update(response_complete=False,bytes_received=received,error=error)
        append_jsonl(ROOT/'provenance/http_log.jsonl',event)
        atomic_write(ROOT/'provenance/last_transport_error.json',json.dumps(event,ensure_ascii=False,indent=2).encode('utf-8'))
        raise StopAcquisition(f'{candidate_id} {kind} stopped: {error}; no retry')

def metadata(client,row,stage,maxdim):
    cid=row['candidate_id']
    size_suffix=f'-{maxdim}' if maxdim != (320 if stage=='preview' else 1600) else ''
    path=ROOT/'provenance/api'/f'{cid}-{stage}{size_suffix}.json'
    if path.exists():
        raw=path.read_bytes()
    else:
        q={'action':'query','format':'json','formatversion':2,'prop':'imageinfo',
           'titles':row['commons_title'],'maxlag':5,'redirects':1,
           'iiprop':'url|size|mime|sha1|extmetadata|timestamp|user',
           'iiurlwidth':maxdim,'iiurlheight':maxdim}
        endpoint=API+'?'+urlencode(q)
        part=ROOT/'provenance/partials'/f'{cid}-{stage}{size_suffix}-api.part'
        downloaded,_=client.fetch(endpoint,'api',cid,part)
        raw=downloaded.read_bytes()
        # Preserve the *actual response bytes*, not a constructed or prettified substitute.
        atomic_write(path,raw)
        downloaded.unlink(missing_ok=True)
    row['metadata_path']=str(path.relative_to(ROOT))
    row[f'api_{stage}_metadata_path']=str(path.relative_to(ROOT))
    row[stage+'_requested_max_edge']=maxdim
    try:
        data=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as e:
        raise StopAcquisition(f'{cid}: unusable JSON metadata: {e}') from e
    if 'error' in data or 'warnings' in data:raise StopAcquisition('API error/warning: '+json.dumps(data))
    pages=data.get('query',{}).get('pages',[])
    if len(pages)!=1 or not pages[0].get('imageinfo'):
        row['review_notes']='API did not return imageinfo for this title; media not acquired.'
        return None
    page=pages[0]
    row['commons_pageid']=page['pageid']
    if page.get('title')!=row['commons_title']:
        row['commons_api_title']=page.get('title')
        row['source_independence_notes']=((row.get('source_independence_notes') or '')+' API returned a canonicalized File title; check redirects.').strip()
    ii=page['imageinfo'][0]
    for target,src in [('original_width','width'),('original_height','height'),('original_mime','mime'),('original_sha1','sha1'),
                       ('original_url','url'),('commons_file_timestamp','timestamp')]:
        if src in ii:row[target]=ii[src]
    meta=ii.get('extmetadata',{})
    for target,src in [('license','LicenseShortName'),('license_url','LicenseUrl'),('creator','Artist'),('credit','Credit')]:
        original=meta.get(src,{}).get('value')
        if original is not None:
            value=html_plain(original)
            if target=='creator' and value in ('Unknown author','Unknown authorUnknown author'):value=None
            row[target]=value
    row['source_license_checked']=bool(meta.get('LicenseShortName',{}).get('value'))
    if ii.get('thumburl'):
        url=ii['thumburl']; rendition='api_reported_unscaled_original' if same_media_url(url,ii.get('url')) else 'api_returned_rendition'
        if rendition=='api_reported_unscaled_original' and max(ii['width'],ii['height'])>maxdim:
            row['review_notes']='API unscaled original exceeds requested bound; not acquired.'
            return None
    elif ii.get('url') and ii.get('width') is not None and ii.get('height') is not None and max(ii['width'],ii['height'])<=maxdim:
        url=ii['url'];rendition='api_reported_unscaled_original'
    else:
        row['review_notes']=f'No API-reported media URL at requested ~{maxdim}px; refusing oversized original.'
        return None
    row[f'{"preview" if stage=="preview" else "acquired"}_rendition_kind']=rendition
    row[f'{"preview" if stage=="preview" else "acquired"}_api_reported_width']=ii.get('thumbwidth') if rendition=='api_returned_rendition' else ii.get('width')
    row[f'{"preview" if stage=="preview" else "acquired"}_api_reported_height']=ii.get('thumbheight') if rendition=='api_returned_rendition' else ii.get('height')
    return url,rendition

def validate_media(path,maxdim):
    with Image.open(path) as im:
        fmt=im.format;w,h=im.size;frames=getattr(im,'n_frames',1)
        if frames>1:raise StopAcquisition('animated image not accepted as a single photographic input')
        if max(w,h)>maxdim*1.5:raise StopAcquisition('Decoded rendition exceeds nominal edge by more than 50%')
        im.load()  # force full decode, not merely header inspection
    ext=EXT.get(fmt)
    if ext is None:raise StopAcquisition(f'unsupported decoded format {fmt!r}')
    return w,h,fmt,ext

def make_contact_sheets(records):
    items=[r for r in records if r.get('preview_path') and (ROOT/r['preview_path']).is_file()]
    if not items:return 0
    cols=4;rows=5;cellw=320;cellh=285
    for i in range(0,len(items),cols*rows):
        sub=items[i:i+cols*rows]
        image=Image.new('RGB',(cellw*cols,cellh*rows),(246,246,246))
        draw=ImageDraw.Draw(image)
        for n,r in enumerate(sub):
            x=(n%cols)*cellw;y=(n//cols)*cellh
            try:
                with Image.open(ROOT/r['preview_path']) as im:
                    im=ImageOps.exif_transpose(im).convert('RGB')
                    im.thumbnail((cellw-14,cellh-42),Image.Resampling.LANCZOS)
                    image.paste(im,(x+(cellw-im.width)//2,y+(cellh-42-im.height)//2))
                draw.text((x+9,y+cellh-34),r['candidate_id']+' '+('['+r['screening_status']+']' if r['screening_status']!='pending_visual_review' else ''),fill=(24,24,24))
            except (OSError,ValueError) as e:
                draw.text((x+8,y+8),f"{r['candidate_id']} bad preview",fill=(127,40,40))
        out=ROOT/'previews'/f'contact-{i//(cols*rows)+1:02d}.jpg'
        image.save(out,'JPEG',quality=92)
    return len(items)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['preview','source','contact'],default='preview')
    p.add_argument('--limit',type=int,default=1,help='max NEW media files; defaults to one; 0 = all (not recommended)')
    p.add_argument('--pace',type=float,default=3.0,help='minimum seconds after any HTTP request (>=1.5)')
    p.add_argument('--timeout',type=float,default=40.0,help='socket timeout per request / read')
    p.add_argument('--user-agent',default=os.environ.get('HAZY_USER_AGENT'))
    p.add_argument('--candidate-id',help='limit this invocation to one existing candidate ID')
    p.add_argument('--preview-edge',type=int,choices=[320,480,640],default=320,help='nominal preview edge; explicit 640 avoids very small portrait thumbnail buckets')
    p.add_argument('--source-edge',type=int,choices=[1280,1600],default=1600,help='nominal source bound; 1280 permits an explicit smaller rendition request')
    p.add_argument('--acknowledge-error',action='store_true',help='manually confirm prior transport error was inspected before continuing')
    args=p.parse_args()
    if args.limit<0 or args.pace<1.5:p.error('limit must be >=0, pace >=1.5')
    if args.stage!='contact' and not args.user_agent:
        p.error('Provide HAZY_USER_AGENT with a truthful project identity and real contact method.')
    prior=ROOT/'provenance/last_transport_error.json'
    if args.stage!='contact' and prior.exists():
        if not args.acknowledge_error:
            p.error('A prior transport failure exists. Inspect provenance/last_transport_error.json; to make a new explicit attempt add --acknowledge-error.')
        # Record explicit resumption and archive the last-error latch. Keep
        # diagnostic history; successful subsequent chunks need no flag.
        old_event=json.loads(prior.read_text(encoding='utf-8'))
        append_jsonl(ROOT/'provenance/error_acknowledgements.jsonl',
            {'utc':iso(),'acknowledged_error':old_event})
        prior.unlink()
    records=load_records()
    if args.candidate_id and args.candidate_id not in {r['candidate_id'] for r in records}:p.error('Unknown candidate ID')
    if args.stage=='contact':
        print('Contact-sheet previews:',make_contact_sheets(records));return 0
    client=Client(args.user_agent,args.pace,args.timeout)
    count=0;stage=args.stage
    for row in records:
        if args.candidate_id and row['candidate_id']!=args.candidate_id:continue
        key='preview_path' if stage=='preview' else 'acquired_path'
        status_key='preview_acquisition_status' if stage=='preview' else 'source_acquisition_status'
        if stage=='source' and row.get('visually_accepted') is not True:continue
        if row.get(key) and local(row[key]).is_file():
            hash_key='preview_sha256' if stage=='preview' else 'acquired_sha256'
            if digest(local(row[key]).read_bytes())!=row.get(hash_key):raise StopAcquisition('Cached bytes changed; not refetching')
            continue
        if args.limit and count>=args.limit:break
        cid=row['candidate_id']
        try:
            maxdim=args.preview_edge if stage=='preview' else args.source_edge
            media=metadata(client,row,stage,maxdim)
            if media is None:
                row[status_key]='unavailable_metadata'
                save_records(records);continue
            url,rendition=media
            if stage=='source':
                if not (row.get('source_license_checked') and row.get('license_review') and row.get('provenance_review')):raise StopAcquisition('Source requires file-specific license and provenance review')
                if row.get('preview_original_sha1')!=row.get('original_sha1'):raise StopAcquisition('Upstream file changed after preview review')
                preview_page=json.loads(local(row['api_preview_metadata_path']).read_bytes())['query']['pages'][0]
                if preview_page['pageid']!=row['commons_pageid']:raise StopAcquisition('Commons page identity changed after preview review')
                preview_license=html_plain(preview_page['imageinfo'][0]['extmetadata']['LicenseShortName']['value'])
                if preview_license!=row['license']:raise StopAcquisition('License statement changed after preview review')
            # Only API-returned URL; do not manufacture a CDN URL.
            suffix=stage + (f'-{maxdim}' if maxdim != (320 if stage=='preview' else 1600) else '')
            temp=ROOT/'previews/partials'/f'{cid}-{suffix}.part'
            completed,headers=client.fetch(url,'preview' if stage=='preview' else 'source',cid,temp)
            try:
                width,height,fmt,ext=validate_media(completed,maxdim)
            except Exception as e:
                event={'utc':iso(),'candidate_id':cid,'kind':'decode','url':url,'status':200,
                       'response_complete':True,'bytes_received':completed.stat().st_size,
                       'partial_path':str(completed.relative_to(ROOT)),'error':f'{type(e).__name__}: {e}'}
                append_jsonl(ROOT/'provenance/http_log.jsonl',event)
                atomic_write(ROOT/'provenance/last_transport_error.json',json.dumps(event,indent=2).encode('utf-8'))
                raise StopAcquisition(f'{cid}: received image but full decoder validation failed: {e}') from e
            raw=completed.read_bytes()
            dest=ROOT/('previews/tiles' if stage=='preview' else 'sources')/f'{cid}.{ext}'
            dest.parent.mkdir(parents=True,exist_ok=True)
            local(str(dest.relative_to(ROOT)))
            if dest.exists():raise StopAcquisition('Unreceipted destination exists; refusing overwrite')
            os.replace(completed,dest)
            fields={'url':url,'width':width,'height':height,'sha256':digest(raw),
                    'path':str(dest.relative_to(ROOT)),'bytes':len(raw),'returned_mime':headers.get('content-type')}
            if stage=='preview':
                for k,v in fields.items():row['preview_'+k]=v
                row['preview_acquisition_status']='complete'
                row['preview_original_sha1']=row['original_sha1']
                row['review_notes']='Preview acquired. Visual review remains independent and pending unless separately recorded.'
            else:
                for k,v in fields.items():row[('acquired_' if k!='returned_mime' else 'acquired_')+k]=v
                row['acquired_format']=fmt
                row['source_acquisition_status']='complete'
                row['image_downloaded']=True
                if args.source_edge!=1600:row['review_notes']='Source acquired from an explicitly requested smaller API rendition after declining an unscaled original above the nominal bound; see provenance/acquisition.json.'
            count+=1;save_records(records)
            print(f'{cid}: {stage} complete {width}x{height}; actual {len(raw)} bytes; {rendition}; {dest.relative_to(ROOT)}',flush=True)
        except StopAcquisition as e:
            if not (ROOT/'provenance/last_transport_error.json').exists():
                atomic_write(ROOT/'provenance/last_transport_error.json',json.dumps(dict(utc=iso(),candidate_id=cid,stage=stage,error=str(e),metadata_path=row.get('metadata_path')),indent=2).encode())
            row[status_key]='failed_or_incomplete'
            save_records(records)
            print(f'STOP: {e}',file=sys.stderr)
            if stage=='preview':make_contact_sheets(records)
            return 2
    save_records(records)
    if stage=='preview':make_contact_sheets(records)
    print(f'New complete {stage} files: {count}; visual decisions unchanged.')
    return 0

if __name__=='__main__':
    lock=local('previews/acquisition.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as stream:
        try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another acquisition/review is running; no request made.')
        sys.exit(main())
