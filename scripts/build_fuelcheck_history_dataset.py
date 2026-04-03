#!/usr/bin/env python3
"""Build a historical FuelCheck station dataset from local full snapshots."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(PROJECT_DIR, "data", "history")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_history_dataset.csv")
OUTAGE_OUTPUT_FILE = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_outages.csv")
MATCHED_STATIONS_FILE = os.path.join(PROJECT_DIR, "data", "clean", "matched_stations.csv")

FUEL_TYPE_ORDER = ["U91", "E10", "E85", "P95", "P98", "DL", "PDL", "LPG", "EV"]


def snapshot_timestamp_from_path(path: str) -> datetime:
    """Extract the UTC timestamp from a snapshot filename."""
    match = re.search(r"fuelcheck_full_(\d{4}-\d{2}-\d{2}T\d{6})\.json$", os.path.basename(path))
    if not match:
        raise ValueError(f"Unrecognized snapshot filename: {path}")
    return datetime.strptime(match.group(1), "%Y-%m-%dT%H%M%S")


def station_identifier(station: dict) -> str:
    """Return a stable identifier for a station across snapshots."""
    station_id = station.get("id")
    if station_id not in (None, ""):
        return str(station_id)
    return f"{station.get('name', '').strip()}|{station.get('address', '').strip()}"


def normalize_fuel_type(value: str) -> str:
    """Normalize a fuel type code."""
    return (value or "").strip().upper()


def sorted_fuel_types(fuel_types: set[str]) -> list[str]:
    """Sort fuel types with common retail fuels first."""
    rank = {fuel: idx for idx, fuel in enumerate(FUEL_TYPE_ORDER)}
    return sorted(fuel_types, key=lambda fuel: (rank.get(fuel, len(rank)), fuel))


def bool_to_csv(value: bool) -> str:
    """Write booleans as lowercase strings for CSV readability."""
    return "true" if value else "false"


def snapshot_fingerprint(snapshot_rows: list[dict]) -> str:
    """Return a stable fingerprint for a snapshot's contents."""
    canonical = json.dumps(snapshot_rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_unique_snapshots(history_dir: str) -> list[tuple[str, datetime, list[dict]]]:
    """Load history snapshots, keeping only the first copy of identical content."""
    snapshot_paths = sorted(
        os.path.join(history_dir, name)
        for name in os.listdir(history_dir)
        if name.startswith("fuelcheck_full_") and name.endswith(".json")
    )
    if not snapshot_paths:
        raise FileNotFoundError(f"No history snapshots found in {history_dir}")

    unique_snapshots: list[tuple[str, datetime, list[dict]]] = []
    seen_fingerprints: set[str] = set()

    for snapshot_path in snapshot_paths:
        with open(snapshot_path, encoding="utf-8") as handle:
            snapshot_rows = json.load(handle)
        fingerprint = snapshot_fingerprint(snapshot_rows)
        if fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(fingerprint)
        unique_snapshots.append(
            (snapshot_path, snapshot_timestamp_from_path(snapshot_path), snapshot_rows)
        )

    return unique_snapshots


def load_refuel_tracked_station_ids(matched_csv: str = MATCHED_STATIONS_FILE) -> set[str]:
    """Return FuelCheck station IDs currently tracked in reFuel's clean matched dataset."""
    if not os.path.exists(matched_csv):
        return set()
    with open(matched_csv, newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return {
            str(row["fc_id"]).strip()
            for row in rows
            if row.get("fc_id") not in (None, "")
        }


def build_fuelcheck_outage_dataset(
    history_rows: list[dict],
    canonical_fuel_types: list[str],
    tracked_station_ids: set[str] | None = None,
) -> list[dict]:
    """Return one row per station/fuel outage.

    An outage means the station has had a fuel type in any historical snapshot,
    but the latest snapshot no longer lists that fuel type.
    """
    outage_rows: list[dict] = []
    tracked_station_ids = tracked_station_ids or set()

    for row in history_rows:
        latest_fuels = {
            fuel_type.strip()
            for fuel_type in (row.get("latest_fuel_types", "") or "").split(",")
            if fuel_type.strip()
        }
        for fuel_type in canonical_fuel_types:
            ever_had = bool(row.get(f"ever_had_{fuel_type}", False))
            latest_has = fuel_type in latest_fuels
            is_outage = ever_had and not latest_has
            if not is_outage:
                continue

            outage_rows.append(
                {
                    "station_id": row["station_id"],
                    "station_name": row["station_name"],
                    "brand": row["brand"],
                    "address": row["address"],
                    "lat": row["lat"],
                    "lng": row["lng"],
                    "fuel_type": fuel_type,
                    "tracked_in_fuel_check": row["station_id"] in tracked_station_ids,
                    "is_outage": True,
                    "ever_had_fuel": True,
                    "latest_has_fuel": False,
                    "first_seen_at": row["first_seen_at"],
                    "last_seen_at": row["last_seen_at"],
                    "snapshots_seen": row["snapshots_seen"],
                    "days_seen_count": row["days_seen_count"],
                    "day_set": row["day_set"],
                    "latest_fuel_types": row["latest_fuel_types"],
                    "fuel_types_ever": row["fuel_types_ever"],
                }
            )

    outage_rows.sort(key=lambda row: (row["station_name"], row["fuel_type"], row["station_id"]))
    return outage_rows


def build_fuelcheck_history_dataset(
    history_dir: str = HISTORY_DIR,
    exclude_ev_only: bool = True,
) -> tuple[list[dict], list[str]]:
    """Return one row per station summarizing fuel history across all snapshots."""
    snapshots = load_unique_snapshots(history_dir)
    stations: dict[str, dict] = {}
    all_fuel_types_seen: set[str] = set()

    for snapshot_path, seen_at, snapshot_rows in snapshots:
        seen_day = seen_at.date().isoformat()
        for station in snapshot_rows:
            key = station_identifier(station)
            row = stations.setdefault(
                key,
                {
                    "station_id": str(station.get("id", "")),
                    "station_name": station.get("name", ""),
                    "brand": station.get("brand", ""),
                    "address": station.get("address", ""),
                    "lat": station.get("lat", ""),
                    "lng": station.get("lng", ""),
                    "first_seen_at": seen_at.isoformat(),
                    "last_seen_at": seen_at.isoformat(),
                    "latest_snapshot_at": seen_at,
                    "latest_fuel_types": set(),
                    "fuel_types_ever": set(),
                    "days_seen": set(),
                    "snapshots_seen": 0,
                },
            )

            row["snapshots_seen"] += 1
            row["days_seen"].add(seen_day)

            if seen_at < datetime.fromisoformat(row["first_seen_at"]):
                row["first_seen_at"] = seen_at.isoformat()
            if seen_at > datetime.fromisoformat(row["last_seen_at"]):
                row["last_seen_at"] = seen_at.isoformat()

            fuel_types_this_snapshot: set[str] = set()
            for price in station.get("prices", []):
                fuel_type = normalize_fuel_type(price.get("fuel_type"))
                if not fuel_type:
                    continue
                fuel_types_this_snapshot.add(fuel_type)
                row["fuel_types_ever"].add(fuel_type)
                all_fuel_types_seen.add(fuel_type)

            if seen_at >= row["latest_snapshot_at"]:
                row["latest_snapshot_at"] = seen_at
                row["station_name"] = station.get("name", row["station_name"])
                row["brand"] = station.get("brand", row["brand"])
                row["address"] = station.get("address", row["address"])
                row["lat"] = station.get("lat", row["lat"])
                row["lng"] = station.get("lng", row["lng"])
                row["latest_fuel_types"] = fuel_types_this_snapshot

    if exclude_ev_only:
        stations = {
            key: row
            for key, row in stations.items()
            if any(fuel != "EV" for fuel in row["fuel_types_ever"])
        }

    canonical_fuel_types = sorted_fuel_types(all_fuel_types_seen)
    dataset_rows: list[dict] = []

    for row in stations.values():
        latest_fuels = sorted_fuel_types(set(row["latest_fuel_types"]))
        ever_fuels = sorted_fuel_types(set(row["fuel_types_ever"]))
        dataset_row = {
            "station_id": row["station_id"],
            "station_name": row["station_name"],
            "brand": row["brand"],
            "address": row["address"],
            "lat": row["lat"],
            "lng": row["lng"],
            "first_seen_at": row["first_seen_at"],
            "last_seen_at": row["last_seen_at"],
            "snapshots_seen": row["snapshots_seen"],
            "days_seen_count": len(row["days_seen"]),
            "day_set": ",".join(sorted(row["days_seen"])),
            "latest_fuel_types": ",".join(latest_fuels),
            "fuel_types_ever": ",".join(ever_fuels),
        }
        for fuel_type in canonical_fuel_types:
            dataset_row[f"ever_had_{fuel_type}"] = fuel_type in row["fuel_types_ever"]
        dataset_rows.append(dataset_row)

    dataset_rows.sort(key=lambda row: (row["station_name"], row["address"], row["station_id"]))
    return dataset_rows, canonical_fuel_types


def write_history_dataset_csv(output_file: str = OUTPUT_FILE) -> tuple[str, int]:
    """Build the historical station dataset and write it to CSV."""
    rows, canonical_fuel_types = build_fuelcheck_history_dataset()
    fieldnames = [
        "station_id",
        "station_name",
        "brand",
        "address",
        "lat",
        "lng",
        "first_seen_at",
        "last_seen_at",
        "snapshots_seen",
        "days_seen_count",
        "day_set",
        "latest_fuel_types",
        "fuel_types_ever",
    ] + [f"ever_had_{fuel_type}" for fuel_type in canonical_fuel_types]

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = row.copy()
            for fuel_type in canonical_fuel_types:
                field = f"ever_had_{fuel_type}"
                csv_row[field] = bool_to_csv(csv_row[field])
            writer.writerow(csv_row)

    return output_file, len(rows)


def write_outage_dataset_csv(output_file: str = OUTAGE_OUTPUT_FILE) -> tuple[str, int]:
    """Build the FuelCheck outage dataset and write it to CSV."""
    rows, canonical_fuel_types = build_fuelcheck_history_dataset()
    tracked_station_ids = load_refuel_tracked_station_ids()
    outage_rows = build_fuelcheck_outage_dataset(rows, canonical_fuel_types, tracked_station_ids)
    fieldnames = [
        "station_id",
        "station_name",
        "brand",
        "address",
        "lat",
        "lng",
        "fuel_type",
        "tracked_in_fuel_check",
        "is_outage",
        "ever_had_fuel",
        "latest_has_fuel",
        "first_seen_at",
        "last_seen_at",
        "snapshots_seen",
        "days_seen_count",
        "day_set",
        "latest_fuel_types",
        "fuel_types_ever",
    ]

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in outage_rows:
            csv_row = row.copy()
            for key in ("tracked_in_fuel_check", "is_outage", "ever_had_fuel", "latest_has_fuel"):
                csv_row[key] = bool_to_csv(csv_row[key])
            writer.writerow(csv_row)

    return output_file, len(outage_rows)


if __name__ == "__main__":
    history_output_file, history_count = write_history_dataset_csv()
    outage_output_file, outage_count = write_outage_dataset_csv()
    print(f"Wrote {history_count} rows to {history_output_file}")
    print(f"Wrote {outage_count} rows to {outage_output_file}")
