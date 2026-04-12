from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


PAGE_SIZES = {
    "A4": A4,
    "LETTER": LETTER,
}


class SafeDict(dict):
    def __missing__(self, key):  # return empty string if missing
        return ""


def replace_placeholders(s: str, data: Dict[str, Any]) -> str:
    try:
        return s.format_map(SafeDict(**data))
    except Exception:
        return s


def load_template(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_pdf_from_template(data: Dict[str, Any], template_path: Path) -> bytes:
    tpl = load_template(template_path)

    page_cfg = tpl.get("page", {})
    size_name = page_cfg.get("size", "A4").upper()
    page_size = PAGE_SIZES.get(size_name, A4)
    margins = page_cfg.get("margins_mm", {"left": 20, "right": 20, "top": 20, "bottom": 20})

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=margins.get("left", 20) * mm,
        rightMargin=margins.get("right", 20) * mm,
        topMargin=margins.get("top", 20) * mm,
        bottomMargin=margins.get("bottom", 20) * mm,
        title=replace_placeholders(tpl.get("title", ""), data),
        author=replace_placeholders(tpl.get("author", "SarvAwas AI"), data),
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="HeadingCenter", parent=styles["Heading1"], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], fontSize=11, leading=15))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9, leading=12))

    story: List[Any] = []

    for block in tpl.get("content", []):
        btype = block.get("type")
        if btype == "title":
            txt = replace_placeholders(block.get("text", ""), data)
            story.append(Paragraph(txt, styles["HeadingCenter"]))
            story.append(Spacer(1, 8))
        elif btype == "heading":
            txt = replace_placeholders(block.get("text", ""), data)
            story.append(Paragraph(txt, styles["Heading2"]))
            story.append(Spacer(1, 6))
        elif btype == "paragraph":
            txt = replace_placeholders(block.get("text", ""), data)
            story.append(Paragraph(txt, styles["Body"]))
            story.append(Spacer(1, 6))
        elif btype == "spacer":
            h_mm = float(block.get("height_mm", 5))
            story.append(Spacer(1, h_mm * mm))
        elif btype == "table":
            # Replace placeholders in table cells
            cols = [replace_placeholders(c, data) for c in block.get("cols", [])]
            rows_raw = block.get("rows", [])
            table_data = [cols] if cols else []
            for r in rows_raw:
                table_data.append([replace_placeholders(str(cell), data) for cell in r])

            t = Table(table_data, hAlign="LEFT")
            t.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(t)
            story.append(Spacer(1, 6))
        elif btype == "smalltext":
            txt = replace_placeholders(block.get("text", ""), data)
            story.append(Paragraph(txt, styles["Small"]))
            story.append(Spacer(1, 4))
        else:
            # Unknown block type: skip or extend here
            continue

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
