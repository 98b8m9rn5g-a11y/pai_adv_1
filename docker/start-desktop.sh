#!/usr/bin/env bash
set -euo pipefail

pids=()
cleanup() {
  trap - EXIT INT TERM
  if ((${#pids[@]})); then
    kill "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

Xvfb "$DISPLAY" -screen 0 1280x900x24 -nolisten tcp &
pids+=("$!")
display_ready=false
for attempt in {1..100}; do
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    display_ready=true
    break
  fi
  sleep 0.1
done
if [[ "$display_ready" != true ]]; then
  echo 'Virtual display did not become ready.' >&2
  exit 1
fi

fluxbox &
pids+=("$!")
x11vnc -display "$DISPLAY" -rfbport 5900 -localhost -forever -shared -nopw &
pids+=("$!")
websockify --web=/usr/share/novnc 6080 localhost:5900 &
pids+=("$!")
bash /work/scripts/run-sim.sh &
pids+=("$!")

echo 'Simulation desktop: http://localhost:6080/vnc.html?autoconnect=1&resize=scale'
set +e
wait -n "${pids[@]}"
status=$?
exit "$status"
