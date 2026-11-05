"""SHOR//LAB FastAPI application: deterministic noise pipeline + actual Gnani API."""
from __future__ import annotations
import csv
import io
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from .audio import create_variants, decode_wav, encode_wav
from .gnani import configured, GnaniError, transcribe
from .metrics import score, compare
from . import storage

load_dotenv()
app = FastAPI(title="shor", version="0.1.0", description="Transparent Indic ASR stress testing with real Gnani inference")
HERE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
LANGS = {"hi-IN","en-IN","ta-IN","te-IN","kn-IN","ml-IN","mr-IN","bn-IN","gu-IN","pa-IN","indic-auto"}
PROFILES = {"none", "broadband", "crowd_synthetic", "traffic_synthetic", "hum_synthetic", "uploaded_ambience"}

@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"ok":True, "gnani_key_configured":configured(), "live_inference_available":configured(),
            "model_options":["prisma-v2.5","prisma-v3.0"], "data_policy":"Local-only, run audio & transcripts stored on the host; use consented/test data."}

@app.get("/api/runs")
def runs():
    records = storage.list_runs()
    return [{"id":r["id"], "title":r["title"], "created_at":r["created_at"], "status":r["status"],
             "model":r["model"], "noise_profile":r["noise_profile"],
             "degraded_wer":(r["results"].get("degraded",{}).get("metrics") or {}).get("wer")} for r in records]

@app.get("/api/runs/{run_id}")
def run(run_id: str):
    rec = storage.get(run_id)
    if not rec: raise HTTPException(404,"Run not found")
    return rec

@app.get("/api/runs/{run_id}/audio/{variant}")
def audio(run_id: str, variant: str):
    p = storage.audio_path(run_id,variant)
    if not p: raise HTTPException(404,"Audio not found")
    return FileResponse(p,media_type="audio/wav",filename=f"shorlab_{variant}.wav")

@app.get("/api/export.csv")
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["run_id","created_at","title","mode","model","language","profile","snr_db","telephony","variant","status","wer_percent","cer_percent","critical_recall_percent","transcript","error"])
    for rec in storage.list_runs(5000):
        for variant, entry in rec["results"].items():
            m = entry.get("metrics") or {}
            writer.writerow([rec["id"], rec["created_at"], rec["title"], rec["mode"], rec["model"],rec["language"],rec["noise_profile"],rec["snr_db"],rec["telephony"],variant,entry["status"],m.get("wer"),m.get("cer"),m.get("critical_recall"),entry.get("transcript"),entry.get("error")])
    return Response(output.getvalue(), media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=shorlab_runs.csv"})

@app.post("/api/evaluate")
async def evaluate(
    audio_file: UploadFile = File(...),
    reference: str = Form(""),
    title: str = Form("Untitled recording"),
    language: str = Form("hi-IN"),
    model: str = Form("prisma-v2.5"),
    profile: str = Form("traffic_synthetic"),
    snr_db: float = Form(8),
    telephony: bool = Form(True),
    seed: int = Form(42),
    critical_terms: str = Form(""),
    mode: str = Form("preview"),
    ambience_file: UploadFile | None = File(None),
):
    if model not in ("prisma-v2.5","prisma-v3.0") or language not in LANGS or profile not in PROFILES:
        raise HTTPException(400,"Invalid model/language/noise profile")
    if model == "prisma-v2.5" and (language == "indic-auto" or "," in language):
        raise HTTPException(400,"Use Prisma v3.0 for auto language detection")
    if not -5 <= snr_db <= 30:
        raise HTTPException(400,"SNR must be between -5 and 30 dB")
    if not 0 <= seed <= 10000000:
        raise HTTPException(400,"Seed must be between 0 and 10,000,000")
    if mode not in {"live","preview"}:
        raise HTTPException(400,"mode must be live or preview")
    if mode == "live" and not configured():
        raise HTTPException(503,"Real inference needs GNANI_API_KEY in .env. Preview does not call Gnani.")
    data = await audio_file.read(8_000_001)
    if len(data) > 8_000_000:
        raise HTTPException(413,"Maximum 8 MB WAV")
    try:
        orig = decode_wav(data)
        ambience = None
        if profile == "uploaded_ambience":
            if ambience_file is None: raise ValueError("Upload a real ambience WAV")
            ambient_bytes = await ambience_file.read(8_000_001)
            if len(ambient_bytes) > 8_000_000: raise ValueError("Ambience WAV exceeds 8 MB")
            ambience = decode_wav(ambient_bytes)
        variants = create_variants(orig,profile,snr_db,telephony,seed,ambience)
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc
    # A run submits three real API calls in live mode; no auto retry, to limit spend.
    wavs = {name: encode_wav(arr) for name,arr in variants.items()}
    results = {}
    terms = [x.strip() for x in critical_terms.split(",") if x.strip()][:30]
    for name, content in wavs.items():
        if mode == "preview":
            results[name] = {"status":"not_run", "transcript":None, "metrics":None,
                             "note":"Local audio preview; no Gnani request, no fabricated accuracy."}
        else:
            try:
                result = transcribe(content,language,model)
                result["metrics"] = score(reference,result["transcript"],terms) if reference.strip() else None
                results[name] = result
            except (GnaniError, ValueError) as exc:
                results[name] = {"status":"error","transcript":None,"metrics":None,"error":str(exc)}
    delta = compare((results.get("degraded") or {}).get("metrics"),(results.get("recovered") or {}).get("metrics"))
    record = {
        "id":str(uuid4()), "created_at":datetime.now(timezone.utc).isoformat(),
        "title":title.strip()[:90] or "Untitled recording", "status":"preview" if mode == "preview" else ("complete" if all(x["status"] == "real" for x in results.values()) else "partial"),
        "mode":mode, "model":model,"language":language, "noise_profile":profile,"snr_db":snr_db,
        "telephony":telephony,"seed":seed,"duration_seconds":round(len(orig)/16000,2),
        "reference":reference[:2500],"critical_terms":terms,"results":results,"comparison":delta,
        "provenance":{"audio":"user-uploaded / locally recorded","noise":"user uploaded recording" if profile == "uploaded_ambience" else ("none" if profile == "none" else "deterministic synthetic audio"),
                      "recovery":"SciPy spectral attenuation, not Gnani model enhancement", "inference":"Gnani Prisma REST endpoint" if mode == "live" else "No inference executed"},
        "caveat":"WER cannot fairly compare transliterated vs native-script references. No external benchmark or production telephony validation implied."
    }
    storage.save(record,wavs)
    return record
