"""Risk categories used by ClauseGuard (8 from UNFAIR-ToS + 6 India-specific)."""

from typing import Dict, List

UNFAIR_TOS_LABELS: List[str] = [
    "limitation_of_liability",
    "unilateral_termination",
    "unilateral_change",
    "content_removal",
    "contract_by_using",
    "choice_of_law",
    "jurisdiction",
    "arbitration",
]

INDIA_LABELS: List[str] = [
    "service_bond_lock_in",
    "deposit_forfeiture",
    "one_sided_notice",
    "rent_escalation",
    "non_compete",
    "broad_data_sharing",
]

LABELS: List[str] = UNFAIR_TOS_LABELS + INDIA_LABELS

DOC_TYPES: List[str] = ["rental", "offer_letter", "tos"]

ALL = ["rental", "offer_letter", "tos"]

CATEGORIES: Dict[str, dict] = {
    "limitation_of_liability": {
        "name": "Limitation of liability",
        "severity": 2,
        "doc_types": ALL,
        "explain": "The other side limits or removes its responsibility if something goes wrong{amount_part}.",
        "why": "If you suffer a loss because of their mistake, you may not be able to claim compensation.",
        "ask": "Will you be responsible if my loss is caused by your negligence?",
    },
    "unilateral_termination": {
        "name": "Unilateral termination",
        "severity": 3,
        "doc_types": ALL,
        "explain": "The other side can end the agreement or your access on its own, sometimes without a reason.",
        "why": "You could lose the house, job or service suddenly, with little time to arrange an alternative.",
        "ask": "Can you add a clear reason and a fair notice period before termination?",
    },
    "unilateral_change": {
        "name": "Unilateral change",
        "severity": 2,
        "doc_types": ALL,
        "explain": "The other side can change the terms later without needing your agreement.",
        "why": "What you sign today may not be what you are bound by tomorrow.",
        "ask": "Will changes need my written consent, and can I exit if I disagree?",
    },
    "content_removal": {
        "name": "Content removal",
        "severity": 1,
        "doc_types": ["tos"],
        "explain": "The service can delete your content or account at its discretion.",
        "why": "Your posts, files or data could disappear without warning or appeal.",
        "ask": "Will I get notice and a chance to download my data before removal?",
    },
    "contract_by_using": {
        "name": "Contract by using",
        "severity": 1,
        "doc_types": ["tos"],
        "explain": "Simply using the app or website counts as accepting all these terms.",
        "why": "You may be bound by terms you never actually read or clicked to accept.",
        "ask": "Where can I read the full terms before I start using the service?",
    },
    "choice_of_law": {
        "name": "Choice of law",
        "severity": 1,
        "doc_types": ALL,
        "explain": "Disputes will be decided under the laws of a place chosen by the other side.",
        "why": "Foreign or unfamiliar law can make it harder for you to protect your rights.",
        "ask": "Can Indian law, or the law of my state, apply instead?",
    },
    "jurisdiction": {
        "name": "Jurisdiction",
        "severity": 2,
        "doc_types": ALL,
        "explain": "Any case must be filed only in courts at a location chosen by the other side.",
        "why": "Travelling to a distant court makes it costly and difficult to take action.",
        "ask": "Can disputes be heard in the city where I live or work?",
    },
    "arbitration": {
        "name": "Arbitration",
        "severity": 2,
        "doc_types": ALL,
        "explain": "Disputes go to private arbitration instead of a regular court.",
        "why": "Arbitration can be expensive, and you may give up the right to go to court or join a group case.",
        "ask": "Who chooses the arbitrator and who pays the arbitration costs?",
    },
    "service_bond_lock_in": {
        "name": "Service bond / lock-in",
        "severity": 3,
        "doc_types": ["rental", "offer_letter"],
        "explain": "You must stay for a fixed period{period_part} or pay a penalty{amount_part} if you leave early.",
        "why": "Leaving early, even for a better opportunity or a genuine problem, could cost you a large sum.",
        "ask": "Is the penalty reduced pro-rata for the time I have already served?",
    },
    "deposit_forfeiture": {
        "name": "Deposit forfeiture",
        "severity": 3,
        "doc_types": ["rental"],
        "explain": "You may lose your security deposit{amount_part} in situations decided by the other side.",
        "why": "The deposit is often several months of rent, and getting it back later is hard.",
        "ask": "Which exact deductions are allowed, and when will the deposit be refunded?",
    },
    "one_sided_notice": {
        "name": "One-sided notice",
        "severity": 2,
        "doc_types": ["rental", "offer_letter"],
        "explain": "The notice period is not equal: you must give longer notice{period_part} than the other side.",
        "why": "You may be stuck for months while the other side can end things quickly.",
        "ask": "Can both sides have the same notice period?",
    },
    "rent_escalation": {
        "name": "Rent escalation",
        "severity": 2,
        "doc_types": ["rental"],
        "explain": "The rent can increase during or after the term{percent_part}.",
        "why": "Steep or open-ended increases can make the place unaffordable later.",
        "ask": "Can the increase be capped at a fixed percentage once a year?",
    },
    "non_compete": {
        "name": "Non-compete",
        "severity": 2,
        "doc_types": ["offer_letter"],
        "explain": "You are restricted from joining competitors or working on similar work{period_part}.",
        "why": "It can limit your next job options; post-employment non-competes are generally unenforceable in India, but can still be used to pressure you.",
        "ask": "Can this be limited to the employment period only, or removed?",
    },
    "broad_data_sharing": {
        "name": "Broad data sharing",
        "severity": 2,
        "doc_types": ["tos", "offer_letter"],
        "explain": "Your personal data can be shared with third parties for wide or unclear purposes.",
        "why": "Your contacts, location or usage data may reach advertisers or partners you never chose.",
        "ask": "Exactly who receives my data, and can I opt out?",
    },
}

SEVERITY_NAME = {3: "High", 2: "Medium", 1: "Low"}


def labels_for_doc_type(doc_type: str) -> List[str]:
    """Return the labels that make sense for a document type."""
    return [k for k in LABELS if doc_type in CATEGORIES[k]["doc_types"]]
