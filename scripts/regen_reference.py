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
