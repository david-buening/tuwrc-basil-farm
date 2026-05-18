# GitHub Push Guide

Everything lives in a **single Git repository** on the `main` branch.

Remote: `https://github.com/david-buening/tuwrc-basil-farm.git`

---

## Workflow after finishing work

```bash
cd ~/Desktop/TUWRC/Robot_Arm_Team
```

Show changed files:
```bash
git status
```

Stage everything (or specific files):
```bash
git add .
# or specific files:
git add Diary.md lerobot/src/lerobot_hardware/
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

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `git push` fails with `rejected` | Someone pushed directly to GitHub | Run `git pull origin main` first, then push again |
| `git push` fails with `no upstream branch` | First push of a new branch | Run `git push -u origin main` once |
