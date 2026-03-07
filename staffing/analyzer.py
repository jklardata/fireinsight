"""
Staffing Justification Analyzer

Detects concurrent incident events, peak demand periods, and response
time degradation during high-concurrency windows — giving fire chiefs
the data they need to justify staffing budget requests to boards.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from collections import defaultdict


def _parse_dt(val) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(str(val))
    except Exception:
        return None


def _fmt_secs(s: float) -> str:
    m, sec = int(s) // 60, int(s) % 60
    return f"{m}m {sec:02d}s"


def analyze_staffing(incidents: list[dict]) -> dict:
    if not incidents:
        return {}

    parsed: list[dict] = []
    for inc in incidents:
        alarm   = _parse_dt(inc.get("call_create"))
        arrival = _parse_dt(inc.get("arrival_time"))
        cleared = _parse_dt(inc.get("cleared_time"))

        if not alarm:
            continue

        # Estimate cleared time when missing
        if not cleared:
            cleared = (arrival or alarm) + timedelta(minutes=45)

        rt = None
        if arrival:
            d = (arrival - alarm).total_seconds()
            if 30 < d < 7200:
                rt = d

        parsed.append({
            "alarm":   alarm,
            "arrival": arrival,
            "cleared": cleared,
            "type":    inc.get("incident_type", "Unknown"),
            "rt":      rt,
        })

    if not parsed:
        return {}

    # ── Concurrent incident detection ─────────────────────────────────────────
    concurrent_counts: list[int] = []
    for i, inc in enumerate(parsed):
        t = inc["alarm"]
        active = sum(
            1 for j, other in enumerate(parsed)
            if i != j and other["alarm"] <= t <= other["cleared"]
        )
        concurrent_counts.append(active)

    max_concurrent  = max(concurrent_counts)
    avg_concurrent  = round(sum(concurrent_counts) / len(concurrent_counts), 2)

    # Incidents where 2+ other calls were active (understaffing pressure events)
    understaffing_count = sum(1 for c in concurrent_counts if c >= 2)

    # ── Peak demand: hour of day ───────────────────────────────────────────────
    by_hour: dict[int, int] = defaultdict(int)
    for inc in parsed:
        by_hour[inc["alarm"].hour] += 1

    peak_hours = sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:5]
    peak_hours_fmt = [
        {"hour": f"{h:02d}:00", "count": c}
        for h, c in peak_hours
    ]

    # ── Peak demand: day of week ───────────────────────────────────────────────
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    by_dow: dict[str, int] = defaultdict(int)
    for inc in parsed:
        by_dow[days[inc["alarm"].weekday()]] += 1

    peak_days = sorted(by_dow.items(), key=lambda x: x[1], reverse=True)[:3]
    peak_days_fmt = [{"day": d, "count": c} for d, c in peak_days]

    # ── Response time degradation during high-concurrency ─────────────────────
    rt_normal: list[float] = []   # 0-1 concurrent
    rt_busy:   list[float] = []   # 2+ concurrent

    for i, inc in enumerate(parsed):
        if inc["rt"] is None:
            continue
        if concurrent_counts[i] <= 1:
            rt_normal.append(inc["rt"])
        else:
            rt_busy.append(inc["rt"])

    avg_rt_normal = round(sum(rt_normal) / len(rt_normal)) if rt_normal else None
    avg_rt_busy   = round(sum(rt_busy)   / len(rt_busy))   if rt_busy   else None

    rt_degradation_pct: int | None = None
    if avg_rt_normal and avg_rt_busy and avg_rt_normal > 0:
        rt_degradation_pct = round((avg_rt_busy - avg_rt_normal) / avg_rt_normal * 100)

    # ── Worst concurrent events ────────────────────────────────────────────────
    worst_events = []
    for inc_data, conc in sorted(zip(parsed, concurrent_counts), key=lambda x: x[1], reverse=True)[:6]:
        worst_events.append({
            "date":       inc_data["alarm"].strftime("%b %d, %Y %H:%M"),
            "type":       inc_data["type"],
            "concurrent": conc,
            "rt":         _fmt_secs(inc_data["rt"]) if inc_data["rt"] else "—",
        })

    # ── Monthly call volume trend ─────────────────────────────────────────────
    month_dt: dict[str, datetime] = {}
    by_month: dict[str, int] = defaultdict(int)
    for inc in parsed:
        key = inc["alarm"].strftime("%b %Y")
        by_month[key] += 1
        if key not in month_dt:
            month_dt[key] = inc["alarm"]

    sorted_months = dict(
        sorted(by_month.items(), key=lambda x: month_dt.get(x[0], datetime.min))
    )

    # ── Incidents per day ─────────────────────────────────────────────────────
    if len(parsed) > 1:
        date_range = (max(i["alarm"] for i in parsed) - min(i["alarm"] for i in parsed)).days + 1
        incidents_per_day = round(len(parsed) / max(date_range, 1), 1)
    else:
        incidents_per_day = len(parsed)

    return {
        "total_incidents":        len(parsed),
        "incidents_per_day":      incidents_per_day,
        "max_concurrent":         max_concurrent,
        "avg_concurrent":         avg_concurrent,
        "understaffing_count":    understaffing_count,
        "understaffing_pct":      round(understaffing_count / len(parsed) * 100, 1),
        "peak_hours":             peak_hours_fmt,
        "peak_days":              peak_days_fmt,
        "avg_rt_normal":          avg_rt_normal,
        "avg_rt_normal_fmt":      _fmt_secs(avg_rt_normal) if avg_rt_normal else "—",
        "avg_rt_busy":            avg_rt_busy,
        "avg_rt_busy_fmt":        _fmt_secs(avg_rt_busy) if avg_rt_busy else "—",
        "rt_degradation_pct":     rt_degradation_pct,
        "worst_events":           worst_events,
        "by_month":               sorted_months,
    }
