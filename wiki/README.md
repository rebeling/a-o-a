# Wiki schema

This wiki is compiled and maintained by Claude. The sources stay untouched and remain the truth:
`tickets/` (plans, notes, reports), `briefs/`, Claude memory, the clones under `~/work`. The wiki is the
layer you read; when a page and a source disagree, the source wins and the page gets fixed.

## Layout
- `index.md` — every page with a one-line summary. Read first on every question.
- `log.md` — append-only, newest last: `## [YYYY-MM-DD] <type> | <key-or-slug> | <one line>`. Types: `ingest`, `decision`, `request`, `lint`.
- `tickets.md` — every ticket: state, repo, outcome.
- `connections.md` — who depends on whom, release order.
- `projects/<name>.md` — customer/project: systems, environments, people by work role, current state.
- `repos/<repo>.md` — path, remote, branches, tests, deploy, hosts, pitfalls.
- `howto/<topic>.md` — procedures that were done at least once and will be done again.
- `decisions/YYYY-MM-DD-<slug>.md` — who decided what, why, consequences.
- `requests/YYYY-MM-DD-<slug>.md` — asks that came in by Slack, mail or call.

Links are `[[path/page]]` without `.md` (Obsidian-compatible).

## Operations (`/aoa-wiki`)
- **Query** `/aoa-wiki <question>`: read `index.md`, then the pages it points to, answer with page links. If the wiki cannot answer, look in the sources, answer, and file the answer.
- **Ingest** `/aoa-wiki ingest [KEY|today]`: read new or changed sources, update the affected pages, add missing ones, update `index.md`, append to `log.md`. One source usually touches several pages.
- **Decision / request** `/aoa-wiki decision: <text>`, `/aoa-wiki request: <text>`: file one page, link it from the ticket row and the index.
- **Lint** `/aoa-wiki lint`: stale states, contradictions between pages, orphan pages, missing index lines, forbidden content. Report only; fix on the user's go.

## Never in the wiki
Time tracking, hours, Tempo. Passwords, tokens, keys, `.env` content. Private contact details (e-mail, phone, postal address, IBAN). Anything about end users or CRM contacts beyond a numeric ID. Names from a VIP list. Raw prompt or transcript text.

Allowed: colleagues and customer staff by name and work role, hostnames and internal IPs, commands.

## Placement rule
Facts go to the wiki. Rules for how Claude behaves stay in `CLAUDE.md` and memory.
