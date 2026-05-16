#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Robot Arm Setup ==="
echo ""

# Step 1: Start Docker Desktop
echo "[1/7] Starting Docker Desktop..."
open -a "Docker Desktop"
echo "      Waiting until Docker is ready..."
until docker info &>/dev/null 2>&1; do
    sleep 2
done
echo "      Docker is ready."

# Step 2: Start the container
echo ""
echo "[2/7] Starting container..."
cd "$SCRIPT_DIR"
docker compose up -d
echo "      Container started."

# Step 3: Open VNC in the browser
echo ""
echo "[3/7] Opening the VNC desktop in the browser (password: ros)..."
open "http://localhost:6080/vnc.html"

# Step 4: Start Gazebo in a new terminal
echo ""
echo "[4/7] Starting Gazebo..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 launch lerobot_description so101_gazebo.launch.py\""'
echo "      Waiting 20 seconds for Gazebo to load..."
sleep 20

# Step 5: Load controllers in a new terminal
echo ""
echo "[5/7] Loading controllers..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 launch lerobot_controller so101_controller.launch.py\""'
echo "      Waiting 5 seconds..."
sleep 5

echo "      Controller status:"
docker exec lerobot_container /bin/bash -ic "ros2 control list_controllers" 2>/dev/null \
    || echo "      (Controllers are not available yet - wait briefly and check manually)"

# Step 6: Start MoveIt in a new terminal
echo ""
echo "[6/7] Starting MoveIt..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 launch lerobot_moveit so101_moveit.launch.py\""'
echo "      Waiting 8 seconds until MoveIt and /compute_ik are ready..."
sleep 8

# Step 7: Start the web GUI in a new terminal
echo ""
echo "[7/7] Starting web GUI..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 run lerobot_gui joint_state_gui\""'
sleep 2
open "http://localhost:3000"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "  VNC Desktop : http://localhost:6080/vnc.html  (password: ros)"
echo "  Web-GUI     : http://localhost:3000"
echo "  MoveIt      : running in a separate terminal"
