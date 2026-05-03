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
