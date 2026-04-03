#!/usr/bin/env python3
"""Recover committed FuelCheck datasets from git history into local history files."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = "data/fuelcheck_stations.json"
HISTORY_DIR = os.path.join(PROJECT_DIR, "data", "history")
OUTPUT_PREFIX = "fuelcheck_full_"
MANIFEST_FILE = os.path.join(HISTORY_DIR, "fuelcheck_git_recovered_manifest.json")


def run_git(*args: str) -> str:
    """Run a git command in the project and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def list_fuelcheck_commits() -> list[dict[str, str]]:
    """Return commits that touched the FuelCheck dataset, oldest first."""
    output = run_git("log", "--follow", "--format=%H\t%cI\t%s", "--", DATA_FILE)
    commits: list[dict[str, str]] = []
    for line in output.splitlines():
        commit_hash, commit_date, subject = line.split("\t", 2)
        commits.append(
            {
                "commit_hash": commit_hash,
                "commit_date": commit_date,
                "commit_subject": subject,
            }
        )
    commits.reverse()
    return commits


def load_dataset_at_commit(commit_hash: str) -> list[dict]:
    """Load the FuelCheck dataset file from a specific commit."""
    raw = run_git("show", f"{commit_hash}:{DATA_FILE}")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"{commit_hash}:{DATA_FILE} did not contain a list")
    return data


def output_name_for_commit(commit_date: str) -> str:
    """Build a history filename using the commit timestamp."""
    dt = datetime.fromisoformat(commit_date)
    timestamp = dt.strftime("%Y-%m-%dT%H%M%S")
    return f"{OUTPUT_PREFIX}{timestamp}.json"


def recover_history() -> list[dict[str, object]]:
    """Recover all git-era FuelCheck datasets into local history files."""
    commits = list_fuelcheck_commits()
    if not commits:
        raise FileNotFoundError(f"No historical commits found for {DATA_FILE}")

    os.makedirs(HISTORY_DIR, exist_ok=True)
    manifest: list[dict[str, object]] = []

    for entry in commits:
        commit_hash = entry["commit_hash"]
        commit_date = entry["commit_date"]
        rows = load_dataset_at_commit(commit_hash)
        filename = output_name_for_commit(commit_date)
        output_path = os.path.join(HISTORY_DIR, filename)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(rows, handle, indent=2)

        manifest.append(
            {
                **entry,
                "output_file": filename,
                "row_count": len(rows),
                "pushed_at": commit_date,
            }
        )

    with open(MANIFEST_FILE, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    return manifest


def main() -> int:
    try:
        manifest = recover_history()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Recovered {len(manifest)} FuelCheck snapshots to {HISTORY_DIR}")
    for entry in manifest:
        print(f"{entry['commit_date']}  {entry['commit_hash'][:7]}  {entry['output_file']}  rows={entry['row_count']}")
    print(f"Manifest: {MANIFEST_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
