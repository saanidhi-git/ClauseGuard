"""Full analysis pipeline: segment -> classify -> risk -> explain -> facts -> summary."""

import logging
import re
import time
from typing import List

from sqlmodel import Session, delete

from .config import llm_enabled
from .db import Clause, Document, engine
from .nlp import entities, explain, risk, segment, summarize
from .nlp.classify import ClauseClassifier
from .nlp.extract import Extracted

log = logging.getLogger("clauseguard.analyze")

# documents above this many words are analysed in a background job
BACKGROUND_WORDS = 6000


def detect_doc_type(text: str) -> str:
    """Guess rental / offer_letter / tos from keywords."""
    t = text.lower()
    scores = {
        "rental": len(re.findall(r"\b(rent|licensor|licensee|tenant|landlord|premises|leave and licen[cs]e)\b", t)),
        "offer_letter": len(re.findall(r"\b(employee|employment|salary|ctc|joining|probation|offer)\b", t)),
        "tos": len(re.findall(r"\b(user|users|account|service|services|app|platform|privacy|website)\b", t)) * 0.6,
    }
    return max(scores, key=scores.get)


def run_analysis(doc_id: int, extracted: Extracted, doc_type: str) -> None:
    """Analyse a document and store the results (safe to call in a background task)."""
    t0 = time.time()
    with Session(engine) as s:
        doc = s.get(Document, doc_id)
        if doc is None:
            return
        try:
            clauses = segment.segment(extracted.text, extracted.page_at)
            if not clauses:
                raise ValueError("No clauses could be found in this document.")
            clf = ClauseClassifier.get()
            preds = clf.predict([c["text"] for c in clauses], doc_type)
            use_llm = llm_enabled()

            scores: List[float] = []
            levels: List[str] = []
            s.exec(delete(Clause).where(Clause.document_id == doc_id))
            llm_budget = 12
            for c, p in zip(clauses, preds):
                score, level = risk.clause_risk(p["labels"], p["probs"])
                c["risk_level"] = level
                scores.append(score)
                levels.append(level)
                want_llm = use_llm and bool(p["labels"]) and llm_budget > 0
                if want_llm:
                    llm_budget -= 1
                exp = explain.explain(c["text"], p["labels"], p["probs"], use_llm=want_llm)
                s.add(Clause(document_id=doc_id, idx=c["id"], number=c["number"], heading=c.get("heading", ""), text=c["text"], page=c["page"],
                             labels=p["labels"], probs=p["probs"], risk_level=level, risk_score=score,
                             explanation=exp))

            doc.score = risk.document_score(scores)
            doc.verdict = risk.verdict(doc.score)
            doc.level_counts = risk.level_counts(levels)
            doc.key_facts = entities.extract_key_facts(clauses, doc_type)
            doc.summary = summarize.summarize(clauses, use_llm=use_llm)
            doc.model_used = clf.model_used
            doc.page_count = extracted.page_count
            doc.status = "done"
            log.info("Analysed document %s (%d clauses) in %.1fs", doc_id, len(clauses), time.time() - t0)
        except Exception as exc:
            log.exception("Analysis failed for %s", doc_id)
            doc.status = "error"
            doc.error = str(exc) if isinstance(exc, ValueError) else "Something went wrong while analysing this document."
        s.add(doc)
        s.commit()
