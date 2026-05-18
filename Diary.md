# May 2 Status

RViz could be opened in the XFCE window.

Steps:
```bash
docker compose up -d
```

Then open this in the browser:
```text
http://localhost:6080/vnc.html
Password: ros
```

Then run:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_description so101_display.launch.py"
```

Next task: continue improving the 3D robot view.

# May 3 Status

RViz works with the correct robot model.
For this, select `Global Options` in the top-left area and set `Fixed Frame` to `world`.

Gazebo works now as well:
- Missing Gazebo and ros2_control packages were added to the Dockerfile.
- `ros_gz_sim`, `ros_gz_bridge`, `gz_ros2_control`, Controller Manager, and Joint Trajectory Controller are available.
- The SO101 can be spawned in Gazebo.
- Controllers can be loaded:
  - `joint_state_broadcaster`
  - `arm_controller`
  - `gripper_controller`
- A test trajectory sent to the arm works.

Important:
- Always run ROS commands without `sudo`.
- In every new container terminal, source the setup files first:
```bash
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash
```

If the container is only stopped and started again, this is usually enough:
```bash
docker compose up -d
```

If the container was deleted or you want to make sure it starts from the new Dockerfile:
```bash
docker compose down
docker compose build
docker compose up -d
```

Then open noVNC in the browser:
```text
http://localhost:6080/vnc.html
Password: ros
```

Start Gazebo:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_description so101_gazebo.launch.py"
```

Load the controllers in a second terminal:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_controller so101_controller.launch.py"
```

Check controller status:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 control list_controllers"
```

Expected output:
```text
joint_state_broadcaster  active
arm_controller           active
gripper_controller       active
```

Send a test trajectory to the arm:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \"{joint_names: ['1', '2', '3', '4', '5'], points: [{positions: [0.2, -0.4, 0.4, 0.2, 0.0], time_from_start: {sec: 2, nanosec: 0}}]}\""
```

Gripper test:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \"{joint_names: ['6'], points: [{positions: [0.5], time_from_start: {sec: 1, nanosec: 0}}]}\""
```

Move the arm back to neutral:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \"{joint_names: ['1', '2', '3', '4', '5'], points: [{positions: [0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 2, nanosec: 0}}]}\""
```

# May 6 Status

MoveIt and the first web GUI were added.

Changed:
- `Dockerfile`: added `ros-humble-moveit` so MoveIt is installed after a fresh Docker build.
- `docker-compose.yml`: added port `3000:3000` for the web GUI.
- `lerobot/src/lerobot_moveit/package.xml`: fixed the dependency:
  - wrong: `moveit_config_utils`
  - correct: `moveit_configs_utils`
- New package `lerobot/src/lerobot_gui` was created.
  - It starts a ROS 2 node.
  - It subscribes to `/joint_states`.
  - It displays the current joint states in the browser.

After a clean rebuild:
```bash
docker compose up -d --build --force-recreate
```

noVNC / Gazebo / RViz desktop:
```text
http://localhost:6080/vnc.html
Password: ros
```

Web GUI:
```text
http://localhost:3000
```

Recommended order after starting the container:

1. Start Gazebo:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_description so101_gazebo.launch.py"
```

2. Start or load the controllers:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_controller so101_controller.launch.py"
```

3. Check whether the controllers are active:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 control list_controllers"
```

Expected:
```text
joint_state_broadcaster  active
arm_controller           active
gripper_controller       active
```

4. Check whether joint states are being published:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic echo --once /joint_states"
```

5. Start the joint-state web GUI:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 run lerobot_gui joint_state_gui"
```

If port 3000 is already in use:
```bash
docker exec -it lerobot_container /bin/bash -lc "pkill -f joint_state_gui"
```

Then restart the GUI. Alternatively, use a different port inside the container:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 run lerobot_gui joint_state_gui -- --port 3000"
```

Important: In the browser on the Mac, port 3000 is reachable only if `docker-compose.yml` maps the port and the container was recreated after that change.

6. Start MoveIt:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_moveit so101_moveit.launch.py"
```

Use MoveIt in RViz:
- In the MotionPlanning panel:
  - `Planning Group`: `arm`
  - `Start State`: `current`
  - `Goal State`: `random valid`
  - then click `Plan & Execute`
- `random valid` is better than only `random`, because MoveIt then chooses a valid state within limits and collision rules.

If MoveIt reports this during execution:
```text
Invalid Trajectory: start point deviates from current robot state more than 0.01
```

Then the planned start state does not match the current robot state. Usually this helps:
- Set `Start State` to `current`.
- Click `Plan & Execute` directly instead of waiting for a long time between planning and execution.
- Check that `/joint_states` are current.

Note:
- Without Gazebo/controllers, or without `joint_state_broadcaster`, the web GUI does not receive `/joint_states`.
- MoveIt itself does not create joint states. It plans motions and sends trajectories to the controllers.

# May 6 Addendum: Automatic Sourcing

The Dockerfile was updated so interactive Bash shells for `rosuser` source these files automatically:
```bash
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash
```

After a new build, you can enter the container:
```bash
docker exec -it lerobot_container /bin/bash
```

Then you can run ROS commands directly:
```bash
ros2 topic echo --once /joint_states
ros2 control list_controllers
ros2 launch lerobot_description so101_gazebo.launch.py
```

Important: For one-line commands from outside the container using `docker exec ... /bin/bash -lc "..."`, explicit sourcing is still the most robust option because that is not the same as using an interactive shell.

# May 13 Status

The web GUI was expanded significantly. The previous joint-space state is now documented here as well:

- The GUI runs at `http://localhost:3000`.
- It displays the current `/joint_states` live.
- For all joints `1` through `6`, there are target fields in degrees.
- Buttons:
  - `Fill current`: copies the current robot position into the target fields.
  - `Reset to 0`: sets all targets to 0.
  - `Send`: sends a joint trajectory to `arm_controller` and `gripper_controller`.

The end-effector display was added as well:

- The GUI reads the transform `base -> gripper` via TF.
- It displays:
  - `X`, `Y`, `Z` in meters.
  - `Roll`, `Pitch`, `Yaw` in degrees.
  - Roll is rotation around X, Pitch around Y, and Yaw around Z.
- Because the arm has only 5 DOF, Roll/Pitch/Yaw are currently displayed only and are not used as targets.
- For the end effector, only `X/Y/Z` are editable for now.
- When `X/Y/Z` are sent, the GUI uses MoveIt through `/compute_ik`, computes suitable joint angles, and then sends them as a trajectory to the arm.
- In `lerobot/src/lerobot_moveit/config/kinematics.yaml`, `position_only_ik: True` was set so MoveIt only needs to reach the position and does not fail on a full 6D pose.

Important insight:

- A full end-effector pose has 6 degrees of freedom: `x/y/z/roll/pitch/yaw`.
- The SO101 arm has only 5 DOF for arm movement.
- Therefore, not every combination of position and orientation can be reached.
- For the current state, the best workflow is:
  1. Click `Fill current`.
  2. Make small changes to `X/Y/Z`.
  3. Click `Send`.

Startup was simplified as well:

- `start.sh` now starts Docker, Gazebo, controllers, MoveIt, and the web GUI.
- Because of this, end-effector position control should work directly after running `./start.sh`.
- `START.md` was updated accordingly.

# May 17 Status — Real Hardware Driver

## What was added

The missing ros2_control hardware driver for the real SO-101 arm was implemented.
Until now, the stack only ran in Gazebo simulation. The Gazebo simulation continues to work unchanged.

### New package: `lerobot/src/lerobot_hardware`

A new ROS 2 package `lerobot_hardware` was created. It contains a `ros2_control` hardware interface (`SystemInterface`) that communicates directly with the Feetech STS3215 servos over USB serial using the SCS binary protocol.

What it does:
- Opens the USB serial port (default `/dev/ttyUSB0`) at 1 Mbaud.
- On activation: pings all 6 servos and reads their current positions so the arm does not jump.
- `read()`: reads the current position of each servo (register `0x38`, 2 bytes, little-endian), converts steps → radians.
- `write()`: converts radians → steps, writes the goal position to each servo (register `0x2A`).
- Step encoding: 4096 steps per revolution, center (0 rad) = step 2048.

Files created:
- `include/lerobot_hardware/so101_hardware_interface.hpp`
- `src/so101_hardware_interface.cpp`
- `CMakeLists.txt`, `package.xml`, `lerobot_hardware.xml`

### Modified files

**`lerobot_description/urdf/so101_ros2_control.xacro`**

Added a `is_sim` xacro argument (default `true`). Depending on the value, either the Gazebo plugin or the real hardware plugin is loaded:
```xml
<xacro:if value="$(arg is_sim)">
    <plugin>gz_ros2_control/GazeboSimSystem</plugin>
</xacro:if>
<xacro:unless value="$(arg is_sim)">
    <plugin>lerobot_hardware/SO101HardwareInterface</plugin>
    <param name="serial_port">/dev/ttyUSB0</param>
    <param name="baud_rate">1000000</param>
</xacro:unless>
```

**`lerobot_description/urdf/so101.urdf.xacro`**

Added `<xacro:arg name="is_sim" default="true"/>` so the argument is accepted at the top level and flows through to included files.

**`lerobot_controller/launch/so101_controller.launch.py`**

Now passes `is_sim` to xacro when generating the robot description:
```python
Command(["xacro ", urdf_path, " is_sim:=", is_sim])
```

### Simulation is unchanged

`so101_gazebo.launch.py` calls xacro without an `is_sim` argument, so the default `true` applies and the Gazebo plugin is used as before. All existing Docker / Gazebo commands from the previous entries continue to work.

---

## What still needs to be done to control the real arm via localhost:3000

The following steps are required on a Linux Ubuntu 24.04 machine with the arm connected via USB.

### Step 1 — Install ROS 2 Jazzy natively

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers ros-jazzy-moveit \
  ros-jazzy-gz-ros2-control ros-jazzy-ros-gz \
  python3-colcon-common-extensions python3-rosdep
```

### Step 2 — Clone the repo and build

```bash
git clone <repo-url> ~/Robot_Arm_Team
cd ~/Robot_Arm_Team/lerobot
source /opt/ros/jazzy/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

Add auto-sourcing to `.bashrc` so every new terminal is ready:
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source ~/Robot_Arm_Team/lerobot/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Step 3 — USB permissions (once)

Without this, the serial port cannot be opened without sudo:
```bash
sudo usermod -aG dialout $USER
# Log out and back in once after this
```

Check that the arm is visible after plugging in USB:
```bash
ls /dev/ttyUSB*
# Expected: /dev/ttyUSB0
```

If the port is different (e.g. `ttyUSB1` or `ttyACM0`), update `serial_port` in:
`lerobot/src/lerobot_description/urdf/so101_ros2_control.xacro` line 19, then rebuild.

### Step 4 — Start the real arm stack (3 terminals)

**Terminal 1 — Controller Manager + hardware driver:**
```bash
ros2 launch lerobot_controller so101_controller.launch.py is_sim:=false
```
This starts `ros2_control_node` with the real hardware plugin, which opens `/dev/ttyUSB0` and pings all 6 servos. Check that all controllers are active:
```bash
ros2 control list_controllers
# Expected: joint_state_broadcaster active, arm_controller active, gripper_controller active
```

**Terminal 2 — MoveIt (needed for X/Y/Z position control in the GUI):**
```bash
ros2 launch lerobot_moveit so101_moveit.launch.py
```

**Terminal 3 — Web GUI:**
```bash
ros2 run lerobot_gui joint_state_gui
```

Open in browser: http://localhost:3000

### Step 5 — Verify

In the GUI, click `Fill current` to load the arm's current position into the target fields.
Make a small change (e.g. joint 1 by a few degrees) and click `Send`.
The real arm should move.

---

## Architecture summary (real arm)

```
Browser (localhost:3000)
    ↓ HTTP POST /send  or  /send_pose
lerobot_gui  (joint_state_gui.py)
    ↓ JointTrajectory topic
JointTrajectoryController  (ros2_control)
    ↓ position commands at 10 Hz
SO101HardwareInterface  (lerobot_hardware)
    ↓ SCS serial protocol over USB
Feetech STS3215 Servos (Joints 1–6)
```
