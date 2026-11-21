---
name: aoa-report
description: Report a ticket's state back to the aoa hub - "/aoa-report KEY [note]". Run from any ticket session (any repo, worktree, host) after a milestone - implemented, pushed, stage, live, closed. Appends a dated entry to ~/Desktop/aoa/tickets/KEY.notes.md.
---

# /aoa-report KEY [note]

The hub (`~/Desktop/aoa`) manages tickets; work happens in per-ticket sessions. This skill is the only way a ticket session tells the hub what happened. Hub reads it in `/aoa-brief` and `/aoa-wiki ingest`.

## Steps
1. KEY missing → take it from the current branch name (`fix/KEY`, `feature/KEY`); still missing → ask.
2. Collect, only what applies:
   - Workdir, branch, last commit (`git log -1 --oneline`), uncommitted files (`git status --short`, names only), pushed or not, MR link.
   - What this session did: change in one or two lines, tests (command, pass/fail count).
   - Where it runs: local / stage / live, version or tag, date. A live run by the user counts; ask if unclear.
   - Jira comment posted (yes/no, one-line gist).
   - Open points and the next step for the hub, at most six words.
   - The user's `note` argument, verbatim.
3. Append to `~/Desktop/aoa/tickets/KEY.notes.md` (create if missing), never rewrite earlier lines:
   ```
   - YYYY-MM-DD: REPORT <state: implemented|pushed|stage|live|done|blocked>. <what>. Branch <b>, <commit>. Tests <x passed>. Next: <step>.
     Open: <points or none>.
   ```
4. Print the appended entry. Nothing else.

## Rules
- Only that one notes file. Never edit the hub's plan `tickets/KEY.md`, `wiki/`, `briefs/`, `.env`; the hub ingests.
- No personal data: names, e-mails, addresses, phone numbers from lists or DBs never go in. Person numbers and IDs are fine.
- No secrets, tokens, passwords, hostnames with credentials.
- Facts only; unknown → "unknown".
