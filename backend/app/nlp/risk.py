# Risk scores for clauses and documents

from typing import Dict, List, Tuple

from .categories import CATEGORIES

HIGH_CUTOFF = 2.1
MEDIUM_CUTOFF = 1.01


# clause score = severity x probability
def clause_risk(labels: List[str], probs: Dict[str, float]) -> Tuple[float, str]:
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


# document score out of 100, led by the worst clauses
def document_score(clause_scores: List[float]) -> int:
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
