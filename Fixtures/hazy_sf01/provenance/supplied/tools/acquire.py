#!/usr/bin/env python3
"""Conservative Commons acquisition for hazy prompt_heap evidence.

Default: acquire exactly ONE small preview, serial requests, no concurrency,
no retries; stop on any HTTP or transport error and preserve diagnostics.
Use actual API-returned thumburl, not guessed URL patterns. Preserve image bytes.
"""
import argparse, csv, hashlib, html, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Pillow required: python3 -m pip install Pillow")

ROOT=Path(__file__).resolve().parents[1]
API="https://commons.wikimedia.org/w/api.php"
IMAGE_EXT={"JPEG":"jpg","PNG":"png","WEBP":"webp","GIF":"gif","TIFF":"tif","BMP":"bmp"}
RELEVANT_HEADERS=("content-type","content-length","retry-after","x-request-id","x-cache","server","etag","last-modified")


def iso():return datetime.now(timezone.utc).isoformat()

def sha256(b):return hashlib.sha256(b).hexdigest()

def jsonlines(path):return [json.loads(l) for l in path.read_text(encoding='utf8').splitlines() if l.strip()]

def atomic_write(path, data:bytes):
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

class Client:
    def __init__(self, ua, pace, timeout):
        self.ua=ua;self.pace=pace;self.timeout=timeout;self.last=0.0
    def request(self,url,kind, candidate_id):
        delay=self.pace-(time.monotonic()-self.last)
        if delay>0:time.sleep(delay)
        self.last=time.monotonic()
        req=Request(url,headers={'User-Agent':self.ua,'Accept':'application/json' if kind=='api' else 'image/*'})
        try:
            with urlopen(req,timeout=self.timeout) as r:
                b=r.read();hdr={k.lower():v for k,v in r.headers.items() if k.lower() in RELEVANT_HEADERS}
                log({'utc':iso(),'candidate_id':candidate_id,'kind':kind,'url':url,'status':r.status,'headers':hdr,'bytes':len(b),'sha256':sha256(b)})
                return b
        except HTTPError as e:
            hdr={k.lower():v for k,v in e.headers.items() if k.lower() in RELEVANT_HEADERS}
            try: excerpt=e.read(2048).decode('utf8','replace')
            except Exception:excerpt=None
            row={'utc':iso(),'candidate_id':candidate_id,'kind':kind,'url':url,'status':e.code,'headers':hdr,'body_excerpt':excerpt}
            log(row);atomic_write(ROOT/'provenance'/'last_transport_error.json',json.dumps(row,ensure_ascii=False,indent=2).encode())
            raise TransportError(f"HTTP {e.code} while requesting {kind} for {candidate_id}; stopped without retry") from e
        except (URLError, OSError) as e:
            row={'utc':iso(),'candidate_id':candidate_id,'kind':kind,'url':url,'status':None,'error_type':type(e).__name__,'error':str(e)}
            log(row);atomic_write(ROOT/'provenance'/'last_transport_error.json',json.dumps(row,ensure_ascii=False,indent=2).encode())
            raise TransportError(f"{type(e).__name__} while requesting {kind} for {candidate_id}; stopped without retry") from e


def get_metadata(client, row, stage, maxdim):
    path=ROOT/'provenance'/'api'/f"{row['candidate_id']}-{stage}.json"
    if path.exists():
        data=json.loads(path.read_text(encoding='utf8'))
    else:
        q={'action':'query','format':'json','formatversion':2,'prop':'imageinfo',
           'titles':row['commons_title'],
           'iiprop':'url|size|mime|sha1|extmetadata|timestamp|user',
           'iiurlwidth':maxdim,'iiurlheight':maxdim}
        url=API+'?'+urlencode(q)
        raw=client.request(url,'api',row['candidate_id'])
        data=json.loads(raw)
        atomic_write(path,json.dumps(data,ensure_ascii=False,indent=2).encode('utf8'))
    row['metadata_path']=str(path.relative_to(ROOT))
    pages=data.get('query',{}).get('pages',[])
    if not pages or not pages[0].get('imageinfo'):
        row['review_notes']='No imageinfo found in API response; visually unresolved.'
        return None
    page=pages[0]
    if page.get('title') != row['commons_title']:
        row['review_notes']='Commons returned a canonicalized title; compare provenance before accepting.'
        row['commons_api_title']=page.get('title')
    ii=page['imageinfo'][0]
    for key,source in [('original_width','width'),('original_height','height'),('original_mime','mime'),('original_sha1','sha1')]:
        if ii.get(source) is not None:row[key]=ii[source]
    meta=ii.get('extmetadata',{})
    for key,field in [('license','LicenseShortName'),('license_url','LicenseUrl'),('creator','Artist'),('credit','Credit')]:
        val=meta.get(field,{}).get('value')
        if val is not None:row[key]=clean_text(val)
    row['source_license_checked']=bool(meta.get('LicenseShortName',{}).get('value'))
    row['original_url']=ii.get('url')
    row['commons_file_timestamp']=ii.get('timestamp')
    return ii


def make_contact_sheets(records):
    paths=[]
    for r in records:
        p=r.get('preview_path')
        if p and (ROOT/p).is_file():paths.append((r['candidate_id'],ROOT/p))
    if not paths:return 0
    cols=6;rows=6;cw=188;ch=165; margin=12
    for start in range(0,len(paths),cols*rows):
        subset=paths[start:start+cols*rows]
        canvas=Image.new('RGB',(cols*cw,rows*ch),(248,248,248))
        d=ImageDraw.Draw(canvas)
        for i,(id,path) in enumerate(subset):
            x=(i%cols)*cw;y=(i//cols)*ch
            with Image.open(path) as src:
                src=src.convert('RGB');src.thumbnail((cw-16,ch-39),Image.Resampling.LANCZOS)
                canvas.paste(src,(x+(cw-src.width)//2,y+(ch-39-src.height)//2))
            d.text((x+8,y+ch-30),id,fill=(30,30,30))
        outfile=ROOT/'previews'/f'contact-{start//(cols*rows)+1:02d}.jpg'
        canvas.save(outfile,'JPEG',quality=92)
    return len(paths)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',choices=['preview','image','contact'],default='preview')
    ap.add_argument('--limit',type=int,default=1,help='max NEW images this run; 0 means all; default=1')
    ap.add_argument('--pace',type=float,default=1.8,help='minimum seconds between ANY network requests')
    ap.add_argument('--timeout',type=float,default=20)
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
        if row.get(key) and (ROOT/row[key]).is_file():continue
        if stage=='image' and row.get('screening_status')!='accept':continue
        if args.limit and count>=args.limit:break
        try:
            maxdim=320 if stage=='preview' else 1600
            ii=get_metadata(client,row,stage,maxdim)
            if ii is None:
                save_records(records);continue
            url=ii.get('thumburl')
            if not url:
                # Some tiny source files do not have a separate thumbnail.
                if max(ii.get('width',999999),ii.get('height',999999)) <= maxdim:
                    url=ii.get('url')
                else:
                    row['review_notes']=f'No API-returned {maxdim}px rendition; refused large original download.'
                    save_records(records)
                    continue
            if not url:
                row['review_notes']='API returned no usable image URL.'
                save_records(records);continue
            raw=client.request(url,'preview' if stage=='preview' else 'image',row['candidate_id'])
            tmp=ROOT/'provenance'/f'.{row["candidate_id"]}-{stage}.partial'
            tmp.write_bytes(raw)
            try:
                with Image.open(tmp) as img:
                    img.verify()
                with Image.open(tmp) as img:
                    w,h=img.size;fmt=img.format
                ext=IMAGE_EXT.get(fmt)
                if not ext:raise ValueError(f'unsupported decoded image format {fmt}')
            except Exception:
                tmp.unlink(missing_ok=True)
                raise
            path=ROOT/('previews/tiles' if stage=='preview' else 'acquired')/f'{row["candidate_id"]}.{ext}'
            path.parent.mkdir(parents=True,exist_ok=True)
            tmp.replace(path)
            rel=str(path.relative_to(ROOT))
            if stage=='preview':
                row.update(preview_url=url,preview_width=w,preview_height=h,preview_sha256=sha256(raw),preview_path=rel)
                row['review_notes']='Preview acquired; awaits visual accept/reject/defer decision.'
            else:
                row.update(acquired_url=url,acquired_width=w,acquired_height=h,acquired_sha256=sha256(raw),acquired_path=rel,acquired_format=fmt,image_downloaded=True)
            count+=1
            save_records(records)
            print(f'{row["candidate_id"]}: acquired {stage} {w}x{h}, {len(raw)} bytes -> {rel}',flush=True)
        except (TransportError, ValueError) as e:
            save_records(records)
            print(f'STOP: {e}',file=sys.stderr)
            make_contact_sheets(records)
            return 2
    save_records(records)
    if stage=='preview':make_contact_sheets(records)
    print(f'New {stage} acquisitions: {count}. (Existing acquisitions reused.)')
    return 0

if __name__=='__main__':sys.exit(main())
