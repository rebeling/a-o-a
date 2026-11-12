---
name: aoa-work
description: Implement a planned Jira ticket - "/aoa-work KEY". Coder works on a ticket branch, reviewer checks against the plan, max two rounds, nothing committed.
---

# /aoa-work KEY

You are the coordinator. You run agents; you do not code or review yourself.
Repo root is the directory containing `main.py`.

1. Check `tickets/KEY.md` exists, else stop: "No plan, run /aoa-brief first."
2. Dispatch `coder` with prompt `implement KEY` (add `ignore questions` only if the user said so). If it stops on a precondition, print its reason and stop.
3. Dispatch `reviewer` with prompt `review KEY`.
4. If verdict is FIX and this was round 1: dispatch `coder` with `implement KEY, rework round 2, apply tickets/KEY.review.md`, then `reviewer` with `review KEY, round 2`.
5. Print: verdict, workdir path(s), branch name, `tickets/KEY.review.md` path, and for FIX the open items. Remind: nothing is committed; commit inside the workdir when satisfied. If the workdir is a worktree, mention `git worktree remove <path>` after merging.

Never commit, never run more than two rounds, never touch files yourself.
