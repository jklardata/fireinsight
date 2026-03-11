"""
Enrich department JSON files with Census ACS demographics, housing risk,
and FEMA disaster declaration history.

Usage:
  python3 enrich_departments.py --state CA

Adds these fields to each department JSON:
  census: { population, median_income, median_home_value, poverty_rate,
            disability_rate, age_65_plus_pct, vacancy_rate, pre1980_pct,
            renter_pct, pop_density_sq_mi }
  disasters: { total_10yr, total_25yr, recent: [...] }
"""

import argparse
import json
import time
import urllib.request
import urllib.parse
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

DEPT_DIR = Path("data/departments")

# State FIPS codes
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

# Census ACS 5-year variables
CENSUS_VARS = ",".join([
    "NAME",
    "B01003_001E",   # total population
    "B19013_001E",   # median household income
    "B25077_001E",   # median home value
    "B17001_002E",   # people below poverty
    "B17001_001E",   # total for poverty universe
    # male with disability: under5, 5-17, 18-34, 35-64, 65-74, 75+
    "B18101_003E", "B18101_005E", "B18101_007E", "B18101_009E", "B18101_011E", "B18101_013E",
    # female with disability: same age groups
    "B18101_016E", "B18101_018E", "B18101_020E", "B18101_022E", "B18101_024E", "B18101_026E",
    "B18101_001E",   # total disability universe (civilian noninstitutionalized pop)
    "B25002_003E",   # vacant housing units
    "B25002_001E",   # total housing units
    "B25003_003E",   # renter occupied
    "B25003_001E",   # total occupied
    "B25034_002E",   # built 1939 or earlier (oldest)
    "B25034_003E",   # built 1940-1949
    "B25034_004E",   # built 1950-1959
    "B25034_005E",   # built 1960-1969
    "B25034_006E",   # built 1970-1979
    "B25034_001E",   # total structure age universe
    # age 65+: male 65-66, 67-69, 70-74, 75-79, 80-84, 85+
    "B01001_020E", "B01001_021E", "B01001_022E", "B01001_023E", "B01001_024E", "B01001_025E",
    # age 65+: female
    "B01001_044E", "B01001_045E", "B01001_046E", "B01001_047E", "B01001_048E", "B01001_049E",
    "B01001_001E",   # total population (for age pct)
])


def fetch_url(url: str) -> dict | list | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "5AlarmData/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"    ERROR fetching {url}: {e}")
        return None


def fetch_census_county(state_fips: str, county_fips: str) -> dict | None:
    """Fetch ACS 5-year data for a county. Uses two calls: detail table + data profile."""
    county_3 = county_fips.zfill(3)

    # Call 1: B/C tables for population, income, housing, age
    vars1 = ",".join([
        "NAME",
        "B01003_001E",   # total population
        "B19013_001E",   # median household income
        "B25077_001E",   # median home value
        "B17001_002E",   # people below poverty
        "B17001_001E",   # poverty universe
        "B25002_003E",   # vacant housing units
        "B25002_001E",   # total housing units
        "B25003_003E",   # renter occupied
        "B25003_001E",   # total occupied
        "B25034_002E","B25034_003E","B25034_004E","B25034_005E","B25034_006E",  # pre-1980
        "B25034_001E",   # total structure age universe
        "B01001_020E","B01001_021E","B01001_022E","B01001_023E","B01001_024E","B01001_025E",
        "B01001_044E","B01001_045E","B01001_046E","B01001_047E","B01001_048E","B01001_049E",
        "B01001_001E",
    ])
    url1 = f"https://api.census.gov/data/2023/acs/acs5?get={vars1}&for=county:{county_3}&in=state:{state_fips}"
    data1 = fetch_url(url1)

    # Call 2: DP02 data profile for pre-computed disability % (DP02_0072PE = % with disability)
    url2 = f"https://api.census.gov/data/2023/acs/acs5/profile?get=DP02_0072PE&for=county:{county_3}&in=state:{state_fips}"
    data2 = fetch_url(url2)

    if not data1 or len(data1) < 2:
        return None

    raw = dict(zip(data1[0], data1[1]))

    def iv(k):
        try:
            v = int(raw.get(k, -1) or -1)
            return v if v >= 0 else None
        except Exception:
            return None

    def fv(k):
        try:
            v = float(raw.get(k, -1) or -1)
            return v if v >= 0 else None
        except Exception:
            return None

    pop = iv("B01003_001E") or 1
    poverty_num = iv("B17001_002E")
    poverty_denom = iv("B17001_001E") or 1
    vacant = iv("B25002_003E")
    total_units = iv("B25002_001E") or 1
    renter = iv("B25003_003E")
    total_occ = iv("B25003_001E") or 1
    pre1980 = sum(v for v in [
        iv("B25034_002E"), iv("B25034_003E"), iv("B25034_004E"),
        iv("B25034_005E"), iv("B25034_006E"),
    ] if v is not None)
    total_age_units = iv("B25034_001E") or 1
    age65_keys = [
        "B01001_020E","B01001_021E","B01001_022E","B01001_023E","B01001_024E","B01001_025E",
        "B01001_044E","B01001_045E","B01001_046E","B01001_047E","B01001_048E","B01001_049E",
    ]
    age65 = sum(v for v in [iv(k) for k in age65_keys] if v is not None)
    total_age_pop = iv("B01001_001E") or 1

    # Disability % from DP02 data profile (pre-computed, avoids cell-summing errors)
    disability_rate = None
    if data2 and len(data2) >= 2:
        try:
            dp_raw = dict(zip(data2[0], data2[1]))
            val = float(dp_raw.get("DP02_0072PE", -1) or -1)
            if val >= 0:
                disability_rate = round(val, 1)
        except Exception:
            pass

    return {
        "county_name": raw.get("NAME", ""),
        "population": pop,
        "median_income": iv("B19013_001E"),
        "median_home_value": iv("B25077_001E"),
        "poverty_rate": round(poverty_num / poverty_denom * 100, 1) if poverty_num else None,
        "disability_rate": disability_rate,
        "age_65_plus_pct": round(age65 / total_age_pop * 100, 1) if age65 else None,
        "vacancy_rate": round(vacant / total_units * 100, 1) if vacant else None,
        "renter_pct": round(renter / total_occ * 100, 1) if renter else None,
        "pre1980_pct": round(pre1980 / total_age_units * 100, 1) if pre1980 else None,
    }


def fetch_fema_disasters(state: str, county_fips_3: str, state_fips: str) -> dict:
    """Fetch FEMA major disaster declarations (DR type) for a county."""
    fips_county = county_fips_3.zfill(3)
    # declarationType=DR limits to major disaster declarations only (excludes FM fire grants)
    url = (
        f"https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
        f"?fipsStateCode={state_fips}&fipsCountyCode={fips_county}"
        f"&declarationType=DR&limit=200&format=json"
    )
    data = fetch_url(url)
    if not data:
        return {"total_10yr": 0, "total_25yr": 0, "recent": []}

    declarations = data.get("DisasterDeclarationsSummaries", [])
    now = datetime.now(timezone.utc)
    total_10yr = 0
    total_25yr = 0
    recent = []
    seen = set()  # deduplicate by disaster number

    for d in declarations:
        disaster_num = d.get("disasterNumber")
        if disaster_num in seen:
            continue
        seen.add(disaster_num)

        date_str = d.get("declarationDate", "")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            continue
        years_ago = (now - dt).days / 365
        if years_ago <= 25:
            total_25yr += 1
        if years_ago <= 10:
            total_10yr += 1
        if len(recent) < 5:
            recent.append({
                "title": d.get("declarationTitle", ""),
                "type": d.get("incidentType", ""),
                "date": date_str[:10],
                "disaster_number": disaster_num,
            })

    return {"total_10yr": total_10yr, "total_25yr": total_25yr, "recent": recent}


def build_peer_comparison(dept: dict, all_depts: list[dict]) -> dict:
    """Find peer departments (same state, similar incident volume) and compute benchmarks."""
    total = dept.get("total_incidents", 0)
    if total == 0:
        return {}

    peers = [
        d for d in all_depts
        if d.get("fdid") != dept.get("fdid")
        and d.get("total_incidents", 0) > 0
        and abs(d.get("total_incidents", 0) - total) / max(total, 1) < 0.5
    ][:20]

    if not peers:
        return {}

    avg_incidents = sum(p.get("total_incidents", 0) for p in peers) / len(peers)

    station_vals = [int(p["num_stations"]) for p in peers if p.get("num_stations", "").isdigit()]
    avg_stations = round(sum(station_vals) / len(station_vals), 1) if station_vals else None

    def ff_count(d):
        try:
            return int(d.get("num_ff_career") or 0) + int(d.get("num_ff_volunteer") or 0)
        except (ValueError, TypeError):
            return 0

    ff_vals = [p.get("total_incidents", 0) / ff_count(p) for p in peers if ff_count(p) > 0]
    avg_incidents_per_ff = round(sum(ff_vals) / len(ff_vals), 1) if ff_vals else None

    station_inc_vals = [p.get("total_incidents", 0) / int(p["num_stations"]) for p in peers if p.get("num_stations", "").isdigit() and int(p["num_stations"]) > 0]
    avg_incidents_per_station = round(sum(station_inc_vals) / len(station_inc_vals), 1) if station_inc_vals else None

    return {
        "peer_count": len(peers),
        "avg_incidents": round(avg_incidents),
        "avg_stations": avg_stations,
        "avg_incidents_per_ff": avg_incidents_per_ff,
        "avg_incidents_per_station": avg_incidents_per_station,
        "dept_incidents": total,
        "dept_stations": dept.get("num_stations"),
        "incidents_vs_peers": round((total - avg_incidents) / avg_incidents * 100) if avg_incidents else None,
    }


def enrich(state: str):
    state = state.upper()
    state_fips = STATE_FIPS.get(state)
    if not state_fips:
        print(f"Unknown state: {state}")
        return

    files = list(DEPT_DIR.glob(f"{state.lower()}-*.json"))
    print(f"Enriching {len(files)} departments in {state}...")

    # Load all depts for peer comparison
    all_depts = [json.loads(f.read_text()) for f in files]

    # Cache census + disaster data by county FIPS (avoid repeat API calls)
    census_cache: dict = {}
    disaster_cache: dict = {}

    for i, f in enumerate(files):
        dept = json.loads(f.read_text())
        county_raw = dept.get("county", "").strip()
        if not county_raw:
            continue

        county_fips = county_raw.zfill(3)

        print(f"  [{i+1}/{len(files)}] {dept.get('name', f.stem)} (county {county_fips})")

        # Census
        if county_fips not in census_cache:
            time.sleep(0.1)  # be polite to Census API
            census_cache[county_fips] = fetch_census_county(state_fips, county_fips)
        dept["census"] = census_cache[county_fips]

        # FEMA disasters
        if county_fips not in disaster_cache:
            time.sleep(0.1)
            disaster_cache[county_fips] = fetch_fema_disasters(state, county_fips, state_fips)
        dept["disasters"] = disaster_cache[county_fips]

        # Peer comparison
        dept["peers"] = build_peer_comparison(dept, all_depts)

        f.write_text(json.dumps(dept, indent=2))

    print(f"Done. Enriched {len(files)} departments.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="CA")
    args = parser.parse_args()
    enrich(args.state)
