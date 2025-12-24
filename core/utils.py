from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path


def stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8", errors="ignore"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    # Avoid reading huge files accidentally.
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="ignore")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
