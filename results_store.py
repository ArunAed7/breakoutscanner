"""Persist breakout scan results to local CSV."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from config import SCAN_META_JSON, SCAN_RESULTS_CSV, ensure_dirs

_BOOL_COLS = ("is_52w_high", "strong_close")


def save_scan_results(df: pd.DataFrame, meta: dict[str, Any]) -> Path:
    """Write scan results and metadata to data_cache/."""
    ensure_dirs()
    out = df.copy()
    out.to_csv(SCAN_RESULTS_CSV, index=False)
    payload = {
        **meta,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "row_count": len(out),
    }
    SCAN_META_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return SCAN_RESULTS_CSV


def load_scan_results() -> tuple[Optional[pd.DataFrame], dict[str, Any]]:
    """Load cached scan results if present."""
    if not SCAN_RESULTS_CSV.is_file():
        return None, {}

    try:
        df = pd.read_csv(SCAN_RESULTS_CSV)
        for col in _BOOL_COLS:
            if col in df.columns:
                df[col] = df[col].map(_parse_bool)
        if "bar_time" in df.columns:
            df["bar_time"] = pd.to_datetime(df["bar_time"], errors="coerce").dt.date
        meta: dict[str, Any] = {}
        if SCAN_META_JSON.is_file():
            meta = json.loads(SCAN_META_JSON.read_text(encoding="utf-8"))
        return df, meta
    except Exception:
        return None, {}


def cached_scan_available() -> bool:
    return SCAN_RESULTS_CSV.is_file()


def _parse_bool(val: object) -> bool:
    if isinstance(val, bool):
        return val
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    return str(val).strip().lower() in {"1", "true", "yes", "t"}
