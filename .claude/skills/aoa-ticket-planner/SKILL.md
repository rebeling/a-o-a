---
name: aoa-ticket-planner
description: Plan one or more Jira tickets on demand - "/aoa-ticket-planner KEY [KEY...]". Writes tickets/KEY.md and prints READY / BLOCKED / NO-REPO with open questions.
---

# /aoa-ticket-planner [KEY ...]

You are the coordinator. You dispatch; you do not plan yourself.
Repo root is the directory containing `main.py`.

1. Keys: the arguments. None given → pick the first non-`TIME-` ticket with status `In Arbeit` from `tickets/snapshot.json`, else the first non-`TIME-` key there. Say which key you picked and why.
2. Dispatch one `ticket-planner` agent per key, prompt `prepare KEY`, all in one message.
3. For each finished plan, qualify from `tickets/KEY.md`:
   - NO-REPO if "Repo and files" says unknown
   - BLOCKED if "Open questions for the ticket writer" is not "None."
   - READY otherwise
4. Print per key: `KEY → QUAL` on one line, then its open questions verbatim, then the plan path. Nothing else.

Never run coder or reviewer. Never edit `tickets/KEY.md`, `tickets/repos.md`, `.env`. Do not rewrite the brief file.
