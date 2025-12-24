from __future__ import annotations

import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from ..types import Document
from ..utils import stable_id

CHROME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def chrome_time_to_dt(value: int) -> datetime:
    # Chrome stores microseconds since 1601-01-01 UTC
    return CHROME_EPOCH + timedelta(microseconds=int(value))


def ingest_chrome_history_sqlite(path: Path, limit: int = 10000) -> List[Document]:
    docs: List[Document] = []
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    query = '''
    SELECT urls.url AS url, urls.title AS title, visits.visit_time AS visit_time
    FROM visits
    JOIN urls ON visits.url = urls.id
    ORDER BY visits.visit_time DESC
    LIMIT ?
    '''

    for row in cur.execute(query, (limit,)):
        url = row["url"] or ""
        title = row["title"] or ""
        visit_time = row["visit_time"]
        ts: Optional[datetime] = None
        try:
            ts = chrome_time_to_dt(int(visit_time)).astimezone(timezone.utc)
        except Exception:
            ts = None
        host = ""
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            host = ""

        # Data minimization: keep the "text" minimal but useful.
        text = f"visited: {host}\nurl: {url}\ntitle: {title}".strip()
        doc_id = stable_id("browser", str(path), url, str(visit_time))
        docs.append(
            Document(
                doc_id=doc_id,
                source="browser",
                text=text,
                timestamp=ts,
                meta={"url": url, "title": title, "host": host, "path": str(path)},
            )
        )

    con.close()
    return docs
