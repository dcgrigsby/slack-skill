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
    if entry is None:
        raise ConfigError(
            f"workspace {name!r} not found\n"
            f"configured workspaces: {', '.join(sorted(workspaces)) or '(none)'}\n"
            "hint: run \"slack.py auth add --workspace " + name + " --token xoxp-...\""
        )
    token = entry.get("token")
    if not token:
        raise ConfigError(
            f"workspace {name!r} has no token (config may be corrupted)\n"
            "hint: run \"slack.py auth add --workspace " + name + " --token xoxp-...\""
        )
    return name, token


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
        if debug_log:
            debug_log(f"POST {SLACK_BASE}/{method} method={method} status={fixture['status']} elapsed=fixture (test mode)")
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
    """Call method repeatedly with cursor or page until exhausted or limit hit.

    Returns {"ok": True, "items": [...], "page_count": N}.
    Supports cursor-based pagination (response_metadata.next_cursor) and
    simple page-based pagination (top-level 'paging' object with 'page'
    and 'pages').
    Raises SlackAPIError on ok:false; TransportError on transport failure.
    """
    items: list = []
    page_count = 0
    cursor = ""
    page_num = 1  # for page-based methods; ignored for cursor-based
    use_page_mode: bool | None = None  # None until first response inspected

    while True:
        page_params = dict(params)
        if use_page_mode is True:
            page_params["page"] = page_num
        elif cursor:
            page_params["cursor"] = cursor
        _status, _hdrs, body = http_post(method, page_params, token, debug_log=debug_log)
        if not body.get("ok"):
            raise SlackAPIError(body, method)
        page_count += 1

        # Determine pagination mode from first response.
        if use_page_mode is None:
            paging = body.get("paging")
            if isinstance(paging, dict) and "pages" in paging:
                use_page_mode = True
            else:
                use_page_mode = False

        field = _detect_array_field(body)
        if field is None:
            raise ValueError(
                "cannot auto-detect array field for --all; pass without --all "
                "and paginate manually using response_metadata.next_cursor "
                "or paging.page (this method may have a nested array shape "
                "such as search.messages — those aren't auto-supported in v1)"
            )
        items.extend(body[field])

        if limit is not None and len(items) >= limit:
            items = items[:limit]
            break

        if use_page_mode:
            paging = body.get("paging", {})
            total_pages = paging.get("pages", 0)
            if page_num >= total_pages:
                break
            page_num += 1
        else:
            cursor = body.get("response_metadata", {}).get("next_cursor") or ""
            if not cursor:
                break

    return {"ok": True, "items": items, "page_count": page_count}


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


import argparse

# ---- argparse + dispatch ---------------------------------------------------


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

    if args.resolve and body.get("ok"):
        resolver = Resolver(token, debug_log=debug)
        body = walk_and_resolve(body, resolver)

    print(json.dumps(body, separators=(",", ":")))
    if not body.get("ok", False):
        print(format_slack_error(args.method, name, body), file=sys.stderr)
        return 1
    return 0


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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="slack.py",
        description="Slack Web API CLI for the slack-skill skill.",
    )
    p.add_argument("--version", action="version", version="slack.py 0.1.0")
    sub = p.add_subparsers(dest="cmd", required=False)

    # call
    pc = sub.add_parser("call", help="Invoke a Slack Web API method")
    pc.add_argument("method", help="Slack Web API method, e.g. conversations.history")
    pc.add_argument("--workspace", default=None,
                    help="Workspace name (from `auth list`); defaults to the configured `default`.")
    pc.add_argument("--params", default="{}",
                    help="JSON object of method params. Nested objects/arrays are JSON-stringified.")
    pc.add_argument("--resolve", action="store_true",
                    help="Walk the response and expand <@U..>/<#C..> refs to readable names.")
    pc.add_argument("--all", action="store_true", dest="all_pages",
                    help="Auto-paginate cursor-based responses; merges all pages into items.")
    pc.add_argument("--limit", type=int, default=None,
                    help="Cap on items collected when --all is set.")
    pc.add_argument("--debug", action="store_true",
                    help="Log HTTP requests to stderr (tokens redacted).")
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


if __name__ == "__main__":
    sys.exit(main())
