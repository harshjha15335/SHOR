#!/usr/bin/env python3
"""One explicit real call on one reviewed, consented manifest sample. No retries."""
import argparse,hashlib,json,sys,os,platform,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from app.benchmark import validate_manifest
from app.gnani import transcribe,configured,GnaniError
from app.audio import encode_wav
from app.metrics import score

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--sample-id',required=True)
    parser.add_argument('--model',choices=['prisma-v2.5','prisma-v3.0'],default='prisma-v2.5')
    parser.add_argument('--allow-one-live-call',action='store_true')
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();load_dotenv()
    try: rows,_=validate_manifest(args.manifest)
    except (OSError,ValueError) as exc:parser.error(str(exc))
    selected=[r for r in rows if r['sample_id']==args.sample_id]
    if not selected:parser.error('sample-id not found')
    row=selected[0]
    if row['language']=='indic-auto' and args.model=='prisma-v2.5':parser.error('indic-auto requires Prisma v3.0')
    if row['actual_or_synthetic_condition']!='actual':parser.error('Smoke test requires actual recorded speech, not a synthetic condition')
    if not args.allow_one_live_call:parser.error('Explicit --allow-one-live-call required')
    if not configured():parser.error('GNANI_API_KEY unavailable in current runtime')
    if args.output.exists():parser.error('Output exists; preserve prior evidence')
    content=encode_wav(row['_audio']); experiment=str(uuid4())
    record={'schema_version':1,'experiment_id':experiment,'sample_id':row['sample_id'],'speaker_id':row['speaker_id'],'dataset_split':row['dataset_split'],'language':row['language'],'condition':row['audio_condition'],'model':args.model,'format':'verbatim','variant':'clean','source_sha256':row['file_sha256'],'audio_sha256':hashlib.sha256(content).hexdigest(),'reference':row['reference_transcript'],'requested_at':datetime.now(timezone.utc).isoformat(),'metrics':None,'code_commit':subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),'python_version':platform.python_version(),'dataset_metadata':{k:row[k] for k in ['consent_status','reference_review_status','transcript_script_convention','code_mixed','recording_environment','recording_device_category','original_sample_rate','processed_sample_rate','duration_seconds','source_utterance_id']}}
    # Prove the evidence destination can be opened before spending any credits.
    args.output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with open(args.output,'x',encoding='utf-8',opener=lambda path,flags:os.open(path,flags,0o600)) as f:
        f.flush();os.fsync(f.fileno())
        failed=False
        started=time.perf_counter()
        try:
            record.update(transcribe(content,row['language'],args.model))
            try:
                record['metrics']=score(row['reference_transcript'],record['transcript'],row['critical_terms'].split('|'))
            except ValueError as exc:
                failed=True;record['metrics_error']=str(exc)
        except (GnaniError,ValueError) as exc:
            failed=True;record.update(status='error',error=str(exc),error_code=getattr(exc,'code','evaluation_error'),http_status=getattr(exc,'http_status',None),transcript=None,wall_time_seconds=round(time.perf_counter()-started,6))
        record['completed_at']=datetime.now(timezone.utc).isoformat()
        record['request_attempts']=1
        f.write(json.dumps(record,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
    print('One API call attempted; evidence saved locally. Status:',record['status'])
    if failed:raise SystemExit(1)
if __name__=='__main__':main()
