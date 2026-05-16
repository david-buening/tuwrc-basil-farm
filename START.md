# Start Guide

All steps needed to bring the project from a clean start to the current working setup.
To run the automated setup, open the `Robot_Arm_Team` folder and run `./start.sh`.

---

## 1. Start Docker Desktop

```bash
open -a "Docker Desktop"
```

Wait until the Docker icon in the menu bar is no longer animated.

---

## 2. Start the container

From the `Robot_Arm_Team` folder:

```bash
docker compose up -d
```

> If you changed the Dockerfile or want a clean restart:
> ```bash
> docker compose down
> docker compose build
> docker compose up -d
> ```

---

## 3. Open the desktop in the browser

[http://localhost:6080/vnc.html](http://localhost:6080/vnc.html)

Password: `ros`

---

## 4. Start Gazebo

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 launch lerobot_description so101_gazebo.launch.py"
```

Wait until Gazebo appears in the browser window.

---

## 5. Load the controllers

In a new terminal:

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 launch lerobot_controller so101_controller.launch.py"
```

Check that all controllers are active:

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 control list_controllers"
```

Expected output:
```text
joint_state_broadcaster  active
arm_controller           active
gripper_controller       active
```

---

## 6. Start MoveIt

MoveIt is required for end-effector position control in the web GUI (`/compute_ik`).

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 launch lerobot_moveit so101_moveit.launch.py"
```

Wait until MoveIt has started. After that, the IK service should be available:

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 service list | grep compute_ik"
```

Expected output:
```text
/compute_ik
```

---

## 7. Start the web GUI (joint control and end-effector pose)

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 run lerobot_gui joint_state_gui"
```

Open: [http://localhost:3000](http://localhost:3000)

The GUI shows:
- current joint angles and editable joint targets
- current end-effector pose `base -> gripper`
- editable end-effector position `X/Y/Z`
- Roll/Pitch/Yaw as display values only, not as targets

> If port 3000 is already in use: `docker exec -it lerobot_container /bin/bash -ic "pkill -f joint_state_gui"` and then start the GUI again.

---

## 8. Use MoveIt in RViz (optional)

In the RViz MotionPlanning panel:
- **Planning Group**: `arm`
- **Start State**: `current`
- **Goal State**: `random valid`
- Click `Plan & Execute`

---

## Port Overview

| Port | Content |
|------|---------|
| [localhost:6080](http://localhost:6080/vnc.html) | Desktop (RViz, Gazebo) |
| [localhost:3000](http://localhost:3000) | Web GUI (joint states) |
| 5901 | Direct VNC access |
