#!/usr/bin/env python3
"""Find gap_google_only stations that aren't yet in manual_gap_fuel_info.json.

Emits JSON to stdout and writes data/pending_gaps.json.
Exit code 0 on success (regardless of whether gaps were found).
"""

from __future__ import annotations

import csv
import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCHED_CSV = os.path.join(PROJECT_DIR, "data", "clean", "matched_stations.csv")
MANUAL_JSON = os.path.join(PROJECT_DIR, "data", "manual_gap_fuel_info.json")
OUTPUT_JSON = os.path.join(PROJECT_DIR, "data", "pending_gaps.json")


def station_key(lat: str, lng: str) -> str:
    return f"{lat}|{lng}"


def main() -> None:
    with open(MATCHED_CSV, encoding="utf-8") as handle:
        gap_rows = [
            r for r in csv.DictReader(handle)
            if r.get("match_status") == "gap_google_only"
        ]

    enriched_keys: set[str] = set()
    if os.path.exists(MANUAL_JSON):
        with open(MANUAL_JSON, encoding="utf-8") as handle:
            manual = json.load(handle)
        for entry in manual.get("stations", []):
            enriched_keys.add(station_key(entry["google_lat"], entry["google_lng"]))

    pending = [
        {
            "google_name": r["google_name"],
            "google_address_full": r["google_address_full"],
            "google_lat": r["google_lat"],
            "google_lng": r["google_lng"],
        }
        for r in gap_rows
        if station_key(r["google_lat"], r["google_lng"]) not in enriched_keys
    ]

    payload = {
        "total_gap_stations": len(gap_rows),
        "enriched_count": len(enriched_keys),
        "pending_count": len(pending),
        "pending": pending,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    json.dump(payload, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
