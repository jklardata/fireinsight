"""
FireInsight CLI — NERIS-powered analytics for fire departments.

Usage:
  python main.py trends  <neris_id> --period "Jan-Dec 2024"
  python main.py report  <neris_id> --period "January 2025"
  python main.py grant   <neris_id> --type AFG --request "2 thermal imaging cameras" --period "2024"
"""

import argparse
import sys
from neris import fetch_incidents, fetch_entity
from analytics import summarize_incidents
from insights.trends import generate_trend_summary
from insights.report import generate_chiefs_report
from insights.grant import generate_grant_narrative


def cmd_trends(args):
    print(f"Fetching incidents for {args.neris_id}...")
    incidents = fetch_incidents(args.neris_id)
    if not incidents:
        print("No incidents returned. Check your NERIS_ID and credentials.")
        sys.exit(1)

    entity = fetch_entity(args.neris_id)
    dept_name = entity.get("name", args.neris_id)

    stats = summarize_incidents(incidents)
    print(f"Analyzing {stats['total_incidents']} incidents...\n")

    summary = generate_trend_summary(dept_name, stats, args.period)
    print(summary)


def cmd_report(args):
    print(f"Fetching incidents for {args.neris_id}...")
    incidents = fetch_incidents(args.neris_id)
    if not incidents:
        print("No incidents returned. Check your NERIS_ID and credentials.")
        sys.exit(1)

    entity = fetch_entity(args.neris_id)
    dept_name = entity.get("name", args.neris_id)

    stats = summarize_incidents(incidents)
    print(f"Generating chief's report for {dept_name}...\n")

    report = generate_chiefs_report(dept_name, stats, args.period)
    print(report)


def cmd_grant(args):
    print(f"Fetching incidents for {args.neris_id}...")
    incidents = fetch_incidents(args.neris_id)
    if not incidents:
        print("No incidents returned. Check your NERIS_ID and credentials.")
        sys.exit(1)

    entity = fetch_entity(args.neris_id)
    dept_name = entity.get("name", args.neris_id)

    stats = summarize_incidents(incidents)
    print(f"Generating {args.type} grant narrative for {dept_name}...\n")

    narrative = generate_grant_narrative(
        dept_name=dept_name,
        stats=stats,
        grant_type=args.type,
        request_description=args.request,
        period=args.period,
    )
    print(narrative)


def main():
    parser = argparse.ArgumentParser(description="FireInsight — AI analytics for fire departments")
    sub = parser.add_subparsers(dest="command", required=True)

    # trends
    p_trends = sub.add_parser("trends", help="Incident trend summary")
    p_trends.add_argument("neris_id", help="Department NERIS ID")
    p_trends.add_argument("--period", default="the past year", help="Time period label (e.g. 'Jan-Dec 2024')")
    p_trends.set_defaults(func=cmd_trends)

    # report
    p_report = sub.add_parser("report", help="Monthly chief's report")
    p_report.add_argument("neris_id", help="Department NERIS ID")
    p_report.add_argument("--period", default="this month", help="Report period label")
    p_report.set_defaults(func=cmd_report)

    # grant
    p_grant = sub.add_parser("grant", help="Grant narrative generator")
    p_grant.add_argument("neris_id", help="Department NERIS ID")
    p_grant.add_argument("--type", choices=["AFG", "SAFER"], required=True, help="Grant program type")
    p_grant.add_argument("--request", required=True, help="What you're requesting (e.g. '2 thermal imaging cameras')")
    p_grant.add_argument("--period", default="the past year", help="Data period label")
    p_grant.set_defaults(func=cmd_grant)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
