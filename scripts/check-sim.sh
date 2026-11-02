#!/usr/bin/env bash
set -euo pipefail

echo "ROS distribution: $ROS_DISTRO"
ros2 pkg prefix ros_gz_bridge
gz sim --versions
echo 'Waiting for the simulation clock via the Gazebo-to-ROS bridge...'
timeout 25 ros2 topic echo /clock rosgraph_msgs/msg/Clock --once
echo 'PASS: ROS 2 received simulation time from Gazebo.'
