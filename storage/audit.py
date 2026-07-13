"""
storage/audit.py

SQLite-backed run logger. Every report generation writes one reproducible
row: the exact inputs, the exact plan, the engine version, AND a hash of
the assumption set (model-governance requirement — "which constants
produced this number for this client" must be answerable forever).

Also carries the data-lifecycle controls a client engagement requires:
per-run deletion and age-based purging (DPDP/retention). The DB path is
overridable via AUDIT_DB_PATH so production can mount a managed volume.

Usage:
    from storage.audit import init_db, log_run
    init_db()
    rid = log_run(company, inputs, plan, payload, mode)
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
import uuid
from pathlib import Path

from observability import get_logger

_log = get_logger("horizon.audit")

ENGINE_VERSION = "5.1.1"   # bump on any formula change (CI enforces this)
CORPUS_VERSION = "0.1.0-unverified"  # bump when corpus entries are verified

DB_PATH = Path(os.environ.get(
    "AUDIT_DB_PATH",
    Path(__file__).parent.parent / "audit.db"))


def assumptions_hash() -> str:
    """Deterministic fingerprint of the full assumption set (constants,
    lever specs, run costs, stacks). Stored on every run so any historical
    number can be traced to the exact model that produced it."""
    from config import value_pools as vp
    blob = json.dumps(
        {"constants": vp.CONSTANTS, "levers": vp.BFSI_LEVERS,
         "run_costs": vp.RUN_COSTS, "stacks": vp.AI_STACKS,
         "gated": sorted(vp.PLATFORM_GATED_LEVERS)},
        sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")       # concurrent readers
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create the runs table if needed; migrate older schemas in place."""
    with _connect() as conn:
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
        cols = {r[1] for r in conn.execute("PRAGMA table_info(runs)")}
        if "assumptions_hash" not in cols:
            conn.execute("ALTER TABLE runs ADD COLUMN assumptions_hash TEXT")


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
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT INTO runs (run_id, ts, company, engine_version, corpus_version,"
            " model, mode, inputs_json, plan_json, payload_json, assumptions_hash)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
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
                assumptions_hash(),
            ),
        )
    _log.info("run logged", extra={"run_id": rid, "company": company, "event": "run_logged"})
    return rid


# ── Data lifecycle (DPDP / client-contract requirements) ─────────────────────

def delete_run(run_id: str) -> bool:
    """Hard-delete one run (right-to-erasure). Returns True if a row went."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
    deleted = cur.rowcount > 0
    if deleted:
        _log.info("run deleted", extra={"run_id": run_id, "event": "run_deleted"})
    return deleted


def delete_company_runs(company: str) -> int:
    """Hard-delete every run for a client (contract exit / erasure request)."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM runs WHERE company = ?", (company,))
    _log.info("company runs deleted",
              extra={"company": company, "event": "company_deleted"})
    return cur.rowcount


def purge_runs_older_than(days: int) -> int:
    """Retention enforcement: remove runs past the retention window."""
    cutoff = (datetime.datetime.now(datetime.timezone.utc)
              - datetime.timedelta(days=days)).isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute("DELETE FROM runs WHERE ts <= ?", (cutoff,))
    _log.info("retention purge", extra={"event": "retention_purge"})
    return cur.rowcount
