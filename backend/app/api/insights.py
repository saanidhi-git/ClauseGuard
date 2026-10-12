"""Model Insights: metrics, dataset stats and single-clause testing."""

import json

from fastapi import APIRouter

from ..config import MODELS_DIR
from ..nlp.categories import CATEGORIES, LABELS
from ..nlp.classify import ClauseClassifier
from ..nlp.explain import template_explanation
from ..nlp.preprocess import analyze_steps
from ..nlp.risk import clause_risk
from ..schemas import ClassifyIn

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("")
def insights():
    path = MODELS_DIR / "metrics.json"
    metrics = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    clf = ClauseClassifier.get()
    return {
        "metrics": metrics,
        "model_used": clf.model_used,
        "available_models": list(clf.models.keys()),
        "is_baseline": clf.model_used.startswith("baseline") or clf.model_used == "keyword-fallback",
        "labels": [{"key": k, "name": CATEGORIES[k]["name"], "severity": CATEGORIES[k]["severity"],
                    "doc_types": CATEGORIES[k]["doc_types"]} for k in LABELS],
    }


@router.post("/classify")
def classify_one(body: ClassifyIn):
    clf = ClauseClassifier.get()
    compare = clf.compare(body.text)
    primary = compare.get(clf.model_used, {"labels": [], "probs": {}})
    score, level = clause_risk(primary["labels"], primary["probs"])
    return {
        "models": compare,
        "model_used": clf.model_used,
        "risk_level": level,
        "risk_score": score,
        "explanation": template_explanation(body.text, primary["labels"], primary["probs"]),
        "preprocessing": analyze_steps(body.text),
    }
