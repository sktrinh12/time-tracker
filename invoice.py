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
    get_client,
    CONSULTANT_ADDR,
    CONSULTANT_EMAIL,
    CONSULTANT_NAME,
    CONSULTANT_PHONE,
)
from db import (
    entries_for_month,
    total_hours_for_month,
    entries_by_ids,
    total_hours_for_ids,
    entries_for_month_excluding_ids,
    total_hours_for_month_excluding_ids,
)


def generate_invoice(
    month: str | None = None,
    ids: list[int] | None = None,
    excluded_ids: list[int] | None = None,
    comment: str | None = None,
    client: str = "preludetx",
):
    if not month and not ids:
        raise ValueError("Must specify either --month or --ids")

    if excluded_ids:
        entries = entries_for_month_excluding_ids(month, excluded_ids, client)
        if not entries:
            raise ValueError(f"No entries found for this month - {month}")
        total_hours = total_hours_for_month_excluding_ids(month, excluded_ids, client)
        billing_period = month
    elif ids:
        entries = entries_by_ids(ids)
        if not entries:
            raise ValueError(f"No entries found for IDs: {ids}")
        total_hours = total_hours_for_ids(ids)
        billing_period = f"IDs: {','.join(map(str, ids))}"
    else:
        assert month is not None
        entries = entries_for_month(month, client)
        if not entries:
            raise ValueError(f"No entries found for this month - {month}")
        total_hours = total_hours_for_month(month, client)
        billing_period = month

    invoice_number = next_invoice_number(client)

    client_dir = INVOICE_DIR / client
    client_dir.mkdir(exist_ok=True)

    if ids:
        filename = f"Invoice_{invoice_number:03}_custom.pdf"
    else:
        filename = f"Invoice_{invoice_number:03}_{month}.pdf"
    path = client_dir / filename

    client_info = get_client(client)
    total_amount = total_hours * client_info["rate"]
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
    if ids and comment:
        elements.append(Paragraph(f"{comment}", normal))
    elif month:
        elements.append(Paragraph(f"Billing Period: {billing_period}", normal))
    elements.append(Spacer(1, 0.25 * inch))

    # ----------------------------
    # Company Info
    # ----------------------------
    elements.append(Paragraph("<b>Bill To:</b>", bold))
    elements.append(Paragraph(client_info["name"], normal))
    elements.append(Paragraph(client_info["addr"], normal))
    elements.append(Paragraph(client_info["email"], normal))
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

    for entry_id, d, start, end, hours, client_id, desc in entries:
        table_data.append(
            [
                Paragraph(d, table_style),
                Paragraph(start[:5], table_style),
                Paragraph(end[:5], table_style),
                Paragraph(f"{hours:.2f}", table_style),
                Paragraph(desc or "", table_style),
            ]
        )
        total_hours += hours

    table = Table(
        table_data,
        colWidths=[1.2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 2.7 * inch],
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))

    # ----------------------------
    # Totals
    # ----------------------------
    total_amount = total_hours * client_info["rate"]

    elements.append(Paragraph(f"Hourly Rate: ${client_info['rate']:.2f}", normal))
    elements.append(Paragraph(f"Total Hours: {total_hours:.2f}", normal))
    elements.append(Paragraph(f"<b>Total Amount Due: ${total_amount:,.2f}</b>", normal))

    elements.append(Spacer(1, 0.4 * inch))

    # Build PDF
    doc.build(elements)

    return path


def next_invoice_number(client: str):
    client_dir = INVOICE_DIR / client
    if not client_dir.exists():
        return 1
    existing = sorted(client_dir.glob("Invoice_*"))
    return len(existing) + 1
