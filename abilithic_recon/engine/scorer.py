"""Transparent, deterministic risk scoring.

Weights come from config (calibratable without a rebuild). Every point of the
score is explained by a contributor with a reason + finding reference.
"""
from __future__ import annotations

from ..core.models import (Finding, RiskBreakdown, RiskContributor, Severity)

_GRADES = [
    (85, "CRITICAL"),
    (65, "HIGH"),
    (40, "MEDIUM"),
    (15, "LOW"),
    (0, "INFO"),
]


def score(findings: list[Finding], weights: dict, i18n=None) -> RiskBreakdown:
    rb = RiskBreakdown()
    total = 0
    for f in findings:
        w = int(weights.get(f.type, 5))
        # scale weight by severity rank (CRITICAL counts fullest)
        try:
            sev_rank = Severity(f.severity).rank
        except Exception:
            sev_rank = 1
        contrib = int(round(w * (0.5 + 0.125 * sev_rank)))  # rank0=0.5x .. rank4=1.0x
        total += contrib
        rb.contributors.append(RiskContributor(
            factor=f.type, weight=contrib,
            reason=f.title or f.type, finding_ref=f.id))
    rb.score = max(0, min(100, total))
    rb.grade = next(g for thr, g in _GRADES if rb.score >= thr)
    return rb
