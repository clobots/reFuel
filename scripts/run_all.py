#!/usr/bin/env python3
"""Run the full cleansing pipeline and validate the CSV outputs."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

from clean_fuelcheck import clean_fuelcheck_stations
from clean_google import clean_google_stations
from build_fuelcheck_history_dataset import write_history_dataset_csv, write_outage_dataset_csv
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

    print("\n[3/5] Merging matched stations...")
    merge_stations()

    print("\n[4/5] Building FuelCheck history dataset...")
    write_history_dataset_csv()

    print("\n[5/5] Building FuelCheck outage dataset...")
    write_outage_dataset_csv()

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
    ok &= validate_csv(
        os.path.join(clean_dir, "fuelcheck_history_dataset.csv"),
        min_rows=1,
        required_cols=["station_id", "latest_fuel_types", "fuel_types_ever"],
    )
    ok &= validate_csv(
        os.path.join(clean_dir, "fuelcheck_outages.csv"),
        min_rows=1,
        required_cols=["station_id", "fuel_type", "tracked_in_fuel_check"],
    )

    if not ok:
        print("\nSome validations FAILED.")
        sys.exit(1)

    print("\nAll validations passed.")

    # Auto-commit and push data changes
    now_local = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "add", "data/"], cwd=PROJECT_DIR, check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=PROJECT_DIR,
        )
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", f"Update FuelCheck prices ({now_local})"], cwd=PROJECT_DIR, check=True)
            subprocess.run(["git", "push", "origin", "dev"], cwd=PROJECT_DIR, check=True)
            subprocess.run(["git", "push", "origin", "dev:main"], cwd=PROJECT_DIR, check=True)
            print("\nCommitted and pushed to dev + main.")
        else:
            print("\nNo data changes to commit.")
    except subprocess.CalledProcessError as e:
        print(f"\nGit push failed: {e}")


if __name__ == "__main__":
    main()
