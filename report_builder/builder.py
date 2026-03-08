"""
No-Code Custom Report Builder
Computes selected metrics from incident data and formats a structured report.
"""
from analytics import summarize_incidents

ALL_METRICS = [
    "total_incidents",
    "fire_incidents",
    "ems_incidents",
    "false_alarms",
    "avg_response_time",
    "response_under_4min",
    "response_under_8min",
    "mutual_aid_given",
    "mutual_aid_received",
    "top_incident_types",
    "busiest_hours",
    "busiest_days",
    "incident_trend_monthly",
]

METRIC_LABELS = {
    "total_incidents":      "Total Incidents",
    "fire_incidents":       "Fire Incidents",
    "ems_incidents":        "EMS / Medical Incidents",
    "false_alarms":         "False Alarms",
    "avg_response_time":    "Average Response Time",
    "response_under_4min":  "Responses Under 4 Minutes",
    "response_under_8min":  "Responses Under 8 Minutes",
    "mutual_aid_given":     "Mutual Aid Given",
    "mutual_aid_received":  "Mutual Aid Received",
    "top_incident_types":   "Top Incident Types",
    "busiest_hours":        "Busiest Hours of Day",
    "busiest_days":         "Busiest Days of Week",
    "incident_trend_monthly": "Monthly Incident Trend",
}


def _compute_metrics(incidents: list, selected: list) -> dict:
    stats = summarize_incidents(incidents)
    results = {}

    if not selected:
        selected = ALL_METRICS

    for m in selected:
        if m == "total_incidents":
            results[m] = {"label": METRIC_LABELS[m], "value": stats.get("total", 0), "unit": "incidents"}

        elif m == "fire_incidents":
            count = sum(1 for i in incidents if "fire" in (i.get("incident_type") or "").lower()
                        or "explosion" in (i.get("incident_type") or "").lower())
            results[m] = {"label": METRIC_LABELS[m], "value": count, "unit": "incidents"}

        elif m == "ems_incidents":
            count = sum(1 for i in incidents if any(k in (i.get("incident_type") or "").lower()
                        for k in ("ems", "medical", "mva", "motor vehicle")))
            results[m] = {"label": METRIC_LABELS[m], "value": count, "unit": "incidents"}

        elif m == "false_alarms":
            count = sum(1 for i in incidents if "alarm" in (i.get("incident_type") or "").lower()
                        or "false" in (i.get("incident_type") or "").lower())
            results[m] = {"label": METRIC_LABELS[m], "value": count, "unit": "incidents"}

        elif m == "avg_response_time":
            times = []
            for i in incidents:
                if i.get("call_create") and i.get("arrival_time"):
                    try:
                        from datetime import datetime
                        s = (datetime.fromisoformat(i["arrival_time"]) -
                             datetime.fromisoformat(i["call_create"])).total_seconds()
                        if 0 < s < 7200:
                            times.append(s)
                    except Exception:
                        pass
            avg = round(sum(times) / len(times)) if times else None
            if avg:
                results[m] = {"label": METRIC_LABELS[m],
                               "value": f"{avg // 60}m {avg % 60:02d}s",
                               "unit": "avg", "raw_seconds": avg}
            else:
                results[m] = {"label": METRIC_LABELS[m], "value": "N/A", "unit": ""}

        elif m == "response_under_4min":
            times = _response_times(incidents)
            under = sum(1 for t in times if t <= 240)
            pct = round(under / len(times) * 100) if times else 0
            results[m] = {"label": METRIC_LABELS[m], "value": under, "unit": "incidents",
                          "pct": pct, "note": f"{pct}% of responded incidents"}

        elif m == "response_under_8min":
            times = _response_times(incidents)
            under = sum(1 for t in times if t <= 480)
            pct = round(under / len(times) * 100) if times else 0
            results[m] = {"label": METRIC_LABELS[m], "value": under, "unit": "incidents",
                          "pct": pct, "note": f"{pct}% of responded incidents"}

        elif m == "mutual_aid_given":
            count = sum(1 for i in incidents if "mutual" in (i.get("incident_type") or "").lower()
                        and "given" in (i.get("incident_type") or "").lower())
            results[m] = {"label": METRIC_LABELS[m], "value": count, "unit": "incidents"}

        elif m == "mutual_aid_received":
            count = sum(1 for i in incidents if "mutual" in (i.get("incident_type") or "").lower()
                        and "received" in (i.get("incident_type") or "").lower())
            results[m] = {"label": METRIC_LABELS[m], "value": count, "unit": "incidents"}

        elif m == "top_incident_types":
            from collections import Counter
            counts = Counter(i.get("incident_type", "Unknown") for i in incidents)
            top = counts.most_common(5)
            results[m] = {"label": METRIC_LABELS[m], "value": top, "unit": "types"}

        elif m == "busiest_hours":
            from collections import Counter
            hours = []
            for i in incidents:
                if i.get("call_create"):
                    try:
                        from datetime import datetime
                        hours.append(datetime.fromisoformat(i["call_create"]).hour)
                    except Exception:
                        pass
            counts = Counter(hours)
            top = [(f"{h:02d}:00", c) for h, c in sorted(counts.items(), key=lambda x: -x[1])[:3]]
            results[m] = {"label": METRIC_LABELS[m], "value": top, "unit": "hours"}

        elif m == "busiest_days":
            from collections import Counter
            DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days = []
            for i in incidents:
                if i.get("call_create"):
                    try:
                        from datetime import datetime
                        days.append(datetime.fromisoformat(i["call_create"]).weekday())
                    except Exception:
                        pass
            counts = Counter(days)
            top = [(DAYS[d], c) for d, c in sorted(counts.items(), key=lambda x: -x[1])[:3]]
            results[m] = {"label": METRIC_LABELS[m], "value": top, "unit": "days"}

        elif m == "incident_trend_monthly":
            from collections import defaultdict
            monthly = defaultdict(int)
            for i in incidents:
                if i.get("call_create"):
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(i["call_create"])
                        monthly[dt.strftime("%Y-%m")] += 1
                    except Exception:
                        pass
            results[m] = {"label": METRIC_LABELS[m],
                          "value": dict(sorted(monthly.items())), "unit": "monthly"}

    return results


def _response_times(incidents):
    times = []
    for i in incidents:
        if i.get("call_create") and i.get("arrival_time"):
            try:
                from datetime import datetime
                s = (datetime.fromisoformat(i["arrival_time"]) -
                     datetime.fromisoformat(i["call_create"])).total_seconds()
                if 0 < s < 7200:
                    times.append(s)
            except Exception:
                pass
    return times


def _compare_metric(current: dict, compare: dict, key: str) -> dict | None:
    """Return delta info for a numeric metric."""
    if key not in current or key not in compare:
        return None
    cv = current[key].get("value")
    pv = compare[key].get("value")
    if not isinstance(cv, (int, float)) or not isinstance(pv, (int, float)):
        return None
    delta = cv - pv
    pct = round(delta / pv * 100, 1) if pv else None
    return {"delta": delta, "pct": pct, "direction": "up" if delta > 0 else "down" if delta < 0 else "flat"}


def build_custom_report(
    dept_name: str,
    incidents: list,
    compare_incidents: list,
    metrics: list,
    period_label: str,
) -> dict:
    current  = _compute_metrics(incidents, metrics)
    compare  = _compute_metrics(compare_incidents, metrics) if compare_incidents else {}
    deltas   = {}
    if compare:
        for key in current:
            d = _compare_metric(current, compare, key)
            if d:
                deltas[key] = d

    return {
        "dept_name":    dept_name,
        "period":       period_label,
        "metrics":      current,
        "compare":      compare,
        "deltas":       deltas,
        "has_compare":  bool(compare_incidents),
        "all_metrics":  ALL_METRICS,
        "metric_labels": METRIC_LABELS,
    }
