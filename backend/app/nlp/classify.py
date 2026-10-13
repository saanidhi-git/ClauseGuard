# Clause classifier

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from ..config import DISABLE_TRANSFORMERS, LEGALBERT_HUB_ID, MODELS_DIR
from .categories import LABELS, UNFAIR_TOS_LABELS, labels_for_doc_type
from .preprocess import clean_for_model

log = logging.getLogger("clauseguard.classify")


# TF-IDF baseline model
class BaselineModel:

    def __init__(self, path: Path, name: str):
        import joblib

        bundle = joblib.load(path)
        self.pipeline = bundle["pipeline"]
        self.labels: List[str] = bundle["labels"]
        self.thresholds: Dict[str, float] = bundle.get("thresholds", {})
        self.name = name

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        cleaned = [clean_for_model(t) for t in texts]
        probs = np.asarray(self.pipeline.predict_proba(cleaned))
        return _reorder(probs, self.labels)


# fine-tuned Legal-BERT model
class LegalBertModel:

    name = "legal-bert"

    def __init__(self, source: str, thresholds: Dict[str, float]):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(source)
        self.model = AutoModelForSequenceClassification.from_pretrained(source)
        self.model.eval()
        id2label = self.model.config.id2label
        self.labels = [id2label[i] for i in range(len(id2label))]
        self.thresholds = thresholds

    def predict_proba(self, texts: List[str], batch_size: int = 16) -> np.ndarray:
        out = []
        with self.torch.no_grad():
            for i in range(0, len(texts), batch_size):
                enc = self.tokenizer(texts[i:i + batch_size], truncation=True, max_length=256,
                                     padding=True, return_tensors="pt")
                logits = self.model(**enc).logits
                out.append(self.torch.sigmoid(logits).cpu().numpy())
        probs = np.vstack(out) if out else np.zeros((0, len(self.labels)))
        return _reorder(probs, self.labels)


# Legal-BERT for the 8 ToS labels, baseline for the 6 Indian labels
class HybridModel:

    name = "hybrid"

    def __init__(self, bert: "LegalBertModel", lr: BaselineModel):
        self.bert, self.lr = bert, lr
        self.thresholds = {l: (bert if l in UNFAIR_TOS_LABELS else lr).thresholds.get(l, 0.5) for l in LABELS}

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        probs = self.lr.predict_proba(texts)
        bert = self.bert.predict_proba(texts)
        for l in UNFAIR_TOS_LABELS:
            j = LABELS.index(l)
            probs[:, j] = bert[:, j]
        return probs


# put model outputs in the same label order
def _reorder(probs: np.ndarray, labels: List[str]) -> np.ndarray:
    full = np.zeros((probs.shape[0], len(LABELS)), dtype=float)
    for j, lab in enumerate(labels):
        if lab in LABELS:
            full[:, LABELS.index(lab)] = probs[:, j]
    return full


# loads the models once and reuses them
class ClauseClassifier:

    _instance: Optional["ClauseClassifier"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.models: Dict[str, object] = {}
        self.primary: Optional[str] = None
        self._load()

    @classmethod
    def get(cls) -> "ClauseClassifier":
        with cls._lock:
            if cls._instance is None:
                cls._instance = ClauseClassifier()
            return cls._instance

    def _load(self) -> None:
        for name, file in [("baseline-lr", "baseline_lr.joblib"), ("baseline-nb", "baseline_nb.joblib")]:
            path = MODELS_DIR / file
            if path.exists():
                try:
                    self.models[name] = BaselineModel(path, name)
                except Exception as exc:
                    log.warning("Could not load %s: %s", file, exc)

        bert_dir = MODELS_DIR / "legalbert"
        source = str(bert_dir) if (bert_dir / "config.json").exists() else LEGALBERT_HUB_ID
        if source and not DISABLE_TRANSFORMERS:
            try:
                thresholds = {}
                tpath = MODELS_DIR / "thresholds.json"
                if tpath.exists():
                    thresholds = json.loads(tpath.read_text(encoding="utf-8"))
                self.models["legal-bert"] = LegalBertModel(source, thresholds)
            except Exception as exc:
                log.warning("Legal-BERT not available, using baseline: %s", exc)

        if "legal-bert" in self.models and "baseline-lr" in self.models:
            self.models["hybrid"] = HybridModel(self.models["legal-bert"], self.models["baseline-lr"])

        for name in ["hybrid", "legal-bert", "baseline-lr", "baseline-nb"]:
            if name in self.models:
                self.primary = name
                break
        log.info("Classifier ready. Primary model: %s", self.primary)

    @property
    def model_used(self) -> str:
        return self.primary or "keyword-fallback"

    def _thresholds(self, name: str) -> np.ndarray:
        model = self.models.get(name)
        th = getattr(model, "thresholds", {}) or {}
        return np.array([float(th.get(lab, 0.5)) for lab in LABELS])

    # predict risk labels for each clause
    def predict(self, texts: List[str], doc_type: str) -> List[dict]:
        if not texts:
            return []
        allowed = set(labels_for_doc_type(doc_type))
        if self.primary is None:
            return [{"labels": [], "probs": {}} for _ in texts]
        probs = self.models[self.primary].predict_proba(texts)
        th = self._thresholds(self.primary)
        results = []
        for row in probs:
            p = {lab: round(float(row[i]), 4) for i, lab in enumerate(LABELS) if lab in allowed}
            labels = [lab for i, lab in enumerate(LABELS) if lab in allowed and row[i] >= th[i]]
            labels.sort(key=lambda l: -p[l])
            results.append({"labels": labels, "probs": p})
        return results

    # run every model on one clause
    def compare(self, text: str) -> Dict[str, dict]:
        out = {}
        for name, model in self.models.items():
            row = model.predict_proba([text])[0]
            th = self._thresholds(name)
            out[name] = {
                "probs": {lab: round(float(row[i]), 4) for i, lab in enumerate(LABELS)},
                "labels": [lab for i, lab in enumerate(LABELS) if row[i] >= th[i]],
            }
        return out
