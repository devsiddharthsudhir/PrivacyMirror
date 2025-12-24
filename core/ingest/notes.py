from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..types import Document
from ..utils import stable_id, safe_read_text

SUPPORTED = {".txt", ".md"}


def ingest_notes_dir(folder: Path, limit: int = 5000) -> List[Document]:
    docs: List[Document] = []
    files = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED]
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[:limit]:
        txt = safe_read_text(p)
        ts: Optional[datetime] = None
        try:
            ts = datetime.fromtimestamp(p.stat().st_mtime)
        except Exception:
            ts = None
        doc_id = stable_id("notes", str(p), str(p.stat().st_size))
        docs.append(
            Document(
                doc_id=doc_id,
                source="notes",
                text=txt,
                timestamp=ts,
                meta={"path": str(p), "size": p.stat().st_size},
            )
        )
    return docs
