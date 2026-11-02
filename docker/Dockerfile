FROM ros:jazzy-ros-base-noble

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    python3-colcon-common-extensions python3-sklearn \
    xvfb x11vnc x11-utils fluxbox xterm novnc websockify wmctrl \
    libgl1-mesa-dri mesa-utils fonts-noto-cjk curl \
    && rm -rf /var/lib/apt/lists/*

# Separate layer so adding recording support can reuse the Gazebo installation.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY docker/start-desktop.sh /opt/pai/start-desktop.sh
RUN chmod +x /opt/pai/start-desktop.sh

EXPOSE 6080
CMD ["/opt/pai/start-desktop.sh"]
