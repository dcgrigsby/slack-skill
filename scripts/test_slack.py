#!/usr/bin/env python3
"""
Mechanical test suite for slack.py.

Runs the script as a subprocess and asserts stdout/stderr/exit code.
Uses two env-var hooks honored by slack.py:

  SLACK_SKILL_CONFIG          override config file path
  SLACK_SKILL_TEST_RESPONSES  override HTTP layer with FIFO canned responses

Run:
  python3 scripts/test_slack.py

Exits 0 if all tests pass, 1 otherwise.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).parent / "slack.py"
PASS = 0
FAIL = 0
FAILURES: list[str] = []


def run(*args: str, env: dict | None = None) -> tuple[int, str, str]:
    full_env = {**os.environ, **(env or {})}
    p = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=full_env,
    )
    return p.returncode, p.stdout, p.stderr


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="slack-test-"))


def make_env(tmpdir: Path, *, responses: list | None = None) -> dict:
    env = {"SLACK_SKILL_CONFIG": str(tmpdir / "config.json")}
    if responses is not None:
        rp = tmpdir / "responses.json"
        rp.write_text(json.dumps(responses))
        env["SLACK_SKILL_TEST_RESPONSES"] = str(rp)
    return env


def case(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: {detail}")
        print(f"  FAIL  {name}: {detail}")


# ---------------------------------------------------------------------- smoke


def test_help_prints_and_exits_2_with_no_args():
    print("\n[smoke] no-arg invocation prints help and exits 2")
    rc, out, err = run()
    case("returns 2", rc == 2, f"got {rc}, stderr={err!r}")
    case("prints usage on stderr", "usage:" in err.lower(), err[:200])


# ---------------------------------------------------------------- token utils


def test_token_validate_accepts_xoxp():
    print("\n[token] xoxp- prefix accepted")
    tmp = make_tmp()
    try:
        rc, _, err = run("auth", "add", "--workspace", "w", "--token", "xoxp-1-abc",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {}, "body":
                              {"ok": True, "user_id": "U1", "user": "alice",
                               "team_id": "T1", "team": "Acme"}},
                         ]))
        case("xoxp- accepted", rc == 0, f"rc={rc} stderr={err!r}")
    finally:
        shutil.rmtree(tmp)


def test_token_validate_rejects_xoxb():
    print("\n[token] xoxb- prefix rejected")
    tmp = make_tmp()
    try:
        rc, _, err = run("auth", "add", "--workspace", "w", "--token", "xoxb-bot-abc",
                         env=make_env(tmp))
        case("returns 5", rc == 5, f"rc={rc}")
        case("explains User OAuth Token", "user oauth token" in err.lower() or "xoxp" in err.lower(),
             err[:200])
    finally:
        shutil.rmtree(tmp)


def test_token_mask_in_auth_list():
    print("\n[token] auth list masks tokens")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-secretvalue",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U1", "user": "alice",
                  "team_id": "T1", "team": "Acme"}},
            ]))
        rc, out, _ = run("auth", "list", env=make_env(tmp))
        case("returns 0", rc == 0)
        case("token not visible", "secretvalue" not in out, out)
        case("masked form shown", "xoxp-***" in out or "xoxp-..." in out, out)
    finally:
        shutil.rmtree(tmp)


# --------------------------------------------------------------------- config


def test_config_round_trip_via_auth_add_list():
    print("\n[config] auth add + auth list round trip")
    tmp = make_tmp()
    try:
        rc, _, err = run("auth", "add", "--workspace", "work", "--token", "xoxp-1-abc",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {}, "body":
                              {"ok": True, "user_id": "U1", "user": "alice",
                               "team_id": "T1", "team": "Acme"}},
                         ]))
        case("auth add returns 0", rc == 0, f"rc={rc} stderr={err!r}")
        cfg_path = tmp / "config.json"
        case("config.json exists", cfg_path.exists())
        cfg = json.loads(cfg_path.read_text())
        case("default set to 'work'", cfg.get("default") == "work", json.dumps(cfg))
        case("workspace token stored", cfg["workspaces"]["work"]["token"] == "xoxp-1-abc")
        case("workspace metadata stored",
             cfg["workspaces"]["work"].get("team_name") == "Acme")
    finally:
        shutil.rmtree(tmp)


def test_config_file_mode_is_0600():
    print("\n[config] file mode is 0600")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        cfg_path = tmp / "config.json"
        mode = cfg_path.stat().st_mode & 0o777
        case("mode is 0600", mode == 0o600, f"got {oct(mode)}")
    finally:
        shutil.rmtree(tmp)


def test_config_atomic_write_no_tmp_left_behind():
    print("\n[config] atomic write removes .tmp")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        case("no .tmp file", not (tmp / "config.json.tmp").exists())
    finally:
        shutil.rmtree(tmp)


# ----------------------------------------------------------------------- http


def test_http_form_encoding_via_call_smoke():
    """Verify call subcommand POSTs form-encoded params and returns the body.

    Uses canned responses; no real network. The fixture echoes a deterministic
    response so we can assert on stdout shape.
    """
    print("\n[http] form-encoded POST via call")
    tmp = make_tmp()
    try:
        # First: register a workspace so call can find a token.
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        # Then: a call.
        rc, out, err = run("call", "auth.test", "--workspace", "w",
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {}, "body":
                                {"ok": True, "user": "alice", "team": "Acme"}},
                           ]))
        case("returns 0", rc == 0, f"rc={rc} stderr={err!r}")
        body = json.loads(out)
        case("returns ok=true", body.get("ok") is True, out)
        case("returns echoed user", body.get("user") == "alice", out)
    finally:
        shutil.rmtree(tmp)


def test_http_nested_params_json_stringified():
    """Slack expects nested objects/arrays as JSON strings in form fields."""
    print("\n[http] nested params JSON-stringified")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, err = run("call", "chat.postMessage", "--workspace", "w",
                           "--params", '{"channel":"C1","blocks":[{"type":"section","text":{"type":"mrkdwn","text":"hi"}}]}',
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {}, "body": {"ok": True, "ts": "1.0"}},
                           ]))
        case("returns 0", rc == 0, f"rc={rc} stderr={err!r}")
    finally:
        shutil.rmtree(tmp)


def test_call_transport_error_exits_3():
    """A transport-layer failure should exit 3 with a redacted stderr message.

    Simulated by exhausting the test fixture: the http_post path raises
    TransportError when SLACK_SKILL_TEST_RESPONSES is set but empty,
    exercising the same except branch as a real urlopen failure.
    """
    print("\n[http] transport error exits 3")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, err = run("call", "auth.test", "--workspace", "w",
                           env=make_env(tmp, responses=[]))
        case("returns 3", rc == 3, f"rc={rc} stderr={err!r}")
        case("stderr names transport error", "transport error" in err.lower(), err[:200])
        case("stdout empty", out == "", repr(out))
        case("token not in stderr", "xoxp-x" not in err, err[:200])
    finally:
        shutil.rmtree(tmp)


# ------------------------------------------------------------- slack errors


def test_call_missing_scope_emits_hint():
    print("\n[errors] missing_scope produces curated hint")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, err = run("call", "conversations.history", "--workspace", "w",
                           "--params", '{"channel":"C1"}',
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {"x-oauth-scopes": "users:read"},
                                "body": {"ok": False, "error": "missing_scope",
                                         "needed": "channels:history",
                                         "provided": "users:read"}},
                           ]))
        case("returns 1", rc == 1, f"rc={rc}")
        body = json.loads(out)
        case("response on stdout", body.get("error") == "missing_scope", out)
        case("hint mentions reinstall", "reinstall" in err.lower(), err)
        case("mentions needed scope", "channels:history" in err, err)


    finally:
        shutil.rmtree(tmp)


def test_call_channel_not_found_emits_hint():
    print("\n[errors] channel_not_found hint")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, _, err = run("call", "conversations.history", "--workspace", "w",
                         "--params", '{"channel":"C999"}',
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {},
                              "body": {"ok": False, "error": "channel_not_found"}},
                         ]))
        case("returns 1", rc == 1)
        case("hint mentions conversations.list",
             "conversations.list" in err or "users.conversations" in err, err)
    finally:
        shutil.rmtree(tmp)


def test_auth_remove_clears_default_when_removing_default():
    print("\n[auth] remove default clears default")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w1", "--token", "xoxp-1",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U1", "user": "u1",
                  "team_id": "T1", "team": "T1Name"}},
            ]))
        run("auth", "add", "--workspace", "w2", "--token", "xoxp-2",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U2", "user": "u2",
                  "team_id": "T2", "team": "T2Name"}},
            ]))
        rc, _, err = run("auth", "remove", "--workspace", "w1",
                         env=make_env(tmp))
        case("remove returns 0", rc == 0, err)
        cfg = json.loads((tmp / "config.json").read_text())
        case("w1 gone", "w1" not in cfg["workspaces"])
        case("default cleared", not cfg.get("default"), json.dumps(cfg))
    finally:
        shutil.rmtree(tmp)


def test_auth_default_errors_on_unknown_workspace():
    print("\n[auth] default rejects unknown workspace")
    tmp = make_tmp()
    try:
        rc, _, err = run("auth", "default", "--workspace", "ghost",
                         env=make_env(tmp))
        case("returns 5", rc == 5)
        case("error mentions configured workspaces",
             "configured" in err.lower() or "ghost" in err, err)
    finally:
        shutil.rmtree(tmp)


def test_auth_test_reports_scopes_from_header():
    print("\n[auth] test reports scopes from x-oauth-scopes header")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "alice",
                  "team_id": "T", "team": "Acme"}},
            ]))
        rc, out, err = run("auth", "test", "--workspace", "w",
                           env=make_env(tmp, responses=[
                               {"status": 200,
                                "headers": {"x-oauth-scopes": "channels:read,chat:write,users:read"},
                                "body": {"ok": True, "user_id": "U", "user": "alice",
                                         "team_id": "T", "team": "Acme"}},
                           ]))
        case("returns 0", rc == 0, err)
        combined = out + err
        case("mentions channels:read", "channels:read" in combined, combined)
        case("mentions team", "Acme" in combined, combined)
    finally:
        shutil.rmtree(tmp)


# ----------------------------------------------------------------- pagination


def test_call_all_merges_pages():
    print("\n[paginate] --all merges multiple pages")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, err = run("call", "conversations.history", "--workspace", "w",
                           "--params", '{"channel":"C1"}', "--all",
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {},
                                "body": {"ok": True, "messages": [{"ts": "1"}, {"ts": "2"}],
                                         "response_metadata": {"next_cursor": "abc"}}},
                               {"status": 200, "headers": {},
                                "body": {"ok": True, "messages": [{"ts": "3"}],
                                         "response_metadata": {"next_cursor": ""}}},
                           ]))
        case("returns 0", rc == 0, err)
        body = json.loads(out)
        case("has items", "items" in body, out)
        case("merged 3 messages", len(body.get("items", [])) == 3, out)
        case("page_count is 2", body.get("page_count") == 2, out)
    finally:
        shutil.rmtree(tmp)


def test_call_all_respects_limit():
    print("\n[paginate] --limit truncates")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, _ = run("call", "conversations.history", "--workspace", "w",
                         "--params", '{"channel":"C1"}', "--all", "--limit", "2",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {},
                              "body": {"ok": True, "messages": [{"ts": "1"}, {"ts": "2"}, {"ts": "3"}],
                                       "response_metadata": {"next_cursor": "abc"}}},
                         ]))
        case("returns 0", rc == 0)
        body = json.loads(out)
        case("truncated to 2", len(body.get("items", [])) == 2, out)
    finally:
        shutil.rmtree(tmp)


def test_call_all_page_based_merges_pages():
    """Page-based pagination (paging.pages / paging.page) — regression guard
    for the silent-truncate-to-page-1 bug fixed in commit 2d5a07d."""
    print("\n[paginate] --all merges page-based responses (paging.pages)")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, err = run("call", "files.list", "--workspace", "w", "--all",
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {},
                                "body": {"ok": True,
                                         "files": [{"id": "F1"}, {"id": "F2"}],
                                         "paging": {"page": 1, "pages": 2,
                                                    "count": 2, "total": 3}}},
                               {"status": 200, "headers": {},
                                "body": {"ok": True,
                                         "files": [{"id": "F3"}],
                                         "paging": {"page": 2, "pages": 2,
                                                    "count": 1, "total": 3}}},
                           ]))
        case("returns 0", rc == 0, err)
        body = json.loads(out)
        case("has items", "items" in body, out)
        case("merged 3 files across 2 pages",
             len(body.get("items", [])) == 3, out)
        case("page_count is 2", body.get("page_count") == 2, out)
        case("preserved item identity",
             [it.get("id") for it in body.get("items", [])] == ["F1", "F2", "F3"],
             out)
    finally:
        shutil.rmtree(tmp)


def test_call_all_search_messages_merges_nested_matches():
    """search.messages keeps results at messages.matches and paging info at
    messages.paging — auto-pagination should walk the nested path."""
    print("\n[paginate] --all merges nested search.messages matches")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, err = run("call", "search.messages", "--workspace", "w",
                           "--params", '{"query":"deploy","count":2}', "--all",
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {},
                                "body": {"ok": True, "query": "deploy",
                                         "messages": {
                                             "total": 3,
                                             "paging": {"count": 2, "total": 3,
                                                        "page": 1, "pages": 2},
                                             "matches": [{"ts": "1", "text": "a"},
                                                         {"ts": "2", "text": "b"}],
                                         }}},
                               {"status": 200, "headers": {},
                                "body": {"ok": True, "query": "deploy",
                                         "messages": {
                                             "total": 3,
                                             "paging": {"count": 1, "total": 3,
                                                        "page": 2, "pages": 2},
                                             "matches": [{"ts": "3", "text": "c"}],
                                         }}},
                           ]))
        case("returns 0", rc == 0, err)
        body = json.loads(out)
        case("merged 3 matches across 2 pages",
             len(body.get("items", [])) == 3, out)
        case("page_count is 2", body.get("page_count") == 2, out)
        case("preserved match identity in order",
             [m.get("ts") for m in body.get("items", [])] == ["1", "2", "3"], out)
    finally:
        shutil.rmtree(tmp)


def test_call_all_search_all_rejects_ambiguous_shape():
    """search.all has both messages.matches and files.matches. The caller
    can't safely pick one, so --all should fail loud rather than guess."""
    print("\n[paginate] --all on ambiguous shape (search.all) errors")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, _, err = run("call", "search.all", "--workspace", "w",
                         "--params", '{"query":"deploy"}', "--all",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {},
                              "body": {"ok": True,
                                       "messages": {"matches": [{"ts": "1"}]},
                                       "files": {"matches": [{"id": "F1"}]}}},
                         ]))
        case("returns 2", rc == 2, f"rc={rc} stderr={err!r}")
        case("stderr explains ambiguity",
             "search.all" in err or "ambiguous" in err.lower(), err[:300])
    finally:
        shutil.rmtree(tmp)


# ----------------------------------------------------------------------- doctor


def test_doctor_reports_ok_for_healthy_workspace():
    print("\n[doctor] OK lines for python, config mode, and auth.test")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, err = run("doctor",
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {},
                                "body": {"ok": True}},
                           ]))
        case("returns 0", rc == 0, f"rc={rc} stderr={err!r}")
        case("python OK line", "OK    python" in out, out)
        case("config mode 0600 OK line",
             "OK    config" in out and "0600" in out, out)
        case("workspace auth.test OK line",
             "OK    w  auth.test" in out, out)
        case("no FAIL lines", "FAIL" not in out, out)
    finally:
        shutil.rmtree(tmp)


def test_doctor_reports_failure_on_auth_test_error():
    print("\n[doctor] returns 1 and surfaces error when auth.test fails")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, _ = run("doctor",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {},
                              "body": {"ok": False, "error": "token_revoked"}},
                         ]))
        case("returns 1", rc == 1, f"rc={rc}")
        case("FAIL line names workspace and error",
             "FAIL  w  token_revoked" in out, out)
    finally:
        shutil.rmtree(tmp)


# -------------------------------------------------------------------- resolve


def test_resolve_expands_user_label_inline():
    """<@U|alice> uses the inline label without an API call."""
    print("\n[resolve] inline user label")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, _ = run("call", "conversations.history", "--workspace", "w",
                         "--params", '{"channel":"C1"}', "--resolve",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {},
                              "body": {"ok": True, "messages": [
                                  {"text": "hi <@U07ABC|alice>"}]}},
                         ]))
        case("returns 0", rc == 0)
        body = json.loads(out)
        text = body["messages"][0]["text"]
        case("expanded to @alice", "@alice" in text and "<@" not in text, text)
    finally:
        shutil.rmtree(tmp)


def test_resolve_falls_back_on_lookup_failure():
    """Lookup failure → readable @U07ABC, rest of message intact."""
    print("\n[resolve] fallback on users.info failure")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, out, _ = run("call", "conversations.history", "--workspace", "w",
                         "--params", '{"channel":"C1"}', "--resolve",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {},
                              "body": {"ok": True, "messages": [{"text": "hi <@U07ABC>"}]}},
                             {"status": 200, "headers": {},
                              "body": {"ok": False, "error": "user_not_found"}},
                         ]))
        case("returns 0", rc == 0)
        body = json.loads(out)
        text = body["messages"][0]["text"]
        case("fell back to @U07ABC", "@U07ABC" in text, text)
    finally:
        shutil.rmtree(tmp)


# ----------------------------------------------------------------------- debug


def test_debug_logs_to_stderr_with_redaction():
    """--debug produces stderr lines and never reveals tokens."""
    print("\n[debug] stderr emits redacted log lines")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-supersecret",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, _, err = run("call", "auth.test", "--workspace", "w", "--debug",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {}, "body": {"ok": True}},
                         ]))
        case("returns 0", rc == 0, err)
        case("stderr non-empty", len(err.strip()) > 0)
        case("token never visible", "supersecret" not in err, err[:300])
        case("POST line present", "POST " in err, err[:300])
    finally:
        shutil.rmtree(tmp)


# ----------------------------------------------------------------------- upload


def test_upload_orchestrates_three_calls():
    """Happy path: getUploadURLExternal → PUT → completeUploadExternal.

    The fixture queue is consumed in order — three responses for the three
    HTTP calls — so passing in three fixtures and observing exit 0 confirms
    the orchestration ran end-to-end.
    """
    print("\n[upload] orchestrates the 3-call flow end-to-end")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        f = tmp / "hello.txt"
        f.write_text("hello world")
        rc, out, err = run("upload", "--workspace", "w",
                           "--file", str(f),
                           "--channel", "C0123",
                           "--title", "Greeting",
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {}, "body":
                                {"ok": True,
                                 "upload_url": "https://files.slack.com/upload/v1/abc?sig=xyz",
                                 "file_id": "F00001"}},
                               {"status": 200, "headers": {}, "body": {}},
                               {"status": 200, "headers": {}, "body":
                                {"ok": True,
                                 "files": [{"id": "F00001", "title": "Greeting"}]}},
                           ]))
        case("returns 0", rc == 0, f"rc={rc} stderr={err!r}")
        body = json.loads(out)
        case("ok=true", body.get("ok") is True, out)
        case("file_id propagated to complete response",
             body.get("files", [{}])[0].get("id") == "F00001", out)
    finally:
        shutil.rmtree(tmp)


def test_upload_rejects_missing_file():
    """A non-existent --file path is a usage error (exit 2). No HTTP at all."""
    print("\n[upload] missing --file path exits 2")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        rc, _, err = run("upload", "--workspace", "w",
                         "--file", str(tmp / "does-not-exist.txt"),
                         env=make_env(tmp))
        case("returns 2", rc == 2, f"rc={rc} stderr={err!r}")
        case("stderr names the path",
             "does-not-exist.txt" in err, err[:200])
    finally:
        shutil.rmtree(tmp)


def test_upload_step1_error_short_circuits():
    """If files.getUploadURLExternal returns ok:false, the PUT and
    completeUploadExternal calls must not happen — verified by passing
    only one fixture: a second http_post would exhaust it and raise."""
    print("\n[upload] step-1 error short-circuits the flow")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        f = tmp / "hello.txt"
        f.write_text("hi")
        rc, out, err = run("upload", "--workspace", "w", "--file", str(f),
                           env=make_env(tmp, responses=[
                               {"status": 200, "headers": {}, "body":
                                {"ok": False, "error": "missing_scope",
                                 "needed": "files:write", "provided": "chat:write"}},
                           ]))
        case("returns 1", rc == 1, f"rc={rc} stderr={err!r}")
        case("stderr names the scope hint",
             "files:write" in err, err[:300])
        body = json.loads(out)
        case("stdout carries the error body",
             body.get("error") == "missing_scope", out)
    finally:
        shutil.rmtree(tmp)


def test_upload_step2_3xx_treated_as_failure():
    """Regression guard: Slack rejects malformed uploads with a 302 redirect
    to https://slack.com instead of a 4xx. The earlier `status >= 400` check
    let that 302 through, after which step 3 (completeUploadExternal) returns
    ok with a phantom file — leaving an uploader who sees success but no
    actual file. The upload command must treat anything outside 2xx as a
    step-2 failure (exit 3) and never invoke step 3.

    The fixture queue gets two responses (auth.test was consumed by `auth
    add`, so the upload run's first fixture is step 1). If step 3 wrongly
    runs, it would pop a third fixture that doesn't exist and raise — making
    the test fail loud.
    """
    print("\n[upload] step-2 non-2xx exits 3 and short-circuits step 3")
    tmp = make_tmp()
    try:
        run("auth", "add", "--workspace", "w", "--token", "xoxp-x",
            env=make_env(tmp, responses=[
                {"status": 200, "headers": {}, "body":
                 {"ok": True, "user_id": "U", "user": "u",
                  "team_id": "T", "team": "Team"}},
            ]))
        f = tmp / "hello.txt"
        f.write_text("hi")
        rc, _, err = run("upload", "--workspace", "w",
                         "--file", str(f),
                         "--channel", "C0123",
                         env=make_env(tmp, responses=[
                             {"status": 200, "headers": {}, "body":
                              {"ok": True,
                               "upload_url": "https://files.slack.com/upload/v1/abc",
                               "file_id": "F00001"}},
                             {"status": 302, "headers": {}, "body": {}},
                         ]))
        case("returns 3", rc == 3, f"rc={rc} stderr={err!r}")
        case("stderr names the failure",
             "upload failed" in err, err[:200])
        case("status is in the message",
             "302" in err, err[:200])
    finally:
        shutil.rmtree(tmp)


# --------------------------------------------------------------------- runner


def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for t in tests:
        try:
            t()
        except Exception as e:  # noqa: BLE001
            case(t.__name__, False, f"raised {type(e).__name__}: {e}")
    print(f"\n{PASS} passed, {FAIL} failed")
    if FAIL:
        print("Failures:")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
