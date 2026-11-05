"""Local SQLite run history. Stores transcripts and local audio. Do not use with real personal records."""
from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(os.getenv("SHORLAB_DATA_DIR", "data")).resolve()
AUDIO_DIR = ROOT / "audio"
DB = ROOT / "runs.sqlite3"

def init():
    ROOT.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL)")

def save(record: dict, waveforms: dict[str, bytes]):
    init()
    run_dir = AUDIO_DIR / record["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, data in waveforms.items():
        (run_dir / f"{name}.wav").write_bytes(data)
    with sqlite3.connect(DB) as db:
        db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?)", (record["id"], record["created_at"], record["title"], record["status"], json.dumps(record, ensure_ascii=False)))

def get(run_id: str):
    init()
    with sqlite3.connect(DB) as db:
        row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
    return json.loads(row[0]) if row else None

def list_runs(limit=40):
    init()
    with sqlite3.connect(DB) as db:
        rows = db.execute("SELECT payload FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(x[0]) for x in rows]

def audio_path(run_id: str, variant: str):
    if variant not in {"clean", "degraded", "recovered"}:
        return None
    rec = get(run_id)
    if not rec: return None
    path = AUDIO_DIR / run_id / f"{variant}.wav"
    return path if path.exists() else None
