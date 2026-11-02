#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
cd /work/ros2_ws
colcon build --symlink-install --packages-select pai_delivery
source install/setup.bash
export RCUTILS_CONSOLE_OUTPUT_FORMAT='{message}'
exec ros2 run pai_delivery delivery
