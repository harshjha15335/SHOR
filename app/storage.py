"""Local SQLite evidence storage with bounded retention and safe artifact paths."""
from __future__ import annotations
import json
import os
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(os.getenv('SHOR_DATA_DIR', os.getenv('SHORLAB_DATA_DIR', 'data'))).resolve()
AUDIO_DIR = ROOT / 'audio'
DB = ROOT / 'runs.sqlite3'
VARIANTS = {'clean', 'degraded', 'recovered'}

def valid_id(run_id):
    try:
        return str(UUID(run_id)) == run_id
    except (ValueError, TypeError, AttributeError):
        return False

def init():
    ROOT.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL)')

def delete(run_id: str):
    if not valid_id(run_id):
        return False
    init()
    with sqlite3.connect(DB) as db:
        existed = db.execute('DELETE FROM runs WHERE id=?', (run_id,)).rowcount > 0
    target = AUDIO_DIR / run_id
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    return existed

def prune():
    """Expire records on storage access; never follows artifact symlinks."""
    init()
    hours = max(1, int(os.getenv('SHOR_RETENTION_HOURS', '168')))
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with sqlite3.connect(DB) as db:
        expired = [r[0] for r in db.execute('SELECT id FROM runs WHERE created_at < ?', (cutoff,))]
    for run_id in expired:
        delete(run_id)
    return len(expired)

def ensure_capacity():
    prune()
    max_runs = max(1, int(os.getenv('SHOR_MAX_RUNS', '500')))
    with sqlite3.connect(DB) as db:
        if db.execute('SELECT count(*) FROM runs').fetchone()[0] >= max_runs:
            raise ValueError('Storage capacity reached; delete old runs before retrying')
    # Check writable filesystem before credit-consuming requests.
    import tempfile
    with tempfile.TemporaryFile(dir=ROOT):
        pass


def save(record: dict, waveforms: dict[str, bytes]):
    if not valid_id(record['id']) or not set(waveforms) <= VARIANTS:
        raise ValueError('Invalid artifact identity')
    ensure_capacity()
    run_dir = AUDIO_DIR / record['id']
    run_dir.mkdir(exist_ok=False)
    try:
        for name, data in waveforms.items():
            (run_dir / f'{name}.wav').write_bytes(data)
        with sqlite3.connect(DB) as db:
            db.execute('INSERT INTO runs VALUES (?, ?, ?, ?, ?)', (record['id'],record['created_at'],record['title'],record['status'],json.dumps(record, ensure_ascii=False,allow_nan=False)))
    except Exception:
        shutil.rmtree(run_dir)
        raise

def get(run_id: str):
    if not valid_id(run_id):
        return None
    prune()
    with sqlite3.connect(DB) as db:
        row = db.execute('SELECT payload FROM runs WHERE id=?', (run_id,)).fetchone()
    return json.loads(row[0]) if row else None

def list_runs(limit=5000):
    prune()
    with sqlite3.connect(DB) as db:
        rows = db.execute('SELECT payload FROM runs ORDER BY created_at DESC LIMIT ?', (max(1,min(limit,5000)),)).fetchall()
    return [json.loads(x[0]) for x in rows]

def audio_path(run_id: str, variant: str):
    if variant not in VARIANTS or not valid_id(run_id) or not get(run_id):
        return None
    path = AUDIO_DIR / run_id / f'{variant}.wav'
    if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
        return None
    return path
