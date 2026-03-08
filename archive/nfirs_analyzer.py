"""
Historical NFIRS Archive Analyzer
Parses old NFIRS CSV exports, normalizes them, and compares to current NERIS data.
Produces 5/10-year trend analysis alongside current NERIS baseline.
"""
import csv
import io
from collections import defaultdict
from datetime import datetime


# ── NFIRS incident type code mapping to readable categories ──────────────────
NFIRS_TYPE_MAP = {
    "1": "Fire",
    "10": "Fire — Other",
    "11": "Building Fire",
    "12": "Fires in structures other than buildings",
    "13": "Mobile property (vehicle) fire",
    "14": "Natural vegetation fire",
    "15": "Outside rubbish, trash or waste fire",
    "16": "Special outside fire",
    "17": "Cultivated vegetation, crop fire",
    "2":  "Overpressure/explosion",
    "3":  "Rescue & EMS",
    "30": "Rescue, EMS — Other",
    "31": "Medical assist",
    "32": "EMS call",
    "33": "Water & ice related rescue",
    "34": "Motor vehicle accident with injuries",
    "35": "Extrication, rescue",
    "36": "Water & ice related rescue",
    "4":  "Hazmat",
    "40": "Hazardous condition",
    "41": "Combustible/flammable spill",
    "42": "Chemical hazard",
    "43": "Fuel burner/boiler malfunction",
    "44": "Electrical wiring/equipment problem",
    "45": "Biological hazard",
    "46": "Nuclear condition",
    "5":  "Service Call",
    "50": "Service call",
    "51": "Public service assistance",
    "52": "Removal of victim",
    "53": "Public service",
    "6":  "Good intent call",
    "60": "Good intent call",
    "61": "Dispatched & cancelled en route",
    "62": "No incident found on arrival",
    "63": "Controlled burning",
    "7":  "False alarm & false call",
    "70": "False alarm/false call",
    "71": "Malicious, mischievous false call",
    "72": "System or detector malfunction",
    "73": "Smoke detector malfunction",
    "74": "Detector activation, no fire",
    "8":  "Severe weather & natural disasters",
    "9":  "Special incident type",
}

NFIRS_CATEGORY_MAP = {
    "1": "Fire", "10": "Fire", "11": "Fire", "12": "Fire",
    "13": "Fire", "14": "Fire", "15": "Fire", "16": "Fire", "17": "Fire",
    "2": "Fire",
    "3": "EMS", "30": "EMS", "31": "EMS", "32": "EMS",
    "33": "Rescue", "34": "EMS", "35": "Rescue", "36": "Rescue",
    "4": "Hazmat", "40": "Hazmat", "41": "Hazmat", "42": "Hazmat",
    "43": "Hazmat", "44": "Hazmat", "45": "Hazmat", "46": "Hazmat",
    "5": "Service Call", "50": "Service Call", "51": "Service Call",
    "52": "Service Call", "53": "Service Call",
    "6": "Good Intent", "60": "Good Intent", "61": "Good Intent",
    "62": "Good Intent", "63": "Good Intent",
    "7": "False Alarm", "70": "False Alarm", "71": "False Alarm",
    "72": "False Alarm", "73": "False Alarm", "74": "False Alarm",
    "8": "Other", "9": "Other",
}

# Common NFIRS CSV column names (headers vary by RMS vendor)
NFIRS_DATE_FIELDS = [
    "alarm_date", "INC_DATE", "ALARM_DATE", "alarm date",
    "Alarm Date", "inc_date", "date", "Date", "DATE",
]
NFIRS_TYPE_FIELDS = [
    "inc_type", "INC_TYPE", "incident_type", "INCIDENT_TYPE",
    "inc_type_id", "type", "Type", "TYPE",
]
NFIRS_YEAR_FIELDS = [
    "year", "YEAR", "cal_year", "CAL_YEAR", "Year",
]


def _find_col(headers: list, candidates: list) -> str | None:
    for c in candidates:
        if c in headers:
            return c
    for c in candidates:
        for h in headers:
            if c.lower() == h.lower():
                return h
    return None


def _parse_year(val: str) -> int | None:
    if not val:
        return None
    val = val.strip()
    # Try YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y"):
        try:
            return datetime.strptime(val, fmt).year
        except ValueError:
            pass
    # Try just extracting 4-digit year
    import re
    m = re.search(r"(19|20)\d{2}", val)
    if m:
        return int(m.group())
    return None


def _normalize_type_code(raw: str) -> str:
    if not raw:
        return "Other"
    raw = raw.strip()
    # Match on first 1-3 digit prefix
    for length in (3, 2, 1):
        prefix = raw[:length]
        if prefix in NFIRS_CATEGORY_MAP:
            return NFIRS_CATEGORY_MAP[prefix]
    return "Other"


def _parse_nfirs_csv(csv_text: str) -> list[dict]:
    """Parse a NFIRS CSV and return normalized incident dicts."""
    reader = csv.DictReader(io.StringIO(csv_text))
    headers = reader.fieldnames or []

    date_col = _find_col(headers, NFIRS_DATE_FIELDS)
    type_col = _find_col(headers, NFIRS_TYPE_FIELDS)
    year_col = _find_col(headers, NFIRS_YEAR_FIELDS)

    records = []
    for row in reader:
        year = None
        if year_col and row.get(year_col):
            try:
                year = int(row[year_col])
            except ValueError:
                pass
        if year is None and date_col:
            year = _parse_year(row.get(date_col, ""))
        if year is None:
            continue  # skip rows without a parseable year

        raw_type = row.get(type_col, "") if type_col else ""
        category = _normalize_type_code(raw_type)

        records.append({"year": year, "category": category, "raw_type": raw_type})

    return records


def _yearly_summary(records: list[dict]) -> dict:
    """Summarize by year: total + by category."""
    by_year: dict = defaultdict(lambda: defaultdict(int))
    for r in records:
        by_year[r["year"]]["total"] += 1
        by_year[r["year"]][r["category"]] += 1
    return {yr: dict(cats) for yr, cats in sorted(by_year.items())}


def _current_neris_summary(incidents: list) -> dict:
    """Summarize current NERIS incidents into the same shape."""
    cats: dict = defaultdict(int)
    for i in incidents:
        t = (i.get("incident_type") or "").lower()
        if "fire" in t or "explosion" in t:
            cats["Fire"] += 1
        elif "ems" in t or "medical" in t or "mva" in t:
            cats["EMS"] += 1
        elif "hazmat" in t or "chemical" in t or "gas" in t:
            cats["Hazmat"] += 1
        elif "rescue" in t or "extrication" in t:
            cats["Rescue"] += 1
        elif "false alarm" in t or "alarm" in t:
            cats["False Alarm"] += 1
        elif "service" in t or "public assist" in t:
            cats["Service Call"] += 1
        else:
            cats["Other"] += 1
    cats["total"] = len(incidents)
    return dict(cats)


def _trend_stats(yearly: dict, category: str) -> dict:
    """Compute trend for a category across years."""
    years = sorted(yearly.keys())
    values = [yearly[y].get(category, 0) for y in years]
    if len(values) < 2:
        return {"trend": "insufficient_data"}

    first, last = values[0], values[-1]
    if first == 0:
        pct_change = None
    else:
        pct_change = round((last - first) / first * 100, 1)

    # Simple linear regression slope
    n = len(values)
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    num = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((xs[i] - x_mean) ** 2 for i in range(n))
    slope = round(num / den, 2) if den != 0 else 0

    direction = "increasing" if slope > 0.3 else "decreasing" if slope < -0.3 else "stable"

    return {
        "first_year":  years[0],
        "last_year":   years[-1],
        "first_value": first,
        "last_value":  last,
        "pct_change":  pct_change,
        "slope":       slope,
        "direction":   direction,
        "years":       years,
        "values":      values,
    }


def analyze_nfirs_archive(csv_text: str, current_incidents: list, dept_name: str) -> dict:
    records = _parse_nfirs_csv(csv_text)

    if not records:
        raise ValueError("No valid incident records found. Check that this is a NFIRS Basic Module CSV with alarm date and incident type columns.")

    yearly  = _yearly_summary(records)
    years   = sorted(yearly.keys())
    span    = years[-1] - years[0] + 1 if len(years) > 1 else 1

    # Current year NERIS baseline
    current_year  = datetime.now().year
    current_total = len(current_incidents)
    neris_summary = _current_neris_summary(current_incidents)

    # Append current NERIS year to yearly for trend lines
    if current_total and current_year not in yearly:
        yearly[current_year] = neris_summary

    # Compute trends per category
    categories = ["Fire", "EMS", "Hazmat", "Rescue", "False Alarm", "Service Call"]
    trends = {}
    for cat in categories:
        trends[cat] = _trend_stats(yearly, cat)

    total_trend = _trend_stats(yearly, "total")

    # Headline insights
    insights = []
    for cat, t in trends.items():
        if t.get("pct_change") is not None and abs(t["pct_change"]) >= 10:
            direction_word = "up" if t["pct_change"] > 0 else "down"
            insights.append(
                f"{cat} incidents are {direction_word} {abs(t['pct_change'])}% "
                f"over {span} years ({t['first_year']}–{t['last_year']})"
            )
    if total_trend.get("pct_change") is not None:
        insights.insert(0,
            f"Total incidents {'increased' if total_trend['pct_change'] > 0 else 'decreased'} "
            f"by {abs(total_trend['pct_change'])}% over {span} years"
        )

    return {
        "dept_name":      dept_name,
        "record_count":   len(records),
        "year_span":      span,
        "years_in_data":  years,
        "yearly":         yearly,
        "current_year":   current_year,
        "current_total":  current_total,
        "neris_baseline": neris_summary,
        "trends":         trends,
        "total_trend":    total_trend,
        "insights":       insights,
        "categories":     categories,
    }
