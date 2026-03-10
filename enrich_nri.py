"""
Enrich department JSON files with FEMA National Risk Index (NRI) v1.2 data.

Usage:
  python3 enrich_nri.py --state NV
  python3 enrich_nri.py --state CA

Reads: data/nri/NRI_Table_Counties.csv
Adds nri: { risk_score, risk_rating, eal_total, hazards: [...] } to each dept JSON.
"""

import argparse
import csv
import json
from pathlib import Path

DEPT_DIR = Path(__file__).parent / "data" / "departments"
NRI_CSV  = Path(__file__).parent / "data" / "nri" / "NRI_Table_Counties.csv"

STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "FL": "12", "GA": "13", "HI": "15", "ID": "16",
    "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22",
    "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40",
    "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47",
    "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56", "DC": "11",
}

HAZARDS = [
    ("AVLN", "Avalanche"),
    ("CFLD", "Coastal Flooding"),
    ("CWAV", "Cold Wave"),
    ("DRGT", "Drought"),
    ("ERQK", "Earthquake"),
    ("HAIL", "Hail"),
    ("HWAV", "Heat Wave"),
    ("HRCN", "Hurricane"),
    ("ISTM", "Ice Storm"),
    ("IFLD", "Inland Flooding"),
    ("LNDS", "Landslide"),
    ("LTNG", "Lightning"),
    ("SWND", "Strong Wind"),
    ("TRND", "Tornado"),
    ("TSUN", "Tsunami"),
    ("VLCN", "Volcanic Activity"),
    ("WFIR", "Wildfire"),
    ("WNTW", "Winter Weather"),
]


def load_nri_index() -> dict:
    """Load NRI CSV into a dict keyed by STCOFIPS."""
    index = {}
    with open(NRI_CSV, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            fips = row.get("STCOFIPS", "").strip()
            if fips:
                index[fips] = row
    print(f"  Loaded {len(index)} counties from NRI CSV")
    return index


def fv(row: dict, key: str) -> float | None:
    try:
        v = float(row.get(key, "") or "")
        return v if v >= 0 else None
    except (ValueError, TypeError):
        return None


def parse_nri(row: dict) -> dict:
    hazards = []
    for prefix, label in HAZARDS:
        score  = fv(row, f"{prefix}_RISKS")
        rating = (row.get(f"{prefix}_RISKR") or "").strip()
        eal    = fv(row, f"{prefix}_EALT")

        # Skip hazards marked Not Applicable
        if rating in ("Not Applicable", ""):
            continue
        if score is None and eal is None:
            continue

        hazards.append({
            "key":    prefix,
            "label":  label,
            "score":  round(score, 1) if score is not None else None,
            "rating": rating,
            "eal":    round(eal) if eal is not None else None,
        })

    # Sort by score descending so highest-risk hazards appear first
    hazards.sort(key=lambda h: h["score"] or 0, reverse=True)

    return {
        "risk_score":  round(fv(row, "RISK_SCORE"), 1) if fv(row, "RISK_SCORE") is not None else None,
        "risk_rating": (row.get("RISK_RATNG") or "").strip() or None,
        "eal_total":   round(fv(row, "EAL_VALT")) if fv(row, "EAL_VALT") is not None else None,
        "sovi_score":  round(fv(row, "SOVI_SCORE"), 1) if fv(row, "SOVI_SCORE") is not None else None,
        "sovi_rating": (row.get("SOVI_RATNG") or "").strip() or None,
        "resl_score":  round(fv(row, "RESL_SCORE"), 1) if fv(row, "RESL_SCORE") is not None else None,
        "resl_rating": (row.get("RESL_RATNG") or "").strip() or None,
        "hazards":     hazards,
        "version":     "v1.2 (December 2025)",
    }


def enrich(state: str):
    state = state.upper()
    state_fips = STATE_FIPS.get(state)
    if not state_fips:
        print(f"Unknown state: {state}")
        return

    nri_index = load_nri_index()
    files = list(DEPT_DIR.glob(f"{state.lower()}-*.json"))
    print(f"Enriching {len(files)} departments in {state} with NRI data...")

    updated = 0
    for f in files:
        dept = json.loads(f.read_text())
        county_raw = dept.get("county", "").strip()
        if not county_raw:
            continue

        stcofips = state_fips + county_raw.zfill(3)
        row = nri_index.get(stcofips)
        if not row:
            print(f"  WARNING: No NRI data for STCOFIPS {stcofips} ({dept.get('name')})")
            continue

        dept["nri"] = parse_nri(row)
        f.write_text(json.dumps(dept, indent=2))
        updated += 1

    print(f"Done. Updated {updated}/{len(files)} department files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    args = parser.parse_args()
    enrich(args.state)
