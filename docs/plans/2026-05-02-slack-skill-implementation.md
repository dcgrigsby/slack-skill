# Slack Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `slack-skill` capability skill per the approved spec — a Python 3 stdlib-only CLI plus progressive-disclosure API docs — and ship to the existing public GitHub repo `dcgrigsby/slack-skill`.

**Architecture:** A portable skill folder. Single CLI at `scripts/slack.py` with `call`, `auth`, and `doctor` subcommands. Stdlib-only Python (`urllib`, `json`, `argparse`, `os`, `pathlib`). Config at `~/.config/slack-skill/config.json` (mode 0600). HTTP mocking for tests via `SLACK_SKILL_TEST_RESPONSES` env var pointing at a JSON file with FIFO canned responses. Tests run the script via subprocess and assert on stdout/stderr/exit code, mirroring `obsidian-skill/scripts/test_obsidian.py`.

**Tech Stack:** Python 3.9+ stdlib only. No external dependencies. Markdown for docs. YAML for the Slack app manifest.

**Spec reference:** [`docs/specs/2026-05-02-slack-skill-design.md`](../specs/2026-05-02-slack-skill-design.md)

**Pre-existing state:** Repo initialized and pushed to `github.com/dcgrigsby/slack-skill`. Initial commit contains `LICENSE`, `NOTICE`, `README.md` (placeholder), `.gitignore`, and the design spec. All work continues on `main` with frequent commits. Push at the end of each task that produces a commit.

**Reference implementations:**
- `slack2omnifocus/internal/slack/client.go:195-265` — the `FormatText` logic for entity-ref expansion (port to Python in Task 18).
- `obsidian-skill/scripts/test_obsidian.py` — test harness style (subprocess + temp config + custom case/PASS/FAIL).
- `obsidian-skill/scripts/obsidian.py` — single-file CLI structure to mirror.
- `omnifocus-skill/SKILL.md` — body structure and instructional tone for inline patterns.

---

## File Structure

| Path | Purpose | Status |
|---|---|---|
| `Makefile` | `make test` / `make package` / `make regen-reference` / `make clean` | Create |
| `.gitignore` | Add test artifacts | Modify |
| `README.md` | Full install + setup + safety README (replaces placeholder) | Modify |
| `SKILL.md` | Frontmatter + body with all inline patterns | Create |
| `scripts/slack.py` | The CLI (~700–900 lines; argparse + http + config + auth + call + doctor + resolver) | Create |
| `scripts/test_slack.py` | Mechanical test suite | Create |
| `scripts/regen_reference.py` | Fetch Slack OpenAPI v2 → emit `FULL-REFERENCE.md` | Create |
| `scripts/package_skill.py` | Build `.skill` bundle for distribution | Create |
| `docs/slack-app-manifest.yaml` | Paste-into-Slack manifest | Create |
| `docs/slack-api/CHEATSHEET.md` | Tier-2: compact API map | Create |
| `docs/slack-api/Conversations.md` | Tier-3: per-namespace doc | Create |
| `docs/slack-api/Chat.md` | Tier-3 | Create |
| `docs/slack-api/Reactions.md` | Tier-3 | Create |
| `docs/slack-api/Users.md` | Tier-3 | Create |
| `docs/slack-api/Search.md` | Tier-3 | Create |
| `docs/slack-api/Files.md` | Tier-3 | Create |
| `docs/slack-api/Pins-Stars-Bookmarks.md` | Tier-3 | Create |
| `docs/slack-api/FULL-REFERENCE.md` | Tier-4: generated from OpenAPI | Generate + commit |
| `evals/evals.json` | Behavioral evals | Create |

`scripts/slack.py` is one file by design (mirrors `obsidian.py`), organized into clearly-delimited sections via comment banners (`# ---- HTTP ----`, `# ---- config ----`, etc.).

---

## Conventions used throughout this plan

**Test invocation pattern.** All tests run `scripts/slack.py` as a subprocess. They use two env-var hooks the script honors:

- `SLACK_SKILL_CONFIG=<path>` — overrides the config file path (test points it at a temp file).
- `SLACK_SKILL_TEST_RESPONSES=<path>` — when set, the script consumes canned HTTP responses from this JSON file in FIFO order instead of making real HTTP calls. File format:
  ```json
  [
    {"status": 200, "headers": {"x-oauth-scopes": "channels:read,users:read"}, "body": {"ok": true, "user": "U01"}},
    {"status": 429, "headers": {"retry-after": "2"}, "body": {"ok": false, "error": "ratelimited"}}
  ]
  ```

These hooks are set at script startup and consulted in `_load_config()` and `_http_post()` respectively.

**Code organization in `scripts/slack.py`.** Sections (in order, separated by banner comments):
1. Imports + constants
2. Token utilities (validate, mask, redact)
3. Config (load, save, atomic write, mode enforcement)
4. HTTP transport (form encoding, POST, error mapping, retry, rate limit)
5. Slack API error interpretation (curated hints)
6. Entity-ref resolver (FormatText port)
7. Pagination loop
8. Subcommand handlers (call, auth-{add,list,remove,default,test}, doctor)
9. Argparse + main + dispatch

**Commit message style.** Conventional Commits, present tense, no scope prefix unless natural. Bodies are terse — explain WHY when non-obvious. Always include the Co-Authored-By footer.

**Frequent commits.** Every task ends with a commit. Push after each commit (`git push origin main`).

---

## Task 1: Repo scaffolding (Makefile, .gitignore, empty script shells)

**Files:**
- Create: `/Users/dan/slack-skill/Makefile`
- Create: `/Users/dan/slack-skill/scripts/slack.py` (skeleton)
- Create: `/Users/dan/slack-skill/scripts/test_slack.py` (skeleton)
- Modify: `/Users/dan/slack-skill/.gitignore`

- [ ] **Step 1: Create the scripts directory**

```bash
mkdir -p /Users/dan/slack-skill/scripts
```

- [ ] **Step 2: Write `Makefile`**

```makefile
.PHONY: help test package regen-reference clean

help:
	@echo "Targets:"
	@echo "  make test              - Run mechanical test suite"
	@echo "  make package           - Build .skill bundle for distribution"
	@echo "  make regen-reference   - Refresh docs/slack-api/FULL-REFERENCE.md from Slack's OpenAPI spec"
	@echo "  make clean             - Remove generated artifacts"

test:
	python3 scripts/test_slack.py

package:
	python3 scripts/package_skill.py .
	@echo ""
	@echo "Install via: npx skills add <repo> -g -a claude-code -a gemini-cli -a codex -a pi -y"

regen-reference:
	python3 scripts/regen_reference.py docs/slack-api/FULL-REFERENCE.md

clean:
	rm -f slack-skill.skill
	find . -name __pycache__ -type d -exec rm -rf {} +
	find . -name '*.pyc' -delete
```

- [ ] **Step 3: Update `.gitignore`**

Replace the existing file content with:

```
__pycache__/
*.pyc
*.skill
.test-tmp/
```

- [ ] **Step 4: Write `scripts/slack.py` skeleton**

```python
#!/usr/bin/env python3
"""
slack.py — bundled helper for the slack skill.

A thin Python 3 stdlib-only CLI that exposes the Slack Web API to
LLM-driven workflows via three subcommands:

  call    Invoke any Slack Web API method with form-encoded params.
  auth    Manage workspace tokens stored in ~/.config/slack-skill/config.json.
  doctor  End-to-end self-check.

See SKILL.md for usage patterns and docs/slack-api/ for API references.

Exit codes:
  0  success
  1  Slack API error (ok: false) — full response on stdout, summary on stderr
  2  usage error (bad args, malformed --params JSON)
  3  transport error (DNS / TCP / TLS / timeout)
  5  config / auth error (workspace not found, no token available)
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slack.py", description=__doc__.split("\n")[1])
    parser.add_argument("--version", action="version", version="slack.py 0.1.0")
    sub = parser.add_subparsers(dest="cmd", required=False)
    # Subcommands wired in later tasks.
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help(sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Make it executable:

```bash
chmod +x /Users/dan/slack-skill/scripts/slack.py
```

- [ ] **Step 5: Write `scripts/test_slack.py` skeleton**

```python
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
```

- [ ] **Step 6: Verify the skeleton runs**

```bash
cd /Users/dan/slack-skill && make test
```

Expected: `2 passed, 0 failed`. Exit 0.

- [ ] **Step 7: Commit**

```bash
git add Makefile .gitignore scripts/
git commit -m "$(cat <<'EOF'
Scaffold Makefile, .gitignore, slack.py and test_slack.py shells

Establishes the build/test contract before adding code. The CLI's
subcommand wiring and the test harness's smoke check are minimal but
exercise the full subprocess invocation path used by every later test.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 2: Token utilities (validate, mask, redact)

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

The masking helper is used by `auth list`, `--debug` logging, and error formatting. The validator is used by `auth add`. Build them first because everything else depends on them never leaking tokens.

- [ ] **Step 1: Write the failing tests in `test_slack.py`**

Insert after the smoke test:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
make test
```

Expected: at least 3 failures (auth subcommand not yet implemented).

- [ ] **Step 3: Implement token utilities in `slack.py`**

Replace the `slack.py` body with the skeleton plus this token-utilities section. Insert after the docstring and imports:

```python
import re

# ---- token utilities --------------------------------------------------------

TOKEN_RE = re.compile(r"xox[abporsuxd]-[A-Za-z0-9-]+")


def validate_user_token(token: str) -> None:
    """Raise ValueError unless token has the User OAuth Token shape."""
    if not token:
        raise ValueError("token is empty")
    if token.startswith("xoxb-"):
        raise ValueError(
            "this skill needs a User OAuth Token (xoxp-...), not a Bot Token (xoxb-...). "
            "Re-check the OAuth & Permissions page; the User OAuth Token is at the top."
        )
    if not token.startswith("xoxp-"):
        raise ValueError(
            f"unrecognized token prefix: {token[:5]}... "
            "expected xoxp-... (User OAuth Token)."
        )


def mask_token(token: str) -> str:
    """Return a redacted form of a single token value."""
    if not token or len(token) < 6:
        return "***"
    return f"{token[:5]}***...***"


def redact(text: str) -> str:
    """Replace any xox*-... substring inside text with a masked form."""
    return TOKEN_RE.sub(lambda m: mask_token(m.group(0)), text)
```

(The `auth add` and `auth list` handlers come in Tasks 11–12; tests will pass at that point. The token utilities themselves are dead-simple and don't need their own test runner now — they're exercised through subprocess tests that come later.)

- [ ] **Step 4: Commit**

```bash
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Add token validate / mask / redact utilities

Centralizes every place a token might be inspected so the leak surface
is small and obvious. Mask form is xoxp-***...*** so debug output is
diff-friendly while never revealing the secret.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 3: Config layer (load, save, atomic write, mode 0600)

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

- [ ] **Step 1: Write the failing tests**

Append to `test_slack.py`:

```python
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
        # Inspect the config file directly.
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
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
make test
```

Expected: failures (auth add not yet implemented).

- [ ] **Step 3: Implement config layer in `slack.py`**

Add after the token-utilities section:

```python
import json
import os
from pathlib import Path

# ---- config -----------------------------------------------------------------


def config_path() -> Path:
    """Resolve the config file path, honoring SLACK_SKILL_CONFIG for tests."""
    env = os.environ.get("SLACK_SKILL_CONFIG")
    if env:
        return Path(env)
    home = Path(os.path.expanduser("~"))
    return home / ".config" / "slack-skill" / "config.json"


def load_config() -> dict:
    """Return the parsed config, or an empty skeleton if the file is missing."""
    p = config_path()
    if not p.exists():
        return {"workspaces": {}}
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(f"config error: {p} is not valid JSON: {e}")
    data.setdefault("workspaces", {})
    return data


def save_config(cfg: dict) -> None:
    """Atomically write cfg to the config path with mode 0700/0600."""
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    # Tighten directory mode (best-effort; ignore if not owner).
    try:
        os.chmod(p.parent, 0o700)
    except OSError:
        pass
    tmp = p.with_suffix(p.suffix + ".tmp")
    # Open with O_CREAT | O_WRONLY | O_TRUNC, mode 0600 — file is never
    # briefly world-readable.
    fd = os.open(tmp, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(cfg, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(tmp, p)
    # Ensure final file mode (defensive — replace preserves source mode).
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
```

- [ ] **Step 4: Run tests**

The config tests still fail because `auth add` isn't wired yet. That's fine — they'll pass when Task 11 lands. The config functions themselves are exercised through Task 11. Don't add separate config-only tests; subprocess tests at the CLI boundary cover the unit.

- [ ] **Step 5: Commit**

```bash
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Add config load/save with atomic writes and mode 0600

Mode is set at open time (O_CREAT with 0o600) so a fresh file is never
briefly world-readable. SLACK_SKILL_CONFIG env var lets tests redirect
the config path without touching the user's real home directory.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 4: HTTP transport — form encoding and POST

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

This task adds the HTTP transport function and the test fixture-consumption hook. It does NOT yet wire the `call` subcommand — that's Task 8.

- [ ] **Step 1: Write the failing tests**

Append to `test_slack.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
make test
```

Expected: failures (call subcommand not yet wired).

- [ ] **Step 3: Implement HTTP transport in `slack.py`**

Add after the config section:

```python
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# ---- HTTP transport ---------------------------------------------------------

SLACK_BASE = "https://slack.com/api"
DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 30


class TransportError(Exception):
    """Raised on DNS/TCP/TLS/timeout — the call did not complete."""


class SlackAPIError(Exception):
    """Raised when Slack returns ok: false. Carries the response dict."""

    def __init__(self, response: dict, method: str):
        self.response = response
        self.method = method
        self.error = response.get("error", "unknown")
        super().__init__(f"slack API error: {self.error}")


def _encode_params(params: dict) -> bytes:
    """Form-encode params, JSON-stringifying nested objects/arrays."""
    flat: list[tuple[str, str]] = []
    for k, v in params.items():
        if isinstance(v, (dict, list)):
            flat.append((k, json.dumps(v, separators=(",", ":"))))
        elif isinstance(v, bool):
            flat.append((k, "true" if v else "false"))
        elif v is None:
            continue
        else:
            flat.append((k, str(v)))
    return urllib.parse.urlencode(flat).encode("utf-8")


def _consume_test_fixture() -> dict | None:
    """If SLACK_SKILL_TEST_RESPONSES is set, pop the next canned response."""
    fp = os.environ.get("SLACK_SKILL_TEST_RESPONSES")
    if not fp:
        return None
    try:
        data = json.loads(Path(fp).read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not data:
        raise TransportError("test fixture exhausted (no more canned responses)")
    nxt = data[0]
    Path(fp).write_text(json.dumps(data[1:]))
    return nxt


def http_post(method: str, params: dict, token: str,
              *, debug_log=None) -> tuple[int, dict, dict]:
    """POST to https://slack.com/api/<method>. Returns (status, headers, body).

    Body is parsed JSON. Headers are lowercase-keyed.
    On TransportError, raises. Does NOT interpret ok:false (caller does).
    Honors SLACK_SKILL_TEST_RESPONSES for tests.
    Retries once on 5xx (1s sleep) and on 429 with Retry-After ≤ 30s.
    """
    fixture = _consume_test_fixture()
    if fixture is not None:
        return fixture["status"], {k.lower(): v for k, v in fixture.get("headers", {}).items()}, fixture["body"]

    url = f"{SLACK_BASE}/{method}"
    body = _encode_params(params)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "User-Agent": "slack-skill/0.1 (+https://github.com/dcgrigsby/slack-skill)",
    }

    for attempt in (1, 2):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=DEFAULT_READ_TIMEOUT) as resp:
                status = resp.getcode()
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            status = e.code
            hdrs = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
            raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise TransportError(f"transport error calling {method}: {e}") from e
        elapsed = time.monotonic() - started

        if debug_log:
            debug_log(f"POST {redact(url)} status={status} elapsed={elapsed:.2f}s attempt={attempt}")

        # Retry on 5xx (once).
        if 500 <= status < 600 and attempt == 1:
            time.sleep(1.0)
            continue

        # Retry on 429 with short Retry-After.
        if status == 429 and attempt == 1:
            retry_after = int(hdrs.get("retry-after", "0") or "0")
            if 0 < retry_after <= 30:
                time.sleep(retry_after)
                continue
            raise SlackAPIError(
                {"ok": False, "error": "ratelimited", "retry_after": retry_after},
                method,
            )

        try:
            parsed = json.loads(raw) if raw else {"ok": False, "error": f"http_{status}"}
        except json.JSONDecodeError:
            raise TransportError(f"non-JSON response from {method}: {raw[:200]}")

        return status, hdrs, parsed

    raise TransportError(f"unreachable: retry loop exited for {method}")
```

- [ ] **Step 4: Commit**

```bash
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Add HTTP transport with form encoding, retry, and test fixture support

POSTs to slack.com/api/<method> with form-encoded params. Nested
objects/arrays are JSON-stringified inside form values, matching what
Slack's API expects for fields like 'blocks' and 'attachments'.

Retries once on 5xx (1s) and on 429 with Retry-After ≤ 30s. Raises
RateLimitError otherwise so the LLM can decide.

SLACK_SKILL_TEST_RESPONSES env var routes the call through a FIFO of
canned responses for tests, never touching the network.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 5: Slack API error interpretation (`ok: false` → curated hints)

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

- [ ] **Step 1: Write the failing test**

Append to `test_slack.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
make test
```

- [ ] **Step 3: Implement error interpretation in `slack.py`**

Add after the HTTP transport section:

```python
# ---- Slack API error interpretation -----------------------------------------


HINTS = {
    "missing_scope": (
        "needed: {needed}; provided: {provided}\n"
        "hint: reinstall the app with the missing scope, then refresh the token "
        "(slack.py auth add --workspace <name> --token xoxp-...)"
    ),
    "channel_not_found": (
        "hint: use conversations.list or users.conversations to discover channel IDs."
    ),
    "not_in_channel": (
        "hint: the user is not a member of that channel; join it first or use "
        "a different channel."
    ),
    "invalid_auth": (
        "hint: token is invalid or revoked. Re-run \"slack.py auth add\" with a "
        "fresh User OAuth Token."
    ),
    "token_revoked": (
        "hint: token was revoked. Re-run \"slack.py auth add\" with a fresh "
        "User OAuth Token."
    ),
    "account_inactive": (
        "hint: the Slack account is suspended."
    ),
    "ratelimited": (
        "hint: Slack returned 429. Wait Retry-After seconds and retry, or "
        "narrow the query."
    ),
}


def format_slack_error(method: str, workspace: str, response: dict) -> str:
    """One-line summary plus a hint for stderr emission."""
    err = response.get("error", "unknown_error")
    head = f"slack API error: {err} (workspace={workspace}, method={method})"
    template = HINTS.get(err)
    if not template:
        return head
    try:
        body = template.format(
            needed=response.get("needed", "?"),
            provided=response.get("provided", "?"),
        )
    except (KeyError, IndexError):
        body = template
    return f"{head}\n{body}"
```

- [ ] **Step 4: Commit**

```bash
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Add curated hints for common Slack API errors

Each ok:false carries a one-line summary plus an actionable hint to
stderr. Stdout still has the full structured response so the LLM can
read the raw error fields.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 6: Argparse skeleton with subcommands wired

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`

- [ ] **Step 1: Replace the `main` block in `slack.py`**

Replace the trailing `main(argv=None)` with the full subcommand wiring (handler functions are stubs that get filled in by Tasks 7–14):

```python
# ---- argparse + dispatch ---------------------------------------------------


def cmd_call(args) -> int:
    raise NotImplementedError("Task 8")


def cmd_auth_add(args) -> int:
    raise NotImplementedError("Task 9")


def cmd_auth_list(args) -> int:
    raise NotImplementedError("Task 10")


def cmd_auth_remove(args) -> int:
    raise NotImplementedError("Task 11")


def cmd_auth_default(args) -> int:
    raise NotImplementedError("Task 12")


def cmd_auth_test(args) -> int:
    raise NotImplementedError("Task 13")


def cmd_doctor(args) -> int:
    raise NotImplementedError("Task 14")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="slack.py",
        description="Slack Web API CLI for the slack-skill skill.",
    )
    p.add_argument("--version", action="version", version="slack.py 0.1.0")
    sub = p.add_subparsers(dest="cmd", required=False)

    # call
    pc = sub.add_parser("call", help="Invoke a Slack Web API method")
    pc.add_argument("method")
    pc.add_argument("--workspace", default=None)
    pc.add_argument("--params", default="{}")
    pc.add_argument("--resolve", action="store_true")
    pc.add_argument("--all", action="store_true", dest="all_pages")
    pc.add_argument("--limit", type=int, default=None)
    pc.add_argument("--debug", action="store_true")
    pc.set_defaults(func=cmd_call)

    # auth
    pa = sub.add_parser("auth", help="Manage workspace tokens")
    pasub = pa.add_subparsers(dest="auth_cmd", required=True)

    paa = pasub.add_parser("add", help="Add or replace a workspace token")
    paa.add_argument("--workspace", required=True)
    paa.add_argument("--token", required=True)
    paa.set_defaults(func=cmd_auth_add)

    pal = pasub.add_parser("list", help="List configured workspaces")
    pal.set_defaults(func=cmd_auth_list)

    par = pasub.add_parser("remove", help="Remove a workspace")
    par.add_argument("--workspace", required=True)
    par.set_defaults(func=cmd_auth_remove)

    pad = pasub.add_parser("default", help="Set the default workspace")
    pad.add_argument("--workspace", required=True)
    pad.set_defaults(func=cmd_auth_default)

    pat = pasub.add_parser("test", help="Run auth.test against configured workspaces")
    pat.add_argument("--workspace", default=None)
    pat.set_defaults(func=cmd_auth_test)

    # doctor
    pd = sub.add_parser("doctor", help="End-to-end self-check")
    pd.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help(sys.stderr)
        return 2
    try:
        return args.func(args)
    except NotImplementedError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
```

- [ ] **Step 2: Verify smoke test still passes**

```bash
make test
```

The no-arg test still passes; subcommand tests still fail with NotImplementedError. That's expected — they pass when their respective tasks land.

- [ ] **Step 3: Commit**

```bash
git add scripts/slack.py
git commit -m "$(cat <<'EOF'
Wire argparse subcommands with handler stubs

call, auth (add/list/remove/default/test), doctor — all parsed,
dispatched to handlers that raise NotImplementedError until their
respective tasks land.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 7: Workspace resolution + token lookup

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`

This is shared by `call`, `auth test`, `doctor` — anything that needs to find a token from a workspace name.

- [ ] **Step 1: Implement `resolve_token` in `slack.py`**

Add after the config section:

```python
# ---- workspace resolution ---------------------------------------------------


class ConfigError(Exception):
    """Raised when no workspace/token can be resolved."""


def resolve_token(cfg: dict, workspace_arg: str | None) -> tuple[str, str]:
    """Return (workspace_name, token) or raise ConfigError.

    Precedence: --workspace flag → cfg['default'] → ConfigError.
    """
    workspaces = cfg.get("workspaces", {})
    name = workspace_arg or cfg.get("default")
    if not name:
        if not workspaces:
            raise ConfigError(
                "no workspaces configured\n"
                "hint: run \"slack.py auth add --workspace <name> --token xoxp-...\""
            )
        raise ConfigError(
            "no --workspace given and no default set\n"
            f"configured workspaces: {', '.join(sorted(workspaces))}\n"
            "hint: pass --workspace <name>, or run "
            "\"slack.py auth default --workspace <name>\""
        )
    entry = workspaces.get(name)
    if not entry:
        raise ConfigError(
            f"workspace {name!r} not found\n"
            f"configured workspaces: {', '.join(sorted(workspaces)) or '(none)'}\n"
            "hint: run \"slack.py auth add --workspace " + name + " --token xoxp-...\""
        )
    return name, entry["token"]
```

- [ ] **Step 2: Commit (no test yet — exercised through Tasks 8–14)**

```bash
git add scripts/slack.py
git commit -m "$(cat <<'EOF'
Add resolve_token for workspace → token lookup with helpful errors

Single source of truth for the precedence rule (--workspace → default →
ConfigError). Errors include the configured workspace list and a fix
hint so the LLM can self-correct.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 8: `call` subcommand — basic flow

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`

Wires HTTP transport + workspace resolution + error interpretation. Pagination and resolve come in Tasks 16–17; this is the basic single-page non-resolved path.

- [ ] **Step 1: Run the existing http tests, verify they still fail**

```bash
make test
```

- [ ] **Step 2: Replace `cmd_call` in `slack.py`**

```python
def cmd_call(args) -> int:
    cfg = load_config()
    try:
        name, token = resolve_token(cfg, args.workspace)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 5

    try:
        params = json.loads(args.params)
        if not isinstance(params, dict):
            raise ValueError("must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"--params: invalid JSON object: {e}", file=sys.stderr)
        return 2

    debug = (lambda msg: print(msg, file=sys.stderr)) if args.debug else None

    try:
        status, _hdrs, body = http_post(args.method, params, token, debug_log=debug)
    except TransportError as e:
        print(f"transport error: {redact(str(e))}", file=sys.stderr)
        return 3
    except SlackAPIError as e:
        # Rate-limited path raises this directly (above 30s wait).
        print(json.dumps(e.response, separators=(",", ":")))
        print(format_slack_error(args.method, name, e.response), file=sys.stderr)
        return 1

    print(json.dumps(body, separators=(",", ":")))
    if not body.get("ok", False):
        print(format_slack_error(args.method, name, body), file=sys.stderr)
        return 1
    return 0
```

- [ ] **Step 3: Run tests, verify they pass**

```bash
make test
```

Expected: `test_http_form_encoding_via_call_smoke`, `test_http_nested_params_json_stringified`, `test_call_missing_scope_emits_hint`, `test_call_channel_not_found_emits_hint` all pass.

- [ ] **Step 4: Commit**

```bash
git add scripts/slack.py
git commit -m "$(cat <<'EOF'
Implement basic call subcommand

Resolves workspace → token, JSON-parses --params, calls http_post,
emits compact JSON to stdout. ok:false yields exit 1 with the curated
hint on stderr. Transport errors map to exit 3.

Pagination and entity resolution come in later tasks.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 9: `auth add` — write workspace with auth.test verification

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`

- [ ] **Step 1: Run config tests, verify they still fail**

```bash
make test
```

- [ ] **Step 2: Replace `cmd_auth_add` in `slack.py`**

```python
def cmd_auth_add(args) -> int:
    try:
        validate_user_token(args.token)
    except ValueError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 5

    # Verify the token works before persisting it.
    try:
        status, _hdrs, body = http_post("auth.test", {}, args.token)
    except TransportError as e:
        print(f"transport error during auth.test: {redact(str(e))}", file=sys.stderr)
        return 3

    if not body.get("ok", False):
        err = body.get("error", "unknown")
        print(f"auth.test failed: {err} (token not saved)", file=sys.stderr)
        return 5

    cfg = load_config()
    cfg.setdefault("workspaces", {})
    entry = {
        "token": args.token,
        "team_id": body.get("team_id", ""),
        "team_name": body.get("team", ""),
        "user_id": body.get("user_id", ""),
        "user_name": body.get("user", ""),
    }
    cfg["workspaces"][args.workspace] = entry
    if not cfg.get("default"):
        cfg["default"] = args.workspace

    save_config(cfg)
    print(f"added workspace {args.workspace!r} (team={entry['team_name']!r}, "
          f"user={entry['user_name']!r})", file=sys.stderr)
    return 0
```

- [ ] **Step 3: Run tests**

```bash
make test
```

Expected: config round-trip, file mode, atomic write, and token validation tests now pass.

- [ ] **Step 4: Commit**

```bash
git add scripts/slack.py
git commit -m "$(cat <<'EOF'
Implement auth add with auth.test verification

Validates token shape, runs auth.test before persisting, populates
team/user metadata from the response. First workspace added becomes
the default. Bad tokens never reach disk — verification happens before
save_config.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 10: `auth list` — pretty-print with masked tokens

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`

- [ ] **Step 1: Run masking test, verify it still fails**

```bash
make test
```

- [ ] **Step 2: Replace `cmd_auth_list` in `slack.py`**

```python
def cmd_auth_list(args) -> int:
    cfg = load_config()
    workspaces = cfg.get("workspaces", {})
    if not workspaces:
        print("(no workspaces configured)")
        return 0
    default = cfg.get("default")
    width = max((len(n) for n in workspaces), default=8)
    for name in sorted(workspaces):
        entry = workspaces[name]
        marker = "*" if name == default else " "
        team = entry.get("team_name") or "?"
        user = entry.get("user_name") or "?"
        token = mask_token(entry.get("token", ""))
        print(f"{marker} {name:<{width}}  team={team}  user={user}  token={token}")
    return 0
```

- [ ] **Step 3: Run tests**

```bash
make test
```

Expected: `test_token_mask_in_auth_list` passes.

- [ ] **Step 4: Commit**

```bash
git add scripts/slack.py
git commit -m "$(cat <<'EOF'
Implement auth list with masked tokens and starred default

Tokens never leave the file in plaintext — output uses mask_token to
produce xoxp-***...***. The default workspace is starred.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 11: `auth remove`

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

- [ ] **Step 1: Write the failing tests**

Append to `test_slack.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify failure**

```bash
make test
```

- [ ] **Step 3: Replace `cmd_auth_remove` in `slack.py`**

```python
def cmd_auth_remove(args) -> int:
    cfg = load_config()
    workspaces = cfg.get("workspaces", {})
    if args.workspace not in workspaces:
        print(f"workspace {args.workspace!r} not configured", file=sys.stderr)
        return 5
    del workspaces[args.workspace]
    if cfg.get("default") == args.workspace:
        cfg["default"] = ""
    save_config(cfg)
    print(f"removed workspace {args.workspace!r}", file=sys.stderr)
    return 0
```

- [ ] **Step 4: Run tests**

```bash
make test
```

- [ ] **Step 5: Commit**

```bash
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Implement auth remove and clear default when removing the default

Removing a workspace clears the default field rather than auto-picking
another — the user explicitly chooses the next default via auth default.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 12: `auth default` — set default workspace

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run, verify failure**

- [ ] **Step 3: Replace `cmd_auth_default` in `slack.py`**

```python
def cmd_auth_default(args) -> int:
    cfg = load_config()
    workspaces = cfg.get("workspaces", {})
    if args.workspace not in workspaces:
        names = ", ".join(sorted(workspaces)) or "(none)"
        print(f"workspace {args.workspace!r} not configured\n"
              f"configured workspaces: {names}", file=sys.stderr)
        return 5
    cfg["default"] = args.workspace
    save_config(cfg)
    print(f"default workspace set to {args.workspace!r}", file=sys.stderr)
    return 0
```

- [ ] **Step 4: Run tests + commit**

```bash
make test
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Implement auth default

Validates the workspace exists before writing. The error path lists
configured workspaces so the LLM can self-correct without re-reading
docs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 13: `auth test` — verify token + report scopes

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run, verify failure**

- [ ] **Step 3: Replace `cmd_auth_test` in `slack.py`**

```python
def cmd_auth_test(args) -> int:
    cfg = load_config()
    workspaces = cfg.get("workspaces", {})
    if not workspaces:
        print("(no workspaces configured)", file=sys.stderr)
        return 5
    targets = [args.workspace] if args.workspace else sorted(workspaces)
    failures = 0
    for name in targets:
        entry = workspaces.get(name)
        if not entry:
            print(f"FAIL  {name}  (not configured)")
            failures += 1
            continue
        try:
            _status, hdrs, body = http_post("auth.test", {}, entry["token"])
        except TransportError as e:
            print(f"FAIL  {name}  transport: {redact(str(e))}")
            failures += 1
            continue
        if not body.get("ok", False):
            print(f"FAIL  {name}  {body.get('error', 'unknown')}")
            failures += 1
            continue
        scopes = hdrs.get("x-oauth-scopes", "?")
        print(f"OK    {name}  team={body.get('team', '?')}  "
              f"user={body.get('user', '?')}  scopes={scopes}")
    return 1 if failures else 0
```

- [ ] **Step 4: Run tests + commit**

```bash
make test
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Implement auth test reporting team, user, and live scopes

The x-oauth-scopes response header is the authoritative current scope
list — comparing it against what a method needs is the fastest way to
diagnose missing_scope without reinstalling.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 14: `doctor` — config + Python + auth.test for every workspace

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`

- [ ] **Step 1: Replace `cmd_doctor` in `slack.py`**

```python
def cmd_doctor(args) -> int:
    failures = 0

    # Python version
    if sys.version_info >= (3, 9):
        print(f"OK    python {sys.version.split()[0]} ≥ 3.9")
    else:
        print(f"FAIL  python {sys.version.split()[0]} < 3.9")
        failures += 1

    # Config file
    p = config_path()
    if not p.exists():
        print(f"WARN  config {p} does not exist (run \"auth add\" to create)")
    else:
        mode = p.stat().st_mode & 0o777
        if mode == 0o600:
            print(f"OK    config {p} mode 0600")
        else:
            print(f"FAIL  config {p} mode {oct(mode)} (should be 0600)")
            failures += 1

    # Workspaces
    cfg = load_config()
    workspaces = cfg.get("workspaces", {})
    if not workspaces:
        print("WARN  no workspaces configured")
    else:
        for name in sorted(workspaces):
            entry = workspaces[name]
            try:
                _status, _hdrs, body = http_post("auth.test", {}, entry["token"])
            except TransportError as e:
                print(f"FAIL  {name}  transport: {redact(str(e))}")
                failures += 1
                continue
            if body.get("ok"):
                print(f"OK    {name}  auth.test")
            else:
                print(f"FAIL  {name}  {body.get('error', 'unknown')}")
                failures += 1

    return 1 if failures else 0
```

- [ ] **Step 2: Smoke-check via REPL run**

```bash
SLACK_SKILL_CONFIG=/tmp/no-such-file.json python3 /Users/dan/slack-skill/scripts/slack.py doctor
```

Expected: `OK python ...`, `WARN config ... does not exist`, `WARN no workspaces configured`, exit 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/slack.py
git commit -m "$(cat <<'EOF'
Implement doctor end-to-end self-check

Python version, config file existence and mode, and an auth.test for
every configured workspace. WARN for unconfigured states (not yet a
failure); FAIL for things actually broken.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 15: Pagination — `--all` + `--limit` with auto-merge

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run, verify failure**

- [ ] **Step 3: Implement pagination in `slack.py`**

Add this helper above `cmd_call`:

```python
# ---- pagination -------------------------------------------------------------


def _detect_array_field(page: dict) -> str | None:
    """Return the single top-level array field name, or None."""
    arrays = [k for k, v in page.items()
              if isinstance(v, list) and k != "response_metadata"]
    if len(arrays) == 1:
        return arrays[0]
    return None


def paginate(method: str, params: dict, token: str, *,
             limit: int | None, debug_log=None) -> dict:
    """Call method repeatedly with cursor until exhausted or limit hit.

    Returns {"ok": True, "items": [...], "page_count": N}.
    Raises SlackAPIError on ok:false; TransportError on transport failure.
    """
    items: list = []
    page_count = 0
    cursor = ""
    while True:
        page_params = dict(params)
        if cursor:
            page_params["cursor"] = cursor
        _status, _hdrs, body = http_post(method, page_params, token, debug_log=debug_log)
        if not body.get("ok"):
            raise SlackAPIError(body, method)
        page_count += 1
        field = _detect_array_field(body)
        if field is None:
            raise ValueError(
                "cannot auto-detect array field for --all; pass without --all "
                "and paginate manually using response_metadata.next_cursor"
            )
        items.extend(body[field])
        if limit is not None and len(items) >= limit:
            items = items[:limit]
            break
        cursor = body.get("response_metadata", {}).get("next_cursor") or ""
        if not cursor:
            break
    return {"ok": True, "items": items, "page_count": page_count}
```

Replace `cmd_call` to honor `--all`:

```python
def cmd_call(args) -> int:
    cfg = load_config()
    try:
        name, token = resolve_token(cfg, args.workspace)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 5

    try:
        params = json.loads(args.params)
        if not isinstance(params, dict):
            raise ValueError("must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"--params: invalid JSON object: {e}", file=sys.stderr)
        return 2

    debug = (lambda msg: print(msg, file=sys.stderr)) if args.debug else None

    try:
        if args.all_pages:
            body = paginate(args.method, params, token, limit=args.limit, debug_log=debug)
        else:
            _status, _hdrs, body = http_post(args.method, params, token, debug_log=debug)
    except TransportError as e:
        print(f"transport error: {redact(str(e))}", file=sys.stderr)
        return 3
    except SlackAPIError as e:
        print(json.dumps(e.response, separators=(",", ":")))
        print(format_slack_error(args.method, name, e.response), file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"--all: {e}", file=sys.stderr)
        return 2

    print(json.dumps(body, separators=(",", ":")))
    if not body.get("ok", False):
        print(format_slack_error(args.method, name, body), file=sys.stderr)
        return 1
    return 0
```

- [ ] **Step 4: Run tests, verify they pass**

```bash
make test
```

- [ ] **Step 5: Commit**

```bash
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Implement --all auto-pagination with --limit cap

Auto-detects the top-level array field per page and merges into items.
On ambiguity (multiple top-level arrays), errors with a hint to
paginate manually. Failures mid-loop raise immediately — no partial
synthetic envelopes ever reach stdout.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 16: Entity-ref resolver — `--resolve` walker

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

Port the regex + resolution logic from `slack2omnifocus/internal/slack/client.go:195-265`. Lookup helpers (`users.info`, `conversations.info`) are called on demand and cached for the lifetime of the invocation.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run, verify failure**

- [ ] **Step 3: Implement resolver in `slack.py`**

Add after the pagination section, before `cmd_call`:

```python
# ---- entity-ref resolver ----------------------------------------------------


# Slack guarantees these are balanced and contain no nested < or >.
ENTITY_RE = re.compile(r"<([^<>]+)>")


class Resolver:
    """Per-invocation cache for users.info / conversations.info lookups."""

    def __init__(self, token: str, *, debug_log=None):
        self.token = token
        self.debug_log = debug_log
        self.users: dict[str, str] = {}     # U-id → display name (or fallback)
        self.channels: dict[str, str] = {}  # C-id → channel name (or fallback)

    def user_name(self, uid: str) -> str:
        if uid in self.users:
            return self.users[uid]
        try:
            _s, _h, body = http_post("users.info", {"user": uid}, self.token,
                                      debug_log=self.debug_log)
            if body.get("ok"):
                profile = body.get("user", {}).get("profile", {})
                name = (profile.get("display_name")
                        or profile.get("real_name")
                        or uid)
                self.users[uid] = name
                return name
        except (TransportError, SlackAPIError):
            pass
        self.users[uid] = uid  # fallback (cached so we don't retry)
        return uid

    def channel_name(self, cid: str) -> str:
        if cid in self.channels:
            return self.channels[cid]
        try:
            _s, _h, body = http_post("conversations.info", {"channel": cid},
                                      self.token, debug_log=self.debug_log)
            if body.get("ok"):
                ch = body.get("channel", {})
                if ch.get("is_im") and ch.get("user"):
                    name = self.user_name(ch["user"])
                else:
                    name = ch.get("name") or cid
                self.channels[cid] = name
                return name
        except (TransportError, SlackAPIError):
            pass
        self.channels[cid] = cid
        return cid

    def expand(self, text: str) -> str:
        def repl(m: re.Match) -> str:
            inner = m.group(1)
            label = ""
            if "|" in inner:
                inner, label = inner.split("|", 1)
            if not inner:
                return m.group(0)
            head = inner[0]
            rest = inner[1:]
            if head == "@":
                if label:
                    return "@" + label
                return "@" + self.user_name(rest)
            if head == "#":
                if label:
                    return "#" + label
                return "#" + self.channel_name(rest)
            if head == "!":
                if label:
                    # !subteam, !date, !command with explicit label.
                    return label
                return "@" + rest  # bare broadcast: !here, !channel, !everyone
            # URL or mailto.
            if label:
                return label
            if inner.startswith("mailto:"):
                return inner[len("mailto:"):]
            return inner
        return ENTITY_RE.sub(repl, text)


def walk_and_resolve(obj, resolver: Resolver):
    """Recursively expand entity refs in any string field."""
    if isinstance(obj, str):
        return resolver.expand(obj)
    if isinstance(obj, list):
        return [walk_and_resolve(x, resolver) for x in obj]
    if isinstance(obj, dict):
        return {k: walk_and_resolve(v, resolver) for k, v in obj.items()}
    return obj
```

Update `cmd_call` to apply `--resolve` after the body is obtained (before the final `print`):

```python
    if args.resolve and body.get("ok"):
        resolver = Resolver(token, debug_log=debug)
        body = walk_and_resolve(body, resolver)

    print(json.dumps(body, separators=(",", ":")))
```

(Place the `if args.resolve` block immediately before the existing `print(json.dumps(body, ...))`.)

- [ ] **Step 4: Run tests, verify they pass**

```bash
make test
```

- [ ] **Step 5: Commit**

```bash
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Implement --resolve entity-ref expansion (port of FormatText)

Walks the response and expands <@U..>, <#C..>, <!here>, <!subteam^...>,
<https://...>, and <mailto:...> in any string field. Inline labels
(<@U|alice>) skip the lookup. Lookup failures fall back to readable
@U07ABC / #C123 — one bad ref never tanks the whole response.

Logic ported from slack2omnifocus/internal/slack/client.go:195-265.
Cache lives for the lifetime of the invocation.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 17: `--debug` flag — log requests with token redaction

**Files:**
- Modify: `/Users/dan/slack-skill/scripts/slack.py`
- Modify: `/Users/dan/slack-skill/scripts/test_slack.py`

The current `--debug` already passes a `debug_log` callback to `http_post` and `Resolver`. This task formalizes the contract and adds tests.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run, verify failure**

- [ ] **Step 3: Implementation**

Already wired in Tasks 4 and 16. Confirm `redact()` is called on every URL before logging by re-reading the `if debug_log:` block in `http_post`. The `auth add` flow doesn't currently pass `--debug`, but that's a non-issue — the flag is on `call` only.

If the test still fails because debug logging is too sparse, expand `http_post`'s log line to include the method name explicitly:

```python
        if debug_log:
            debug_log(f"POST {redact(url)} method={method} status={status} elapsed={elapsed:.2f}s attempt={attempt}")
```

- [ ] **Step 4: Run tests, commit**

```bash
make test
git add scripts/slack.py scripts/test_slack.py
git commit -m "$(cat <<'EOF'
Verify --debug logging redacts tokens unconditionally

Test asserts both that debug output reaches stderr and that token
substrings never appear in it, even when present in the URL or
headers. redact() runs before any log line is emitted.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 18: App manifest

**Files:**
- Create: `/Users/dan/slack-skill/docs/slack-app-manifest.yaml`

- [ ] **Step 1: Create the directory and file**

```bash
mkdir -p /Users/dan/slack-skill/docs
```

Write `/Users/dan/slack-skill/docs/slack-app-manifest.yaml` with the exact content from the spec:

```yaml
display_information:
  name: Slack Skill
  description: User-API access for the Slack skill (Claude/agents)
features:
  bot_user: null
oauth_config:
  scopes:
    user:
      - channels:history
      - groups:history
      - im:history
      - mpim:history
      - channels:read
      - groups:read
      - im:read
      - mpim:read
      - chat:write
      - reactions:read
      - reactions:write
      - users:read
      - users.profile:read
      - search:read
      - files:read
      - pins:read
      - pins:write
      - stars:read
      - stars:write
      - bookmarks:read
      - bookmarks:write
settings:
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

- [ ] **Step 2: Commit**

```bash
git add docs/slack-app-manifest.yaml
git commit -m "$(cat <<'EOF'
Add Slack app manifest with full user-token scope set

Paste-into-Slack manifest covers every scope the skill exercises:
read/write across channels, DMs, groups, MPIMs; reactions; users;
search; files (read only — multipart out of scope for v1); plus
pins, stars, and bookmarks. Bot user disabled; Socket Mode disabled;
token rotation disabled (skill assumes long-lived xoxp- tokens).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 19: CHEATSHEET.md (Tier-2 API map)

**Files:**
- Create: `/Users/dan/slack-skill/docs/slack-api/CHEATSHEET.md`

This is content-heavy. Format: one line per method, grouped by namespace, with required params (`*`), required scopes, and a `[paginated]` flag where applicable. Coverage target: every method useful with a User OAuth Token. Aim for ~300 lines.

- [ ] **Step 1: Create the directory**

```bash
mkdir -p /Users/dan/slack-skill/docs/slack-api
```

- [ ] **Step 2: Write `CHEATSHEET.md`**

Use this exact template; every method line is `name  description. Params: <param>*<rest>. Scope: <scope>. [paginated]`. Source of truth: <https://api.slack.com/methods> (curate the user-token-relevant subset).

```markdown
# Slack Web API Cheatsheet

Compact one-line-per-method map of the Slack Web API surface that's
useful with a User OAuth Token (`xoxp-...`). For full per-method
detail, see the per-namespace file (`Conversations.md`, `Chat.md`,
etc.). For methods not covered here, see `FULL-REFERENCE.md`.

Conventions:
- `param*` = required.
- `[paginated]` = uses `cursor` / `response_metadata.next_cursor`; pass `--all` to auto-loop.
- Scope columns reflect User Token Scopes.

## auth

- `auth.test`         Check token validity. Params: (none). Scope: (none).
- `auth.revoke`       Revoke the token. Params: (none). Scope: (none).

## conversations

- `conversations.list`         List channels / DMs. Params: types, exclude_archived. Scope: channels:read,groups:read,im:read,mpim:read. [paginated]
- `conversations.history`      Get messages in a channel/DM. Params: channel*, oldest, latest, inclusive, limit. Scope: channels:history (groups:/im:/mpim: variants). [paginated]
- `conversations.replies`      Get a thread (parent + replies). Params: channel*, ts*, oldest, latest. Scope: as conversations.history. [paginated]
- `conversations.info`         Channel / DM metadata. Params: channel*, include_locale, include_num_members. Scope: channels:read (groups:/im:/mpim:).
- `conversations.members`      List members of a channel. Params: channel*, limit. Scope: as conversations.info. [paginated]
- `conversations.mark`         Mark a channel read up to ts. Params: channel*, ts*. Scope: channels:write (or im:write etc).
- `conversations.open`         Open a DM (1:1 or group). Params: users (csv) OR channel. Scope: im:write,mpim:write.
- `conversations.close`        Close a DM. Params: channel*. Scope: im:write,mpim:write.
- `conversations.create`       Create a public/private channel. Params: name*, is_private, team_id. Scope: channels:write,groups:write.
- `conversations.archive`      Archive a channel. Params: channel*. Scope: channels:write,groups:write.
- `conversations.unarchive`    Unarchive a channel. Params: channel*. Scope: channels:write,groups:write.
- `conversations.invite`       Invite users to a channel. Params: channel*, users (csv)*. Scope: channels:write,groups:write.
- `conversations.kick`         Remove a user from a channel. Params: channel*, user*. Scope: channels:write,groups:write.
- `conversations.join`         Join a public channel. Params: channel*. Scope: channels:write.
- `conversations.leave`        Leave a channel. Params: channel*. Scope: channels:write,groups:write,im:write,mpim:write.
- `conversations.rename`       Rename a channel. Params: channel*, name*. Scope: channels:write,groups:write.
- `conversations.setPurpose`   Set channel purpose. Params: channel*, purpose*. Scope: channels:write,groups:write.
- `conversations.setTopic`     Set channel topic. Params: channel*, topic*. Scope: channels:write,groups:write.

## chat

- `chat.postMessage`     Send a message. Params: channel*, text or blocks*, thread_ts, reply_broadcast, mrkdwn, parse, link_names, unfurl_links, unfurl_media. Scope: chat:write.
- `chat.postEphemeral`   Post a message visible only to user. Params: channel*, user*, text or blocks*. Scope: chat:write.
- `chat.update`          Edit a message. Params: channel*, ts*, text or blocks*. Scope: chat:write.
- `chat.delete`          Delete a message. Params: channel*, ts*. Scope: chat:write.
- `chat.meMessage`       Post a /me message. Params: channel*, text*. Scope: chat:write.
- `chat.scheduleMessage` Schedule a future message. Params: channel*, post_at*, text or blocks*. Scope: chat:write.
- `chat.deleteScheduledMessage` Delete a scheduled message. Params: channel*, scheduled_message_id*. Scope: chat:write.
- `chat.scheduledMessages.list` List scheduled messages. Params: channel, latest, oldest. Scope: none. [paginated]
- `chat.getPermalink`    Get a permalink for a message. Params: channel*, message_ts*. Scope: (none).
- `chat.unfurl`          Provide custom unfurl content. Params: channel*, ts*, unfurls*. Scope: links:write.

## reactions

- `reactions.add`     Add a reaction. Params: name*, channel*, timestamp*. Scope: reactions:write.
- `reactions.remove`  Remove a reaction. Params: name*, channel*, timestamp*. Scope: reactions:write.
- `reactions.get`     List reactions on a single item. Params: channel, timestamp, file, file_comment, full. Scope: reactions:read.
- `reactions.list`    List items the user has reacted to. Params: user, full. Scope: reactions:read. [paginated]

## users

- `users.list`              List all users. Params: limit, include_locale. Scope: users:read. [paginated]
- `users.info`              User profile by ID. Params: user*, include_locale. Scope: users:read.
- `users.lookupByEmail`     User by email. Params: email*. Scope: users:read.email.
- `users.identity`          The token's user identity. Params: (none). Scope: identity.basic.
- `users.conversations`     Channels / DMs the token's user is in. Params: types, exclude_archived. Scope: channels:read,groups:read,im:read,mpim:read. [paginated]
- `users.profile.get`       User's profile fields. Params: user. Scope: users.profile:read.
- `users.profile.set`       Update the token's user profile. Params: name, value, profile (json). Scope: users.profile:write.
- `users.setActive`         Mark active. Params: (none). Scope: users:write.
- `users.setPresence`       Set auto/away. Params: presence*. Scope: users:write.
- `users.getPresence`       Get user presence. Params: user. Scope: users:read.

## search

- `search.messages`  Search messages across the workspace. Params: query*, count, page, sort, sort_dir. Scope: search:read. [paginated via page]
- `search.files`     Search files. Params: query*, count, page, sort, sort_dir. Scope: search:read. [paginated via page]
- `search.all`       Combined search. Params: query*, count, page. Scope: search:read. [paginated via page]

## files

- `files.list`     List files. Params: user, channel, ts_from, ts_to, types, count, page. Scope: files:read. [paginated via page]
- `files.info`     File metadata + comments. Params: file*, count, page. Scope: files:read. [paginated via page]
- `files.delete`   Delete a file. Params: file*. Scope: files:write.
- `files.upload`   Upload a file. (Multipart — out of scope for v1.)

## pins

- `pins.add`     Pin a message. Params: channel*, timestamp*. Scope: pins:write.
- `pins.remove`  Unpin a message. Params: channel*, timestamp*. Scope: pins:write.
- `pins.list`    List pins for a channel. Params: channel*. Scope: pins:read.

## stars

- `stars.add`     Star a message/file. Params: channel, timestamp, file, file_comment. Scope: stars:write.
- `stars.remove`  Unstar. Params: channel, timestamp, file, file_comment. Scope: stars:write.
- `stars.list`    List the user's stars. Params: count, page. Scope: stars:read. [paginated via page]

## bookmarks

- `bookmarks.add`     Add a channel bookmark. Params: channel_id*, title*, type*, link, emoji, entity_id, parent_id. Scope: bookmarks:write.
- `bookmarks.edit`    Edit a bookmark. Params: bookmark_id*, channel_id*, title, link, emoji. Scope: bookmarks:write.
- `bookmarks.remove`  Remove a bookmark. Params: bookmark_id*, channel_id*. Scope: bookmarks:write.
- `bookmarks.list`    List bookmarks for a channel. Params: channel_id*. Scope: bookmarks:read.

## team

- `team.info`             Workspace metadata. Params: team. Scope: team:read.
- `team.profile.get`      Custom profile field schema. Params: visibility. Scope: users.profile:read.
- `team.preferences.list` Workspace preferences. Params: (none). Scope: team:read.
- `team.billableInfo`     Billable users. Params: user. Scope: admin (rare).

## dnd

- `dnd.info`           User's DND status. Params: user. Scope: dnd:read.
- `dnd.teamInfo`       Team-wide DND. Params: users (csv). Scope: dnd:read.
- `dnd.setSnooze`      Snooze the user's DND. Params: num_minutes*. Scope: dnd:write.
- `dnd.endSnooze`      End snooze early. Params: (none). Scope: dnd:write.
- `dnd.endDnd`         End DND. Params: (none). Scope: dnd:write.

## reminders

- `reminders.add`       Create a reminder. Params: text*, time* (Unix or natural), user. Scope: reminders:write.
- `reminders.complete`  Mark complete. Params: reminder*. Scope: reminders:write.
- `reminders.delete`    Delete. Params: reminder*. Scope: reminders:write.
- `reminders.info`      Reminder by ID. Params: reminder*. Scope: reminders:read.
- `reminders.list`      All reminders. Params: (none). Scope: reminders:read.

## emoji

- `emoji.list`  List custom emoji. Params: (none). Scope: emoji:read.

For methods not in this cheatsheet (admin.*, calls.*, workflows.*,
canvas.*, etc.), see `FULL-REFERENCE.md`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/slack-api/CHEATSHEET.md
git commit -m "$(cat <<'EOF'
Add Tier-2 API cheatsheet

Compact one-line-per-method map covering every Slack Web API method
useful with a User OAuth Token. Each line: method, params (* required),
required scopes, paginated flag. Pointer to FULL-REFERENCE.md for
niche surfaces.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 20: Per-namespace docs (Tier 3)

**Files:**
- Create: `/Users/dan/slack-skill/docs/slack-api/Conversations.md`
- Create: `/Users/dan/slack-skill/docs/slack-api/Chat.md`
- Create: `/Users/dan/slack-skill/docs/slack-api/Reactions.md`
- Create: `/Users/dan/slack-skill/docs/slack-api/Users.md`
- Create: `/Users/dan/slack-skill/docs/slack-api/Search.md`
- Create: `/Users/dan/slack-skill/docs/slack-api/Files.md`
- Create: `/Users/dan/slack-skill/docs/slack-api/Pins-Stars-Bookmarks.md`

Each file: ~150–300 lines covering its namespace with focused examples, common parameter patterns, edge cases, and required scopes. Use the omnifocus-skill per-class files (`Task.md`, `Project.md`) as the structural template.

For each file, follow this skeleton (filled in per namespace):

```markdown
# <Namespace>

<one-paragraph orientation>

## Methods

### method.name

What it does. Params:
- `name` (type, required/optional) — description.

Required scope: `scope:name`.

Example:

\`\`\`bash
python3 scripts/slack.py call method.name --workspace work \
  --params '{"key":"value"}'
\`\`\`

Returns:
\`\`\`json
{...}
\`\`\`

Edge cases:
- Edge case 1
- Edge case 2

### method.next ...
```

Per-file content guidance:

- **Conversations.md** — emphasize the channel/DM vs. private/MPIM distinctions, the `types` parameter on list methods, the difference between `conversations.history` and `conversations.replies`, and the `conversations.mark` semantics ("ts" is the *latest message you've seen*, not a deletion point).
- **Chat.md** — emphasize text vs. blocks vs. attachments, thread replies via `thread_ts`, scheduled messages, getPermalink semantics, mrkdwn vs. plain text.
- **Reactions.md** — emphasize emoji name format (no colons), reactions.list pagination, reaction event vs. reaction state.
- **Users.md** — display_name vs. real_name fallback, lookupByEmail caveats, users.conversations vs. conversations.list (the former is scoped to the user's memberships).
- **Search.md** — query syntax, page-based pagination (NOT cursor-based), sort options, the user-token requirement (search isn't available to bot tokens).
- **Files.md** — read-only for v1 (uploads excluded), filtering by channel/user/time, the `is_external` distinction.
- **Pins-Stars-Bookmarks.md** — combined because each namespace is small; cover the differences between pinning (channel-scoped, visible to all members), starring (user-private, deprecated in modern Slack but still functional), and bookmarks (channel-scoped, structured).

- [ ] **Step 1: Write `Conversations.md`**

(Engineer fills in per the skeleton, ~250 lines covering every method in the conversations namespace from the cheatsheet, with one full bash example per method and edge-case notes.)

- [ ] **Step 2: Write `Chat.md`**

(Same approach, covering chat.* methods.)

- [ ] **Step 3: Write `Reactions.md`**
- [ ] **Step 4: Write `Users.md`**
- [ ] **Step 5: Write `Search.md`**
- [ ] **Step 6: Write `Files.md`**
- [ ] **Step 7: Write `Pins-Stars-Bookmarks.md`**

- [ ] **Step 8: Commit (one commit covers all per-namespace files)**

```bash
git add docs/slack-api/
git commit -m "$(cat <<'EOF'
Add Tier-3 per-namespace API references

One file per Slack API namespace useful with a User OAuth Token. Each
file covers every method in its namespace with bash examples, return
shapes, and edge-case notes. Loaded on demand when CHEATSHEET.md isn't
detailed enough.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 21: `regen_reference.py` — fetch OpenAPI → FULL-REFERENCE.md

**Files:**
- Create: `/Users/dan/slack-skill/scripts/regen_reference.py`

The script downloads <https://api.slack.com/specs/openapi/v2/slack_web.json>, parses it, and emits a Markdown reference of every operation. The output is committed (Task 22) so the LLM has it locally without network.

- [ ] **Step 1: Write `regen_reference.py`**

```python
#!/usr/bin/env python3
"""
regen_reference.py — fetch Slack's OpenAPI v2 spec and emit a Markdown
reference covering every operation.

Output is intended for docs/slack-api/FULL-REFERENCE.md. Output is
deterministic given the same input spec (sorted keys, stable iteration).

Usage:
  python3 scripts/regen_reference.py docs/slack-api/FULL-REFERENCE.md

The script fails loud if Slack changes the spec format in a way the
parser doesn't recognize — better to fail than silently emit garbage.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

SPEC_URL = "https://api.slack.com/specs/openapi/v2/slack_web.json"


def fetch_spec() -> dict:
    print(f"fetching {SPEC_URL}", file=sys.stderr)
    with urllib.request.urlopen(SPEC_URL, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def emit(spec: dict, out: Path) -> None:
    paths = spec.get("paths", {})
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        f.write("# Slack Web API — Full Reference\n\n")
        f.write(f"Generated from {SPEC_URL}.\n\n")
        f.write("Loaded only when CHEATSHEET.md and the per-namespace files don't cover what you need.\n\n")
        f.write("---\n\n")
        for path in sorted(paths):
            ops = paths[path]
            for method_verb, op in sorted(ops.items()):
                if not isinstance(op, dict):
                    continue
                api_method = path.lstrip("/")
                summary = op.get("summary", "")
                description = op.get("description", "").strip()
                f.write(f"## {api_method}\n\n")
                if summary:
                    f.write(f"**{summary}**\n\n")
                if description:
                    f.write(f"{description}\n\n")
                params = op.get("parameters", []) or []
                if params:
                    f.write("**Parameters:**\n\n")
                    for p in params:
                        name = p.get("name", "?")
                        loc = p.get("in", "?")
                        required = " (required)" if p.get("required") else ""
                        desc = (p.get("description") or "").replace("\n", " ").strip()
                        f.write(f"- `{name}` ({loc}){required}: {desc}\n")
                    f.write("\n")
                tags = op.get("tags") or []
                if tags:
                    f.write(f"Tags: {', '.join(tags)}\n\n")
                f.write("---\n\n")
    print(f"wrote {out}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <output-path>", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    spec = fetch_spec()
    emit(spec, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Commit (no test — content-driven, validated by output)**

```bash
git add scripts/regen_reference.py
git commit -m "$(cat <<'EOF'
Add regen_reference.py to generate FULL-REFERENCE.md from OpenAPI

Downloads Slack's published OpenAPI v2 spec, walks every operation,
and emits a Markdown file covering all of them. Run via
'make regen-reference' on demand; output is committed to the repo so
no network access is needed at skill-load time.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 22: Run `regen-reference` and commit FULL-REFERENCE.md

**Files:**
- Generate: `/Users/dan/slack-skill/docs/slack-api/FULL-REFERENCE.md`

- [ ] **Step 1: Run regen**

```bash
cd /Users/dan/slack-skill && make regen-reference
```

Expected: `wrote docs/slack-api/FULL-REFERENCE.md` on stderr; non-empty file produced. The file will be ~5–10k lines.

- [ ] **Step 2: Spot-check the output**

```bash
head -50 docs/slack-api/FULL-REFERENCE.md
wc -l docs/slack-api/FULL-REFERENCE.md
```

Confirm: header looks right, line count > 1000, several `## ` headers visible.

- [ ] **Step 3: Commit**

```bash
git add docs/slack-api/FULL-REFERENCE.md
git commit -m "$(cat <<'EOF'
Generate Tier-4 FULL-REFERENCE.md from Slack's OpenAPI v2 spec

Comprehensive method-by-method reference for the entire Slack Web API.
Loaded only when the cheatsheet and per-namespace files don't cover
what's needed. Regenerable via 'make regen-reference'.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 23: SKILL.md — frontmatter + body with all inline patterns

**Files:**
- Create: `/Users/dan/slack-skill/SKILL.md`

The body has 11 inline patterns (per the spec) plus a "When to use", "When not to use", "How to invoke", "First-time setup", and "API reference discovery" sections. Aim for ~400–600 lines, modeled on `omnifocus-skill/SKILL.md`'s tone and structure.

- [ ] **Step 1: Write the frontmatter**

```markdown
---
name: slack
description: |-
  Read, send, and react to messages in the user's Slack workspaces on the user's behalf via the Slack Web API. Use whenever the user wants to read recent messages or threads in a channel or DM, send a message or DM, react to or unreact from a message, mark a channel as read up to a point, list channels and DMs, search across messages, get a permalink, manage pins / stars / bookmarks, or set up / add / verify a Slack workspace token. Operates with a User OAuth Token (xoxp-...) — every action is attributed to the user, not a bot. Calls the Slack Web API directly via a Python helper script (scripts/slack.py); no Bot Token, no Socket Mode, no daemon. Multi-workspace via named profiles in ~/.config/slack-skill/config.json.
---
```

- [ ] **Step 2: Write the body**

Sections in order:

1. **Title + one-paragraph overview** (this skill is a thin shim around the Slack Web API; the LLM composes calls).
2. **Scope: macOS only in v1** + Python 3.9+.
3. **When to use this skill** — concrete trigger phrases grouped by category (read recent / read thread / send / react / mark read / list / search / setup / multi-workspace).
4. **When NOT to use this skill** — note that Slack DMs aren't notes (route to obsidian-skill); committed work goes to omnifocus-skill; this skill never uses bot tokens.
5. **First-time setup / adding a workspace** — full walkthrough:
   - Check existing: `python3 scripts/slack.py auth list`.
   - Direct user to <https://api.slack.com/apps?new_app=1> → "From an app manifest".
   - Show them `docs/slack-app-manifest.yaml` to paste.
   - Have them install to workspace, copy the User OAuth Token, paste in chat.
   - Run `auth add`, verify with `auth test`.
6. **How to invoke** — exit codes, output conventions, when to use `--resolve` and `--all`.
7. **Inline patterns** (numbered, with full bash examples for each):
   1. Resolve channel/user names to IDs.
   2. Read recent messages from a channel or DM.
   3. Read a full thread.
   4. Send a message (channel, DM, thread reply).
   5. React / unreact.
   6. Mark a channel read up to a message.
   7. List my channels and DMs.
   8. List members of a channel.
   9. Search across my messages.
   10. Get a permalink.
   11. Multi-workspace: same operation against multiple workspaces.
8. **API reference discovery** — when to load CHEATSHEET → per-namespace → FULL-REFERENCE.
9. **Token security & write operations** — confirm sensitive sends, no destructive bulk ops without explicit confirmation, never paste tokens into chat output.
10. **Common errors and what to do** — short table mapping `missing_scope` / `channel_not_found` / `not_in_channel` / `invalid_auth` to recovery actions.
11. **Tips** — limit results, check for null fields, use IDs over names, check `--resolve` is producing readable text before assuming the LLM should re-do resolution itself.

(Engineer fills in the body content directly; cap at 600 lines and keep the instructional tone consistent with omnifocus-skill.)

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "$(cat <<'EOF'
Add SKILL.md with frontmatter and inline patterns

11 hot-path patterns covering read, send, react, mark-read, list,
search, permalink, and multi-workspace, plus a full first-time-setup
walkthrough so the LLM can guide a user from zero to a configured
workspace without manual steps beyond the browser.

Tier discovery section directs the LLM to CHEATSHEET → per-namespace
files → FULL-REFERENCE based on coverage need.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 24: README.md full rewrite

**Files:**
- Modify: `/Users/dan/slack-skill/README.md`

Replaces the placeholder README with the full install / setup / scope / safety document. Model on `obsidian-skill/README.md`.

- [ ] **Step 1: Replace `README.md` content**

Sections in order:

1. Title + one-paragraph overview.
2. **⛔ DANGER — READ BEFORE USE** (preserve the existing block; tighten prose if needed).
3. **Companion skills** — note that `obsidian-skill` and `omnifocus-skill` complement this; `slack2omnifocus` is unrelated and runs separately.
4. **Install** — `npx skills add dcgrigsby/slack-skill -g -a claude-code -a gemini-cli -a codex -a pi -y`.
5. **Create a Slack app** — point at `docs/slack-app-manifest.yaml`; explain manual scope-clicking as fallback; explicitly say "create a new app — don't reuse a token from `slack2omnifocus` or anywhere else."
6. **Configure** — `python3 scripts/slack.py auth add --workspace <name> --token xoxp-...`.
7. **Usage** — point at SKILL.md.
8. **Development** — `make test`, `make package`, `make regen-reference`, `make clean`.
9. **License** — Apache 2.0.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
Rewrite README: install, setup, scope, safety

Full installation and setup walkthrough referencing the app manifest.
Explicit instruction to create a separate Slack app rather than reusing
a token from slack2omnifocus. Existing danger callout preserved.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 25: evals/evals.json

**Files:**
- Create: `/Users/dan/slack-skill/evals/evals.json`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p /Users/dan/slack-skill/evals
```

- [ ] **Step 2: Write `evals/evals.json`**

Structure mirrors `omnifocus-skill/evals/evals.json`. Each eval is `{id, name, prompt, expected_output}`. Use `SKILLTEST_` prefix on any side-effecting prompts so produced messages are easy to identify and clean up.

```json
{
  "skill_name": "slack",
  "evals": [
    {
      "id": 0,
      "name": "first_time_setup",
      "prompt": "Set up Slack for my work workspace.",
      "expected_output": "A walkthrough that points the user at the app manifest, explains the browser steps, captures the token from chat, and runs auth add + auth test to verify."
    },
    {
      "id": 1,
      "name": "read_recent_channel",
      "prompt": "What's new in #general today on my work Slack?",
      "expected_output": "A summarized listing of today's messages from #general, with @user / #channel refs resolved (used --resolve)."
    },
    {
      "id": 2,
      "name": "read_thread",
      "prompt": "Summarize the thread starting at this message: <permalink>",
      "expected_output": "A summary of the thread parent and all replies, fetched via conversations.replies."
    },
    {
      "id": 3,
      "name": "send_dm",
      "prompt": "DM bob saying SKILLTEST_running 5 late",
      "expected_output": "A successful chat.postMessage to bob's DM channel containing the literal SKILLTEST_running 5 late text."
    },
    {
      "id": 4,
      "name": "send_channel",
      "prompt": "Post to #ops: SKILLTEST_deploy is done",
      "expected_output": "A successful chat.postMessage to #ops containing the SKILLTEST_ literal."
    },
    {
      "id": 5,
      "name": "react",
      "prompt": "React to the most recent message in #general with eyes.",
      "expected_output": "A reactions.add call with name=eyes against the latest message ts in #general."
    },
    {
      "id": 6,
      "name": "mark_read",
      "prompt": "Mark #general as read up to the latest message.",
      "expected_output": "A conversations.mark call with the latest visible ts."
    },
    {
      "id": 7,
      "name": "list_channels",
      "prompt": "What channels and DMs am I in on work Slack?",
      "expected_output": "A users.conversations call (likely with --all and types=public_channel,private_channel,im,mpim), grouped output by type."
    },
    {
      "id": 8,
      "name": "search",
      "prompt": "Find messages where alice mentioned 'launch' in the last week.",
      "expected_output": "A search.messages call with a query like 'from:alice launch after:<date>' and a readable result list."
    },
    {
      "id": 9,
      "name": "permalink",
      "prompt": "Get me a permalink for that last message in #ops.",
      "expected_output": "A chat.getPermalink call returning the canonical https://<workspace>.slack.com/... URL."
    },
    {
      "id": 10,
      "name": "multi_workspace",
      "prompt": "Send 'SKILLTEST_status update' to #status in both my work and personal Slack.",
      "expected_output": "Two chat.postMessage calls, one per --workspace."
    },
    {
      "id": 11,
      "name": "error_recovery_not_in_channel",
      "prompt": "Read #private-im-not-in.",
      "expected_output": "A first attempt that returns not_in_channel, followed by a clear explanation that the user is not a member and a suggestion to join or pick a different channel — not retried blindly."
    },
    {
      "id": 12,
      "name": "cross_skill",
      "prompt": "Post the result of my OmniFocus weekly review to #status.",
      "expected_output": "An OmniFocus query for completed-this-week tasks, formatted into a message body, then posted to #status via chat.postMessage."
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add evals/evals.json
git commit -m "$(cat <<'EOF'
Add evals/evals.json with 13 behavioral eval prompts

Coverage: first-time setup, read-recent, read-thread, send-DM,
send-channel, react, mark-read, list-channels, search, permalink,
multi-workspace, error-recovery, cross-skill.

SKILLTEST_ prefix on side-effecting prompts so produced messages are
easy to identify and clean up post-eval.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 26: `scripts/package_skill.py`

**Files:**
- Create: `/Users/dan/slack-skill/scripts/package_skill.py`

- [ ] **Step 1: Write `package_skill.py`**

Mirrors `obsidian-skill/scripts/package_skill.py` if present, or implements the minimum: tar the relevant files into `slack-skill.skill`.

```python
#!/usr/bin/env python3
"""
package_skill.py — build a .skill bundle for distribution.

Tars the skill files (SKILL.md, scripts/, docs/, evals/, LICENSE,
NOTICE, README.md) into <skill-name>.skill at the repo root.

Usage:
  python3 scripts/package_skill.py <repo-root>
"""

from __future__ import annotations

import sys
import tarfile
from pathlib import Path

INCLUDE = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "NOTICE",
    "scripts",
    "docs",
    "evals",
]


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <repo-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    out = root / "slack-skill.skill"
    with tarfile.open(out, "w:gz") as tf:
        for name in INCLUDE:
            p = root / name
            if not p.exists():
                print(f"warn: {name} missing, skipping", file=sys.stderr)
                continue
            tf.add(p, arcname=name)
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Test packaging**

```bash
cd /Users/dan/slack-skill && make package
ls -la slack-skill.skill
make clean
ls -la slack-skill.skill 2>&1 || echo "removed"
```

Expected: `make package` produces a non-empty `.skill` file; `make clean` removes it.

- [ ] **Step 3: Commit**

```bash
git add scripts/package_skill.py
git commit -m "$(cat <<'EOF'
Add package_skill.py for .skill bundle distribution

Tars SKILL.md, scripts/, docs/, evals/, LICENSE, NOTICE, README.md into
slack-skill.skill at the repo root. Wired into the Makefile's
'make package' target. Removed by 'make clean'.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 27: Final verification

**Files:**
- (none — checks only)

- [ ] **Step 1: Run the full test suite**

```bash
cd /Users/dan/slack-skill && make test
```

Expected: every test passes, exit 0.

- [ ] **Step 2: Verify package builds**

```bash
make package
ls -la slack-skill.skill
make clean
```

Expected: `.skill` produced, then cleaned.

- [ ] **Step 3: Verify file inventory matches plan**

```bash
find . -type f -not -path './.git/*' | sort
```

Expected files present (no extras, none missing):

```
./.gitignore
./LICENSE
./Makefile
./NOTICE
./README.md
./SKILL.md
./docs/plans/2026-05-02-slack-skill-implementation.md
./docs/slack-api/CHEATSHEET.md
./docs/slack-api/Chat.md
./docs/slack-api/Conversations.md
./docs/slack-api/Files.md
./docs/slack-api/FULL-REFERENCE.md
./docs/slack-api/Pins-Stars-Bookmarks.md
./docs/slack-api/Reactions.md
./docs/slack-api/Search.md
./docs/slack-api/Users.md
./docs/slack-app-manifest.yaml
./docs/specs/2026-05-02-slack-skill-design.md
./evals/evals.json
./scripts/package_skill.py
./scripts/regen_reference.py
./scripts/slack.py
./scripts/test_slack.py
```

- [ ] **Step 4: Manual smoke test against a real workspace**

Engineer: only do this after every other task is green. Steps:

1. Create a new Slack app from `docs/slack-app-manifest.yaml`.
2. Install to your workspace; copy the User OAuth Token.
3. `python3 scripts/slack.py auth add --workspace test --token xoxp-...`
4. `python3 scripts/slack.py auth test --workspace test` → expect OK with team/user/scopes.
5. `python3 scripts/slack.py call conversations.list --workspace test --params '{"types":"public_channel","limit":5}'` → expect a JSON list of channels.
6. Pick a test channel ID from step 5.
7. `python3 scripts/slack.py call chat.postMessage --workspace test --params '{"channel":"<id>","text":"SKILLTEST_smoke from slack-skill"}'` → expect a successful post.
8. Verify the message appears in Slack as you (the user), not as a bot.
9. Clean up: delete the test message via `chat.delete` or in the Slack UI.

If any of step 1–8 fails, file an issue against the corresponding task and fix.

- [ ] **Step 5: Final push (if anything outstanding)**

```bash
git status
git push origin main
```

---

## Spec coverage check

| Spec section | Task(s) |
|---|---|
| Goals: User-API access via thin Python helper | Tasks 4, 8 |
| Goals: Multi-workspace via named profiles | Tasks 3, 9, 11, 12 |
| Goals: First-time setup driveable from chat | Tasks 18, 23, 24 |
| Goals: Trigger reliably on natural phrasings | Task 23 (SKILL.md) + Task 25 (evals) |
| CLI: `call` subcommand with --params | Tasks 4, 8 |
| CLI: --workspace selection | Tasks 7, 8 |
| CLI: --all pagination + --limit | Task 15 |
| CLI: --resolve walker | Task 16 |
| CLI: `auth` add/list/remove/default/test | Tasks 9–13 |
| CLI: `doctor` | Task 14 |
| CLI: --debug with token redaction | Tasks 2, 17 |
| CLI: exit codes 0/1/2/3/5 | Tasks 8 (1, 2, 3), 7 (5), 9 (5), all (0) |
| Errors: curated hints for common Slack errors | Task 5 |
| Errors: rate limit handling (30s cap) | Task 4 |
| Errors: HTTP 5xx retry | Task 4 |
| Auth: config schema with metadata | Task 9 |
| Auth: file mode 0600 at open time | Task 3 |
| Auth: atomic writes | Task 3 |
| Auth: token shape validation (xoxp-) | Task 2 |
| Auth: never log tokens | Tasks 2, 17 |
| Docs: SKILL.md inline patterns | Task 23 |
| Docs: CHEATSHEET.md | Task 19 |
| Docs: per-namespace files | Task 20 |
| Docs: FULL-REFERENCE.md generated | Tasks 21, 22 |
| Docs: README with safety + setup | Task 24 |
| Docs: app manifest | Task 18 |
| Tests: mechanical, no network | Tasks 2, 3, 5, 9, 11–13, 15–17 |
| Evals: behavioral coverage | Task 25 |
| Distribution: `.skill` bundle | Task 26 |

No spec section is unaddressed.

---

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-05-02-slack-skill-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
