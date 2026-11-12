# a-o-a — Jira tickets hub for Claude Code

A small hub for working Jira tickets with Claude Code: a Jira CLI, three agents (planner, coder, reviewer),
three skills that drive them, and a local knowledge base that is never committed.

The CLI fetches your Jira Cloud tickets and can post a comment. Nothing else is written. No dependencies beyond
the Python standard library. Meant for you and for agents that need ticket context.

## Setup

Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens
and put it in `.env` next to `main.py` (git-ignored), or export the same vars in
your shell (shell wins over `.env`):

```sh
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
```

## Usage

```sh
uv run main.py mytickets            # open tickets assigned to you, as a table
uv run main.py mytickets --json     # same, as JSON
uv run main.py get ABC-12 ABC-13    # full details as markdown
uv run main.py get ABC-12 --json    # same, as JSON
uv run main.py sync                 # what changed since last run; keeps tickets/snapshot.json
uv run main.py sync --json          # {"new": [...], "gone": [...], "changed": [{key, fields}], "unchanged": [...]}
uv run main.py comment ABC-12 "text" # post a comment; "-" reads the text from stdin. The only write.
```

`sync` fetches details only for tickets whose Jira `updated` stamp differs from the
snapshot, so a quiet morning costs one request.

`mytickets` uses the JQL
`assignee = currentUser() AND statusCategory != Done ORDER BY priority ASC, updated DESC`.

Exit codes: `0` ok, `1` Jira/HTTP error (message on stderr), `2` missing env var.

## Tests

```sh
uv run pytest
```

## Workflow

Run Claude Code in this folder. `CLAUDE.md` holds the rules; agents live in `.claude/agents/`, skills in `.claude/skills/`.

| Command | What it does |
|---|---|
| `/aoa-brief` | Morning: syncs tickets, lists and qualifies all, writes `briefs/YYYY-MM-DD.md`. Plans nothing. |
| `/aoa-brief KEY: note` | Records a decision for one ticket in `tickets/KEY.notes.md` and re-plans it. |
| `/aoa-ticket-planner KEY` | Turns a ticket into a plan file `tickets/KEY.md`. |
| `/aoa-work KEY` | Coder implements the plan in a git worktree, reviewer checks it. Max two rounds. Nothing is committed. |

Qualification in the brief: `UNPLANNED` (no plan), `READY`, `BLOCKED` (open questions), `NO-REPO` (no clone named),
`FEEDBACK` (reviewed OK, waiting).

Tickets whose key starts with `TIME-` are treated as time-tracking buckets and skipped; change the prefix in
`CLAUDE.md` and the skills to match yours. `/aoa-brief tempo` expects a `reporter` agent of your own that turns
git history into time entries; it is not part of this repo.

## Knowledge base

The hub keeps what it learns as plain markdown next to the code. It is local only: `.gitignore` excludes the
content, the folders ship empty. Nothing about your tickets, customers or systems ends up in git.

| Path | Content |
|---|---|
| `tickets/KEY.md` | Plan: what the ticket is about, problem, solution, repo and files, open questions |
| `tickets/KEY.notes.md` | Your notes and decisions, dated, one line each. Overrides the ticket text. Special forms: `repo: <path>`, `base: <branch>`, `branch: <branch>` |
| `tickets/KEY.done.md` | Coder report: what changed, tests run |
| `tickets/KEY.review.md` | Reviewer verdict `OK` or `FIX` with open items |
| `tickets/repos.md` | Known local clones, one per line, so no agent has to guess a repo |
| `tickets/snapshot.json` | Last ticket state, used by `sync` to report what changed |
| `briefs/YYYY-MM-DD.md` | Daily brief: changes since last sync, ticket table, open questions |
| `wiki/` | Project info, decisions and incoming requests that outlive a ticket. Markdown, one topic per file. No time tracking, no credentials, no personal data |

Keep it out of git on purpose: back it up with your own means if you need history.
