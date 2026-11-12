---
name: aoa-brief
description: Morning brief - sync Jira tickets, list and qualify all, write briefs/YYYY-MM-DD.md. Never plans. Also "tempo" or "KEY: note".
---

# /aoa-brief

You are the coordinator. You run agents; you do not plan, code or review yourself.
Repo root is the directory containing `main.py`. Run all commands from there.

## Mode A — no argument (morning)

1. `uv run main.py sync --json`. Exit 2 → print the stderr line and stop. It returns `new`, `gone`, `changed` (with per-field old/new values) and `unchanged`, and refreshes `tickets/snapshot.json`. Ignore every key starting with `TIME-` everywhere below.
2. Never dispatch `ticket-planner` here. Planning is the user's call via `/aoa-ticket-planner KEY`. In the changes line, name every ticket that needs it: "KEY has no plan, run /aoa-ticket-planner KEY" for a missing `tickets/KEY.md`; "KEY changed/has new notes, run /aoa-ticket-planner KEY" when the ticket is in `changed` or `tickets/KEY.notes.md` is newer than the plan.
3. Qualify every open ticket from its plan file:
   - UNPLANNED if `tickets/KEY.md` is missing (checked first)
   - FEEDBACK if `tickets/KEY.review.md` exists and its verdict is OK
   - NO-REPO if "Repo and files" says unknown and `tickets/KEY.notes.md` has no `repo:` line. A `repo:` note counts as answered; the "which repo" question then no longer counts as open.
   - BLOCKED if "Open questions for the ticket writer" is not "None." (after dropping questions answered in the notes)
   - READY otherwise
   Next step is a short human action, no commands, at most six words:
   - UNPLANNED → `Plan it`
   - FEEDBACK → `Waiting for feedback`
   - READY → `Ready to implement`
   - BLOCKED → `Clarify N questions` (N = count of open questions)
   - NO-REPO → `Name the repo`
   Commands live in the legend, not in the table.

4. Tempo only when asked (`/aoa-brief tempo`, or the user says "with tempo" / "time"): dispatch the `reporter` agent: "tempo entries since the last working day for these repos: <every distinct non-empty path in tickets/repos.md>". These are separate clones; the reporter handles each as its own repo. Print the reporter's table in the terminal after the brief summary; it never goes into the brief file.
5. Write `briefs/YYYY-MM-DD.md`:
   ```markdown
   # Brief YYYY-MM-DD

   Jira: <base>/jira/for-you?tab=assigned   (base = any ticket url up to the host, e.g. https://your-site.atlassian.net)

   ## Changes since last sync
   New: ... · Gone: ... · Changed: KEY field old -> new (one line per change; description changes just say "description changed")
   or: Nothing changed.

   | Key | Title | Status | Prio | Qual | Next step |
   |---|---|---|---|---|---|
   | [KEY](<ticket url>) | <title> | ... |      (key links to the Jira ticket; title = the summary cut to 3–5 words, prefix like "Shop:" dropped)
   | TODO-N | <title> | — | — | — | <next step> |      (items the user adds that have no Jira ticket; keys `TODO-1`, `TODO-2`, … numbered in order of adding, never reused; first rows of the table; kept across briefs until the user says done)

   Qual:
   - FEEDBACK: implemented and reviewed OK, pushed. Waiting for feedback from stage or ticket writer.
   - READY: plan complete, repo known. `/aoa-work KEY` can start.
   - BLOCKED: open questions. Answer: `/aoa-brief KEY: <answer>`. Skip: `/aoa-work KEY ignore questions`.
   - NO-REPO: no clone named. Tell it via `/aoa-brief KEY: repo <path>`.
   - UNPLANNED: no plan file. `/aoa-ticket-planner KEY`.

   ## Open questions (only tickets in `new` or `changed` that have a plan)
   ### KEY — summary
   1. ...

   ```
6. Print to the terminal: the changes line, the table, the legend line, the count of UNPLANNED/FEEDBACK/READY/BLOCKED/NO-REPO, and the brief path. Nothing else.

## Mode A with argument `tempo`

Same as Mode A, with step 4 included. Tempo output is terminal only.

## Mode B — argument `KEY: note`

Notes are free text. Forms the planner understands specially: `repo: <path>` (which clone, may repeat), `base: <branch>` (branch the ticket branch off it), `branch: <branch>` (work directly on that branch, no new branch). Everything else is an answer or decision that overrides the ticket text.

1. Append `- YYYY-MM-DD: <note>` to `tickets/KEY.notes.md` (create if missing).
2. Dispatch `ticket-planner` with `prepare KEY`.
3. Qualify as in A3 and print one line: `KEY → <QUAL>. <next step>` plus remaining open questions if any.
Do not rewrite the brief file.

## Rules

- Never run coder or reviewer from here. Mode A never runs the planner either; only Mode B does.
- Never edit `tickets/KEY.md`, `tickets/repos.md`, `.env`.
- If an agent fails, say which ticket and why; do not retry more than once.
