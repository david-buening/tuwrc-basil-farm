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

# May 27 Status

## Fixed Docker build issue in `lerobot_description`

### Problem

`lerobot_description/CMakeLists.txt` still installed a `config` directory although `lerobot_description/config` no longer exists in the repository.

### Fix

Removed `config` from the `install(DIRECTORY ...)` section in `lerobot_description/CMakeLists.txt`.

### Result

`colcon build` inside the Docker container now continues past `lerobot_description` successfully.

# July 17 Status — X-Rail as 6th DOF (prismatic joint)

The SO-101 arm was extended with a linear X-axis (rail + carriage) as a new prismatic joint `rail_joint`. The arm now has 6 DOF, so full 6D end-effector poses (position + orientation) can be targeted.

> **Note / known limitation:** The URDF extension is **not a 1:1 accurate model** of the real rail assembly. The rail and plate meshes were placed with hand-tuned offsets and rotations (eyeballed in RViz), the mesh scale (`0.0001`) is a workaround, masses/inertias are rough placeholder values, and the visual-only rail links have no proper collision geometry. If the rail is ever supposed to be represented fully realistically (correct geometry, mounting positions, and assembly of rail, carriage, and slider), the URDF needs another revision.

## Changed files

**`lerobot_description/urdf/so101_base.xacro`**
- New link `rail_link`: two rail meshes (`meshes/rail/rail.stl`), 90 mm apart in Y, fixed to `world` via `world_to_rail` (raised by `z=0.085` so the rail bottom sits on the Gazebo ground instead of sinking into it — buried collision meshes make physics extremely slow).
- New link `carriage_link`: the moving plate (`meshes/rail/plate.stl`).
- New joint `rail_joint` (prismatic, axis X, range −0.5 m … +0.5 m, effort 50, velocity 1.0) between rail and carriage, plus a transmission.
- `base_joint` now attaches the robot `base` to `carriage_link` (with a fine-tune offset of −3 cm in X, −7 cm in Z) instead of directly to `world` — the whole arm rides on the carriage.

**`lerobot_description/meshes/rail/`** (new)
- `rail.stl` and `plate.stl` meshes for the linear axis.

**`lerobot_description/urdf/so101_ros2_control.xacro`**
- Added `rail_joint` with position command interface (−0.5 … 0.5) and position state interface.

**`lerobot_controller/config/so101_controllers.yaml`**
- `rail_joint` added to the `arm_controller` joint list.

**`lerobot_moveit/config/*`**
- `so101.srdf`: planning group `arm` now starts at `rail_joint` (instead of the fixed `base_joint`), `rail_joint` added to the `home` state, and collision checking disabled between rail/carriage/base/shoulder pairs.
- `joint_limits.yaml`, `initial_positions.yaml`, `moveit_controllers.yaml`: `rail_joint` registered everywhere.
- `kinematics.yaml`: `position_only_ik` switched from `True` to `False` — with the rail as 6th DOF, MoveIt now solves full 6D poses including orientation.

**`lerobot_gui/lerobot_gui/joint_state_gui.py`**
- `rail_joint` added to the joint table; it is treated as a linear joint (values in **meters**, not degrees — separate handling in display, input step size, and the `/send` endpoint).
- Pose reference frame switched from `base` to `world`, because `base` now moves with the carriage and is no longer a fixed frame.
- Roll/Pitch/Yaw are no longer display-only: they are now editable target fields. The GUI converts them to a quaternion (`euler_to_quaternion`) and sends the full 6D pose to `/compute_ik`. The IK solution now also includes `rail_joint`.

**`waypoint_runner.py`** (new, repo root)
- Standalone script that drives the robot through a list of full 6D Cartesian waypoints (`x, y, z, roll, pitch, yaw` in the `world` frame): for each waypoint it calls MoveIt `/compute_ik` (which includes `rail_joint` via the `arm` group), sends the solution as a timed trajectory, waits until the pose is reached, then continues. Waypoints with failing IK are skipped with a warning instead of aborting.

# July 29 Status — One-command startup for the rail setup

`start.sh` still brings up the original 5-DOF robot. For the rail version there is now a separate script:

```bash
./start_rail.sh
```

It does everything from a cold start: Docker Desktop, container, build, Gazebo, controllers, MoveIt, web GUI — and verifies along the way that the setup actually came up.

## Why a separate script and not just `start.sh`

Two extra steps are needed for the rail, and both caused real debugging sessions before they were automated:

**1. `colcon build` before launching (step 4).**
Gazebo spawns the robot from `install/`, not from `src/`. Without a rebuild, every URDF/controller/MoveIt change is silently ignored and the *old* robot starts — it looks like the edit "did nothing".

**2. Killing stale processes first (step 3).**
A surviving `robot_state_publisher` or `joint_state_publisher` keeps serving the OLD robot description. The result is confusing: `rail_joint` is missing from `/joint_states` even though the URDF is correct. Ports and controller activation can also block.

## Verification instead of just printing status

- Step 7 polls for up to 60 s until `arm_controller` really reports `active`. On timeout it names the most likely cause (robot stuck in the ground plane → physics rate collapses → activation times out).
- Step 8 polls for up to 40 s until `/compute_ik` exists (without it, all 6D pose targets fail).
- At the end it checks whether `rail_joint` actually appears in `/joint_states`. That is the single best indicator that the 6-DOF setup is live.

## Two pitfalls found while testing the script

**`pkill` killed itself.** The cleanup ran as `bash -c 'pkill -9 -f "ign gazebo"; pkill -9 -f rviz2; ...'`. The pattern text is part of that shell's own command line, so the first `pkill` matched the shell itself and killed it — Gazebo died, but `move_group`, `rviz2` and `robot_state_publisher` survived. Fix: the bracket trick in every pattern (`"[i]gn gazebo"`), which matches the real process but not the pattern string itself.

**Terminal windows may be blocked.** The script opens one macOS Terminal window per launch via `osascript`. If macOS denies the Apple Event (error `-1743`, missing Automation permission), the launches now fall back to running detached inside the container, so the stack still comes up. To get real windows: *System Settings → Privacy & Security → Automation*, and allow the terminal app to control Terminal.

## After startup

| What | Where |
|------|-------|
| Desktop (Gazebo, RViz) | [localhost:6080](http://localhost:6080/vnc.html), password `ros` |
| Web GUI (`rail_joint` in meters, 6D pose) | [localhost:3000](http://localhost:3000) |

Run the waypoint sequence:
```bash
docker exec -it lerobot_container /bin/bash -ic "source /opt/ros/humble/setup.bash && source /workspace/lerobot/install/setup.bash && python3 /workspace/waypoint_runner.py"
```

Shut everything down (the running stack uses several hundred percent CPU):
```bash
docker compose stop
```

# July 29 Addendum: TCP Tool Frame (fixes the "axes are off" problem)

## The symptom

Commanding a pose and reading it back gave completely different orientation numbers:

| | commanded | GUI showed |
|---|-----------|------------|
| Waypoint 2 | roll 113.5, pitch -90, yaw 120 | roll -0.21, pitch -90, yaw -126.29 |
| back to waypoint 1 | roll -156.5, pitch -90, yaw 66.5 | roll 65.54, pitch -90, yaw -155.54 |

Driving to the *same* commanded pose twice even produced *different* displayed values.

## The cause: gimbal lock, not a control error

The rotations were in fact identical - verified by converting both triples to
quaternions and comparing (dot product = 1.000000). At `pitch = ±90°` the Euler
decomposition is singular: roll and yaw axes coincide, so only the **sum
`roll + yaw`** is defined and the individual values can be split arbitrarily.

Check the sums: -156.5 + 66.5 = **-90**, and 65.54 - 155.54 = **-90**. Same rotation.
For waypoint 2: 113.5 + 120 = 233.5 and -0.21 - 126.29 = -126.5, which differ by
exactly 360°. Also the same rotation.

Why was pitch *always* exactly -90? Because the `gripper` link frame comes from CAD
with its **X axis pointing straight up**. In the ROS convention `R[2][0] = -sin(pitch)`,
so a vertical X axis forces `pitch = -90°`. The setup was therefore **permanently
parked in the singularity**, which is why roll/yaw were never reproducible.

Measured at the home pose, the gripper axes pointed like this:

| gripper axis | direction in `world` |
|--------------|----------------------|
| X | +Z (up)  ← causes the singularity |
| Y | +X |
| Z | +Y |

## The fix: a `tcp` frame with the standard tool convention

Instead of commanding the `gripper` link, there is now a dedicated tool frame.
The approach direction was derived from the mesh geometry rather than guessed: the
jaw extends from `gripper z = -0.013` to `-0.105`, so the gripper approaches along
**gripper -Z**. (Consistent with joint `5` rotating about `gripper-Z` - the classic
wrist roll about the approach axis.)

```xml
<link name="tcp" />
<joint name="gripper_to_tcp" type="fixed">
    <parent link="gripper" /><child link="tcp" />
    <origin xyz="0 0 -0.090" rpy="3.14159 0 1.5708" />
</joint>
```

| TCP axis | equals | meaning |
|----------|--------|---------|
| Z | gripper -Z | approach direction, out of the gripper |
| X | gripper +Y | horizontal → **out of the singularity** |
| Y | gripper +X | |

The origin sits on the approach axis at 9 cm, i.e. at the grasp point just short of
the fingertip (10.5 cm).

## Result

| | before (`gripper`) | after (`tcp`) |
|--|--------------------|---------------|
| home position | (-0.009, -0.277, 0.282) | (-0.009, **-0.367**, 0.282) |
| home RPY | (-156.5, **-90.0**, 66.5) | (**+90.0, 0.0, 0.0**) |

Round-trip test: commanded (70, 15, 25) came back as (70.67, 14.58, 25.16) - under
1° deviation (IK tolerance plus controller settling). Previously commanded and
displayed values were 222° apart.

**Note:** `roll = 90°` at the home pose is not an offset. `RPY = (0,0,0)` would mean
the TCP axes coincide with the world axes, i.e. the gripper pointing *straight up*.
At home it points horizontally forward (`world -Y`), which is exactly a 90° rotation
about X.

## Changed files

- `so101_base.xacro`: added `tcp` link + fixed joint `gripper_to_tcp`.
- `so101.srdf`: `gripper_to_tcp` added to the `arm` group so MoveIt can solve IK for `tcp`.
- `joint_state_gui.py`: `END_EFFECTOR_FRAME = "tcp"`.
- `waypoint_runner.py`: `END_EFFECTOR_LINK = "tcp"`.
- `moveit.rviz`: TF display added (frames `world`, `rail_link`, `carriage_link`, `base`,
  `tcp`), `Marker Scale 0.45`, and **Fixed Frame changed from `Base` to `world`** -
  with `base` as reference the world appeared to move whenever the rail travelled.

**Important:** old waypoint numbers are no longer valid. They referred to the
`gripper` link origin; targets now control the TCP - 9 cm further out and with a
different axis convention. Easiest way to get new ones: drive the robot, press
`Fill current`, copy the values.

# July 29 Addendum: Home button in the task-space section

`Reset to 0` made no sense for the end-effector section: position (0,0,0) sits inside
the base, and an orientation of (0,0,0) would mean the gripper points straight up.
That button is now **`Home`** and fills the target fields with the pose the robot has
when every joint is at 0:

```text
x = -0.0094   y = -0.3675   z = +0.2819   roll = 90   pitch = 0   yaw = 0
```

Verified by driving all joints to exactly 0 and measuring the TCP.

The values live in a single `HOME_POSE` constant in `joint_state_gui.py` and are
injected into the page via a placeholder, so Python and JavaScript cannot drift apart.
In the joint-space section `Reset to 0` stays as it is - there it is meaningful.

## Two debugging lessons from this session

- **`ros2 topic echo /joint_states` is only a snapshot.** Several confusing readings
  turned out to be samples taken *during* a motion. When measuring a pose, take
  multiple samples and only trust values that stay constant.
- **RViz overwrites its config file on a clean exit.** Kill RViz hard before editing
  `moveit.rviz`, otherwise the old configuration is written back over the change.
