#!/usr/bin/env python3
"""Record the current acquisition outcome without changing visual decisions."""
import hashlib,json
from collections import Counter
from common import ROOT,load_records,atomic_write
rows=load_records();selected=[r for r in rows if r['screening_status']=='accept']
acquired=[r for r in selected if r.get('acquired_path')];pending=[r for r in selected if not r.get('acquired_path')]
stop=ROOT/'provenance/last_transport_error.json'
log=[json.loads(l) for l in (ROOT/'provenance/http_log.jsonl').read_text().splitlines()]
status='stopped' if stop.exists() else 'partial' if pending else 'complete'
if not stop.exists() and all(r['screening_status'] in ('accept','reject','defer') for r in rows) and len(selected)<30 and not acquired:
    status='abandoned_below_floor'
result=dict(status=status,candidate_count=len(rows),preview_count=sum(bool(r.get('preview_path')) for r in rows),visually_selected=len(selected),acquired_count=len(acquired),pending_candidate_ids=[r['candidate_id'] for r in pending],pending_statuses={r['candidate_id']:r['source_acquisition_status'] for r in pending},request_attempts=sum(r.get('kind')!='decode' for r in log),complete_responses=sum(r.get('kind')!='decode' and r.get('response_complete') is True for r in log),decode_stops=sum(r.get('kind')=='decode' for r in log),automatic_retries=0,media_bytes=sum((ROOT/r['acquired_path']).stat().st_size for r in acquired),rendition_kinds=dict(Counter(r['acquired_rendition_kind'] for r in acquired)))
if status=='abandoned_below_floor':result['reason']='Completed screening produced fewer than the required 30 viable inputs; no source acquisition or publication.'
result['initial_visual_fits']=sum(r.get('visually_accepted') is True for r in rows)
result['eligible_selected']=len(selected)
result['excluded_after_visual_fit']=sum(r.get('visually_accepted') is True and r['screening_status']=='reject' for r in rows)
result['preview_size_diagnosis']='provenance/preview-size-diagnosis.json'
result['preview_requested_edges']=dict(Counter(r.get('preview_requested_max_edge') for r in rows if r.get('preview_path')))
result['resolution_adjustments']=[dict(candidate_id=r['candidate_id'],initial_metadata_path=f"provenance/api/{r['candidate_id']}-source.json",acquired_metadata_path=r['api_source_metadata_path'],requested_max_edge=r['source_requested_max_edge'],reason='Explicit smaller API rendition request after the nominal 1600 request offered an unscaled original outside the bound.') for r in acquired if r['source_requested_max_edge']!=1600]
if stop.exists():result.update(stop_record='provenance/last_transport_error.json',stop_record_sha256=hashlib.sha256(stop.read_bytes()).hexdigest(),reason=json.loads(stop.read_text()))
atomic_write(ROOT/'provenance/acquisition.json',(json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))
