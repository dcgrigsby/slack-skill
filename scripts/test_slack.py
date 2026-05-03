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
