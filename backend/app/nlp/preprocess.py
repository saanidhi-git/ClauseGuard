"""Text normalisation, tokenization, stopwords and lemmatization."""

import re
import unicodedata
from functools import lru_cache
from typing import Dict, List


@lru_cache(maxsize=1)
def get_nlp():
    """Load spaCy once (with a blank fallback if the model is missing)."""
    import spacy

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
    return nlp


@lru_cache(maxsize=1)
def _stopwords() -> set:
    try:
        from nltk.corpus import stopwords

        words = set(stopwords.words("english"))
    except LookupError:
        words = set(get_nlp().Defaults.stop_words)
    # keep words that change legal meaning
    return words - {"not", "no", "nor", "without", "against", "any", "all", "only", "before", "after"}


def normalize(text: str) -> str:
    """Lowercase, unify unicode, map currency symbols and squeeze spaces."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("₹", " inr ").replace("Rs.", " inr ").replace("Rs ", " inr ")
    text = text.lower()
    text = re.sub(r"[“”\"'`]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)?|\d+(?:[.,]\d+)*")


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(normalize(text))


@lru_cache(maxsize=1)
def _lemmatizer():
    try:
        from nltk.stem import WordNetLemmatizer

        lem = WordNetLemmatizer()
        lem.lemmatize("tests")  # triggers LookupError early if wordnet is missing
        return lem
    except LookupError:
        return None


def lemmatize_tokens(tokens: List[str]) -> List[str]:
    lem = _lemmatizer()
    if lem is None:
        return tokens
    out = []
    for t in tokens:
        w = lem.lemmatize(t, pos="v")
        out.append(lem.lemmatize(w, pos="n"))
    return out


def clean_for_model(text: str) -> str:
    """Pipeline used by the baseline: normalise, tokenize, drop stopwords, lemmatize."""
    stops = _stopwords()
    tokens = [t for t in tokenize(text) if t not in stops and len(t) > 1]
    return " ".join(lemmatize_tokens(tokens))


def analyze_steps(text: str) -> Dict[str, list]:
    """Show every preprocessing step (for the Model Insights page)."""
    text = (text or "")[:2000]
    doc = get_nlp()(text)
    tokens = tokenize(text)
    stops = _stopwords()
    no_stop = [t for t in tokens if t not in stops and len(t) > 1]
    return {
        "normalized": [normalize(text)],
        "tokens": tokens,
        "without_stopwords": no_stop,
        "lemmas": lemmatize_tokens(no_stop),
        "pos": [{"text": t.text, "pos": t.pos_ or "-"} for t in doc if not t.is_space][:80],
        "entities": [{"text": e.text, "label": e.label_} for e in doc.ents],
    }


SENT_RE = re.compile(r"(?<=[.;!?])\s+(?=[A-Z(\"“])")


def split_sentences(text: str) -> List[str]:
    """Fast regex sentence splitter (spaCy is used for heavier work)."""
    parts = [p.strip() for p in SENT_RE.split(text) if p.strip()]
    return parts or [text.strip()]
