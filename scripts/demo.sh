#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose exec -T sim /ros_entrypoint.sh bash -c \
  'source /work/ros2_ws/install/setup.bash && exec ros2 run pai_delivery demo'
