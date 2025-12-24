from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

from ..types import Document


@dataclass
class RhythmProfile:
    hourly_counts: Dict[int, int]
    day_counts: Dict[int, int]
    active_days: int
    peak_hour: Optional[int]
    earliest_active_hour: Optional[int]
    latest_active_hour: Optional[int]
    inferred_chronotype: str  # "morning-leaning" | "night-leaning" | "mixed" | "insufficient-data"
    confidence: float  # 0..1


def infer_rhythm(docs: List[Document]) -> RhythmProfile:
    times = [d.timestamp for d in docs if d.timestamp is not None]
    hourly = {h: 0 for h in range(24)}
    dow = {d: 0 for d in range(7)}  # Monday=0

    if len(times) < 20:
        return RhythmProfile(
            hourly,
            dow,
            active_days=0,
            peak_hour=None,
            earliest_active_hour=None,
            latest_active_hour=None,
            inferred_chronotype="insufficient-data",
            confidence=0.0,
        )

    days = set()
    for t in times:
        hourly[t.hour] += 1
        dow[t.weekday()] += 1
        days.add(t.date())

    peak_hour = max(hourly, key=lambda h: hourly[h])

    # Define "active hours" as those above a small threshold (relative to max)
    maxc = max(hourly.values()) if hourly else 0
    thr = max(2, int(maxc * 0.15))
    active_hours = [h for h, c in hourly.items() if c >= thr]
    earliest = min(active_hours) if active_hours else None
    latest = max(active_hours) if active_hours else None

    # Chronotype heuristic:
    late_activity = sum(hourly[h] for h in range(22, 24)) + sum(hourly[h] for h in range(0, 2))
    morning_activity = sum(hourly[h] for h in range(6, 10))
    total = sum(hourly.values())

    chronotype = "mixed"
    if total > 0:
        if late_activity / total >= 0.18 and peak_hour >= 18:
            chronotype = "night-leaning"
        elif morning_activity / total >= 0.18 and peak_hour <= 11 and late_activity / total <= 0.10:
            chronotype = "morning-leaning"
        else:
            chronotype = "mixed"

    # Confidence: higher with more concentration (lower entropy)
    counts = np.array([hourly[h] for h in range(24)], dtype=float)
    if counts.sum() == 0:
        conf = 0.0
    else:
        p = counts / counts.sum()
        entropy = -np.sum(p[p > 0] * np.log(p[p > 0]))
        max_entropy = np.log(24)
        conf = float(1.0 - entropy / max_entropy)
        conf = min(1.0, max(0.1, conf))

    return RhythmProfile(
        hourly_counts=hourly,
        day_counts=dow,
        active_days=len(days),
        peak_hour=int(peak_hour),
        earliest_active_hour=int(earliest) if earliest is not None else None,
        latest_active_hour=int(latest) if latest is not None else None,
        inferred_chronotype=chronotype,
        confidence=conf,
    )
