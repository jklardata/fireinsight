"""
Mock NERIS incident data for local development without API credentials.
Loads from sample_nfirs_large.csv (1,012 incidents, full calendar year 2024)
via the NFIRS→NERIS converter so the schema matches exactly what the API returns.
"""

import os
import random
from datetime import datetime

random.seed(42)

DEPT = {
    "neris_id": "MOCK-001",
    "name": "Riverside Volunteer Fire Department",
    "state": "VA",
}

# Centre of the department's response area (Chesterfield County, VA)
_LAT_CENTER  =  37.378
_LON_CENTER  = -77.506
_LAT_SPREAD  =  0.08
_LON_SPREAD  =  0.10

_CSV_PATH = os.path.join(os.path.dirname(__file__), "sample_nfirs_large.csv")

# Cache so we only parse the CSV once per process
_INCIDENT_CACHE: list[dict] | None = None


def _load_from_csv() -> list[dict]:
    from convert.nfirs_to_neris import convert_nfirs_csv

    with open(_CSV_PATH, "r", encoding="utf-8") as f:
        csv_text = f.read()

    incidents, _ = convert_nfirs_csv(csv_text)

    rng = random.Random(99)  # separate seed so lat/lon is stable
    enriched = []
    for i, inc in enumerate(incidents):
        inc["neris_id_incident"] = f"MOCK-INC-{i+1:04d}"
        inc["neris_id_entity"]   = DEPT["neris_id"]
        inc["status"]            = "APPROVED"
        # Scatter incidents across a realistic response area
        inc["latitude"]  = round(_LAT_CENTER + rng.uniform(-_LAT_SPREAD, _LAT_SPREAD), 6)
        inc["longitude"] = round(_LON_CENTER + rng.uniform(-_LON_SPREAD, _LON_SPREAD), 6)
        enriched.append(inc)

    return enriched


def generate_incidents(
    n: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    global _INCIDENT_CACHE
    if _INCIDENT_CACHE is None:
        _INCIDENT_CACHE = _load_from_csv()

    incidents = _INCIDENT_CACHE

    # Apply date filter when requested
    if start or end:
        def _in_range(inc: dict) -> bool:
            ts = inc.get("call_create")
            if not ts:
                return True
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                if start and dt < start:
                    return False
                if end and dt > end:
                    return False
            except ValueError:
                pass
            return True

        incidents = [i for i in incidents if _in_range(i)]

    return incidents
