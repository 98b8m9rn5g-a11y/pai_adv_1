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

ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=/work/simulation/bridge.yaml &
pids+=("$!")
gz sim -r -v 2 --render-engine ogre --gui-config /work/simulation/gui.config /work/simulation/lab.sdf &
pids+=("$!")
xterm -fa 'DejaVu Sans Mono' -fs 11 -geometry 125x12+0+650 \
  -T 'AI delivery log' -e bash /work/scripts/start-robot.sh &
pids+=("$!")
bash /work/scripts/layout-desktop.sh &
pids+=("$!")
set +e
# The layout helper exits normally; only monitor the three long-running services.
wait -n "${pids[0]}" "${pids[1]}" "${pids[2]}"
status=$?
exit "$status"
