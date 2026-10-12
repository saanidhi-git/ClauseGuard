"""Split a document into clauses."""

import re
from typing import Callable, List, Optional

from .preprocess import split_sentences

HEADING_RE = re.compile(
    r"""^\s*(
        (?:clause|article|section)\s+\d+[a-z]?(?:\.\d+)*\s*[.:)\-]?   # Clause 5 / Article 2
      | \d{1,2}(?:\.\d{1,2}){1,3}\.?(?=\s) | \d{1,2}[.)](?=\s)        # 1. / 1.1 / 2)
      | \([a-z]\)|[a-z]\)                                             # (a) / a)
      | \((?:i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii)\)|(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\)  # (iv) / iv)
    )\s*""",
    re.I | re.X,
)

# leading ALL-CAPS heading such as "SECURITY DEPOSIT The Licensee..."
HEAD_WORDS_RE = re.compile(r"^((?:[A-Z0-9-][A-Z0-9&/,'().\-]*\s+){0,8}[A-Z][A-Z&/,'().\-]+)\s+(?=[A-Z][a-z])")

MIN_WORDS = 6
MAX_WORDS = 120


def _words(text: str) -> int:
    return len(text.split())


def _numbered_blocks(text: str) -> List[dict]:
    """Group lines into blocks that start at a numbered heading."""
    blocks: List[dict] = []
    pos = 0
    current: Optional[dict] = None
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        start = pos
        pos += len(line)
        if not stripped:
            continue
        m = HEADING_RE.match(line)
        if m:
            current = {"number": m.group(1).strip().rstrip(".:-"), "start": start, "end": pos,
                       "text": line[m.end():].strip()}
            blocks.append(current)
        elif current is None:
            current = {"number": "", "start": start, "end": pos, "text": stripped}
            blocks.append(current)
        else:
            current["text"] += " " + stripped
            current["end"] = pos
    return blocks


def _sentence_blocks(text: str) -> List[dict]:
    """Fallback: paragraphs, then sentences."""
    blocks = []
    for m in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", text):
        para = m.group(0)
        offset = m.start()
        for sent in split_sentences(para.replace("\n", " ")):
            idx = text.find(sent[:30], offset)
            start = idx if idx >= 0 else offset
            blocks.append({"number": "", "start": start, "end": start + len(sent), "text": sent})
            offset = start + 1
    return blocks


def _merge_short(blocks: List[dict]) -> List[dict]:
    """Merge very short blocks (like headings) into the following block."""
    out: List[dict] = []
    carry: Optional[dict] = None
    for b in blocks:
        if carry:
            b = {"number": b["number"] or carry["number"], "start": carry["start"], "end": b["end"],
                 "text": f"{carry['text']} {b['text']}".strip()}
            carry = None
        if _words(b["text"]) < MIN_WORDS:
            carry = b
            continue
        out.append(b)
    if carry:
        if out:
            out[-1]["text"] += " " + carry["text"]
            out[-1]["end"] = carry["end"]
        else:
            out.append(carry)
    return out


def _split_long(blocks: List[dict]) -> List[dict]:
    """Split very long blocks at sentence boundaries."""
    out = []
    for b in blocks:
        if _words(b["text"]) <= MAX_WORDS:
            out.append(b)
            continue
        chunk: List[str] = []
        part = 0
        for sent in split_sentences(b["text"]):
            if chunk and _words(" ".join(chunk + [sent])) > MAX_WORDS:
                out.append({**b, "number": f"{b['number']}" + (f" (part {part + 1})" if b["number"] else ""), "text": " ".join(chunk)})
                part += 1
                chunk = []
            chunk.append(sent)
        if chunk:
            label = f"{b['number']} (part {part + 1})" if b["number"] and part else b["number"]
            out.append({**b, "number": label, "text": " ".join(chunk)})
    return out


def segment(text: str, page_at: Optional[Callable[[int], int]] = None) -> List[dict]:
    """Return [{id, number, text, page, start, end}] for the document."""
    if not text or not text.strip():
        return []
    blocks = _numbered_blocks(text)
    numbered = sum(1 for b in blocks if b["number"])
    if numbered < 3:
        blocks = _sentence_blocks(text)
    blocks = _split_long(_merge_short(blocks))
    clauses = []
    for i, b in enumerate(blocks):
        text = re.sub(r"\s+", " ", b["text"]).strip()
        heading = ""
        m = HEAD_WORDS_RE.match(text)
        if m and sum(ch.isupper() for ch in m.group(1)) >= 3 and _words(text[m.end():]) >= MIN_WORDS:
            heading, text = m.group(1).strip(" -:"), text[m.end():].strip()
        clauses.append({
            "id": i,
            "number": b["number"] or ("Intro" if numbered >= 3 and i == 0 else str(i + 1)),
            "heading": heading.title() if heading else "",
            "text": text,
            "page": page_at(b["start"]) if page_at else 1,
            "start": b["start"],
            "end": b["end"],
        })
    return clauses
