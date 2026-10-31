#!/usr/bin/env python3
"""Reproduce metadata-only provenance decisions. Never reads image pixels."""
import argparse
import hashlib
import html
import re
from urllib.parse import unquote, urlparse, parse_qs

from poty import (ROOT, CATEGORIES, metadata_records, norm, page_content, read,
                  require, review_rows, slug, text)
from transport import dump


def creator_identity(artist):
    """Accept one explicit author identity; ambiguous role lists need an override."""
    artist = artist or ''
    original = re.search(r'(?is)Original(?: version)?:\s*(?:</b>\s*)?(.+?)(?:</li>|\n|$)', artist)
    if original:
        keys, basis = creator_identity(original[1])
        return keys, 'Original role explicitly separated from derivative/editor attribution. ' + basis
    before_editor = re.split(r'(?i)(?:,?\s+(?:restored|edited|edit) by|\s*-\s*Edited from)', artist)[0]
    if before_editor != artist:
        keys, basis = creator_identity(re.sub(r'(?i)^Photo:\s*', '', before_editor))
        return keys, 'Original credit before explicitly identified editor/restorer. ' + basis
    identities = set()
    for href in re.findall(r'href="([^"]+)"', artist or ''):
        parsed = urlparse(html.unescape(href))
        title = unquote(parsed.path.split('/wiki/', 1)[-1]) if '/wiki/' in parsed.path else parse_qs(parsed.query).get('title', [''])[0]
        if parsed.hostname == 'www.wikidata.org' and re.fullmatch(r'Q\d+', title):
            identities.add('wikidata:' + title)
        elif parsed.hostname in ('commons.wikimedia.org', 'zh.wikipedia.org') and title.startswith('User:'):
            identities.add('user:' + norm(title[5:]))
    if len(identities) == 1:
        return sorted(identities), 'Explicit identity link in Commons Artist attribution.'
    if len(identities) > 1:
        return None, 'Multiple attributed roles require an explicit original-creator review.'
    plain = text(artist)
    if not plain or re.search(r'(?i)unknown|anonymous|unidentified', plain):
        return [], 'Original creator explicitly unknown; uploader is not substituted.'
    if len(plain) < 180 and not re.search(r'(?i)restor|derivative|cropp|panorama|NOTE:', plain):
        return ['name:' + norm(plain)], 'Named Artist attribution, without a canonical identity link; aliases checked in this population.'
    return None, 'Complex Artist field needs explicit original-creator review.'


def relationships(wikitext, title):
    """Preserve explicit other-version/derivation evidence, never inferred visual links."""
    passages = re.findall(r'(?im)^[ \t]*\|[ \t]*other[ _]?versions?[ \t]*=([^\n]*(?:\n(?![ \t]*\||[ \t]*}}).*)*)', wikitext)
    passages += re.findall(r'(?is)\{\{(?:derived from|extracted from|image extracted|cropped)[^}]*}}', wikitext)
    refs = set()
    for passage in passages:
        refs.update(re.findall(r'(?i)(?:File:|Image:)([^\]|}\n]+\.(?:jpg|jpeg|png|tiff?|webp))', passage))
        refs.update(re.findall(r'\|\s*(?:\d+=)?\s*([^|{}\n]+\.(?:jpg|jpeg|png|tiff?|webp))', passage, re.I))
        refs.update(re.findall(r'(?im)^\s*(?:File:)?([^<>\n|]+\.(?:jpg|jpeg|png|tiff?|webp))(?=\s*\||\s*$)', passage))
    # An asset and any explicitly named alternate share an exclusion key.
    refs.add(title.removeprefix('File:'))
    return sorted('asset:' + norm(r.strip()) for r in refs), [p.strip() for p in passages if p.strip()]


def derive(root):
    evidence = review_rows(root)
    metas = metadata_records(root)
    overrides = read(root / 'provenance/review-overrides.json')
    aliases = read(root / 'provenance/creator-aliases.json')
    result = {}
    for ev in evidence:
        cid = ev['candidate_id']
        page, _ = metas[norm(ev['commons_title'])]
        wikitext = page_content(page) if page.get('revisions') else ''
        keys, basis = creator_identity(ev['artist_html'])
        groups, passages = relationships(wikitext, ev['canonical_title'])
        reason = None
        if not ev['pageid'] or not ev['original_sha1']:
            reason = 'source_identity_unverified'
        elif ev['mime'] not in ('image/jpeg', 'image/png', 'image/webp', 'image/tiff'):
            reason = 'unsupported_media_type'
        elif not ev['license'] or not (ev['license_url'] or ev['license'] == 'Public domain'):
            reason = 'license_unverified'
        elif re.search(r'(?i)\bcrop(?:ped)?\d*\b', ev['canonical_title']) or re.search(r'(?i)\{\{\s*(?:extracted from|cropped)\b', wikitext):
            reason = 'documented_alternate_crop'
        elif re.search(r'(?is)\{\{retouched[^}]*\bcrop(?:ped)?\b|the image is a crop', wikitext):
            reason = 'documented_alternate_crop'
        if keys is None:
            reason = reason or 'original_creator_roles_unresolved'
        decision = dict(metadata_sha256=ev['metadata_sha256'], creator_keys=keys or [],
                        creator_basis=basis, creator_unknown=keys == [],
                        license_basis='File-specific API LicenseShortName/LicenseUrl and cached file-page license templates; no collection license inferred.',
                        relationship_keys=groups, relationship_evidence=passages,
                        relationship_basis='Explicit other_versions and derivation references plus canonical page ID and upstream SHA-1; creator cap additionally removes repeated known photographers. No visual or exhaustive series-independence claim.',
                        exclude_reason=reason)
        decision.update(overrides.get(cid, {}))
        decision['creator_keys'] = sorted(set(aliases.get(key, key) for key in decision['creator_keys']))
        result[cid] = decision
    require(set(overrides) <= set(result), 'Override references missing metadata')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--category', choices=CATEGORIES)
    args = parser.parse_args()
    for category in CATEGORIES:
        if args.category and category != args.category:
            continue
        root = ROOT / slug(category)
        result = derive(root)
        dump(root / 'provenance/provenance-review.json', result)
        print(category, len(result), 'reviewed')
        for cid, row in result.items():
            if row['exclude_reason']:
                print(cid, row['exclude_reason'])


if __name__ == '__main__':
    main()
