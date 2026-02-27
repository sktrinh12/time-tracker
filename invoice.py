from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from config import (
    INVOICE_DIR,
    HOURLY_RATE,
    COMPANY_NAME,
    COMPANY_EMAIL,
    COMPANY_ADDR,
    CONSULTANT_ADDR,
    CONSULTANT_EMAIL,
    CONSULTANT_NAME,
    CONSULTANT_PHONE,
)
from db import entries_for_month, total_hours_for_month


def generate_monthly_invoice(month: str):
    """
    month: YYYY-MM
    """
    entries = entries_for_month(month)
    if not entries:
        raise ValueError(f"No entries found for this month - {month}")
    total_hours = total_hours_for_month(month)

    invoice_number = next_invoice_number()
    filename = f"Invoice_{invoice_number:03}_{month}.pdf"
    path = INVOICE_DIR / filename

    total_amount = total_hours * HOURLY_RATE
    today = datetime.today().date().isoformat()

    doc = SimpleDocTemplate(str(path), pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    bold = ParagraphStyle(
        name="Bold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
    )
    table_style = styles["BodyText"]
    table_style.fontSize = 9

    # ----------------------
    # Header
    # ----------------------
    elements.append(Paragraph("<b>INVOICE</b>", styles["Title"]))
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph(f"Invoice #: {invoice_number:03}", normal))
    elements.append(Paragraph(f"Invoice Date: {today}", normal))
    elements.append(Paragraph(f"Billing Month: {month}", normal))
    elements.append(Spacer(1, 0.25 * inch))

    # ----------------------------
    # Company Info
    # ----------------------------
    elements.append(Paragraph("<b>Bill To:</b>", bold))
    elements.append(Paragraph(COMPANY_NAME, normal))
    elements.append(Paragraph(COMPANY_ADDR, normal))
    elements.append(Paragraph(COMPANY_EMAIL, normal))
    elements.append(Spacer(1, 0.3 * inch))

    # ----------------------------
    # Consultant Info
    # ----------------------------
    elements.append(Paragraph("<b>From:</b>", bold))
    elements.append(Paragraph(CONSULTANT_NAME, normal))
    elements.append(Paragraph(CONSULTANT_ADDR, normal))
    elements.append(Paragraph(CONSULTANT_EMAIL, normal))
    elements.append(Paragraph(CONSULTANT_PHONE, normal))
    elements.append(Spacer(1, 0.4 * inch))

    # ----------------------
    # Table
    # ----------------------
    table_data = [["Date", "Start", "End", "Hours", "Description"]]

    total_hours = 0.0

    for d, start, end, hours, desc in entries:
        table_data.append([
            Paragraph(d, table_style),
            Paragraph(start[:5], table_style),
            Paragraph(end[:5], table_style),
            Paragraph(f"{hours:.2f}", table_style),
            Paragraph(desc or "", table_style),
        ])
        total_hours += hours

    table = Table(
        table_data,
        colWidths=[1.2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 2.7 * inch],
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))

    # ----------------------------
    # Totals
    # ----------------------------
    total_amount = total_hours * HOURLY_RATE

    elements.append(Paragraph(f"Hourly Rate: ${HOURLY_RATE:.2f}", normal))
    elements.append(Paragraph(f"Total Hours: {total_hours:.2f}", normal))
    elements.append(Paragraph(
        f"<b>Total Amount Due: ${total_amount:,.2f}</b>",
        normal
    ))

    elements.append(Spacer(1, 0.4 * inch))

    # Build PDF
    doc.build(elements)

    return path


def next_invoice_number():
    existing = sorted(INVOICE_DIR.glob("Invoice_*"))
    return len(existing) + 1
