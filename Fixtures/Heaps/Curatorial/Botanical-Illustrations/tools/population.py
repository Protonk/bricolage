#!/usr/bin/env python3
"""Offline reconstruction of the actual Safari-exported Botanical Illustrations PetScan population."""
import hashlib,json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,unquote
from transport import sha
ROOT=Path(__file__).resolve().parents[1]
SEED='hazy-botanical-illustrations-direct-v1'

def require(value,message):
 if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text())

def rows_from_export(data):
 require(data.get('n')=='result' and len(data.get('*',[]))==1,'Unexpected PetScan result structure')
 rows=data['*'][0]['a']['*'];require(rows and all(r['namespace']==6 and r['nstext']=='File' for r in rows),'Expected nonempty File namespace population')
 require(len({r['id'] for r in rows})==len(rows),'Repeated File page ID; reconcile raw listings explicitly')
 require(len({r['title'] for r in rows})==len(rows),'Repeated File title; reconcile raw listings explicitly')
 return rows

def candidates(rows):
 result=[]
 for row in rows:
  title='File:'+row['title'];cid=hashlib.sha256(('hazy-botanical-file-v1\n'+title).encode('utf-8')).hexdigest()[:20]
  result.append(dict(candidate_id=cid,frozen_title=title,petscan_pageid=row['id'],raw_row=row))
 require(len({r['candidate_id'] for r in result})==len(result),'Candidate ID collision')
 return result

def ordering(rows):return sorted([r['candidate_id'] for r in rows],key=lambda c:(hashlib.sha256((SEED+'\n'+c).encode('utf-8')).hexdigest(),c))

class HTMLRows(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.titles=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='input' and a.get('class')=='qcb':self.ids.append(int(a['q']))
  if tag=='a' and a.get('class')=='pagelink':self.titles.append(unquote(urlsplit(a['href']).path.split('/wiki/',1)[1]))

def check(root=ROOT):
 intake=read(root/'provenance/intake.json')
 for name,digest in intake['source_files'].items():require(sha(root/'provenance/supplied'/name)==digest,'Changed supplied handoff')
 rec=read(root/'provenance/population/browser-export.json');raw=root/rec['export_file'];page=root/rec['html_file']
 require(sha(raw)==rec['export_sha256'] and sha(page)==rec['html_sha256'],'Changed browser export evidence')
 data=read(raw);rows=rows_from_export(data);params=parse_qs(urlsplit(data['a']['query']).query,keep_blank_values=True)
 require(params==rec['export_reported_parameters'] and data['a']['query']==rec['export_reported_query_url'],'Changed executed query')
 for key,value in [('project','wikimedia'),('language','commons'),('depth','0'),('ns[6]','1'),('format','json'),('output_limit','5000'),('categories','Botanical illustrations')]:require(params[key]==[value],'Changed population scope')
 require(len(rows)<int(params['output_limit'][0]),'Output cap reached; completeness unresolved')
 html=HTMLRows();html.feed(page.read_text());require(html.ids==[r['id'] for r in rows] and html.titles==['File:'+r['title'] for r in rows],'Loaded Safari results differ from JSON export')
 require(len(rows)==rec['reported_browser_count']==rec['export_rows']==rec['unique_pageids']==rec['unique_titles'],'Population counts differ')
 inv=read(root/'provenance/intake/inventory.json');require(inv['snapshot_sha256']==sha(raw) and inv['candidates']==candidates(rows),'Inventory cannot be reconstructed from raw export')
 ordered=read(root/'provenance/intake/ordering.json');require(ordered['seed']==SEED and ordered['snapshot_sha256']==sha(raw) and ordered['candidate_ids']==ordering(inv['candidates']),'Seeded order differs')
 return dict(status='passed',raw_listings=len(rows),unique_file_identities=len(rows),browser_count=rec['reported_browser_count'],snapshot_sha256=sha(raw),psid=rec['psid'])
if __name__=='__main__':print(json.dumps(check(),indent=2))
