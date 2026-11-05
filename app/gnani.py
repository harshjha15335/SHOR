"""Real Gnani Prisma REST adapter. Never returns synthetic or fabricated transcriptions."""
from __future__ import annotations
import os
import time
import requests

ENDPOINT = "https://api.vachana.ai/stt/v3"

class GnaniError(Exception):
    pass


def configured() -> bool:
    return bool(os.environ.get("GNANI_API_KEY", "").strip())


def transcribe(wav_bytes: bytes, language: str, model: str) -> dict:
    api_key = os.environ.get("GNANI_API_KEY", "").strip()
    if not api_key:
        raise GnaniError("Gnani API key is missing. Set GNANI_API_KEY on the server.")
    if model not in {"prisma-v2.5", "prisma-v3.0"}:
        raise GnaniError("Unsupported model")
    if model == "prisma-v2.5" and language == "indic-auto":
        raise GnaniError("indic-auto requires Prisma v3.0")
    params = {"model": model, "language_code": language, "format": "verbatim"}
    start = time.perf_counter()
    try:
        response = requests.post(
            ENDPOINT, headers={"X-API-Key-ID": api_key},
            files={"audio_file": ("recording.wav", wav_bytes, "audio/wav")},
            data=params, timeout=75,
        )
        elapsed = round(time.perf_counter() - start, 3)
        if response.status_code != 200:
            # Do not surface raw upstream body (may contain private user data).
            raise GnaniError(f"Gnani returned HTTP {response.status_code}. Verify key, credits, model and format.")
        data = response.json()
        if data.get("success") is False:
            raise GnaniError("Gnani reported an unsuccessful transcription")
        transcript = data.get("transcript")
        if not isinstance(transcript, str):
            raise GnaniError("Gnani returned no transcript text")
        return {"status": "real", "transcript": transcript, "request_id": data.get("request_id"),
                "api_model": data.get("model", model), "detected_language": data.get("detected_language_code"),
                "wall_time_seconds": elapsed, "provider_latency_seconds": data.get("end_to_end_latency")}
    except requests.RequestException as exc:
        raise GnaniError("Unable to reach Gnani STT service; check connection and retry") from exc
    except ValueError as exc:
        raise GnaniError("Gnani returned invalid JSON") from exc
