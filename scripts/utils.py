from __future__ import annotations

import datetime as _dt

def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string with 'Z'."""
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def normalize_ws(s: str) -> str:
    return " ".join((s or "").split())
