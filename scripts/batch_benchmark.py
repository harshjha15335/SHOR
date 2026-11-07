#!/usr/bin/env python3
"""Auditable paired-model and recovery evaluator. No live calls without explicit budget."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from app.audio import create_variants,encode_wav
from app.benchmark import validate_manifest
from app.gnani import transcribe,configured,GnaniError
from app.metrics import score
from app.recovery import recover


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--output',default='evidence/raw_results/benchmark.jsonl')
    parser.add_argument('--model',choices=['prisma-v2.5','prisma-v3.0'],default='prisma-v2.5')
    parser.add_argument('--models',nargs='+',choices=['prisma-v2.5','prisma-v3.0'],help='Paired models; same source/configuration')
    parser.add_argument('--limit',type=int,default=10)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--allow-live',action='store_true',help='Explicitly authorize planned live requests')
    parser.add_argument('--max-api-calls',type=int,default=0,help='Approved total request budget; never automatically retry')
    args=parser.parse_args(); load_dotenv()
    if args.limit<1: parser.error('--limit must be positive')
    try: rows,validation=validate_manifest(Path(args.manifest))
    except (ValueError,OSError) as exc: parser.error(str(exc))
    rows=rows[:args.limit]; models=list(dict.fromkeys(args.models or [args.model]))
    if 'prisma-v2.5' in models and any(r['language']=='indic-auto' for r in rows): parser.error('indic-auto is incompatible with prisma-v2.5')
    planned=len(rows)*len(models)*4
    print(json.dumps({'validation':validation,'selected_samples':len(rows),'models':models,'planned_api_calls':0 if args.dry_run else planned},ensure_ascii=False))
    # Exercise preprocessing even on dry run; validate complete manifest before any call.
    prepared=[]
    for row in rows:
        variants=create_variants(row['_audio'],row['noise_profile'],row['_snr'],row['_telephony'],row['_seed'],row.get('_ambience'))
        fixed,fixed_decision=recover(variants['degraded'],'fixed')
        adaptive,decision=recover(variants['degraded'],'adaptive')
        prepared.append((row,{'clean':variants['clean'],'degraded':variants['degraded'],'fixed':fixed,'adaptive':adaptive},{'fixed':fixed_decision,'adaptive':decision}))
    if args.dry_run:
        print('DRY RUN COMPLETE: all selected audio processed; zero API requests and no measured accuracy.'); return
    if not args.allow_live or args.max_api_calls<planned: parser.error(f'Live execution needs --allow-live and approved --max-api-calls >= {planned}')
    if not configured(): parser.error('GNANI_API_KEY is unavailable in the runtime')
    output=Path(args.output)
    if output.exists(): parser.error('Output already exists; choose a fresh filename to preserve prior evidence')
    output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    experiment=str(uuid4()); calls=0; failures=0
    code_commit=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    with open(output,'x',encoding='utf-8',opener=lambda path,flags:os.open(path,flags,0o600)) as f:
        for row,variants,decisions in prepared:
            for model in models:
                for variant,audio in variants.items():
                    content=encode_wav(audio)
                    record={'schema_version':1,'experiment_id':experiment,'sample_id':row['sample_id'],'speaker_id':row['speaker_id'],'dataset_split':row['dataset_split'],'language':row['language'],'condition':row['audio_condition'],'condition_origin':row['actual_or_synthetic_condition'],'model':model,'format':'verbatim','variant':variant,'source_sha256':row['file_sha256'],'audio_sha256':hashlib.sha256(content).hexdigest(),'reference':row['reference_transcript'],'critical_terms':row['critical_terms'].split('|'),'noise_profile':row['noise_profile'],'configured_snr_db':row['_snr'],'telephone_simulation':row['_telephony'],'seed':row['_seed'],'recovery':decisions.get(variant),'requested_at':datetime.now(timezone.utc).isoformat(),'metrics':None,'code_commit':code_commit,'python_version':platform.python_version(),'dataset_metadata':{k:row[k] for k in ['consent_status','reference_review_status','transcript_script_convention','code_mixed','recording_environment','recording_device_category','original_sample_rate','processed_sample_rate','duration_seconds','source_utterance_id']}}
                    # Calls remain within the preflight cap; no hidden retry.
                    calls+=1
                    try:
                        record.update(transcribe(content,row['language'],model))
                        try:
                            record['metrics']=score(row['reference_transcript'],record['transcript'],record['critical_terms'])
                        except ValueError as exc:
                            failures+=1; record['metrics_error']=str(exc)
                    except (GnaniError,ValueError) as exc:
                        failures+=1; record.update(status='error',error=str(exc),error_code=getattr(exc,'code','evaluation_error'),http_status=getattr(exc,'http_status',None),transcript=None)
                        if getattr(exc,'diagnostics',None) is not None:
                            record['private_http_diagnostics']=exc.diagnostics
                    record['completed_at']=datetime.now(timezone.utc).isoformat()
                    f.write(json.dumps(record,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
    print(json.dumps({'output':str(output),'requests_attempted':calls,'errors':failures,'experiment_id':experiment}))
    if failures: raise SystemExit(1)

if __name__=='__main__':main()
