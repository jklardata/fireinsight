"""
FireInsight CLI — NERIS-powered analytics for fire departments.

Usage:
  python3 main.py trends  [neris_id] [--period "..."] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--output file.md] [--mock]
  python3 main.py report  [neris_id] [--period "..."] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--output file.md] [--mock]
  python3 main.py grant   [neris_id] --type AFG --request "..." [--period "..."] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--output file.md] [--mock]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from analytics import summarize_incidents
from insights.trends import generate_trend_summary
from insights.report import generate_chiefs_report
from insights.grant import generate_grant_narrative


def parse_date(s: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"Unrecognized date format: '{s}'. Use YYYY-MM-DD.")


def load_data(args):
    start = getattr(args, "start", None)
    end = getattr(args, "end", None)

    if args.mock:
        from mock_data import generate_incidents, DEPT
        label = "mock data"
        if start or end:
            label += f" ({(start or datetime(2024,2,1)).strftime('%b %d %Y')} — {(end or datetime(2025,1,31)).strftime('%b %d %Y')})"
        print(f"Using {label}...")
        incidents = generate_incidents(start=start, end=end)
        return incidents, DEPT["name"]
    else:
        from neris import fetch_incidents, fetch_entity
        print(f"Fetching incidents for {args.neris_id}...")
        incidents = fetch_incidents(args.neris_id, start=start, end=end)
        if not incidents:
            print("No incidents returned. Check your NERIS_ID, credentials, and date range.")
            sys.exit(1)
        entity = fetch_entity(args.neris_id)
        return incidents, entity.get("name", args.neris_id)


def save_output(text: str, path: str, label: str):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"\nSaved {label} to {out.resolve()}")


def cmd_trends(args):
    incidents, dept_name = load_data(args)
    stats = summarize_incidents(incidents)
    print(f"Analyzing {stats['total_incidents']} incidents...\n")
    result = generate_trend_summary(dept_name, stats, args.period)
    print(result)
    if args.output:
        save_output(result, args.output, "trend summary")


def cmd_report(args):
    incidents, dept_name = load_data(args)
    stats = summarize_incidents(incidents)
    print(f"Generating chief's report for {dept_name}...\n")
    result = generate_chiefs_report(dept_name, stats, args.period)
    print(result)
    if args.output:
        save_output(result, args.output, "chief's report")


def cmd_grant(args):
    incidents, dept_name = load_data(args)
    stats = summarize_incidents(incidents)
    print(f"Generating {args.type} grant narrative for {dept_name}...\n")
    result = generate_grant_narrative(
        dept_name=dept_name,
        stats=stats,
        grant_type=args.type,
        request_description=args.request,
        period=args.period,
    )
    print(result)
    if args.output:
        save_output(result, args.output, "grant narrative")


def main():
    parser = argparse.ArgumentParser(description="FireInsight — AI analytics for fire departments")
    sub = parser.add_subparsers(dest="command", required=True)

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("neris_id", nargs="?", default="MOCK-001")
    shared.add_argument("--mock", action="store_true", help="Use generated sample data")
    shared.add_argument("--start", type=parse_date, metavar="YYYY-MM-DD", help="Filter incidents from this date")
    shared.add_argument("--end", type=parse_date, metavar="YYYY-MM-DD", help="Filter incidents up to this date")
    shared.add_argument("--output", metavar="FILE", help="Save output to file (e.g. report.md)")

    p_trends = sub.add_parser("trends", parents=[shared], help="Incident trend summary")
    p_trends.add_argument("--period", default="February 2024 - January 2025")
    p_trends.set_defaults(func=cmd_trends)

    p_report = sub.add_parser("report", parents=[shared], help="Monthly chief's report")
    p_report.add_argument("--period", default="January 2025")
    p_report.set_defaults(func=cmd_report)

    p_grant = sub.add_parser("grant", parents=[shared], help="Grant narrative generator")
    p_grant.add_argument("--type", choices=["AFG", "SAFER"], required=True)
    p_grant.add_argument("--request", required=True, help="What you're requesting")
    p_grant.add_argument("--period", default="February 2024 - January 2025")
    p_grant.set_defaults(func=cmd_grant)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
