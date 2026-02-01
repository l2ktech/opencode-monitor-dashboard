#!/usr/bin/env bash
set -euo pipefail

LABEL="com.ocmonitor.dashboard"
UID_NUM="$(id -u)"

if launchctl print "gui/${UID_NUM}/${LABEL}" >/dev/null 2>&1; then
  echo "Service is running."
else
  echo "Service is NOT running."
fi
