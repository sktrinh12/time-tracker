from datetime import datetime
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
    entries = entries_for_month(month)
    total_hours = total_hours_for_month(month)

    invoice_number = len(list(INVOICE_DIR.glob("Invoice_*.txt"))) + 1
    filename = f"Invoice_{invoice_number:03}_{month}.txt"
    path = INVOICE_DIR / filename

    total_amount = total_hours * HOURLY_RATE
    today = datetime.today().date().isoformat()

    lines = [
        f"Invoice #: {invoice_number:03}",
        f"Invoice Date: {today}",
        f"Billing Month: {month}",
        "",
        "Company:",
        COMPANY_NAME,
        f"Address: {COMPANY_ADDR}",
        "Attn: Contracts Department",
        COMPANY_EMAIL,
        "",
        "Consultant:",
        CONSULTANT_NAME,
        CONSULTANT_ADDR,
        f"Attn: {CONSULTANT_NAME}",
        CONSULTANT_EMAIL,
        f"cell {CONSULTANT_PHONE}",
        "",
        "Date       Start   End     Hours   Description",
        "-" * 55,
    ]

    for d, s, e, h, desc in entries:
        lines.append(f"{d}  {s[:5]}   {e[:5]}   {h:>5.2f}   {desc}")

    lines.extend(
        [
            "",
            f"Total Hours: {total_hours:.2f}",
            f"Rate: ${HOURLY_RATE:.2f}/hr",
            f"Amount Due: ${total_amount:.2f}",
        ]
    )

    path.write_text("\n".join(lines))
    return path


def next_invoice_number():
    return len(list(INVOICE_DIR.glob("Invoice_*.txt"))) + 1
