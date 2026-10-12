"""Five-bullet summary: TextRank over clause embeddings (or the LLM)."""

from typing import List

import numpy as np

from .llm import complete, parse_json
from .rag import embed

LLM_SYSTEM = (
    "Summarise this agreement for a student in exactly 5 short bullet points (max 25 words each). "
    "Use only facts in the text. Mention the riskiest points. "
    'Reply with JSON only: {"bullets": [str, str, str, str, str]}'
)


def _shorten(text: str, words: int = 40) -> str:
    parts = text.split()
    return text if len(parts) <= words else " ".join(parts[:words]) + "…"


def textrank(clauses: List[dict], n: int = 5) -> List[str]:
    """Pick the n most central clauses and keep their document order."""
    cands = [c for c in clauses if len(c["text"].split()) >= 10]
    if not cands:
        return [_shorten(c["text"]) for c in clauses[:n]]
    if len(cands) <= n:
        return [_shorten(c["text"]) for c in cands]
    vecs = embed([c["text"] for c in cands])
    sim = np.clip(vecs @ vecs.T, 0, None)
    np.fill_diagonal(sim, 0)
    rows = sim.sum(axis=1, keepdims=True)
    rows[rows == 0] = 1
    m = sim / rows
    score = np.ones(len(cands)) / len(cands)
    for _ in range(50):
        score = 0.15 / len(cands) + 0.85 * (m.T @ score)
    # small boost for risky clauses so the summary mentions them
    boost = np.array([1.0 + 0.4 * {"High": 2, "Medium": 1}.get(c.get("risk_level", ""), 0) for c in cands])
    top = sorted(np.argsort(-(score * boost))[:n])
    return [_shorten(cands[i]["text"]) for i in top]


def summarize(clauses: List[dict], use_llm: bool = False) -> List[str]:
    """Return five bullet strings."""
    if use_llm and clauses:
        text = "\n".join(f"{c['number']}. {c['text']}" for c in clauses)[:9000]
        data = parse_json(complete(LLM_SYSTEM, text))
        if data and isinstance(data.get("bullets"), list) and data["bullets"]:
            return [str(b) for b in data["bullets"][:5]]
    return textrank(clauses)
