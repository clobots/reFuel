#!/usr/bin/env python3
"""Clean Google station data into a flat CSV."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
from typing import Iterable

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_DIR, "data", "google_stations.json")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "data", "clean", "google_stations.csv")

STATE_CODES = {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}
UPPER_TOKENS = {"BP", "EG", "LPG", "EV", *STATE_CODES}

FIELDNAMES = [
    "google_name",
    "google_address_full",
    "google_street",
    "google_suburb",
    "google_state",
    "google_lat",
    "google_lng",
    "google_address_missing",
]


def smart_title(text: str) -> str:
    """Title-case text while restoring known uppercase tokens."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""

    titled = text.title()
    for token in sorted(UPPER_TOKENS, key=len, reverse=True):
        titled = re.sub(rf"\b{re.escape(token.title())}\b", token, titled)
    return titled


def title_case_name(name: str) -> str:
    """Normalize station names without destroying brand acronyms."""
    return smart_title(name)


def normalize_address_full(address: str) -> str:
    """Normalize an address string while preserving state abbreviations."""
    return smart_title(address)


def parse_address(address: str | None) -> tuple[str, str, str]:
    """Parse Google address strings into street/suburb/state components."""
    if not address or not address.strip():
        return ("", "", "")

    compact = re.sub(r"\s+", " ", address.strip())
    parts = [part.strip() for part in compact.rsplit(",", 1)]
    if len(parts) == 2:
        street, rest = parts
    else:
        street, rest = "", parts[0]

    match = re.match(r"^(?P<suburb>.*?)(?:\s+(?P<state>NSW|VIC|QLD|SA|WA|TAS|NT|ACT))?$", rest, re.IGNORECASE)
    if not match:
        return (smart_title(street), smart_title(rest), "")

    suburb = smart_title(match.group("suburb") or "")
    state = (match.group("state") or "").upper()
    return (smart_title(street), suburb, state)


def coerce_coord(value: object) -> str:
    """Round coordinates to 6dp and return a stable string for CSV output."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if math.isnan(numeric) or math.isinf(numeric):
        return ""
    return f"{numeric:.6f}"


def build_rows(stations: Iterable[dict]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for station in stations:
        address = str(station.get("address", "") or "")
        street, suburb, state = parse_address(address)
        rows.append(
            {
                "google_name": title_case_name(str(station.get("name", "") or "")),
                "google_address_full": normalize_address_full(address),
                "google_street": street,
                "google_suburb": suburb,
                "google_state": state,
                "google_lat": coerce_coord(station.get("lat")),
                "google_lng": coerce_coord(station.get("lng")),
                "google_address_missing": str(not bool(address.strip())).lower(),
            }
        )
    return rows


def clean_google_stations(input_file: str = INPUT_FILE, output_file: str = OUTPUT_FILE) -> list[dict[str, object]]:
    """Clean Google station data and write the output CSV."""
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    with open(input_file, encoding="utf-8") as handle:
        stations = json.load(handle)

    if not isinstance(stations, list):
        print(f"ERROR: Expected a JSON list in {input_file}", file=sys.stderr)
        sys.exit(1)

    rows = build_rows(stations)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    missing_count = sum(row["google_address_missing"] == "true" for row in rows)
    print(f"Wrote {len(rows)} rows to {output_file}")
    print(f"Address missing: {missing_count}")
    return rows


if __name__ == "__main__":
    clean_google_stations()
