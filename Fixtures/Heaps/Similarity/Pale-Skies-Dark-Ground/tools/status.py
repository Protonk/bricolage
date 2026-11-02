#!/usr/bin/env python3
"""Report candidate review/acquisition counts without conflating them."""
from collections import Counter
from common import load_records,ROOT
rs=load_records()
print('candidates:',len(rs))
for field in ['screening_status','preview_acquisition_status','source_acquisition_status']:
    print(field,dict(Counter(str(r.get(field)) for r in rs)))
print('visual accepts:',sum(r.get('visually_accepted') is True for r in rs))
print('visually accepted but source not acquired:',sum(r.get('visually_accepted') is True and not (r.get('acquired_path') and (ROOT/r['acquired_path']).is_file()) for r in rs))
print('preview files present:',sum(bool(r.get('preview_path') and (ROOT/r['preview_path']).is_file()) for r in rs))
print('source files present:',sum(bool(r.get('acquired_path') and (ROOT/r['acquired_path']).is_file()) for r in rs))
