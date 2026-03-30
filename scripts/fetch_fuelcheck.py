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
from datetime import datetime, timezone

# --- Configuration ---

# Bounding box covering Ryde, Auburn, Hornsby and surrounding suburbs
# Generous bounds to avoid missing stations between centroids
BOUNDS = {
    "lat_min": -33.90,   # South of Auburn
    "lat_max": -33.65,   # North of Hornsby
    "lng_min": 150.95,   # West of Auburn
    "lng_max": 151.25,   # East to Neutral Bay / Cammeray
}

API_BASE = "https://api.onegov.nsw.gov.au"
AUTH_URL = f"{API_BASE}/oauth/client_credential/accesstoken?grant_type=client_credentials"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "fuelcheck_stations.json")
LOG_FILE = os.path.join(PROJECT_DIR, "logging.log")
ENV_FILE = os.path.join(PROJECT_DIR, ".env")


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

    # Filter stations to bounding box
    filtered = []
    for s in stations_raw:
        loc = s.get("location", {})
        lat = loc.get("latitude")
        lng = loc.get("longitude")
        if lat is not None and lng is not None and in_bounds(lat, lng):
            sid = s.get("code")
            filtered.append({
                "id": sid,
                "name": s.get("name", ""),
                "brand": s.get("brand", ""),
                "address": s.get("address", ""),
                "lat": lat,
                "lng": lng,
                "prices": price_map.get(sid, []),
                "source": "fuelcheck",
            })

    print(f"Total NSW stations: {len(stations_raw)}")
    print(f"Stations in bounding box: {len(filtered)}")

    # Write output
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(filtered, f, indent=2)

    # Write metadata for freshness indicator
    meta = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_nsw": len(stations_raw),
        "in_bounds": len(filtered),
    }
    with open(os.path.join(DATA_DIR, "fuelcheck_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    log_action(f"source=fuelcheck stations={len(filtered)} total_nsw={len(stations_raw)}")
    print(f"\nWrote {len(filtered)} stations to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
