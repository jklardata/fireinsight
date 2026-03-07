"""
Generate a sample NFIRS Basic Module CSV for testing the FireInsight converter.
Produces sample_nfirs.csv in the current directory.

Usage: python3 generate_sample_nfirs.py
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(99)

FDID  = "VA12345"
STATE = "VA"

# (NFIRS code, weight)
INCIDENT_TYPES = [
    ("311", 35),  # EMS Medical Emergency
    ("321", 10),  # MVA with injuries
    ("111", 8),   # Structure fire - single family
    ("113", 4),   # Structure fire - multi-family
    ("131", 5),   # Vehicle fire
    ("142", 5),   # Brush/grass fire
    ("424", 6),   # Carbon monoxide incident
    ("611", 8),   # Alarm system malfunction
    ("621", 3),   # Malicious false alarm
    ("500", 6),   # Service call / public assist
    ("522", 4),   # Water problem
    ("341", 2),   # Water rescue
    ("351", 2),   # Extrication
    ("412", 2),   # Gas leak
]

pool = []
for code, weight in INCIDENT_TYPES:
    pool.extend([code] * weight)

# Weighted hour distribution (busier during day)
HOUR_WEIGHTS = [1,1,1,1,1,2,3,5,6,6,6,7,7,7,7,7,7,8,8,6,5,4,3,2]
hours = []
for h, w in enumerate(HOUR_WEIGHTS):
    hours.extend([h] * w)

START = datetime(2024, 1, 1)
END   = datetime(2024, 12, 31)

ACTIONS_TAKEN = ["11", "32", "51", "86", "13", "22"]

rows = []
for i in range(1, 101):
    # Random date
    days_offset = random.randint(0, (END - START).days)
    date = START + timedelta(days=days_offset)
    date_str = date.strftime("%m%d%Y")

    # Alarm time
    alarm_hour   = random.choice(hours)
    alarm_minute = random.randint(0, 59)
    alarm_str    = f"{alarm_hour:02d}{alarm_minute:02d}"

    # Arrival ~4-12 min later
    arrival_delta = random.randint(240, 720)
    arrival_dt    = date.replace(hour=alarm_hour, minute=alarm_minute) + timedelta(seconds=arrival_delta)
    arrival_str   = f"{arrival_dt.hour:02d}{arrival_dt.minute:02d}"

    # Controlled ~10-40 min after arrival
    controlled_dt  = arrival_dt + timedelta(minutes=random.randint(10, 40))
    controlled_str = f"{controlled_dt.hour:02d}{controlled_dt.minute:02d}"

    # Cleared ~5-15 min after controlled
    cleared_dt  = controlled_dt + timedelta(minutes=random.randint(5, 15))
    cleared_str = f"{cleared_dt.hour:02d}{cleared_dt.minute:02d}"

    inc_type = random.choice(pool)

    # Casualties — rare
    ff_death  = 1 if random.random() < 0.005 else 0
    oth_death = 1 if random.random() < 0.008 else 0
    ff_inj    = 1 if random.random() < 0.03  else 0
    oth_inj   = random.randint(0, 2) if inc_type in ("311", "321") and random.random() < 0.15 else 0

    # Property loss — only for fires
    prop_loss = ""
    cont_loss = ""
    if inc_type.startswith("1"):
        prop_loss = str(random.randint(1000, 250000))
        cont_loss = str(random.randint(500, 50000))

    # Aid: 1=none, 3=given, 4=received
    aid = random.choices(["1", "3", "4"], weights=[85, 8, 7])[0]

    rows.append({
        "STATE":    STATE,
        "FDID":     FDID,
        "INC_DATE": date_str,
        "INC_NO":   f"{i:04d}",
        "EXP_NO":   "0",
        "INC_TYPE": inc_type,
        "AID":      aid,
        "ALARM":    alarm_str,
        "ARRIVAL":  arrival_str,
        "INC_CONT": controlled_str,
        "LU_CLEAR": cleared_str,
        "SHIFT":    random.choice(["A", "B", "C"]),
        "ALARMS":   "1",
        "FF_DEATH": str(ff_death),
        "OTH_DEATH":str(oth_death),
        "FF_INJ":   str(ff_inj),
        "OTH_INJ":  str(oth_inj),
        "PROP_LOSS":prop_loss,
        "CONT_LOSS":cont_loss,
        "ACT_TAKE1":random.choice(ACTIONS_TAKEN),
        "ACT_TAKE2":random.choice(ACTIONS_TAKEN),
    })

out = "sample_nfirs.csv"
fieldnames = list(rows[0].keys())

with open(out, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} incidents → {out}")
