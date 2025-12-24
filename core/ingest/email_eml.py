from __future__ import annotations

import email
from email.header import decode_header
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from dateutil import parser as dtparser

from ..types import Document
from ..utils import stable_id


def _decode_header(value: Optional[str]) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for txt, enc in parts:
        if isinstance(txt, bytes):
            out.append(txt.decode(enc or "utf-8", errors="ignore"))
        else:
            out.append(str(txt))
    return "".join(out)


def _extract_text(msg: email.message.Message, max_chars: int = 200_000) -> str:
    texts = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            disp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue
            if ctype == "text/plain":
                payload = part.get_payload(decode=True) or b""
                texts.append(payload.decode(part.get_content_charset() or "utf-8", errors="ignore"))
            elif ctype == "text/html" and not texts:
                payload = part.get_payload(decode=True) or b""
                html = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "lxml")
                    texts.append(soup.get_text(" ", strip=True))
                except Exception:
                    texts.append(html)
    else:
        payload = msg.get_payload(decode=True) or b""
        texts.append(payload.decode(msg.get_content_charset() or "utf-8", errors="ignore"))

    full = "\n".join(t for t in texts if t).strip()
    return full[:max_chars]


def ingest_eml_dir(folder: Path, limit: int = 5000) -> List[Document]:
    docs: List[Document] = []
    emls = sorted([p for p in folder.rglob("*.eml") if p.is_file()])
    for p in emls[:limit]:
        raw = p.read_bytes()
        msg = email.message_from_bytes(raw)
        subj = _decode_header(msg.get("Subject"))
        from_ = _decode_header(msg.get("From"))
        date_raw = msg.get("Date")
        ts: Optional[datetime] = None
        if date_raw:
            try:
                ts = dtparser.parse(date_raw)
            except Exception:
                ts = None

        body = _extract_text(msg)
        text = f"subject: {subj}\nfrom: {from_}\n\n{body}".strip()
        doc_id = stable_id("eml", str(p), subj, from_)
        docs.append(
            Document(
                doc_id=doc_id,
                source="email_eml",
                text=text,
                timestamp=ts,
                meta={"subject": subj, "from": from_, "path": str(p)},
            )
        )
    return docs
