"""Built-in demo documents."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..config import SAMPLES_DIR
from ..db import get_session
from ..nlp.extract import extract
from .documents import create_document

router = APIRouter(prefix="/api/samples", tags=["samples"])

# kind: "risky" samples show red flags, "fair" samples show what a balanced document looks like
SAMPLES = {
    "rental_agreement": {"title": "Leave and Licence Agreement (Pune)", "doc_type": "rental", "kind": "risky",
                         "description": "11-month flat rental in Pune with lock-in and deposit terms"},
    "offer_letter": {"title": "Software Engineer Offer Letter", "doc_type": "offer_letter", "kind": "risky",
                     "description": "Fresher offer with a 2-year service bond and non-compete"},
    "app_terms": {"title": "App Terms of Service & Privacy", "doc_type": "tos", "kind": "risky",
                  "description": "Social app terms with arbitration and data sharing"},
    "rental_agreement_fair": {"title": "Fair Rental Agreement (Baner)", "doc_type": "rental", "kind": "fair",
                              "description": "Equal notice, full deposit refund, capped rent increase"},
    "offer_letter_fair": {"title": "Fair Offer Letter (Trainee)", "doc_type": "offer_letter", "kind": "fair",
                          "description": "No bond, equal 30-day notice, company-paid training"},
}


def _sample_file(name: str):
    for ext in (".pdf", ".txt"):
        path = SAMPLES_DIR / f"{name}{ext}"
        if path.exists():
            return path
    return None


@router.get("")
def list_samples():
    return [{"name": k, **v, "available": _sample_file(k) is not None} for k, v in SAMPLES.items()]


@router.post("/{name}/analyze")
def analyze_sample(name: str, session: Session = Depends(get_session)):
    meta = SAMPLES.get(name)
    path = _sample_file(name) if meta else None
    if path is None:
        raise HTTPException(404, "Sample not found.")
    extracted = extract(path.read_bytes(), path.name)
    doc = create_document(session, extracted, meta["doc_type"], meta["title"], path.name, None)
    return {"document_id": doc.id, "status": doc.status}
