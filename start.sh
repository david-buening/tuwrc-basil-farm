#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Robot Arm Setup ==="
echo ""

# Step 1: Docker Desktop starten
echo "[1/7] Docker Desktop starten..."
open -a "Docker Desktop"
echo "      Warte bis Docker bereit ist..."
until docker info &>/dev/null 2>&1; do
    sleep 2
done
echo "      Docker ist bereit."

# Step 2: Container starten
echo ""
echo "[2/7] Container starten..."
cd "$SCRIPT_DIR"
docker compose up -d
echo "      Container gestartet."

# Step 3: VNC im Browser öffnen
echo ""
echo "[3/7] VNC-Desktop im Browser öffnen (Passwort: ros)..."
open "http://localhost:6080/vnc.html"

# Step 4: Gazebo in neuem Terminal starten
echo ""
echo "[4/7] Gazebo starten..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 launch lerobot_description so101_gazebo.launch.py\""'
echo "      Warte 20 Sekunden bis Gazebo geladen ist..."
sleep 20

# Step 5: Controller in neuem Terminal laden
echo ""
echo "[5/7] Controller laden..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 launch lerobot_controller so101_controller.launch.py\""'
echo "      Warte 5 Sekunden..."
sleep 5

echo "      Controller-Status:"
docker exec lerobot_container /bin/bash -ic "ros2 control list_controllers" 2>/dev/null \
    || echo "      (Controller noch nicht verfügbar — kurz warten und manuell prüfen)"

# Step 6: MoveIt in neuem Terminal starten
echo ""
echo "[6/7] MoveIt starten..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 launch lerobot_moveit so101_moveit.launch.py\""'
echo "      Warte 8 Sekunden bis MoveIt und /compute_ik bereit sind..."
sleep 8

# Step 7: Web-GUI in neuem Terminal starten
echo ""
echo "[7/7] Web-GUI starten..."
osascript -e 'tell application "Terminal" to do script "docker exec -it lerobot_container /bin/bash -ic \"ros2 run lerobot_gui joint_state_gui\""'
sleep 2
open "http://localhost:3000"

echo ""
echo "=== Setup abgeschlossen! ==="
echo ""
echo "  VNC Desktop : http://localhost:6080/vnc.html  (Passwort: ros)"
echo "  Web-GUI     : http://localhost:3000"
echo "  MoveIt      : läuft im separaten Terminal"
