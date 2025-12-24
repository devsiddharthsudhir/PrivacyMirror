from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import re

from ..types import Document
from ..nlp.text_clean import normalize, sentence_snippet


@dataclass
class Attribution:
    inference: str
    signals: List[Dict[str, Any]]
    top_documents: List[Dict[str, Any]]


def keyword_attribution(docs: List[Document], label: str, keywords: List[str], top_docs: int = 6) -> Attribution:
    scores: List[Tuple[float, Document, List[str]]] = []

    for d in docs:
        t = normalize(d.text)
        hit_kws: List[str] = []
        s = 0.0
        for kw in keywords:
            kw_norm = normalize(kw)
            if " " in kw_norm:
                c = t.count(kw_norm)
            else:
                c = len(re.findall(rf"\b{re.escape(kw_norm)}\b", t))
            if c:
                s += c
                hit_kws.append(kw)
        if s > 0:
            scores.append((s, d, hit_kws))

    scores.sort(key=lambda x: x[0], reverse=True)

    kw_counts = defaultdict(int)
    for s, d, hit_kws in scores:
        for k in hit_kws:
            kw_counts[k] += 1

    sigs = [{"type": "keyword", "value": k, "strength": int(c)} for k, c in sorted(kw_counts.items(), key=lambda x: x[1], reverse=True)[:10]]

    top_documents = []
    for s, d, hit_kws in scores[:top_docs]:
        top_documents.append(
            {
                "doc_id": d.doc_id,
                "source": d.source,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                "score": float(s),
                "matched": hit_kws[:8],
                "preview": sentence_snippet(d.text),
                "meta": {k: d.meta.get(k) for k in ("subject", "from", "host", "title", "path", "url") if k in d.meta},
            }
        )

    return Attribution(inference=label, signals=sigs, top_documents=top_documents)
