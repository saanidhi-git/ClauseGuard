"""Clause-level and document-level risk scoring."""

from typing import Dict, List, Tuple

from .categories import CATEGORIES

# clause score = max over labels of severity (1-3) x probability, so it ranges 0..3
HIGH_CUTOFF = 2.1
MEDIUM_CUTOFF = 1.01


def clause_risk(labels: List[str], probs: Dict[str, float]) -> Tuple[float, str]:
    """Return (score 0..3, level) for one clause; only predicted labels count."""
    if not labels:
        return 0.0, "Safe"
    score = max(CATEGORIES[l]["severity"] * probs.get(l, 0.0) for l in labels)
    if score >= HIGH_CUTOFF:
        level = "High"
    elif score >= MEDIUM_CUTOFF:
        level = "Medium"
    else:
        level = "Low"
    return round(score, 3), level


def document_score(clause_scores: List[float]) -> int:
    """0-100 score dominated by the worst clauses.

    The clause scores are sorted from worst to best and combined with decaying weights
    (1, 1/2, 1/3, ...), so one very risky clause matters a lot, and many medium clauses
    add up, but long documents with lots of safe clauses are not diluted.
    score = 100 * (1 - exp(-sum_k (s_k / 3) / k / 1.5))
    """
    import math

    ranked = sorted((s for s in clause_scores if s > 0), reverse=True)
    total = sum((s / 3.0) / (k + 1) for k, s in enumerate(ranked))
    return int(round(100 * (1 - math.exp(-total / 1.5))))


def verdict(score: int) -> str:
    if score >= 70:
        return "High risk: read carefully and negotiate before signing"
    if score >= 40:
        return "Moderate risk: some clauses need attention"
    if score >= 15:
        return "Low risk: a few points to check"
    return "Looks fair: no major red flags found"


def level_counts(levels: List[str]) -> Dict[str, int]:
    counts = {"High": 0, "Medium": 0, "Low": 0, "Safe": 0}
    for lv in levels:
        counts[lv] = counts.get(lv, 0) + 1
    return counts
