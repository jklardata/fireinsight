"""
NFIRS → NERIS Converter

Reads NFIRS Basic Module CSV exports and maps fields to NERIS-compatible
incident records. Outputs a list of dicts matching the schema used throughout
FireInsight (same shape as mock_data.py / neris.py).

NFIRS field references:
  https://www.nfirs.fema.gov/documentation/reference/

Supported NFIRS modules: Basic (BAS) only in v1.
"""

import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional


# ── NFIRS Incident Type → NERIS label ──────────────────────────────────────
# NFIRS uses 3-digit codes; we map to human-readable NERIS-style labels.
# Reference: NFIRS Incident Type matrix (Table 20)

INCIDENT_TYPE_MAP: dict[str, str] = {
    # Structure fires
    "111": "Fire - Structure Fire",
    "112": "Fire - Structure Fire",
    "113": "Fire - Structure Fire",
    "114": "Fire - Structure Fire",
    "115": "Fire - Structure Fire",
    "116": "Fire - Structure Fire",
    "117": "Fire - Structure Fire",
    "118": "Fire - Structure Fire",
    "120": "Fire - Structure Fire",
    "121": "Fire - Structure Fire",
    "122": "Fire - Structure Fire",
    "123": "Fire - Structure Fire",

    # Vehicle fires
    "130": "Fire - Vehicle Fire",
    "131": "Fire - Vehicle Fire",
    "132": "Fire - Vehicle Fire",
    "133": "Fire - Vehicle Fire",
    "134": "Fire - Vehicle Fire",
    "135": "Fire - Vehicle Fire",
    "136": "Fire - Vehicle Fire",
    "137": "Fire - Vehicle Fire",
    "138": "Fire - Vehicle Fire",

    # Outside fires
    "140": "Fire - Outside/Brush/Grass Fire",
    "141": "Fire - Outside/Brush/Grass Fire",
    "142": "Fire - Outside/Brush/Grass Fire",
    "143": "Fire - Outside/Brush/Grass Fire",
    "150": "Fire - Outside/Brush/Grass Fire",
    "151": "Fire - Outside/Brush/Grass Fire",
    "152": "Fire - Outside/Brush/Grass Fire",
    "153": "Fire - Outside/Brush/Grass Fire",
    "154": "Fire - Outside/Brush/Grass Fire",
    "155": "Fire - Outside/Brush/Grass Fire",
    "160": "Fire - Special Outside Fire",
    "161": "Fire - Special Outside Fire",
    "162": "Fire - Special Outside Fire",
    "163": "Fire - Special Outside Fire",

    # Explosion
    "170": "Fire - Explosion",
    "171": "Fire - Explosion",
    "172": "Fire - Explosion",
    "173": "Fire - Explosion",

    # Rupture / overpressure
    "180": "Hazmat - Rupture/Explosion (No Fire)",

    # Rescue / EMS
    "300": "EMS - Medical Emergency",
    "311": "EMS - Medical Emergency",
    "320": "EMS - Motor Vehicle Accident",
    "321": "EMS - Motor Vehicle Accident",
    "322": "EMS - Motor Vehicle Accident",
    "323": "EMS - Motor Vehicle Accident",
    "324": "EMS - Motor Vehicle Accident",
    "325": "EMS - Motor Vehicle Accident",
    "340": "Rescue - Water",
    "341": "Rescue - Water",
    "342": "Rescue - Water",
    "350": "Rescue - Extrication",
    "351": "Rescue - Extrication",
    "352": "Rescue - Extrication",
    "353": "Rescue - Extrication",
    "360": "Rescue - Water",
    "361": "Rescue - Water",
    "362": "Rescue - Water",
    "363": "Rescue - Water",
    "364": "Rescue - Water",
    "365": "Rescue - Water",
    "370": "Rescue - Technical",
    "371": "Rescue - Technical",
    "372": "Rescue - Technical",
    "373": "Rescue - Technical",
    "374": "Rescue - Technical",
    "381": "EMS - Medical Emergency",

    # Hazmat
    "400": "Hazmat - Hazardous Condition",
    "410": "Hazmat - Combustible/Flammable Spill",
    "411": "Hazmat - Combustible/Flammable Spill",
    "412": "Hazmat - Combustible/Flammable Spill",
    "413": "Hazmat - Combustible/Flammable Spill",
    "420": "Hazmat - Chemical Release",
    "421": "Hazmat - Chemical Release",
    "422": "Hazmat - Chemical Release",
    "423": "Hazmat - Chemical Release",
    "424": "Hazmat - Carbon Monoxide",
    "440": "Hazmat - Electrical",
    "441": "Hazmat - Electrical",
    "442": "Hazmat - Electrical",
    "443": "Hazmat - Electrical",
    "444": "Hazmat - Electrical",
    "445": "Hazmat - Electrical",
    "451": "Hazmat - Biological",
    "460": "Hazmat - Radioactive",
    "461": "Hazmat - Radioactive",
    "462": "Hazmat - Radioactive",

    # Service calls
    "500": "Service Call - Public Assist",
    "510": "Service Call - Public Assist",
    "511": "Service Call - Public Assist",
    "512": "Service Call - Public Assist",
    "520": "Service Call - Public Assist",
    "521": "Service Call - Public Assist",
    "522": "Service Call - Public Assist",
    "531": "Service Call - Public Assist",
    "540": "Service Call - Animal Rescue",
    "541": "Service Call - Animal Rescue",
    "542": "Service Call - Animal Rescue",
    "550": "Service Call - Public Assist",
    "551": "Service Call - Public Assist",
    "552": "Service Call - Public Assist",
    "553": "Service Call - Public Assist",
    "554": "Service Call - Public Assist",
    "561": "Service Call - Public Assist",

    # False alarms
    "600": "False Alarm - Undetermined",
    "611": "False Alarm - System Malfunction",
    "621": "False Alarm - Malicious",
    "622": "False Alarm - Malicious",
    "631": "False Alarm - System Malfunction",
    "632": "False Alarm - System Malfunction",
    "641": "False Alarm - Smoke Scare",
    "650": "False Alarm - System Malfunction",
    "651": "False Alarm - System Malfunction",
    "652": "False Alarm - System Malfunction",
    "653": "False Alarm - System Malfunction",
    "661": "False Alarm - Steam/Other Gas",
    "671": "False Alarm - System Malfunction",

    # Severe weather
    "700": "Severe Weather - Standby",
    "711": "Severe Weather - Wind",
    "712": "Severe Weather - Ice/Sleet",
    "713": "Severe Weather - Ice/Sleet",
    "714": "Severe Weather - Flood",
    "715": "Severe Weather - Flood",
    "720": "Severe Weather - Standby",
    "721": "Severe Weather - Standby",
    "722": "Severe Weather - Standby",
    "723": "Severe Weather - Standby",

    # Special incident
    "800": "Special Incident - Other",
    "812": "Special Incident - Police Assist",
    "813": "Special Incident - Police Assist",

    # Other
    "900": "Other",
    "911": "Other",
    "900": "Other",
}


def _nfirs_code_to_neris(code: str) -> str:
    """Map an NFIRS 3-digit incident type code to a NERIS label."""
    code = (code or "").strip().lstrip("0") or "0"
    # Try exact match first (zero-padded to 3)
    padded = code.zfill(3)
    if padded in INCIDENT_TYPE_MAP:
        return INCIDENT_TYPE_MAP[padded]
    # Try category-level fallback (first digit + "00")
    category = code[0] + "00" if code else "000"
    return INCIDENT_TYPE_MAP.get(category, f"Other (NFIRS {padded})")


def _parse_nfirs_datetime(date_str: str, time_str: str) -> Optional[str]:
    """
    Parse NFIRS date (MMDDYYYY or YYYYMMDD) + time (HHMM) into ISO 8601.
    Returns None if unparseable.
    """
    date_str = (date_str or "").strip()
    time_str = (time_str or "").strip().zfill(4)

    if not date_str:
        return None

    for fmt in ("%m%d%Y", "%Y%m%d", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(date_str, fmt)
            hour = int(time_str[:2]) if len(time_str) >= 2 else 0
            minute = int(time_str[2:4]) if len(time_str) >= 4 else 0
            dt = d.replace(hour=hour, minute=minute, tzinfo=timezone.utc)
            return dt.isoformat()
        except (ValueError, IndexError):
            continue

    return None


def _parse_casualties(row: dict) -> dict:
    """Extract casualty counts from NFIRS row."""
    def _int(key: str) -> int:
        try:
            return int((row.get(key) or "0").strip())
        except ValueError:
            return 0

    return {
        "firefighter_deaths": _int("FF_DEATH"),
        "civilian_deaths": _int("OTH_DEATH"),
        "firefighter_injuries": _int("FF_INJ"),
        "civilian_injuries": _int("OTH_INJ"),
    }


def _parse_losses(row: dict) -> dict:
    """Extract property/contents loss from NFIRS row."""
    def _float(key: str) -> Optional[float]:
        val = (row.get(key) or "").strip()
        if not val or val in ("0", "00000000"):
            return None
        try:
            return float(val)
        except ValueError:
            return None

    return {
        "property_loss_usd": _float("PROP_LOSS"),
        "contents_loss_usd": _float("CONT_LOSS"),
    }


# ── Common column name aliases ──────────────────────────────────────────────
# Different NFIRS export tools use slightly different column headers.
# We normalise them all to the canonical NFIRS field names.

_ALIASES: dict[str, str] = {
    # Incident date
    "INC_DATE": "INC_DATE",
    "INCIDENT_DATE": "INC_DATE",
    "INCDATE": "INC_DATE",
    # Incident number
    "INC_NO": "INC_NO",
    "INCIDENT_NUMBER": "INC_NO",
    "INCNO": "INC_NO",
    # Alarm time
    "ALARM": "ALARM",
    "ALARM_TIME": "ALARM",
    "ALARMTIME": "ALARM",
    # Arrival time
    "ARRIVAL": "ARRIVAL",
    "ARRIVAL_TIME": "ARRIVAL",
    "ARRIVALTIME": "ARRIVAL",
    # Incident controlled time
    "INC_CONT": "INC_CONT",
    "CONTROLLED_TIME": "INC_CONT",
    # Cleared time
    "LU_CLEAR": "LU_CLEAR",
    "CLEAR_TIME": "LU_CLEAR",
    # Incident type
    "INC_TYPE": "INC_TYPE",
    "INCIDENT_TYPE": "INC_TYPE",
    "INCTYPE": "INC_TYPE",
    # FDID / state
    "FDID": "FDID",
    "STATE": "STATE",
    # Casualties
    "FF_DEATH": "FF_DEATH",
    "OTH_DEATH": "OTH_DEATH",
    "FF_INJ": "FF_INJ",
    "OTH_INJ": "OTH_INJ",
    # Losses
    "PROP_LOSS": "PROP_LOSS",
    "CONT_LOSS": "CONT_LOSS",
    # Aid given/received
    "AID": "AID",
    # Latitude / longitude (some export tools include these)
    "LATITUDE": "LATITUDE",
    "LAT": "LATITUDE",
    "LONGITUDE": "LONGITUDE",
    "LON": "LONGITUDE",
    "LONG": "LONGITUDE",
}


def _normalise_row(raw_row: dict) -> dict:
    """Remap aliased column names to canonical NFIRS names."""
    normalised = {}
    for k, v in raw_row.items():
        canonical = _ALIASES.get(k.strip().upper(), k.strip().upper())
        normalised[canonical] = v
    return normalised


def convert_nfirs_csv(csv_text: str) -> tuple[list[dict], list[str]]:
    """
    Convert NFIRS Basic Module CSV text to a list of NERIS-compatible
    incident dicts.

    Returns:
        (incidents, warnings)
        incidents  — list of dicts matching FireInsight's internal schema
        warnings   — list of human-readable warnings about unparseable rows
    """
    incidents: list[dict] = []
    warnings: list[str] = []

    reader = csv.DictReader(io.StringIO(csv_text.strip()))

    if not reader.fieldnames:
        raise ValueError("CSV appears to be empty or has no header row.")

    for i, raw_row in enumerate(reader, start=2):  # row 2 = first data row
        row = _normalise_row(raw_row)

        inc_no = row.get("INC_NO", "").strip() or f"ROW-{i}"

        # Timestamps
        inc_date = row.get("INC_DATE", "")
        alarm_time = _parse_nfirs_datetime(inc_date, row.get("ALARM", ""))
        arrival_time = _parse_nfirs_datetime(inc_date, row.get("ARRIVAL", ""))
        controlled_time = _parse_nfirs_datetime(inc_date, row.get("INC_CONT", ""))
        cleared_time = _parse_nfirs_datetime(inc_date, row.get("LU_CLEAR", ""))

        if not alarm_time:
            warnings.append(f"Row {i} (INC_NO={inc_no}): could not parse alarm date/time — skipping timestamps.")

        # Incident type
        raw_type = row.get("INC_TYPE", "").strip()
        neris_type = _nfirs_code_to_neris(raw_type) if raw_type else "Other"

        # Casualties & losses
        casualties = _parse_casualties(row)
        losses = _parse_losses(row)

        # Aid type → mutual aid flag
        aid = row.get("AID", "").strip()
        mutual_aid = aid in ("3", "4")  # NFIRS: 3=given, 4=received

        incident = {
            # Core identity
            "incident_id": inc_no,
            "source": "NFIRS",
            "nfirs_inc_type": raw_type,

            # Timestamps (ISO 8601)
            "call_create": alarm_time,
            "arrival_time": arrival_time,
            "controlled_time": controlled_time,
            "cleared_time": cleared_time,

            # Classification
            "incident_type": neris_type,

            # Location (if available)
            "latitude": row.get("LATITUDE") or None,
            "longitude": row.get("LONGITUDE") or None,

            # Department
            "fdid": row.get("FDID", "").strip() or None,
            "state": row.get("STATE", "").strip() or None,

            # Outcomes
            **casualties,
            **losses,
            "mutual_aid": mutual_aid,
        }

        incidents.append(incident)

    return incidents, warnings


def convert_nfirs_csv_to_json(csv_text: str, pretty: bool = True) -> tuple[str, list[str]]:
    """Convenience wrapper: returns JSON string + warnings."""
    incidents, warnings = convert_nfirs_csv(csv_text)
    indent = 2 if pretty else None
    return json.dumps(incidents, indent=indent, default=str), warnings


def summarise_conversion(incidents: list[dict]) -> dict:
    """Return a quick summary dict for display after conversion."""
    from collections import Counter
    types = Counter(i["incident_type"] for i in incidents)
    with_timestamps = sum(1 for i in incidents if i.get("call_create"))
    with_location   = sum(1 for i in incidents if i.get("latitude") and i.get("longitude"))
    ff_injuries = sum(i.get("firefighter_injuries", 0) or 0 for i in incidents)
    civ_injuries = sum(i.get("civilian_injuries", 0) or 0 for i in incidents)

    return {
        "total": len(incidents),
        "with_timestamps": with_timestamps,
        "with_location": with_location,
        "top_types": dict(types.most_common(5)),
        "firefighter_injuries": ff_injuries,
        "civilian_injuries": civ_injuries,
    }
