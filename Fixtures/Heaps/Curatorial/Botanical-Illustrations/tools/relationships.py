"""Retain explicit alternate-file links as exclusion evidence, never expected pairs."""
import re
import botanical as b


def links(wikitext):
    passages = re.findall(r'(?im)^[ \t]*\|[ \t]*other[ _]?versions?[ \t]*=([^\n]*(?:\n(?![ \t]*\||[ \t]*}}).*)*)', wikitext)
    passages += re.findall(r'(?is)\{\{(?:derived from|extracted from|image extracted|cropped)[^}]*}}', wikitext)
    titles = set()
    for passage in passages:
        titles.update(re.findall(r'(?i)(?:File:|Image:)([^\]|}\n]+\.(?:jpg|jpeg|png|tiff?|webp|svg))', passage))
        titles.update(re.findall(r'\|\s*(?:\d+=)?\s*([^|{}\n]+\.(?:jpg|jpeg|png|tiff?|webp|svg))', passage, re.I))
        titles.update(re.findall(r'(?im)^\s*(?:File:)?([^<>\n|]+\.(?:jpg|jpeg|png|tiff?|webp|svg))(?=\s*\||\s*$)', passage))
    return sorted({'File:'+b.norm(t.strip()) for t in titles}), sorted(set(p.strip() for p in passages if p.strip()))


def evidence():
    titles = {}
    meta = b.evidence()
    for cid, candidate in b.candidates().items():
        titles.setdefault(b.norm(candidate['frozen_title']), set()).add(cid)
        if cid in meta:
            titles.setdefault(b.norm(meta[cid]['page']['title']), set()).add(cid)
    rows = []
    for cid, record in meta.items():
        page = record['page']
        text = page.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('content', '')
        refs, passages = links(text)
        if passages:
            ids = sorted({other for ref in refs for other in titles.get(b.norm(ref), []) if other != cid})
            rows.append(dict(candidate_id=cid, metadata_path=record['metadata_path'], metadata_sha256=record['metadata_sha256'],
                             linked_titles=refs, linked_inventory_candidates=ids, raw_passages=passages))
    return sorted(rows, key=lambda r: r['candidate_id'])


def check_selected(selected):
    chosen = set(selected)
    for row in evidence():
        if row['candidate_id'] in chosen:
            b.require(not (chosen & set(row['linked_inventory_candidates'])), 'Selected explicit alternate-file relationship requires reconciliation: '+row['candidate_id'])
