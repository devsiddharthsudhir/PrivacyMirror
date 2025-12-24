from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Document:
    """A unit of text + metadata to analyze."""

    doc_id: str
    source: str  # "email_mbox" | "email_eml" | "notes" | "browser"
    text: str
    timestamp: Optional[datetime] = None
    meta: Dict[str, Any] = field(default_factory=dict)
