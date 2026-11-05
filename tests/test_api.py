import io
import os
import pytest
from fastapi.testclient import TestClient
from app.audio import encode_wav
from app.main import app
import numpy as np

client=TestClient(app)

@pytest.fixture
def audio():
    t = np.arange(16000)/16000
    return encode_wav((.2*np.sin(2*np.pi*280*t)).astype(np.float32))

def test_health():
    r=client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['ok']

def test_preview_does_not_fabricate_transcripts(tmp_path,monkeypatch,audio):
    import app.storage as storage
    monkeypatch.setattr(storage,'ROOT',tmp_path)
    monkeypatch.setattr(storage,'AUDIO_DIR',tmp_path/'audio')
    monkeypatch.setattr(storage,'DB',tmp_path/'test.sqlite3')
    r=client.post('/api/evaluate',files={'audio_file':('sample.wav',audio,'audio/wav')},
                  data={'mode':'preview','reference':'hello world','title':'test-preview','language':'hi-IN','profile':'traffic_synthetic'})
    assert r.status_code==200,r.text
    data=r.json()
    assert data['status']=='preview'
    assert data['results']['clean']['transcript'] is None
    assert data['results']['degraded']['metrics'] is None
    assert data['provenance']['inference']=='No inference executed'
    assert client.get('/api/runs/'+data['id']+'/audio/degraded').status_code==200
    assert client.get('/api/export.csv').status_code==200
    history = client.get('/api/runs')
    assert history.status_code == 200
    assert history.json()[0]['id'] == data['id']
    assert history.json()[0]['degraded_wer'] is None

def test_live_requires_key(monkeypatch,audio):
    monkeypatch.delenv('GNANI_API_KEY',raising=False)
    r=client.post('/api/evaluate',files={'audio_file':('sample.wav',audio,'audio/wav')},data={'mode':'live'})
    assert r.status_code == 503

def test_rejects_invalid_snr(audio):
    r=client.post('/api/evaluate',files={'audio_file':('sample.wav',audio,'audio/wav')},data={'mode':'preview','snr_db':'300'})
    assert r.status_code==400

def test_live_records_actual_adapter_provenance_without_fabricating(monkeypatch,tmp_path,audio):
    import app.main as main
    import app.storage as storage
    monkeypatch.setattr(storage,'ROOT',tmp_path)
    monkeypatch.setattr(storage,'AUDIO_DIR',tmp_path/'audio')
    monkeypatch.setattr(storage,'DB',tmp_path/'test.sqlite3')
    monkeypatch.setattr(main,'configured',lambda:True)
    called=[]
    def fake_transcribe(raw,language,model):
        called.append((len(raw),language,model))
        return {'status':'real','transcript':'hello world','request_id':'test-only-id','api_model':model,
                'detected_language':'en-IN','wall_time_seconds':0.1,'provider_latency_seconds':None}
    monkeypatch.setattr(main,'transcribe',fake_transcribe)
    r=client.post('/api/evaluate',files={'audio_file':('sample.wav',audio,'audio/wav')},
                  data={'mode':'live','reference':'hello world','model':'prisma-v2.5','language':'en-IN','profile':'broadband'})
    assert r.status_code==200,r.text
    assert len(called)==3
    assert r.json()['status']=='complete'
    assert r.json()['results']['clean']['metrics']['wer']==0.0
    # The test double must never be confused with production Gnani evidence.
    assert r.json()['results']['clean']['request_id']=='test-only-id'


def test_truncated_audio_is_rejected(audio):
    response = client.post('/api/evaluate',
        files={'audio_file': ('truncated.wav', audio[:-100], 'audio/wav')},
        data={'mode': 'preview'})
    assert response.status_code == 400
    assert 'Truncated WAV' in response.json()['detail']
