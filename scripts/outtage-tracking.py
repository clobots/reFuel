#!/usr/bin/env python3
"""Retrospective FuelCheck outage tracking and station-map export."""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

from build_fuelcheck_history_dataset import load_unique_snapshots, normalize_fuel_type  # noqa: E402

HISTORY_DIR = os.path.join(PROJECT_DIR, "data", "history")
HISTORY_ANALYSIS_CSV = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_history_dataset.csv")
IN_SCOPE_JSON = os.path.join(PROJECT_DIR, "data", "fuelcheck_stations.json")
META_JSON = os.path.join(PROJECT_DIR, "data", "fuelcheck_meta.json")
DAILY_OUTPUT_CSV = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_daily_availability.csv")
SUMMARY_OUTPUT_CSV = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_unavailability_summary.csv")
STATION_STATUS_CSV = os.path.join(PROJECT_DIR, "data", "clean", "fuelcheck_station_outage_status.csv")
HTML_OUTPUT = os.path.join(PROJECT_DIR, "data", "clean", "outtage-tracking.html")

PETROL_FUEL_TYPES = ["U91", "E10", "E85", "P95", "P98"]


def load_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_in_scope_station_ids(path: str = IN_SCOPE_JSON) -> set[str]:
    rows = load_json(path)
    return {
        str(row.get("id", "")).strip()
        for row in rows
        if str(row.get("id", "")).strip()
    }


def latest_snapshot_per_day(history_dir: str = HISTORY_DIR) -> list[tuple[str, object, list[dict]]]:
    snapshots = load_unique_snapshots(history_dir)
    latest_by_day: dict[str, tuple[str, object, list[dict]]] = {}

    for snapshot_path, seen_at, snapshot_rows in snapshots:
        day = seen_at.date().isoformat()
        current = latest_by_day.get(day)
        if current is None or seen_at > current[1]:
            latest_by_day[day] = (snapshot_path, seen_at, snapshot_rows)

    return [latest_by_day[day] for day in sorted(latest_by_day)]


def csv_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def split_fuels(value: str) -> list[str]:
    fuels = []
    for fuel_type in str(value or "").split(","):
        fuel_type = normalize_fuel_type(fuel_type)
        if fuel_type and fuel_type != "EV":
            fuels.append(fuel_type)
    return sorted(set(fuels))


def station_snapshot_map(snapshot_rows: list[dict]) -> dict[str, dict]:
    mapped = {}
    for station in snapshot_rows:
        station_id = str(station.get("id", "")).strip()
        if station_id:
            mapped[station_id] = station
    return mapped


def station_fuel_set(station: dict | None) -> set[str]:
    if not station:
        return set()
    return {
        normalize_fuel_type(price.get("fuel_type"))
        for price in station.get("prices", [])
        if normalize_fuel_type(price.get("fuel_type")) and normalize_fuel_type(price.get("fuel_type")) != "EV"
    }


def build_daily_availability_rows(
    history_rows: list[dict[str, str]],
    daily_snapshots: list[tuple[str, object, list[dict]]],
    in_scope_ids: set[str],
) -> list[dict[str, str]]:
    """Build one row per station, fuel type, and day using latest-daily snapshots."""
    rows: list[dict[str, str]] = []

    for history_row in history_rows:
        station_id = str(history_row.get("station_id", "")).strip()
        if not station_id or station_id not in in_scope_ids:
            continue

        tracked_fuels = split_fuels(history_row.get("fuel_types_ever", ""))
        if not tracked_fuels:
            continue

        lat = history_row.get("lat", "")
        lng = history_row.get("lng", "")

        for _snapshot_path, seen_at, snapshot_rows in daily_snapshots:
            day = seen_at.date().isoformat()
            station = station_snapshot_map(snapshot_rows).get(station_id)
            available_fuels = station_fuel_set(station)
            station_seen = station is not None

            for fuel_type in tracked_fuels:
                available = station_seen and fuel_type in available_fuels
                unavailable = station_seen and fuel_type not in available_fuels
                rows.append(
                    {
                        "station_id": station_id,
                        "station_name": history_row.get("station_name", ""),
                        "brand": history_row.get("brand", ""),
                        "address": history_row.get("address", ""),
                        "lat": lat,
                        "lng": lng,
                        "fuel_type": fuel_type,
                        "day": day,
                        "snapshot_at": seen_at.isoformat(),
                        "station_seen_on_day": "true" if station_seen else "false",
                        "fuel_available_on_day": "true" if available else "false",
                        "fuel_unavailable_on_day": "true" if unavailable else "false",
                        "latest_truth_fuel_types": history_row.get("latest_fuel_types", ""),
                        "fuel_types_ever": history_row.get("fuel_types_ever", ""),
                    }
                )

    rows.sort(key=lambda row: (row["station_name"], row["fuel_type"], row["day"], row["station_id"]))
    return rows


def build_unavailability_summary(daily_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in daily_rows:
        grouped[(row["station_id"], row["fuel_type"])].append(row)

    summaries: list[dict[str, str]] = []

    for (_station_id, fuel_type), rows in grouped.items():
        rows.sort(key=lambda row: row["day"])
        available_days = 0
        unavailable_days = 0
        station_missing_days = 0
        longest_streak = 0
        current_streak = 0
        first_unavailable_day = ""
        last_unavailable_day = ""

        for row in rows:
            if row["station_seen_on_day"] != "true":
                station_missing_days += 1
                current_streak = 0
                continue

            if row["fuel_available_on_day"] == "true":
                available_days += 1
                current_streak = 0
            else:
                unavailable_days += 1
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
                if not first_unavailable_day:
                    first_unavailable_day = row["day"]
                last_unavailable_day = row["day"]

        trailing_streak = 0
        for row in reversed(rows):
            if row["station_seen_on_day"] != "true":
                break
            if row["fuel_available_on_day"] == "true":
                break
            trailing_streak += 1

        observed_days = available_days + unavailable_days
        summaries.append(
            {
                "station_id": rows[0]["station_id"],
                "station_name": rows[0]["station_name"],
                "brand": rows[0]["brand"],
                "address": rows[0]["address"],
                "lat": rows[0]["lat"],
                "lng": rows[0]["lng"],
                "fuel_type": fuel_type,
                "days_observed": str(observed_days),
                "days_available": str(available_days),
                "days_unavailable": str(unavailable_days),
                "days_station_missing": str(station_missing_days),
                "first_unavailable_day": first_unavailable_day,
                "last_unavailable_day": last_unavailable_day,
                "longest_unavailable_streak_days": str(longest_streak),
                "current_unavailable_streak_days": str(trailing_streak),
                "currently_unavailable": "true" if trailing_streak > 0 else "false",
                "unavailability_rate_observed": (
                    f"{(unavailable_days / observed_days):.4f}" if observed_days else "0.0000"
                ),
                "latest_truth_fuel_types": rows[0]["latest_truth_fuel_types"],
                "fuel_types_ever": rows[0]["fuel_types_ever"],
            }
        )

    summaries.sort(
        key=lambda row: (
            -int(row["days_unavailable"]),
            -int(row["longest_unavailable_streak_days"]),
            row["station_name"],
            row["fuel_type"],
        )
    )
    return summaries


def classify_station_status(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in summary_rows:
        grouped[row["station_id"]].append(row)

    station_rows: list[dict[str, str]] = []

    for station_id, rows in grouped.items():
        sample = rows[0]
        usual_fuels = split_fuels(sample.get("fuel_types_ever", ""))
        basis_fuels = usual_fuels

        currently_unavailable_rows = [row for row in rows if csv_bool(row["currently_unavailable"])]
        unavailable_all = sorted({row["fuel_type"] for row in currently_unavailable_rows})
        unavailable_basis = sorted({row["fuel_type"] for row in currently_unavailable_rows if row["fuel_type"] in basis_fuels})
        available_basis = sorted(fuel for fuel in basis_fuels if fuel not in unavailable_basis)

        basis_count = len(basis_fuels)
        unavailable_count = len(unavailable_basis)
        unavailable_ratio = (unavailable_count / basis_count) if basis_count else 0.0
        max_current_streak = max(
            (int(row["current_unavailable_streak_days"]) for row in currently_unavailable_rows if row["fuel_type"] in unavailable_basis),
            default=0,
        )
        completely_out_of_all_usual = bool(usual_fuels) and len(unavailable_all) == len(usual_fuels)

        if completely_out_of_all_usual or (unavailable_ratio >= 0.75 and max_current_streak > 3):
            status = "red"
            status_label = "Critical outage"
        elif unavailable_ratio >= 0.75:
            status = "orange"
            status_label = "Most fuels out"
        elif unavailable_count > 0:
            status = "yellow"
            status_label = "Partial outage"
        else:
            status = "green"
            status_label = "All usual fuels available"

        station_rows.append(
            {
                "station_id": station_id,
                "station_name": sample["station_name"],
                "brand": sample["brand"],
                "address": sample["address"],
                "lat": sample["lat"],
                "lng": sample["lng"],
                "status": status,
                "status_label": status_label,
                "usual_fuel_types": ",".join(usual_fuels),
                "usual_petrol_types": ",".join(basis_fuels),
                "available_now": ",".join(available_basis),
                "unavailable_now": ",".join(unavailable_basis),
                "usual_fuel_count": str(len(usual_fuels)),
                "basis_fuel_count": str(basis_count),
                "unavailable_count": str(unavailable_count),
                "unavailable_ratio_pct": f"{unavailable_ratio * 100:.1f}",
                "max_current_streak_days": str(max_current_streak),
                "completely_out_of_all_usual": "true" if completely_out_of_all_usual else "false",
            }
        )

    station_rows.sort(
        key=lambda row: (
            {"red": 0, "orange": 1, "yellow": 2, "green": 3}.get(row["status"], 9),
            -float(row["unavailable_ratio_pct"]),
            -int(row["max_current_streak_days"]),
            row["station_name"],
        )
    )
    return station_rows


def write_csv(path: str, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_daily_unavailability_series(
    station_rows: list[dict[str, str]],
    daily_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Aggregate daily unavailability across tracked stations with usual fuels."""
    basis_by_station = {
        row["station_id"]: int(row["basis_fuel_count"])
        for row in station_rows
        if int(row.get("basis_fuel_count") or 0) > 0
    }
    days = sorted({row["day"] for row in daily_rows})
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in daily_rows:
        station_id = row["station_id"]
        if station_id not in basis_by_station:
            continue
        grouped[(row["day"], station_id)].append(row)

    series: list[dict[str, str]] = []
    tracked_station_count = len(basis_by_station)

    for day in days:
        stations_with_outage = 0
        observed_station_count = 0
        availability_scores = []

        for station_id, basis_count in basis_by_station.items():
            rows = grouped.get((day, station_id), [])
            if not rows:
                continue
            observed_station_count += 1
            unavailable_count = sum(1 for row in rows if row["fuel_unavailable_on_day"] == "true")
            availability_scores.append(1 - (unavailable_count / basis_count))
            if unavailable_count > 0:
                stations_with_outage += 1

        outage_pct = ((stations_with_outage / tracked_station_count) * 100) if tracked_station_count else 0.0
        avg_availability_pct = (sum(availability_scores) / len(availability_scores) * 100) if availability_scores else 0.0
        series.append(
            {
                "day": day,
                "stations_with_outage": str(stations_with_outage),
                "tracked_station_count": str(tracked_station_count),
                "observed_station_count": str(observed_station_count),
                "outage_pct": f"{outage_pct:.1f}",
                "avg_availability_pct": f"{avg_availability_pct:.1f}",
            }
        )

    return series


def build_map_html(station_rows: list[dict[str, str]], daily_rows: list[dict[str, str]], output_path: str) -> None:
    marker_rows = [
        row
        for row in station_rows
        if row.get("lat") not in ("", None) and row.get("lng") not in ("", None)
    ]
    current_counts = defaultdict(int)
    for row in station_rows:
        current_counts[row["status"]] += 1
    total_in_scope = len(load_in_scope_station_ids())
    stations_with_outages_today = current_counts["yellow"] + current_counts["orange"] + current_counts["red"]
    outage_station_pct = ((stations_with_outages_today / total_in_scope) * 100) if total_in_scope else 0.0
    availability_scores = []
    for row in station_rows:
        basis_count = int(row["basis_fuel_count"]) if row.get("basis_fuel_count") else 0
        unavailable_count = int(row["unavailable_count"]) if row.get("unavailable_count") else 0
        if basis_count <= 0:
            continue
        availability_scores.append(1 - (unavailable_count / basis_count))
    average_availability_pct = (sum(availability_scores) / len(availability_scores) * 100) if availability_scores else 0.0
    daily_series = build_daily_unavailability_series(station_rows, daily_rows)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>reFuel Retrospective Outage Tracking</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  >
  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""
  ></script>
  <style>
    :root {{
      color-scheme: dark;
      --bg:#081119;
      --panel:#0f1b2b;
      --line:#23364f;
      --text:#edf4ff;
      --muted:#9bb0c9;
      --accent:#f0c76e;
      --green:#47c27d;
      --yellow:#f0c76e;
      --orange:#ff9c54;
      --red:#ff6b6b;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      font:14px/1.45 ui-sans-serif,system-ui,-apple-system,sans-serif;
      color:var(--text);
      background:radial-gradient(circle at top,#17304a 0,#081119 60%);
    }}
    .wrap {{ max-width:1500px; margin:0 auto; padding:24px; }}
    .top {{ display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom:18px; }}
    h1 {{ margin:0; font-size:28px; }}
    p {{ margin:6px 0 0; color:var(--muted); }}
    .stats {{ display:grid; grid-template-columns:repeat(7,minmax(120px,1fr)); gap:12px; width:min(1280px,100%); }}
    .card {{ background:rgba(15,27,43,.92); border:1px solid var(--line); border-radius:14px; padding:14px 16px; }}
    .card strong {{ display:block; font-size:24px; margin-bottom:4px; }}
    .card small {{ display:block; margin-top:6px; color:var(--muted); font-size:12px; line-height:1.35; }}
    .legend {{ display:flex; gap:12px; flex-wrap:wrap; margin:14px 0 18px; }}
    .legend-item {{ display:flex; align-items:center; gap:8px; background:#16263c; border:1px solid var(--line); border-radius:999px; padding:6px 10px; color:var(--muted); }}
    .swatch {{ width:12px; height:12px; border-radius:50%; border:1px solid rgba(255,255,255,.35); }}
    .chart-card {{ background:rgba(15,27,43,.92); border:1px solid var(--line); border-radius:16px; padding:16px; margin:0 0 18px; }}
    .chart-card h2 {{ margin:0; font-size:18px; }}
    .chart-card p {{ margin:6px 0 0; }}
    .chart-wrap {{ margin-top:14px; }}
    .chart-svg {{ width:100%; height:auto; display:block; }}
    .chart-axis {{ stroke:#4a5f7d; stroke-width:1; }}
    .chart-grid {{ stroke:#2b3f5b; stroke-width:1; stroke-dasharray:4 4; }}
    .chart-line {{ fill:none; stroke:var(--accent); stroke-width:3; }}
    .chart-point {{ fill:var(--accent); }}
    .chart-label {{ fill:var(--muted); font-size:12px; }}
    .chart-value {{ fill:var(--text); font-size:12px; font-weight:600; }}
    .controls {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin:0 0 16px; }}
    input, select {{ background:var(--panel); color:var(--text); border:1px solid var(--line); border-radius:10px; padding:10px 12px; }}
    input {{ min-width:260px; flex:1 1 280px; }}
    #map {{ height:56vh; min-height:420px; border-radius:18px; overflow:hidden; border:1px solid var(--line); box-shadow:0 10px 30px rgba(0,0,0,.25); }}
    .table-wrap {{ margin-top:18px; background:rgba(15,27,43,.92); border:1px solid var(--line); border-radius:16px; overflow:auto; max-height:50vh; }}
    table {{ width:100%; border-collapse:collapse; min-width:1350px; }}
    th, td {{ padding:9px 10px; border-bottom:1px solid rgba(35,54,79,.8); text-align:left; vertical-align:top; }}
    th {{ position:sticky; top:0; background:#0d1726; color:#c6d6f4; font-size:12px; letter-spacing:.02em; cursor:pointer; user-select:none; }}
    tbody tr:nth-child(even) {{ background:rgba(255,255,255,.02); }}
    tbody tr:hover td {{ background:rgba(255,255,255,.04); }}
    .marker {{
      width:18px; height:18px; border-radius:50%;
      border:2px solid rgba(255,255,255,.92);
      box-shadow:0 0 0 3px rgba(4,10,14,.22);
    }}
    .green {{ background:var(--green); }}
    .yellow {{ background:var(--yellow); }}
    .orange {{ background:var(--orange); }}
    .red {{ background:var(--red); }}
    .status-pill {{
      display:inline-flex; align-items:center; gap:6px;
      border:1px solid var(--line); border-radius:999px; padding:4px 8px;
      color:var(--text);
    }}
    .status-pill .swatch {{ width:10px; height:10px; }}
    .num-bad {{ color:var(--red); font-weight:700; }}
    .num-warn {{ color:var(--orange); font-weight:700; }}
    .num-mid {{ color:var(--yellow); font-weight:700; }}
    .bool-true {{ color:var(--red); font-weight:700; }}
    .bool-false {{ color:var(--muted); }}
    .popup p {{ margin:6px 0; color:#23364f; }}
    .popup h3 {{ margin:0 0 6px; color:#11202b; }}
    .popup strong {{ color:#11202b; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div>
        <h1>reFuel Retrospective Outage Tracking</h1>
        <p>Green means all usual fuels are available. Yellow means some usual petrol types are missing. Orange means 75%+ of usual petrol types are out. Red means 75%+ are out for more than 3 days consecutively, or all usual types are currently unavailable.</p>
      </div>
      <div class="stats">
        <div class="card"><strong>{len(station_rows)}</strong><span>Tracked Stations</span></div>
        <div class="card"><strong>{len({row['day'] for row in daily_rows})}</strong><span>Days Analysed</span></div>
        <div class="card"><strong>{current_counts['green']}</strong><span>Green</span></div>
        <div class="card"><strong>{current_counts['yellow'] + current_counts['orange']}</strong><span>Partial / Major</span></div>
        <div class="card"><strong>{current_counts['red']}</strong><span>Critical</span></div>
        <div class="card"><strong>{outage_station_pct:.1f}%</strong><span>Stations with outages today</span><small>{stations_with_outages_today} of {total_in_scope} in-scope FuelCheck stations currently show a partial or full outage. This is not a measure of total suburb-wide supply.</small></div>
        <div class="card"><strong>{average_availability_pct:.1f}%</strong><span>Average station availability</span><small>For each tracked station, we compare fuels shown today against the fuels that station has ever shown before. A station showing 3 of 4 usual fuels scores 75%.</small></div>
      </div>
    </div>
    <div class="legend">
      <span class="legend-item"><span class="swatch green"></span>All usual fuels available</span>
      <span class="legend-item"><span class="swatch yellow"></span>Some usual petrol types unavailable</span>
      <span class="legend-item"><span class="swatch orange"></span>75%+ of usual petrol types unavailable</span>
      <span class="legend-item"><span class="swatch red"></span>Critical prolonged outage or all usual types unavailable</span>
    </div>
    <section class="chart-card">
      <h2>Availability Since Tracking Began</h2>
      <p>This line shows the average share of each station's usual fuels that were available on each tracked day. Higher is better, and small dips do not automatically mean widespread local shortages.</p>
      <div class="chart-wrap">
        <svg id="daily-chart" class="chart-svg" viewBox="0 0 960 280" role="img" aria-label="Daily availability percentage line chart"></svg>
      </div>
    </section>
    <div class="controls">
      <input id="search" placeholder="Filter by station, address, fuel list, status">
      <select id="status-filter">
        <option value="">All statuses</option>
        <option value="green">Green</option>
        <option value="yellow">Yellow</option>
        <option value="orange">Orange</option>
        <option value="red">Red</option>
      </select>
    </div>
    <div id="map"></div>
    <div class="table-wrap">
      <table>
        <thead id="head"></thead>
        <tbody id="body"></tbody>
      </table>
    </div>
  </div>
  <script>
    const stationRows = {json.dumps(station_rows, separators=(",", ":"))};
    const dailySeries = {json.dumps(daily_series, separators=(",", ":"))};
    const columns = [
      "station_name",
      "brand",
      "status_label",
      "unavailable_ratio_pct",
      "max_current_streak_days",
      "usual_fuel_count",
      "basis_fuel_count",
      "unavailable_count",
      "usual_fuel_types",
      "usual_petrol_types",
      "available_now",
      "unavailable_now",
      "completely_out_of_all_usual",
      "address",
      "lat",
      "lng"
    ];
    const map = L.map("map", {{ zoomControl: true, preferCanvas: true }}).setView([-33.82, 151.03], 11);
    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }}).addTo(map);

    const markers = [];
    const markerById = new Map();
    const head = document.getElementById("head");
    const body = document.getElementById("body");
    const search = document.getElementById("search");
    const statusFilter = document.getElementById("status-filter");
    const chart = document.getElementById("daily-chart");
    let sortState = {{ column: "status_label", direction: "asc" }};

    function escapeHtml(value) {{
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function markerIcon(status) {{
      return L.divIcon({{
        className: "",
        html: `<div class="marker ${{status}}"></div>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
      }});
    }}

    function popupHtml(row) {{
      return `
        <div class="popup">
          <h3>${{escapeHtml(row.station_name)}}</h3>
          <p><strong>Status:</strong> ${{escapeHtml(row.status_label)}}</p>
          <p><strong>Unavailable now:</strong> ${{escapeHtml(row.unavailable_now || "-")}}</p>
          <p><strong>Available now:</strong> ${{escapeHtml(row.available_now || "-")}}</p>
          <p><strong>Usual fuels:</strong> ${{escapeHtml(row.usual_fuel_types || "-")}}</p>
          <p><strong>Max current streak:</strong> ${{escapeHtml(row.max_current_streak_days)}} day(s)</p>
          <p><strong>Address:</strong> ${{escapeHtml(row.address)}}</p>
        </div>
      `;
    }}

    stationRows.forEach((row) => {{
      const lat = Number(row.lat);
      const lng = Number(row.lng);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      const marker = L.marker([lat, lng], {{ icon: markerIcon(row.status) }})
        .bindPopup(popupHtml(row), {{ maxWidth: 360 }})
        .addTo(map);
      marker.row = row;
      markers.push(marker);
      markerById.set(row.station_id, marker);
    }});

    if (markers.length) {{
      map.fitBounds(L.featureGroup(markers).getBounds(), {{ padding: [30, 30] }});
    }}

    function renderHead() {{
      head.innerHTML = "";
      const tr = document.createElement("tr");
      columns.forEach((column) => {{
        const th = document.createElement("th");
        const arrow = sortState.column === column ? (sortState.direction === "asc" ? " ▲" : " ▼") : "";
        th.textContent = column + arrow;
        th.addEventListener("click", () => {{
          if (sortState.column === column) {{
            sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
          }} else {{
            sortState = {{ column, direction: "asc" }};
          }}
          renderTable();
        }});
        tr.appendChild(th);
      }});
      head.appendChild(tr);
    }}

    function filteredRows() {{
      const q = search.value.trim().toLowerCase();
      const selectedStatus = statusFilter.value;
      return stationRows.filter((row) => {{
        const textOk = !q || Object.values(row).some((value) => String(value).toLowerCase().includes(q));
        const statusOk = !selectedStatus || row.status === selectedStatus;
        return textOk && statusOk;
      }});
    }}

    function compareValues(a, b) {{
      const aNum = Number(a);
      const bNum = Number(b);
      if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) return aNum - bNum;
      return String(a).localeCompare(String(b));
    }}

    function updateMap(rows) {{
      const visibleIds = new Set(rows.map((row) => row.station_id));
      const visibleMarkers = [];
      markers.forEach((marker) => {{
        if (visibleIds.has(marker.row.station_id)) {{
          if (!map.hasLayer(marker)) marker.addTo(map);
          visibleMarkers.push(marker);
        }} else if (map.hasLayer(marker)) {{
          map.removeLayer(marker);
        }}
      }});
      if (visibleMarkers.length) {{
        map.fitBounds(L.featureGroup(visibleMarkers).getBounds(), {{ padding: [30, 30], maxZoom: 14 }});
      }}
    }}

    function decorateCell(td, column, row) {{
      if (column === "status_label") {{
        td.innerHTML = `<span class="status-pill"><span class="swatch ${{row.status}}"></span>${{escapeHtml(row.status_label)}}</span>`;
        return;
      }}
      if (column === "completely_out_of_all_usual") {{
        td.className = row[column] === "true" ? "bool-true" : "bool-false";
      }}
      if (["unavailable_ratio_pct", "max_current_streak_days", "unavailable_count"].includes(column)) {{
        const value = Number(row[column]);
        if (value >= 75 || value >= 4) td.classList.add("num-bad");
        else if (value > 0) td.classList.add("num-warn");
      }}
    }}

    function renderTable() {{
      const rows = filteredRows().sort((a, b) => {{
        const result = compareValues(a[sortState.column], b[sortState.column]);
        return sortState.direction === "asc" ? result : -result;
      }});

      updateMap(rows);

      body.innerHTML = "";
      rows.forEach((row) => {{
        const tr = document.createElement("tr");
        tr.addEventListener("click", () => {{
          const marker = markerById.get(row.station_id);
          if (!marker) return;
          map.setView(marker.getLatLng(), 14);
          marker.openPopup();
        }});
        columns.forEach((column) => {{
          const td = document.createElement("td");
          td.textContent = row[column] || "";
          decorateCell(td, column, row);
          tr.appendChild(td);
        }});
        body.appendChild(tr);
      }});
    }}

    search.addEventListener("input", renderTable);
    statusFilter.addEventListener("change", renderTable);

    function renderChart() {{
      if (!dailySeries.length) return;
      const width = 960;
      const height = 280;
      const margin = {{ top: 20, right: 24, bottom: 48, left: 52 }};
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      const values = dailySeries.map((row) => Number(row.avg_availability_pct));
      const minValue = Math.min(...values, 95);
      const maxValue = 100;
      const domainMin = Math.max(0, Math.floor((minValue - 2) / 5) * 5);
      const points = dailySeries.map((row, index) => {{
        const x = margin.left + (dailySeries.length === 1 ? innerWidth / 2 : (index / (dailySeries.length - 1)) * innerWidth);
        const y = margin.top + innerHeight - (((Number(row.avg_availability_pct) - domainMin) / (maxValue - domainMin || 1)) * innerHeight);
        return {{ ...row, x, y }};
      }});
      const path = points.map((point, index) => `${{index === 0 ? "M" : "L"}}${{point.x.toFixed(1)}},${{point.y.toFixed(1)}}`).join(" ");
      const ticks = [domainMin, (domainMin + maxValue) / 2, maxValue];
      chart.innerHTML = `
        <line class="chart-axis" x1="${{margin.left}}" y1="${{margin.top + innerHeight}}" x2="${{width - margin.right}}" y2="${{margin.top + innerHeight}}"></line>
        <line class="chart-axis" x1="${{margin.left}}" y1="${{margin.top}}" x2="${{margin.left}}" y2="${{margin.top + innerHeight}}"></line>
        ${{ticks.map((tick) => {{
          const y = margin.top + innerHeight - (((tick - domainMin) / (maxValue - domainMin || 1)) * innerHeight);
          return `
            <line class="chart-grid" x1="${{margin.left}}" y1="${{y}}" x2="${{width - margin.right}}" y2="${{y}}"></line>
            <text class="chart-label" x="${{margin.left - 10}}" y="${{y + 4}}" text-anchor="end">${{tick.toFixed(1)}}%</text>
          `;
        }}).join("")}}
        <path class="chart-line" d="${{path}}"></path>
        ${{points.map((point) => `
          <circle class="chart-point" cx="${{point.x}}" cy="${{point.y}}" r="4"></circle>
          <text class="chart-value" x="${{point.x}}" y="${{point.y - 10}}" text-anchor="middle">${{point.avg_availability_pct}}%</text>
          <text class="chart-label" x="${{point.x}}" y="${{height - 18}}" text-anchor="middle">${{point.day.slice(5)}}</text>
        `).join("")}}
      `;
    }}

    renderChart();
    renderHead();
    renderTable();
  </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(html)


def main() -> int:
    history_rows = load_csv(HISTORY_ANALYSIS_CSV)
    in_scope_ids = load_in_scope_station_ids()
    daily_snapshots = latest_snapshot_per_day()
    meta = load_json(META_JSON)

    daily_rows = build_daily_availability_rows(history_rows, daily_snapshots, in_scope_ids)
    summary_rows = build_unavailability_summary(daily_rows)
    station_rows = classify_station_status(summary_rows)

    write_csv(
        DAILY_OUTPUT_CSV,
        daily_rows,
        [
            "station_id",
            "station_name",
            "brand",
            "address",
            "lat",
            "lng",
            "fuel_type",
            "day",
            "snapshot_at",
            "station_seen_on_day",
            "fuel_available_on_day",
            "fuel_unavailable_on_day",
            "latest_truth_fuel_types",
            "fuel_types_ever",
        ],
    )
    write_csv(
        SUMMARY_OUTPUT_CSV,
        summary_rows,
        [
            "station_id",
            "station_name",
            "brand",
            "address",
            "lat",
            "lng",
            "fuel_type",
            "days_observed",
            "days_available",
            "days_unavailable",
            "days_station_missing",
            "first_unavailable_day",
            "last_unavailable_day",
            "longest_unavailable_streak_days",
            "current_unavailable_streak_days",
            "currently_unavailable",
            "unavailability_rate_observed",
            "latest_truth_fuel_types",
            "fuel_types_ever",
        ],
    )
    write_csv(
        STATION_STATUS_CSV,
        station_rows,
        [
            "station_id",
            "station_name",
            "brand",
            "address",
            "lat",
            "lng",
            "status",
            "status_label",
            "usual_fuel_types",
            "usual_petrol_types",
            "available_now",
            "unavailable_now",
            "usual_fuel_count",
            "basis_fuel_count",
            "unavailable_count",
            "unavailable_ratio_pct",
            "max_current_streak_days",
            "completely_out_of_all_usual",
        ],
    )
    build_map_html(station_rows, daily_rows, HTML_OUTPUT)

    print("reFuel retrospective outage tracking")
    print("=" * 34)
    print(f"In-scope FuelCheck stations: {len(in_scope_ids)}")
    print(f"Metadata in_scraped_suburbs: {meta.get('in_scraped_suburbs', '-')}")
    print(f"Latest-per-day snapshots analysed: {len(daily_snapshots)}")
    print(f"Stations with tracked fuel history: {len({row['station_id'] for row in summary_rows})}")
    print(f"Daily station/fuel rows: {len(daily_rows)}")
    print(f"Station/fuel summaries: {len(summary_rows)}")
    print(f"Station map rows: {len(station_rows)}")
    print(f"Wrote: {DAILY_OUTPUT_CSV}")
    print(f"Wrote: {SUMMARY_OUTPUT_CSV}")
    print(f"Wrote: {STATION_STATUS_CSV}")
    print(f"Wrote: {HTML_OUTPUT}")

    status_counts = defaultdict(int)
    for row in station_rows:
        status_counts[row["status"]] += 1

    print("\nStation status counts:")
    for status in ("green", "yellow", "orange", "red"):
        print(f"- {status}: {status_counts[status]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
