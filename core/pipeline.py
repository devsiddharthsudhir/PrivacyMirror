from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .types import Document
from .ingest.email_mbox import ingest_mbox
from .ingest.email_eml import ingest_eml_dir
from .ingest.notes import ingest_notes_dir
from .ingest.browser_history import ingest_chrome_history_sqlite
from .report.report import build_report


@dataclass
class ImportConfig:
    mbox_path: Optional[Path] = None
    eml_dir: Optional[Path] = None
    notes_dir: Optional[Path] = None
    browser_history_sqlite: Optional[Path] = None


def run_pipeline(cfg: ImportConfig, limits: dict | None = None) -> Tuple[List[Document], dict]:
    limits = limits or {}
    docs: List[Document] = []

    if cfg.mbox_path:
        docs.extend(ingest_mbox(cfg.mbox_path, limit=int(limits.get("mbox", 5000))))
    if cfg.eml_dir:
        docs.extend(ingest_eml_dir(cfg.eml_dir, limit=int(limits.get("eml", 5000))))
    if cfg.notes_dir:
        docs.extend(ingest_notes_dir(cfg.notes_dir, limit=int(limits.get("notes", 5000))))
    if cfg.browser_history_sqlite:
        docs.extend(ingest_chrome_history_sqlite(cfg.browser_history_sqlite, limit=int(limits.get("browser", 10000))))

    docs.sort(key=lambda d: d.timestamp.isoformat() if d.timestamp else "", reverse=True)
    report = build_report(docs)
    return docs, report
