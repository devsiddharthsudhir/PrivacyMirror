from __future__ import annotations

import mailbox
import email
import re
from email.header import decode_header
from datetime import datetime
from pathlib import Path
from typing import List, Optional

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
            try:
                out.append(txt.decode(enc or "utf-8", errors="ignore"))
            except Exception:
                out.append(txt.decode("utf-8", errors="ignore"))
        else:
            out.append(str(txt))
    return "".join(out)


def _extract_text(msg: email.message.Message, max_chars: int = 200_000) -> str:
    # Prefer text/plain, fall back to stripping HTML.
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
                    texts.append(re.sub(r"<[^>]+>", " ", html))
    else:
        payload = msg.get_payload(decode=True) or b""
        texts.append(payload.decode(msg.get_content_charset() or "utf-8", errors="ignore"))

    full = "\n".join(t for t in texts if t).strip()
    return full[:max_chars]


def ingest_mbox(path: Path, limit: int = 5000) -> List[Document]:
    docs: List[Document] = []
    mbox = mailbox.mbox(path)
    for i, msg in enumerate(mbox):
        if i >= limit:
            break
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

        doc_id = stable_id("mbox", str(path), str(i), subj, from_)
        docs.append(
            Document(
                doc_id=doc_id,
                source="email_mbox",
                text=text,
                timestamp=ts,
                meta={"subject": subj, "from": from_, "index": i, "path": str(path)},
            )
        )
    return docs
