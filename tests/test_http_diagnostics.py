"""Entirely local response fixtures; no HTTP call is allowed by these tests."""
import json
import requests
import pytest
from app.http_diagnostics import capture_error,MAX_BODY
from app import gnani
from app.audio import encode_wav
import numpy as np


def reply(body,headers=None,status=403):
 r=requests.Response();r.status_code=status
 r._content=json.dumps(body).encode() if not isinstance(body,bytes) else body
 r.headers.update(headers or {})
 return r


def test_scope_code_kept_free_text_and_secret_fields_dropped():
 secret='test-credential-only-never-real'
 d=capture_error(reply({'detail':{'error_code':'SCOPE_NOT_ALLOWED','message':secret,'transcript':'private speech'},'api_key':secret,'reference':'private reference'}),secret)
 assert d['body']['sanitized']=={'detail':{'error_code':'SCOPE_NOT_ALLOWED'}}
 assert secret not in json.dumps(d)
 assert 'private speech' not in json.dumps(d) and 'private reference' not in json.dumps(d)
 assert d['origin']=='unverified'


def test_header_allowlist_redacts_credential_and_drops_auth_cookies():
 secret='test-credential-only'
 d=capture_error(reply({}, {'Content-Type':'application/json','X-Proxy-Error':'POLICY_DENIED','X-Request-ID':'safe-correlation-123','Authorization':'Bearer '+secret,'Set-Cookie':secret,'X-Correlation-ID':secret,'X-Other':'private'}),secret)
 assert d['headers']=={'content-type':'application/json','x-proxy-error':'POLICY_DENIED','x-request-id':'safe-correlation-123','x-correlation-id':'[REDACTED]'}
 assert secret not in json.dumps(d)


@pytest.mark.parametrize('body,expected',[(b'<html>secret or personal response</html>','non_json_redacted'),(b'x'*(MAX_BODY+1),'omitted_size_limit'),([], 'non_object_json_redacted')])
def test_untrusted_bodies_are_not_preserved(body,expected):
 d=capture_error(reply(body),'secret')
 assert d['body']['capture']==expected
 assert 'personal' not in json.dumps(d)


def test_unknown_error_code_and_arbitrary_nested_fields_redacted():
 d=capture_error(reply({'detail':{'error_code':'UNRECOGNIZED_OR_PERSONAL_VALUE','message':'private'},'message':'private'}),'key')
 assert d['body']['sanitized']=={}


def test_credential_that_equals_code_is_redacted():
 d=capture_error(reply({'detail':{'error_code':'SCOPE_NOT_ALLOWED'}}),'SCOPE_NOT_ALLOWED')
 assert 'SCOPE_NOT_ALLOWED' not in json.dumps(d)


def test_adapter_attaches_private_diagnostics_without_public_leak(monkeypatch):
 monkeypatch.setenv('GNANI_API_KEY','test-credential-only')
 calls=[]
 def fake(*args,**kwargs):
  calls.append(kwargs)
  return reply({'detail':{'error_code':'SCOPE_NOT_ALLOWED','message':'test-credential-only'}},{'X-Request-ID':'test-correlation','Content-Type':'application/json'})
 monkeypatch.setattr(gnani.requests,'post',fake)
 with pytest.raises(gnani.GnaniError) as e:
  gnani.transcribe(encode_wav(np.zeros(16000,dtype=np.float32)),'en-IN','prisma-v2.5')
 assert len(calls)==1
 assert calls[0]['headers']['X-API-Key-ID']=='test-credential-only'
 assert e.value.diagnostics['body']['sanitized']['detail']['error_code']=='SCOPE_NOT_ALLOWED'
 assert 'test-correlation' not in str(e.value)
 assert 'SCOPE_NOT_ALLOWED' not in json.dumps(gnani.status_snapshot())
 assert 'test-credential-only' not in str(e.value)
