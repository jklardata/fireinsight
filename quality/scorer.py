"""
NERIS Data Quality Scorer

Evaluates completeness and validity of NERIS incident records.
Returns a structured quality report used both by the UI and Claude narrative.

Scoring model (100 pts per record):
  Critical  — without these, the record is nearly useless for analysis
  Important — needed for most reports and grant narratives
  Supplemental — adds depth; absence lowers score but isn't fatal

Field weights:
  incident_type      20  critical
  call_create        15  critical  (alarm time)
  arrival_time       15  critical
  cleared_time       10  important
  controlled_time     8  important
  location           12  important  (lat+lon together)
  incident_id         5  supplemental
  casualty_complete  10  supplemental (only checked for fire/rescue incidents)
  loss_complete       5  supplemental (only checked for fire incidents)
  ─────────────────────
  max possible       100

Validity checks (flagged as issues but don't reduce base score):
  - Arrival before alarm
  - Response time > 2 hours or < 30 seconds
  - Cleared before controlled
  - Duplicate incident IDs
  - Future-dated incidents
"""

from datetime import datetime, timezone
from collections import Counter, defaultdict
from typing import Optional


# ── Field definitions ────────────────────────────────────────────────────────

FIELDS = [
    # (key, label, weight, tier, check_fn)
    # check_fn receives the incident dict and returns True if field is present+valid
    ("incident_type",  "Incident Type",     20, "critical"),
    ("call_create",    "Alarm Time",        15, "critical"),
    ("arrival_time",   "Arrival Time",      15, "critical"),
    ("cleared_time",   "Cleared Time",      10, "important"),
    ("controlled_time","Controlled Time",    8, "important"),
    ("location",       "Location (lat/lon)", 12, "important"),
    ("incident_id",    "Incident ID",        5, "supplemental"),
    ("casualty",       "Casualty Fields",   10, "supplemental"),
    ("loss",           "Property Loss",      5, "supplemental"),
]

FIRE_TYPES = {
    "fire", "structure fire", "vehicle fire", "brush", "grass", "wildfire",
    "outside fire", "explosion",
}
RESCUE_TYPES = {
    "rescue", "ems", "medical", "extrication", "water rescue", "technical rescue",
    "mva", "motor vehicle",
}


def _is_fire(incident: dict) -> bool:
    t = (incident.get("incident_type") or "").lower()
    return any(f in t for f in FIRE_TYPES)


def _is_rescue_or_ems(incident: dict) -> bool:
    t = (incident.get("incident_type") or "").lower()
    return any(r in t for r in RESCUE_TYPES)


def _present(val) -> bool:
    """True if value is non-null and non-empty."""
    if val is None:
        return False
    if isinstance(val, str):
        return val.strip() not in ("", "0", "None", "null")
    return True


def _parse_dt(val) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


def _score_record(incident: dict) -> tuple[int, list[str]]:
    """
    Returns (score 0-100, list of missing/invalid field labels).
    """
    score = 0
    missing = []

    for field_key, label, weight, _tier in FIELDS:

        if field_key == "location":
            lat = incident.get("latitude") or incident.get("lat")
            lon = incident.get("longitude") or incident.get("lon")
            if _present(lat) and _present(lon):
                score += weight
            else:
                missing.append(label)

        elif field_key == "casualty":
            # Only penalise for fire/rescue incidents
            if _is_fire(incident) or _is_rescue_or_ems(incident):
                has_ff = _present(incident.get("firefighter_injuries")) or _present(incident.get("FF_INJ"))
                has_cv = _present(incident.get("civilian_injuries")) or _present(incident.get("OTH_INJ"))
                # Both present → full credit; one present → half; neither → zero
                if has_ff and has_cv:
                    score += weight
                elif has_ff or has_cv:
                    score += weight // 2
                    missing.append(f"{label} (partial)")
                else:
                    missing.append(label)
            else:
                score += weight  # not applicable — full credit

        elif field_key == "loss":
            if _is_fire(incident):
                has_prop = _present(incident.get("property_loss_usd")) or _present(incident.get("PROP_LOSS"))
                if has_prop:
                    score += weight
                else:
                    missing.append(label)
            else:
                score += weight  # not applicable — full credit

        else:
            val = incident.get(field_key)
            if _present(val):
                score += weight
            else:
                missing.append(label)

    return score, missing


def _validity_flags(incident: dict) -> list[str]:
    """Return a list of validity issue strings for a single record."""
    flags = []

    alarm   = _parse_dt(incident.get("call_create"))
    arrival = _parse_dt(incident.get("arrival_time"))
    ctrl    = _parse_dt(incident.get("controlled_time"))
    cleared = _parse_dt(incident.get("cleared_time"))
    now     = datetime.now(timezone.utc)

    if alarm and alarm.tzinfo is None:
        alarm = alarm.replace(tzinfo=timezone.utc)
    if arrival and arrival.tzinfo is None:
        arrival = arrival.replace(tzinfo=timezone.utc)
    if ctrl and ctrl.tzinfo is None:
        ctrl = ctrl.replace(tzinfo=timezone.utc)
    if cleared and cleared.tzinfo is None:
        cleared = cleared.replace(tzinfo=timezone.utc)

    if alarm and alarm > now:
        flags.append("Future-dated alarm time")

    if alarm and arrival:
        delta = (arrival - alarm).total_seconds()
        if delta < 0:
            flags.append("Arrival before alarm")
        elif delta < 30:
            flags.append("Response time < 30 seconds (possible error)")
        elif delta > 7200:
            flags.append("Response time > 2 hours (possible error)")

    if ctrl and cleared and cleared < ctrl:
        flags.append("Cleared before controlled time")

    if alarm and cleared:
        total = (cleared - alarm).total_seconds()
        if total > 86400:
            flags.append("Incident duration > 24 hours (possible error)")

    return flags


def score_incidents(incidents: list[dict]) -> dict:
    """
    Main entry point. Returns a full quality report dict.
    """
    if not incidents:
        return {}

    total = len(incidents)
    record_scores = []
    field_missing_counts = defaultdict(int)
    flag_counts = defaultdict(int)
    flagged_records = []
    inc_ids_seen = Counter()

    for inc in incidents:
        score, missing = _score_record(inc)
        flags = _validity_flags(inc)

        # Duplicate ID check
        inc_id = str(inc.get("incident_id") or "").strip()
        if inc_id:
            inc_ids_seen[inc_id] += 1

        for m in missing:
            field_missing_counts[m] += 1
        for f in flags:
            flag_counts[f] += 1

        record_scores.append({
            "incident_id": inc_id or f"record-{len(record_scores)+1}",
            "incident_type": inc.get("incident_type", "Unknown"),
            "score": score,
            "missing": missing,
            "flags": flags,
        })

    # Duplicate IDs
    dup_count = sum(1 for c in inc_ids_seen.values() if c > 1)
    if dup_count:
        flag_counts[f"Duplicate incident IDs"] += dup_count

    # Aggregate stats
    scores = [r["score"] for r in record_scores]
    overall = round(sum(scores) / total)

    # Grade
    if overall >= 85:
        grade, grade_label = "A", "Excellent"
    elif overall >= 70:
        grade, grade_label = "B", "Good"
    elif overall >= 55:
        grade, grade_label = "C", "Fair"
    elif overall >= 40:
        grade, grade_label = "D", "Poor"
    else:
        grade, grade_label = "F", "Critical"

    # Field completion rates
    field_completion = []
    for field_key, label, weight, tier in FIELDS:
        missing_count = field_missing_counts.get(label, 0)
        # also check partial
        partial_label = f"{label} (partial)"
        missing_count += field_missing_counts.get(partial_label, 0)
        pct = round((1 - missing_count / total) * 100)
        field_completion.append({
            "label": label,
            "tier": tier,
            "weight": weight,
            "completion_pct": pct,
            "missing_count": missing_count,
        })
    field_completion.sort(key=lambda x: x["completion_pct"])

    # Worst records (bottom 10 by score)
    worst = sorted(record_scores, key=lambda r: r["score"])[:10]

    # Score distribution buckets
    buckets = {"90-100": 0, "70-89": 0, "50-69": 0, "below-50": 0}
    for s in scores:
        if s >= 90:   buckets["90-100"] += 1
        elif s >= 70: buckets["70-89"] += 1
        elif s >= 50: buckets["50-69"] += 1
        else:         buckets["below-50"] += 1

    return {
        "total": total,
        "overall_score": overall,
        "grade": grade,
        "grade_label": grade_label,
        "field_completion": field_completion,
        "validity_flags": dict(flag_counts),
        "worst_records": worst,
        "score_distribution": buckets,
        "avg_score": overall,
        "min_score": min(scores),
        "max_score": max(scores),
    }
