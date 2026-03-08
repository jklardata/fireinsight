"""
State NERIS Coordinator Export
Generates state-specific CSV exports for VA, TX, FL, CA, OH, PA.
Each state coordinator has slightly different required fields/ordering.
"""
import csv
import io
from datetime import datetime

# ── State format definitions ──────────────────────────────────────────────────
# Each entry defines: required fields, field renames, and any computed fields.

STATE_CONFIGS = {
    "VA": {
        "name": "Virginia",
        "coordinator": "VA NERIS Coordinator",
        "filename": "va-neris-export.csv",
        "fields": [
            "neris_id_incident", "call_create", "arrival_time", "clear_time",
            "incident_type", "property_use", "latitude", "longitude",
            "injuries_firefighter", "injuries_civilian", "fatalities_firefighter", "fatalities_civilian",
            "apparatus_count", "personnel_count", "aid_given_received",
        ],
        "renames": {
            "neris_id_incident": "incident_id",
            "call_create": "dispatch_datetime",
            "clear_time": "clear_datetime",
            "incident_type": "incident_type_desc",
        },
    },
    "TX": {
        "name": "Texas",
        "coordinator": "TX State Fire Marshal NERIS",
        "filename": "tx-neris-export.csv",
        "fields": [
            "neris_id_incident", "call_create", "arrival_time", "clear_time",
            "incident_type", "property_use", "structure_type",
            "latitude", "longitude", "county",
            "injuries_firefighter", "injuries_civilian", "fatalities_firefighter", "fatalities_civilian",
            "apparatus_count", "personnel_count",
            "suppression_type", "aid_given_received",
        ],
        "renames": {
            "neris_id_incident": "tx_incident_number",
            "call_create":       "alarm_time",
            "arrival_time":      "arrival_time",
            "clear_time":        "last_unit_clear",
        },
    },
    "FL": {
        "name": "Florida",
        "coordinator": "FL Division of State Fire Marshal",
        "filename": "fl-neris-export.csv",
        "fields": [
            "neris_id_incident", "call_create", "arrival_time", "clear_time",
            "incident_type", "property_use",
            "latitude", "longitude",
            "injuries_firefighter", "injuries_civilian",
            "fatalities_firefighter", "fatalities_civilian",
            "apparatus_count", "personnel_count",
            "dollar_loss_property", "dollar_loss_contents",
            "aid_given_received",
        ],
        "renames": {
            "neris_id_incident":     "fl_incident_id",
            "dollar_loss_property":  "prop_loss",
            "dollar_loss_contents":  "cont_loss",
        },
    },
    "CA": {
        "name": "California",
        "coordinator": "CA Office of the State Fire Marshal",
        "filename": "ca-neris-export.csv",
        "fields": [
            "neris_id_incident", "call_create", "arrival_time", "clear_time",
            "incident_type", "property_use", "structure_type",
            "latitude", "longitude",
            "injuries_firefighter", "injuries_civilian",
            "fatalities_firefighter", "fatalities_civilian",
            "apparatus_count", "personnel_count",
            "dollar_loss_property", "dollar_loss_contents",
            "suppression_type", "aid_given_received",
            "wildland_acres",
        ],
        "renames": {
            "neris_id_incident": "ca_incident_id",
            "wildland_acres":    "acres_burned",
        },
    },
    "OH": {
        "name": "Ohio",
        "coordinator": "OH State Fire Marshal",
        "filename": "oh-neris-export.csv",
        "fields": [
            "neris_id_incident", "call_create", "arrival_time", "clear_time",
            "incident_type", "property_use",
            "latitude", "longitude",
            "injuries_firefighter", "injuries_civilian",
            "fatalities_firefighter", "fatalities_civilian",
            "apparatus_count", "personnel_count",
            "aid_given_received",
        ],
        "renames": {
            "neris_id_incident": "oh_incident_number",
            "call_create":       "alarm_date_time",
        },
    },
    "PA": {
        "name": "Pennsylvania",
        "coordinator": "PA State Fire Commissioner",
        "filename": "pa-neris-export.csv",
        "fields": [
            "neris_id_incident", "call_create", "arrival_time", "clear_time",
            "incident_type", "property_use",
            "latitude", "longitude", "county",
            "injuries_firefighter", "injuries_civilian",
            "fatalities_firefighter", "fatalities_civilian",
            "apparatus_count", "personnel_count",
            "dollar_loss_property",
            "aid_given_received",
        ],
        "renames": {
            "neris_id_incident": "pa_incident_id",
            "dollar_loss_property": "fire_loss",
        },
    },
}

SUPPORTED_STATES = list(STATE_CONFIGS.keys())


def _safe(incident: dict, field: str) -> str:
    val = incident.get(field)
    if val is None:
        return ""
    return str(val)


def generate_state_export(incidents: list, state: str, dept_name: str) -> dict:
    state = state.upper()
    if state not in STATE_CONFIGS:
        raise ValueError(f"State '{state}' is not supported. Supported: {', '.join(SUPPORTED_STATES)}")

    cfg = STATE_CONFIGS[state]
    fields   = cfg["fields"]
    renames  = cfg["renames"]

    # Build CSV
    output = io.StringIO()
    headers = [renames.get(f, f) for f in fields]
    writer  = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    skipped = 0
    for inc in incidents:
        row = {}
        for field in fields:
            col = renames.get(field, field)
            row[col] = _safe(inc, field)
        writer.writerow(row)

    csv_content = output.getvalue()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Summary stats
    total = len(incidents)
    date_range = ""
    dates = [i.get("call_create") for i in incidents if i.get("call_create")]
    if dates:
        dates_sorted = sorted(dates)
        date_range = f"{dates_sorted[0][:10]} to {dates_sorted[-1][:10]}"

    inj_ff = sum(int(i.get("injuries_firefighter") or 0) for i in incidents)
    inj_ci = sum(int(i.get("injuries_civilian") or 0) for i in incidents)
    fat_ff = sum(int(i.get("fatalities_firefighter") or 0) for i in incidents)
    fat_ci = sum(int(i.get("fatalities_civilian") or 0) for i in incidents)

    return {
        "state":        state,
        "state_name":   cfg["name"],
        "coordinator":  cfg["coordinator"],
        "dept_name":    dept_name,
        "total":        total,
        "date_range":   date_range,
        "generated_at": generated_at,
        "csv_content":  csv_content,
        "filename":     cfg["filename"],
        "fields":       headers,
        "field_count":  len(headers),
        "summary": {
            "injuries_ff":    inj_ff,
            "injuries_civ":   inj_ci,
            "fatalities_ff":  fat_ff,
            "fatalities_civ": fat_ci,
        },
    }
