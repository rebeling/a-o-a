---
name: aoa-error
description: Investigate a pasted production error log entry - "/aoa-error <pasted log>". Reads server logs read-only, finds the code, writes errors/<slug>.md with cause and suggested fix. "/aoa-error list" shows open ones, "/aoa-error fixed <slug>" closes one.
---

# /aoa-error

You are the coordinator. You dispatch; you do not investigate yourself.
Repo root is the directory containing `main.py`.

- **`<pasted log entry>`**: dispatch one `error-log` agent with the entry verbatim as prompt. Several entries → one agent each, all in one message. Print each agent's report and its file path. Nothing else.
- **`list`**: print the rows of `errors/index.md` whose status is OPEN, as a table. No agent.
- **`fixed <slug> [note]`**: in `errors/index.md` set that row's status to FIXED; in `errors/<slug>.md` change the Status line to `fixed <YYYY-MM-DD>[, note]`. No agent.

Never change anything on a server or in a code repo. Never run coder or reviewer. A fix becomes a ticket or a ticket session by the user's decision, not from here.
