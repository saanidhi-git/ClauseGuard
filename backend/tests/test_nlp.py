"""Unit tests for segmentation, entity extraction and risk scoring."""

from app.nlp.entities import clause_facts, extract_key_facts
from app.nlp.extract import ExtractError, from_text, validate
from app.nlp.risk import clause_risk, document_score
from app.nlp.segment import segment

DOC = """RENTAL AGREEMENT
This agreement is made at Pune between Mr. Ramesh Kulkarni and Mr. Rohan Patil.
1. RENT
1.1 The Licensee shall pay a monthly licence fee of Rs. 18,000 per month on or before the 5th day.
1.2 The Licensee has paid an interest-free refundable security deposit of Rs. 54,000.
2. LOCK-IN
There shall be a lock-in period of 6 months during which the Licensee cannot terminate this agreement.
3. NOTICE
The Licensee shall give three months' written notice, whereas the Licensor may end it with 15 days' notice.
"""


def test_segment_numbered_clauses():
    clauses = segment(DOC)
    numbers = [c["number"] for c in clauses]
    assert "1.1" in numbers and "1.2" in numbers and "2" in numbers and "3" in numbers
    assert all(c["text"] for c in clauses)


def test_segment_merges_short_headings():
    clauses = segment(DOC)
    # "1. RENT" is too short on its own, so it joins clause 1.1
    assert not any(c["text"].strip() == "RENT" for c in clauses)


def test_segment_fallback_to_sentences():
    text = "This app collects your data. We may share it with partners. You can delete your account anytime."
    clauses = segment(text)
    assert len(clauses) >= 1
    assert segment("") == []


def test_segment_splits_long_clause():
    long = "1. " + " ".join(["The tenant shall keep the premises clean and tidy at all times."] * 30)
    clauses = segment(long + "\n2. Short second clause about rent payment here.\n3. Third clause about the notice period.")
    assert all(len(c["text"].split()) <= 130 for c in clauses)


def test_key_facts():
    clauses = segment(DOC)
    facts = extract_key_facts(clauses, "rental")
    assert facts["rent"]["value"].startswith("Rs. 18,000")
    assert facts["deposit"]["value"] == "Rs. 54,000"
    assert facts["lock_in"]["value"] == "6 months"
    assert facts["notice_period"]["value"] == "three months"


def test_clause_facts_amounts_and_durations():
    f = clause_facts("You must serve for two (2) years or pay ₹2,00,000 as bond amount.")
    assert f["amount"] == "₹2,00,000"
    assert f["period"] == "two (2) years"


def test_risk_levels():
    assert clause_risk([], {}) == (0.0, "Safe")
    assert clause_risk(["deposit_forfeiture"], {"deposit_forfeiture": 0.9})[1] == "High"
    assert clause_risk(["arbitration"], {"arbitration": 0.9})[1] == "Medium"
    assert clause_risk(["contract_by_using"], {"contract_by_using": 0.9})[1] == "Low"


def test_document_score_range_and_order():
    assert document_score([]) == 0
    one_bad = document_score([2.7])
    many_bad = document_score([2.7, 2.7, 2.4, 1.8])
    assert 0 < one_bad < many_bad <= 100
    # safe clauses must not dilute the score
    assert document_score([2.7] + [0.0] * 50) == one_bad


def test_empty_text_rejected():
    try:
        validate(from_text("   "))
    except ExtractError:
        return
    raise AssertionError("empty text should be rejected")
