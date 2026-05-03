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
