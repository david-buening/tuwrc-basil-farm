# Start-Anleitung

Alle Schritte die nötig sind um von 0 auf den aktuellen Stand zu kommen.
!! Automatisiert ausführen: im Folder Robot_Arm sein und ./start.sh ausführen !!

---

## 1. Docker Desktop starten

```bash
open -a "Docker Desktop"
```

Warten bis das Docker-Icon in der Menüleiste nicht mehr animiert ist.

---

## 2. Container starten

Im `Robot_Arm`-Ordner:

```bash
docker compose up -d
```

> Falls du das Dockerfile geändert hast oder einen sauberen Neustart willst:
> ```bash
> docker compose down
> docker compose build
> docker compose up -d
> ```

---

## 3. Desktop im Browser öffnen

[http://localhost:6080/vnc.html](http://localhost:6080/vnc.html)

Passwort: `ros`

---

## 4. Gazebo starten

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 launch lerobot_description so101_gazebo.launch.py"
```

Warten bis Gazebo im Browser-Fenster erscheint.

---

## 5. Controller laden

In einem neuen Terminal:

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 launch lerobot_controller so101_controller.launch.py"
```

Prüfen ob alle Controller aktiv sind:

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 control list_controllers"
```

Erwartete Ausgabe:
```
joint_state_broadcaster  active
arm_controller           active
gripper_controller       active
```

---

## 6. MoveIt starten

MoveIt wird fuer die Endeffektor-Positionssteuerung im Web-GUI gebraucht (`/compute_ik`).

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 launch lerobot_moveit so101_moveit.launch.py"
```

Warten bis MoveIt gestartet ist. Danach sollte der IK-Service verfuegbar sein:

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 service list | grep compute_ik"
```

Erwartete Ausgabe:
```text
/compute_ik
```

---

## 7. Web-GUI starten (Joint Control + Endeffektor-Pose)

```bash
docker exec -it lerobot_container /bin/bash -ic "ros2 run lerobot_gui joint_state_gui"
```

Öffnen: [http://localhost:3000](http://localhost:3000)

Das GUI zeigt:
- aktuelle Joint-Winkel und editierbare Joint-Targets
- aktuelle Endeffektor-Pose `base -> gripper`
- editierbare Endeffektor-Position `X/Y/Z`
- Roll/Pitch/Yaw nur als Anzeige, nicht als Ziel

> Falls Port 3000 belegt ist: `docker exec -it lerobot_container /bin/bash -ic "pkill -f joint_state_gui"` — dann neu starten.

---

## 8. MoveIt in RViz benutzen (optional)

Im RViz MotionPlanning-Panel:
- **Planning Group**: `arm`
- **Start State**: `current`
- **Goal State**: `random valid`
- → `Plan & Execute`

---

## Übersicht der Ports

| Port | Inhalt |
|------|--------|
| [localhost:6080](http://localhost:6080/vnc.html) | Desktop (RViz, Gazebo) |
| [localhost:3000](http://localhost:3000) | Web-GUI (Joint States) |
| 5901 | VNC direkt |
