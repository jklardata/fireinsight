"""
NERIS Pre-Submission Validator
Runs local field checks on incidents before they touch the NERIS API.
Returns a structured report: per-incident status + aggregate summary.
"""
import re
from datetime import datetime

# NERIS ID patterns
_NERIS_ID_RE = re.compile(r"^(FD|FM)\d{8}$")
_INC_NUM_RE  = re.compile(r"^[\w\-\:]+$")

# Required fields and their human labels
REQUIRED_FIELDS = [
    ("neris_id_incident",  "Incident Number",       "critical"),
    ("call_create",        "Dispatch Timestamp",     "critical"),
    ("arrival_time",       "Arrival Timestamp",      "critical"),
    ("clear_time",         "Clear Timestamp",        "warning"),
    ("incident_type",      "Incident Type",          "critical"),
    ("latitude",           "GPS Latitude",           "warning"),
    ("longitude",          "GPS Longitude",          "warning"),
]


def _parse_dt(val: str | None) -> datetime | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def _check_incident(inc: dict, dept_neris_id: str | None) -> dict:
    errors   = []
    warnings = []
    passed   = []

    inc_id = (
        inc.get("neris_id_incident") or
        inc.get("incident_id") or
        inc.get("incident_number") or ""
    )
    inc_type = inc.get("incident_type", "")

    # ── Required field presence ──
    for field, label, severity in REQUIRED_FIELDS:
        val = inc.get(field)
        if not val:
            msg = f"{label} is missing"
            (errors if severity == "critical" else warnings).append(msg)
        else:
            passed.append(label)

    # ── NERIS department ID format ──
    if dept_neris_id:
        if not _NERIS_ID_RE.match(dept_neris_id):
            errors.append(f"Department NERIS ID '{dept_neris_id}' must match FD########")
        else:
            passed.append("Department NERIS ID")

    # ── Incident number format ──
    if inc_id and not _INC_NUM_RE.match(inc_id):
        errors.append(f"Incident number '{inc_id}' contains invalid characters (only A-Z, 0-9, -, :, _ allowed)")

    # ── Timestamp ordering ──
    dispatch = _parse_dt(inc.get("call_create"))
    arrival  = _parse_dt(inc.get("arrival_time"))
    clear    = _parse_dt(inc.get("clear_time"))

    if dispatch and arrival:
        delta = (arrival - dispatch).total_seconds()
        if delta < 0:
            errors.append("Arrival time is before dispatch time")
        elif delta > 7200:
            warnings.append(f"Response time is {int(delta/60)}m — unusually long (>2 hr)")
        else:
            passed.append("Timestamp ordering")

    if arrival and clear:
        if (clear - arrival).total_seconds() < 0:
            errors.append("Clear time is before arrival time")

    # ── GPS bounds (contiguous US + territories) ──
    try:
        lat = float(inc.get("latitude") or 0)
        lon = float(inc.get("longitude") or 0)
        if lat and lon:
            if not (17.0 <= lat <= 72.0):
                errors.append(f"Latitude {lat} is outside valid US range (17–72)")
            elif not (-180.0 <= lon <= -65.0):
                errors.append(f"Longitude {lon} is outside valid US range (-180 to -65)")
            else:
                passed.append("GPS coordinates in range")
    except (TypeError, ValueError):
        errors.append("GPS coordinates are not valid numbers")

    # ── Incident type non-empty ──
    if inc_type and len(inc_type.strip()) < 2:
        warnings.append("Incident type is very short — verify it maps to a NERIS type code")

    status = "error" if errors else ("warning" if warnings else "ready")

    return {
        "incident_id": inc_id or f"record-{id(inc)}",
        "incident_type": inc_type or "Unknown",
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def pre_validate(incidents: list[dict], dept_neris_id: str | None = None) -> dict:
    """
    Run local pre-submission checks on a list of incidents.
    Returns a summary + per-incident results.
    """
    results = [_check_incident(inc, dept_neris_id) for inc in incidents]

    ready_count   = sum(1 for r in results if r["status"] == "ready")
    warning_count = sum(1 for r in results if r["status"] == "warning")
    error_count   = sum(1 for r in results if r["status"] == "error")
    total         = len(results)

    # Aggregate most common errors for the action guide
    from collections import Counter
    all_errors   = [e for r in results for e in r["errors"]]
    all_warnings = [w for r in results for w in r["warnings"]]
    top_errors   = Counter(all_errors).most_common(5)
    top_warnings = Counter(all_warnings).most_common(5)

    submittable = ready_count + warning_count  # warnings don't block submission

    return {
        "total":         total,
        "ready":         ready_count,
        "with_warnings": warning_count,
        "with_errors":   error_count,
        "submittable":   submittable,
        "pct_ready":     round(submittable / total * 100) if total else 0,
        "top_errors":    top_errors,
        "top_warnings":  top_warnings,
        "incidents":     results,
        "dept_neris_id": dept_neris_id,
    }
