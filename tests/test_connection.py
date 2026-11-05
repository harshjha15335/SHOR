"""Connection guidance never calls the provider or discloses credentials."""
import json
from fastapi.testclient import TestClient
import pytest
from app import connection,gnani,main

@pytest.fixture(autouse=True)
def isolated(monkeypatch,tmp_path):
 monkeypatch.delenv('GNANI_API_KEY',raising=False)
 monkeypatch.delenv('SHOR_ACCESS_PASSWORD',raising=False)
 monkeypatch.delenv('SHOR_PUBLIC_MODE',raising=False)
 monkeypatch.setattr(gnani,'_state',{'network_reachable':None,'authentication_validated':False,'validated_models':[],'last_successful_request_at':None,'last_connection_error':None})
 monkeypatch.setattr(connection,'POLICY_PATH',tmp_path/'policy.json')
 monkeypatch.setattr(gnani.requests,'post',lambda *a,**k:pytest.fail('Status recheck must not call Gnani'))

@pytest.mark.parametrize('policy,expected',[
 ({'version':1,'http_network_policy':{'type':'restricted','egress_rules':[]}},False),
 ({'version':1,'http_network_policy':{'type':'restricted','egress_rules':[{'host':'api.vachana.ai'}]}},True),
 ({'version':1,'http_network_policy':{'type':'restricted','egress_rules':[{'host':'*.vachana.ai'}]}},True),
 ({'version':1,'http_network_policy':{'type':'unrestricted'}},True),
 ({'version':1,'http_network_policy':{'type':'disabled'}},False),
 ({'version':2},None),({},None),
])
def test_policy_snapshot(policy,expected):
 connection.POLICY_PATH.write_text(json.dumps(policy))
 assert connection.network_policy_status() is expected

def test_missing_policy_is_unknown():
 assert connection.network_policy_status() is None

def test_invalid_policy_is_unknown():
 connection.POLICY_PATH.write_text('not JSON')
 assert connection.network_policy_status() is None

def test_saved_secret_not_falsely_called_invalid():
 d=TestClient(main.app).get('/api/connection').json()
 assert d['status']=='credential_unavailable'
 assert d['can_attempt_live'] is False
 assert 'does not mean your key is invalid' in d['explanation']
 assert d['provider_requests_made']==0

def test_runtime_changes_are_observed_on_recheck(monkeypatch):
 client=TestClient(main.app)
 assert client.get('/api/connection').json()['key_present'] is False
 monkeypatch.setenv('GNANI_API_KEY','TEST-SECRET-NOT-REAL')
 r=client.get('/api/connection');d=r.json()
 assert d['key_present'] is True and d['status']=='unverified'
 assert d['can_attempt_live'] is True
 assert d['gnani']['authentication_validated'] is False
 assert 'TEST-SECRET-NOT-REAL' not in r.text

def test_network_snapshot_denial_has_specific_guidance(monkeypatch):
 monkeypatch.setenv('GNANI_API_KEY','test-only')
 connection.POLICY_PATH.write_text(json.dumps({'version':1,'http_network_policy':{'type':'restricted','egress_rules':[]}}))
 d=connection.snapshot()
 assert d['policy_allows_endpoint'] is False
 assert 'api.vachana.ai' in d['actions'][0]
 assert 'snapshot' in d['actions'][0]

def test_previous_success_does_not_hide_latest_failure(monkeypatch):
 monkeypatch.setenv('GNANI_API_KEY','test-only')
 gnani._state.update(authentication_validated=True,last_connection_error={'code':'credits'})
 assert connection.snapshot()['status']=='credits'

def test_real_success_is_only_observed_state(monkeypatch):
 monkeypatch.setenv('GNANI_API_KEY','test-only')
 gnani._state.update(authentication_validated=True,validated_models=['prisma-v2.5'])
 assert connection.snapshot()['status']=='validated'

def test_connection_details_require_demo_auth(monkeypatch):
 monkeypatch.setenv('SHOR_ACCESS_PASSWORD','test-only')
 client=TestClient(main.app)
 assert client.get('/api/connection').status_code==401
 assert client.get('/api/connection',auth=('shor','test-only')).status_code==200
