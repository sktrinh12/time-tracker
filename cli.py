import argparse
from datetime import date, datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich import box

from db import init_db, insert_entry, entries_for_month, total_hours_for_month, entries_for_client, total_hours_for_client
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
    review.add_argument("--month", help="YYYY-MM")
    review.add_argument(
        "--client", default="preludetx", help="Client ID (default: preludetx)"
    )
    review.add_argument("--show-ids", action="store_true", help="Show entry IDs")
    review.add_argument("--markdown", help="Export to a markdown file (e.g. review.md)")

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
        if args.markdown:
            # Default client for markdown is parabilis, and month is not required
            client = "parabilis" if args.client == "preludetx" else args.client
            rows = entries_for_client(client)
            total = total_hours_for_client(client)
        else:
            if not args.month:
                parser.error("Must specify --month for standard review")
            rows = entries_for_month(args.month, args.client)
            total = total_hours_for_month(args.month, args.client)

        if args.markdown:
            headers = ["ID", "Date", "Start", "End", "Hours", "Description"] if args.show_ids else ["Date", "Start", "End", "Hours", "Description"]
            
            lines = []
            current_week = None
            
            for entry in rows:
                entry_id, d_str, s, e, h, client_name, desc = entry
                d = date.fromisoformat(d_str)
                # Use isocalendar to get week number
                year, week, weekday = d.isocalendar()
                week_key = (year, week)
                
                if week_key != current_week:
                    if current_week is not None:
                        lines.append("") # Spacer between tables
                    
                    # Find the Monday of this week
                    monday = d - timedelta(days=d.weekday())
                    
                    lines.append(f"### Week of {monday}")
                    lines.append("| " + " | ".join(headers) + " |")
                    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    current_week = week_key

                if args.show_ids:
                    row = [str(entry_id), str(d).replace("-", "\u2011"), s[:5], e[:5], f"{h:.2f}", desc or ""]
                else:
                    row = [str(d).replace("-", "\u2011"), s[:5], e[:5], f"{h:.2f}", desc or ""]
                lines.append("| " + " | ".join(row) + " |")
            
            lines.append(f"\n**Total hours: {total:.2f}**")
            
            content = "\n".join(lines)
            with open(args.markdown, "w") as f:
                f.write(content)
            print(f"✓ Exported to {args.markdown}")
        else:
            console = Console()

            table = Table(
                box=box.SIMPLE_HEAD,
                show_header=True,
                header_style="bold cyan",
                expand=True,
            )

            if args.show_ids:
                table.add_column("ID", style="dim", no_wrap=True, min_width=3)
            table.add_column("Date", style="green", no_wrap=True)
            table.add_column("Start", style="yellow", no_wrap=True)
            table.add_column("End", style="yellow", no_wrap=True)
            table.add_column("Hours", style="magenta", no_wrap=True, justify="right")
            table.add_column("Description", style="white")

            for entry in rows:
                entry_id, d, s, e, h, client, desc = entry
                row = []
                if args.show_ids:
                    row.append(str(entry_id))
                row += [str(d), s[:5], e[:5], f"{h:.2f}", desc or ""]
                table.add_row(*row)

            console.print(table)
            console.print(f"\n[bold]Total hours: [magenta]{total:.2f}[/magenta][/bold]")

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
