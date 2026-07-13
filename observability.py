"""
observability.py — structured logging and optional error tracking.

Every log line is one JSON object so any log aggregator can index it.
Sentry activates only when SENTRY_DSN is set; the dependency is optional
so production can enable it without code change and dev runs without it.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": round(time.time(), 3),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("run_id", "company", "event", "duration_s", "provider"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_observability() -> None:
    """Idempotent: safe to call on every Streamlit rerun."""
    root = logging.getLogger("horizon")
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        root.addHandler(handler)
        root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        root.propagate = False

    dsn = os.environ.get("SENTRY_DSN")
    if dsn and not getattr(setup_observability, "_sentry_done", False):
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=dsn, traces_sample_rate=0.0,
                            send_default_pii=False)
            setup_observability._sentry_done = True
            root.info("sentry initialised")
        except ImportError:
            root.warning("SENTRY_DSN set but sentry-sdk not installed")


def get_logger(name: str = "horizon") -> logging.Logger:
    return logging.getLogger(name)
