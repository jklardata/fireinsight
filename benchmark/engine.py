"""
Benchmark comparison engine.

Filters peer database by state/region/type/size, then computes
percentile rankings for each metric.
"""
from __future__ import annotations

from .peers import PEER_DATABASE, get_region


def _percentile_rank(values: list[float], target: float, lower_is_better: bool) -> int:
    """Return 0-100 rank where 100 = best possible."""
    if not values:
        return 50
    if lower_is_better:
        # Count peers who are worse (higher value) than us
        better_count = sum(1 for v in values if v > target)
    else:
        better_count = sum(1 for v in values if v < target)
    return round(better_count / len(values) * 100)


def _fmt_seconds(s: float) -> str:
    m, sec = int(s) // 60, int(s) % 60
    return f"{m}m {sec:02d}s"


def _peer_metric(peer_list: list[dict], field: str, our_value: float,
                 lower_is_better: bool = False) -> dict | None:
    vals = [p[field] for p in peer_list if p.get(field) is not None]
    if not vals or our_value is None:
        return None
    avg = round(sum(vals) / len(vals), 1)
    pct = _percentile_rank(vals, our_value, lower_is_better)
    diff = round(our_value - avg, 1)
    return {
        "our_value":       our_value,
        "peer_avg":        avg,
        "peer_min":        round(min(vals), 1),
        "peer_max":        round(max(vals), 1),
        "percentile":      pct,
        "peer_count":      len(vals),
        "diff":            diff,
        "above_avg":       (diff < 0) if lower_is_better else (diff > 0),
    }


def run_benchmark(
    dept_stats: dict,
    dept_name:  str,
    state:      str,
    dept_type:  str,
    population: int,
) -> dict:
    """
    Compare a department's stats against three peer tiers:
    state, regional, national — filtered by dept type and population size.
    """
    # ── Derive our metrics from summarize_incidents() output ─────────────────
    rt_data  = dept_stats.get("response_time_seconds", {})
    avg_rt   = rt_data.get("average")          # seconds, may be None
    total    = dept_stats.get("total_incidents", 0)
    inc_1000 = round(total / population * 1000, 1) if population > 0 else 0

    call_types  = dept_stats.get("call_types", {})
    typed_total = sum(call_types.values()) or 1

    def _pct(keywords):
        count = sum(v for k, v in call_types.items()
                    if any(kw in k.lower() for kw in keywords))
        return round(count / typed_total * 100, 1)

    ems_pct    = _pct(["ems", "medical", "mva", "motor vehicle"])
    fire_pct   = _pct(["structure fire", "building fire", "residential fire"])
    alarm_pct  = _pct(["false alarm", "alarm activation", "unintentional"])

    # ── Build peer groups ─────────────────────────────────────────────────────
    region = get_region(state)
    lo, hi = population * 0.15, population * 6.5   # size band

    state_peers    = [p for p in PEER_DATABASE
                      if p["state"] == state and p["dept_type"] == dept_type]
    regional_peers = [p for p in PEER_DATABASE
                      if p["region"] == region and p["dept_type"] == dept_type
                      and lo <= p["population_served"] <= hi]
    national_peers = [p for p in PEER_DATABASE
                      if p["dept_type"] == dept_type
                      and lo <= p["population_served"] <= hi]

    # ── Build metric comparisons ──────────────────────────────────────────────
    def _compare(field, our_val, lower_is_better=False):
        return {
            "national": _peer_metric(national_peers, field, our_val, lower_is_better),
            "regional": _peer_metric(regional_peers, field, our_val, lower_is_better),
            "state":    _peer_metric(state_peers,    field, our_val, lower_is_better),
        }

    metrics = {}

    if avg_rt:
        rt_comp = _compare("avg_response_seconds", avg_rt, lower_is_better=True)
        # Add human-readable time strings
        for scope, m in rt_comp.items():
            if m:
                m["our_fmt"]      = _fmt_seconds(avg_rt)
                m["peer_avg_fmt"] = _fmt_seconds(m["peer_avg"])
                m["diff_fmt"]     = _fmt_seconds(abs(m["diff"]))
        metrics["response_time"] = {
            "label":           "Avg Response Time",
            "subtitle":        "Dispatch to first unit on scene",
            "lower_is_better": True,
            "unit":            "time",
            "our_display":     _fmt_seconds(avg_rt),
            **rt_comp,
        }

    metrics["call_volume"] = {
        "label":           "Calls per 1,000 Population",
        "subtitle":        "Annual volume relative to service area population",
        "lower_is_better": False,
        "unit":            "number",
        "our_display":     str(inc_1000),
        **_compare("incidents_per_1000", inc_1000),
    }

    metrics["structure_fire_rate"] = {
        "label":           "Structure Fire Rate",
        "subtitle":        "Structure fires as % of all incidents",
        "lower_is_better": False,
        "unit":            "percent",
        "our_display":     f"{fire_pct}%",
        **_compare("structure_fire_pct", fire_pct),
    }

    metrics["ems_rate"] = {
        "label":           "EMS Call Rate",
        "subtitle":        "EMS incidents as % of total calls",
        "lower_is_better": False,
        "unit":            "percent",
        "our_display":     f"{ems_pct}%",
        **_compare("ems_pct", ems_pct),
    }

    metrics["false_alarm_rate"] = {
        "label":           "False Alarm Rate",
        "subtitle":        "Alarm activations with no fire found",
        "lower_is_better": True,
        "unit":            "percent",
        "our_display":     f"{alarm_pct}%",
        **_compare("false_alarm_pct", alarm_pct, lower_is_better=True),
    }

    return {
        "dept_name":   dept_name,
        "state":       state,
        "region":      region,
        "dept_type":   dept_type,
        "population":  population,
        "metrics":     metrics,
        "peer_counts": {
            "state":    len(state_peers),
            "regional": len(regional_peers),
            "national": len(national_peers),
        },
    }
