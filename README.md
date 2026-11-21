# aoa — agent of agents

One hub you talk to. It sends specialised agents out to plan, build, review and ship Jira tickets, and reports back.
You decide at the gates; no agent starts on its own, and nothing is pushed, deployed or sent without your go.

## Quick start

Needs [Claude Code](https://docs.claude.com/en/docs/claude-code), [uv](https://docs.astral.sh/uv/) and a
[Jira Cloud API token](https://id.atlassian.com/manage-profile/security/api-tokens).

```sh
git clone https://github.com/rebeling/aoa.git ~/Desktop/aoa
cd ~/Desktop/aoa
cat > .env <<'EOF'
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
EOF
mkdir -p ~/.claude/skills && ln -s "$PWD/.claude/skills/aoa-report" ~/.claude/skills/aoa-report
claude
```

In Claude, type `/aoa-brief`. That is the start of every day.

Once, so agents never guess:
- `tickets/repos.md`: your local clones, one per line (key prefix, path, remote, what it is).
- `TIME-` in `CLAUDE.md` and the skills: the key prefix of your time-tracking buckets, which are skipped.
- "Known sites" in `.claude/agents/error-log.md`: server, docroot and clone per site, if you want `/aoa-error`.

`/aoa-report` and `/aoa-session` assume the hub lives at `~/Desktop/aoa`. Cloned elsewhere → change that path in
`.claude/skills/aoa-report/SKILL.md` and `.claude/skills/aoa-session/SKILL.md`.

## Workflow

### Morning: `/aoa-brief`

Syncs your Jira tickets, shows what changed since yesterday, qualifies every ticket and writes `briefs/YYYY-MM-DD.md`.
It plans nothing and starts nothing; it tells you what is next.

```
| Key    | Title                       | Status      | Prio | Qual      | Next step              |
|--------|-----------------------------|-------------|------|-----------|------------------------|
| TODO-3 | Speed up deploy             | —           | —    | —         | In progress (own session) |
| ABC-12 | Export fails for big orders | In Progress | High | REPORTED  | Test on stage          |
| ABC-15 | Add VAT field to invoice    | To Do       | High | READY     | Ready to implement     |
| ABC-17 | Newsletter per region       | To Do       | Med  | BLOCKED   | Clarify 2 questions    |
| XYZ-4  | Login loop on mobile        | To Do       | Med  | UNPLANNED | Plan it                |
```

| Qual | Meaning | You do |
|---|---|---|
| `UNPLANNED` | No plan file yet | `/aoa-ticket-planner KEY` |
| `NO-REPO` | Plan exists, no clone named | `/aoa-brief KEY: repo <path>` |
| `BLOCKED` | Open questions for the ticket writer | Answer: `/aoa-brief KEY: <answer>` |
| `READY` | Plan complete, repo known | `/aoa-work KEY` or `/aoa-session KEY` |
| `REPORTED` | A ticket session reported a milestone | Next step comes from that report |
| `FEEDBACK` | Implemented and reviewed OK | Wait for stage test or ticket writer |

Below the table the brief lists the open questions and every running session with its `claude --resume <id>` line.

Talk to the hub in plain words during the day: "done ABC-12", "ABC-17 next week", "new todo: check backups".
Work without a Jira ticket becomes `TODO-1`, `TODO-2`, … in the brief. These keys stay local: never in commits,
merge requests, pushed branch names or Jira comments. Run `/aoa-brief` again any time to refresh.

### Plan, then work

1. `/aoa-ticket-planner KEY` writes `tickets/KEY.md`: what, problem, solution, repo and files, open questions.
2. Decisions and answers go in with `/aoa-brief KEY: <note>`; they override the ticket text and re-plan it.
3. Then either:
   - `/aoa-work KEY`: coder implements test-first in a git worktree, reviewer checks against the plan, max two rounds; or
   - `/aoa-session KEY`: worktree one-liner plus first message for a separate Claude session that you drive yourself.
4. In the ticket session, after each milestone (implemented, pushed, stage, live): `/aoa-report KEY`. The next brief
   shows it as `REPORTED` with its next step.
5. You commit, push and deploy. Nothing is committed by an agent.

### Hub and ticket sessions

Keep one Claude session in this folder as the hub: brief, planning, notes, wiki. Each ticket runs in its own session
and worktree and reports back with `/aoa-report`. The hub stays small and you can switch between tickets without
losing context.

### On demand

| Command | What it does |
|---|---|
| `/aoa-error <pasted log>` | `error-log` agent reads the server logs read-only and the code, writes cause and suggested fix to `errors/<slug>.md`. `/aoa-error list`, `/aoa-error fixed <slug>`. Never fixes. |
| `/aoa-wiki <question>` | Answers from the wiki. Also `ingest [KEY\|today]`, `decision: ...`, `request: ...`, `lint`. Schema: `wiki/README.md`. |
| `/aoa-brief tempo` | Brief plus time entries; expects a `reporter` agent of your own (not in this repo). |

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
| librarian | Keeps the wiki current: query, ingest, lint (`/aoa-wiki`, skill for now) | partly |
| scout | Maps where work sits: folder, branch, uncommitted and unpushed work per ticket | planned |
| watcher | Reads pipelines and merge requests, reports red jobs and stuck MRs | planned |
| releaser | Compares develop, stage and main across connected repos, prepares merges and release notes | planned |
| verifier | Checks stage or live read-only after a deploy against what the release claims | planned |
| fixer | Writes one-off data scripts in the dry-run / apply pattern, runs stage, hands over the live command | planned |
| tester | Clicks through a change in the browser on stage | planned |
| scribe | Turns the day's work into time entries, chat messages and ticket comments | planned |

Chains: a ticket runs planner → coder → reviewer today. The goal is to continue with
releaser → watcher → verifier → scribe → librarian, stopping at every gate.

## Knowledge base

The hub keeps what it learns as plain markdown next to the code. It is local only: `.gitignore` excludes the
content, the folders ship empty. Nothing about your tickets, customers or systems ends up in git.

| Path | Content |
|---|---|
| `tickets/KEY.md` | Plan: what the ticket is about, problem, solution, repo and files, open questions |
| `tickets/KEY.notes.md` | Your notes and decisions, dated, one line each; reports from ticket sessions. Overrides the ticket text. Special forms: `repo: <path>`, `base: <branch>`, `branch: <branch>` |
| `tickets/KEY.done.md` | Coder report: what changed, tests run |
| `tickets/KEY.review.md` | Reviewer verdict `OK` or `FIX` with open items |
| `tickets/repos.md` | Known local clones, one per line, so no agent has to guess a repo |
| `tickets/snapshot.json` | Last ticket state, used by `sync` to report what changed |
| `briefs/YYYY-MM-DD.md` | Daily brief: changes since last sync, ticket table, open questions, sessions |
| `errors/<slug>.md`, `errors/index.md` | Prod error reports from `/aoa-error`: cause, evidence, suggested fix, status |
| `wiki/` | Project info, decisions and incoming requests that outlive a ticket. Markdown, one topic per file. No time tracking, no credentials, no personal data |
| `wiki/connections.md` | Which repo calls or consumes which, project-to-repo map, release order. Agents read it before touching a repo that has a neighbour |

Keep it out of git on purpose: back it up with your own means if you need history.

## Jira CLI (under the hood)

The skills call `main.py`; you rarely need it directly. It reads Jira Cloud and can post a comment, nothing else.
Credentials come from `.env` next to `main.py` (git-ignored) or the same variables in your shell (shell wins).

```sh
uv run main.py mytickets [--json]          # open tickets assigned to you
uv run main.py get ABC-12 [ABC-13] [--json] [--comments]
uv run main.py sync [--json]               # new / gone / changed since last run; keeps tickets/snapshot.json
uv run main.py comment ABC-12 "text"       # the only write; "-" reads the text from stdin
uv run pytest                              # tests
```

`sync` fetches details only for tickets whose `updated` stamp changed, so a quiet morning costs one request.
`mytickets` uses `assignee = currentUser() AND statusCategory != Done ORDER BY priority ASC, updated DESC`.
Exit codes: `0` ok, `1` Jira/HTTP error, `2` missing env var.
