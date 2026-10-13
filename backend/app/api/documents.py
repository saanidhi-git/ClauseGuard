# Upload, list, read and delete documents

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlmodel import Session, delete, select

from ..analyze import BACKGROUND_WORDS, detect_doc_type, run_analysis
from ..config import DISCLAIMER, MAX_UPLOAD_MB
from ..db import ChatMessage, Clause, Document, get_session, iso
from ..nlp import rag
from ..nlp.categories import CATEGORIES, DOC_TYPES
from ..nlp.extract import Extracted, ExtractError, extract, from_text, validate
from ..schemas import TextIn

router = APIRouter(prefix="/api/documents", tags=["documents"])

DOC_TYPE_NAMES = {"rental": "Rental agreement", "offer_letter": "Job offer letter", "tos": "Terms of Service"}


# save a new document and analyse it
def create_document(session: Session, extracted: Extracted, doc_type: str, title: str,
                    filename: Optional[str], background: Optional[BackgroundTasks]) -> Document:
    if doc_type not in DOC_TYPES:
        doc_type = detect_doc_type(extracted.text)
    doc = Document(title=title[:200] or "Untitled document", doc_type=doc_type, filename=filename,
                   status="processing", page_count=extracted.page_count)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    if background is not None and len(extracted.text.split()) > BACKGROUND_WORDS:
        background.add_task(run_analysis, doc.id, extracted, doc_type)
    else:
        run_analysis(doc.id, extracted, doc_type)
        session.refresh(doc)
        if doc.status == "error":
            raise HTTPException(422, doc.error or "Analysis failed.")
    return doc


def doc_summary(doc: Document) -> dict:
    return {
        "id": doc.id, "title": doc.title, "doc_type": doc.doc_type, "doc_type_name": DOC_TYPE_NAMES.get(doc.doc_type),
        "filename": doc.filename, "created_at": iso(doc.created_at), "score": doc.score,
        "verdict": doc.verdict, "status": doc.status, "level_counts": doc.level_counts,
    }


def clause_dict(c: Clause) -> dict:
    return {
        "id": c.idx, "number": c.number, "heading": c.heading, "text": c.text, "page": c.page, "labels": c.labels,
        "label_names": [CATEGORIES[l]["name"] for l in c.labels if l in CATEGORIES],
        "probs": c.probs, "risk_level": c.risk_level, "risk_score": c.risk_score, "explanation": c.explanation,
    }


def load_clauses(session: Session, doc_id: int) -> list:
    rows = session.exec(select(Clause).where(Clause.document_id == doc_id).order_by(Clause.idx)).all()
    return [clause_dict(c) for c in rows]


def get_doc_or_404(session: Session, doc_id: int) -> Document:
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found.")
    return doc


# upload a file or pasted text
@router.post("")
async def upload(request: Request, background: BackgroundTasks, session: Session = Depends(get_session)):
    ctype = request.headers.get("content-type", "")
    try:
        if ctype.startswith("multipart/form-data"):
            form = await request.form()
            doc_type = str(form.get("doc_type") or "auto")
            title = str(form.get("title") or "")
            file = form.get("file")
            if file is not None and hasattr(file, "read"):
                data = await file.read()
                if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
                    raise ExtractError(f"The file is larger than {MAX_UPLOAD_MB} MB.")
                if not data:
                    raise ExtractError("The uploaded file is empty.")
                extracted = extract(data, file.filename or "")
                filename = file.filename
                title = title or (filename or "Document").rsplit(".", 1)[0].replace("_", " ").title()
            else:
                extracted = validate(from_text(str(form.get("text") or "")))
                filename = None
        else:
            try:
                body = TextIn(**(await request.json()))
            except (ValidationError, ValueError):
                raise ExtractError("Please paste some text or upload a file.")
            extracted = validate(from_text(body.text))
            doc_type, title, filename = body.doc_type, body.title or "", None
    except ExtractError as exc:
        raise HTTPException(400, str(exc))
    if not title:
        first = extracted.text.strip().splitlines()[0][:80]
        title = first if len(first.split()) <= 12 else "Pasted document"
    doc = create_document(session, extracted, doc_type, title, filename, background)
    return {"document_id": doc.id, "status": doc.status}


@router.get("")
def list_documents(session: Session = Depends(get_session)):
    docs = session.exec(select(Document).order_by(Document.created_at.desc())).all()
    return [doc_summary(d) for d in docs]


@router.get("/{doc_id}")
def get_document(doc_id: int, session: Session = Depends(get_session)):
    doc = get_doc_or_404(session, doc_id)
    out = doc_summary(doc)
    out.update({
        "error": doc.error, "key_facts": doc.key_facts, "summary": doc.summary, "model_used": doc.model_used,
        "page_count": doc.page_count, "clauses": load_clauses(session, doc_id) if doc.status == "done" else [],
        "disclaimer": DISCLAIMER,
    })
    return out


@router.delete("/{doc_id}")
def delete_document(doc_id: int, session: Session = Depends(get_session)):
    doc = get_doc_or_404(session, doc_id)
    session.exec(delete(Clause).where(Clause.document_id == doc_id))
    session.exec(delete(ChatMessage).where(ChatMessage.document_id == doc_id))
    session.delete(doc)
    session.commit()
    rag.drop_index(doc_id)
    return {"ok": True}
