#!/usr/bin/env python3
"""Conservative Commons acquisition for hazy prompt_heap evidence.

Default: acquire exactly ONE small preview, serial requests, no concurrency,
no retries; stop on any HTTP or transport error and preserve diagnostics.
Use actual API-returned thumburl, not guessed URL patterns. Preserve image bytes.
"""
import argparse, csv, fcntl, hashlib, html, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    raise SystemExit("Pillow required: python3 -m pip install Pillow")

ROOT=Path(__file__).resolve().parents[1]
API="https://commons.wikimedia.org/w/api.php"
IMAGE_EXT={"JPEG":"jpg","PNG":"png","WEBP":"webp","GIF":"gif","TIFF":"tif","BMP":"bmp"}
RELEVANT_HEADERS=("content-type","content-length","retry-after","x-request-id","x-cache","server","etag","last-modified")
MAX_BYTES=12*1024*1024

def local(name):
    p=ROOT/name
    if Path(name).is_absolute() or '..' in Path(name).parts or ROOT.resolve() not in p.resolve().parents:
        raise ValueError(f'Path outside fixture: {name}')
    if any(q.is_symlink() for q in [p,*p.parents] if q!=ROOT.parent):
        raise ValueError(f'Symlink not allowed: {name}')
    return p


def same_media_url(a,b):
    a=urlparse(a or '');b=urlparse(b or '')
    return (a.scheme,a.hostname,a.path)==(b.scheme,b.hostname,b.path)

def iso():return datetime.now(timezone.utc).isoformat()

def sha256(b):return hashlib.sha256(b).hexdigest()

def jsonlines(path):return [json.loads(l) for l in path.read_text(encoding='utf8').splitlines() if l.strip()]

def atomic_write(path, data:bytes):
    local(str(path.relative_to(ROOT)))
    local(str(path.with_name(path.name+'.tmp').relative_to(ROOT)))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_bytes(data);tmp.replace(path)

def save_records(records):
    json_path=ROOT/'candidates.jsonl'
    atomic_write(json_path,(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records)).encode('utf-8'))
    # MediaWiki enriches rows incrementally. Some fields first appear on a later
    # record; derive CSV columns from the union rather than the first row only.
    keys=list(dict.fromkeys(key for record in records for key in record))
    import io
    s=io.StringIO(newline='')
    w=csv.DictWriter(s,fieldnames=keys);w.writeheader();w.writerows(records)
    atomic_write(ROOT/'candidates.csv',s.getvalue().encode('utf-8'))

def clean_text(s):
    return html.unescape(re.sub(r'<[^>]*>','',s or '')).strip() or None

def log(row):
    path=ROOT/'provenance'/'http_log.jsonl'
    with path.open('a',encoding='utf8') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')

class TransportError(RuntimeError):pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Client:
    def __init__(self, ua, pace, timeout):
        if local('provenance/last_transport_error.json').exists():
            raise TransportError('Diagnose the persisted last_transport_error.json before resuming.')
        self.ua=ua;self.pace=pace;self.timeout=timeout;self.last=0.0
        self.opener=build_opener(NoRedirect)
    def request(self,url,kind, candidate_id):
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname not in ('commons.wikimedia.org','upload.wikimedia.org','thumb.wikimedia.org'):
            raise ValueError('Unexpected Wikimedia URL')
        delay=self.pace-(time.monotonic()-self.last)
        if delay>0:time.sleep(delay)
        self.last=time.monotonic()
        req=Request(url,headers={'User-Agent':self.ua,'Accept':'application/json' if kind=='api' else 'image/*'})
        status=None;hdr={}
        try:
            with self.opener.open(req,timeout=self.timeout) as r:
                status=r.status;hdr={k.lower():v for k,v in r.headers.items() if k.lower() in RELEVANT_HEADERS}
                b=r.read(MAX_BYTES+1)
                if len(b)>MAX_BYTES:raise ValueError('Response exceeds 12 MiB; stopped without retry')
                content_type=r.headers.get_content_type()
                if kind=='api':
                    if content_type!='application/json':raise ValueError(f'Unexpected API content type: {content_type}')
                    data=json.loads(b)
                    if 'error' in data or 'warnings' in data:raise ValueError('API error/warning: '+json.dumps(data))
                elif not content_type.startswith('image/'):
                    raise ValueError(f'Unexpected media content type: {content_type}')
                log({'utc':iso(),'candidate_id':candidate_id,'kind':kind,'url':url,'status':r.status,'headers':hdr,'bytes':len(b),'sha256':sha256(b),'user_agent':self.ua})
                return b
        except HTTPError as e:
            hdr={k.lower():v for k,v in e.headers.items() if k.lower() in RELEVANT_HEADERS}
            try: excerpt=e.read(2048).decode('utf8','replace')
            except Exception:excerpt=None
            row={'utc':iso(),'candidate_id':candidate_id,'kind':kind,'url':url,'status':e.code,'headers':hdr,'body_excerpt':excerpt}
            log(row);atomic_write(ROOT/'provenance'/'last_transport_error.json',json.dumps(row,ensure_ascii=False,indent=2).encode())
            raise TransportError(f"HTTP {e.code} while requesting {kind} for {candidate_id}; stopped without retry") from e
        except (URLError, OSError, ValueError) as e:
            row={'utc':iso(),'candidate_id':candidate_id,'kind':kind,'url':url,'status':status,'headers':hdr,'error_type':type(e).__name__,'error':str(e)}
            log(row);atomic_write(ROOT/'provenance'/'last_transport_error.json',json.dumps(row,ensure_ascii=False,indent=2).encode())
            raise TransportError(f"{type(e).__name__} while requesting {kind} for {candidate_id}; stopped without retry") from e
        finally:
            self.last=time.monotonic()


def get_metadata(client, row, stage, maxdim):
    path=local(f"provenance/api/{row['candidate_id']}-{stage}.json")
    if path.exists():
        data=json.loads(path.read_text(encoding='utf8'))
    else:
        q={'action':'query','format':'json','formatversion':2,'prop':'imageinfo','maxlag':5,'redirects':1,
           'titles':row['commons_title'],
           'iiprop':'url|size|mime|sha1|extmetadata|timestamp|user',
           'iiurlwidth':maxdim,'iiurlheight':maxdim}
        url=API+'?'+urlencode(q)
        raw=client.request(url,'api',row['candidate_id'])
        data=json.loads(raw)
        atomic_write(path,json.dumps(data,ensure_ascii=False,indent=2).encode('utf8'))
    row['metadata_path']=str(path.relative_to(ROOT))
    row[stage+'_metadata_path']=str(path.relative_to(ROOT))
    pages=data.get('query',{}).get('pages',[])
    if not pages or not pages[0].get('imageinfo'):
        row['review_notes']='No imageinfo found in API response; visually unresolved.'
        return None
    page=pages[0]
    row['commons_pageid']=page['pageid']
    if page.get('title') != row['commons_title']:
        row['review_notes']='Commons returned a canonicalized title; compare provenance before accepting.'
        row['commons_api_title']=page.get('title')
    ii=page['imageinfo'][0]
    for key,source in [('original_width','width'),('original_height','height'),('original_mime','mime'),('original_sha1','sha1')]:
        if ii.get(source) is not None:row[key]=ii[source]
    meta=ii.get('extmetadata',{})
    for key,field in [('license','LicenseShortName'),('license_url','LicenseUrl'),('creator','Artist'),('credit','Credit')]:
        val=meta.get(field,{}).get('value')
        if val is not None:
            value=clean_text(val)
            if key=='creator' and value in ('Unknown author','Unknown authorUnknown author'):value=None
            row[key]=value
    row['source_license_checked']=bool(meta.get('LicenseShortName',{}).get('value'))
    row['original_url']=ii.get('url')
    row['commons_file_timestamp']=ii.get('timestamp')
    return ii


def make_contact_sheets(records):
    paths=[]
    for r in records:
        p=r.get('preview_path')
        if p and local(p).is_file():paths.append((r['candidate_id'],local(p)))
    if not paths:return 0
    cols=4;rows=5;cw=320;ch=285
    for start in range(0,len(paths),cols*rows):
        subset=paths[start:start+cols*rows]
        canvas=Image.new('RGB',(cols*cw,rows*ch),(248,248,248))
        d=ImageDraw.Draw(canvas)
        for i,(id,path) in enumerate(subset):
            x=(i%cols)*cw;y=(i//cols)*ch
            with Image.open(path) as src:
                src=ImageOps.exif_transpose(src).convert('RGB');src.thumbnail((cw-16,ch-39),Image.Resampling.LANCZOS)
                canvas.paste(src,(x+(cw-src.width)//2,y+(ch-39-src.height)//2))
            d.text((x+8,y+ch-30),id,fill=(30,30,30))
        outfile=ROOT/'previews'/f'contact-{start//(cols*rows)+1:02d}.jpg'
        canvas.save(outfile,'JPEG',quality=92)
    return len(paths)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',choices=['preview','image','contact'],default='preview')
    ap.add_argument('--limit',type=int,default=1,help='max NEW images this run; 0 means all; default=1')
    ap.add_argument('--pace',type=float,default=3.0,help='minimum seconds after ANY network request')
    ap.add_argument('--timeout',type=float,default=40)
    ap.add_argument('--user-agent',default=os.environ.get('HAZY_USER_AGENT'))
    args=ap.parse_args()
    if args.stage!='contact' and not args.user_agent:
        ap.error('Provide HAZY_USER_AGENT identifying your client and a real contact method (per Wikimedia policy).')
    if args.limit<0 or args.pace<1:ap.error('limit must be >=0, pace >=1 second')
    records=jsonlines(ROOT/'candidates.jsonl')
    if args.stage=='contact':
        n=make_contact_sheets(records);print('Previews on contact sheets:',n);return
    stage=args.stage
    count=0;client=Client(args.user_agent,args.pace,args.timeout)
    for row in records:
        key='preview_path' if stage=='preview' else 'acquired_path'
        if row.get(key) and local(row[key]).is_file():
            hash_key='preview_sha256' if stage=='preview' else 'acquired_sha256'
            if sha256(local(row[key]).read_bytes())!=row.get(hash_key):raise ValueError('Cached file hash changed; not refetching')
            continue
        if stage=='image' and row.get('screening_status')!='accept':continue
        if args.limit and count>=args.limit:break
        try:
            maxdim=320 if stage=='preview' else 1600
            ii=get_metadata(client,row,stage,maxdim)
            if ii is None:
                save_records(records);continue
            if stage=='image' and not (row.get('source_license_checked') and row.get('license_review') and row.get('provenance_review')):
                raise ValueError('Image acquisition requires file-specific license and provenance reviews')
            if stage=='image' and row.get('preview_original_sha1')!=row.get('original_sha1'):
                raise ValueError('Upstream file changed since preview review; stopped')
            url=ii.get('thumburl')
            if not url:
                # Some tiny source files do not have a separate thumbnail.
                if max(ii.get('width',999999),ii.get('height',999999)) <= maxdim and ii.get('size',MAX_BYTES+1)<=MAX_BYTES:
                    url=ii.get('url')
                else:
                    row['review_notes']=f'No API-returned {maxdim}px rendition; refused large original download.'
                    save_records(records)
                    continue
            if not url:
                row['review_notes']='API returned no usable image URL.'
                save_records(records);continue
            if not ii.get('thumburl') and same_media_url(url,ii.get('url')) and max(ii['width'],ii['height'])>maxdim:
                raise ValueError('API returned an oversized original; refused')
            raw=client.request(url,'preview' if stage=='preview' else 'image',row['candidate_id'])
            tmp=local(f'previews/partial/{row["candidate_id"]}-{stage}.partial')
            tmp.parent.mkdir(parents=True,exist_ok=True)
            tmp.write_bytes(raw)
            try:
                with Image.open(tmp) as img:
                    img.verify()
                with Image.open(tmp) as img:
                    img.load();w,h=img.size;fmt=img.format
                    if getattr(img,'n_frames',1)!=1:raise ValueError('Multiple image frames are unsupported')
                    if max(w,h)>maxdim*1.5:raise ValueError('Actual rendition exceeds nominal edge by more than 50%')
                ext=IMAGE_EXT.get(fmt)
                if not ext:raise ValueError(f'unsupported decoded image format {fmt}')
            except Exception:
                tmp.unlink(missing_ok=True)
                raise
            folder='previews/tiles' if stage=='preview' else 'sources'
            path=local(f'{folder}/{row["candidate_id"]}.{ext}')
            if path.exists():raise ValueError(f'Unreceipted file exists: {path.name}')
            path.parent.mkdir(parents=True,exist_ok=True)
            tmp.replace(path)
            rel=str(path.relative_to(ROOT))
            if stage=='preview':
                row.update(preview_url=url,preview_width=w,preview_height=h,preview_sha256=sha256(raw),preview_path=rel)
                row['preview_original_sha1']=row.get('original_sha1')
                row['review_notes']='Preview acquired; awaits visual accept/reject/defer decision.'
            else:
                row.update(acquired_url=url,acquired_width=w,acquired_height=h,acquired_sha256=sha256(raw),acquired_path=rel,acquired_format=fmt,image_downloaded=True,acquisition_kind='api_unscaled_original' if same_media_url(url,ii.get('url')) else 'commons_rendition',requested_max_edge=maxdim)
            count+=1
            save_records(records)
            print(f'{row["candidate_id"]}: acquired {stage} {w}x{h}, {len(raw)} bytes -> {rel}',flush=True)
        except (TransportError, ValueError, OSError) as e:
            if not local('provenance/last_transport_error.json').exists():
                atomic_write(local('provenance/last_transport_error.json'),json.dumps({'utc':iso(),'candidate_id':row['candidate_id'],'stage':stage,'error':str(e)}).encode())
            save_records(records)
            print(f'STOP: {e}',file=sys.stderr)
            make_contact_sheets(records)
            return 2
    save_records(records)
    if stage=='preview':make_contact_sheets(records)
    print(f'New {stage} acquisitions: {count}. (Existing acquisitions reused.)')
    return 0

if __name__=='__main__':
    lock=local('previews/acquisition.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as stream:
        try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another acquisition is running; no request made.')
        sys.exit(main())
