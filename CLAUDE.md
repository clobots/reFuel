# reFuel Project — Claude Instructions

Sydney fuel gap/availability map. Scrapes Google Maps + NSW FuelCheck API, matches stations, tracks outages, renders a Leaflet map at `index.html`.

## Data pipeline (order matters)

Scripts live in `scripts/`. Canonical end-to-end runner is `scripts/refresh_data.sh`, which executes:

1. **`fetch_fuelcheck.py`** — pulls fresh FuelCheck API snapshot.
2. **`run_all.py --no-commit`** — clean google + fuelcheck, merge → `matched_stations.csv`, write history + outages CSVs. Validates shape of 5 CSVs.
3. **`analysis_and_fuel_baseline.sh`** — runs `build_fuelcheck_history_dataset.py` then `outtage-tracking.py`. Produces `data/clean/fuelcheck_station_outage_status.csv` — **the file that drives the frontpage summary cards**.
4. **`gap_detector.py`** — diffs `matched_stations.csv` (`gap_google_only` rows) against `data/manual_gap_fuel_info.json`; writes `data/pending_gaps.json` with stations needing manual Chrome enrichment.

`refresh_data.sh` does NOT commit. The wrapping `/refuel-pipeline` skill commits once at the end, after optional gap enrichment, so every data change lands in a single aligned commit.

## Scheduled refresh (two launchd jobs)

Two separate daily runs, one shell-only, one full-Claude.

**Shell-only, midnight AEST — `com.refuel.datarefresh`**
- Plist: `~/Library/LaunchAgents/com.refuel.datarefresh.plist`
- Runs `scripts/refresh_data_commit.sh` → wraps `refresh_data.sh` + git commit+push.
- No Claude, no Chrome, no gap enrichment. Fast, cheap, keeps data fresh overnight.
- Fires: **00:00 daily**.

**Claude pipeline, 8 AM AEST — `com.chloe.fuel-refresh`**
- Plist: `~/Library/LaunchAgents/com.chloe.fuel-refresh.plist`
- Runs `scripts/launch_fuel_refresh.sh` → writes a throwaway `.command` file → `open -a Terminal` opens it → Terminal runs `cd ~/Documents/fuel && claude '/refuel-pipeline'`.
- Interactive Claude session (not headless) — Chrome MCP + AppleScript both available for the gap-enrichment step.
- Terminal is intentionally visible — Chloe glances at progress.
- Fires: **08:00 daily**.

Why `.command` + `open` instead of `osascript tell Terminal`: the AppleScript path is blocked by macOS TCC automation permission when invoked by launchd. LaunchServices via `open` bypasses that wall.

## Manual trigger

From any Claude Code session with `~/Documents/fuel` as cwd:

```
/refuel-pipeline
```

Skill definition: `.claude/skills/refuel-pipeline/SKILL.md`.

## Frontpage alignment invariant

The four summary cards in `index.html` (`available-count`, `partial-count`, `unavailable-count`, `unknown-count`) must sum to the total row count of `matched_stations.csv`:

- **available** = matched rows with zero unavailable usual fuels + manual gap entries with `status: operational`
- **partial** = matched rows with 1+ unavailable but not `completely_out_of_all_usual`
- **out/closed** = matched rows with `completely_out_of_all_usual == true` + manual entries with `status: temporarily_closed`
- **unknown** = `gap_google_only` rows NOT in `manual_gap_fuel_info.json` (= `pending_gaps.json.pending_count`)

The `/refuel-pipeline` skill verifies this before every commit and refuses to commit if it breaks.

## Key files

| File | Purpose |
|------|---------|
| `data/clean/matched_stations.csv` | Google-to-FuelCheck merged result; `match_status` drives marker coloring |
| `data/clean/fuelcheck_station_outage_status.csv` | Per-station outage %; drives frontpage card counts |
| `data/manual_gap_fuel_info.json` | Manually curated fuel info for `gap_google_only` stations |
| `data/pending_gaps.json` | Gap stations awaiting manual enrichment |
| `index.html` | Leaflet map + summary UI |
| `logging.log` | Timestamps of each launchd-triggered refresh |

## Enrichment skill

Manual gap lookups go through the user-level **`reFuel-check-gaps`** skill (Chrome + aggregator reading). `/refuel-pipeline` invokes it for pending gaps only. Read that skill before editing enrichment logic — it documents which aggregators to trust and which to ignore.

## Common pitfalls

- **Don't regex aggregator pages.** Claude must read + judge fuel types from context. The skill warns specifically about this — it previously hallucinated E10 for Medco Carlingford.
- **Don't overwrite `manual_gap_fuel_info.json`.** Append new entries; preserve old `found_date`.
- **Don't commit mid-pipeline.** `run_all.py` supports `--no-commit` for this reason. Only `/refuel-pipeline` should commit.
- **lat/lng are strings in the JSON lookup.** Copy verbatim from CSV; don't re-parse as floats.
