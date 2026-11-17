---
name: aoa-session
description: Start a ticket in its own Claude session - "/aoa-session KEY". Prints the worktree one-liner and the first message for the new session. The hub session stays for management.
---

# /aoa-session KEY

Hub = this a-o-a session (brief, planning, notes, wiki, Slack/Tempo texts). Ticket work runs in its own session.

1. Repo: from `tickets/KEY.notes.md` `repo:` line or `tickets/KEY.md` "Repo and files". Unknown → stop: "Name the repo: /aoa-brief KEY: repo <path>". Never guess.
2. Base branch: `base:` note, else the repo's develop branch per `wiki/repos/<repo>.md`. `branch:` note → work on that branch, no new one. Existing clone whose branch contains KEY → reuse it.
3. Print two code blocks:
   - One-liner: `cd ~/work/<repo> && git worktree add ../<repo>-KEY -b <fix|feature>/KEY <base> && cd ../<repo>-KEY && claude`
   - First message:
     ```
     Ticket KEY "<title>". Plan: ~/Desktop/a-o-a/tickets/KEY.md, notes: ~/Desktop/a-o-a/tickets/KEY.notes.md (read both; hub CLAUDE.md rules apply). Jira: cd ~/Desktop/a-o-a && uv run main.py get KEY --json --comments. Fix test-first, never commit (I commit). Commit and MR text: one line, no body, no Co-Authored-By, no Claude mention, no TODO-N key (local only). After each milestone (implemented, pushed, stage, live, done) run /aoa-report KEY.
     ```
4. Append `- YYYY-MM-DD: session started in <workdir> on <branch>` to `tickets/KEY.notes.md`.

Never start coder/reviewer, never open the session yourself.
