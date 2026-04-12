from io import BytesIO
from typing import Dict, Optional, Tuple

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from PyPDF2 import PdfReader, PdfWriter


def generate_overlay_pdf(data: Dict[str, str], page_size=A4) -> BytesIO:
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=page_size)
    width, height = page_size

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(30 * mm, height - 30 * mm, "Buyer Agreement")

    c.setFont("Helvetica", 11)
    y = height - 45 * mm
    line_gap = 8 * mm

    def draw(label: str, key: str):
        nonlocal y
        value = data.get(key, "")
        c.drawString(25 * mm, y, f"{label}: {value}")
        y -= line_gap

    # Basic fields
    draw("Buyer Name", "buyerName")
    draw("Buyer Address", "buyerAddress")
    draw("Buyer Mobile", "buyerMobile")
    draw("Investor Name", "investorName")
    draw("Investor Address", "investorAddress")
    draw("Investor Mobile", "investorMobile")
    draw("Property Name", "propertyName")
    draw("Property Location", "propertyLocationText")
    draw("Latitude", "latitude")
    draw("Longitude", "longitude")
    draw("Property Value", "propertyValue")
    draw("Buyer Contribution", "buyerAmount")
    draw("Investor Contribution", "investorAmount")
    draw("Down Payment", "downPayment")
    draw("Equity %", "equityPercent")

    c.showPage()
    c.save()
    packet.seek(0)
    return packet


def compose_pdf_with_base(base_pdf_bytes: Optional[bytes], overlay_stream: BytesIO) -> bytes:
    if base_pdf_bytes:
        base_reader = PdfReader(BytesIO(base_pdf_bytes))
        overlay_reader = PdfReader(overlay_stream)
        writer = PdfWriter()

        # Place overlay on the first page (simple case)
        base_page = base_reader.pages[0]
        overlay_page = overlay_reader.pages[0]
        base_page.merge_page(overlay_page)
        writer.add_page(base_page)

        # Copy rest of base pages unchanged
        for i in range(1, len(base_reader.pages)):
            writer.add_page(base_reader.pages[i])

        out = BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read()

    # If no base provided, just return overlay as final PDF
    return overlay_stream.getvalue()


def get_base_page_size(base_pdf_bytes: bytes):
    reader = PdfReader(BytesIO(base_pdf_bytes))
    page = reader.pages[0]
    media_box = page.mediabox
    width = float(media_box.width)
    height = float(media_box.height)
    return width, height


def generate_positioned_overlay(
    data: Dict[str, str],
    positions: Dict[str, Dict[str, float]],
    page_size,
    draw_grid: bool = False,
):
    """
    positions: {
      key: {"x_mm": float, "y_mm": float, "page": int}
    }
    """
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=page_size)
    width, height = page_size

    if draw_grid:
        c.setStrokeColorRGB(0.85, 0.85, 0.85)
        c.setLineWidth(0.2)
        # draw 10mm grid
        step = 10 * mm
        x = 0
        while x <= width:
            c.line(x, 0, x, height)
            x += step
        y = 0
        while y <= height:
            c.line(0, y, width, y)
            y += step
        c.setFont("Helvetica", 6)
        # axes labels every 20mm
        for xm in range(0, int(width / mm) + 1, 20):
            c.drawString(xm * mm + 1, 1 * mm, str(xm))
        for ym in range(0, int(height / mm) + 1, 20):
            c.drawString(1 * mm, ym * mm + 1, str(ym))

    c.setFont("Helvetica", 11)
    for key, pos in positions.items():
        val = str(data.get(key, "") or "")
        x = pos.get("x_mm", 0) * mm
        y = pos.get("y_mm", 0) * mm
        # Assuming first page for simplicity; extend to multi-page by saving pages selectively
        c.drawString(x, y, val)

    c.showPage()
    c.save()
    packet.seek(0)
    return packet


def append_signature_page(pdf_bytes: bytes, page_size=A4) -> Tuple[bytes, int]:
    """
    Append a standardized signature page to the given PDF bytes.
    Returns a tuple of (combined_pdf_bytes, signature_page_number), where page numbers start at 1.
    """
    # Create a single-page PDF with signature lines and labels
    sig_buffer = BytesIO()
    c = canvas.Canvas(sig_buffer, pagesize=page_size)
    width, height = page_size

    # Heading
    c.setFont("Helvetica-Bold", 16)
    c.drawString(25 * mm, height - 30 * mm, "Signatures")

    # Buyer signature area
    c.setFont("Helvetica", 11)
    c.drawString(25 * mm, height - 60 * mm, "Buyer Signature:")
    c.line(25 * mm, height - 65 * mm, width - 25 * mm, height - 65 * mm)
    c.setFont("Helvetica", 9)
    c.drawString(25 * mm, height - 70 * mm, "Name:")
    c.line(40 * mm, height - 70 * mm, width / 2 - 10 * mm, height - 70 * mm)
    c.drawString(width / 2 + 5 * mm, height - 70 * mm, "Date:")
    c.line(width / 2 + 20 * mm, height - 70 * mm, width - 25 * mm, height - 70 * mm)

    # Investor signature area
    c.setFont("Helvetica", 11)
    c.drawString(25 * mm, height - 100 * mm, "Investor Signature:")
    c.line(25 * mm, height - 105 * mm, width - 25 * mm, height - 105 * mm)
    c.setFont("Helvetica", 9)
    c.drawString(25 * mm, height - 110 * mm, "Name:")
    c.line(40 * mm, height - 110 * mm, width / 2 - 10 * mm, height - 110 * mm)
    c.drawString(width / 2 + 5 * mm, height - 110 * mm, "Date:")
    c.line(width / 2 + 20 * mm, height - 110 * mm, width - 25 * mm, height - 110 * mm)

    c.showPage()
    c.save()
    sig_buffer.seek(0)

    # Combine original PDF with signature page
    reader_original = PdfReader(BytesIO(pdf_bytes))
    reader_sig = PdfReader(sig_buffer)
    writer = PdfWriter()

    for page in reader_original.pages:
        writer.add_page(page)

    # Append the signature page (single page)
    writer.add_page(reader_sig.pages[0])

    out = BytesIO()
    writer.write(out)
    out.seek(0)

    signature_page_number = len(reader_original.pages) + 1  # 1-based index
    return out.read(), signature_page_number
