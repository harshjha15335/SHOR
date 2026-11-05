"""Observed health is distinct from configured credentials; no external calls."""
from fastapi.testclient import TestClient
from app import main,gnani

def test_health_does_not_claim_authentication_for_key_presence(monkeypatch):
 monkeypatch.setenv('GNANI_API_KEY','test-key-not-real')
 monkeypatch.setattr(gnani,'_state',{'network_reachable':None,'authentication_validated':False,'validated_models':[],'last_successful_request_at':None,'last_connection_error':None})
 r=TestClient(main.app).get('/api/health')
 assert r.status_code==200
 d=r.json();assert d['gnani_key_configured'] is True
 assert d['live_inference_available'] is False
 assert d['gnani']['network_reachable'] is None
 assert 'test-key-not-real' not in r.text

def test_health_prior_success_does_not_hide_latest_connection_error(monkeypatch):
 monkeypatch.setenv('GNANI_API_KEY','test-key-not-real')
 monkeypatch.setattr(gnani,'_state',{'network_reachable':False,'authentication_validated':True,'validated_models':['prisma-v2.5'],'last_successful_request_at':'2026-11-05T00:00:00+00:00','last_connection_error':{'code':'connection_error'}})
 d=TestClient(main.app).get('/api/health').json()
 assert d['live_inference_available'] is False
 assert d['gnani']['last_successful_request_at'] is not None
