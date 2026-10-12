"""PDF report download."""

import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session

from ..db import get_session
from ..reports.pdf import build_report
from .documents import get_doc_or_404, load_clauses

router = APIRouter(prefix="/api/documents", tags=["reports"])


@router.get("/{doc_id}/report.pdf")
def report(doc_id: int, session: Session = Depends(get_session)):
    doc = get_doc_or_404(session, doc_id)
    if doc.status != "done":
        raise HTTPException(409, "The document is still being analysed.")
    pdf = build_report(doc, load_clauses(session, doc_id))
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", doc.title)[:50] or "report"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="ClauseGuard_{safe}.pdf"'})
