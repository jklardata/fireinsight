"""
Fetch 2 departments from the NERIS test API and save as JSON.
Run: python3 fetch_departments.py

Set NERIS_CLIENT_ID and NERIS_CLIENT_SECRET in .env before running.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from neris_api_client import NerisApiClient
from neris_api_client.config import Config, GrantType

load_dotenv()

OUTPUT_DIR = Path("data/departments")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_client():
    return NerisApiClient(Config(
        base_url=os.getenv("NERIS_BASE_URL", "https://api-test.neris.fsri.org/v1"),
        grant_type=GrantType.CLIENT_CREDENTIALS,
        client_id=os.getenv("NERIS_CLIENT_ID"),
        client_secret=os.getenv("NERIS_CLIENT_SECRET"),
    ))


def fetch_two_departments():
    client = get_client()

    print("Fetching department list...")
    result = client.list_entities(page_number=1, page_size=2)
    print("Raw response:", json.dumps(result, indent=2, default=str))

    departments = result.get("data", [])
    if not departments:
        print("No departments returned. Check credentials and API access.")
        return

    for dept in departments:
        neris_id = dept.get("neris_id") or dept.get("id")
        name = dept.get("name", "unknown")
        print(f"\nFetching incidents for: {name} ({neris_id})")

        try:
            incidents_result = client.list_incidents(
                neris_id_entity=neris_id,
                page_number=1,
                page_size=50,
            )
            incidents = incidents_result.get("data", [])
        except Exception as e:
            print(f"  Could not fetch incidents: {e}")
            incidents = []

        payload = {
            "entity": dept,
            "incidents_sample": incidents,
            "incident_count_sample": len(incidents),
        }

        slug = neris_id.lower().replace(" ", "-")
        out_path = OUTPUT_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(payload, indent=2, default=str))
        print(f"  Saved to {out_path}")

    print("\nDone.")


if __name__ == "__main__":
    fetch_two_departments()
