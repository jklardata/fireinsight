"""
EV / Lithium Battery Fire Detector

Identifies EV and lithium battery incidents from NERIS incident data,
computes trend stats, and surfaces operational risk indicators.
"""
from __future__ import annotations

from datetime import datetime
from collections import defaultdict

EV_KEYWORDS = [
    "ev battery", "lithium battery", "electric vehicle fire",
    "ev fire", "bev", "phev", "tesla", "hybrid fire",
    "lithium", "battery fire",
]


def _is_ev(incident: dict) -> bool:
    t = (incident.get("incident_type") or "").lower()
    return any(kw in t for kw in EV_KEYWORDS)


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


def analyze_ev_incidents(incidents: list[dict]) -> dict:
    ev_list = [i for i in incidents if _is_ev(i)]

    # Categorise all vehicle fire types (traditional + EV)
    traditional_vf = [i for i in incidents
                      if "vehicle fire" in (i.get("incident_type") or "").lower()
                      and not _is_ev(i)]
    all_fires = [i for i in incidents
                 if "fire" in (i.get("incident_type") or "").lower()]

    total_vehicle = len(traditional_vf) + len(ev_list)
    ev_pct_vehicle = round(len(ev_list) / max(total_vehicle, 1) * 100, 1)
    ev_pct_fires   = round(len(ev_list) / max(len(all_fires), 1) * 100, 1)

    # Response times
    rt_ev, rt_trad = [], []
    for inc in ev_list:
        a, b = _parse_dt(inc.get("call_create")), _parse_dt(inc.get("arrival_time"))
        if a and b:
            d = (b - a).total_seconds()
            if 0 < d < 7200:
                rt_ev.append(d)
    for inc in traditional_vf:
        a, b = _parse_dt(inc.get("call_create")), _parse_dt(inc.get("arrival_time"))
        if a and b:
            d = (b - a).total_seconds()
            if 0 < d < 7200:
                rt_trad.append(d)

    avg_rt_ev   = round(sum(rt_ev)   / len(rt_ev))   if rt_ev   else None
    avg_rt_trad = round(sum(rt_trad) / len(rt_trad)) if rt_trad else None

    # Monthly trend — sorted chronologically
    month_dt: dict[str, datetime] = {}
    by_month: dict[str, int] = defaultdict(int)
    for inc in ev_list:
        dt = _parse_dt(inc.get("call_create"))
        if dt:
            key = dt.strftime("%b %Y")
            by_month[key] += 1
            if key not in month_dt:
                month_dt[key] = dt

    sorted_months = dict(
        sorted(by_month.items(), key=lambda x: month_dt.get(x[0], datetime.min))
    )

    # YoY trend estimate: compare first half vs second half of dataset
    values = list(sorted_months.values())
    if len(values) >= 4:
        mid = len(values) // 2
        first_half = sum(values[:mid])
        second_half = sum(values[mid:])
        if first_half > 0:
            trend_pct = round((second_half - first_half) / first_half * 100)
        else:
            trend_pct = None
    else:
        trend_pct = None

    # Map points
    map_points = []
    for inc in ev_list:
        lat = inc.get("latitude") or inc.get("lat")
        lon = inc.get("longitude") or inc.get("lon")
        if lat and lon:
            dt = _parse_dt(inc.get("call_create"))
            map_points.append({
                "lat":  float(lat),
                "lon":  float(lon),
                "type": inc.get("incident_type", "EV Fire"),
                "time": dt.strftime("%b %d, %Y %H:%M") if dt else "",
            })

    # Recent incidents table (most recent 10)
    ev_sorted = sorted(ev_list, key=lambda i: _parse_dt(i.get("call_create")) or datetime.min, reverse=True)
    recent = []
    for inc in ev_sorted[:10]:
        alarm   = _parse_dt(inc.get("call_create"))
        arrival = _parse_dt(inc.get("arrival_time"))
        rt = None
        if alarm and arrival:
            d = (arrival - alarm).total_seconds()
            if 0 < d < 7200:
                rt = _fmt_secs(d)
        recent.append({
            "id":       inc.get("neris_id_incident") or inc.get("incident_id") or "—",
            "type":     inc.get("incident_type", "Unknown"),
            "date":     alarm.strftime("%b %d, %Y") if alarm else "—",
            "response": rt or "—",
        })

    return {
        "total_ev":          len(ev_list),
        "total_vehicle":     total_vehicle,
        "total_fires":       len(all_fires),
        "ev_pct_vehicle":    ev_pct_vehicle,
        "ev_pct_fires":      ev_pct_fires,
        "avg_rt_ev":         avg_rt_ev,
        "avg_rt_ev_fmt":     _fmt_secs(avg_rt_ev) if avg_rt_ev else "—",
        "avg_rt_trad":       avg_rt_trad,
        "avg_rt_trad_fmt":   _fmt_secs(avg_rt_trad) if avg_rt_trad else "—",
        "trend_pct":         trend_pct,
        "by_month":          sorted_months,
        "map_points":        map_points,
        "recent_incidents":  recent,
        "has_data":          len(ev_list) > 0,
    }
