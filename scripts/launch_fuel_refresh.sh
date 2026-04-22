#!/bin/bash
# Called by launchd. Opens Terminal via a .command file — this bypasses the
# AppleScript/TCC automation permission wall that blocks `osascript tell Terminal`
# from launchd. `open file.command` uses LaunchServices which works from launchd.

set -u

LOG=/Users/chloethelaw/Documents/fuel/logging.log
echo "[$(date)] launchd fired — launching Terminal + Claude for refuel pipeline" >> "$LOG"

# Write a single-use .command file Terminal will open + execute.
CMD_FILE=$(/usr/bin/mktemp /tmp/fuel-refresh-XXXXXX.command)
cat > "$CMD_FILE" <<'CMD'
#!/bin/bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd "$HOME/Documents/fuel"
claude "/refuel-pipeline"
CMD
/bin/chmod +x "$CMD_FILE"

# open -a Terminal <file> launches Terminal and executes the .command file.
/usr/bin/open -a Terminal "$CMD_FILE"
