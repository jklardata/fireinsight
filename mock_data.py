"""
Mock NERIS incident data for local development without API credentials.
Simulates a mid-size volunteer department (~400 calls/year).
"""

from datetime import datetime, timedelta
import random

random.seed(42)

DEPT = {
    "neris_id": "MOCK-001",
    "name": "Riverside Volunteer Fire Department",
    "state": "VA",
}

INCIDENT_TYPES = [
    ("EMS - Medical Emergency", 38),
    ("EMS - Motor Vehicle Accident", 12),
    ("Fire - Structure Fire", 8),
    ("Fire - Vehicle Fire", 5),
    ("Fire - EV Battery Fire", 4),
    ("Hazmat - Lithium Battery", 2),
    ("Fire - Brush/Grass Fire", 6),
    ("Hazmat - Carbon Monoxide", 7),
    ("Service Call - Public Assist", 10),
    ("False Alarm - System Malfunction", 9),
    ("Rescue - Water", 3),
    ("Other", 2),
]

_pool = []
for label, weight in INCIDENT_TYPES:
    _pool.extend([label] * weight)

HOUR_WEIGHTS = [1,1,1,1,1,2,3,4,5,6,6,6,6,6,6,6,6,7,7,6,5,4,3,2]


def _random_timestamp(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def _weighted_hour() -> int:
    return random.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]


def generate_incidents(
    n: int = 380,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    start = start or datetime(2024, 2, 1, 0, 0, 0)
    end = end or datetime(2025, 1, 31, 23, 59, 59)
    incidents = []

    for i in range(n):
        call_dt = _random_timestamp(start, end)
        call_dt = call_dt.replace(hour=_weighted_hour())

        response_secs = max(60, int(random.gauss(420, 120)))
        arrival_dt = call_dt + timedelta(seconds=response_secs)

        incidents.append({
            "neris_id_incident": f"MOCK-INC-{i+1:04d}",
            "neris_id_entity": DEPT["neris_id"],
            "incident_type": random.choice(_pool),
            "call_create": call_dt.isoformat(),
            "arrival_time": arrival_dt.isoformat(),
            "status": "APPROVED",
            "latitude": round(37.5 + random.uniform(-0.1, 0.1), 6),
            "longitude": round(-77.4 + random.uniform(-0.1, 0.1), 6),
        })

    # Filter to date range (handles cases where random dates fall outside when range is narrow)
    return [
        inc for inc in incidents
        if start <= datetime.fromisoformat(inc["call_create"]) <= end
    ]
