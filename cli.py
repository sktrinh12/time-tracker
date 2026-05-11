import argparse
from datetime import date, datetime
from db import init_db, insert_entry, entries_for_month, total_hours_for_month
from models import TimeEntry
from invoice import generate_invoice, next_invoice_number
from config import CONSULTANT_NAME, COMPANY_NAME


def parse_time(value: str):
    return datetime.strptime(value, "%H:%M").time()


def compute_hours(start, end):
    delta = datetime.combine(date.min, end) - datetime.combine(date.min, start)
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
    log.add_argument(
        "--client", default="preludetx", help="Client ID (default: preludetx)"
    )
    log.add_argument("--category", default="")
    log.add_argument("--desc", default="")

    # ---- invoice ----
    inv = sub.add_parser("invoice")
    inv.add_argument("--month", help="YYYY-MM")
    inv.add_argument(
        "--client", default="preludetx", help="Client ID (default: preludetx)"
    )
    inv.add_argument("--ids", help="Comma-separated entry IDs (e.g., 1,2,3)")
    inv.add_argument("--comment", help="Custom comment for custom invoices")

    review = sub.add_parser("review")
    review.add_argument("--month", required=True, help="YYYY-MM")
    review.add_argument(
        "--client", default="preludetx", help="Client ID (default: preludetx)"
    )
    review.add_argument("--show-ids", action="store_true", help="Show entry IDs")

    email = sub.add_parser("email-template")
    email.add_argument("--month", required=True, help="YYYY-MM")
    email.add_argument(
        "--client", default="preludetx", help="Client ID (default: preludetx)"
    )

    args = parser.parse_args()

    if args.cmd == "log":
        work_date = date.fromisoformat(args.date) if args.date else date.today()

        start = parse_time(args.start)
        end = parse_time(args.end)
        hours = compute_hours(start, end)

        entry = TimeEntry(
            work_date=work_date,
            start_time=start,
            end_time=end,
            hours=hours,
            client=args.client,
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
        if not args.month and not args.ids:
            parser.error("Must specify either --month or --ids")

        ids = None
        excluded_ids = None
        if args.ids:
            try:
                ids = [int(x.strip()) for x in args.ids.split(",")]
            except ValueError:
                parser.error("--ids must be comma-separated integers")
            if args.month:
                excluded_ids = ids
                ids = None

        path = generate_invoice(
            month=args.month,
            ids=ids,
            excluded_ids=excluded_ids,
            comment=args.comment,
            client=args.client,
        )
        print(f"✓ Invoice generated: {path}")

    elif args.cmd == "review":
        rows = entries_for_month(args.month, args.client)
        total = total_hours_for_month(args.month, args.client)

        from colorama import init, Fore, Style

        init(autoreset=True)  # resets style after each print

        # ... inside elif args.cmd == "review":
        rows = entries_for_month(args.month, args.client)
        total = total_hours_for_month(args.month, args.client)

        # Colour definitions
        HEADER = Fore.CYAN + Style.BRIGHT
        TOTAL_COLOR = Fore.YELLOW + Style.BRIGHT
        ROW_COLOR = Fore.WHITE
        ALT_ROW = Fore.LIGHTBLACK_EX

        if args.show_ids:
            print(
                HEADER
                + f"{'ID':<4} {'Date':<12} {'Start':<8} {'End':<8} {'Hours':>6}   Description"
            )
            print("-" * 70)
            for i, (entry_id, d, s, e, h, client, category, desc) in enumerate(rows):
                color = ROW_COLOR if i % 2 == 0 else ALT_ROW
                print(
                    color
                    + f"{entry_id:<4} {d:<12} {s[:5]:<8} {e[:5]:<8} {h:>6.2f}   {desc or ''}"
                )
        else:
            print(
                HEADER
                + f"{'Date':<12} {'Start':<8} {'End':<8} {'Hours':>6}   Description"
            )
            print("-" * 60)
            for i, (entry_id, d, s, e, h, client, category, desc) in enumerate(rows):
                color = ROW_COLOR if i % 2 == 0 else ALT_ROW
                print(color + f"{d:<12} {s[:5]:<8} {e[:5]:<8} {h:>6.2f}   {desc or ''}")

        print("-" * 60)
        print(TOTAL_COLOR + f"Total hours: {total:.2f}")

    elif args.cmd == "email-template":
        from config import get_client

        client_info = get_client(args.client)
        invoice_number = next_invoice_number() - 1
        year, month = args.month.split("-")

        import calendar

        month_name = calendar.month_name[int(month)]

        subject = f"Invoice No. {invoice_number:03} – {month_name} {year}"

        body = f"""
Hi {client_info["name"]},

Please find attached my invoice for services rendered in {month_name} {year}.

Let me know if you have any questions. Thanks.

Best regards,
{CONSULTANT_NAME}
        """.strip()

        print(subject)
        print()
        print(body)


if __name__ == "__main__":
    main()
