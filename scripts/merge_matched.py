#!/usr/bin/env python3
"""Merge cleaned Google and FuelCheck station CSVs into a match analysis CSV."""

from __future__ import annotations

import csv
import math
import os
import re
import sys
from difflib import SequenceMatcher
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


def normalise_address(addr: str) -> str:
    """Normalise an address for comparison: lowercase, strip NSW/postcode/unit, collapse whitespace."""
    s = (addr or "").lower()
    s = re.sub(r"\bnsw\b", "", s)
    s = re.sub(r"\b\d{4}\b", "", s)
    s = re.sub(r"\bunit\s*\d*\b", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def address_similarity(addr1: str, addr2: str) -> float:
    """Return 0-1 similarity score between two normalised addresses."""
    a = normalise_address(addr1)
    b = normalise_address(addr2)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


ADDR_EXACT_THRESHOLD = 0.95  # normalised addresses nearly identical
ADDR_FUZZY_THRESHOLD = 0.70  # fuzzy fallback — same street, minor differences
ADDR_EXACT_MAX_DISTANCE_M = 5000.0  # exact matches can be far (bad geocoding)
ADDR_FUZZY_MAX_DISTANCE_M = 300.0  # fuzzy matches must be close


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


def _make_matched_row(
    google_row: dict, fc_row: dict, distance: float, confidence: str
) -> dict[str, str]:
    row = {
        "match_status": "matched",
        "match_distance_m": f"{distance:.1f}",
        "match_confidence": confidence,
    }
    row.update({c: google_row.get(c, "") for c in GOOGLE_COLS})
    row.update({c: fc_row.get(c, "") for c in FUELCHECK_COLS})
    return row


def _make_gap_row(google_row: dict) -> dict[str, str]:
    row = {
        "match_status": "gap_google_only",
        "match_distance_m": "",
        "match_confidence": "",
    }
    row.update({c: google_row.get(c, "") for c in GOOGLE_COLS})
    row.update(empty_row(FUELCHECK_COLS))
    return row


def merge_stations(
    google_csv: str = GOOGLE_CSV,
    fuelcheck_csv: str = FUELCHECK_CSV,
    output_file: str = OUTPUT_FILE,
) -> list[dict[str, str]]:
    """Merge Google and FuelCheck stations into one output CSV.

    Matching strategy (in priority order):
      1. Exact address match (similarity >= 0.95, within 5 km)
      2. Fuzzy address match (similarity >= 0.70, within 500 m)
      3. Coordinate distance match (<= 100 m)
    Earlier passes claim FC IDs so later passes don't double-match.
    """
    google_rows = read_csv_rows(google_csv)
    fuelcheck_rows = read_csv_rows(fuelcheck_csv)

    used_fc_ids: set[str] = set()
    used_google_idxs: set[int] = set()
    merged_rows: list[dict[str, str]] = []

    # Pre-compute normalised addresses for FuelCheck rows
    fc_norm_addrs = [normalise_address(r.get("fc_address_full", "")) for r in fuelcheck_rows]

    # --- Pass 1: Exact address match (score >= ADDR_EXACT_THRESHOLD) ---
    for g_idx, google_row in enumerate(google_rows):
        google_addr = normalise_address(google_row.get("google_address_full", ""))
        if not google_addr:
            continue
        google_lat = to_float(google_row.get("google_lat", ""))
        google_lng = to_float(google_row.get("google_lng", ""))

        best_fc = None
        best_score = 0.0
        best_dist = float("inf")

        for f_idx, fc_row in enumerate(fuelcheck_rows):
            fc_id = fc_row.get("fc_id", "")
            if fc_id and fc_id in used_fc_ids:
                continue
            score = SequenceMatcher(None, google_addr, fc_norm_addrs[f_idx]).ratio()
            if score >= ADDR_EXACT_THRESHOLD and score > best_score:
                fc_lat = to_float(fc_row.get("fc_lat", ""))
                fc_lng = to_float(fc_row.get("fc_lng", ""))
                dist = (
                    haversine_meters(google_lat, google_lng, fc_lat, fc_lng)
                    if google_lat and google_lng and fc_lat and fc_lng
                    else 0.0
                )
                if dist > ADDR_EXACT_MAX_DISTANCE_M:
                    continue
                best_fc = fc_row
                best_score = score
                best_dist = dist

        if best_fc:
            fc_id = best_fc.get("fc_id", "")
            if fc_id:
                used_fc_ids.add(fc_id)
            used_google_idxs.add(g_idx)
            merged_rows.append(_make_matched_row(google_row, best_fc, best_dist, "high"))

    # --- Pass 2: Fuzzy address match (score >= ADDR_FUZZY_THRESHOLD, within 2 km) ---
    for g_idx, google_row in enumerate(google_rows):
        if g_idx in used_google_idxs:
            continue
        google_addr = normalise_address(google_row.get("google_address_full", ""))
        if not google_addr:
            continue
        google_lat = to_float(google_row.get("google_lat", ""))
        google_lng = to_float(google_row.get("google_lng", ""))
        if google_lat is None or google_lng is None:
            continue

        best_fc = None
        best_score = 0.0
        best_dist = float("inf")

        for f_idx, fc_row in enumerate(fuelcheck_rows):
            fc_id = fc_row.get("fc_id", "")
            if fc_id and fc_id in used_fc_ids:
                continue
            fc_lat = to_float(fc_row.get("fc_lat", ""))
            fc_lng = to_float(fc_row.get("fc_lng", ""))
            if fc_lat is None or fc_lng is None:
                continue
            dist = haversine_meters(google_lat, google_lng, fc_lat, fc_lng)
            if dist > ADDR_FUZZY_MAX_DISTANCE_M:
                continue
            score = SequenceMatcher(None, google_addr, fc_norm_addrs[f_idx]).ratio()
            if score >= ADDR_FUZZY_THRESHOLD and score > best_score:
                best_fc = fc_row
                best_score = score
                best_dist = dist

        if best_fc:
            fc_id = best_fc.get("fc_id", "")
            if fc_id:
                used_fc_ids.add(fc_id)
            used_google_idxs.add(g_idx)
            merged_rows.append(_make_matched_row(google_row, best_fc, best_dist, "medium"))

    # --- Pass 3: Coordinate distance match (<= 100 m) ---
    for g_idx, google_row in enumerate(google_rows):
        if g_idx in used_google_idxs:
            continue
        google_lat = to_float(google_row.get("google_lat", ""))
        google_lng = to_float(google_row.get("google_lng", ""))
        if google_lat is None or google_lng is None:
            used_google_idxs.add(g_idx)
            merged_rows.append(_make_gap_row(google_row))
            continue

        best_match = None
        best_distance = float("inf")

        for fc_row in fuelcheck_rows:
            fc_id = fc_row.get("fc_id", "")
            if fc_id and fc_id in used_fc_ids:
                continue
            fc_lat = to_float(fc_row.get("fc_lat", ""))
            fc_lng = to_float(fc_row.get("fc_lng", ""))
            if fc_lat is None or fc_lng is None:
                continue
            distance = haversine_meters(google_lat, google_lng, fc_lat, fc_lng)
            if distance < best_distance:
                best_distance = distance
                best_match = fc_row

        if best_match and best_distance <= MATCH_THRESHOLD_METERS:
            fc_id = best_match.get("fc_id", "")
            if fc_id:
                used_fc_ids.add(fc_id)
            used_google_idxs.add(g_idx)
            merged_rows.append(
                _make_matched_row(google_row, best_match, best_distance, confidence_label(best_distance))
            )
        else:
            used_google_idxs.add(g_idx)
            merged_rows.append(_make_gap_row(google_row))

    # --- Remaining FuelCheck stations (not matched) ---
    for fc_row in fuelcheck_rows:
        fc_id = fc_row.get("fc_id", "")
        if fc_id and fc_id in used_fc_ids:
            continue
        row = {
            "match_status": "fuelcheck_only",
            "match_distance_m": "",
            "match_confidence": "",
        }
        row.update(empty_row(GOOGLE_COLS))
        row.update({c: fc_row.get(c, "") for c in FUELCHECK_COLS})
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
