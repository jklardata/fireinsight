"""
NERIS Compliance Tracker

Checks incidents against NERIS mandatory schema fields (Jan 2026 mandate).
Returns per-module compliance rates and a prioritised list of gaps.
"""
from __future__ import annotations
from collections import defaultdict

FIRE_KEYWORDS = {"fire", "explosion", "wildfire", "brush", "arson"}

MODULES: dict[str, list[tuple[str, str, str]]] = {
    "Core Incident": [
        ("neris_id_incident", "Incident ID",      "always"),
        ("neris_id_entity",   "Entity ID",        "always"),
        ("incident_type",     "Incident Type",    "always"),
        ("status",            "Incident Status",  "always"),
        ("call_create",       "Alarm Time",       "always"),
        ("dispatch_time",     "Dispatch Time",    "always"),
        ("arrival_time",      "Arrival Time",     "always"),
        ("cleared_time",      "Cleared Time",     "always"),
    ],
    "Location / Geocoding": [
        ("latitude",  "Latitude",  "always"),
        ("longitude", "Longitude", "always"),
        ("address",   "Address",   "always"),
    ],
    "Life Safety Outcomes": [
        ("civilian_injuries",      "Civilian Injuries",      "always"),
        ("civilian_fatalities",    "Civilian Fatalities",    "always"),
        ("firefighter_injuries",   "Firefighter Injuries",   "always"),
        ("firefighter_fatalities", "Firefighter Fatalities", "always"),
    ],
    "Actions & Tactics": [
        ("primary_action", "Primary Action Taken", "always"),
    ],
    "Fire Module": [
        ("area_of_origin",    "Area of Origin",    "fire_only"),
        ("fire_cause",        "Fire Cause",        "fire_only"),
        ("construction_type", "Construction Type", "fire_only"),
    ],
    "Aid Classification": [
        ("aid_type", "Aid Given / Received", "always"),
    ],
}


def _is_fire(inc: dict) -> bool:
    t = (inc.get("incident_type") or "").lower()
    return any(kw in t for kw in FIRE_KEYWORDS)


def _present(val) -> bool:
    if val is None:
        return False
    if isinstance(val, str):
        return val.strip().lower() not in ("", "none", "null", "0", "n/a")
    return True


def check_compliance(incidents: list[dict]) -> dict:
    if not incidents:
        return {}

    total      = len(incidents)
    fire_total = sum(1 for i in incidents if _is_fire(i))
    all_gaps: list[dict] = []

    module_results: dict[str, dict] = {}

    for module_name, fields in MODULES.items():
        field_stats: list[dict] = []

        for field_key, label, scope in fields:
            applicable = [i for i in incidents if scope == "always" or _is_fire(i)]
            n = len(applicable)

            if n == 0:
                field_stats.append({"label": label, "scope": scope, "pct": 100, "na": True})
                continue

            if field_key == "address":
                present = sum(
                    1 for i in applicable
                    if _present(i.get("address"))
                    or _present(i.get("full_address"))
                    or _present(i.get("street_address"))
                )
            elif field_key == "neris_id_incident":
                present = sum(
                    1 for i in applicable
                    if _present(i.get("neris_id_incident")) or _present(i.get("incident_id"))
                )
            elif field_key == "neris_id_entity":
                present = sum(
                    1 for i in applicable
                    if _present(i.get("neris_id_entity")) or _present(i.get("entity_id"))
                )
            else:
                present = sum(1 for i in applicable if _present(i.get(field_key)))

            pct     = round(present / n * 100)
            missing = n - present

            if pct < 100:
                all_gaps.append({
                    "module": module_name,
                    "field":  label,
                    "missing": missing,
                    "pct":    pct,
                    "total":  n,
                    "scope":  scope,
                })

            field_stats.append({
                "label":   label,
                "scope":   scope,
                "present": present,
                "total":   n,
                "pct":     pct,
                "na":      False,
            })

        real_fields = [f for f in field_stats if not f["na"]]
        module_pct  = round(sum(f["pct"] for f in real_fields) / len(real_fields)) if real_fields else 100

        module_results[module_name] = {
            "fields":         field_stats,
            "compliance_pct": module_pct,
            "level": (
                "Compliant" if module_pct >= 95
                else "Warning"  if module_pct >= 70
                else "Critical"
            ),
        }

    all_gaps.sort(key=lambda g: g["pct"])

    module_pcts  = [v["compliance_pct"] for v in module_results.values()]
    overall_pct  = round(sum(module_pcts) / len(module_pcts)) if module_pcts else 0

    return {
        "total_incidents": total,
        "fire_incidents":  fire_total,
        "modules":         module_results,
        "overall_pct":     overall_pct,
        "overall_level":   (
            "Compliant" if overall_pct >= 95
            else "Warning"  if overall_pct >= 70
            else "Critical"
        ),
        "top_gaps":        all_gaps[:8],
        "deadline_passed": True,
    }
