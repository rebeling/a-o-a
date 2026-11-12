# Jira tickets

This repo has a read-only Jira CLI in `main.py`. Use it to fetch the user's tickets
instead of calling the Jira API directly. Credentials come from `.env` next to
`main.py` (git-ignored, never read or print it) or from `JIRA_BASE_URL`, `JIRA_EMAIL`,
`JIRA_API_TOKEN` in the shell; if missing, exit code is 2 and the message
names the missing variable — tell the user, do not guess values.

```sh
uv run main.py mytickets --json          # open tickets assigned to the user
uv run main.py get KEY [KEY...] --json   # summary, description, status, labels, url; --comments adds the thread
uv run main.py sync --json               # new / gone / changed since last snapshot, refreshes it
uv run main.py comment KEY "text"        # the only write: post a comment ("-" = text from stdin)
```

Prefer `--json` when consuming output. `comment` is the only Jira write and runs only when the user asks for it; never transitions, edits or deletes.

# Ticket planning

`.claude/agents/ticket-planner.md` turns one ticket into `tickets/<KEY>.md` (what,
problem, solution, repo/files, open questions). `tickets/repos.md` lists known local clones. Which
clone a ticket belongs to is decided by the user per ticket (`/aoa-brief KEY: repo <path>`) or by an
existing clone whose branch contains the key. Never guess a repo. Tickets with key prefix `TIME-` are
timetracking buckets, never work.

# Workflow

- `/aoa-brief` morning: `main.py sync` diffs tickets against `tickets/snapshot.json`; plans nothing; lists and qualifies all (no plan file = UNPLANNED); writes `briefs/YYYY-MM-DD.md`. `/aoa-brief tempo` adds Tempo estimates.
- `/aoa-brief KEY: note` records a change for one ticket in `tickets/KEY.notes.md` and re-plans it.
- `/aoa-ticket-planner KEY [KEY...]` plans given tickets on demand. `/aoa-brief` never plans a ticket just because its notes changed.
- `/aoa-work KEY` runs coder → reviewer (max 2 rounds). Workdir is the existing clone whose branch contains KEY (building on the user's uncommitted work there), else a new git worktree `<repo>-KEY` on `fix/KEY` or `feature/KEY`. Other clones are never touched. Nothing is committed; the user commits.
- Agents: `ticket-planner`, `coder`, `reviewer` in `.claude/agents/`. Skills in `.claude/skills/`.
- Per-ticket files in `tickets/`: `KEY.md` plan, `KEY.notes.md` user notes, `KEY.done.md` coder report, `KEY.review.md` verdict.

# Commits

One line, `KEY: what changed` where a ticket applies. No body, no Co-Authored-By, no Claude mention. Applies to every repo.
