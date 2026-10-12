"""Ask questions about a document: MiniLM embeddings + FAISS retrieval (+ optional LLM)."""

import logging
import re
import threading
from collections import OrderedDict
from functools import lru_cache
from typing import List, Optional

import numpy as np

from ..config import EMBED_MODEL, DISABLE_TRANSFORMERS
from .llm import complete

log = logging.getLogger("clauseguard.rag")
_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_embedder():
    """Load MiniLM once; returns None if it is not available."""
    if DISABLE_TRANSFORMERS:
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(EMBED_MODEL, device="cpu")
    except Exception as exc:
        log.warning("Embedding model not available, using TF-IDF retrieval: %s", exc)
        return None


def embed(texts: List[str]) -> np.ndarray:
    """Normalised embeddings (MiniLM, or TF-IDF vectors as a fallback)."""
    model = get_embedder()
    if model is not None:
        with _lock:
            vecs = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype="float32")
    from sklearn.feature_extraction.text import HashingVectorizer

    hv = HashingVectorizer(n_features=2048, ngram_range=(1, 2), stop_words="english", norm="l2")
    return hv.transform(texts).toarray().astype("float32")


class DocIndex:
    def __init__(self, clauses: List[dict]):
        import faiss

        self.clauses = clauses
        vecs = embed([c["text"] for c in clauses]) if clauses else np.zeros((0, 384), dtype="float32")
        self.index = faiss.IndexFlatIP(vecs.shape[1])
        if len(vecs):
            self.index.add(vecs)

    def search(self, question: str, k: int = 3) -> List[tuple]:
        if not self.clauses:
            return []
        q = embed([question])
        scores, ids = self.index.search(q, min(k, len(self.clauses)))
        return [(self.clauses[i], float(s)) for s, i in zip(scores[0], ids[0]) if i >= 0]


_indexes: "OrderedDict[int, DocIndex]" = OrderedDict()


def get_index(doc_id: int, clauses: List[dict]) -> DocIndex:
    """Per-document FAISS index, cached in memory (last 20 documents)."""
    idx = _indexes.get(doc_id)
    if idx is None or len(idx.clauses) != len(clauses):
        idx = DocIndex(clauses)
        _indexes[doc_id] = idx
        while len(_indexes) > 20:
            _indexes.popitem(last=False)
    _indexes.move_to_end(doc_id)
    return idx


def drop_index(doc_id: int) -> None:
    _indexes.pop(doc_id, None)


def _highlight(clause_text: str, question: str) -> str:
    """Pick the sentence in a clause that best matches the question."""
    parts = re.split(r"(?<!Rs\.)(?<!No\.)(?<!Mr\.)(?<!Ms\.)(?<=[.;])\s+(?=[A-Za-z(])", clause_text)
    sents = [s for s in parts if len(s.split()) > 3] or [clause_text]
    if len(sents) == 1:
        return sents[0]
    vecs = embed(sents + [question])
    sims = vecs[:-1] @ vecs[-1]
    return sents[int(np.argmax(sims))]


RAG_SYSTEM = (
    "You answer questions about one agreement using ONLY the clauses given. "
    "Cite clause numbers like [Clause 4]. If the clauses do not answer the question, reply exactly: "
    "\"The document doesn't say.\" Keep it under 90 words, plain English, no legal advice."
)


def ask(doc_id: int, clauses: List[dict], question: str, use_llm: bool = False) -> dict:
    """Retrieve top-3 clauses and answer (LLM) or show highlighted matches (no LLM)."""
    question = (question or "").strip()[:500]
    hits = get_index(doc_id, clauses).search(question, k=3)
    matches = [{
        "clause_id": c["id"], "number": c["number"], "score": round(s, 3),
        "highlight": _highlight(c["text"], question), "text": c["text"],
    } for c, s in hits]

    answer: Optional[str] = None
    if use_llm and matches:
        ctx = "\n\n".join(f"[Clause {m['number']}] {m['text'][:1200]}" for m in matches)
        answer = complete(RAG_SYSTEM, f"Clauses:\n{ctx}\n\nQuestion: {question}", use_cache=False)
    mode = "llm" if answer else "retrieval"
    if not answer:
        if not matches or matches[0]["score"] < 0.2:
            answer = "I couldn't find a clause that clearly answers this. The document may not say."
        else:
            lines = [f"• Clause {m['number']}: \"{m['highlight']}\"" for m in matches]
            answer = "These clauses are the most relevant to your question:\n" + "\n".join(lines)
    cited = [m["clause_id"] for m in matches]
    if mode == "llm":
        nums = set(re.findall(r"Clause\s+([\w.() ]+?)\]", answer))
        cited = [m["clause_id"] for m in matches if m["number"] in nums] or cited
    return {"answer": answer.strip(), "cited_clause_ids": cited, "matches": matches, "mode": mode}
