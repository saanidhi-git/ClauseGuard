"""Key facts extraction: spaCy NER + regex rules for Indian agreements."""

import re
from typing import Dict, List, Optional

from .preprocess import get_nlp

NUM_WORDS = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|eighteen|twenty|twenty-four|thirty|sixty|ninety"

MONEY_RE = re.compile(
    r"(?:₹|Rs\.?|INR)\s?\d{1,3}(?:,\d{2,3})*(?:\.\d+)?(?:\s?/-)?(?:\s?(?:lakhs?|lacs?|crores?))?"
    r"|\d{1,3}(?:,\d{2,3})*(?:\.\d+)?\s?(?:lakhs?|lacs?)\b",
    re.I,
)
DURATION_RE = re.compile(
    rf"\b(?:\d{{1,3}}|{NUM_WORDS})(?:\s*\((?:\d{{1,3}}|{NUM_WORDS})\))?[\s-]*(?:calendar\s+)?(?:days?|weeks?|months?|years?)\b",
    re.I,
)
PERCENT_RE = re.compile(r"\b\d{1,2}(?:\.\d+)?\s?(?:%|percent|per cent)", re.I)

FACT_RULES = [
    # (fact key, clause keywords, value type)
    ("rent", r"\b(monthly rent|rent of|licen[cs]e fee|rent shall|rent payable|monthly compensation|as rent|rent amount|rent is)\b", "money"),
    ("deposit", r"\b(security deposit|deposit of|interest[- ]free deposit|refundable deposit)\b", "money"),
    ("salary", r"\b(ctc|cost to company|annual compensation|gross salary|annual salary|fixed pay)\b", "money"),
    ("penalty", r"\b(penalty|liquidated damages|bond amount|pay the company|pay an amount|forfeit)\b", "money"),
    ("lock_in", r"\b(lock[- ]in)\b", "duration"),
    ("bond_period", r"\b(service bond|service agreement|bond period|serve the company|minimum period of service)\b", "duration"),
    ("notice_period", r"\b(notice period|prior notice|notice of|written notice|days' notice|months' notice)", "notice"),
    ("probation", r"\bprobation\b", "duration"),
    ("term", r"\b(period of|term of|tenure of|valid for)\b", "duration"),
    ("rent_increase", r"\b(increase|escalat|enhance|revis)\w*", "percent"),
]

FACT_LABELS = {
    "rent": "Rent", "deposit": "Security deposit", "salary": "Salary / CTC", "penalty": "Penalty / bond amount",
    "lock_in": "Lock-in period", "bond_period": "Service bond period", "notice_period": "Notice period",
    "term": "Agreement term", "rent_increase": "Rent increase", "parties": "Parties", "start_date": "Start date",
    "location": "Location", "probation": "Probation period",
}

UNIT_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}
WORD_NUM = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}


def _first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(0).strip() if m else None


def _days(duration: str) -> float:
    """Rough length of a duration in days, used to compare notice periods."""
    m = re.match(r"(\d+|[a-z-]+)", duration.lower())
    num = m.group(1) if m else "1"
    n = float(num) if num.isdigit() else WORD_NUM.get(num, 1)
    unit = next((d for u, d in UNIT_DAYS.items() if u in duration.lower()), 1)
    return n * unit


def notice_period(text: str) -> Optional[str]:
    """Longest duration mentioned close to the word 'notice' (the one you must give)."""
    near = [m.group(0).strip() for m in DURATION_RE.finditer(text)
            if re.search(r"notice", text[max(0, m.start() - 40):m.end() + 40], re.I)]
    return max(near, key=_days) if near else None


def clause_facts(text: str, label: Optional[str] = None) -> Dict[str, Optional[str]]:
    """First amount, duration and percentage in a single clause."""
    period = notice_period(text) if label == "one_sided_notice" else None
    return {"amount": _first(MONEY_RE, text), "period": period or _first(DURATION_RE, text),
            "percent": _first(PERCENT_RE, text)}


def _value(kind: str, text: str) -> Optional[str]:
    if kind == "money":
        val = _first(MONEY_RE, text)
        if val and re.search(r"per month|monthly|every month|/month|p\.m\.", text, re.I) and not re.search(r"deposit", text, re.I):
            val += " per month"
        return val
    if kind == "duration":
        return _first(DURATION_RE, text)
    if kind == "notice":
        return notice_period(text)
    return _first(PERCENT_RE, text)


def _parties(clauses: List[dict], doc_ents: List[tuple]) -> List[str]:
    head = " ".join(c["text"] for c in clauses[:4])
    found: List[str] = []
    for m in re.finditer(r"(?:between|by and between)\s+(.{3,90}?)\s*(?:,|\(|hereinafter)", head, re.I):
        found.append(m.group(1))
    for m in re.finditer(r"\band\s+((?:M/s\.?\s+)?[A-Z][\w.&]*(?:\s+[A-Z][\w.&]*){0,5})\s*(?:,|\(|hereinafter)", head):
        found.append(m.group(1))
    for text, label, cid in doc_ents:
        if cid >= 4 or len(text) <= 3:
            continue
        if label == "PERSON" or (label == "ORG" and re.search(r"\b(pvt|ltd|llp|limited|inc|corp)\b", text, re.I)):
            found.append(text)
    for m in re.finditer(r"[A-Z][\w&]*(?:\s+[A-Z][\w&]*){0,4}\s+(?:Pvt\.?\s+Ltd|Private Limited|LLP|Limited)\.?", head):
        found.append(m.group(0))

    junk = r"\b(agreement|licensor|licensee|hereinafter|terms|policy|society|apartments?|residency|residence|heights|towers?|nagar|park|road|floor|dear)\b"
    clean: List[str] = []
    for p in found:
        p = re.sub(r"\s+", " ", p.strip(" ,.;:"))
        if not 3 < len(p) < 80 or re.search(junk, p, re.I) or p.isupper():
            continue
        bare = re.sub(r"^(mr|mrs|ms|shri|smt|dr|m/s)\.?\s+", "", p, flags=re.I).lower().rstrip(".")
        dup = next((i for i, q in enumerate(clean) if bare in q.lower() or q.lower().rstrip(".").endswith(bare)), None)
        if dup is None and not any(re.sub(r"^(mr|mrs|ms|shri|smt|dr|m/s)\.?\s+", "", q, flags=re.I).lower().rstrip(".") in bare for q in clean):
            clean.append(p)
    return clean[:4]


def extract_key_facts(clauses: List[dict], doc_type: str) -> Dict[str, dict]:
    """Return {fact: {label, value, clause_id}} for the document."""
    facts: Dict[str, dict] = {}
    for c in clauses:
        text = c["text"]
        for key, kw, kind in FACT_RULES:
            if key in facts or not re.search(kw, text, re.I):
                continue
            if key == "rent_increase" and doc_type != "rental":
                continue
            if key in {"rent", "deposit"} and doc_type != "rental":
                continue
            if key == "salary" and doc_type != "offer_letter":
                continue
            if (key == "term" and doc_type == "offer_letter") or (key == "probation" and doc_type != "offer_letter"):
                continue
            val = _value(kind, text)
            if val:
                facts[key] = {"label": FACT_LABELS[key], "value": val, "clause_id": c["id"]}

    nlp = get_nlp()
    ents: List[tuple] = []
    start_date = None
    location = None
    texts = [c["text"][:1500] for c in clauses]
    for c, doc in zip(clauses, nlp.pipe(texts, batch_size=32)):
        for e in doc.ents:
            ents.append((e.text, e.label_, c["id"]))
            if e.label_ == "DATE" and start_date is None and re.search(
                    r"commenc|effective|joining|start|from", c["text"], re.I) and re.search(r"\d|19|20", e.text):
                start_date = {"label": FACT_LABELS["start_date"], "value": e.text, "clause_id": c["id"]}
            if e.label_ == "GPE" and location is None and c["id"] < 6:
                location = {"label": FACT_LABELS["location"], "value": e.text, "clause_id": c["id"]}

    parties = _parties(clauses, ents)
    if parties:
        facts["parties"] = {"label": FACT_LABELS["parties"], "value": parties, "clause_id": clauses[0]["id"]}
    if start_date:
        facts["start_date"] = start_date
    if location:
        facts["location"] = location
    return facts
