# GitHub Push Guide

You have **two separate Git repositories** that must be pushed independently.

---

## Why two repositories?

| Folder | GitHub repository | Content |
|--------|-------------------|---------|
| `Robot_Arm_Team/` | `david-buening/robot-arm-basil` | Dockerfile, docker-compose, START.md, Diary.md, etc. |
| `Robot_Arm_Team/lerobot/` | `david-buening/lerobot` | Your fork with all ROS code (URDF, controllers, GUI, etc.) |

The outer repository (`robot-arm-basil`) treats `lerobot/` as a **Git submodule**. It stores only a pointer to a specific commit of the inner repository, not the inner source code itself. That means you must **always push the inner repository first**, then push the outer repository.

---

## Step 1 - Push changes in the `lerobot` repository

```bash
cd ~/Desktop/TUWRC/Robot_Arm_Team/lerobot
```

Show changed files:
```bash
git status
```

Stage changes, either specific files or everything:
```bash
git add src/lerobot_gui/lerobot_gui/joint_state_gui.py
git add src/lerobot_gui/package.xml
# or everything at once:
git add .
```

Create a commit:
```bash
git commit -m "Short description of what changed"
```

Push:
```bash
git push origin main
```

---

## Step 2 - Push the submodule pointer and the outer repository

```bash
cd ~/Desktop/TUWRC/Robot_Arm_Team
```

Show status:
```bash
git status
```

You will see something like this:
```text
 m lerobot          <- submodule has new commits
?? test_pose.py     <- new files
 M Dockerfile       <- changed files
```

Stage everything:
```bash
git add lerobot         # update the submodule pointer
git add .               # add all other new or changed files
```

Create a commit:
```bash
git commit -m "Short description of what changed"
```

Push:
```bash
git push origin master
```

---

## One-time fixes

### Missing `.gitmodules` file

Without this file, Git does not know where to find `lerobot/` when someone clones the repository. Run this once:

```bash
cd ~/Desktop/TUWRC/Robot_Arm_Team
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

## Full workflow in one pass

```bash
# 1. Inner repository
cd ~/Desktop/TUWRC/Robot_Arm_Team/lerobot
git add .
git commit -m "Short description of what changed"
git push origin main

# 2. Outer repository
cd ~/Desktop/TUWRC/Robot_Arm_Team
git add .
git commit -m "Update lerobot submodule and project files"
git push origin master
```

---

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `git push` fails with `rejected` | Someone pushed directly to GitHub | Run `git pull origin main` first |
| `lerobot` does not appear in `git status` | The submodule has no new commits | Normal, nothing to do |
| New machine and the `lerobot/` folder is empty | The submodule was not initialized | Run `git submodule update --init` |

---

## Remote URL Overview

```text
robot-arm-basil:  https://github.com/david-buening/robot-arm-basil.git
lerobot (fork):   https://github.com/david-buening/lerobot.git
lerobot (origin): https://github.com/jb-balaji/lerobot  (read-only, do not push)
```
