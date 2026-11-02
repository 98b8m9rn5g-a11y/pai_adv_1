#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
source /work/ros2_ws/install/setup.bash
mkdir -p /work/output
# Let the GUI finish applying its recording layout after a container restart.
sleep 8
ffmpeg -hide_banner -loglevel warning -y \
  -f x11grab -video_size 1280x900 -framerate 15 -i :1.0 \
  -loop 1 -i /work/simulation/video-banner.png \
  -t 90 -filter_complex '[0:v][1:v]overlay=0:0:shortest=1' \
  -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -movflags +faststart \
  /work/output/pai-delivery-demo.mp4 > /work/output/recording.log 2>&1 &
recorder_pid=$!
trap 'kill "$recorder_pid" 2>/dev/null || true' EXIT
sleep 4
kill -0 "$recorder_pid"
ros2 run pai_delivery demo --ros-args -p pause_seconds:=12.0
wait "$recorder_pid"
trap - EXIT
ffprobe -v error -show_entries format=duration -of default=nw=1 /work/output/pai-delivery-demo.mp4
