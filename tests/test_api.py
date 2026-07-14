"""
API contract tests: the service must serve the same numbers as the engine,
validate every input, and enforce auth when configured.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from tests.test_invariants import mf_answers


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import storage.audit as audit
    monkeypatch.setattr(audit, "DB_PATH", tmp_path / "audit_api.db")
    audit.init_db()
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_config_serves_the_single_sources_of_truth(client):
    cfg = client.get("/api/config").json()
    from config.value_pools import GOALS
    from config.questions import QUESTIONS
    assert cfg["goals"] == list(GOALS)
    assert len(cfg["questions"]) == len(QUESTIONS)
    assert set(cfg["ai_stacks"]) == {"Frontier", "Balanced", "Cost-optimized"}


def test_report_matches_the_engine_exactly(client):
    ans = mf_answers()
    r = client.post("/api/report", json={
        "answers": ans, "company_name": "API Test AMC",
        "target_sector": "Mutual Funds / Asset Management",
        "budget_usd_m": 100.0,
    })
    assert r.status_code == 200, r.text
    body = r.json()

    from engine.math_engine import build_investment_plan
    ans2 = dict(ans)
    ans2["target_sector"] = "Mutual Funds / Asset Management"
    plan = build_investment_plan(ans2, 100.0, [], scenario="base", ai_stack="Balanced")
    by_id = {p["id"]: p for p in plan}
    assert len(body["levers"]) == len(plan)
    for lever in body["levers"]:
        assert abs(lever["anv_m"] - by_id[lever["id"]]["anv"] / 1e6) < 0.01

    s = body["summary"]
    assert abs(s["committed_m"] + s["uncommitted_m"] - 100.0) < 0.01
    assert s["confidence_pct"] == 100 - s["exec_risk_pct"]
    assert body["run_id"] and body["assumptions_hash"]
    assert body["diagnostic"]["verdict"]
    assert body["diagnostic"]["rebuild_breakdown"], "cost breakdown must ship"


def test_invalid_inputs_are_rejected(client):
    assert client.post("/api/report", json={"budget_usd_m": -5}).status_code == 422
    assert client.post("/api/report", json={"target_sector": "Nonsense"}).status_code == 422
    assert client.post("/api/report",
                       json={"primary_goals": ["Not A Goal"]}).status_code == 422


def test_bearer_auth_enforced_when_configured(client, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "s3cret")
    assert client.get("/api/config").status_code == 401
    assert client.get("/api/config",
                      headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/api/config",
                      headers={"Authorization": "Bearer s3cret"}).status_code == 200


def test_memo_degrades_honestly_without_key(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = client.post("/api/memo", json={
        "answers": mf_answers(), "company_name": "Memo Test AMC",
        "target_sector": "Mutual Funds / Asset Management",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["generated"] is False, "no key must mean an honest fallback, not silence"
    assert len(body["paragraphs"]) >= 2 and body["grounded_on"]


def test_reports_are_rebuildable_by_url(client):
    """A run id must reconstruct the exact same report from the audit trail."""
    first = client.post("/api/report", json={
        "answers": mf_answers(), "company_name": "Durable Reports AMC",
        "target_sector": "Mutual Funds / Asset Management",
        "budget_usd_m": 80.0, "scenario": "aggressive", "ai_stack": "Frontier",
    }).json()
    rebuilt = client.get(f"/api/runs/{first['run_id']}")
    assert rebuilt.status_code == 200
    body = rebuilt.json()
    assert body["run_id"] == first["run_id"]
    assert body["summary"] == first["summary"], "deterministic rebuild must match"
    assert body["scenario"] == "aggressive" and body["ai_stack"] == "Frontier"
    assert client.get("/api/runs/nonexist1").status_code == 404

    runs = client.get("/api/runs").json()
    assert any(r["run_id"] == first["run_id"] for r in runs)


def test_prefill_degrades_honestly_without_key(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = client.post("/api/prefill", json={"company_name": "No Key Test Ltd"})
    assert r.status_code == 200
    body = r.json()
    assert body["searched"] is False and body["fields"] == {}, \
        "without a key there must be no retrieval and no pretend results"
