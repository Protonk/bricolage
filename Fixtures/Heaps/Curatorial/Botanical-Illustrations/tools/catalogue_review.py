#!/usr/bin/env python3
"""Record explicit named MS Sherard 244 folios from retained catalogue fields.

These original watercolor folios are identified by manuscript and folio, not
artist equality or a species label. All other candidates require explicit review.
"""
import sys,re,json,subprocess
from pathlib import Path
import botanical as b
p=b.ROOT
reviews=b.read(p/'provenance/work-review.json');ev=b.evidence();result={}
for n,c in enumerate(b.order(),1):
 if n>int(sys.argv[1]) or c in reviews or c not in ev:continue
 page=ev[c]['page'];m=re.fullmatch(r'File:Bodleian-Library-MS-Sherard-244 \d+ f-(\d+)-(.+)\.jpg',page['title'])
 if not m:continue
 w=page['revisions'][0]['slots']['main']['content'];folio=m[1]
 assert re.search(r'\|\s*Illustrator\s*=.*Ferdinand Bauer',w)
 assert re.search(r'\|\s*Pageoverview\s*=\s*f\.'+folio+r' of 196',w)
 assert 'Flora Græca Drawings and Watercolours' in w
 assert page['imageinfo'][0]['extmetadata']['LicenseShortName']['value']=='Public domain'
 result[n]=dict(decision='eligible',work_key='bodleian-ms-sherard-244-f'+folio,basis='Metadata identifies an individual Flora Graeca original drawing/watercolour in manuscript MS Sherard 244, folio '+folio+', subtitle '+m[2].replace('-',' ')+'. Named folio identity distinguishes the original work; reviewed from retained Book template and source collection evidence, without aesthetic inspection. No named alternate version in file record.',original_artist='Ferdinand Bauer',digitizer='Bodleian Libraries, University of Oxford',creator_basis='Retained Book template explicitly names Ferdinand Bauer as Illustrator, independently of its Author/rendered Artist field. Digital Source names the Bodleian collection; uploader recorded separately.')
subprocess.run([sys.executable,str(p/'tools/review.py')],input=json.dumps(result),text=True,check=True)
