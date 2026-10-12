"""Ask ClauseGuard: questions about a document."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..config import llm_enabled
from ..db import ChatMessage, get_session, iso
from ..nlp import rag
from ..schemas import AskIn
from .documents import get_doc_or_404, load_clauses

router = APIRouter(prefix="/api/documents", tags=["chat"])


def _msg(m: ChatMessage) -> dict:
    return {"id": m.id, "role": m.role, "content": m.content, "cited_clause_ids": m.cited_clause_ids,
            "created_at": iso(m.created_at)}


@router.post("/{doc_id}/ask")
def ask(doc_id: int, body: AskIn, session: Session = Depends(get_session)):
    doc = get_doc_or_404(session, doc_id)
    if doc.status != "done":
        raise HTTPException(409, "The document is still being analysed.")
    clauses = load_clauses(session, doc_id)
    result = rag.ask(doc_id, clauses, body.question, use_llm=llm_enabled())
    session.add(ChatMessage(document_id=doc_id, role="user", content=body.question.strip()))
    session.add(ChatMessage(document_id=doc_id, role="assistant", content=result["answer"],
                            cited_clause_ids=result["cited_clause_ids"]))
    session.commit()
    return result


@router.get("/{doc_id}/chat")
def chat_history(doc_id: int, session: Session = Depends(get_session)):
    get_doc_or_404(session, doc_id)
    rows = session.exec(select(ChatMessage).where(ChatMessage.document_id == doc_id).order_by(ChatMessage.id)).all()
    return [_msg(m) for m in rows]
