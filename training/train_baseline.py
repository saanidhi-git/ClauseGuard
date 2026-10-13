# Train the TF-IDF baseline models

import time

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from common import LABELS, MODELS, group_holdout, load_in, load_unfair_tos, tune_thresholds
from app.nlp.preprocess import clean_for_model

IN_OVERSAMPLE = 3  # repeat the small Indian dataset


def make_pipeline(kind: str) -> Pipeline:
    tfidf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)
    if kind == "lr":
        clf = OneVsRestClassifier(LogisticRegression(class_weight="balanced", max_iter=2000, C=4.0))
    else:
        clf = OneVsRestClassifier(MultinomialNB(alpha=0.1))
    return Pipeline([("tfidf", tfidf), ("clf", clf)])


def stack(parts):
    texts = [t for p in parts for t in p[0]]
    y = np.vstack([p[1] for p in parts])
    return texts, y


def main() -> None:
    t0 = time.time()
    tos_x, tos_y = load_unfair_tos("train")
    tos_vx, tos_vy = load_unfair_tos("validation")
    in_x, in_y, in_df = load_in("train")
    print(f"UNFAIR-ToS train={len(tos_x)} val={len(tos_vx)}  ClauseGuard-IN train={len(in_x)}")

    clean = lambda xs: [clean_for_model(x) for x in xs]  # noqa: E731
    tos_x, tos_vx, in_x = clean(tos_x), clean(tos_vx), clean(in_x)

    dev_mask = group_holdout(in_df)
    in_tr = ([x for x, d in zip(in_x, dev_mask) if not d] * IN_OVERSAMPLE, np.vstack([in_y[~dev_mask]] * IN_OVERSAMPLE))
    in_dev = ([x for x, d in zip(in_x, dev_mask) if d], in_y[dev_mask])
    fit_x, fit_y = stack([(tos_x, tos_y), in_tr])
    dev_x, dev_y = stack([(tos_vx, tos_vy), in_dev])
    full_x, full_y = stack([(tos_x, tos_y), (in_x * IN_OVERSAMPLE, np.vstack([in_y] * IN_OVERSAMPLE))])

    MODELS.mkdir(parents=True, exist_ok=True)
    for kind in ["lr", "nb"]:
        pipe = make_pipeline(kind)
        pipe.fit(fit_x, fit_y)
        thresholds = tune_thresholds(dev_y, pipe.predict_proba(dev_x))
        pipe = make_pipeline(kind)
        pipe.fit(full_x, full_y)
        bundle = {"pipeline": pipe, "labels": LABELS, "thresholds": thresholds,
                  "trained_on": "UNFAIR-ToS train + ClauseGuard-IN train"}
        joblib.dump(bundle, MODELS / f"baseline_{kind}.joblib", compress=3)
        print(f"saved baseline_{kind}.joblib  thresholds={thresholds}")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
