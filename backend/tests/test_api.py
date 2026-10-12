"""API smoke tests on the three built-in samples."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


@pytest.mark.parametrize("name,expected", [
    ("rental_agreement", "deposit_forfeiture"),
    ("offer_letter", "service_bond_lock_in"),
    ("app_terms", "arbitration"),
])
def test_samples_end_to_end(client, name, expected):
    r = client.post(f"/api/samples/{name}/analyze")
    assert r.status_code == 200
    doc_id = r.json()["document_id"]
    d = client.get(f"/api/documents/{doc_id}").json()
    assert d["status"] == "done"
    assert 0 <= d["score"] <= 100
    assert len(d["summary"]) >= 1
    labels = {l for c in d["clauses"] for l in c["labels"]}
    assert expected in labels
    # a ToS must never get rental-only labels
    if name == "app_terms":
        assert "rent_escalation" not in labels and "deposit_forfeiture" not in labels

    a = client.post(f"/api/documents/{doc_id}/ask", json={"question": "What happens if I leave early?"})
    assert a.status_code == 200 and a.json()["cited_clause_ids"]
    assert len(client.get(f"/api/documents/{doc_id}/chat").json()) == 2

    pdf = client.get(f"/api/documents/{doc_id}/report.pdf")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"


def test_paste_text_and_delete(client):
    text = "1. The Company may terminate your account at any time without notice.\n2. You agree to arbitration in Singapore for all disputes.\n3. We may share your data with advertisers and partners."
    r = client.post("/api/documents", json={"text": text, "doc_type": "tos", "title": "Pasted"})
    assert r.status_code == 200
    doc_id = r.json()["document_id"]
    assert any(d["id"] == doc_id for d in client.get("/api/documents").json())
    assert client.delete(f"/api/documents/{doc_id}").json()["ok"]
    assert client.get(f"/api/documents/{doc_id}").status_code == 404


def test_friendly_errors(client):
    assert client.post("/api/documents", json={"text": "  ", "doc_type": "tos"}).status_code == 400
    r = client.post("/api/documents", files={"file": ("x.exe", b"MZ....", "application/octet-stream")})
    assert r.status_code == 400 and "Unsupported" in r.json()["detail"]
    r = client.post("/api/documents", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert r.status_code == 400


def test_insights(client):
    r = client.get("/api/insights").json()
    assert r["model_used"]
    c = client.post("/api/insights/classify", json={"text": "We may change these terms at any time without notice."}).json()
    assert c["models"] and c["preprocessing"]["tokens"]
