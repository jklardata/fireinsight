"""
Community Risk Scorer

Grids the service area and assigns a composite risk score to each cell
based on incident density, type severity, and response time gaps.
"""
from __future__ import annotations

from datetime import datetime
from collections import defaultdict

RESPONSE_TARGET = 480  # 8 minutes — NFPA 1710/1720 benchmark

RISK_WEIGHT: dict[str, int] = {
    "structure fire":   15,
    "building fire":    15,
    "residential fire": 15,
    "ev battery":       12,
    "lithium battery":  12,
    "wildfire":         12,
    "vehicle fire":      8,
    "brush":             7,
    "grass fire":        7,
    "rescue":            8,
    "extrication":       8,
    "water rescue":      8,
    "hazmat":           10,
    "carbon monoxide":  10,
    "mva":               5,
    "motor vehicle":     5,
    "medical":           3,
    "ems":               3,
    "false alarm":       1,
    "alarm":             1,
    "service":           1,
    "public assist":     1,
}


def _weight(incident_type: str) -> int:
    t = (incident_type or "").lower()
    for kw, w in RISK_WEIGHT.items():
        if kw in t:
            return w
    return 2


def _parse_dt(val) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(str(val))
    except Exception:
        return None


def compute_risk_zones(incidents: list[dict], grid_size: float = 0.02) -> list[dict]:
    """
    Partition incidents into geographic grid cells and score each.
    grid_size ~0.02° ≈ 2 km cells at mid-latitudes.
    """
    grid: dict = defaultdict(lambda: {
        "count": 0, "weight": 0.0,
        "types": defaultdict(int),
        "rt_sum": 0.0, "rt_count": 0,
    })

    for inc in incidents:
        lat = inc.get("latitude") or inc.get("lat")
        lon = inc.get("longitude") or inc.get("lon")
        if not lat or not lon:
            continue

        lat, lon = float(lat), float(lon)
        cell = (
            round(round(lat / grid_size) * grid_size, 5),
            round(round(lon / grid_size) * grid_size, 5),
        )

        w = _weight(inc.get("incident_type", ""))
        grid[cell]["count"]  += 1
        grid[cell]["weight"] += w
        grid[cell]["types"][inc.get("incident_type", "Other")] += 1

        alarm   = _parse_dt(inc.get("call_create"))
        arrival = _parse_dt(inc.get("arrival_time"))
        if alarm and arrival:
            d = (arrival - alarm).total_seconds()
            if 0 < d < 7200:
                grid[cell]["rt_sum"]   += d
                grid[cell]["rt_count"] += 1

    if not grid:
        return []

    max_weight = max(v["weight"] for v in grid.values())
    zones = []

    for (clat, clon), data in grid.items():
        base = (data["weight"] / max_weight) * 100

        # Penalise zones with slow response (up to +20 pts)
        avg_rt = None
        rt_penalty = 0.0
        if data["rt_count"] > 0:
            avg_rt = data["rt_sum"] / data["rt_count"]
            if avg_rt > RESPONSE_TARGET:
                rt_penalty = min((avg_rt - RESPONSE_TARGET) / 60 * 3, 20)

        score = min(round(base + rt_penalty), 100)
        dominant = max(data["types"], key=data["types"].get) if data["types"] else "Unknown"

        level = (
            "Critical" if score >= 75
            else "High"   if score >= 50
            else "Medium" if score >= 25
            else "Low"
        )

        zones.append({
            "lat":                   clat,
            "lon":                   clon,
            "risk_score":            score,
            "incident_count":        data["count"],
            "dominant_type":         dominant,
            "avg_response_seconds":  round(avg_rt) if avg_rt else None,
            "risk_level":            level,
        })

    return sorted(zones, key=lambda z: z["risk_score"], reverse=True)


def compute_risk_summary(zones: list[dict]) -> dict:
    if not zones:
        return {}

    by_level: dict[str, list] = defaultdict(list)
    for z in zones:
        by_level[z["risk_level"]].append(z)

    gap_zones = [
        z for z in zones
        if z.get("avg_response_seconds") and z["avg_response_seconds"] > RESPONSE_TARGET
    ]

    avg_score = round(sum(z["risk_score"] for z in zones) / len(zones))
    overall = (
        "Critical" if avg_score >= 75
        else "High"   if avg_score >= 50
        else "Medium" if avg_score >= 25
        else "Low"
    )

    # Categorise top zones by dominant type for the risk profile
    fire_zones = [z for z in zones if "fire" in (z["dominant_type"] or "").lower()
                  or "ev" in (z["dominant_type"] or "").lower()
                  or "lithium" in (z["dominant_type"] or "").lower()]
    ems_zones  = [z for z in zones if "ems" in (z["dominant_type"] or "").lower()
                  or "medical" in (z["dominant_type"] or "").lower()
                  or "mva" in (z["dominant_type"] or "").lower()]

    return {
        "total_zones":      len(zones),
        "avg_risk_score":   avg_score,
        "overall_level":    overall,
        "critical_count":   len(by_level["Critical"]),
        "high_count":       len(by_level["High"]),
        "medium_count":     len(by_level["Medium"]),
        "low_count":        len(by_level["Low"]),
        "response_gap_count": len(gap_zones),
        "top_zones":        zones[:6],
        "gap_zones":        gap_zones[:4],
        "fire_zone_count":  len(fire_zones),
        "ems_zone_count":   len(ems_zones),
    }
