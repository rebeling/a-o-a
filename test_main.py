import io
import json
import urllib.error
from urllib.parse import parse_qs, urlparse

import pytest

import main

ENV = {
    "JIRA_BASE_URL": "https://acme.atlassian.net",
    "JIRA_EMAIL": "me@acme.com",
    "JIRA_API_TOKEN": "tok",
}


class FakeHTTP:
    """Replaces main.urlopen. Serves queued JSON bodies, records requests."""

    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        body = self.bodies.pop(0)
        if isinstance(body, Exception):
            raise body
        return io.BytesIO(json.dumps(body).encode())


def http_error(status, body):
    return urllib.error.HTTPError(
        "https://acme.atlassian.net/x", status, "err", {}, io.BytesIO(json.dumps(body).encode())
    )


def issue(key, summary="S", status="To Do", priority="High", itype="Task", desc="D", labels=()):
    return {
        "key": key,
        "fields": {
            "summary": summary,
            "status": {"name": status},
            "priority": {"name": priority},
            "issuetype": {"name": itype},
            "description": desc,
            "labels": list(labels),
        },
    }


@pytest.fixture
def fake(monkeypatch):
    def install(*bodies):
        f = FakeHTTP(bodies)
        monkeypatch.setattr(main, "urlopen", f)
        return f
    return install


# --- config ---------------------------------------------------------------

def test_missing_env_var_exits_2_with_message(capsys):
    env = dict(ENV)
    del env["JIRA_API_TOKEN"]
    assert main.main(["mytickets"], env) == 2
    assert "JIRA_API_TOKEN" in capsys.readouterr().err


# --- request plumbing -----------------------------------------------------

def test_request_uses_basic_auth_and_json_accept(fake):
    f = fake({"issues": [], "isLast": True})
    main.main(["mytickets"], ENV)
    req = f.requests[0]
    assert req.get_header("Authorization") == "Basic bWVAYWNtZS5jb206dG9r"
    assert req.get_header("Accept") == "application/json"


def test_http_error_prints_jira_messages_and_exits_1(fake, capsys):
    fake(http_error(401, {"errorMessages": ["Unauthorized", "Bad token"]}))
    assert main.main(["mytickets"], ENV) == 1
    err = capsys.readouterr().err
    assert "HTTP 401" in err and "Unauthorized" in err and "Bad token" in err


# --- mytickets ------------------------------------------------------------

def test_mytickets_queries_open_issues_assigned_to_me(fake):
    f = fake({"issues": [], "isLast": True})
    main.main(["mytickets"], ENV)
    url = urlparse(f.requests[0].full_url)
    assert url.path == "/rest/api/2/search/jql"
    q = parse_qs(url.query)
    assert q["jql"] == [
        "assignee = currentUser() AND statusCategory != Done ORDER BY priority ASC, updated DESC"
    ]
    assert q["fields"] == ["summary,status,priority,updated"]


def test_mytickets_follows_next_page_token(fake):
    f = fake(
        {"issues": [issue("A-1")], "nextPageToken": "p2"},
        {"issues": [issue("A-2")], "isLast": True},
    )
    main.main(["mytickets", "--json"], ENV)
    assert len(f.requests) == 2
    assert parse_qs(urlparse(f.requests[1].full_url).query)["nextPageToken"] == ["p2"]


def test_mytickets_json_output(fake, capsys):
    fake({"issues": [issue("A-1", "Fix login", "In Progress", "High")], "isLast": True})
    main.main(["mytickets", "--json"], ENV)
    assert json.loads(capsys.readouterr().out) == [
        {
            "key": "A-1",
            "status": "In Progress",
            "priority": "High",
            "summary": "Fix login",
            "updated": "",
            "url": "https://acme.atlassian.net/browse/A-1",
        }
    ]


def test_mytickets_table_output(fake, capsys):
    fake({"issues": [issue("A-1", "Fix login", "In Progress", "High"),
                     issue("A-22", "Add tests", "To Do", "Low")], "isLast": True})
    main.main(["mytickets"], ENV)
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["KEY", "STATUS", "PRIORITY", "SUMMARY"]
    assert lines[1].startswith("A-1 ") and lines[1].endswith("Fix login")
    assert lines[2].startswith("A-22") and lines[2].endswith("Add tests")


def test_mytickets_empty_prints_notice(fake, capsys):
    fake({"issues": [], "isLast": True})
    main.main(["mytickets"], ENV)
    assert "No open tickets" in capsys.readouterr().out


# --- get ------------------------------------------------------------------

def test_get_fetches_each_key_with_fields(fake):
    f = fake(issue("A-1"), issue("B-2"))
    main.main(["get", "A-1", "B-2"], ENV)
    paths = [urlparse(r.full_url).path for r in f.requests]
    assert paths == ["/rest/api/2/issue/A-1", "/rest/api/2/issue/B-2"]
    q = parse_qs(urlparse(f.requests[0].full_url).query)
    assert q["fields"] == ["summary,status,priority,issuetype,description,labels"]


def test_get_json_output(fake, capsys):
    fake(issue("A-1", "Fix login", "To Do", "High", "Bug", "Steps...", ["auth"]))
    main.main(["get", "A-1", "--json"], ENV)
    assert json.loads(capsys.readouterr().out) == [
        {
            "key": "A-1",
            "type": "Bug",
            "status": "To Do",
            "priority": "High",
            "labels": ["auth"],
            "summary": "Fix login",
            "description": "Steps...",
            "url": "https://acme.atlassian.net/browse/A-1",
        }
    ]


def test_get_markdown_output(fake, capsys):
    fake(issue("A-1", "Fix login", "To Do", "High", "Bug", "Steps...", ["auth"]))
    main.main(["get", "A-1"], ENV)
    out = capsys.readouterr().out
    assert out.startswith("# A-1: Fix login")
    assert "Type: Bug" in out and "Status: To Do" in out and "Priority: High" in out
    assert "Labels: auth" in out
    assert "https://acme.atlassian.net/browse/A-1" in out
    assert "Steps..." in out


def test_get_comments_adds_thread(fake, capsys):
    thread = {"comments": [
        {"id": "7", "author": {"displayName": "Ann"}, "created": "2026-10-14T09:00:00.000+0200", "body": "Answer 1"},
    ]}
    f = fake(issue("A-1"), thread)
    main.main(["get", "A-1", "--comments", "--json"], ENV)
    paths = [urlparse(r.full_url).path for r in f.requests]
    assert paths == ["/rest/api/2/issue/A-1", "/rest/api/2/issue/A-1/comment"]
    out = json.loads(capsys.readouterr().out)[0]
    assert out["comments"] == [{"id": "7", "author": "Ann", "created": "2026-10-14T09:00:00.000+0200", "body": "Answer 1"}]


def test_get_comments_markdown_lists_each_comment(fake, capsys):
    thread = {"comments": [{"id": "7", "author": {"displayName": "Ann"}, "created": "2026-10-14T09:00:00.000+0200", "body": "Answer 1"}]}
    fake(issue("A-1"), thread)
    main.main(["get", "A-1", "--comments"], ENV)
    out = capsys.readouterr().out
    assert "## Ann (2026-10-14 09:00, #7)" in out and "Answer 1" in out


def test_get_without_comments_flag_makes_no_comment_request(fake, capsys):
    f = fake(issue("A-1"))
    main.main(["get", "A-1", "--json"], ENV)
    assert len(f.requests) == 1
    assert "comments" not in json.loads(capsys.readouterr().out)[0]


def test_get_handles_null_description_and_priority(fake, capsys):
    body = issue("A-1")
    body["fields"]["description"] = None
    body["fields"]["priority"] = None
    fake(body)
    main.main(["get", "A-1", "--json"], ENV)
    data = json.loads(capsys.readouterr().out)[0]
    assert data["description"] == ""
    assert data["priority"] == ""


def test_network_error_prints_reason_and_exits_1(fake, capsys):
    fake(urllib.error.URLError("nodename nor servname provided"))
    assert main.main(["mytickets"], ENV) == 1
    err = capsys.readouterr().err
    assert "nodename nor servname" in err and "Traceback" not in err


# --- .env -----------------------------------------------------------------

def test_load_dotenv_fills_missing_vars_without_overriding(tmp_path):
    (tmp_path / ".env").write_text(
        "# comment\nJIRA_BASE_URL=https://dotenv.atlassian.net\n"
        "JIRA_EMAIL='quoted@acme.com'\n\nJIRA_API_TOKEN=\"t\"\n"
    )
    env = {"JIRA_EMAIL": "shell@acme.com"}
    main.load_dotenv(tmp_path / ".env", env)
    assert env == {
        "JIRA_BASE_URL": "https://dotenv.atlassian.net",
        "JIRA_EMAIL": "shell@acme.com",
        "JIRA_API_TOKEN": "t",
    }


def test_load_dotenv_missing_file_is_noop(tmp_path):
    env = {}
    main.load_dotenv(tmp_path / ".env", env)
    assert env == {}


def test_mytickets_includes_updated_timestamp(fake, capsys):
    body = issue("A-1")
    body["fields"]["updated"] = "2026-10-11T09:30:00.000+0200"
    fake({"issues": [body], "isLast": True})
    main.main(["mytickets", "--json"], ENV)
    row = json.loads(capsys.readouterr().out)[0]
    assert row["updated"] == "2026-10-11T09:30:00.000+0200"


def test_mytickets_requests_updated_field(fake):
    f = fake({"issues": [], "isLast": True})
    main.main(["mytickets"], ENV)
    q = parse_qs(urlparse(f.requests[0].full_url).query)
    assert q["fields"] == ["summary,status,priority,updated"]


# --- sync -----------------------------------------------------------------

def search_page(*issues):
    return {"issues": list(issues), "isLast": True}


def listed(key, status="To Do", updated="2026-10-10T10:00:00.000+0200", summary="S"):
    it = issue(key, summary=summary, status=status)
    it["fields"]["updated"] = updated
    return it


def detailed(key, status="To Do", updated="2026-10-10T10:00:00.000+0200", desc="D", summary="S"):
    it = issue(key, summary=summary, status=status, desc=desc)
    it["fields"]["updated"] = updated
    return it


def test_sync_first_run_reports_all_new_and_writes_snapshot(fake, capsys, tmp_path):
    snap = tmp_path / "snapshot.json"
    fake(search_page(listed("A-1")), detailed("A-1"))
    assert main.main(["sync", "--snapshot", str(snap), "--json"], ENV) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["new"] == ["A-1"] and out["changed"] == [] and out["gone"] == []
    stored = json.loads(snap.read_text())
    assert stored["A-1"]["description"] == "D"
    assert stored["A-1"]["updated"] == "2026-10-10T10:00:00.000+0200"


def test_sync_unchanged_fetches_no_details(fake, capsys, tmp_path):
    snap = tmp_path / "snapshot.json"
    snap.write_text(json.dumps({"A-1": {"key": "A-1", "status": "To Do", "summary": "S",
                                        "updated": "2026-10-10T10:00:00.000+0200"}}))
    f = fake(search_page(listed("A-1")))
    main.main(["sync", "--snapshot", str(snap), "--json"], ENV)
    assert len(f.requests) == 1
    out = json.loads(capsys.readouterr().out)
    assert out == {"new": [], "gone": [], "changed": [], "unchanged": ["A-1"]}


def test_sync_reports_changed_fields_with_old_and_new(fake, capsys, tmp_path):
    snap = tmp_path / "snapshot.json"
    snap.write_text(json.dumps({"A-1": {"key": "A-1", "status": "To Do", "summary": "S",
                                        "description": "D", "priority": "High",
                                        "updated": "2026-10-10T10:00:00.000+0200"}}))
    fake(search_page(listed("A-1", status="In Progress", updated="2026-10-12T09:00:00.000+0200")),
         detailed("A-1", status="In Progress", updated="2026-10-12T09:00:00.000+0200", desc="D2"))
    main.main(["sync", "--snapshot", str(snap), "--json"], ENV)
    out = json.loads(capsys.readouterr().out)
    assert out["changed"] == [{
        "key": "A-1",
        "fields": {"status": ["To Do", "In Progress"], "description": ["D", "D2"]},
    }]
    assert json.loads(snap.read_text())["A-1"]["status"] == "In Progress"


def test_sync_reports_gone_and_drops_from_snapshot(fake, capsys, tmp_path):
    snap = tmp_path / "snapshot.json"
    snap.write_text(json.dumps({"A-1": {"key": "A-1", "updated": "x"}}))
    fake(search_page())
    main.main(["sync", "--snapshot", str(snap), "--json"], ENV)
    assert json.loads(capsys.readouterr().out)["gone"] == ["A-1"]
    assert json.loads(snap.read_text()) == {}


def test_sync_text_output(fake, capsys, tmp_path):
    snap = tmp_path / "snapshot.json"
    snap.write_text(json.dumps({"A-1": {"key": "A-1", "status": "To Do", "summary": "S",
                                        "updated": "2026-10-10T10:00:00.000+0200"},
                                "B-2": {"key": "B-2", "updated": "x"}}))
    fake(search_page(listed("A-1", status="Done", updated="2026-10-12T09:00:00.000+0200"),
                     listed("C-3")),
         detailed("A-1", status="Done", updated="2026-10-12T09:00:00.000+0200"),
         detailed("C-3"))
    main.main(["sync", "--snapshot", str(snap)], ENV)
    out = capsys.readouterr().out
    assert "New: C-3" in out
    assert "Gone: B-2" in out
    assert "A-1 status: To Do -> Done" in out


def test_sync_text_output_nothing_changed(fake, capsys, tmp_path):
    snap = tmp_path / "snapshot.json"
    snap.write_text(json.dumps({"A-1": {"key": "A-1", "updated": "2026-10-10T10:00:00.000+0200"}}))
    fake(search_page(listed("A-1")))
    main.main(["sync", "--snapshot", str(snap)], ENV)
    assert capsys.readouterr().out.strip() == "Nothing changed."


# --- comment --------------------------------------------------------------

def test_comment_posts_body_to_issue(fake, capsys):
    f = fake({"id": "10001"})
    assert main.main(["comment", "A-1", "Hallo\nWelt"], ENV) == 0
    req = f.requests[0]
    assert req.get_method() == "POST"
    assert urlparse(req.full_url).path == "/rest/api/2/issue/A-1/comment"
    assert req.get_header("Content-type") == "application/json"
    assert json.loads(req.data) == {"body": "Hallo\nWelt"}
    assert "A-1" in capsys.readouterr().out


def test_comment_reads_body_from_stdin_when_dash(fake, monkeypatch):
    f = fake({"id": "1"})
    monkeypatch.setattr("sys.stdin", io.StringIO("from stdin"))
    main.main(["comment", "A-1", "-"], ENV)
    assert json.loads(f.requests[0].data) == {"body": "from stdin"}


def test_comment_refuses_empty_body(fake, capsys):
    f = fake({"id": "1"})
    assert main.main(["comment", "A-1", "  "], ENV) == 2
    assert f.requests == []
