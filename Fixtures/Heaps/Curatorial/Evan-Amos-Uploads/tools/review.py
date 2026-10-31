#!/usr/bin/env python3
"""Record current file-specific identity/rights claims, without changing membership."""
import re
import evan as e
from transport import dump


def records():
    result={};members=e.candidates()
    for cid,record in e.evidence().items():
        page=record['page'];infos=page.get('imageinfo',[]);revisions=page.get('revisions',[])
        info=infos[0]if infos else {};meta=info.get('extmetadata',{});value=lambda k:e.clean(meta.get(k,{}).get('value'))
        text=revisions[0].get('slots',{}).get('main',{}).get('content','')if revisions else ''
        author=re.search(r'(?im)^\|\s*Author\s*=([^\n]*)',text)
        author=author.group(1).strip()if author else None
        artist=value('Artist');license_name=value('LicenseShortName');license_url=value('LicenseUrl')
        pd_self=bool(re.search(r'(?i)\{\{\s*PD-self\s*(?:\||}})',text))
        reasons=[]
        if page.get('pageid')!=members[cid]['category_pageid'] or record['redirected']:reasons.append('Resolved category identity differs; explicit reconciliation required')
        if len(infos)!=1 or len(revisions)!=1 or not text:reasons.append('Missing current file or page-revision evidence')
        if not (license_name=='Public domain' and value('Copyrighted')=='False' and pd_self):reasons.append('Rights declaration outside the reviewed PD-self case; manual review required')
        if info.get('mime') not in e.SUPPORTED_MIME:reasons.append('Original format requires supported standalone rendition review')
        # This role follows the file's Author attribution, never category/uploader identity.
        photographer='Evan-Amos'if author and re.search(r'\[\[User:Evan-Amos\|Evan-Amos]]',author)and artist and artist.startswith('Evan-Amos')else None
        modifier='Gunnar.offel'if author and 'modified by [[User:Gunnar.offel|Gunnar.offel]]'in author else None
        result[cid]=dict(candidate_id=cid,status='blocked'if reasons else'ready',blocking_reasons=reasons,
                         metadata_path=record['metadata_path'],metadata_sha256=record['metadata_sha256'],
                         category_title=members[cid]['frozen_title'],category_pageid=members[cid]['category_pageid'],
                         canonical_title=page['title'],pageid=page.get('pageid'),redirected=record['redirected'],
                         reported_artist=artist,reported_author_wikitext=author,original_creator=photographer,
                         digital_modifier=modifier,copyright_holder=None,uploader_current_file_revision=info.get('user'),
                         creator_basis='Original creator follows the file-specific Author attribution when explicitly parsed; digital modifier only when explicitly named. Neither category membership nor current file-version uploader supplies creator identity. Copyright holder remains unknown.',
                         credit=value('Credit'),license=license_name,license_url=license_url,usage_terms=value('UsageTerms'),restrictions=value('Restrictions'),
                         rights_basis='Retained file-specific PD-self declaration, Public domain usage claim and Copyrighted=False agree.'if not reasons else'Unresolved: '+'; '.join(reasons),
                         rights_limit='Commons claims are preserved, not independently authenticated; no blanket collection license.')
    return result


if __name__=='__main__':
    result=records();dump(e.ROOT/'provenance/rights-review.json',result)
    print({s:sum(r['status']==s for r in result.values())for s in ('ready','blocked')})
