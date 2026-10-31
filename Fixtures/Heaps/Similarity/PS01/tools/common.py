"""Shared, lossless JSONL↔CSV operations for this prompt_heap acquisition pack."""
import csv, io, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'candidates.jsonl'

def local(name):
    p=ROOT/name
    if Path(name).is_absolute() or '..' in Path(name).parts or ROOT.resolve() not in p.resolve().parents:
        raise ValueError(f'Path outside fixture: {name}')
    if any(q.is_symlink() for q in [p,*p.parents] if q!=ROOT.parent):
        raise ValueError(f'Symlink not allowed: {name}')
    return p

def load_records():
    with CANON.open('r',encoding='utf-8') as fp:
        records=[json.loads(line) for line in fp if line.strip()]
    ids=[r['candidate_id'] for r in records]
    if len(ids)!=len(set(ids)):
        raise ValueError('Repeated candidate_id in canonical JSONL')
    return records

def atomic_write(path,contents):
    path=local(str(Path(path).relative_to(ROOT)));path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp');local(str(tmp.relative_to(ROOT)))
    tmp.write_bytes(contents)
    os.replace(tmp,path)

def save_records(records):
    ids=[r['candidate_id'] for r in records]
    if len(ids)!=len(set(ids)):
        raise ValueError('Refusing to write duplicate candidate IDs')
    blob=''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records).encode('utf-8')
    # Build CSV from UNION of all keys, because API enrichment introduces fields later.
    keys=list(dict.fromkeys(k for record in records for k in record.keys()))
    buff=io.StringIO(newline='')
    writer=csv.DictWriter(buff,fieldnames=keys)
    writer.writeheader();writer.writerows(records)
    atomic_write(CANON,blob)
    atomic_write(ROOT/'candidates.csv',buff.getvalue().encode('utf-8'))

def append_jsonl(path,record):
    path=local(str(Path(path).relative_to(ROOT)));path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as fp:
        fp.write(json.dumps(record,ensure_ascii=False)+'\n')
