#!/usr/bin/env python3
"""Merge cleaned Google and FuelCheck station CSVs into a match analysis CSV."""

from __future__ import annotations

import csv
import math
import os
import sys
from typing import Iterable

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOOGLE_CSV = os.path.join(PROJECT_DIR, "data", "clean", "google_stations.csv")
FUELCHECK_CSV = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_stations.csv")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "data", "clean", "matched_stations.csv")
MATCH_THRESHOLD_METERS = 100.0

GOOGLE_COLS = [
    "google_name",
    "google_address_full",
    "google_street",
    "google_suburb",
    "google_state",
    "google_lat",
    "google_lng",
    "google_address_missing",
]

FUELCHECK_COLS = [
    "fc_id",
    "fc_name",
    "fc_brand",
    "fc_brand_group",
    "fc_address_full",
    "fc_street",
    "fc_suburb",
    "fc_state",
    "fc_postcode",
    "fc_lat",
    "fc_lng",
    "fc_fuel_types",
    "fc_num_fuel_types",
    "fc_price_DL_cents",
    "fc_price_E10_cents",
    "fc_price_E85_cents",
    "fc_price_LPG_cents",
    "fc_price_P95_cents",
    "fc_price_P98_cents",
    "fc_price_PDL_cents",
    "fc_price_U91_cents",
    "fc_has_price_outlier",
]

FIELDNAMES = ["match_status", "match_distance_m", "match_confidence"] + GOOGLE_COLS + FUELCHECK_COLS


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the haversine distance between two coordinates in meters."""
    radius = 6371000.0
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(delta_lng / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def confidence_label(distance_m: float) -> str:
    """Label a match by distance band."""
    if distance_m < 50:
        return "high"
    if distance_m < 80:
        return "medium"
    return "low"


def read_csv_rows(path: str) -> list[dict[str, str]]:
    """Read a CSV file into a list of rows."""
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def empty_row(columns: Iterable[str]) -> dict[str, str]:
    """Return an empty row for a set of columns."""
    return {column: "" for column in columns}


def to_float(value: str) -> float | None:
    """Convert a CSV scalar to float, returning None on invalid input."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def merge_stations(
    google_csv: str = GOOGLE_CSV,
    fuelcheck_csv: str = FUELCHECK_CSV,
    output_file: str = OUTPUT_FILE,
) -> list[dict[str, str]]:
    """Merge Google and FuelCheck stations into one output CSV."""
    google_rows = read_csv_rows(google_csv)
    fuelcheck_rows = read_csv_rows(fuelcheck_csv)

    used_fc_ids: set[str] = set()
    merged_rows: list[dict[str, str]] = []

    for google_row in google_rows:
        google_lat = to_float(google_row.get("google_lat", ""))
        google_lng = to_float(google_row.get("google_lng", ""))
        if google_lat is None or google_lng is None:
            row = {
                "match_status": "gap_google_only",
                "match_distance_m": "",
                "match_confidence": "",
            }
            row.update({column: google_row.get(column, "") for column in GOOGLE_COLS})
            row.update(empty_row(FUELCHECK_COLS))
            merged_rows.append(row)
            continue

        best_match = None
        best_distance = float("inf")

        for fuelcheck_row in fuelcheck_rows:
            fc_id = fuelcheck_row.get("fc_id", "")
            if fc_id and fc_id in used_fc_ids:
                continue

            fuelcheck_lat = to_float(fuelcheck_row.get("fc_lat", ""))
            fuelcheck_lng = to_float(fuelcheck_row.get("fc_lng", ""))
            if fuelcheck_lat is None or fuelcheck_lng is None:
                continue

            distance = haversine_meters(google_lat, google_lng, fuelcheck_lat, fuelcheck_lng)
            if distance < best_distance:
                best_distance = distance
                best_match = fuelcheck_row

        if best_match and best_distance <= MATCH_THRESHOLD_METERS:
            fc_id = best_match.get("fc_id", "")
            if fc_id:
                used_fc_ids.add(fc_id)
            row = {
                "match_status": "matched",
                "match_distance_m": f"{best_distance:.1f}",
                "match_confidence": confidence_label(best_distance),
            }
            row.update({column: google_row.get(column, "") for column in GOOGLE_COLS})
            row.update({column: best_match.get(column, "") for column in FUELCHECK_COLS})
            merged_rows.append(row)
        else:
            row = {
                "match_status": "gap_google_only",
                "match_distance_m": "",
                "match_confidence": "",
            }
            row.update({column: google_row.get(column, "") for column in GOOGLE_COLS})
            row.update(empty_row(FUELCHECK_COLS))
            merged_rows.append(row)

    for fuelcheck_row in fuelcheck_rows:
        fc_id = fuelcheck_row.get("fc_id", "")
        if fc_id and fc_id in used_fc_ids:
            continue
        row = {
            "match_status": "fuelcheck_only",
            "match_distance_m": "",
            "match_confidence": "",
        }
        row.update(empty_row(GOOGLE_COLS))
        row.update({column: fuelcheck_row.get(column, "") for column in FUELCHECK_COLS})
        merged_rows.append(row)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged_rows)

    matched = sum(row["match_status"] == "matched" for row in merged_rows)
    google_only = sum(row["match_status"] == "gap_google_only" for row in merged_rows)
    fuelcheck_only = sum(row["match_status"] == "fuelcheck_only" for row in merged_rows)
    low_confidence = sum(row["match_confidence"] == "low" for row in merged_rows)

    print(f"Wrote {len(merged_rows)} rows to {output_file}")
    print(f"Matched: {matched}")
    print(f"Gaps (Google only): {google_only}")
    print(f"FuelCheck only: {fuelcheck_only}")
    print(f"Low confidence matches: {low_confidence}")
    return merged_rows


if __name__ == "__main__":
    merge_stations()
