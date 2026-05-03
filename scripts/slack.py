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

import re

# ---- token utilities --------------------------------------------------------

TOKEN_RE = re.compile(r"(?:xox[a-z]|xapp)-[A-Za-z0-9-]+")


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


import json
import os
import sys
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
        print(f"config error: {p} is not valid JSON: {e}", file=sys.stderr)
        raise SystemExit(5)
    data.setdefault("workspaces", {})
    return data


def save_config(cfg: dict) -> None:
    """Atomically write cfg to the config path with mode 0700/0600."""
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(p.parent, 0o700)
    except OSError:
        pass
    tmp = p.with_suffix(p.suffix + ".tmp")
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
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


import time
import urllib.error
import urllib.parse
import urllib.request

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
    except OSError as e:
        raise TransportError(f"test fixture file unreadable: {e}")
    except json.JSONDecodeError as e:
        raise TransportError(f"test fixture file is not valid JSON: {e}")
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
            debug_log(f"POST {redact(url)} method={method} status={status} elapsed={elapsed:.2f}s attempt={attempt}")

        # Retry on 5xx (once).
        if 500 <= status < 600 and attempt == 1:
            time.sleep(1.0)
            continue

        # Retry on 429 with short Retry-After.
        if status == 429 and attempt == 1:
            try:
                retry_after = int(hdrs.get("retry-after", "0") or "0")
            except ValueError:
                retry_after = 0  # Unparseable → don't sleep; raise.
            if 0 < retry_after <= 30:
                time.sleep(retry_after)
                continue
            raise SlackAPIError(
                {"ok": False, "error": "ratelimited", "retry_after": retry_after},
                method,
            )

        if not raw:
            raise TransportError(f"empty body from {method} (status={status})")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise TransportError(f"non-JSON response from {method}: {raw[:200]}")
        if not isinstance(parsed, dict):
            raise TransportError(
                f"unexpected response shape from {method}: "
                f"got {type(parsed).__name__}, expected object"
            )

        return status, hdrs, parsed

    raise TransportError(f"unreachable: retry loop exited for {method}")


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
        "hint: the user is not a member of that channel. For public channels "
        "call conversations.join with the channel ID. Private channels require "
        "an existing member to invite you."
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
        "hint: Slack returned 429; retry_after={retry_after}s. "
        "Wait that long and retry, or narrow the query."
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
            retry_after=response.get("retry_after", "?"),
        )
    except (KeyError, IndexError):
        body = template
    return f"{head}\n{body}"


import argparse


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
