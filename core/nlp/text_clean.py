from __future__ import annotations

import re

_RE_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_RE_EMAIL = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", re.IGNORECASE)
_RE_NUM = re.compile(r"\b\d+\b")
_RE_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    # Minimal, fast normalization for offline use.
    t = text.lower()
    t = _RE_URL.sub(" URL ", t)
    t = _RE_EMAIL.sub(" EMAIL ", t)
    t = _RE_NUM.sub(" NUM ", t)
    t = re.sub(r"[^a-z0-9_\s]", " ", t)
    t = _RE_WS.sub(" ", t).strip()
    return t


def sentence_snippet(text: str, max_len: int = 220) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) <= max_len:
        return t
    return t[:max_len].rstrip() + "…"
