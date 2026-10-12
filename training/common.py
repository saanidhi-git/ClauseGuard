"""Shared data loading for training and evaluation."""

import random
import re
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.nlp.categories import LABELS  # noqa: E402

DATA = ROOT / "data"
MODELS = ROOT / "backend" / "models"
SEED = 42


def _key(name: str) -> str:
    return re.sub(r"[^a-z]+", "_", name.lower()).strip("_")


def load_unfair_tos(split: str) -> Tuple[List[str], np.ndarray]:
    """UNFAIR-ToS split mapped into the 14-label space (label order read from the dataset)."""
    from datasets import load_dataset

    ds = load_dataset("coastalcph/lex_glue", "unfair_tos", split=split)
    names = ds.features["labels"].feature.names
    cols = [LABELS.index(_key(n)) for n in names]
    y = np.zeros((len(ds), len(LABELS)), dtype=int)
    for i, labs in enumerate(ds["labels"]):
        for l in labs:
            y[i, cols[l]] = 1
    return list(ds["text"]), y


def load_in(split: str) -> Tuple[List[str], np.ndarray, pd.DataFrame]:
    """ClauseGuard-IN split ('train', 'test' or 'all')."""
    name = "clauseguard_in.csv" if split == "all" else f"clauseguard_in_{split}.csv"
    df = pd.read_csv(DATA / name, keep_default_na=False)
    y = np.zeros((len(df), len(LABELS)), dtype=int)
    for i, labs in enumerate(df["labels"]):
        for l in filter(None, str(labs).split("|")):
            y[i, LABELS.index(l)] = 1
    return list(df["text"]), y, df


def group_holdout(df: pd.DataFrame, frac: float = 0.2) -> np.ndarray:
    """Boolean mask of a dev set made of whole template groups."""
    rng = random.Random(SEED)
    groups = sorted(df["group"].unique())
    rng.shuffle(groups)
    dev = set(groups[: max(1, int(len(groups) * frac))])
    return df["group"].isin(dev).to_numpy()


def tune_thresholds(y_true: np.ndarray, probs: np.ndarray) -> dict:
    """Best F1 threshold per label on a dev set (0.5 if the label has no positives)."""
    from sklearn.metrics import f1_score

    out = {}
    for j, lab in enumerate(LABELS):
        if y_true[:, j].sum() == 0:
            out[lab] = 0.5
            continue
        best_t, best_f = 0.5, -1.0
        for t in np.arange(0.3, 0.91, 0.05):
            f = f1_score(y_true[:, j], (probs[:, j] >= t).astype(int), zero_division=0)
            if f > best_f:
                best_t, best_f = float(round(t, 2)), f
        out[lab] = best_t
    return out
