# Simple explanations for risky clauses

from typing import Dict, List

from .categories import CATEGORIES, SEVERITY_NAME
from .entities import clause_facts
from .llm import complete, parse_json

LLM_SYSTEM = (
    "You explain contract clauses to Indian students and freshers in plain English. "
    "Use ONLY facts stated in the clause. Do not invent amounts, dates or parties. "
    'Reply with JSON only: {"explanation": str, "why": str, "ask": str}. '
    "Each field at most 60 words. This is information, not legal advice."
)


def _fill(template: str, facts: Dict[str, str]) -> str:
    amount, period, percent = facts.get("amount"), facts.get("period"), facts.get("percent")
    return template.format(
        amount_part=f" ({amount})" if amount else "",
        period_part=f" ({period})" if period else "",
        percent_part=f" (by {percent})" if percent else "",
    )


# clearer sentence when we know the amount and period
def _special(label: str, facts: Dict[str, str]) -> str:
    amount, period = facts.get("amount"), facts.get("period")
    if label == "deposit_forfeiture" and amount and period:
        return f"You could lose the {amount} deposit if you leave before {period}."
    if label == "service_bond_lock_in" and amount and period:
        return f"If you leave within {period}, you may have to pay {amount}."
    if label == "rent_escalation" and facts.get("percent"):
        return f"The rent can go up by {facts['percent']} as decided in this clause."
    return ""


# explanation from the category template
def template_explanation(text: str, labels: List[str], probs: Dict[str, float]) -> dict:
    facts = clause_facts(text, labels[0] if labels else None)
    cats = [{
        "key": l, "name": CATEGORIES[l]["name"], "severity": SEVERITY_NAME[CATEGORIES[l]["severity"]],
        "probability": round(probs.get(l, 0.0), 3),
    } for l in labels]
    if not labels:
        return {"categories": [], "explanation": "", "why": "", "ask": "", "source": "none"}
    main = labels[0]
    parts = [_special(main, facts) or _fill(CATEGORIES[main]["explain"], facts)]
    if len(labels) > 1:
        others = ", ".join(CATEGORIES[l]["name"].lower() for l in labels[1:3])
        parts.append(f"It also looks like a {others} clause.")
    return {
        "categories": cats,
        "explanation": " ".join(parts),
        "why": CATEGORIES[main]["why"],
        "ask": CATEGORIES[main]["ask"],
        "facts": {k: v for k, v in facts.items() if v},
        "source": "template",
    }


# explanation, improved by the LLM if a key is set
def explain(text: str, labels: List[str], probs: Dict[str, float], use_llm: bool = False) -> dict:
    base = template_explanation(text, labels, probs)
    if not labels or not use_llm:
        return base
    names = ", ".join(CATEGORIES[l]["name"] for l in labels)
    data = parse_json(complete(LLM_SYSTEM, f"Risk categories: {names}\nClause: {text[:1500]}"))
    if data and all(isinstance(data.get(k), str) and data.get(k) for k in ("explanation", "why", "ask")):
        base.update({k: " ".join(data[k].split()[:60]) for k in ("explanation", "why", "ask")})
        base["source"] = "llm"
    return base
