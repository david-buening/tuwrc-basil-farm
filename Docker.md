# Build the container only when something changed in the Docker image

```bash
cd /Users/davidbuening/Desktop/TUWRC/Robot_Arm_Team
docker compose build
```

# Start the container when the image did not change

```bash
docker compose up
```

# Stop the container

```bash
docker compose down
```

# When to rebuild

- You need `docker compose build` only when you change the Docker image itself.
  - Examples: installing new packages, changing the Dockerfile, or adding system dependencies.
- If you only change source code in `lerobot`, you usually do not need to rebuild the image.
  - The folder `.` is mounted into the container, so the container sees your current files.

# Code changes vs. image changes

- Code changes (controllers, ROS packages, launch files):
  - `docker compose up` is usually enough.
  - If the changes need compilation, run `colcon build` inside the container.
- Dockerfile or dependency changes:
  - Use `docker compose build` or `docker compose up --build`.

# Open a shell in the container

```bash
docker compose exec lerobot /bin/bash
```

With the current Dockerfile, ROS 2 and the workspace are sourced automatically in interactive Bash shells. After opening the shell, commands like this are enough:

```bash
ros2 topic echo --once /joint_states
```

# Restart sequence

```bash
docker compose down
docker compose build
docker compose up -d
docker compose exec lerobot /bin/bash
ros2 launch lerobot_description so101_display.launch.py
```

# Non-interactive shell commands

If a ROS command is executed in a non-interactive shell command, keep sourcing explicitly:

```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic echo --once /joint_states"
```
