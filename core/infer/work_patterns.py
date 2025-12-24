from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import numpy as np

from ..types import Document


@dataclass
class WorkPattern:
    weekday_ratio: float
    weekend_ratio: float
    typical_work_start: Optional[int]
    typical_work_end: Optional[int]
    meeting_hour_guess: Optional[int]
    confidence: float


def infer_work_patterns(docs: List[Document]) -> WorkPattern:
    times = [d.timestamp for d in docs if d.timestamp is not None]
    if len(times) < 30:
        return WorkPattern(
            weekday_ratio=0.0,
            weekend_ratio=0.0,
            typical_work_start=None,
            typical_work_end=None,
            meeting_hour_guess=None,
            confidence=0.0,
        )

    weekday = 0
    weekend = 0
    weekday_hourly = np.zeros(24, dtype=float)

    for t in times:
        if t.weekday() < 5:
            weekday += 1
            weekday_hourly[t.hour] += 1
        else:
            weekend += 1

    total = weekday + weekend
    weekday_ratio = weekday / total if total else 0.0
    weekend_ratio = weekend / total if total else 0.0

    w = weekday_hourly.copy()
    w[:5] *= 0.25
    w[23:] *= 0.25

    best_sum = -1.0
    best_start = None
    for start in range(6, 15):
        s = float(w[start : start + 9].sum())
        if s > best_sum:
            best_sum = s
            best_start = start

    if best_start is None or best_sum <= 0:
        return WorkPattern(weekday_ratio, weekend_ratio, None, None, None, 0.2)

    work_start = int(best_start)
    work_end = int(best_start + 9)

    mid = weekday_hourly[9:18]
    meeting_hour = int(9 + int(np.argmax(mid))) if mid.sum() > 0 else None

    if weekday_hourly.sum() == 0:
        conf = 0.0
    else:
        p = weekday_hourly / weekday_hourly.sum()
        entropy = -float(np.sum(p[p > 0] * np.log(p[p > 0])))
        conf = float(1.0 - entropy / np.log(24))
        conf = max(0.1, min(1.0, conf))
        if weekday_ratio < 0.55:
            conf *= 0.7

    return WorkPattern(
        weekday_ratio=float(weekday_ratio),
        weekend_ratio=float(weekend_ratio),
        typical_work_start=work_start,
        typical_work_end=work_end,
        meeting_hour_guess=meeting_hour,
        confidence=float(conf),
    )
