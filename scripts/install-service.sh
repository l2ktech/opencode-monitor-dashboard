#!/usr/bin/env bash
set -euo pipefail

echo "Installing OCMonitor Dashboard Service (LaunchAgent)..."

# Resolve project root from this script location
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.ocmonitor.dashboard"
DEST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$DEST_DIR/${LABEL}.plist"

PYTHON_BIN="$(command -v python3)"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$DEST_DIR" "$LOG_DIR"

# Generate plist with portable paths
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_BIN}</string>
    <string>${PROJECT_DIR}/app.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/stderr.log</string>
  <key>WorkingDirectory</key>
  <string>${PROJECT_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>OPENCODE_DATA_DIR</key>
    <string>${OPENCODE_DATA_DIR:-$HOME/.local/share/opencode/storage/message}</string>
    <key>DASHBOARD_HOST</key>
    <string>${DASHBOARD_HOST:-0.0.0.0}</string>
    <key>DASHBOARD_PORT</key>
    <string>${DASHBOARD_PORT:-38002}</string>
    <key>AUTO_REFRESH_INTERVAL</key>
    <string>${AUTO_REFRESH_INTERVAL:-5}</string>
  </dict>
</dict>
</plist>
EOF

# Reload service
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/${LABEL}" 2>/dev/null || true

echo "Service installed: $PLIST_PATH"
echo "Dashboard: http://localhost:${DASHBOARD_PORT:-38002}"
echo "Logs: $LOG_DIR"
echo "Manage: ./scripts/start.sh | ./scripts/stop.sh | ./scripts/restart.sh | ./scripts/status.sh"
