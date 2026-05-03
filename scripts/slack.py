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
