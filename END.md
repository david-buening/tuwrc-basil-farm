# GitHub Push-Anleitung

Du hast **zwei separate Git-Repos**, die du unabhängig pushen musst.

---

## Warum zwei Repos?

| Ordner | GitHub-Repo | Inhalt |
|--------|-------------|--------|
| `Robot_Arm/` | `david-buening/robot-arm-basil` | Dockerfile, docker-compose, START.md, Tagebuch, etc. |
| `Robot_Arm/lerobot/` | `david-buening/lerobot` | Dein Fork mit dem ganzen ROS-Code (URDF, Controller, GUI, ...) |

Das äußere Repo (`robot-arm-basil`) behandelt `lerobot/` als **Git-Submodul** — es speichert nur einen Zeiger auf einen bestimmten Commit des inneren Repos, nicht den Code selbst. Deshalb musst du **immer zuerst den inneren Repo pushen**, dann den äußeren.

---

## Schritt 1 — Änderungen im `lerobot`-Repo pushen

```bash
cd ~/Desktop/TUWRC/Robot_Arm/lerobot
```

Geänderte Dateien anzeigen:
```bash
git status
```

Änderungen stagen (entweder einzelne Dateien oder alles):
```bash
git add src/lerobot_gui/lerobot_gui/joint_state_gui.py
git add src/lerobot_gui/package.xml
# oder alles auf einmal:
git add .
```

Commit erstellen:
```bash
git commit -m "Kurze Beschreibung was du geändert hast"
```

Pushen:
```bash
git push origin main
```

---

## Schritt 2 — Submodul-Zeiger + äußeres Repo pushen

```bash
cd ~/Desktop/TUWRC/Robot_Arm
```

Status anzeigen:
```bash
git status
```

Du wirst so etwas sehen:
```
 m lerobot          ← Submodul hat neue Commits
?? test_pose.py     ← neue Dateien
 M Dockerfile       ← geänderte Dateien
```

Alles stagen:
```bash
git add lerobot         # Submodul-Zeiger aktualisieren
git add .               # alle anderen neuen/geänderten Dateien
```

Commit erstellen:
```bash
git commit -m "Kurze Beschreibung was du geändert hast"
```

Pushen:
```bash
git push origin master
```

---

## Einmalige Fixes (nur einmal nötig)

### `.gitmodules`-Datei fehlt

Ohne diese Datei weiß Git nicht, wo `lerobot/` zu finden ist, wenn jemand das Repo neu klont. Einmal ausführen:

```bash
cd ~/Desktop/TUWRC/Robot_Arm
cat > .gitmodules << 'EOF'
[submodule "lerobot"]
    path = lerobot
    url = https://github.com/david-buening/lerobot.git
EOF
git add .gitmodules
git commit -m "Add .gitmodules for lerobot submodule"
git push origin master
```

---

## Komplett-Workflow in einem Rutsch

```bash
# 1. Inneres Repo
cd ~/Desktop/TUWRC/Robot_Arm/lerobot
git add .
git commit -m "Was auch immer du geändert hast"
git push origin main

# 2. Äußeres Repo
cd ~/Desktop/TUWRC/Robot_Arm
git add .
git commit -m "Update lerobot submodule + ..."
git push origin master
```

---

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `git push` schlägt fehl (rejected) | Jemand hat direkt auf GitHub gepusht | `git pull origin main` zuerst |
| `lerobot` taucht nicht in `git status` auf | Submodul hat keine neuen Commits | Normal, nichts zu tun |
| Neues Gerät — `lerobot/` Ordner ist leer | Submodul wurde nicht initialisiert | `git submodule update --init` |

---

## Übersicht der Remote-URLs

```
robot-arm-basil:  https://github.com/david-buening/robot-arm-basil.git
lerobot (fork):   https://github.com/david-buening/lerobot.git
lerobot (origin): https://github.com/jb-balaji/lerobot  (nur lesen, kein push)
```
