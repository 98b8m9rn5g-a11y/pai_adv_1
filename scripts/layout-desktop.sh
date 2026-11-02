#!/usr/bin/env bash
set -euo pipefail
for attempt in {1..60}; do
  if wmctrl -l | grep -q 'Gazebo'; then
    sleep 5
    wmctrl -r 'Gazebo' -b remove,maximized_vert,maximized_horz
    wmctrl -r 'Gazebo' -e 0,0,0,1280,620
    wmctrl -r 'AI delivery log' -e 0,0,650,1280,220
    exit 0
  fi
  sleep 1
done
