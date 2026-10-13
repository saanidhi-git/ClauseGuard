# PDF report built with ReportLab

import io
from datetime import datetime
from typing import List
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, String, Wedge, Circle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..config import DISCLAIMER

LEVEL_COLORS = {"High": "#dc2626", "Medium": "#d97706", "Low": "#ca8a04", "Safe": "#16a34a"}
ACCENT = colors.HexColor("#4f46e5")


def _t(text) -> str:
    # Helvetica has no rupee glyph, so write Rs.
    return escape(str(text or "")).replace("₹", "Rs. ")


def _gauge(score: int) -> Drawing:
    d = Drawing(180, 105)
    d.add(Wedge(90, 10, 80, 0, 180, fillColor=colors.HexColor("#e5e7eb"), strokeColor=None))
    color = "#16a34a" if score < 15 else "#ca8a04" if score < 40 else "#d97706" if score < 70 else "#dc2626"
    start = 180 - 180 * max(0, min(score, 100)) / 100
    if score > 0:
        d.add(Wedge(90, 10, 80, start, 180, fillColor=colors.HexColor(color), strokeColor=None))
    d.add(Circle(90, 10, 55, fillColor=colors.white, strokeColor=None))
    d.add(String(90, 22, str(score), fontSize=28, fontName="Helvetica-Bold", textAnchor="middle"))
    d.add(String(90, 8, "out of 100", fontSize=8, textAnchor="middle", fillColor=colors.grey))
    return d


def build_report(doc, clauses: List[dict]) -> bytes:
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title=f"ClauseGuard report - {doc.title}")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=ACCENT, alignment=0, fontSize=20)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=colors.HexColor("#111827"), spaceBefore=10)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.HexColor("#6b7280"))

    story = [
        Paragraph("ClauseGuard: Know what you sign", h1),
        Paragraph(f"<b>{_t(doc.title)}</b> &nbsp;·&nbsp; {_t(doc.doc_type.replace('_', ' ').title())} &nbsp;·&nbsp; "
                  f"Generated {datetime.now().strftime('%d %b %Y, %H:%M')}", small),
        Spacer(1, 8),
    ]

    counts = doc.level_counts or {}
    count_rows = [[Paragraph(f'<font color="{LEVEL_COLORS[lv]}"><b>{lv}</b></font>', body), str(counts.get(lv, 0))]
                  for lv in ["High", "Medium", "Low", "Safe"]]
    counts_tbl = Table([["Risk level", "Clauses"]] + count_rows, colWidths=[35 * mm, 20 * mm])
    counts_tbl.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey)]))
    top = Table([[_gauge(doc.score), [Paragraph(f"<b>{_t(doc.verdict)}</b>", body), Spacer(1, 6), counts_tbl]]],
                colWidths=[70 * mm, 100 * mm])
    top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [top, Spacer(1, 6)]

    facts = doc.key_facts or {}
    if facts:
        story.append(Paragraph("Key facts", h2))
        rows = []
        for f in facts.values():
            val = ", ".join(f["value"]) if isinstance(f["value"], list) else f["value"]
            rows.append([Paragraph(f"<b>{_t(f['label'])}</b>", body), Paragraph(_t(val), body)])
        t = Table(rows, colWidths=[45 * mm, 125 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
                               ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(t)

    if doc.summary:
        story.append(Paragraph("Summary", h2))
        for b in doc.summary:
            story.append(Paragraph(f"• {_t(b)}", body))

    flagged = [c for c in clauses if c["risk_level"] != "Safe"]
    order = {"High": 0, "Medium": 1, "Low": 2}
    flagged.sort(key=lambda c: (order.get(c["risk_level"], 3), c["id"]))
    story.append(Paragraph(f"Flagged clauses ({len(flagged)})", h2))
    if not flagged:
        story.append(Paragraph("No risky clauses were found.", body))
    for c in flagged:
        exp = c.get("explanation") or {}
        color = LEVEL_COLORS[c["risk_level"]]
        block = [
            Paragraph(f'<font color="{color}"><b>{c["risk_level"]} risk</b></font> &nbsp; '
                      f'<b>Clause {_t(c["number"])}</b> (page {c["page"]}) &nbsp; '
                      f'<font color="#6b7280">{_t(", ".join(c["label_names"]))}</font>', body),
            Paragraph(f'<i>"{_t(c["text"][:700])}{"..." if len(c["text"]) > 700 else ""}"</i>', small),
            Paragraph(f"<b>What it means:</b> {_t(exp.get('explanation'))}", body),
            Paragraph(f"<b>Why it matters:</b> {_t(exp.get('why'))}", body),
            Paragraph(f"<b>Ask before signing:</b> {_t(exp.get('ask'))}", body),
            Spacer(1, 8),
        ]
        story.append(KeepTogether(block))

    story += [Spacer(1, 10), Paragraph(f"<b>Disclaimer:</b> {_t(DISCLAIMER)} Model used: {_t(doc.model_used)}.", small)]
    pdf.build(story)
    return buf.getvalue()
