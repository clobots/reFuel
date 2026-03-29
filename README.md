# reFuel — Fuel Station Gap Analysis

Compares petrol stations from Google Maps against the NSW FuelCheck API to find coverage gaps in the Ryde / inner-west Sydney area.

## Live App

**[Open reFuel](https://gist.github.com/clobots/56f0248fcb95852896c62ee9b88ae457)** (private gist — download the HTML and open locally, or use a raw gist viewer)

## What It Does

- Maps all petrol stations from two sources (Google Maps scrape + FuelCheck API)
- Matches stations within 200m using Haversine distance
- Highlights gaps: stations in one source but not the other
- Live price refresh via the NSW FuelCheck API (browser-based, no server needed)
- Filters by fuel type (E10, U91, U95, U98, Diesel, LPG, AdBlue)

## Data Pipeline

```
scripts/fetch_fuelcheck.py   # Fetch stations + prices from FuelCheck API
scripts/clean_google.py      # Normalise Google Maps scrape data
scripts/clean_fuelcheck.py   # Normalise FuelCheck data, filter EV-only stations
scripts/merge_matched.py     # Match stations across sources (200m threshold)
scripts/run_all.py           # Run the full pipeline
```

## Local Development

```bash
python3 scripts/serve.py     # Starts dev server at http://localhost:8000
```

## Data Sources

- **Google Maps** — scraped via browser automation (194 stations across 30 zones)
- **NSW FuelCheck API** — `api.onegov.nsw.gov.au` (OAuth client credentials flow)
