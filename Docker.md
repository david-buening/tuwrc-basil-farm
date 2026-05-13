# Container bauen: (nur nötig wenn was an "lerobot" geändert wurde)
cd /Users/davidbuening/Desktop/TUWRC/Robot_Arm
docker compose build

# Container starten (wenn nichts an Image/ "lerobot" geändert wurde)
docker compose up

# Container runter fahren
docker compose down

# Wann du neu bauen musst
- `docker compose build` brauchst du nur, wenn du am Docker-Image selbst änderst.
  - z.B. neue Pakete installierst, den Dockerfile änderst oder System-Abhängigkeiten einfügst.
- Wenn du nur am Quellcode in `lerobot` änderst, musst du das Image normalerweise nicht neu bauen.
  - Der Ordner `.` wird in den Container gemountet, daher sieht der Container deine aktuellen Dateien.

# Code ändern vs. Image ändern
- Code ändern (Controller, ROS-Pakete, Launch-Dateien):
  - `docker compose up` reicht meistens.
  - Wenn du Änderungen kompilieren musst, mach das innerhalb des Containers mit `colcon build`.
- Dockerfile / Abhängigkeiten ändern:
  - `docker compose build` oder docker compose up --build verwenden.

# in den container gehen:
docker compose exec lerobot /bin/bash

# Nach dem aktuellen Dockerfile werden ROS 2 und der Workspace in interaktiven
# Bash-Shells automatisch gesourced. Danach reicht z.B.:
ros2 topic echo --once /joint_states

# Reihenfolge um container neu hochzufahren
docker compose down
docker compose build
docker compose up -d
docker compose exec lerobot /bin/bash
ros2 launch lerobot_description so101_display.launch.py


# Falls ein ROS-Befehl in einem nicht-interaktiven Shell-Kommando ausgeführt wird,
# weiter explizit sourcen, z.B.:
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic echo --once /joint_states"
