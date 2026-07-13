"""
Production-hardening invariants: SSRF guards, source tiering, audit-trail
governance, and data lifecycle. Each encodes a control from
docs/PRODUCTION_READINESS.md so it cannot silently regress.
"""
import socket

import pytest

from llm.search_client import _is_safe_url, _confidence_cap, _validate


# ── SSRF guard ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "http://example.com/report",              # not https
    "https://127.0.0.1/latest",                # loopback
    "https://10.0.0.8/internal",               # private
    "https://192.168.1.1/router",              # private
    "https://169.254.169.254/metadata",        # cloud metadata endpoint
    "https://user:pass@example.com/",          # credentials in URL
    "ftp://example.com/file",                  # wrong scheme
    "https://",                                # no host
])
def test_unsafe_urls_are_blocked(url):
    assert _is_safe_url(url) is False


def test_public_https_urls_pass(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo",
                        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))])
    assert _is_safe_url("https://www.irdai.gov.in/annual-report") is True


def test_dns_to_private_address_is_blocked(monkeypatch):
    """A hostile domain resolving to an internal IP must be rejected."""
    monkeypatch.setattr(socket, "getaddrinfo",
                        lambda *a, **k: [(2, 1, 6, "", ("10.1.2.3", 443))])
    assert _is_safe_url("https://innocent-looking.example.com/") is False


# ── Source tiering (prompt-injection / SEO-spam defence) ─────────────────────

def test_high_confidence_requires_primary_source():
    assert _confidence_cap("https://www.irdai.gov.in/report.pdf") == "High"
    assert _confidence_cap("https://www.amfiindia.com/data") == "High"
    assert _confidence_cap("https://some-finance-blog.example.com/post") == "Med"


def test_validate_downgrades_model_asserted_confidence():
    data = {"S1_AUM": {"value": "52.3", "source_url": "https://random-blog.example.com",
                       "quote": "AUM of $52.3B", "confidence": "High"}}
    out = _validate(data)
    assert out["S1_AUM"]["confidence"] == "Med", \
        "confidence must be earned by the source domain, not asserted by the model"


# ── Audit trail governance & data lifecycle ──────────────────────────────────

@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    import storage.audit as audit
    monkeypatch.setattr(audit, "DB_PATH", tmp_path / "audit_test.db")
    audit.init_db()
    return audit


def test_every_run_carries_the_assumptions_hash(isolated_db):
    audit = isolated_db
    rid = audit.log_run("Test Firm", {"S1_AUM": 50}, [{"id": "lever_1"}], {}, "test")
    import sqlite3
    with sqlite3.connect(audit.DB_PATH) as conn:
        row = conn.execute(
            "SELECT assumptions_hash, engine_version FROM runs WHERE run_id=?",
            (rid,)).fetchone()
    assert row[0] == audit.assumptions_hash(), \
        "a logged run must be traceable to the exact assumption set"
    assert row[1] == audit.ENGINE_VERSION


def test_assumptions_hash_moves_when_constants_move(isolated_db, monkeypatch):
    audit = isolated_db
    before = audit.assumptions_hash()
    from config import value_pools
    monkeypatch.setitem(value_pools.CONSTANTS, "Base_Haircut_Pct", 61)
    assert audit.assumptions_hash() != before


def test_right_to_erasure_and_retention(isolated_db):
    audit = isolated_db
    rid = audit.log_run("Erase Me Ltd", {}, [], {}, "test")
    audit.log_run("Keep Me Ltd", {}, [], {}, "test")

    assert audit.delete_run(rid) is True
    assert audit.delete_run(rid) is False          # idempotent, honest return

    assert audit.delete_company_runs("Keep Me Ltd") == 1
    audit.log_run("Old Corp", {}, [], {}, "test")
    assert audit.purge_runs_older_than(0) >= 1     # everything is "older than now"
