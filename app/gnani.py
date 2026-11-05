"""Bounded, server-side Gnani REST adapter; never synthesizes provider evidence.

The diagnostic snapshot is process-local observed state, not an active probe or a
credential-validity guarantee. No automatic retries: each call can consume credits.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import math
import os
from threading import Lock
import time

import requests

ENDPOINT = "https://api.vachana.ai/stt/v3"
MODELS = {"prisma-v2.5", "prisma-v3.0"}
LANGUAGES = {"hi-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "mr-IN", "bn-IN", "gu-IN", "pa-IN", "indic-auto"}
TIMEOUT = (5, 75)  # connect seconds, read-inactivity seconds; not total wall deadline
_lock = Lock()
_state = {"network_reachable": None, "authentication_validated": False,
          "validated_models": [], "last_successful_request_at": None,
          "last_connection_error": None}


class GnaniError(Exception):
    """Safe error details; never include a raw upstream body or exception text."""

    def __init__(self, message: str, code: str = "provider_error", http_status: int | None = None):
        super().__init__(message)
        self.code = code
        self.http_status = http_status


def configured() -> bool:
    return bool(os.environ.get("GNANI_API_KEY", "").strip())


def status_snapshot() -> dict:
    """Return observations since process startup, without requests or secret values."""
    with _lock:
        snapshot = dict(_state)
        snapshot["validated_models"] = list(_state["validated_models"])
        snapshot["last_connection_error"] = dict(_state["last_connection_error"]) if _state["last_connection_error"] else None
    snapshot["key_present"] = configured()
    snapshot["observation_scope"] = "this_process_since_startup"
    snapshot["live_inference_available"] = bool(
        snapshot["key_present"] and snapshot["authentication_validated"]
        and snapshot["last_connection_error"] is None)
    return snapshot


def _failure(message: str, code: str, http_status: int | None = None) -> GnaniError:
    with _lock:
        _state["last_connection_error"] = {
            "code": code, "http_status": http_status,
            "observed_at": datetime.now(timezone.utc).isoformat()}
        if code in {"authentication", "access_denied"}:
            _state["authentication_validated"] = False
            _state["validated_models"] = []
        if code == "connection_error":
            _state["network_reachable"] = False
    return GnaniError(message, code, http_status)


def _optional_string(value, max_length=512):
    return value if isinstance(value, str) and len(value) <= max_length else None


def transcribe(wav_bytes: bytes, language: str, model: str) -> dict:
    api_key = os.environ.get("GNANI_API_KEY", "").strip()
    if not api_key:
        raise GnaniError("Gnani API key is missing. Set GNANI_API_KEY on the server.", "missing_key")
    if model not in MODELS:
        raise GnaniError("Unsupported model", "invalid_model")
    if language not in LANGUAGES:
        raise GnaniError("Unsupported language", "invalid_language")
    if model == "prisma-v2.5" and language == "indic-auto":
        raise GnaniError("indic-auto requires Prisma v3.0", "invalid_language")
    if not isinstance(wav_bytes, bytes) or not 44 <= len(wav_bytes) <= 8_000_000:
        raise GnaniError("Audio must be a nonempty WAV of at most 8 MB", "invalid_audio")
    if wav_bytes[:4] != b"RIFF" or wav_bytes[8:12] != b"WAVE":
        raise GnaniError("Audio must use a WAV container", "invalid_audio")
    params = {"language_code": language, "format": "verbatim"}
    # Official REST docs: omit model for default v2.5; only v3.0 is an explicit option.
    if model == "prisma-v3.0":
        params["model"] = model
    submitted_at = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    response = None
    try:
        response = requests.post(
            ENDPOINT, headers={"X-API-Key-ID": api_key},
            files={"audio_file": ("recording.wav", wav_bytes, "audio/wav")},
            data=params, timeout=TIMEOUT, allow_redirects=False,
        )
        with _lock:
            _state["network_reachable"] = True
        http_status = response.status_code
        if http_status != 200:
            errors = {
                400: ("invalid_request", "Gnani rejected the audio, language or model configuration."),
                401: ("authentication", "Gnani authentication failed; check the server-side key."),
                402: ("credits", "Gnani requires credits or payment; check the account."),
                403: ("access_denied", "Gnani denied access; check credentials, entitlement and network policy."),
                404: ("unsupported_resource", "Gnani endpoint or requested model is unavailable."),
                413: ("invalid_audio", "Gnani rejected the audio size."),
                422: ("invalid_request", "Gnani rejected the audio or request parameters."),
                429: ("rate_limited", "Gnani rate limit reached; no automatic retry was made."),
            }
            code, message = errors.get(http_status, ("provider_unavailable" if http_status >= 500 else "provider_error", "Gnani service request failed."))
            raise _failure(message, code, http_status)
        try:
            data = response.json()
        except ValueError:
            raise _failure("Gnani returned invalid or truncated JSON.", "invalid_response", http_status) from None
        if not isinstance(data, dict):
            raise _failure("Gnani returned an unexpected response structure.", "invalid_response", http_status)
        if data.get("success") is False:
            raise _failure("Gnani reported an unsuccessful transcription.", "provider_error", http_status)
        transcript = data.get("transcript")
        if not isinstance(transcript, str) or len(transcript) > 100_000:
            raise _failure("Gnani returned no valid transcript text.", "invalid_response", http_status)
        received_at = datetime.now(timezone.utc).isoformat()
        elapsed = round(time.perf_counter() - start, 6)
        latency = data.get("end_to_end_latency")
        if not isinstance(latency, (int, float)) or isinstance(latency, bool) or not math.isfinite(latency) or latency < 0:
            latency = None
        with _lock:
            _state["authentication_validated"] = True
            _state["validated_models"] = sorted(set(_state["validated_models"]) | {model})
            _state["last_successful_request_at"] = received_at
            _state["last_connection_error"] = None
        return {"status": "real", "http_status": http_status, "request_parameters": dict(params), "transcript": transcript,
                "request_id": _optional_string(data.get("request_id")),
                "api_model": _optional_string(data.get("model"), 128),
                "requested_model": model, "language": language, "format": "verbatim",
                "detected_language": _optional_string(data.get("detected_language_code"), 128),
                "wall_time_seconds": elapsed, "provider_latency_seconds": latency,
                "request_started_at": submitted_at, "response_received_at": received_at,
                "audio_sha256": hashlib.sha256(wav_bytes).hexdigest()}
    except requests.Timeout:
        # Read timeout does not establish whether the provider processed/billed the call.
        raise _failure("Gnani request timed out; completion and billing are unknown. No automatic retry was made.", "timeout") from None
    except requests.RequestException:
        raise _failure("Unable to reach Gnani STT service; inspect network configuration.", "connection_error") from None
    finally:
        if response is not None:
            response.close()
