---
name: aoa-wiki
description: Knowledge-base wiki in wiki/ - "/aoa-wiki <question>" answers from it, "ingest [KEY|today]" updates it from tickets/briefs/memory, "decision: ..." / "request: ..." file a page, "lint" checks it.
---

# /aoa-wiki

The wiki in `wiki/` is maintained by you. Read `wiki/README.md` first: it is the schema and the list of what must never be written. Repo root is the directory containing `main.py`.

## `<question>` (default)
1. Read `wiki/index.md`, then only the pages it points to for this question.
2. Answer short, with the page paths you used.
3. Wiki cannot answer → look in `tickets/`, `briefs/`, memory, the clone. Answer, then write the answer into the fitting page (or a new one), add the index line and a `log.md` line.

## `ingest [KEY|today]`
1. No argument or `today`: sources changed since the last `ingest` line in `wiki/log.md` (compare file mtimes). `KEY`: that ticket's files.
2. For each source: update `wiki/tickets.md` row, the repo/project/howto pages it touches, and file decisions it states explicitly.
3. Update `wiki/index.md`, append one `log.md` line per source: `## [YYYY-MM-DD] ingest | <key> | <what changed>`.
4. Print the pages touched. Nothing else.

## `decision: <text>` / `request: <text>`
Write `wiki/decisions/YYYY-MM-DD-<slug>.md` or `wiki/requests/YYYY-MM-DD-<slug>.md` in the format of the existing pages, add index and log lines. A request without a Jira key gets the next free `TODO-N` (never reuse a number) as `tickets/TODO-N.notes.md`.

## `lint`
Check: states in `tickets.md` against the newest brief and notes; contradictions between pages; pages missing from the index and index lines without a page; broken `[[links]]`; forbidden content (grep for e-mail addresses, phone numbers, IBANs, "Tempo", hours). Print the findings as a list. Change nothing until the user says so.

## Rules
- Sources are never edited from here. Never read `.env`.
- Every page names its sources at the bottom. No fact without a source; write "unknown" instead of guessing.
- Never run planner, coder or reviewer from here.
