#!/usr/bin/env python3
"""
WHAT: Fetch all NSW FuelCheck stations, filter to target bounding box
WHY: Single bulk call is simpler than per-zone radius searches
"""

import json
import os
import sys
import urllib.request
import ssl
import base64
import re
from datetime import datetime, timezone

# --- Configuration ---

# Bounding box covering Ryde, Auburn, Hornsby and surrounding suburbs
# Generous bounds to avoid missing stations between centroids
BOUNDS = {
    "lat_min": -33.92,   # South to Canley Heights / Bass Hill
    "lat_max": -33.65,   # North of Hornsby
    "lng_min": 150.91,   # West to Smithfield / Fairfield
    "lng_max": 151.26,   # East to Neutral Bay / Cammeray
}

API_BASE = "https://api.onegov.nsw.gov.au"
AUTH_URL = f"{API_BASE}/oauth/client_credential/accesstoken?grant_type=client_credentials"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "fuelcheck_stations.json")
FULL_OUTPUT_FILE = os.path.join(DATA_DIR, "fuelcheck_stations_full.json")
LOG_FILE = os.path.join(PROJECT_DIR, "logging.log")
ENV_FILE = os.path.join(PROJECT_DIR, ".env")
GOOGLE_META_FILE = os.path.join(DATA_DIR, "google_meta.json")
GOOGLE_STATIONS_FILE = os.path.join(DATA_DIR, "google_stations.json")


def load_env():
    """Read .env file and return dict of key=value pairs."""
    env = {}
    if not os.path.exists(ENV_FILE):
        print(f"ERROR: .env file not found at {ENV_FILE}")
        print("Create it with FUELCHECK_API_KEY and FUELCHECK_API_SECRET")
        sys.exit(1)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


def get_access_token(api_key, api_secret):
    """Authenticate with NSW API and return an access token."""
    credentials = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()

    req = urllib.request.Request(
        AUTH_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "User-Agent": "reFuel/1.0",
        },
    )

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read().decode())
        return data["access_token"]


def fetch_all_prices(token, api_key):
    """Fetch all fuel prices for all NSW stations in one call."""
    url = f"{API_BASE}/FuelPriceCheck/v1/fuel/prices"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "reFuel/1.0",
            "apikey": api_key,
            "transactionid": datetime.now().strftime("%Y%m%d%H%M%S"),
            "requesttimestamp": datetime.now(timezone.utc).strftime(
                "%d/%m/%Y %I:%M:%S %p"
            ),
        },
    )

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())


def in_bounds(lat, lng):
    """Check if a coordinate falls within the target bounding box."""
    return (
        BOUNDS["lat_min"] <= lat <= BOUNDS["lat_max"]
        and BOUNDS["lng_min"] <= lng <= BOUNDS["lng_max"]
    )


def normalize_suburb_name(value):
    """Normalize suburb names for cross-source comparisons."""
    value = re.sub(r"\s+", " ", (value or "").strip().lower())
    return value.replace("_", " ")


def looks_like_suburb_name(value):
    """Best-effort filter to avoid treating street labels as suburbs."""
    if not value:
        return False
    if any(ch.isdigit() for ch in value) or "," in value:
        return False
    street_suffixes = {
        "st", "street", "rd", "road", "ave", "avenue", "dr", "drive", "hwy",
        "highway", "pde", "parade", "pl", "place", "ct", "court", "way",
        "blvd", "boulevard", "cres", "crescent", "lane", "ln",
    }
    tokens = value.split()
    return not tokens or tokens[-1] not in street_suffixes


def extract_suburb_from_address(address):
    """Extract suburb from either FuelCheck or scraped Google address strings."""
    if not address or not address.strip():
        return ""

    compact = re.sub(r"\s+", " ", address.strip())
    match = re.search(r",\s*(.+?)\s+NSW(?:\s+\d{4})?$", compact, re.IGNORECASE)
    if match:
        return normalize_suburb_name(match.group(1))

    parts = [part.strip() for part in compact.split(",") if part.strip()]
    if len(parts) > 1:
        return normalize_suburb_name(parts[-1])
    return ""


def load_allowed_suburbs():
    """Load the set of already-scraped suburbs from existing Google data."""
    suburbs = set()

    if os.path.exists(GOOGLE_META_FILE):
        with open(GOOGLE_META_FILE) as f:
            meta = json.load(f)
        for zone in meta.get("zones_scraped", []):
            normalized = normalize_suburb_name(zone)
            if looks_like_suburb_name(normalized):
                suburbs.add(normalized)

    if os.path.exists(GOOGLE_STATIONS_FILE):
        with open(GOOGLE_STATIONS_FILE) as f:
            stations = json.load(f)
        for station in stations:
            suburb = extract_suburb_from_address(station.get("address", ""))
            if looks_like_suburb_name(suburb):
                suburbs.add(suburb)

    return suburbs


def log_action(message):
    """Append a log entry to logging.log."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)
    print(entry.strip())


def main():
    env = load_env()
    api_key = env.get("FUELCHECK_API_KEY", "")
    api_secret = env.get("FUELCHECK_API_SECRET", "")

    if not api_key or not api_secret or "your_" in api_key:
        print("ERROR: Set real API credentials in .env")
        print("Register free at: https://api.nsw.gov.au/Account/Register")
        sys.exit(1)

    print("Authenticating with NSW FuelCheck API...")
    token = get_access_token(api_key, api_secret)
    print("Authenticated successfully.")

    print("Fetching all NSW stations (bulk)...")
    result = fetch_all_prices(token, api_key)

    stations_raw = result.get("stations", [])
    prices_raw = result.get("prices", [])
    allowed_suburbs = load_allowed_suburbs()
    print(f"Allowed scraped suburbs: {len(allowed_suburbs)}")

    # Build price lookup by station code
    price_map = {}
    for p in prices_raw:
        sid = p.get("stationcode")
        if sid not in price_map:
            price_map[sid] = []
        price_map[sid].append({
            "fuel_type": p.get("fueltype"),
            "price": p.get("price"),
        })

    # Filter stations to bounding box first, then derive the site-safe scraped-suburb subset.
    in_bounds_stations = []
    filtered = []
    filtered_in_bounds = 0
    for s in stations_raw:
        loc = s.get("location", {})
        lat = loc.get("latitude")
        lng = loc.get("longitude")
        if lat is not None and lng is not None and in_bounds(lat, lng):
            filtered_in_bounds += 1
            sid = s.get("code")
            station_record = {
                "id": sid,
                "name": s.get("name", ""),
                "brand": s.get("brand", ""),
                "address": s.get("address", ""),
                "lat": lat,
                "lng": lng,
                "prices": price_map.get(sid, []),
                "source": "fuelcheck",
            }
            in_bounds_stations.append(station_record)

            suburb = extract_suburb_from_address(s.get("address", ""))
            if allowed_suburbs and suburb not in allowed_suburbs:
                continue
            filtered.append(station_record)

    print(f"Total NSW stations: {len(stations_raw)}")
    print(f"Stations in bounding box: {filtered_in_bounds}")
    print(f"Stations in scraped suburbs: {len(filtered)}")

    # Write filtered site output
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(filtered, f, indent=2)

    # Write full in-bounds dataset for local analysis/reference.
    with open(FULL_OUTPUT_FILE, "w") as f:
        json.dump(in_bounds_stations, f, indent=2)

    # Save timestamped full snapshot to history (gitignored)
    history_dir = os.path.join(DATA_DIR, "history")
    os.makedirs(history_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    history_file = os.path.join(history_dir, f"fuelcheck_full_{ts}.json")
    with open(history_file, "w") as f:
        json.dump(in_bounds_stations, f, indent=2)

    # Write metadata for freshness indicator
    meta = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_nsw": len(stations_raw),
        "in_bounds": filtered_in_bounds,
        "in_scraped_suburbs": len(filtered),
        "scraped_suburb_count": len(allowed_suburbs),
        "full_output_file": os.path.basename(FULL_OUTPUT_FILE),
        "history_file": os.path.basename(history_file),
    }
    with open(os.path.join(DATA_DIR, "fuelcheck_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    log_action(
        f"source=fuelcheck stations={len(filtered)} in_bounds={filtered_in_bounds} "
        f"scraped_suburbs={len(allowed_suburbs)} total_nsw={len(stations_raw)}"
    )
    print(f"\nWrote {len(filtered)} stations to {OUTPUT_FILE}")
    print(f"Wrote {len(in_bounds_stations)} full in-bounds stations to {FULL_OUTPUT_FILE}")
    print(f"Saved full history snapshot to {history_file}")


if __name__ == "__main__":
    main()
