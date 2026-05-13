#!/bin/bash
set -e
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1 2>/dev/null || true
vncserver :1 -geometry 1920x1080 -depth 24 -localhost no
websockify --web /usr/share/novnc/ 6080 localhost:5901 &
export DISPLAY=:1
echo "READY: http://localhost:6080/vnc.html — password: ros"
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash
tail -f /dev/null
