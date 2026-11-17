# a-o-a — agent of agents

One hub you talk to. It sends specialised agents out to plan, build, review and ship Jira tickets, and reports back.
You decide at the gates; no agent starts on its own, and nothing is pushed, deployed or sent without your go.

## Quick start

Needs [uv](https://docs.astral.sh/uv/), [Claude Code](https://docs.claude.com/en/docs/claude-code) and a Jira Cloud API token.

```sh
git clone https://github.com/rebeling/a-o-a.git ~/Desktop/a-o-a
cd ~/Desktop/a-o-a
cp /dev/null .env && chmod 600 .env       # then fill in the three JIRA_* lines (see Jira CLI below)
uv run main.py mytickets                  # check: your open tickets as a table
mkdir -p ~/.claude/skills && ln -s "$PWD/.claude/skills/aoa-report" ~/.claude/skills/aoa-report
claude                                    # then type /aoa-brief
```

The `aoa-report` link makes `/aoa-report` available in every repo, so ticket sessions can report back to the hub.
It writes to `~/Desktop/a-o-a/tickets/`; clone somewhere else → change that path in `.claude/skills/aoa-report/SKILL.md`
and `.claude/skills/aoa-session/SKILL.md`.

Then, once:
- list your local clones in `tickets/repos.md` (one per line: key prefix, path, remote, what it is), so no agent guesses a repo;
- change the time-tracking key prefix `TIME-` in `CLAUDE.md` and the skills to yours, or leave it;
- fill the "Known sites" table in `.claude/agents/error-log.md` if you want `/aoa-error`.

## Principles

- **Simple.** Plain markdown files, one small Python CLI, no dependencies beyond the standard library. Every agent has one job and a short brief.
- **Always the repo.** Every agent works in exactly one named repo and worktree. A repo is never guessed: it comes from your note (`repo: <path>`) or from a clone whose branch contains the ticket key.
- **Connections are known.** How repos and projects depend on each other is written down (`wiki/connections.md`: who calls whom, what must be released first) and every agent reads it before touching a repo that has a neighbour.
- **Knowledge stays.** What a ticket taught goes into the wiki, so the next agent does not start from zero.

## Agents

| Agent | Job | State |
|---|---|---|
| planner | Turns a ticket into a plan: problem, solution, repo and files, open questions | built |
| coder | Implements the plan test-first in a git worktree. Never commits | built |
| reviewer | Checks the diff against the plan, verdict OK or FIX | built |
| error-log | Reads a pasted prod error, the server logs (read-only) and the code; writes cause and suggested fix. Never fixes | built |
| scout | Maps where work sits: folder, branch, uncommitted and unpushed work per ticket | planned |
| watcher | Reads pipelines and merge requests, reports red jobs and stuck MRs | planned |
| releaser | Compares develop, stage and main across connected repos, prepares merges and release notes | planned |
| verifier | Checks stage or live read-only after a deploy against what the release claims | planned |
| fixer | Writes one-off data scripts in the dry-run / apply pattern, runs stage, hands over the live command | planned |
| tester | Clicks through a change in the browser on stage | planned |
| scribe | Turns the day's work into time entries, chat messages and ticket comments | planned |
| librarian | Keeps the wiki current: query, ingest, lint (`/aoa-wiki`, skill for now) | partly |

Chains: a ticket runs planner → coder → reviewer today. The goal is to continue with
releaser → watcher → verifier → scribe → librarian, stopping at every gate.

## Jira CLI

The CLI fetches your Jira Cloud tickets and can post a comment. Nothing else is written. Meant for you and for
agents that need ticket context.

### Setup

Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens
and put it in `.env` next to `main.py` (git-ignored), or export the same vars in
your shell (shell wins over `.env`):

```sh
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
```

### Usage

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

### Tests

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
| `/aoa-session KEY` | Prints the worktree one-liner and the first message to work a ticket in its own Claude session. |
| `/aoa-report KEY [note]` | Run inside a ticket session after a milestone (implemented, pushed, stage, live): appends a `REPORT` line to the hub's `tickets/KEY.notes.md`. |
| `/aoa-error <pasted log>` | `error-log` agent explains a prod error and writes `errors/<slug>.md`. `/aoa-error list`, `/aoa-error fixed <slug>`. |
| `/aoa-wiki <question>` | Answers from the wiki. Also `ingest [KEY\|today]`, `decision: ...`, `request: ...`, `lint`. Schema: `wiki/README.md`. |

### Hub and ticket sessions

Keep one Claude session in this folder as the hub: brief, planning, notes, wiki. Each ticket gets its own session in
its own worktree (`/aoa-session KEY`), which reports back with `/aoa-report`. The brief lists all sessions with their
`claude --resume <id>` line, so you can jump back into any of them.

Work without a Jira ticket goes into the brief as `TODO-1`, `TODO-2`, … (just tell the hub). These keys are local:
they never appear in commits, merge requests, pushed branch names or Jira comments.

Qualification in the brief: `UNPLANNED` (no plan), `READY`, `BLOCKED` (open questions), `NO-REPO` (no clone named),
`FEEDBACK` (reviewed OK, waiting), `REPORTED` (a ticket session reported; next step comes from that report).

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
| `briefs/YYYY-MM-DD.md` | Daily brief: changes since last sync, ticket table, open questions, sessions |
| `errors/<slug>.md`, `errors/index.md` | Prod error reports from `/aoa-error`: cause, evidence, suggested fix, status |
| `wiki/` | Project info, decisions and incoming requests that outlive a ticket. Markdown, one topic per file. No time tracking, no credentials, no personal data |
| `wiki/connections.md` | Which repo calls or consumes which, project-to-repo map, release order. Agents read it before touching a repo that has a neighbour |

Keep it out of git on purpose: back it up with your own means if you need history.
