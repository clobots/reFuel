#!/usr/bin/env python3
"""Run the full cleansing pipeline and validate the CSV outputs."""

from __future__ import annotations

import csv
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

from clean_fuelcheck import clean_fuelcheck_stations
from clean_google import clean_google_stations
from merge_matched import merge_stations


def validate_csv(path: str, min_rows: int, required_cols: list[str]) -> bool:
    """Validate that a CSV exists and has the expected basic shape."""
    if not os.path.exists(path):
        print(f"FAIL: {path} does not exist")
        return False

    with open(path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) < min_rows:
        print(f"FAIL: {path} has {len(rows)} rows, expected at least {min_rows}")
        return False

    if not rows:
        print(f"FAIL: {path} is empty")
        return False

    missing = [column for column in required_cols if column not in rows[0]]
    if missing:
        print(f"FAIL: {path} missing columns: {missing}")
        return False

    print(f"OK: {path} — {len(rows)} rows, {len(rows[0])} columns")
    return True


def main() -> None:
    print("=" * 60)
    print("reFuel Data Cleansing Pipeline")
    print("=" * 60)

    print("\n[1/3] Cleaning Google stations...")
    clean_google_stations()

    print("\n[2/3] Cleaning FuelCheck stations...")
    clean_fuelcheck_stations()

    print("\n[3/3] Merging matched stations...")
    merge_stations()

    clean_dir = os.path.join(PROJECT_DIR, "data", "clean")

    print("\n" + "=" * 60)
    print("Validation")
    print("=" * 60)

    ok = True
    ok &= validate_csv(
        os.path.join(clean_dir, "google_stations.csv"),
        min_rows=1,
        required_cols=["google_name", "google_lat", "google_lng"],
    )
    ok &= validate_csv(
        os.path.join(clean_dir, "fuelcheck_stations.csv"),
        min_rows=100,
        required_cols=["fc_id", "fc_name", "fc_price_U91_cents"],
    )
    ok &= validate_csv(
        os.path.join(clean_dir, "matched_stations.csv"),
        min_rows=1,
        required_cols=["match_status", "google_name", "fc_name"],
    )

    if not ok:
        print("\nSome validations FAILED.")
        sys.exit(1)

    print("\nAll validations passed.")


if __name__ == "__main__":
    main()
