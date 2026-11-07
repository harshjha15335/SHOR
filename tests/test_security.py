"""Local HTTP privacy controls; mocked inference tests are not live API evidence."""
import base64,csv,hashlib,io
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app import main,storage
from app.audio import encode_wav

client=TestClient(main.app)

@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
 monkeypatch.setattr(storage,'ROOT',tmp_path)
 monkeypatch.setattr(storage,'AUDIO_DIR',tmp_path/'audio')
 monkeypatch.setattr(storage,'DB',tmp_path/'runs.sqlite3')
 monkeypatch.delenv('SHOR_ACCESS_PASSWORD',raising=False)
 monkeypatch.delenv('SHOR_PUBLIC_MODE',raising=False)
 monkeypatch.setenv('SHOR_REQUESTS_PER_MINUTE','100')
 main._recent.clear()
 monkeypatch.setattr(main,'_busy',False)

@pytest.fixture
def wav():return encode_wav((np.sin(np.arange(16000)*.1)*.2).astype(np.float32))

def post(wav,**data):
 return client.post('/api/evaluate',files={'audio_file':('test.wav',wav,'audio/wav')},data={'mode':'preview',**data})

def test_basic_auth_protects_site_data_exports_and_static(monkeypatch):
 monkeypatch.setenv('SHOR_ACCESS_PASSWORD','test-only-password')
 for endpoint in ['/','/static/app.js','/api/runs','/api/evidence.json','/api/export.csv','/api/summary']:
  assert client.get(endpoint).status_code==401
  assert client.get(endpoint,auth=('shor','test-only-password')).status_code==200
 assert client.get('/api/runs',auth=('wrong','test-only-password')).status_code==401
 assert client.get('/api/runs',auth=('shor','wrong')).status_code==401
 assert client.get('/api/health').status_code==200

@pytest.mark.parametrize('header',['Basic !!!','Basic '+base64.b64encode(b'no-colon').decode(),'Bearer abc','Basic '+base64.b64encode(b'\xff:bad').decode()])
def test_bad_auth_never_raises(monkeypatch,header):
 monkeypatch.setenv('SHOR_ACCESS_PASSWORD','test-only-password')
 assert client.get('/api/runs',headers={'Authorization':header}).status_code==401

def test_public_mode_fails_closed_without_password(monkeypatch):
 monkeypatch.setenv('SHOR_PUBLIC_MODE','true')
 for endpoint in ['/','/api/health','/api/runs','/static/app.js']:
  assert client.get(endpoint).status_code==503

@pytest.mark.parametrize('value',['NaN','inf','-inf'])
def test_nonfinite_snr_rejected_without_saving(wav,value):
 assert post(wav,snr_db=value).status_code in (400,422)
 assert storage.list_runs()==[]

def test_live_request_approval_required(wav,monkeypatch):
 monkeypatch.setattr(main,'configured',lambda:True)
 monkeypatch.setattr(main,'transcribe',lambda *args:pytest.fail('No unapproved call allowed'))
 r=post(wav,mode='live')
 assert r.status_code==400
 assert 'approval' in r.json()['detail'].lower()

def test_provenance_json_csv_filter_delete(wav):
 a=post(wav,title='=DANGEROUS()',language='ta-IN',model='prisma-v3.0',profile='none',telephony='false',audio_condition='noisy_real',speaker_id='pseudonym-1',dataset_split='dev',recovery_mode='adaptive')
 assert a.status_code==200,a.text
 r=a.json()
 assert r['source_sha256']==hashlib.sha256(wav).hexdigest()
 for variant in ['clean','degraded','recovered']:
  downloaded=client.get(f'/api/runs/{r["id"]}/audio/{variant}').content
  assert hashlib.sha256(downloaded).hexdigest()==r['audio_hashes'][variant]
 assert client.get('/api/runs',params={'language':'hi-IN'}).json()==[]
 assert len(client.get('/api/runs',params={'language':'ta-IN','model':'prisma-v3.0','profile':'none','mode':'preview','q':'dangerous'}).json())==1
 assert client.get('/api/runs',params={'q':'absent'}).json()==[]
 evidence=client.get('/api/evidence.json').json()
 assert evidence['schema_version']=='SHOR-2'
 assert evidence['runs'][0]['audio_hashes']==r['audio_hashes']
 rows=list(csv.DictReader(io.StringIO(client.get('/api/export.csv').text)))
 assert len(rows)==3
 assert rows[0]['title']=="'=DANGEROUS()"
 assert client.delete('/api/runs/'+r['id']).json()['audio_artifacts_deleted']
 assert client.get('/api/runs/'+r['id']).status_code==404
 assert client.get(f'/api/runs/{r["id"]}/audio/clean').status_code==404
 assert client.get('/api/runs').json()==[]

@pytest.mark.parametrize('value',['=SUM(A1:A3)',' +cmd','-cmd','@cmd','\t=cmd','\r=cmd'])
def test_csv_formula_safe(value):assert main.csv_safe(value).startswith("'")

def test_numeric_csv_not_text_escaped():assert main.csv_safe(-5)==-5

def test_partial_provider_failures_retained(wav,monkeypatch):
 monkeypatch.setattr(main,'configured',lambda:True)
 count=[]
 def fake(*args):
  count.append(1)
  if len(count)==2:raise main.GnaniError('Test-only timeout')
  return {'status':'real','transcript':'hello','request_id':'test-only-'+str(len(count)),'api_model':None,'wall_time_seconds':.01}
 monkeypatch.setattr(main,'transcribe',fake)
 r=post(wav,mode='live',approved_api_calls='3',reference='hello')
 assert r.status_code==200,r.text
 d=r.json();assert d['status']=='partial';assert len(count)==3
 assert d['results']['degraded']['status']=='error'
 assert d['results']['clean']['status']=='real'
 assert client.get('/api/runs/'+d['id']).json()['results']==d['results']

def test_references_do_not_change_recovery(wav):
 a=post(wav,reference='पहला reference',critical_terms='पहला',recovery_mode='adaptive').json()
 b=post(wav,reference='different answer',critical_terms='different',recovery_mode='adaptive').json()
 assert a['audio_hashes']==b['audio_hashes']
 assert a['recovery']['action']==b['recovery']['action']
 assert a['recovery']['features']==b['recovery']['features']

def test_rate_limit_and_busy_gate(wav,monkeypatch):
 monkeypatch.setenv('SHOR_REQUESTS_PER_MINUTE','1')
 assert post(wav).status_code==200
 assert post(wav).status_code==429
 main._recent.clear();monkeypatch.setattr(main,'_busy',True)
 assert post(wav).status_code==409

def test_security_headers(wav):
 r=post(wav)
 assert r.headers['cache-control']=='no-store'
 assert r.headers['x-content-type-options']=='nosniff'
 assert r.headers['referrer-policy']=='same-origin'

@pytest.mark.parametrize('headers',[
 {'Origin':'https://attacker.invalid'},
 {'Origin':'null'},
 {'Sec-Fetch-Site':'cross-site'},
 {'Origin':'http://testserver','Sec-Fetch-Site':'cross-site'},
])
def test_cross_origin_mutations_rejected(wav,headers):
 r=client.post('/api/evaluate',headers=headers,files={'audio_file':('test.wav',wav,'audio/wav')},data={'mode':'preview'})
 assert r.status_code==403
 assert storage.list_runs()==[]
 assert client.delete('/api/runs/not-real',headers=headers).status_code==403

def test_same_origin_mutation_allowed(wav):
 r=client.post('/api/evaluate',headers={'Origin':'http://testserver','Sec-Fetch-Site':'same-origin'},files={'audio_file':('test.wav',wav,'audio/wav')},data={'mode':'preview'})
 assert r.status_code==200,r.text

def test_invalid_rate_configuration_fails_safe(wav,monkeypatch):
 monkeypatch.setenv('SHOR_REQUESTS_PER_MINUTE','not-an-integer')
 r=post(wav);assert r.status_code==503
 assert storage.list_runs()==[]

def test_capacity_preflight_prevents_credit_consumption(wav,monkeypatch):
 monkeypatch.setenv('SHOR_MAX_RUNS','1')
 assert post(wav).status_code==200
 monkeypatch.setattr(main,'configured',lambda:True)
 monkeypatch.setattr(main,'transcribe',lambda *args:pytest.fail('Full storage must not consume credits'))
 assert post(wav,mode='live',approved_api_calls='3').status_code==507
 assert len(storage.list_runs())==1

@pytest.mark.parametrize('declared,body,expected',[
 (None,b'abc',411),('invalid',b'abc',411),('16100001',b'',413),('2',b'abc',400),('3',b'abc',200),
])
def test_raw_body_bound_before_multipart_parser(declared,body,expected):
 import asyncio
 sent=[];called=[]
 async def downstream(scope,receive,send):
  called.append(True)
  message=await receive();assert message['body']==body
  await send({'type':'http.response.start','status':200,'headers':[]})
  await send({'type':'http.response.body','body':b'ok'})
 async def exercise():
  messages=[{'type':'http.request','body':body,'more_body':False}]
  async def receive():return messages.pop(0) if messages else {'type':'http.disconnect'}
  async def send(message):sent.append(message)
  headers=[] if declared is None else [(b'content-length',declared.encode())]
  scope={'type':'http','method':'POST','path':'/api/evaluate','headers':headers}
  await main.BoundedUpload(downstream)(scope,receive,send)
 asyncio.run(exercise())
 assert sent[0]['status']==expected
 assert bool(called)==(expected==200)

def test_actual_body_limit_not_only_declared_length():
 import asyncio
 sent=[]
 async def downstream(*args):pytest.fail('Multipart parser must not see oversized actual bytes')
 async def exercise():
  messages=[{'type':'http.request','body':b'a'*8_050_001,'more_body':True},
            {'type':'http.request','body':b'a'*8_050_001,'more_body':False}]
  async def receive():return messages.pop(0) if messages else {'type':'http.disconnect'}
  async def send(message):sent.append(message)
  await main.BoundedUpload(downstream)({'type':'http','method':'POST','path':'/api/evaluate','headers':[(b'content-length',b'1')]},receive,send)
 asyncio.run(exercise())
 assert sent[0]['status']==413


def test_private_provider_diagnostics_never_reach_web_or_exports(wav,monkeypatch):
 from app.gnani import GnaniError
 monkeypatch.setattr(main,'configured',lambda:True)
 def failed(*args):
  raise GnaniError('Safe access denial','access_denied',403,diagnostics={'body':{'detail':{'error_code':'SCOPE_NOT_ALLOWED'}},'headers':{'x-request-id':'private-correlation-only'}})
 monkeypatch.setattr(main,'transcribe',failed)
 response=post(wav,mode='live',approved_api_calls='3')
 assert response.status_code==200
 for text in [response.text,client.get('/api/evidence.json').text,client.get('/api/export.csv').text,client.get('/api/health').text]:
  assert 'private-correlation-only' not in text
  assert 'SCOPE_NOT_ALLOWED' not in text
  assert 'private_http_diagnostics' not in text
