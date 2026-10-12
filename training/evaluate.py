"""Evaluate LR, NB and Legal-BERT on the UNFAIR-ToS test set and the ClauseGuard-IN test set.

Writes backend/models/metrics.json, docs/results.md and charts in docs/figures/.
Every number comes from running the saved models; nothing is typed in by hand.
"""

import json
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import precision_recall_fscore_support  # noqa: E402

from common import LABELS, MODELS, ROOT, load_in, load_unfair_tos  # noqa: E402
from app.nlp.categories import CATEGORIES, UNFAIR_TOS_LABELS, labels_for_doc_type  # noqa: E402
from app.nlp.classify import BaselineModel, HybridModel, LegalBertModel  # noqa: E402

DOCS = ROOT / "docs"
FIG = DOCS / "figures"
DISPLAY = {"baseline-lr": "TF-IDF + Logistic Regression", "baseline-nb": "TF-IDF + Naive Bayes",
           "legal-bert": "Legal-BERT (fine-tuned)", "hybrid": "Hybrid (Legal-BERT + LR)"}
COLORS = {"baseline-lr": "#2a78d6", "baseline-nb": "#eb6834", "legal-bert": "#1baf7a", "hybrid": "#eda100"}


def load_models() -> dict:
    models = {}
    for name, file in [("baseline-lr", "baseline_lr.joblib"), ("baseline-nb", "baseline_nb.joblib")]:
        if (MODELS / file).exists():
            models[name] = BaselineModel(MODELS / file, name)
    if (MODELS / "legalbert" / "config.json").exists():
        th = json.loads((MODELS / "thresholds.json").read_text()) if (MODELS / "thresholds.json").exists() else {}
        models["legal-bert"] = LegalBertModel(str(MODELS / "legalbert"), th)
    if "legal-bert" in models and "baseline-lr" in models:
        models["hybrid"] = HybridModel(models["legal-bert"], models["baseline-lr"])
    return models


def predict(model, texts, doc_types) -> np.ndarray:
    probs = model.predict_proba(texts)
    th = np.array([float(model.thresholds.get(l, 0.5)) for l in LABELS])
    pred = (probs >= th).astype(int)
    # same document-type filter the app uses
    for i, dt in enumerate(doc_types):
        allowed = set(labels_for_doc_type(dt))
        for j, l in enumerate(LABELS):
            if l not in allowed:
                pred[i, j] = 0
    return pred


def scores(y: np.ndarray, p: np.ndarray, labels: list) -> dict:
    idx = [LABELS.index(l) for l in labels]
    y, p = y[:, idx], p[:, idx]
    mi = precision_recall_fscore_support(y, p, average="micro", zero_division=0)
    present = [j for j in range(len(labels)) if y[:, j].sum() > 0]
    ma = precision_recall_fscore_support(y[:, present], p[:, present], average="macro", zero_division=0)
    per = {}
    for j, l in enumerate(labels):
        tp = int(((y[:, j] == 1) & (p[:, j] == 1)).sum())
        fp = int(((y[:, j] == 0) & (p[:, j] == 1)).sum())
        fn = int(((y[:, j] == 1) & (p[:, j] == 0)).sum())
        tn = int(((y[:, j] == 0) & (p[:, j] == 0)).sum())
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        per[l] = {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4),
                  "support": tp + fn, "tp": tp, "fp": fp, "fn": fn, "tn": tn}
    return {"micro_precision": round(mi[0], 4), "micro_recall": round(mi[1], 4), "micro_f1": round(mi[2], 4),
            "macro_precision": round(ma[0], 4), "macro_recall": round(ma[1], 4), "macro_f1": round(ma[2], 4),
            "per_label": per}


def plot_f1(metrics: dict, ds: str, title: str) -> str:
    names = [m for m in metrics["models"] if ds in metrics["models"][m]["results"]]
    first = metrics["models"][names[0]]["results"][ds]["per_label"]
    labels = [l for l in first if first[l]["support"] > 0]
    y = np.arange(len(labels))
    h = 0.8 / len(names)
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(labels) + 1.5))
    for k, m in enumerate(names):
        vals = [metrics["models"][m]["results"][ds]["per_label"][l]["f1"] * 100 for l in labels]
        ax.barh(y + k * h, vals, height=h * 0.9, color=COLORS[m], label=DISPLAY[m])
    ax.set_yticks(y + h * (len(names) - 1) / 2, [CATEGORIES[l]["name"] for l in labels])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("F1 (%)")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    path = FIG / f"f1_{ds}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def plot_confusion(metrics: dict, model: str, ds: str) -> str:
    per = metrics["models"][model]["results"][ds]["per_label"]
    labels = [l for l in per if per[l]["support"] > 0]
    cols = 4
    rows = int(np.ceil(len(labels) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.6, rows * 2.5))
    for ax, l in zip(np.ravel(axes), labels):
        c = per[l]
        m = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
        ax.imshow(m, cmap="Blues")
        for (i, j), v in np.ndenumerate(m):
            ax.text(j, i, str(v), ha="center", va="center", color="white" if v > m.max() / 2 else "black", fontsize=9)
        ax.set_xticks([0, 1], ["pred 0", "pred 1"], fontsize=7)
        ax.set_yticks([0, 1], ["true 0", "true 1"], fontsize=7)
        ax.set_title(CATEGORIES[l]["name"], fontsize=8)
    for ax in np.ravel(axes)[len(labels):]:
        ax.axis("off")
    fig.suptitle(f"{DISPLAY[model]} - {ds}", fontsize=10)
    fig.tight_layout()
    path = FIG / f"confusion_{model}_{ds}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path.name


def label_counts(y: np.ndarray, labels: list) -> dict:
    return {l: int(y[:, LABELS.index(l)].sum()) for l in labels}


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    tos_x, tos_y = load_unfair_tos("test")
    tos_train_x, tos_train_y = load_unfair_tos("train")
    tos_val_x, _ = load_unfair_tos("validation")
    in_x, in_y, in_df = load_in("test")
    _, in_all_y, in_all = load_in("all")
    sets = {
        "unfair_tos_test": (tos_x, tos_y, ["tos"] * len(tos_x), UNFAIR_TOS_LABELS),
        "clauseguard_in_test": (in_x, in_y, list(in_df["doc_type"]), LABELS),
    }

    models = load_models()
    metrics = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "labels": LABELS, "models": {},
               "datasets": {
                   "unfair_tos": {
                       "name": "UNFAIR-ToS (LexGLUE)",
                       "description": "Sentences from 50 online Terms of Service, labelled with 8 unfair clause types.",
                       "split_sizes": {"train": len(tos_train_x), "validation": len(tos_val_x), "test": len(tos_x)},
                       "label_counts": label_counts(tos_train_y, UNFAIR_TOS_LABELS),
                   },
                   "clauseguard_in": {
                       "name": "ClauseGuard-IN (Indian agreements)",
                       "description": "Clauses from Indian rental agreements, offer letters and app policies; 14 labels.",
                       "split_sizes": {"total": len(in_all), "train": len(in_all) - len(in_x), "test": len(in_x),
                                       "fair/neutral": int((in_all["labels"] == "").sum())},
                       "label_counts": label_counts(in_all_y, LABELS),
                   },
               }}
    for name in ["baseline-lr", "baseline-nb", "legal-bert", "hybrid"]:
        entry = {"display_name": DISPLAY[name], "available": name in models, "results": {}}
        if name in models:
            for ds, (x, y, dts, labs) in sets.items():
                entry["results"][ds] = scores(y, predict(models[name], x, dts), labs)
                r = entry["results"][ds]
                print(f"{name:12s} {ds:20s} micro-F1={r['micro_f1']:.3f} macro-F1={r['macro_f1']:.3f}")
        metrics["models"][name] = entry

    (MODELS / "metrics.json").write_text(json.dumps(metrics, indent=2))

    figs = [plot_f1(metrics, ds, t) for ds, t in [("unfair_tos_test", "Per-label F1 on UNFAIR-ToS test"),
                                                  ("clauseguard_in_test", "Per-label F1 on ClauseGuard-IN test")]]
    best = max(models, key=lambda m: metrics["models"][m]["results"]["unfair_tos_test"]["macro_f1"])
    figs += [plot_confusion(metrics, best, ds) for ds in sets]
    write_results(metrics, figs, best)
    print("wrote backend/models/metrics.json, docs/results.md and docs/figures/")


def write_results(metrics: dict, figs: list, best: str) -> None:
    lines = ["# Results", "", f"_Generated by `training/evaluate.py` on {metrics['generated_at']}. "
             "All numbers are computed from the saved models; nothing is hand-written._", ""]
    for ds, title in [("unfair_tos_test", "UNFAIR-ToS test set (8 labels)"),
                      ("clauseguard_in_test", "ClauseGuard-IN test set (14 labels)")]:
        lines += [f"## {title}", "", "| Model | Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 |",
                  "|---|---|---|---|---|---|---|"]
        for m, e in metrics["models"].items():
            r = e["results"].get(ds)
            if not r:
                lines.append(f"| {e['display_name']} | not trained | | | | | |")
                continue
            vals = [r[k] * 100 for k in ("micro_precision", "micro_recall", "micro_f1", "macro_precision",
                                          "macro_recall", "macro_f1")]
            lines.append(f"| {e['display_name']} | " + " | ".join(f"{v:.1f}" for v in vals) + " |")
        lines += ["", "Per-label F1 (%):", "", "| Label | Support | " + " | ".join(
            metrics["models"][m]["display_name"] for m in metrics["models"] if ds in metrics["models"][m]["results"]) + " |"]
        avail = [m for m in metrics["models"] if ds in metrics["models"][m]["results"]]
        lines.append("|---|---|" + "---|" * len(avail))
        first = metrics["models"][avail[0]]["results"][ds]["per_label"]
        for l, v in first.items():
            if v["support"] == 0:
                continue
            row = [f"{metrics['models'][m]['results'][ds]['per_label'][l]['f1'] * 100:.1f}" for m in avail]
            lines.append(f"| {CATEGORIES[l]['name']} | {v['support']} | " + " | ".join(row) + " |")
        lines.append("")
    lines += ["## Figures", ""] + [f"![{f}](figures/{f})" for f in figs]
    lines += ["", f"Confusion matrices are shown for the model with the best UNFAIR-ToS macro-F1 ({DISPLAY[best]}).", "",
              "## Notes", "",
              "- Macro averages use only labels that appear in that test set.",
              "- ClauseGuard-IN test clauses come from templates never seen in training (group split), "
              "but the set is small (about 50 clauses), so its scores have high variance.",
              "- Hybrid uses Legal-BERT for the 8 UNFAIR-ToS labels and the LR baseline for the 6 India-specific labels.",
              "- Predictions use the per-label thresholds tuned on the dev set and the same document-type filter as the app.", ""]
    (DOCS / "results.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
