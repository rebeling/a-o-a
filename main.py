"""Read-only CLI for the user's Jira Cloud tickets.

Config via env vars JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, or a .env file
next to this script (shell env wins).

    uv run main.py mytickets [--json]
    uv run main.py get KEY [KEY...] [--json] [--comments]
    uv run main.py sync [--json] [--snapshot PATH]
    uv run main.py comment KEY "text"      # the only write; "-" reads text from stdin
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlencode
from urllib.request import urlopen  # patched in tests

REQUIRED_ENV = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")
MY_TICKETS_JQL = (
    "assignee = currentUser() AND statusCategory != Done "
    "ORDER BY priority ASC, updated DESC"
)
LIST_FIELDS = "summary,status,priority,updated"
ISSUE_FIELDS = "summary,status,priority,issuetype,description,labels"


class CliError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


def load_dotenv(path, env):
    """Read KEY=VALUE lines from path into env. Existing env values win."""
    if not Path(path).is_file():
        return
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env.setdefault(key.strip(), value.strip().strip("'\""))


def load_config(env):
    missing = [k for k in REQUIRED_ENV if not env.get(k)]
    if missing:
        raise CliError(f"Missing env var(s): {', '.join(missing)}", 2)
    return {
        "base_url": env["JIRA_BASE_URL"].rstrip("/"),
        "email": env["JIRA_EMAIL"],
        "token": env["JIRA_API_TOKEN"],
    }


def request(cfg, path, params, body=None):
    url = f"{cfg['base_url']}{path}" + (f"?{urlencode(params)}" if params else "")
    creds = base64.b64encode(f"{cfg['email']}:{cfg['token']}".encode()).decode()
    headers = {"Authorization": f"Basic {creds}", "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, headers=headers, data=data, method="POST" if data else "GET")
    try:
        with urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            messages = json.load(e).get("errorMessages", [])
        except (ValueError, AttributeError):
            messages = []
        detail = "; ".join(messages) or e.reason
        raise CliError(f"HTTP {e.code}: {detail}", 1) from e
    except urllib.error.URLError as e:
        raise CliError(f"Connection failed: {e.reason}", 1) from e


def name(field):
    return field["name"] if field else ""


def browse_url(cfg, key):
    return f"{cfg['base_url']}/browse/{key}"


def my_tickets(cfg):
    rows = []
    params = {"jql": MY_TICKETS_JQL, "fields": LIST_FIELDS, "maxResults": 100}
    while True:
        page = request(cfg, "/rest/api/2/search/jql", params)
        for it in page.get("issues", []):
            f = it["fields"]
            rows.append({
                "key": it["key"],
                "status": name(f.get("status")),
                "priority": name(f.get("priority")),
                "summary": f.get("summary") or "",
                "updated": f.get("updated") or "",
                "url": browse_url(cfg, it["key"]),
            })
        token = page.get("nextPageToken")
        if not token:
            return rows
        params["nextPageToken"] = token


def get_comments(cfg, key):
    page = request(cfg, f"/rest/api/2/issue/{key}/comment", {"orderBy": "created"})
    return [{
        "id": c.get("id"),
        "author": (c.get("author") or {}).get("displayName") or "",
        "created": c.get("created") or "",
        "body": c.get("body") or "",
    } for c in page.get("comments", [])]


def get_issue(cfg, key, comments=False):
    it = request(cfg, f"/rest/api/2/issue/{key}", {"fields": ISSUE_FIELDS})
    f = it["fields"]
    issue = {
        "key": it["key"],
        "type": name(f.get("issuetype")),
        "status": name(f.get("status")),
        "priority": name(f.get("priority")),
        "labels": f.get("labels") or [],
        "summary": f.get("summary") or "",
        "description": f.get("description") or "",
        "url": browse_url(cfg, it["key"]),
    }
    if comments:
        issue["comments"] = get_comments(cfg, key)
    return issue


DIFF_FIELDS = ("summary", "status", "priority", "type", "labels", "description")


def sync(cfg, snapshot_path):
    """Compare current tickets with the stored snapshot; refresh it; return the diff."""
    path = Path(snapshot_path)
    old = json.loads(path.read_text()) if path.is_file() else {}
    current = {r["key"]: r for r in my_tickets(cfg)}
    diff = {"new": [], "gone": sorted(k for k in old if k not in current),
            "changed": [], "unchanged": []}
    new = {}
    for key, row in current.items():
        prev = old.get(key)
        if prev and prev.get("updated") == row["updated"]:
            new[key] = prev
            diff["unchanged"].append(key)
            continue
        detail = get_issue(cfg, key)
        detail["updated"] = row["updated"]
        new[key] = detail
        if prev is None:
            diff["new"].append(key)
        else:
            fields = {f: [prev[f], detail.get(f)] for f in DIFF_FIELDS
                      if f in prev and prev[f] != detail.get(f)}
            if fields:
                diff["changed"].append({"key": key, "fields": fields})
            else:
                diff["unchanged"].append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(new, indent=2, ensure_ascii=False))
    return diff


def format_sync(diff):
    lines = []
    if diff["new"]:
        lines.append("New: " + ", ".join(diff["new"]))
    if diff["gone"]:
        lines.append("Gone: " + ", ".join(diff["gone"]))
    for ch in diff["changed"]:
        for field, (a, b) in ch["fields"].items():
            if field == "description":
                lines.append(f"{ch['key']} description changed")
            else:
                lines.append(f"{ch['key']} {field}: {a} -> {b}")
    return "\n".join(lines) if lines else "Nothing changed."


def add_comment(cfg, key, text):
    if text == "-":
        text = sys.stdin.read()
    if not text.strip():
        raise CliError("Empty comment, nothing posted.", 2)
    resp = request(cfg, f"/rest/api/2/issue/{key}/comment", None, {"body": text})
    return f"Comment {resp.get('id', '?')} posted to {key}: {browse_url(cfg, key)}"


def format_table(rows):
    if not rows:
        return "No open tickets."
    cols = ("key", "status", "priority", "summary")
    widths = {c: max(len(c), *(len(r[c]) for r in rows)) for c in cols[:-1]}
    def line(r):
        return "  ".join(r[c].ljust(widths[c]) for c in cols[:-1]) + "  " + r["summary"]
    header = {c: c.upper() for c in cols}
    return "\n".join([line(header)] + [line(r) for r in rows])


def format_issue(i):
    return "\n".join([
        f"# {i['key']}: {i['summary']}",
        f"Type: {i['type']}",
        f"Status: {i['status']}",
        f"Priority: {i['priority']}",
        f"Labels: {', '.join(i['labels'])}",
        f"URL: {i['url']}",
        "",
        i["description"],
    ] + [
        f"\n## {c['author']} ({c['created'][:16].replace('T', ' ')}, #{c['id']})\n{c['body']}"
        for c in i.get("comments", [])
    ])


def main(argv=None, env=None):
    if env is None:
        env = dict(os.environ)
        load_dotenv(Path(__file__).with_name(".env"), env)
    parser = argparse.ArgumentParser(description="Fetch Jira tickets.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("mytickets", help="open tickets assigned to me")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("get", help="full details for ticket keys")
    p.add_argument("keys", nargs="+")
    p.add_argument("--json", action="store_true")
    p.add_argument("--comments", action="store_true", help="include the comment thread")
    p = sub.add_parser("comment", help="post a comment to a ticket (the only write)")
    p.add_argument("key")
    p.add_argument("text", help='comment text, or "-" to read from stdin')
    p = sub.add_parser("sync", help="diff my tickets against the stored snapshot")
    p.add_argument("--json", action="store_true")
    p.add_argument("--snapshot", default=str(Path(__file__).with_name("tickets") / "snapshot.json"))
    args = parser.parse_args(argv)

    try:
        cfg = load_config(env)
        if args.cmd == "mytickets":
            rows = my_tickets(cfg)
            print(json.dumps(rows, indent=2) if args.json else format_table(rows))
        elif args.cmd == "get":
            issues = [get_issue(cfg, k, comments=args.comments) for k in args.keys]
            print(json.dumps(issues, indent=2) if args.json
                  else "\n\n".join(format_issue(i) for i in issues))
        elif args.cmd == "comment":
            print(add_comment(cfg, args.key, args.text))
        else:
            diff = sync(cfg, args.snapshot)
            print(json.dumps(diff, indent=2) if args.json else format_sync(diff))
    except CliError as e:
        print(e, file=sys.stderr)
        return e.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
