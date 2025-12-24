from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from ..types import Document
from ..infer.rhythm import infer_rhythm
from ..infer.work_patterns import infer_work_patterns
from ..infer.interests import infer_interests, CATEGORY_KEYWORDS
from ..explain.attribution import keyword_attribution


def build_report(docs: List[Document]) -> Dict[str, Any]:
    rhythm = infer_rhythm(docs)
    work = infer_work_patterns(docs)
    interests = infer_interests(docs)

    attributions = []
    for it in interests:
        kws = CATEGORY_KEYWORDS.get(it.label, [])
        if kws:
            attr = keyword_attribution(docs, it.label, kws)
            attributions.append(
                {"inference": it.label, "signals": attr.signals, "top_documents": attr.top_documents}
            )

    return {
        "summary": {"documents_analyzed": len(docs), "sources": sorted(list({d.source for d in docs}))},
        "rhythm": asdict(rhythm),
        "work_patterns": asdict(work),
        "interests": [
            {"label": it.label, "score": it.score, "top_keywords": it.top_keywords, "top_sources": it.top_sources}
            for it in interests
        ],
        "attributions": attributions,
        "minimization_tips": minimization_tips(),
    }


def minimization_tips() -> List[Dict[str, Any]]:
    return [
        {
            "title": "Reduce identity leakage in emails",
            "why": "Signatures and forwarded threads often include phone numbers, addresses, job titles, and org charts.",
            "do_this": [
                "Use a short signature (name + role only).",
                "Avoid forwarding entire threads; copy only necessary context.",
                "Remove tracking pixels where possible (mail clients that block remote images).",
            ],
        },
        {
            "title": "Make your daily rhythm less fingerprintable",
            "why": "Consistent activity windows can reveal chronotype, routines, and time zone.",
            "do_this": [
                "Batch-send emails (draft now, schedule send later).",
                "Avoid logging into sensitive services at the same times daily.",
                "Use privacy-respecting browsers and clear history periodically (if it doesn’t break your workflow).",
            ],
        },
        {
            "title": "Minimize interest profiling from browsing",
            "why": "Visited domains + search terms are highly predictive of interests and life events.",
            "do_this": [
                "Use separate browser profiles for work vs personal.",
                "Use private windows for sensitive topics.",
                "Disable third-party cookies; consider tracker-blocking extensions.",
            ],
        },
        {
            "title": "Keep local data local",
            "why": "Cloud note apps or sync can leak metadata even if content is encrypted end-to-end.",
            "do_this": [
                "Store sensitive notes offline where possible.",
                "Encrypt local backups; set strong device passcodes.",
                "Use full-disk encryption (BitLocker/FileVault/LUKS).",
            ],
        },
    ]
