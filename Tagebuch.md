# 2.5. Stand
konnte Rviz in XFCE Fenster öffnen!
Dafür:
docker compose up -d
Dann in Browser: http://localhost:6080/vnc.html (Passwort: ros)
Dann: docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_description so101_display.launch.py"
Nächste Aufgabe: 3D Roboter im 

# 3.5 Stand
Rviz funktioniert mit passendem Roboter
Dafür oben links Global Options --> fixed frame --> world auswählen.

Gazebo funktioniert jetzt auch:
- Fehlende Gazebo/ros2_control Pakete wurden im Dockerfile ergänzt.
- `ros_gz_sim`, `ros_gz_bridge`, `gz_ros2_control`, Controller Manager und Joint Trajectory Controller sind verfügbar.
- SO101 kann in Gazebo gespawnt werden.
- Controller können geladen werden:
  - `joint_state_broadcaster`
  - `arm_controller`
  - `gripper_controller`
- Test-Trajectory an den Arm funktioniert.

Wichtig:
- ROS-Befehle immer ohne `sudo` ausführen.
- In jedem neuen Container-Terminal zuerst sourcen:
```bash
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash
```

Wenn der Container nur gestoppt/gestartet wird, reicht normalerweise:
```bash
docker compose up -d
```

Wenn der Container gelöscht wurde oder ich ganz sicher mit dem neuen Dockerfile starten will:
```bash
docker compose down
docker compose build
docker compose up -d
```

Dann im Browser noVNC öffnen:
```text
http://localhost:6080/vnc.html
Passwort: ros
```

Gazebo starten:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_description so101_gazebo.launch.py"
```

In einem zweiten Terminal Controller laden:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_controller so101_controller.launch.py"
```

Controller-Status prüfen:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 control list_controllers"
```

Sollte ungefähr zeigen:
```text
joint_state_broadcaster  active
arm_controller           active
gripper_controller       active
```

Test-Trajectory an den Arm schicken:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \"{joint_names: ['1', '2', '3', '4', '5'], points: [{positions: [0.2, -0.4, 0.4, 0.2, 0.0], time_from_start: {sec: 2, nanosec: 0}}]}\""
```

Gripper-Test:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \"{joint_names: ['6'], points: [{positions: [0.5], time_from_start: {sec: 1, nanosec: 0}}]}\""
```

Arm wieder neutral stellen:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \"{joint_names: ['1', '2', '3', '4', '5'], points: [{positions: [0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 2, nanosec: 0}}]}\""
```

# 6.5 Stand

MoveIt und erstes Web-GUI wurden ergänzt.

Geändert:
- `Dockerfile`: `ros-humble-moveit` ergänzt, damit MoveIt nach einem frischen Docker-Build installiert ist.
- `docker-compose.yml`: Port `3000:3000` ergänzt für das Web-GUI.
- `lerobot/src/lerobot_moveit/package.xml`: Dependency korrigiert:
  - falsch: `moveit_config_utils`
  - richtig: `moveit_configs_utils`
- Neues Paket `lerobot/src/lerobot_gui` angelegt.
  - Startet eine ROS2-Node.
  - Subscribed `/joint_states`.
  - Zeigt die aktuellen Joint States im Browser an.

Nach sauberem Rebuild:
```bash
docker compose up -d --build --force-recreate
```

noVNC / Gazebo / RViz Desktop:
```text
http://localhost:6080/vnc.html
Passwort: ros
```

Web-GUI:
```text
http://localhost:3000
```

Empfohlene Reihenfolge nach Container-Start:

1. Gazebo starten:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_description so101_gazebo.launch.py"
```

2. Controller starten/laden:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_controller so101_controller.launch.py"
```

3. Prüfen, ob Controller aktiv sind:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 control list_controllers"
```

Erwartung:
```text
joint_state_broadcaster  active
arm_controller           active
gripper_controller       active
```

4. Prüfen, ob Joint States kommen:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 topic echo --once /joint_states"
```

5. Joint-State-Web-GUI starten:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 run lerobot_gui joint_state_gui"
```

Falls Port 3000 belegt ist:
```bash
docker exec -it lerobot_container /bin/bash -lc "pkill -f joint_state_gui"
```

Danach GUI neu starten. Alternativ anderer Port innerhalb des Containers:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 run lerobot_gui joint_state_gui -- --port 3000"
```

Wichtig: Im Browser auf dem Mac ist nur Port 3000 erreichbar, wenn `docker-compose.yml` den Port mapped und der Container nach dieser Änderung neu erstellt wurde.

6. MoveIt starten:
```bash
docker exec -it lerobot_container /bin/bash -lc "source /opt/ros/humble/setup.bash && source /workspace/install/setup.bash && ros2 launch lerobot_moveit so101_moveit.launch.py"
```

MoveIt in RViz benutzen:
- Im MotionPlanning-Panel:
  - `Planning Group`: `arm`
  - `Start State`: `current`
  - `Goal State`: `random valid`
  - dann `Plan & Execute`
- `random valid` ist besser als nur `random`, weil MoveIt dann einen gueltigen Zustand innerhalb von Limits und Kollisionsregeln waehlt.

Wenn MoveIt beim Ausfuehren meldet:
```text
Invalid Trajectory: start point deviates from current robot state more than 0.01
```

Dann passt der geplante Startzustand nicht zum aktuellen Roboterzustand. Meist hilft:
- `Start State` auf `current` setzen.
- Direkt `Plan & Execute` statt lange zwischen Plan und Execute warten.
- Pruefen, ob `/joint_states` aktuell kommen.

Hinweis:
- Ohne Gazebo/Controller bzw. ohne `joint_state_broadcaster` bekommt das Web-GUI keine `/joint_states`.
- MoveIt selbst erzeugt nicht die Joint States; es plant Bewegungen und schickt Trajektorien an die Controller.

# 6.5 Zusatz: Automatisches Sourcen

Das Dockerfile wurde so angepasst, dass interaktive Bash-Shells fuer `rosuser` automatisch sourcen:
```bash
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash
```

Nach einem neuen Build kann man also in den Container gehen:
```bash
docker exec -it lerobot_container /bin/bash
```

Und dann direkt ROS-Befehle ausfuehren:
```bash
ros2 topic echo --once /joint_states
ros2 control list_controllers
ros2 launch lerobot_description so101_gazebo.launch.py
```

Wichtig: Bei Einzeiler-Kommandos von aussen mit `docker exec ... /bin/bash -lc "..."` ist explizites Sourcen weiterhin die robusteste Variante, weil das nicht dieselbe interaktive Shell-Nutzung ist.

# 13.5 Stand

Heute wurde das Web-GUI deutlich ausgebaut. Der vorherige Joint-Space-Stand ist damit jetzt auch nachgetragen:

- Das GUI laeuft unter `http://localhost:3000`.
- Es zeigt live die aktuellen `/joint_states`.
- Fuer alle Joints `1` bis `6` gibt es Target-Felder in Grad.
- Buttons:
  - `Fill current`: uebernimmt die aktuelle Roboterstellung als Target.
  - `Reset to 0`: setzt Targets auf 0.
  - `Send`: schickt eine Joint-Trajectory an `arm_controller` und `gripper_controller`.

Zusaetzlich wurde die Endeffektor-Anzeige gebaut:

- Das GUI liest per TF die Transformation `base -> gripper`.
- Angezeigt werden:
  - `X`, `Y`, `Z` in Metern.
  - `Roll`, `Pitch`, `Yaw` in Grad.
  - Roll ist Rotation um X, Pitch um Y, Yaw um Z.
- Wegen nur 5 DOF am Arm werden Roll/Pitch/Yaw aktuell nur angezeigt, aber nicht als Ziel vorgegeben.
- Bearbeitbar sind fuer den Endeffektor erstmal nur `X/Y/Z`.
- Beim Senden von `X/Y/Z` nutzt das GUI MoveIt ueber `/compute_ik`, berechnet daraus passende Joint-Winkel und sendet diese dann als Trajectory an den Arm.
- In `lerobot/src/lerobot_moveit/config/kinematics.yaml` wurde `position_only_ik: True` gesetzt, damit MoveIt nur die Position erreichen muss und nicht an einer vollstaendigen 6D-Pose scheitert.

Wichtige Erkenntnis:

- Eine volle Endeffektor-Pose hat 6 Freiheitsgrade: `x/y/z/roll/pitch/yaw`.
- Der SO101-Arm hat fuer die Armbewegung nur 5 DOF.
- Deshalb kann nicht jede beliebige Kombination aus Position und Orientierung erreicht werden.
- Fuer den aktuellen Stand ist daher die beste Bedienung:
  1. `Fill current` klicken.
  2. Kleine Aenderungen an `X/Y/Z` machen.
  3. `Send` klicken.

Start wurde ebenfalls vereinfacht:

- `start.sh` startet jetzt Docker, Gazebo, Controller, MoveIt und Web-GUI.
- Dadurch sollte nach `./start.sh` auch die Endeffektor-Positionssteuerung direkt funktionieren.
- `START.md` wurde entsprechend aktualisiert.
