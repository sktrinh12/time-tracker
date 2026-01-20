import argparse
from datetime import date, datetime
from db import init_db, insert_entry, entries_for_month, total_hours_for_month
from models import TimeEntry
from invoice import generate_monthly_invoice, next_invoice_number
from config import CONSULTANT_NAME, COMPANY_NAME

def parse_time(value: str):
    return datetime.strptime(value, "%H:%M").time()

def compute_hours(start, end):
    delta = (
        datetime.combine(date.min, end)
        - datetime.combine(date.min, start)
    )
    if delta.total_seconds() <= 0:
        raise ValueError("End time must be after start time")
    return round(delta.total_seconds() / 3600, 2)

def main():
    init_db()

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- log ----
    log = sub.add_parser("log")
    log.add_argument("--date", help="YYYY-MM-DD (defaults to today)")
    log.add_argument("--start", required=True, help="HH:MM")
    log.add_argument("--end", required=True, help="HH:MM")
    log.add_argument("--category", default="")
    log.add_argument("--desc", default="")

    # ---- invoice ----
    inv = sub.add_parser("invoice")
    inv.add_argument("--month", required=True, help="YYYY-MM")

    review = sub.add_parser("review")
    review.add_argument("--month", required=True, help="YYYY-MM")

    email = sub.add_parser("email-template")
    email.add_argument("--month", required=True, help="YYYY-MM")

    args = parser.parse_args()

    if args.cmd == "log":
        work_date = (
            date.fromisoformat(args.date)
            if args.date
            else date.today()
        )

        start = parse_time(args.start)
        end = parse_time(args.end)
        hours = compute_hours(start, end)

        entry = TimeEntry(
            work_date=work_date,
            start_time=start,
            end_time=end,
            hours=hours,
            category=args.category,
            description=args.desc,
        )

        insert_entry(entry)
        print(
            f"✓ Logged {work_date} "
            f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')} "
            f"({hours:.2f}h)"
        )

    elif args.cmd == "invoice":
        path = generate_monthly_invoice(args.month)
        print(f"✓ Invoice generated: {path}")

    elif args.cmd == "review":
        rows = entries_for_month(args.month)
        total = total_hours_for_month(args.month)

        print("Date        Start   End     Hours   Description")
        print("-" * 60)

        for d, s, e, h, desc in rows:
            print(
                f"{d}  {s[:5]}   {e[:5]}   {h:>5.2f}   {desc or ''}"
            )

        print("-" * 60)
        print(f"Total hours: {total:.2f}")

    elif args.cmd == "email-template":
        invoice_number = next_invoice_number()
        year, month = args.month.split("-")

        import calendar
        month_name = calendar.month_name[int(month)]

        subject = f"Invoice No. {invoice_number:03} – {month_name} {year}"

        body = f"""
Hi {COMPANY_NAME},

Please find attached my invoice for services rendered in {month_name} {year}.

Let me know if you have any questions.

Best regards,
{CONSULTANT_NAME}
        """.strip()

        print("\nSubject:")
        print(subject)
        print("\nBody:\n")
        print(body)

if __name__ == "__main__":
    main()
