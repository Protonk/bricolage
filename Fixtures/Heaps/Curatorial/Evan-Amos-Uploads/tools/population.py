#!/usr/bin/env python3
"""Freeze and verify direct category membership; exact exclusions, no sampling."""
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from transport import Client, dump, sha, utc

ROOT = Path(__file__).resolve().parents[1]
CATEGORY = 'Category:Media uploaded by Evan Amos'
QUERY = dict(list='categorymembers', cmtitle=CATEGORY, cmtype='file',
             cmprop='ids|title|timestamp', cmlimit='max')


def read(path):
    return json.loads(path.read_text())


def require(value, message):
    if not value:
        raise ValueError(message)


def candidates(rows):
    require(rows and all(r['ns'] == 6 and r['title'].startswith('File:') for r in rows), 'Expected File members')
    require(len({r['pageid'] for r in rows}) == len(rows), 'Repeated category page ID')
    require(len({r['title'] for r in rows}) == len(rows), 'Repeated category title')
    result = [dict(candidate_id=hashlib.sha256(('hazy-evan-amos-file-v1\n'+str(r['pageid'])+'\n'+r['title']).encode('utf-8')).hexdigest()[:20],
                   frozen_title=r['title'], category_pageid=r['pageid'], category_timestamp=r['timestamp'], raw_row=r) for r in rows]
    require(len({r['candidate_id'] for r in result}) == len(rows), 'Candidate ID collision')
    return result


def selection(inventory):
    excluded = (ROOT / 'EXCLUSIONS.txt').read_text().splitlines()
    require(len(excluded) == 3 and len(set(excluded)) == 3, 'Expected three exact exclusions')
    rows = inventory['candidates']
    ordered = sorted(rows, key=lambda r: (r['frozen_title'], r['category_pageid']))
    decisions = [dict(candidate_id=r['candidate_id'], rank=i, frozen_title=r['frozen_title'],
                      decision='excluded_by_user' if r['frozen_title'] in excluded else 'included')
                 for i, r in enumerate(ordered, 1)]
    return dict(policy='Every frozen direct File member except exactly matching supplied titles; no sampling, creator cap, deduplication or substitutions.',
                category=CATEGORY, user_exclusions=excluded,
                absent_exclusion_titles=[t for t in excluded if t not in {r['frozen_title'] for r in rows}],
                included=[r['candidate_id'] for r in decisions if r['decision']=='included'], decisions=decisions,
                counts={state:sum(r['decision']==state for r in decisions) for state in ('included','excluded_by_user')})


def api_receipt(path, expected=None):
    receipt = read(path.with_suffix('.receipt.json'))
    require(receipt['status']==200 and receipt['response_complete'], 'Incomplete API receipt')
    require(receipt['sha256']==sha(path) and receipt['bytes_received']==path.stat().st_size, 'API bytes changed')
    url = urlsplit(receipt['url'])
    require(url.scheme=='https' and url.netloc=='commons.wikimedia.org' and url.path=='/w/api.php', 'Unexpected API URL')
    params = parse_qs(url.query)
    require(params['action']==['query'] and params['format']==['json'] and params['formatversion']==['2'] and params['maxlag']==['5'], 'API query convention differs')
    if expected is not None:
        require(params=={k:[str(v)] for k,v in dict(action='query',format='json',formatversion=2,maxlag=5,**expected).items()}, 'API query differs')
    data = read(path)
    require(not any(k in data for k in ('error','warnings')), 'Failed API response')
    return data, receipt, params


def reconstruct():
    rows=[]; responses=[]; continuation={}; seen=set(); n=1
    while True:
        path=ROOT/f'provenance/api/category-{n:04d}.json'
        data,receipt,_=api_receipt(path,dict(**QUERY,**continuation))
        require('categorymembers' in data.get('query',{}), 'Missing category result')
        rows.extend(data['query']['categorymembers'])
        next_token=data.get('continue')
        responses.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),url=receipt['url'],utc=receipt['utc'],
                              rows=len(data['query']['categorymembers']),continuation=next_token))
        if next_token is None:break
        require(set(next_token)=={'continue','cmcontinue'}, 'Unexpected category continuation')
        token=json.dumps(next_token,sort_keys=True)
        require(token not in seen,'Repeated category continuation');seen.add(token)
        continuation=next_token;n+=1
    require({p.name for p in (ROOT/'provenance/api').glob('category-*.json') if not p.name.endswith('.receipt.json')}=={Path(r['path']).name for r in responses}, 'Unexpected category response files')
    return dict(category=CATEGORY,depth=0,method='MediaWiki list=categorymembers, direct File members, all continuations exhausted',
                candidate_id_algorithm='First 20 hex SHA-256 of UTF-8 hazy-evan-amos-file-v1 + LF + frozen page ID + LF + exact frozen title',
                observed_expected_count=136,actual_count=len(rows),count_difference=len(rows)-136,responses=responses,candidates=candidates(rows))


def freeze():
    require(not (ROOT/'inventory.json').exists(), 'Population already frozen; use offline check')
    client=Client(ROOT);continuation={};seen=set();n=1
    try:
        while True:
            data=client.api(f'category-{n:04d}',**QUERY,**continuation)
            if 'continue' not in data:break
            next_token=data['continue'];require(set(next_token)=={'continue','cmcontinue'},'Unexpected continuation')
            token=json.dumps(next_token,sort_keys=True);require(token not in seen,'Repeated continuation');seen.add(token)
            continuation=next_token;n+=1
        inventory=reconstruct()
    except ValueError as error:
        client.stop(dict(utc=utc(),kind='population-validation',error=str(error),metadata_path=f'provenance/api/category-{n:04d}.json'))
    dump(ROOT/'inventory.json',inventory)
    chosen=selection(inventory);dump(ROOT/'selection.json',chosen)
    dump(ROOT/'ordering.json',dict(algorithm='Ascending exact frozen Unicode title, then numeric category page ID; enumeration only, no random seed or cutoff.',
                                   candidate_ids=[r['candidate_id'] for r in chosen['decisions']]))
    print(check())


def check():
    intake=read(ROOT/'provenance/intake.json')
    for name,digest in intake['source_files'].items():require(sha(ROOT/'provenance/supplied'/name)==digest,'Changed handoff')
    require((ROOT/'EXCLUSIONS.txt').read_bytes()==(ROOT/'provenance/supplied/EXCLUSIONS.txt').read_bytes(),'Changed supplied exclusions')
    inventory=reconstruct();require(read(ROOT/'inventory.json')==inventory,'Inventory does not replay')
    chosen=selection(inventory);require(read(ROOT/'selection.json')==chosen,'Selection does not replay')
    require(read(ROOT/'ordering.json')['candidate_ids']==[r['candidate_id'] for r in chosen['decisions']],'Order differs')
    return dict(status='passed',members=inventory['actual_count'],**chosen['counts'],absent_exclusion_titles=chosen['absent_exclusion_titles'])


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['freeze']:
        import fcntl
        lock=ROOT/'previews/intake.lock';lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a')as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);freeze()
    else:print(json.dumps(check(),indent=2))
