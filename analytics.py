from collections import Counter, defaultdict
from datetime import datetime, timezone


def summarize_incidents(incidents: list[dict]) -> dict:
    """
    Aggregate raw NERIS incident data into structured stats
    ready to be passed to Claude for plain-English analysis.
    """
    if not incidents:
        return {}

    total = len(incidents)
    call_types = Counter()
    response_times = []
    by_hour = Counter()
    by_day = Counter()
    by_month = Counter()
    geo_coords = []

    for inc in incidents:
        # Call type
        call_type = inc.get("incident_type") or inc.get("type") or "Unknown"
        call_types[call_type] += 1

        # Response time (dispatch to arrival, in seconds)
        dispatch = inc.get("call_create") or inc.get("dispatch_time")
        arrival = inc.get("arrival_time")
        if dispatch and arrival:
            try:
                t0 = datetime.fromisoformat(dispatch)
                t1 = datetime.fromisoformat(arrival)
                delta = (t1 - t0).total_seconds()
                if 0 < delta < 7200:  # sanity check: ignore negatives and >2hr outliers
                    response_times.append(delta)
            except ValueError:
                pass

        # Time-of-day / day-of-week patterns
        ts_str = dispatch or inc.get("call_create")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str)
                by_hour[ts.hour] += 1
                by_day[ts.strftime("%A")] += 1
                by_month[ts.strftime("%B %Y")] += 1
            except ValueError:
                pass

        # Geographic
        lat = inc.get("latitude") or inc.get("lat")
        lon = inc.get("longitude") or inc.get("lon")
        if lat and lon:
            geo_coords.append({"lat": lat, "lon": lon})

    avg_response = (sum(response_times) / len(response_times)) if response_times else None
    busiest_hour = by_hour.most_common(3)
    busiest_day = by_day.most_common(3)

    return {
        "total_incidents": total,
        "call_types": dict(call_types.most_common(10)),
        "response_time_seconds": {
            "average": round(avg_response, 1) if avg_response else None,
            "min": round(min(response_times), 1) if response_times else None,
            "max": round(max(response_times), 1) if response_times else None,
            "sample_size": len(response_times),
        },
        "busiest_hours": [{"hour": h, "count": c} for h, c in busiest_hour],
        "busiest_days": [{"day": d, "count": c} for d, c in busiest_day],
        "by_month": dict(by_month),
        "geo_sample_size": len(geo_coords),
    }
