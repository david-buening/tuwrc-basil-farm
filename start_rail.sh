#!/bin/bash
#
# start_rail.sh
# =============
# Brings up the SO-101 WITH the prismatic X-rail (6 DOF) from a cold start.
#
# Differences from start.sh (the original 5-DOF setup):
#   * kills stale ROS/Gazebo processes first  -> a leftover publisher serves an
#     OLD robot description and the new rail joint never shows up
#   * runs colcon build                       -> Gazebo spawns the robot from
#     install/, so URDF edits are invisible without a rebuild
#   * verifies that the controllers really went active and that `rail_joint`
#     actually appears in /joint_states, instead of only printing status
#
# Usage:  ./start_rail.sh
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Everything inside the container needs ROS + the workspace overlay sourced.
SOURCE_ENV="source /opt/ros/humble/setup.bash && source /workspace/lerobot/install/setup.bash"

# Opens a new macOS Terminal window running one command inside the container.
# If macOS blocks the Apple Event (missing Automation permission), fall back to
# running the command detached inside the container so the stack still comes up.
run_in_terminal() {
    if ! osascript -e "tell application \"Terminal\" to do script \"docker exec -it lerobot_container /bin/bash -ic \\\"$1\\\"\"" >/dev/null 2>&1; then
        echo "      (no Terminal window - running in the background instead;"
        echo "       to get windows, allow Automation for your terminal app in"
        echo "       System Settings > Privacy & Security > Automation)"
        docker compose exec -d lerobot bash -c "export DISPLAY=:1 && $1" >/dev/null 2>&1
    fi
}

echo "=== Robot Arm Setup (with X-rail, 6 DOF) ==="
echo ""

# ---------------------------------------------------------------------------
# Step 1: Start Docker Desktop
# ---------------------------------------------------------------------------
echo "[1/8] Starting Docker Desktop..."
open -a "Docker Desktop"
echo "      Waiting until Docker is ready..."
until docker info &>/dev/null 2>&1; do
    sleep 2
done
echo "      Docker is ready."

# ---------------------------------------------------------------------------
# Step 2: Start the container
# ---------------------------------------------------------------------------
echo ""
echo "[2/8] Starting container..."
cd "$SCRIPT_DIR"
docker compose up -d
echo "      Container started."

# ---------------------------------------------------------------------------
# Step 3: Kill leftover processes from a previous session
#
# This matters: a surviving robot_state_publisher / joint_state_publisher keeps
# serving the OLD robot description, so the rail joint is missing from
# /joint_states even though the URDF is correct. Run as root because the old
# processes may not belong to the current user.
# ---------------------------------------------------------------------------
echo ""
echo "[3/8] Cleaning up stale ROS processes..."
# NOTE the [b]racket trick in every pattern: without it pkill also matches the
# command line of this very shell (which contains the patterns as text) and
# kills itself before reaching the later lines.
docker compose exec -T -u root lerobot bash -c '
    pkill -9 -f "[i]gn gazebo"      2>/dev/null
    pkill -9 -f "[r]viz2"           2>/dev/null
    pkill -9 -f "[m]ove_group"      2>/dev/null
    pkill -9 -f "[j]oint_state"     2>/dev/null
    pkill -9 -f "[r]obot_state"     2>/dev/null
    pkill -9 -f "[p]arameter_bridge" 2>/dev/null
    pkill -9 -f "[s]o101_"          2>/dev/null
    pkill -9 -f "[r]uby"            2>/dev/null
    exit 0
' >/dev/null 2>&1
sleep 2
echo "      Clean."

# ---------------------------------------------------------------------------
# Step 4: Build the workspace
#
# Gazebo spawns the robot from install/, NOT from src/. Without this step any
# change to the URDF / controller / MoveIt configs is silently ignored.
# ---------------------------------------------------------------------------
echo ""
echo "[4/8] Building workspace (URDF, controllers, MoveIt, GUI)..."
if docker compose exec -T lerobot bash -c "
    cd /workspace/lerobot &&
    source /opt/ros/humble/setup.bash &&
    colcon build --packages-select lerobot_description lerobot_controller lerobot_moveit lerobot_gui
" 2>&1 | tail -2; then
    echo "      Build finished."
else
    echo "      BUILD FAILED - fix the errors above before continuing."
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 5: Open the VNC desktop (Gazebo + RViz appear here)
# ---------------------------------------------------------------------------
echo ""
echo "[5/8] Opening the VNC desktop in the browser (password: ros)..."
open "http://localhost:6080/vnc.html"

# ---------------------------------------------------------------------------
# Step 6: Start Gazebo
#
# Must come first: Gazebo brings up the controller_manager via gz_ros2_control,
# which the controller spawners in the next step attach to.
# ---------------------------------------------------------------------------
echo ""
echo "[6/8] Starting Gazebo..."
run_in_terminal "$SOURCE_ENV && ros2 launch lerobot_description so101_gazebo.launch.py"
echo "      Waiting 25 seconds for Gazebo to load..."
sleep 25

# ---------------------------------------------------------------------------
# Step 7: Load the controllers, then verify they are really active
# ---------------------------------------------------------------------------
echo ""
echo "[7/8] Loading controllers..."
run_in_terminal "$SOURCE_ENV && ros2 launch lerobot_controller so101_controller.launch.py"
echo "      Waiting for controllers to activate..."

CONTROLLERS_OK=0
for _ in $(seq 1 12); do   # up to ~60 s
    sleep 5
    STATUS=$(docker compose exec -T lerobot bash -c \
        "$SOURCE_ENV && ros2 control list_controllers" 2>/dev/null)
    if echo "$STATUS" | grep -q "arm_controller.*active"; then
        CONTROLLERS_OK=1
        break
    fi
done

if [ "$CONTROLLERS_OK" -eq 1 ]; then
    echo "      Controllers are active:"
    echo "$STATUS" | sed 's/^/        /'
else
    echo "      WARNING: controllers did not become active."
    echo "      Common cause: the robot is stuck in the ground plane, which"
    echo "      collapses the physics rate and makes activation time out."
    echo "      Check the Gazebo terminal window for errors."
fi

# ---------------------------------------------------------------------------
# Step 8: Start MoveIt (provides /compute_ik for full 6-DOF pose targets)
# ---------------------------------------------------------------------------
echo ""
echo "[8/8] Starting MoveIt and the web GUI..."
run_in_terminal "$SOURCE_ENV && ros2 launch lerobot_moveit so101_moveit.launch.py"
echo "      Waiting for the IK service..."

IK_OK=0
for _ in $(seq 1 8); do    # up to ~40 s
    sleep 5
    if docker compose exec -T lerobot bash -c \
        "$SOURCE_ENV && ros2 service list" 2>/dev/null | grep -q compute_ik; then
        IK_OK=1
        break
    fi
done
[ "$IK_OK" -eq 1 ] && echo "      /compute_ik is available." \
                   || echo "      WARNING: /compute_ik not found - pose targets will fail."

# Web GUI on port 3000
run_in_terminal "$SOURCE_ENV && ros2 run lerobot_gui joint_state_gui"
sleep 3
open "http://localhost:3000"

# ---------------------------------------------------------------------------
# Final check: is the rail joint actually being published?
# ---------------------------------------------------------------------------
echo ""
echo "Verifying the rail joint..."
JOINTS=$(docker compose exec -T lerobot bash -c \
    "$SOURCE_ENV && timeout 5 ros2 topic echo /joint_states --once" 2>/dev/null)
if echo "$JOINTS" | grep -q "rail_joint"; then
    echo "  OK - rail_joint is present in /joint_states (6 DOF active)."
else
    echo "  WARNING: rail_joint missing from /joint_states."
    echo "  Check that the build succeeded and no old processes survived."
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "  VNC Desktop : http://localhost:6080/vnc.html  (password: ros)"
echo "  Web-GUI     : http://localhost:3000   (rail_joint in m, 6-DOF pose)"
echo ""
echo "  Run the waypoint sequence:"
echo "    docker exec -it lerobot_container /bin/bash -ic \\"
echo "      \"$SOURCE_ENV && python3 /workspace/waypoint_runner.py\""
echo ""
echo "  Shut everything down again:"
echo "    docker compose stop"
