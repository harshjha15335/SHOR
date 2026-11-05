"""SHOR: transparent local speech reliability experiments and auditable evidence."""
from __future__ import annotations
import asyncio
import base64
import csv
import hashlib
import hmac
import io
import json
import math
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

from .audio import create_variants, decode_wav, encode_wav
from .gnani import configured, GnaniError, transcribe
from .metrics import score, compare, normalize
from .recovery import recover
from . import storage, gnani

load_dotenv()
app = FastAPI(title='SHOR', version='0.2.0', description='Evidence-first Indic speech reliability research')
HERE = Path(__file__).resolve().parent
app.mount('/static', StaticFiles(directory=str(HERE / 'static')), name='static')
LANGS = {'hi-IN','en-IN','ta-IN','te-IN','kn-IN','ml-IN','mr-IN','bn-IN','gu-IN','pa-IN','indic-auto'}
PROFILES = {'none','broadband','crowd_synthetic','traffic_synthetic','hum_synthetic','uploaded_ambience'}
_recent = defaultdict(deque)
_busy = False

@app.middleware('http')
async def access_control(request: Request, call_next):
    global _busy
    if request.method not in {'GET','HEAD','OPTIONS'}:
        origin = request.headers.get('origin')
        if request.headers.get('sec-fetch-site') == 'cross-site' or (origin and urlsplit(origin).netloc != request.headers.get('host')):
            return JSONResponse({'detail':'Cross-origin mutations are forbidden'},status_code=403)
    password = os.getenv('SHOR_ACCESS_PASSWORD', '')
    if os.getenv('SHOR_PUBLIC_MODE', 'false').lower() == 'true' and not password:
        return JSONResponse({'detail':'Public mode requires SHOR_ACCESS_PASSWORD'},status_code=503)
    if password and request.url.path != '/api/health':
        try:
            scheme, value = request.headers.get('authorization','').split(' ',1)
            user, supplied = base64.b64decode(value, validate=True).decode().split(':',1)
            authorized = scheme.lower() == 'basic' and hmac.compare_digest(user, 'shor') and hmac.compare_digest(supplied.encode(), password.encode())
        except (ValueError, UnicodeError):
            authorized = False
        if not authorized:
            return JSONResponse({'detail':'Authentication required'},status_code=401,headers={'WWW-Authenticate':'Basic realm="SHOR"'})
    evaluating = request.method == 'POST' and request.url.path == '/api/evaluate'
    if evaluating:
        try:
            length = int(request.headers.get('content-length','-1'))
        except ValueError:
            length = -1
        if length < 0:
            return JSONResponse({'detail':'Content-Length required'},status_code=411)
        if length > 16_100_000:
            return JSONResponse({'detail':'Multipart request exceeds 16.1 MB'},status_code=413)
        now = time.monotonic()
        # One local or authenticated demo operator; aggregate cap avoids spoofed proxy headers.
        recent = _recent['evaluate']
        while recent and recent[0] < now - 60:
            recent.popleft()
        try:
            rate_limit = max(1, min(100, int(os.getenv('SHOR_REQUESTS_PER_MINUTE','10'))))
        except ValueError:
            return JSONResponse({'detail':'Invalid server rate-limit configuration'},status_code=503)
        if len(recent) >= rate_limit:
            return JSONResponse({'detail':'Experiment rate limit reached'},status_code=429)
        if _busy:
            return JSONResponse({'detail':'Another experiment is running; retry after it finishes'},status_code=409)
        recent.append(now)
        _busy = True
    try:
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store'
        return response
    finally:
        if evaluating:
            _busy = False

class BoundedUpload:
    """Bound actual multipart bytes before parsing; one in-memory upload <=16.1 MB."""
    def __init__(self, app):
        self.app = app
        self.receiving = False

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('method') != 'POST' or scope.get('path') != '/api/evaluate':
            return await self.app(scope,receive,send)
        if self.receiving:
            return await JSONResponse({'detail':'Another upload is in progress'},status_code=409)(scope,receive,send)
        self.receiving = True
        try:
            return await self.handle_upload(scope,receive,send)
        finally:
            self.receiving = False

    async def handle_upload(self, scope, receive, send):
        headers = dict(scope.get('headers',[]))
        try:
            declared = int(headers.get(b'content-length', b'-1'))
        except ValueError:
            declared = -1
        if not 0 <= declared <= 16_100_000:
            response=JSONResponse({'detail':'Content-Length required and body must be <=16.1 MB'},status_code=413 if declared>16_100_000 else 411)
            return await response(scope,receive,send)
        chunks=[]; size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':
                return
            chunk=message.get('body',b'');size+=len(chunk)
            if size>16_100_000:
                return await JSONResponse({'detail':'Upload exceeds body limit'},status_code=413)(scope,receive,send)
            chunks.append(chunk)
            if not message.get('more_body',False):
                break
        if size != declared:
            return await JSONResponse({'detail':'Body size differs from Content-Length'},status_code=400)(scope,receive,send)
        payload=b''.join(chunks); delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {'type':'http.request','body':payload,'more_body':False}
            return await receive()
        return await self.app(scope,replay,send)

app.add_middleware(BoundedUpload)

@app.get('/')
def index():
    return FileResponse(HERE / 'static' / 'index.html')

@app.get('/api/health')
def health():
    status = gnani.status_snapshot()
    return {'ok':True, 'gnani_key_configured':configured(),
            'live_inference_available':status.get('live_inference_available', False),
            'gnani':status, 'model_options':['prisma-v2.5','prisma-v3.0'],
            'data_policy':'Private local storage; seven-day default retention on access; delete runs explicitly.'}

@app.get('/api/connection')
def connection_status():
    from .connection import snapshot
    return snapshot()

@app.get('/api/runs')
def runs(q: str='', language: str='', model: str='', profile: str='', mode: str=''):
    records = storage.list_runs()
    records = [r for r in records if (not q or q.casefold() in r['title'].casefold()) and all(not wanted or r.get(key)==wanted for key,wanted in [('language',language),('model',model),('noise_profile',profile),('mode',mode)])]
    return [{'id':r['id'],'title':r['title'],'created_at':r['created_at'],'status':r['status'],
             'model':r['model'],'language':r['language'],'mode':r['mode'],'noise_profile':r['noise_profile'],
             'degraded_wer':(r['results'].get('degraded',{}).get('metrics') or {}).get('wer')} for r in records]

@app.get('/api/summary')
def summary():
    from .benchmark import summarize_runs
    return summarize_runs(storage.list_runs())

@app.get('/api/runs/{run_id}')
def run(run_id: str):
    rec = storage.get(run_id)
    if not rec: raise HTTPException(404,'Run not found')
    return rec

@app.delete('/api/runs/{run_id}')
def delete_run(run_id: str):
    if not storage.delete(run_id): raise HTTPException(404,'Run not found')
    return {'deleted':True,'id':run_id,'audio_artifacts_deleted':True}

@app.get('/api/runs/{run_id}/audio/{variant}')
def audio(run_id: str, variant: str):
    path = storage.audio_path(run_id,variant)
    if not path: raise HTTPException(404,'Audio not found')
    return FileResponse(path, media_type='audio/wav',filename=f'SHOR_{variant}.wav')

@app.get('/api/evidence.json')
def export_evidence():
    return Response(json.dumps({'schema_version':'SHOR-2','runs':storage.list_runs()},ensure_ascii=False,allow_nan=False),media_type='application/json',headers={'Content-Disposition':'attachment; filename=SHOR_evidence.json'})

def csv_safe(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@','\t','\r')):
        return "'"+value
    return value

@app.get('/api/export.csv')
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['run_id','created_at','title','mode','model','language','profile','snr_db','telephony','variant','status','wer_percent','cer_percent','critical_recall_percent','transcript','error','audio_sha256','request_id','api_model','wall_time_seconds','recovery_action','scoring_mode'])
    for rec in storage.list_runs():
        for variant, entry in rec['results'].items():
            m=entry.get('metrics') or {}
            row=[rec['id'],rec['created_at'],rec['title'],rec['mode'],rec['model'],rec['language'],rec['noise_profile'],rec['snr_db'],rec['telephony'],variant,entry['status'],m.get('wer'),m.get('cer'),m.get('critical_recall'),entry.get('transcript'),entry.get('error'),rec.get('audio_hashes',{}).get(variant),entry.get('request_id'),entry.get('api_model'),entry.get('wall_time_seconds'),rec.get('recovery',{}).get('action'),rec.get('scoring_mode','unicode')]
            writer.writerow([csv_safe(v) for v in row])
    return Response(output.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=SHOR_runs.csv'})

@app.post('/api/evaluate')
async def evaluate(
    audio_file: UploadFile=File(...),reference: str=Form(''),title: str=Form('Untitled recording'),
    language: str=Form('hi-IN'),model: str=Form('prisma-v2.5'),profile: str=Form('traffic_synthetic'),
    snr_db: float=Form(8),telephony: bool=Form(True),seed: int=Form(42),critical_terms: str=Form(''),
    mode: str=Form('preview'),ambience_file: UploadFile | None=File(None),
    recovery_mode: str=Form('fixed'),scoring_mode: str=Form('unicode'),
    audio_condition: str=Form('unspecified'),speaker_id: str=Form(''),dataset_split: str=Form('unassigned'),
    approved_api_calls: int=Form(0),
):
    if model not in ('prisma-v2.5','prisma-v3.0') or language not in LANGS or profile not in PROFILES:
        raise HTTPException(400,'Invalid model/language/noise profile')
    if model=='prisma-v2.5' and language=='indic-auto': raise HTTPException(400,'Use Prisma v3.0 for auto language detection')
    if not math.isfinite(snr_db) or not -5<=snr_db<=30: raise HTTPException(400,'SNR must be finite and between -5 and 30 dB')
    if not 0<=seed<=10000000: raise HTTPException(400,'Seed must be between 0 and 10,000,000')
    if mode not in {'live','preview'} or recovery_mode not in {'fixed','adaptive','passthrough'} or scoring_mode not in {'unicode','strict'}:
        raise HTTPException(400,'Invalid mode, recovery or scoring convention')
    if audio_condition not in {'unspecified','quiet_real','noisy_real','telephony_real','synthetic'} or dataset_split not in {'unassigned','dev','validation','test'}:
        raise HTTPException(400,'Invalid source condition or dataset split')
    if len(reference)>2500 or len(critical_terms)>500 or len(speaker_id)>80: raise HTTPException(400,'Text field exceeds limit')
    if reference.strip() and not normalize(reference): raise HTTPException(400,'Reference must contain spoken words')
    if mode=='live':
        if not configured(): raise HTTPException(503,'GNANI_API_KEY is missing; preview does not call Gnani')
        if approved_api_calls != 3: raise HTTPException(400,'Explicit approval for three API requests is required')
    try:
        await run_in_threadpool(storage.ensure_capacity)
    except (ValueError,OSError) as exc:
        raise HTTPException(507,'Storage unavailable or full; free space or delete old runs') from exc
    data=await audio_file.read(8_000_001)
    if len(data)>8_000_000: raise HTTPException(413,'Maximum 8 MB WAV')
    try:
        orig=await run_in_threadpool(decode_wav,data)
        ambience=None
        if profile=='uploaded_ambience':
            if ambience_file is None: raise ValueError('Upload a real ambience WAV')
            ambient_bytes=await ambience_file.read(8_000_001)
            if len(ambient_bytes)>8_000_000: raise ValueError('Ambience WAV exceeds 8 MB')
            ambience=await run_in_threadpool(decode_wav,ambient_bytes)
        variants=await run_in_threadpool(create_variants,orig,profile,snr_db,telephony,seed,ambience)
        recovered,decision=await run_in_threadpool(recover,variants['degraded'],recovery_mode)
        variants['recovered']=recovered
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc
    wavs={name:encode_wav(arr) for name,arr in variants.items()}
    terms=[x.strip() for x in critical_terms.split(',') if x.strip()][:30]
    results={}
    for name,content in wavs.items():
        if mode=='preview':
            results[name]={'status':'not_run','transcript':None,'metrics':None,'note':'Local audio preview; no Gnani request, no fabricated accuracy.'}
        else:
            try:
                result=await run_in_threadpool(transcribe,content,language,model)
                result['metrics']=None
                if reference.strip():
                    try:
                        result['metrics']=score(reference,result['transcript'],terms,scoring_mode=scoring_mode)
                    except ValueError as exc:
                        result['metrics_error']=str(exc)
                results[name]=result
            except (GnaniError,ValueError) as exc:
                results[name]={'status':'error','transcript':None,'metrics':None,'error':str(exc),'error_code':getattr(exc,'code','evaluation_error')}
    delta=compare(results['degraded'].get('metrics'),results['recovered'].get('metrics'))
    record={'schema_version':'SHOR-2','id':str(uuid4()),'created_at':datetime.now(timezone.utc).isoformat(),
            'title':title.strip()[:90] or 'Untitled recording','status':'preview' if mode=='preview' else ('complete' if all(x['status']=='real' for x in results.values()) else 'partial'),
            'mode':mode,'model':model,'language':language,'noise_profile':profile,'snr_db':snr_db,'telephony':telephony,'seed':seed,
            'duration_seconds':round(len(orig)/16000,2),'reference':reference,'critical_terms':terms,'results':results,'comparison':delta,
            'scoring_mode':scoring_mode,'recovery':decision,'audio_condition':audio_condition,'speaker_id':speaker_id,'dataset_split':dataset_split,
            'source_sha256':hashlib.sha256(data).hexdigest(),'audio_hashes':{k:hashlib.sha256(v).hexdigest() for k,v in wavs.items()},
            'parameters':{'format':'verbatim','language_code':language,'model':model},'api_requests_attempted':3 if mode=='live' else 0,
            'provenance':{'audio':'user-uploaded / locally recorded','noise':'user uploaded recording' if profile=='uploaded_ambience' else ('none' if profile=='none' else 'deterministic synthetic audio'),
                          'recovery':f"{decision['action']}: {decision['reason']}",'inference':'Gnani Prisma REST endpoint' if mode=='live' else 'No inference executed'},
            'caveat':'Acoustic risk estimates are heuristic; no ASR improvement guaranteed. No cross-script equivalence or real telephony validation implied.'}
    try:
        await run_in_threadpool(storage.save,record,wavs)
    except ValueError as exc:
        raise HTTPException(507,str(exc)) from exc
    return record
