"""Safe, non-billable connection guidance from server observations and startup policy."""
from datetime import datetime, timezone
import fnmatch
import json
from pathlib import Path
from . import gnani

POLICY_PATH = Path('/etc/codex/network-policy.json')

def network_policy_status():
    """A startup snapshot is guidance, not a fresh external connectivity test."""
    try:
        data = json.loads(POLICY_PATH.read_text())
        if data.get('version') != 1:
            return None
        policy = data.get('http_network_policy', {})
        mode = policy.get('type')
        if mode == 'unrestricted':
            return True
        if mode == 'disabled':
            return False
        if mode != 'restricted':
            return None
        return any(fnmatch.fnmatchcase('api.vachana.ai', rule.get('host','').lower()) for rule in policy.get('egress_rules',[]) if isinstance(rule,dict))
    except (OSError,ValueError,TypeError,AttributeError):
        return None

def snapshot():
    observed = gnani.status_snapshot()
    policy = network_policy_status()
    error = observed.get('last_connection_error') or {}
    key = observed['key_present']
    if not key:
        code, title = 'credential_unavailable', 'Saved key is not available to this server'
        explanation = 'A key can be saved in HTTP secrets without being attached to the running app. This does not mean your key is invalid.'
        actions = ['In environment settings, attach the saved HTTP secret as GNANI_API_KEY for api.vachana.ai.',
                   'Apply the updated environment configuration and restart or reconnect the app, then select Recheck connection.',
                   'Do not enter your API key in this website or paste it into chat. Audio preview works while live access is unavailable.']
    elif error:
        code, title = error.get('code','provider_error'), 'Last live request did not establish current access'
        explanation = 'A credential is available. Inspect the safe error category below; key presence alone does not prove authentication or available credits.'
        actions = ['For authentication/access_denied, verify the secret binding and model entitlement in your Gnani account.',
                   'For credits/rate_limited, check your account balance or wait before explicitly approving another request.',
                   'For connection_error/timeout, verify api.vachana.ai access. A timeout may have consumed credits; no automatic retry occurs.']
    elif observed.get('live_inference_available'):
        code, title = 'validated', 'A real Gnani request succeeded in this app session'
        explanation = 'Review the validated model and timestamp. This is not a guarantee of current credits or access to other models.'
        actions = ['Use consented speech and approve the request budget for each new experiment.']
    else:
        code, title = 'unverified', 'Credential available — live access not yet verified'
        explanation = 'No successful live request has been observed in this app session. Rechecking status does not test authentication or spend credits.'
        actions = ['Complete the one-request speech smoke test before approving a three-request experiment.',
                   'Use a short consented recording and a reviewed transcript; keep provider request IDs and returned evidence.']
    if policy is False:
        actions.insert(0, 'The server startup policy does not permit api.vachana.ai. Apply the allowed destination in environment settings; the snapshot may require a restart to update.')
    return {'checked_at':datetime.now(timezone.utc).isoformat(), 'status':code,'title':title,'explanation':explanation,
            'actions':actions,'key_present':key,'can_attempt_live':key,'last_error_code':error.get('code'),
            'policy_allows_endpoint':policy,'policy_observation':'server_startup_snapshot_not_a_connectivity_probe',
            'gnani':observed,'provider_requests_made':0,'note':'This endpoint only reads status. It does not retrieve a saved secret value or call Gnani.'}
