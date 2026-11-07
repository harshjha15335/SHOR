"""Allowlisted error metadata for PRIVATE CLI evidence, never public API output."""
import re
from collections.abc import Mapping

MAX_BODY = 32_768
KNOWN_CODES = {'INVALID_API_KEY','SCOPE_NOT_ALLOWED','RATE_LIMITED','INSUFFICIENT_CREDIT','INSUFFICIENT_CREDITS','INVALID_REQUEST','INVALID_AUDIO','MODEL_NOT_AVAILABLE','MODEL_NOT_FOUND','INTERNAL_SERVER_ERROR','UNAUTHORIZED','FORBIDDEN'}
HEADERS = {'content-type','x-proxy-error','x-request-id','x-correlation-id','request-id','traceparent','x-amzn-trace-id','cf-ray'}


def safe_marker(value, credential):
    """Keep bounded identifiers/categories; reject secrets, free text and control chars."""
    if not isinstance(value,str) or len(value)>192 or not value:
        return '[REDACTED]'
    if credential and credential in value:
        return '[REDACTED]'
    if not re.fullmatch(r'[A-Za-z0-9_.:;=/+\-]+',value) or re.search(r'(?i)bearer|api[_-]?key|token|secret|authorization',value):
        return '[REDACTED]'
    return value


def capture_error(response, credential):
    """No raw messages/transcripts/cookies/authorization. No additional requests."""
    result={'http_status':response.status_code,'headers':{},'body':{'capture':'omitted'},'origin':'unverified'}
    headers=getattr(response,'headers',None)
    if isinstance(headers,Mapping):
        for name,value in headers.items():
            if isinstance(name,str) and name.lower() in HEADERS:
                if name.lower() == 'content-type' and isinstance(value,str):
                    value=value.replace(' ','')
                result['headers'][name.lower()]=safe_marker(value,credential)
    content=getattr(response,'content',None)
    if not isinstance(content,bytes):
        result['body']={'capture':'unavailable'}
        return result
    if len(content)>MAX_BODY:
        result['body']={'capture':'omitted_size_limit'}
        return result
    try:
        payload=response.json()
    except (ValueError,TypeError):
        result['body']={'capture':'non_json_redacted'}
        return result
    if not isinstance(payload,dict):
        result['body']={'capture':'non_object_json_redacted'}
        return result
    # Preserve the known provider error code's structural location, never free text.
    cleaned={}
    for name in ('error_code','code'):
        value=payload.get(name)
        if isinstance(value,str) and value in KNOWN_CODES and not (credential and credential in value):
            cleaned[name]=value
    detail=payload.get('detail')
    if isinstance(detail,dict):
        d={}
        for name in ('error_code','code'):
            value=detail.get(name)
            if isinstance(value,str) and value in KNOWN_CODES and not (credential and credential in value):
                d[name]=value
        if d:cleaned['detail']=d
    result['body']={'capture':'allowlisted_json_fields_only','sanitized':cleaned,'other_fields':'redacted'}
    return result
