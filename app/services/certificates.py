from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth


def _draw_fitted_centered(pdf, text, center_x, y, font_name, max_size, max_width):
    font_size = max_size
    while font_size > 12 and stringWidth(text, font_name, font_size) > max_width:
        font_size -= 1
    pdf.setFont(font_name, font_size)
    pdf.drawCentredString(center_x, y, text)


def render_certificate_pdf(recipient_name, certificate_data):
    """Render one certificate using the application's fixed PDF design."""
    output = BytesIO()
    page_width, page_height = landscape(letter)
    pdf = canvas.Canvas(output, pagesize=(page_width, page_height))
    pdf.setTitle(f"Certificate - {recipient_name}")

    pdf.setStrokeColor(HexColor("#1F4E79"))
    pdf.setLineWidth(5)
    pdf.rect(28, 28, page_width - 56, page_height - 56)

    center_x = page_width / 2
    content_width = page_width - 120
    pdf.setFillColor(HexColor("#1F4E79"))
    _draw_fitted_centered(
        pdf,
        certificate_data["title"],
        center_x,
        page_height - 112,
        "Helvetica-Bold",
        30,
        content_width,
    )

    pdf.setFillColor(HexColor("#333333"))
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(center_x, page_height - 165, "This certificate is presented to")

    pdf.setFillColor(HexColor("#1F4E79"))
    _draw_fitted_centered(
        pdf,
        recipient_name,
        center_x,
        page_height - 218,
        "Helvetica-Bold",
        30,
        content_width,
    )

    pdf.setFillColor(HexColor("#333333"))
    _draw_fitted_centered(
        pdf,
        f"for successfully completing {certificate_data['course']}",
        center_x,
        page_height - 270,
        "Helvetica",
        16,
        content_width,
    )
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(center_x, 95, f"Issued on {certificate_data['issued_on']}")
    if certificate_data.get("issuer"):
        pdf.drawCentredString(center_x, 74, certificate_data["issuer"])

    pdf.save()
    return output.getvalue()
