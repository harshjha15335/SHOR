"""Software tests using mocked HTTP responses; no real inference evidence."""
import numpy as np
import pytest
import requests
from unittest.mock import Mock
from app import gnani
from app.audio import encode_wav


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    monkeypatch.setenv('GNANI_API_KEY', 'software-test-placeholder')
    with gnani._lock:
        gnani._state.update(network_reachable=None, authentication_validated=False,
                            validated_models=[], last_successful_request_at=None,
                            last_connection_error=None)


@pytest.fixture
def audio():
    return encode_wav(np.zeros(16000, dtype=np.float32))


def response(monkeypatch, status=200, data=None):
    r=Mock(status_code=status)
    r.json.return_value=data if data is not None else {'transcript':'नमस्ते', 'request_id':'software-test-id', 'model':'software-test-version'}
    post=Mock(return_value=r)
    monkeypatch.setattr(gnani.requests,'post',post)
    return r,post


def test_key_presence_is_not_live_validation():
    s=gnani.status_snapshot()
    assert s['key_present']
    assert s['network_reachable'] is None
    assert not s['authentication_validated']
    assert not s['live_inference_available']


def test_real_shaped_response_preserves_provenance(audio,monkeypatch):
    r,post=response(monkeypatch)
    d=gnani.transcribe(audio,'hi-IN','prisma-v2.5')
    assert d['transcript']=='नमस्ते'
    assert d['api_model']=='software-test-version'
    assert d['requested_model']=='prisma-v2.5'
    assert d['request_id']=='software-test-id'
    assert len(d['audio_sha256'])==64
    assert d['request_started_at']<=d['response_received_at']
    assert d['wall_time_seconds']>=0
    assert post.call_args.kwargs['timeout']==(5,75)
    assert post.call_args.kwargs['allow_redirects'] is False
    assert gnani.status_snapshot()['live_inference_available']
    r.close.assert_called_once()


def test_missing_metadata_stays_missing_and_empty_transcript_valid(audio,monkeypatch):
    response(monkeypatch,data={'transcript':''})
    d=gnani.transcribe(audio,'ta-IN','prisma-v3.0')
    assert d['transcript']=='' and d['api_model'] is None and d['request_id'] is None


@pytest.mark.parametrize('status,code',[(400,'invalid_request'),(401,'authentication'),(402,'credits'),(403,'access_denied'),(404,'unsupported_resource'),(413,'invalid_audio'),(422,'invalid_request'),(429,'rate_limited'),(500,'provider_unavailable'),(503,'provider_unavailable')])
def test_http_failure_is_safe_and_not_retried(audio,monkeypatch,status,code):
    r,post=response(monkeypatch,status=status,data={'private':'sensitive test content'})
    with pytest.raises(gnani.GnaniError) as e: gnani.transcribe(audio,'hi-IN','prisma-v2.5')
    assert e.value.code==code and e.value.http_status==status
    assert 'sensitive' not in str(e.value)
    post.assert_called_once()
    assert gnani.status_snapshot()['last_connection_error']['code']==code
    assert not gnani.status_snapshot()['authentication_validated']


@pytest.mark.parametrize('payload',[[],None,{}, {'transcript':None},{'transcript':12},{'success':False,'transcript':'hi'}, {'transcript':'x'*100001}])
def test_invalid_schemas(audio,monkeypatch,payload):
    r,_=response(monkeypatch); r.json.return_value=payload
    with pytest.raises(gnani.GnaniError): gnani.transcribe(audio,'hi-IN','prisma-v2.5')


def test_invalid_json(audio,monkeypatch):
    r,_=response(monkeypatch); r.json.side_effect=ValueError('private upstream text')
    with pytest.raises(gnani.GnaniError,match='invalid or truncated JSON'): gnani.transcribe(audio,'hi-IN','prisma-v2.5')


@pytest.mark.parametrize('exc,code',[(requests.Timeout('secret'), 'timeout'),(requests.ConnectionError('secret'), 'connection_error'),(requests.exceptions.ChunkedEncodingError('secret'),'connection_error')])
def test_network_exceptions_safe(audio,monkeypatch,exc,code):
    post=Mock(side_effect=exc);monkeypatch.setattr(gnani.requests,'post',post)
    with pytest.raises(gnani.GnaniError) as e: gnani.transcribe(audio,'hi-IN','prisma-v2.5')
    assert e.value.code==code and 'secret' not in str(e.value)
    post.assert_called_once()


@pytest.mark.parametrize('language,model', [('invalid','prisma-v2.5'),('indic-auto','prisma-v2.5'),('hi-IN','unknown')])
def test_invalid_configuration_never_sends(audio,monkeypatch,language,model):
    _,post=response(monkeypatch)
    with pytest.raises(gnani.GnaniError): gnani.transcribe(audio,language,model)
    post.assert_not_called()


def test_missing_key_never_sends(audio,monkeypatch):
    monkeypatch.delenv('GNANI_API_KEY')
    _,post=response(monkeypatch)
    with pytest.raises(gnani.GnaniError) as e:gnani.transcribe(audio,'hi-IN','prisma-v2.5')
    assert e.value.code=='missing_key';post.assert_not_called()


@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1,True,'fast'])
def test_invalid_latency_is_not_evidence(audio,monkeypatch,value):
    response(monkeypatch,data={'transcript':'hi','end_to_end_latency':value})
    assert gnani.transcribe(audio,'en-IN','prisma-v3.0')['provider_latency_seconds'] is None


def test_bad_audio_never_sends(monkeypatch):
    _,post=response(monkeypatch)
    with pytest.raises(gnani.GnaniError):gnani.transcribe(b'not a wav','hi-IN','prisma-v2.5')
    post.assert_not_called()


def test_redirect_does_not_forward_credentials(audio,monkeypatch):
    _,post=response(monkeypatch,status=302)
    with pytest.raises(gnani.GnaniError):gnani.transcribe(audio,'hi-IN','prisma-v2.5')
    assert post.call_args.kwargs['allow_redirects'] is False
    post.assert_called_once()


@pytest.mark.parametrize('model,expected',[('prisma-v2.5',{'language_code':'hi-IN','format':'verbatim'}),('prisma-v3.0',{'language_code':'hi-IN','format':'verbatim','model':'prisma-v3.0'})])
def test_model_selection_matches_current_official_rest_docs(audio,monkeypatch,model,expected):
    _,post=response(monkeypatch)
    result=gnani.transcribe(audio,'hi-IN',model)
    assert post.call_args.kwargs['data']==expected
    assert result['request_parameters']==expected
    assert result['http_status']==200
    assert result['requested_model']==model
