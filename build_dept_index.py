"""
Build a lightweight search/listing index from all department JSON files.

Output: data/departments_index.json

Run this whenever department files are added or updated:
  python3 build_dept_index.py
"""

import json
from pathlib import Path
from collections import defaultdict

DEPT_DIR = Path("data/departments")
OUTPUT = Path("data/departments_index.json")


def main():
    entries = []
    files = list(DEPT_DIR.glob("*.json"))
    print(f"Reading {len(files)} department files...")

    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        entries.append({
            "stem":            f.stem,
            "name":            d.get("name", ""),
            "city":            d.get("city", ""),
            "state":           d.get("state", ""),
            "fdid":            d.get("fdid", ""),
            "total_incidents": d.get("total_incidents", 0),
            "incident_types":  d.get("incident_types", {}),
        })

    OUTPUT.write_text(json.dumps(entries))
    print(f"Wrote {len(entries)} entries to {OUTPUT}  ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
