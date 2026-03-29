#!/usr/bin/env python3
"""Clean FuelCheck station data into a flat CSV."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
from typing import Iterable

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_DIR, "data", "fuelcheck_stations.json")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_stations.csv")

STATE_CODES = {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}
UPPER_TOKENS = {"BP", "EG", "LPG", "EV", *STATE_CODES}
LIQUID_FUEL_TYPES = {"U91", "E10", "E85", "P95", "P98", "DL", "PDL", "LPG"}
PRICE_OUTLIER_THRESHOLD = 400

FIELDNAMES = [
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
] + [f"fc_price_{fuel_type}_cents" for fuel_type in sorted(LIQUID_FUEL_TYPES)] + [
    "fc_has_price_outlier",
]

BRAND_GROUP_RULES = (
    ("ampol foodary", "Ampol"),
    ("eg ampol", "Ampol"),
    ("ampol", "Ampol"),
    ("caltex", "Ampol"),
    ("coles express", "Ampol"),
    ("reddy express", "Shell"),
    ("shell", "Shell"),
    ("bp", "BP"),
    ("metro", "Metro"),
    ("mobil", "Mobil"),
    ("7-eleven", "7-Eleven"),
    ("budget", "Budget"),
    ("speedway", "Speedway"),
)


def smart_title(text: str) -> str:
    """Title-case text while restoring common uppercase abbreviations."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""

    titled = text.title()
    for token in sorted(UPPER_TOKENS, key=len, reverse=True):
        titled = re.sub(rf"\b{re.escape(token.title())}\b", token, titled)
    return titled


def normalize_brand_group(brand: str) -> str:
    """Map brand variants to a simpler parent brand."""
    cleaned = re.sub(r"\s+", " ", (brand or "").strip())
    if not cleaned:
        return ""

    lowered = cleaned.lower()
    for needle, group in BRAND_GROUP_RULES:
        if needle in lowered:
            return group
    return smart_title(cleaned)


def is_ev_only(station: dict) -> bool:
    """Return True when a station has no non-EV fuel types worth analysing."""
    prices = station.get("prices", [])
    if not prices:
        return True
    return not any(price.get("fuel_type") in LIQUID_FUEL_TYPES for price in prices)


def parse_fc_address(address: str | None) -> tuple[str, str, str, str]:
    """Parse FuelCheck addresses into street, suburb, state, and postcode."""
    if not address or not address.strip():
        return ("", "", "", "")

    compact = re.sub(r"\s+", " ", address.strip())
    parts = [part.strip() for part in compact.rsplit(",", 1)]
    if len(parts) == 2:
        street, rest = parts
    else:
        street, rest = "", parts[0]

    match = re.match(
        r"^(?P<suburb>.*?)\s+(?P<state>NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\s+(?P<postcode>\d{4})$",
        rest,
        re.IGNORECASE,
    )
    if not match:
        return (smart_title(street), smart_title(rest), "", "")

    suburb = smart_title(match.group("suburb") or "")
    state = (match.group("state") or "").upper()
    postcode = match.group("postcode") or ""
    return (smart_title(street), suburb, state, postcode)


def normalize_address_full(address: str) -> str:
    """Normalize the display address while preserving state abbreviations."""
    street, suburb, state, postcode = parse_fc_address(address)
    if street and suburb and state and postcode:
        return f"{street}, {suburb} {state} {postcode}"
    return smart_title(address)


def coerce_coord(value: object) -> str:
    """Round coordinates to 6dp and return a stable string for CSV output."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if math.isnan(numeric) or math.isinf(numeric):
        return ""
    return f"{numeric:.6f}"


def pivot_prices(prices: Iterable[dict]) -> tuple[dict[str, object], bool]:
    """Pivot nested prices into wide columns and flag large outliers."""
    result = {f"fc_price_{fuel_type}_cents": "" for fuel_type in sorted(LIQUID_FUEL_TYPES)}
    has_outlier = False

    for price in prices:
        fuel_type = price.get("fuel_type")
        raw_value = price.get("price")
        if fuel_type not in LIQUID_FUEL_TYPES or raw_value in (None, ""):
            continue
        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            continue
        result[f"fc_price_{fuel_type}_cents"] = numeric
        if numeric > PRICE_OUTLIER_THRESHOLD:
            has_outlier = True

    return result, has_outlier


def build_rows(stations: Iterable[dict]) -> tuple[list[dict[str, object]], int]:
    """Transform raw FuelCheck stations into CSV rows."""
    rows: list[dict[str, object]] = []
    excluded = 0

    for station in stations:
        if is_ev_only(station):
            excluded += 1
            continue

        prices = station.get("prices", [])
        fuel_types = sorted({price.get("fuel_type") for price in prices if price.get("fuel_type") in LIQUID_FUEL_TYPES})
        street, suburb, state, postcode = parse_fc_address(str(station.get("address", "") or ""))
        price_columns, has_outlier = pivot_prices(prices)

        row = {
            "fc_id": str(station.get("id", "") or ""),
            "fc_name": smart_title(str(station.get("name", "") or "")),
            "fc_brand": smart_title(str(station.get("brand", "") or "")),
            "fc_brand_group": normalize_brand_group(str(station.get("brand", "") or "")),
            "fc_address_full": normalize_address_full(str(station.get("address", "") or "")),
            "fc_street": street,
            "fc_suburb": suburb,
            "fc_state": state,
            "fc_postcode": postcode,
            "fc_lat": coerce_coord(station.get("lat")),
            "fc_lng": coerce_coord(station.get("lng")),
            "fc_fuel_types": ",".join(fuel_types),
            "fc_num_fuel_types": str(len(fuel_types)),
            "fc_has_price_outlier": str(has_outlier).lower(),
        }
        row.update(price_columns)
        rows.append(row)

    return rows, excluded


def clean_fuelcheck_stations(input_file: str = INPUT_FILE, output_file: str = OUTPUT_FILE) -> list[dict[str, object]]:
    """Clean FuelCheck station data and write the output CSV."""
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    with open(input_file, encoding="utf-8") as handle:
        stations = json.load(handle)

    if not isinstance(stations, list):
        print(f"ERROR: Expected a JSON list in {input_file}", file=sys.stderr)
        sys.exit(1)

    rows, excluded = build_rows(stations)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    flagged = sum(row["fc_has_price_outlier"] == "true" for row in rows)
    print(f"Wrote {len(rows)} rows to {output_file}")
    print(f"EV-only excluded: {excluded}")
    print(f"Price outliers flagged: {flagged}")
    return rows


if __name__ == "__main__":
    clean_fuelcheck_stations()
