"""
llm/search_client.py  —  Enterprise prefill retrieval (v6 rebuild).

WHY THE OLD ONE RETURNED "NOT FOUND" FOR EVERYTHING
----------------------------------------------------
1. `duckduckgo_search` is deprecated and its backends now return 403
   rate-limits on the first call. The exception was swallowed and the
   function returned {} — so the app literally never searched.
2. One keyword-soup query ("assets AUM architecture ERP claims") was fired
   for all fields at once; even when it worked, 5 two-line snippets never
   contain an AUM figure, let alone a data-architecture description.
3. The prompt told the model to FABRICATE "plausible" values when data was
   missing. Invented numbers wearing provenance chips destroy trust.

THE REBUILD — three honest tiers, per-field queries, no fabrication
-------------------------------------------------------------------
Tier 1  Gemini + Google Search grounding (the sanctioned way to search
        Google; you already hold the key). Grounding cannot be combined
        with structured output in ONE call, so we use the correct two-step
        pattern: grounded research call → structured extraction call.
Tier 2  ddgs (the maintained successor of duckduckgo_search) with
        per-field targeted queries, as fallback when no Gemini key.
Tier 3  Direct fetch of trusted publisher pages the search surfaced
        (company IR pages, IRDAI/AMFI disclosures, annual-report PDF
        landing pages) — fetching a publisher's own site is legitimate,
        unlike scraping Google's results pages (ToS violation; avoided).

SCOPE HONESTY
-------------
Only genuinely PUBLIC facts are attempted (AUM/GWP, claims volume, policy
applications, official name). Internal facts (data architecture, ERP age)
are only reported if an actual public signal is found (tech case study,
vendor press release, engineering blog); otherwise the field is returned
as NOT FOUND with the searches we ran listed — never estimated.

Returns:
{
  "company_name": str,
  "<FIELD>": {value, source_url, quote, confidence, method},
  "_search_log": {queries_run, sources_seen, fields_found, fields_missing,
                  backend, duration_s}
}
"""
from __future__ import annotations
import ipaddress
import os
import json
import socket
import time
import re
from urllib.parse import urlparse

from observability import get_logger

_log = get_logger("horizon.prefill")

# Gemini call ceiling per prefill run and hard timeout per call: retrieval
# must never hang the wizard or run up an unbounded bill.
LLM_TIMEOUT_MS = 45_000
CACHE_TTL_S = 24 * 3600   # a firm's public facts don't change intra-day

# ── Field definitions: what is genuinely findable, and how to ask for it ────
# Each field gets its OWN targeted query set. This is the single biggest fix.
FIELD_SPECS = {
    "S1_AUM": {
        "label": "Total AUM / Gross Written Premium ($B)",
        "queries": [
            '{company} assets under management crore OR billion site:*.com annual report',
            '{company} AUM latest',
            '{company} gross written premium annual',
        ],
        "kind": "public",   # exists in filings/press — should usually be found
        "hint": "AUM or GWP in Billions USD as a number string, e.g. \"52.3\". "
                "Convert INR crore to USD billions at ~83 INR/USD (1 lakh crore ≈ $12B).",
    },
    "S3_ANNUAL_CLAIMS": {
        "label": "Annual insurance claims processed",
        "queries": [
            '{company} claims settled number annual report',
            '{company} claim settlement ratio IRDAI number of claims',
        ],
        "kind": "public",
        "hint": "Count of claims settled/processed per year, as a number string.",
    },
    "S2_ANNUAL_UNDERWRITING_APPS": {
        "label": "Annual policy applications",
        "queries": [
            '{company} number of policies issued annual report',
            '{company} new business policies sold',
        ],
        "kind": "public",
        "hint": "New policies issued/applications received per year, number string.",
    },
    "S1_ARCH": {
        "label": "Core data platform architecture",
        "queries": [
            '{company} cloud migration AWS OR Azure OR GCP case study',
            '{company} data platform modernization press release',
        ],
        "kind": "signal",   # internal fact — only report if a real signal exists
        "hint": "ONLY if a source explicitly describes their stack, output one of: "
                "\"Siloed On-Premises (Batch)\", \"Hybrid — partial cloud\", "
                "\"Cloud-Native (AWS/Azure/GCP)\". If no explicit signal, omit.",
    },
    "S1_ERP": {
        "label": "Core policy-admin / ERP status",
        "queries": [
            '{company} policy administration system Guidewire OR "Duck Creek" OR mainframe',
            '{company} core system modernization vendor',
        ],
        "kind": "signal",
        "hint": "ONLY if a source names their core system or its age, output one of: "
                "\"Legacy monolith (>10 years old)\", \"On-prem with API layer\", "
                "\"Modern cloud-native\". If no explicit signal, omit.",
    },
}

_CACHE: dict[str, tuple[float, dict]] = {}   # company -> (fetched_at, result)

# Source tiering: numeric facts only earn High confidence from primary
# sources (regulators, exchanges, the company's own filings). Everything
# else is capped at Med so the reviewer's attention lands where it should.
TIER_A_SUFFIXES = (".gov.in", ".sebi.gov.in", ".irdai.gov.in", ".rbi.org.in",
                   ".amfiindia.com", ".bseindia.com", ".nseindia.com", ".sec.gov")


def _is_safe_url(url: str) -> bool:
    """SSRF guard for outbound page fetches: https only, no credentials in
    the URL, no private/loopback/link-local/metadata destinations. Resolves
    the hostname so DNS-based dodges (private A records) are caught too."""
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username:
            return False
        host = parsed.hostname
        try:
            infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            return False
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                return False
        return True
    except Exception:
        return False


def _confidence_cap(source_url: str) -> str:
    """High only for tier-A primary sources; everything else caps at Med."""
    host = (urlparse(source_url).hostname or "").lower()
    if any(host == s.lstrip(".") or host.endswith(s) for s in TIER_A_SUFFIXES):
        return "High"
    return "Med"


# ═════════════════════════════════════════════════════════════════════════════
# Public entry point
# ═════════════════════════════════════════════════════════════════════════════

def extract_company_data(company_name: str) -> dict:
    company_name = (company_name or "").strip()
    if not company_name:
        return {}
    cached = _CACHE.get(company_name)
    if cached and (time.time() - cached[0]) < CACHE_TTL_S:
        return cached[1]

    t0 = time.time()
    log = {"queries_run": [], "sources_seen": [], "fields_found": [],
           "fields_missing": [], "backend": None, "duration_s": 0.0}

    api_key = _gemini_key()
    result: dict = {}

    if api_key:
        log["backend"] = "gemini-google-grounding"
        research_notes = _tier1_grounded_research(company_name, api_key, log)
        if research_notes:
            result = _structured_extract(company_name, research_notes, api_key, log)
        if not result:
            # Tier 2 fallback: per-field ddgs queries -> structured extraction
            snippets = _tier2_ddgs_research(company_name, log)
            if snippets:
                result = _structured_extract(company_name, snippets, api_key, log)
    else:
        # No key -> extraction is impossible; do NOT waste the user's time on
        # searches whose results can never be parsed. UI stays fully manual.
        log["backend"] = "no retrieval (GEMINI_API_KEY missing)"

    # Finalise the log
    for fid in FIELD_SPECS:
        (log["fields_found"] if fid in result else log["fields_missing"]).append(fid)
    log["duration_s"] = round(time.time() - t0, 1)
    if result or log["queries_run"]:
        result["_search_log"] = log

    _log.info("prefill complete", extra={"company": company_name, "event": "prefill",
                                         "duration_s": log["duration_s"]})
    _CACHE[company_name] = (time.time(), result)
    return result


# ═════════════════════════════════════════════════════════════════════════════
# Tier 1 — Gemini with Google Search grounding (two-step pattern)
# ═════════════════════════════════════════════════════════════════════════════

def _tier1_grounded_research(company: str, api_key: str, log: dict) -> str:
    """One grounded call that RUNS the per-field searches and returns cited
    research notes as text. (Grounding + JSON schema can't share a call, so
    extraction happens in a second, ungrounded call.)"""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key,
                              http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS))

        field_briefs = "\n".join(
            f"- {fid} ({spec['label']}): try searches like " +
            "; ".join(q.format(company=company) for q in spec["queries"][:2])
            for fid, spec in FIELD_SPECS.items()
        )
        prompt = f"""You are a research analyst. Using Google Search, gather facts about
the financial-services firm "{company}". Prioritise Tier-A sources: annual
reports, IRDAI/AMFI/SEBI disclosures, SEC filings, the company's own
investor-relations pages; then investor presentations; then reputable press.

Facts needed (search separately per fact):
{field_briefs}

For EVERY fact you find, write one line:
FIELD_ID | value | source URL | short verbatim quote

STRICT RULES:
- Report ONLY what a source states. If you cannot find a fact, write
  "FIELD_ID | NOT FOUND" — do NOT estimate, infer, or use prior knowledge.
- Also output: COMPANY_NAME | <official spelled name> | <source> | <quote>.
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.0,
            ),
        )
        text = resp.text or ""
        log["queries_run"].append("grounded-research (per-field briefs)")
        log["sources_seen"] += re.findall(r"https?://[^\s|\)\]]+", text)[:12]
        return text
    except Exception as e:
        log["queries_run"].append(f"grounded-research FAILED: {type(e).__name__}")
        return ""


# ═════════════════════════════════════════════════════════════════════════════
# Tier 2 — ddgs fallback (maintained fork), per-field queries + direct fetch
# ═════════════════════════════════════════════════════════════════════════════

_TRUSTED_HOSTS = ("irdai.gov.in", "amfiindia.com", "sebi.gov.in", "bseindia.com",
                  "nseindia.com", "sec.gov")

def _tier2_ddgs_research(company: str, log: dict) -> str:
    notes = []
    try:
        try:
            from ddgs import DDGS          # maintained successor
        except ImportError:
            from duckduckgo_search import DDGS   # legacy fallback
        with DDGS() as ddgs:
            for fid, spec in FIELD_SPECS.items():
                q = spec["queries"][0].format(company=company)
                log["queries_run"].append(q)
                try:
                    hits = list(ddgs.text(q, max_results=3)) or []
                except Exception as e:
                    log["queries_run"].append(f"  -> failed: {type(e).__name__}")
                    continue
                for h in hits:
                    url, body = h.get("href", ""), h.get("body", "")
                    log["sources_seen"].append(url)
                    notes.append(f"[{fid}] {url}\n{body}")
                    # Tier 3: pull full text from trusted publisher pages
                    if any(t in url for t in _TRUSTED_HOSTS) or "investor" in url:
                        page = _fetch_page(url)
                        if page:
                            notes.append(f"[{fid} FULLTEXT] {url}\n{page[:3000]}")
                time.sleep(0.4)   # be polite; avoids backend rate-limits
    except Exception as e:
        log["queries_run"].append(f"ddgs unavailable: {type(e).__name__}")
    return "\n\n".join(notes)


def _fetch_page(url: str) -> str:
    """Direct fetch of a trusted publisher page (NOT a search-engine SERP).
    SSRF-guarded: https-only, public destinations only, bounded size."""
    if not _is_safe_url(url):
        _log.warning("blocked unsafe fetch", extra={"event": "ssrf_block"})
        return ""
    try:
        import requests
        r = requests.get(url, timeout=8, allow_redirects=False,
                         headers={"User-Agent": "Mozilla/5.0 (research)"}, stream=True)
        if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
            return ""
        raw = r.raw.read(512_000, decode_content=True).decode("utf-8", "ignore")
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


# ═════════════════════════════════════════════════════════════════════════════
# Structured extraction (second step — no tools, JSON schema enforced)
# ═════════════════════════════════════════════════════════════════════════════

def _structured_extract(company: str, research: str, api_key: str, log: dict) -> dict:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key,
                              http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS))

        prov = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "value": types.Schema(type=types.Type.STRING),
                "source_url": types.Schema(type=types.Type.STRING),
                "quote": types.Schema(type=types.Type.STRING),
                "confidence": types.Schema(type=types.Type.STRING, enum=["High", "Med", "Low"]),
            },
            required=["value", "source_url", "quote", "confidence"],
        )
        schema = types.Schema(
            type=types.Type.OBJECT,
            properties={"company_name": types.Schema(type=types.Type.STRING),
                        **{fid: prov for fid in FIELD_SPECS}},
            required=["company_name"],
        )
        hints = "\n".join(f"- {fid}: {spec['hint']}" for fid, spec in FIELD_SPECS.items())
        prompt = f"""From the research notes below about "{company}", fill the JSON schema.

Field rules:
{hints}

Confidence rubric:
- High = regulator/exchange filing, annual report, or the company's own IR page.
- Med  = investor presentation or reputable financial press.
- Low  = any other source.

ABSOLUTE RULES:
- A field may ONLY be populated if the notes contain a source URL and quote
  supporting it. If the notes say NOT FOUND (or say nothing) for a field,
  OMIT that field entirely from the JSON. Never estimate or invent.
- Numeric values: plain number strings (e.g. "52.3"), USD billions for AUM.

RESEARCH NOTES:
{research[:24000]}
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        data = json.loads(resp.text)
        data = {k: v for k, v in data.items() if v}
        # Range guards — reject nonsense before it reaches the UI
        data = _validate(data)
        return data
    except Exception as e:
        log["queries_run"].append(f"extraction FAILED: {type(e).__name__}")
        return {}


def _validate(data: dict) -> dict:
    """Numeric sanity guards, plus source tiering: retrieved text is
    untrusted input, so model-asserted confidence is capped by the QUALITY
    OF THE SOURCE DOMAIN, not taken at face value (prompt-injection and
    SEO-spam defence)."""
    ranges = {"S1_AUM": (0.05, 5000.0),
              "S3_ANNUAL_CLAIMS": (100, 50_000_000),
              "S2_ANNUAL_UNDERWRITING_APPS": (100, 50_000_000)}
    for fid, (lo, hi) in ranges.items():
        obj = data.get(fid)
        if isinstance(obj, dict):
            try:
                v = float(str(obj.get("value", "")).replace(",", ""))
                if not (lo <= v <= hi):
                    data.pop(fid, None)
                else:
                    obj["value"] = str(v)
            except ValueError:
                data.pop(fid, None)
    for obj in data.values():
        if isinstance(obj, dict) and "confidence" in obj:
            cap = _confidence_cap(str(obj.get("source_url", "")))
            if obj["confidence"] == "High" and cap != "High":
                obj["confidence"] = "Med"
    return data


def _gemini_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.session_state.get("gemini_api_key")
    except Exception:
        return None
