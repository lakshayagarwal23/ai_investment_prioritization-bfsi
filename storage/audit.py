"""
storage/audit.py

SQLite-backed run logger.  Every report generation writes one reproducible row.
The run_id lets anyone replay the exact plan from the stored inputs.

Usage (from app.py):
    from storage.audit import init_db, log_run
    init_db()
    rid = log_run(company, inputs, plan, payload, mode, versions)
"""

from __future__ import annotations

import datetime
import json
import sqlite3
import uuid
from pathlib import Path

ENGINE_VERSION = "4.0.0"   # bump on any formula change
CORPUS_VERSION = "0.1.0-unverified"  # bump when corpus entries are verified

DB_PATH = Path(__file__).parent.parent / "audit.db"


def init_db() -> None:
    """Create the runs table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                run_id        TEXT PRIMARY KEY,
                ts            TEXT,
                company       TEXT,
                engine_version TEXT,
                corpus_version TEXT,
                model         TEXT,
                mode          TEXT,
                inputs_json   TEXT,
                plan_json     TEXT,
                payload_json  TEXT
            )"""
        )


def log_run(
    company: str,
    inputs: dict,
    plan: dict,
    payload: dict,
    mode: str,
    versions: dict | None = None,
) -> str:
    """Write one run row; return the short run_id (first 8 chars of UUID)."""
    versions = versions or {}
    rid = str(uuid.uuid4())[:8]
    ts = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                rid,
                ts,
                company,
                versions.get("engine", ENGINE_VERSION),
                versions.get("corpus", CORPUS_VERSION),
                versions.get("model", "deterministic"),
                mode,
                json.dumps(inputs, default=str),
                json.dumps(plan, default=str),
                json.dumps(payload, default=str),
            ),
        )
    return rid
