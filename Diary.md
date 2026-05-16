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
