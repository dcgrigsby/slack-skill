#!/usr/bin/env python3
"""
package_skill.py — build a .skill bundle for distribution.

Tars the runtime skill files into <skill-name>.skill at the repo root.
Dev-only artifacts (test_slack.py, regen_reference.py, this script,
docs/plans/, docs/specs/) are deliberately excluded — they exist for
maintainers, not users.

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
    "scripts/slack.py",
    "docs/slack-api",
    "docs/slack-app-manifest.json",
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
