#!/bin/bash
# Shell-only path: runs the deterministic pipeline + commits. No Claude, no gap enrichment.
# Used by launchd com.refuel.datarefresh at midnight.

set -e
export PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

"$SCRIPT_DIR/refresh_data.sh"

echo ""
echo "[$(date)] Shell-only commit step..."
/usr/bin/git add data/
if /usr/bin/git diff --cached --quiet; then
    echo "No data changes to commit."
else
    NOW=$(date '+%Y-%m-%d %H:%M')
    /usr/bin/git commit -m "Shell refresh — FuelCheck data ($NOW)"
    /usr/bin/git push origin dev
    /usr/bin/git push origin dev:main
    echo "Committed and pushed (shell path)."
fi
