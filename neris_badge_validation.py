"""
NERIS Data Exchange Compatibility Badge — Validation Script
5AlarmData / KlarData

Walks through all 5 steps required for Version 1 Data Exchange Compatibility:
  1. Health check + auth verification
  2. Enroll integration with FSRI test department
  3a. Create a valid incident
  3b. Update (patch) that incident by UID
  4a. Create a new station in FSRI department
  4b. Add a unit to that station
  5. (Manual) Submit compatibility check request via helpdesk

Usage:
  pip install neris-api-client
  export NERIS_CLIENT_ID="your-client-id"
  export NERIS_CLIENT_SECRET="your-client-secret"
  python neris_badge_validation.py

  Optional dry-run (validates payloads only, no API calls):
  python neris_badge_validation.py --dry-run
"""

import os
import sys
import uuid
import json
import argparse
from datetime import datetime, timezone, timedelta

from neris_api_client import NerisApiClient
from neris_api_client.config import Config, GrantType
from neris_api_client import models


# ─────────────────────────────────────────────
# CONFIG — load from env or override here
# ─────────────────────────────────────────────

CLIENT_ID     = os.getenv("NERIS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("NERIS_CLIENT_SECRET", "")
FSRI_DEPT_ID  = os.getenv("NERIS_FSRI_DEPT_ID", "FD39023033")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def step(n, title):
    print(f"\n{'='*60}")
    print(f"  STEP {n}: {title}")
    print(f"{'='*60}")

def ok(msg):
    print(f"  ✅  {msg}")

def info(msg):
    print(f"  ℹ️   {msg}")

def fail(msg):
    print(f"  ❌  {msg}")
    sys.exit(1)

def pretty(obj):
    return json.dumps(obj, indent=2, default=str)


def build_incident_payload(dept_id: str) -> dict:
    now = datetime.now(timezone.utc)
    call_arrival  = now - timedelta(hours=2)           # 911 call hits PSAP
    call_answered = call_arrival  + timedelta(seconds=12)  # dispatcher picks up
    call_create   = call_answered + timedelta(seconds=30)  # CAD incident opened in RMS

    location = models.LocationPayload(
        number=123,
        street="Main St",
        incorporated_municipality="Springfield",
        state=models.StatesTerrs.VA,
        postal_code="22150",
    )

    unit_dispatch   = call_create   + timedelta(seconds=45)   # unit dispatched after CAD create
    unit_enroute    = unit_dispatch  + timedelta(seconds=60)   # turnout time
    unit_on_scene   = unit_enroute   + timedelta(minutes=5)    # travel time

    dispatch = models.DispatchPayload(
        incident_number="5ALARM-TEST-001",
        call_create=call_create,
        call_answered=call_answered,
        call_arrival=call_arrival,
        location=location,
        unit_responses=[
            models.DispatchUnitResponsePayload(
                reported_unit_id="ENGINE-1",
                staffing=4,
                dispatch=unit_dispatch,
                enroute_to_scene=unit_enroute,
                on_scene=unit_on_scene,
            )
        ],
    )

    base = models.IncidentBasePayload(
        department_neris_id=dept_id,
        incident_number="5ALARM-TEST-001",
        location=location,
    )

    incident_type = models.IncidentTypePayload(
        type=models.TypeIncidentValue("FIRE||OUTSIDE_FIRE||TRASH_RUBBISH_FIRE"),
        primary=True,
    )

    payload = models.IncidentPayload(
        base=base,
        incident_types=[incident_type],
        dispatch=dispatch,
    )

    return payload.model_dump(mode="json", exclude_none=True)


def build_patch_payload(incident_uid: str, base_neris_uid: int | None = None) -> dict:
    """
    patch_incident expects a single PatchIncidentAction dict (not a list).
    Structure: { neris_id, action: "patch", properties: { base: { neris_uid, ... } } }
    base_neris_uid is the integer neris_uid from incident.base.neris_uid (required by API).
    """
    patch = models.PatchIncidentAction(
        neris_id=incident_uid,
        action="patch",
        properties=models.FieldPatchIncidentActionProperties(
            base=models.PatchIncidentBaseAction(
                neris_uid=base_neris_uid,
                action="patch",
                properties=models.FieldPatchIncidentBaseActionProperties(
                    outcome_narrative=models.SetNarrativeStrAction(
                        action="set",
                        value="Test update from 5AlarmData compatibility validation script.",
                    )
                ),
            )
        ),
    )
    return patch.model_dump(mode="json", exclude_none=True)


def build_station_payload() -> dict:
    payload = models.CreateStationPayload(
        address_line_1="456 Fire Station Rd",
        city="Springfield",
        state=models.StatesTerrs.VA,
        zip_code="22150",
        station_id="STA-5ALARM-01",
        staffing=12,
    )
    return payload.model_dump(mode="json", exclude_none=True)


def build_unit_payload() -> dict:
    payload = models.CreateUnitPayload(
        staffing=4,
        type=models.TypeUnitValue("ENGINE_STRUCT"),
        cad_designation_1="E-1",
    )
    return payload.model_dump(mode="json", exclude_none=True)


# ─────────────────────────────────────────────
# DRY RUN
# ─────────────────────────────────────────────

def dry_run():
    print("\n🔍  DRY RUN — validating payload construction only (no API calls)\n")

    incident_payload = build_incident_payload("FD00000000")
    print("Incident payload:")
    print(pretty(incident_payload))

    patch_payload = build_patch_payload("FD00000000|TEST-001|0000000000")
    print("\nPatch payload:")
    print(pretty(patch_payload))

    station_payload = build_station_payload()
    print("\nStation payload:")
    print(pretty(station_payload))

    unit_payload = build_unit_payload()
    print("\nUnit payload:")
    print(pretty(unit_payload))

    print("\n✅  All payloads constructed successfully.")


# ─────────────────────────────────────────────
# MAIN BADGE VALIDATION FLOW
# ─────────────────────────────────────────────

def run_badge_validation(incident_uid_override: str | None = None):
    if not CLIENT_ID or not CLIENT_SECRET:
        fail("NERIS_CLIENT_ID and NERIS_CLIENT_SECRET must be set as environment variables.")
    if not FSRI_DEPT_ID:
        fail("NERIS_FSRI_DEPT_ID must be set (default: FD39023033).")

    BASE_URL = os.getenv("NERIS_BASE_URL", "https://api-test.neris.fsri.org/v1")

    client = NerisApiClient(Config(
        base_url=BASE_URL,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        grant_type=GrantType.CLIENT_CREDENTIALS,
    ))

    def extract(response):
        """Safely coerce NERIS response to dict regardless of return type."""
        if isinstance(response, dict):
            return response
        if hasattr(response, 'json'):
            try:
                return response.json()
            except Exception:
                pass
        if hasattr(response, '__dict__'):
            return {k: v for k, v in response.__dict__.items() if not k.startswith('_')}
        return {}

    def get_uid(response):
        """Extract UID from response — checks all known NERIS UID field names."""
        d = extract(response)
        return (d.get("neris_id") or d.get("neris_id_incident") or
                d.get("neris_id_station") or d.get("neris_id_unit") or
                d.get("uid") or d.get("id"))

    info(f"Base URL: {BASE_URL}")
    info(f"Dept ID:  {FSRI_DEPT_ID}")

    # ── STEP 1: Health check ──────────────────
    step(1, "Health Check + Auth Verification")
    try:
        health = client.health()
        ok(f"API reachable: {health}")
    except Exception as e:
        fail(f"Health check failed: {e}")

    # Non-fatal — 403 expected before enrollment
    try:
        dept = extract(client.get_entity(FSRI_DEPT_ID))
        ok(f"FSRI test department found: {dept.get('name', FSRI_DEPT_ID)}")
    except Exception as e:
        info(f"Dept fetch skipped (403 expected before enrollment): {e}")

    # ── STEP 2: Enroll integration ────────────
    step(2, "Enroll Integration with FSRI Department")
    try:
        integrations = extract(client.list_integrations(FSRI_DEPT_ID))
        info(f"Existing integrations: {pretty(integrations)}")
    except Exception as e:
        info(f"Could not list integrations: {e}")

    try:
        enroll_result = extract(client.enroll_integration(
            neris_id=FSRI_DEPT_ID,
            client_id=CLIENT_ID,
        ))
        ok(f"Enrollment result: {pretty(enroll_result)}")
    except Exception as e:
        info(f"Enrollment note (may already be enrolled): {e}")

    # ── STEP 3a: Create incident ──────────────
    step("3a", "Create a Valid Incident")

    incident_uid = None
    if incident_uid_override:
        incident_uid = incident_uid_override
        ok(f"Skipping create — using provided UID: {incident_uid}")
    else:
        incident_payload = build_incident_payload(FSRI_DEPT_ID)
        info(f"Payload preview:\n{pretty(incident_payload)}")

        try:
            validation = extract(client.validate_incident(FSRI_DEPT_ID, incident_payload))
            ok(f"Validation passed: {pretty(validation)}")
        except Exception as e:
            info(f"Validation warning (proceeding anyway): {e}")

        try:
            created = extract(client.create_incident(FSRI_DEPT_ID, incident_payload))
            incident_uid = get_uid(created)
            ok(f"Incident created. UID: {incident_uid}")
            info(f"Full response:\n{pretty(created)}")
        except Exception as e:
            fail(f"create_incident failed: {e}")

        if not incident_uid:
            fail("Could not extract incident UID. Check full response above.")

    # ── STEP 3b: Patch incident (update a field) ──────
    step("3b", f"Patch Incident — Update Narrative (UID: {incident_uid})")
    info("Patching outcome_narrative field via patch_incident()")

    # Fetch base.neris_uid — required by PatchIncidentBaseAction
    base_neris_uid = None
    try:
        incidents_list = extract(client.list_incidents(neris_id_entity=FSRI_DEPT_ID))
        all_incidents = incidents_list.get("incidents", [])
        match = next((i for i in all_incidents if i.get("neris_id") == incident_uid), None)
        if match:
            base_neris_uid = (match.get("base") or {}).get("neris_uid")
            info(f"Fetched base.neris_uid: {base_neris_uid}")
        else:
            info(f"Incident {incident_uid} not found in list — will try patch without neris_uid")
    except Exception as e:
        info(f"Could not fetch incident list (will try patch without neris_uid): {e}")

    patch_payload = build_patch_payload(incident_uid, base_neris_uid=base_neris_uid)
    info(f"Patch payload:\n{pretty(patch_payload)}")

    try:
        updated = extract(client.patch_incident(
            neris_id_entity=FSRI_DEPT_ID,
            neris_id_incident=incident_uid,
            body=patch_payload,
        ))
        if isinstance(updated, dict) and "detail" in updated and "error" in str(updated.get("detail", "")).lower() or \
                isinstance(updated.get("detail"), list):
            fail(f"patch_incident returned error: {pretty(updated)}")
        ok(f"Incident patched: {pretty(updated)}")
    except Exception as e:
        fail(f"patch_incident failed: {e}")

    # ── STEP 4a: Create station ───────────────
    step("4a", "Create New Station in FSRI Department")
    station_payload = build_station_payload()
    info(f"Station payload: {pretty(station_payload)}")

    station_uid = None
    try:
        station = extract(client.create_station(FSRI_DEPT_ID, station_payload))
        station_uid = get_uid(station)
        if station_uid:
            ok(f"Station created. UID: {station_uid}")
        else:
            # 409 conflict — station already exists from prior run, reuse it
            detail = station.get("detail", "")
            if "FD39023033S" in str(detail):
                import re
                match = re.search(r"FD39023033S\d+", str(detail))
                station_uid = match.group(0) if match else None
            if station_uid:
                ok(f"Station already exists, reusing: {station_uid}")
            else:
                fail("Could not create or find existing station.")
        info(f"Full response:\n{pretty(station)}")
    except Exception as e:
        fail(f"create_station failed: {e}")

    if not station_uid:
        fail("Could not extract station UID. Check full response above.")

    # ── STEP 4b: Add unit to station ─────────
    step("4b", f"Add Unit to Station (UID: {station_uid})")
    unit_payload = build_unit_payload()
    info(f"Unit payload: {pretty(unit_payload)}")

    unit_uid = None
    try:
        # Direct POST to /entity/{entity}/station/{station}/unit
        # (client.create_unit hits the wrong URL — missing /unit suffix)
        client._update_auth()
        import requests as req_lib
        unit_url = f"{BASE_URL}/entity/{FSRI_DEPT_ID}/station/{station_uid}/unit"
        headers = {"Authorization": f"Bearer {client.tokens.access_token}"}
        unit_resp = req_lib.post(unit_url, json=unit_payload, headers=headers)
        info(f"Unit POST URL: {unit_url}")
        info(f"Unit POST status: {unit_resp.status_code}")
        try:
            unit_result = unit_resp.json()
        except Exception:
            unit_result = {"raw": unit_resp.text}
        unit_uid = (unit_result.get("neris_id") or unit_result.get("neris_id_unit")
                    if isinstance(unit_result, dict) else None)
        if not unit_uid and isinstance(unit_result, dict):
            # Check nested units list
            units = unit_result.get("units", [])
            if units:
                unit_uid = units[0].get("neris_id") or units[0].get("neris_id_unit")
        ok(f"Unit created. UID: {unit_uid}")
        info(f"Full response:\n{pretty(unit_result)}")
    except Exception as e:
        fail(f"create_unit failed: {e}")

    # ── SUMMARY ───────────────────────────────
    print(f"\n{'='*60}")
    print("  🎉  ALL STEPS COMPLETE")
    print(f"{'='*60}")
    print(f"""
  Incident UID : {incident_uid}
  Station UID  : {station_uid}
  Unit UID     : {unit_uid}

  Next step (manual):
  → Go to https://neris.atlassian.net/servicedesk/customer/portals
  → Select "Request Compatibility Check"
  → Reference the incident / station / unit UIDs above
""")


# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NERIS Data Exchange Compatibility Badge Validator")
    parser.add_argument("--dry-run", action="store_true", help="Validate payload construction only, no API calls")
    parser.add_argument("--incident-uid", metavar="UID", help="Skip step 3a and patch this existing incident UID")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    else:
        run_badge_validation(incident_uid_override=args.incident_uid)