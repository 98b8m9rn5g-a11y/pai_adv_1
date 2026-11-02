#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
source /work/ros2_ws/install/setup.bash
bash /work/scripts/check-sim.sh
ros2 run pai_delivery evaluate > /work/output/intent-evaluation.json
ros2 run pai_delivery demo
