# Fine-tune Legal-BERT (small) for the 14 risk labels

import argparse
import json
import random
import time

import numpy as np
import torch
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from common import LABELS, MODELS, SEED, group_holdout, load_in, load_unfair_tos, tune_thresholds

BASE = "nlpaueb/legal-bert-small-uncased"
IN_OVERSAMPLE = 3


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def make_loader(texts, y, tok, max_len, batch, shuffle):
    data = list(zip(texts, y.astype("float32")))

    def collate(items):
        enc = tok([t for t, _ in items], truncation=True, max_length=max_len, padding=True, return_tensors="pt")
        enc["labels"] = torch.tensor(np.stack([l for _, l in items]))
        return enc

    return DataLoader(data, batch_size=batch, shuffle=shuffle, collate_fn=collate)


@torch.no_grad()
def predict(model, loader, device) -> np.ndarray:
    model.eval()
    out = []
    for b in loader:
        b = {k: v.to(device) for k, v in b.items() if k != "labels"}
        with torch.autocast(device, enabled=device == "cuda"):
            out.append(torch.sigmoid(model(**b).logits.float()).cpu().numpy())
    return np.vstack(out)


def load_data():
    tos_x, tos_y = load_unfair_tos("train")
    tos_vx, tos_vy = load_unfair_tos("validation")
    in_x, in_y, in_df = load_in("train")
    dev = group_holdout(in_df)
    tr_x = tos_x + [x for x, d in zip(in_x, dev) if not d] * IN_OVERSAMPLE
    tr_y = np.vstack([tos_y] + [in_y[~dev]] * IN_OVERSAMPLE)
    dev_x = tos_vx + [x for x, d in zip(in_x, dev) if d]
    dev_y = np.vstack([tos_vy, in_y[dev]])
    return tr_x, tr_y, dev_x, dev_y


def train(epochs=4, max_len=256, batch=16, lr=5e-5) -> None:
    set_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device={device}")
    tr_x, tr_y, dev_x, dev_y = load_data()

    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE, num_labels=len(LABELS), problem_type="multi_label_classification",
        id2label=dict(enumerate(LABELS)), label2id={l: i for i, l in enumerate(LABELS)},
    ).to(device)

    # give rare labels more weight
    pos = tr_y.sum(axis=0)
    pos_weight = torch.tensor(np.clip(np.sqrt((len(tr_y) - pos) / np.maximum(pos, 1)), 1.0, 15.0), dtype=torch.float32)
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))

    train_dl = make_loader(tr_x, tr_y, tok, max_len, batch, True)
    dev_dl = make_loader(dev_x, dev_y, tok, max_len, 64, False)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    steps = len(train_dl) * epochs
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
    scaler = torch.amp.GradScaler(enabled=device == "cuda")

    best_f1, best_state = -1.0, None
    for epoch in range(epochs):
        model.train()
        t0, total = time.time(), 0.0
        for b in train_dl:
            b = {k: v.to(device) for k, v in b.items()}
            labels = b.pop("labels")
            with torch.autocast(device, enabled=device == "cuda"):
                loss = loss_fn(model(**b).logits.float(), labels)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt)
            scaler.update()
            sched.step()
            opt.zero_grad()
            total += loss.item()
        f1 = f1_score(dev_y, (predict(model, dev_dl, device) >= 0.5).astype(int), average="micro", zero_division=0)
        print(f"epoch {epoch + 1}: loss {total / len(train_dl):.4f}, dev micro-F1 {f1:.4f} ({time.time() - t0:.0f}s)")
        if f1 > best_f1:
            best_f1, best_state = f1, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    # keep the best epoch and tune a threshold per label
    model.load_state_dict(best_state)
    thresholds = tune_thresholds(dev_y, predict(model, dev_dl, device))
    out = MODELS / "legalbert"
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out)
    tok.save_pretrained(out)
    (MODELS / "thresholds.json").write_text(json.dumps(thresholds, indent=2))
    print(f"saved to {out}, best dev micro-F1 {best_f1:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--max_len", type=int, default=256)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=5e-5)
    a = ap.parse_args()
    train(a.epochs, a.max_len, a.batch, a.lr)
