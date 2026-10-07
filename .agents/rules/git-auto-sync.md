---
description: Mandatory git auto-sync and commit activity rule for all projects in loyihalar
globs: **/*
---

# Git Auto-Sync & Contribution Activity Rule

Whenever ANY file or project is modified or created in this workspace:
1. Always run `./sync-git.sh "<message>"` or `python3 sync-git.py "<message>"` upon completing the task.
2. This ensures all commits are pushed to `all-projects` and to each individual project's standalone GitHub repository.
3. NEVER commit `.env`, SSH keys, secrets, or large dependencies.
