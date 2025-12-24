from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from collections import Counter, defaultdict
import re

from ..types import Document
from ..nlp.text_clean import normalize

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "software & engineering": ["api", "docker", "kubernetes", "python", "node", "react", "linux", "database", "sql", "backend", "frontend", "compiler", "kafka"],
    "cybersecurity": ["vulnerability", "cve", "threat", "exploit", "malware", "phishing", "tls", "mfa", "auth", "encryption", "zero trust", "siem", "incident"],
    "finance & investing": ["portfolio", "stocks", "equity", "investment", "mutual fund", "crypto", "bitcoin", "tax", "salary", "budget", "loan", "interest rate"],
    "health & fitness": ["workout", "calories", "diet", "protein", "running", "sleep", "gym", "doctor", "medicine", "symptom"],
    "education & research": ["paper", "arxiv", "thesis", "dataset", "experiment", "university", "admission", "sop", "scholarship", "journal"],
    "travel & location": ["flight", "hotel", "visa", "itinerary", "trip", "tour", "booking", "airport"],
    "shopping": ["buy", "price", "discount", "order", "cart", "shipping", "delivery"],
    "entertainment": ["movie", "music", "lyrics", "netflix", "spotify", "anime", "game", "youtube"],
}

DOMAIN_HINTS: Dict[str, str] = {
    "github.com": "software & engineering",
    "stackoverflow.com": "software & engineering",
    "docs.google.com": "education & research",
    "arxiv.org": "education & research",
    "coursera.org": "education & research",
    "udemy.com": "education & research",
    "netflix.com": "entertainment",
    "spotify.com": "entertainment",
    "youtube.com": "entertainment",
    "amazon.": "shopping",
    "flipkart.": "shopping",
}


@dataclass
class InterestSignal:
    label: str
    score: float
    top_keywords: List[Tuple[str, float]]
    top_sources: List[Dict[str, Any]]


def _keyword_score(text_norm: str, keywords: List[str]) -> Tuple[float, Counter]:
    score = 0.0
    hit = Counter()
    for kw in keywords:
        kw_norm = normalize(kw)
        if " " in kw_norm:
            c = text_norm.count(kw_norm)
        else:
            c = len(re.findall(rf"\b{re.escape(kw_norm)}\b", text_norm))
        if c:
            hit[kw] += c
            score += float(c)
    return score, hit


def infer_interests(docs: List[Document], top_k: int = 6) -> List[InterestSignal]:
    per_doc_norm = [(d, normalize(d.text)) for d in docs if d.text.strip()]

    label_scores = defaultdict(float)
    label_hits = defaultdict(Counter)
    label_doc_scores = defaultdict(list)  # label -> [(score, doc), ...]

    for d, tnorm in per_doc_norm:
        for label, kws in CATEGORY_KEYWORDS.items():
            s, hits = _keyword_score(tnorm, kws)
            if s > 0:
                label_scores[label] += s
                label_hits[label].update(hits)
                label_doc_scores[label].append((s, d))

        if d.source == "browser":
            host = (d.meta.get("host") or "").lower()
            for k, lbl in DOMAIN_HINTS.items():
                if k.endswith("."):
                    if host.startswith(k) or k in host:
                        label_scores[lbl] += 1.0
                        label_doc_scores[lbl].append((1.0, d))
                else:
                    if host == k:
                        label_scores[lbl] += 2.0
                        label_doc_scores[lbl].append((2.0, d))

    total = sum(label_scores.values()) or 1.0
    ranked = sorted(label_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    out: List[InterestSignal] = []
    for label, score in ranked:
        hits = label_hits[label]
        top_kw = [(k, float(v)) for k, v in hits.most_common(8)]
        top_docs = sorted(label_doc_scores[label], key=lambda x: x[0], reverse=True)[:5]
        top_sources = []
        for s, d in top_docs:
            top_sources.append(
                {
                    "doc_id": d.doc_id,
                    "source": d.source,
                    "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                    "score": float(s),
                    "preview": d.text[:180].replace("\n", " "),
                    "meta": {k: d.meta.get(k) for k in ("subject", "from", "host", "title", "path", "url") if k in d.meta},
                }
            )
        out.append(
            InterestSignal(
                label=label,
                score=float(score / total),
                top_keywords=top_kw,
                top_sources=top_sources,
            )
        )
    return out
