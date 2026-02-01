#!/usr/bin/env bash
set -euo pipefail

LABEL="com.ocmonitor.dashboard"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
UID_NUM="$(id -u)"

if [ ! -f "$PLIST" ]; then
  echo "Plist not found: $PLIST"
  exit 1
fi

launchctl bootout "gui/${UID_NUM}/${LABEL}" 2>/dev/null || true

echo "Service stopped."
