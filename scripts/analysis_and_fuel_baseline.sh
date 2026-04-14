#!/bin/bash
# Compute station outage availability from FuelCheck history
#
# This script runs two Python pipelines in sequence:
# 1. build_fuelcheck_history_dataset.py — builds historical fuel type records
# 2. outtage-tracking.py — computes availability ratios by comparing current fuels to historical "usual" fuels
#
# Output files:
# - data/clean/fuelcheck_history_dataset.csv (fuel_types_ever, ever_had_* columns)
# - data/clean/fuelcheck_station_outage_status.csv (unavailable_ratio_pct, completely_out_of_all_usual)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Outage Tracking Pipeline ==="
echo "Project dir: $PROJECT_DIR"
echo ""

# Step 1: Build history dataset
echo "[1/2] Building FuelCheck history dataset..."
python3 "$SCRIPT_DIR/build_fuelcheck_history_dataset.py"
if [ $? -eq 0 ]; then
  echo "✓ History dataset created: data/clean/fuelcheck_history_dataset.csv"
else
  echo "✗ Failed to build history dataset"
  exit 1
fi
echo ""

# Step 2: Compute outage tracking
echo "[2/2] Computing outage availability tracking..."
python3 "$SCRIPT_DIR/outtage-tracking.py"
if [ $? -eq 0 ]; then
  echo "✓ Outage tracking computed: data/clean/fuelcheck_station_outage_status.csv"
else
  echo "✗ Failed to compute outage tracking"
  exit 1
fi
echo ""

echo "=== Pipeline Complete ==="
echo "Output files:"
ls -lh "$PROJECT_DIR/data/clean/fuelcheck_history_dataset.csv"
ls -lh "$PROJECT_DIR/data/clean/fuelcheck_station_outage_status.csv"
