# Slack Skill — Design

**Date:** 2026-05-02
**Status:** Approved (brainstorming complete; ready for implementation planning)
**Slug:** `slack`
**Repo (intended):** `github.com/dcgrigsby/slack-skill`
**Install:** `npx skills add dcgrigsby/slack-skill -g -a claude-code -a gemini-cli -a codex -a pi -y`

---

## Overview

A portable, harness-agnostic skill that gives Claude (or any skill-aware
agent) read/write access to the user's Slack workspaces via the Slack Web
API, acting **as the user** with a User OAuth Token (`xoxp-...`). Bundles
a single Python 3 helper script (`scripts/slack.py`) and progressive-
disclosure API documentation. No server, no daemon, no compilation, no
external dependencies beyond Python 3 (which ships with macOS).

The skill mirrors the architectural pattern of the existing
`obsidian-skill` and `omnifocus-skill`: a thin script in `scripts/`,
doc tiers in `docs/`, no build step, runs immediately. It is
deliberately complementary to the existing `slack2omnifocus` project,
which is a single-purpose deterministic daemon; this skill is a generic
interactive surface. Both can coexist on the same workspace, ideally
via separate Slack apps.

## Goals

- Read and write Slack on the user's behalf via direct Web API calls,
  with a single thin Python helper.
- Cover the full surface of user-token API capabilities: read messages,
  send messages, react, mark read, search, navigate channels and DMs,
  resolve user/channel references — anything Slack exposes to a User OAuth
  Token.
- Work in any harness with skill support (Claude Code first, plus others
  via `npx skills`).
- Trigger reliably on natural phrasings — read, send, react, search,
  permalink, set-up, multi-workspace, error recovery.
- Stay generic and forkable. Personal workflow conventions (channel
  routing, message templates, status update formats) belong in a separate
  workflow skill, not here.
- Make first-time setup fully driveable from a chat session: the LLM
  walks the user through Slack app creation, scope grants, and token
  capture, then runs the `auth add` command itself.

## Non-goals

- Bot tokens (`xoxb-...`) and Slack Apps with bot users. This skill
  represents *the user*. `auth add` rejects bot-shaped tokens.
- Socket Mode / RTM / WebSocket subscriptions. Request/response only;
  no daemon.
- File uploads (multipart). `files.read` and `files.list` are supported;
  uploads are deferred until needed.
- Sandboxing, per-call confirmation, or cross-invocation rate-limit
  smoothing. Each invocation is independent.
- Tests against the real Slack API bundled with the skill. Mechanical
  offline tests only; manual verification is part of the release
  checklist.
- Linux / Windows for v1. macOS only. Stdlib code is portable; config
  paths and setup docs aren't yet generalized.
- User-specific workflow conventions (separate skill).

## Architecture

### Directory layout

```
slack-skill/
├── SKILL.md                 # frontmatter + body (common patterns inline)
├── README.md                # install, scope setup, safety, examples
├── LICENSE                  # Apache 2.0 (carry over from slack2omnifocus)
├── NOTICE                   # safety warning (adapt from slack2omnifocus)
├── Makefile                 # test, package, regen-reference, clean
├── .gitignore
├── scripts/
│   ├── slack.py             # the CLI (Python 3 stdlib only)
│   ├── test_slack.py        # mechanical test suite
│   └── regen_reference.py   # fetch Slack OpenAPI → docs/slack-api/FULL-REFERENCE.md
├── docs/
│   ├── specs/
│   │   └── 2026-05-02-slack-skill-design.md   # this document
│   ├── slack-app-manifest.yaml                # paste-into-Slack manifest
│   └── slack-api/
│       ├── CHEATSHEET.md
│       ├── Conversations.md
│       ├── Chat.md
│       ├── Reactions.md
│       ├── Users.md
│       ├── Search.md
│       ├── Files.md
│       ├── Pins-Stars-Bookmarks.md
│       └── FULL-REFERENCE.md                   # generated from OpenAPI
└── evals/
    └── evals.json
```

### Doc tiers

**Tier 1 — `SKILL.md` body (always loaded).** Hot-path patterns inline
with full bash examples:

1. First-time setup / adding a workspace
2. Resolve channel/user names to IDs
3. Read recent messages from a channel or DM
4. Read a full thread (parent + replies)
5. Send a message (channel, DM, thread reply)
6. React / unreact
7. Mark a channel read up to a message
8. List my channels and DMs
9. List members of a channel
10. Search across my messages
11. Get a permalink for a message

**Tier 2 — `docs/slack-api/CHEATSHEET.md` (load when SKILL.md is
insufficient).** One-line-per-method map grouped by namespace, with
required params, required scopes, and pagination flags. Target: ~300
lines covering every method useful with a User OAuth Token.

**Tier 3 — Per-namespace files (`Conversations.md`, `Chat.md`, etc.).**
Focused references with examples and edge-case notes; load only the
relevant file.

**Tier 4 — `docs/slack-api/FULL-REFERENCE.md` (niche only).** Generated
from Slack's OpenAPI v2 spec via `scripts/regen_reference.py`,
committed to the repo so the LLM has it locally. Loaded only for
methods not covered by the focused files.

(Four tiers — the same structure as omnifocus-skill but adds focused
per-namespace files between cheatsheet and full reference, since
Slack's API surface is wider.)

### Data flow per LLM-driven operation

1. User asks something Slack-shaped.
2. Harness loads `SKILL.md`. For coverage beyond the body, the LLM reads
   `CHEATSHEET.md`, then a per-namespace file, then `FULL-REFERENCE.md`
   only when needed.
3. LLM invokes `python3 scripts/slack.py call <method> --workspace <name>
   --params '<json>'` (and optionally `--resolve`, `--all`, `--limit`).
4. The script POSTs to `https://slack.com/api/<method>` with the user
   token and form-encoded params, returns the response JSON to stdout.
5. LLM reads JSON, optionally re-calls with `--resolve` for entity
   expansion, composes the next call.

## CLI surface

### Subcommands

```
slack.py call <method> [--workspace NAME] [--params JSON] [--resolve] [--all] [--limit N] [--debug]
slack.py auth list
slack.py auth add --workspace NAME --token xoxp-...
slack.py auth remove --workspace NAME
slack.py auth default --workspace NAME
slack.py auth test [--workspace NAME]
slack.py doctor
```

### `call` — primary surface

POSTs to `https://slack.com/api/<method>` with form-encoded `--params`,
returns response JSON to stdout.

**Workspace selection** (precedence):

1. `--workspace NAME` → look up in `~/.config/slack-skill/config.json`.
2. `default` workspace from `config.json`.
3. Otherwise: exit 5 with a fix hint.

(No `SLACK_TOKEN` env var fallback. Workspace names are the only handle.)

**Params handling.** `--params '{"channel":"C123","text":"hi"}'` →
form-encoded for POST body. Nested objects/arrays (e.g., `blocks`) are
JSON-stringified before form encoding — exactly what Slack expects.

**Pagination.**

- Default: single page; full Slack envelope incl. `response_metadata.next_cursor`.
- `--all`: auto-loop until the cursor empties or `--limit N` is reached.
  Returns a synthetic envelope:
  `{"ok": true, "items": [...merged...], "page_count": N}`.
- The merged array is auto-detected (the single top-level array field —
  `messages`, `members`, `channels`, etc.). If multiple top-level arrays
  exist, error with usage hint.

**Resolution (`--resolve`).** Walks the response and expands entity refs
in any string field:

- `<@U07ABC>` → `@<display_name>` (cached `users.info`)
- `<@U07ABC|alice>` → `@alice` (inline label, no lookup)
- `<#C123>` → `#<channel_name>` (cached `conversations.info`)
- `<!here>` / `<!channel>` / `<!subteam^S1|@team>` → broadcast / label
- `<https://url>` → `https://url`; `<https://url|text>` → `text`
- `<mailto:a@b.com>` → `a@b.com`

Caches lookups for the lifetime of the invocation. On lookup failure
(missing scope, deleted user), falls back to readable `@U07ABC` /
`#C456`. Logic ported from
`slack2omnifocus/internal/slack/client.go:195-265`.

### `auth` — workspace management

- `auth list` — prints workspaces with masked tokens; default starred.
- `auth add --workspace NAME --token xoxp-...` — validates token format
  (rejects `xoxb-`), runs `auth.test` first, refuses to write on failure;
  on success populates team/user metadata. First workspace becomes
  default automatically.
- `auth remove --workspace NAME` — deletes entry; clears `default` if it
  pointed at the removed workspace.
- `auth default --workspace NAME` — sets `default`; errors if the
  workspace isn't configured.
- `auth test [--workspace NAME]` — calls `auth.test`, prints user_id,
  team, and the scopes the token actually has (from response headers).
  Without `--workspace`, tests every configured workspace.

### `doctor`

End-to-end self-check: config exists, mode 600, Python ≥ 3.9, every
configured workspace's `auth.test` passes. Plain-text output suitable
for both human and LLM consumption.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Slack API error (`ok: false`) — full response on stdout, summary on stderr |
| 2 | Usage error (bad args, malformed `--params` JSON) |
| 3 | Transport error (DNS / TCP / TLS / timeout) |
| 5 | Config / auth error (workspace not found, no token available) |

### Output conventions

- **Stdout:** compact JSON only (`json.dumps(obj)`, no indent). Same
  spirit as omnifocus-skill's `JSON.stringify(...)`.
- **Stderr:** human-readable diagnostics, one line where possible.

### Examples

```bash
# Read latest 20 messages from #general
python3 scripts/slack.py call conversations.history --workspace work \
  --params '{"channel":"C0123","limit":20}'

# Same, with @user / #channel refs expanded
python3 scripts/slack.py call conversations.history --workspace work \
  --params '{"channel":"C0123","limit":20}' --resolve

# Send a DM
python3 scripts/slack.py call chat.postMessage --workspace work \
  --params '{"channel":"D0456","text":"running 5 late"}'

# React to a message
python3 scripts/slack.py call reactions.add --workspace work \
  --params '{"channel":"C0123","timestamp":"1712345678.123456","name":"thumbsup"}'

# Walk every channel/DM I'm in
python3 scripts/slack.py call users.conversations --workspace work \
  --params '{"types":"public_channel,private_channel,im,mpim"}' --all
```

## Auth & config

### Config location

`~/.config/slack-skill/config.json` (XDG Base Directory). Consistent
with `slack2omnifocus`'s state path under `~/.local/state/`.

### Schema

```json
{
  "default": "work",
  "workspaces": {
    "work": {
      "token": "xoxp-...",
      "team_id": "T01ABC",
      "team_name": "Acme",
      "user_id": "U01XYZ",
      "user_name": "dan"
    },
    "personal": {
      "token": "xoxp-..."
    }
  }
}
```

`token` is required; metadata fields are populated by `auth add` after a
successful `auth.test` and exist purely for readable `auth list` output.
The CLI doesn't depend on metadata.

### File and directory modes

- Directory: `0700`
- File: `0600`

Set at creation time, not chmod'd after — `os.umask(0o077)` before
`mkdir`, and writes via `os.open(path, O_CREAT | O_WRONLY | O_TRUNC,
0o600)` so there's no window where a fresh file is briefly world-
readable.

### Atomic writes

Mutations write to `config.json.tmp`, fsync, rename. No file locking;
concurrent invocations against the same config file are unsupported and
documented as such.

### Token security rules

- Never logged, even with `--debug`.
- Never printed to stdout.
- `auth list` masks tokens (`xoxp-***...***`).
- Errors include workspace *name* but never token *value*.
- Stack traces suppressed in normal operation; opt in via `--debug`.
- Token-shaped strings (`xoxp-`, `xoxb-`, `xapp-`) in any logged URL,
  header, or param are unconditionally replaced with `xoxp-***...***`
  before stderr emission.

### Setup flow (one-time, per workspace)

1. User: create a new Slack app from `docs/slack-app-manifest.yaml`
   (paste into "Create New App → From an app manifest"). One paste.
2. User: click **Install to Workspace** → **Allow** → copy the User
   OAuth Token. Paste it into chat.
3. LLM: `python3 scripts/slack.py auth add --workspace <name> --token xoxp-...`
4. LLM: `python3 scripts/slack.py auth test --workspace <name>` to
   verify and report scopes.

The LLM drives steps 3–4 directly. Steps 1–2 require the user's
browser; the LLM walks the user through them with exact URLs and the
manifest YAML inline.

## App manifest

`docs/slack-app-manifest.yaml`:

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

The README points users at the manifest as the recommended setup path;
manual scope-clicking is the documented fallback. The README also
explicitly tells users to **create a new Slack app for this skill, not
reuse a token from another integration** (e.g., `slack2omnifocus`).
Different scope sets, separate revocation, and clean credential
boundaries are simpler this way.

## Errors, retries, rate limits, debug

### Error taxonomy

| Category | Exit | Stdout | Stderr |
|----------|-----:|--------|--------|
| Success (`ok: true`) | 0 | response JSON | (empty) |
| Slack API error (`ok: false`) | 1 | response JSON | summary + hint |
| Usage error | 2 | (empty) | message + usage hint |
| Transport error | 3 | (empty) | message |
| Config / auth error | 5 | (empty) | message + fix hint |

Two invariants: **stdout always carries the structured data**, and
**stderr always carries an actionable hint**.

### Slack API errors (`ok: false`)

Slack returns HTTP 200 with `{"ok": false, "error": "..."}`. The CLI
exits 1, emits the full response on stdout, and prints a one-line
summary on stderr with curated hints for common errors:

- `missing_scope` → `needs: <scope>; current: <list>; hint: reinstall the app with the missing scope, then refresh the token.`
- `channel_not_found` → `hint: use conversations.list or users.conversations to discover channel IDs.`
- `not_in_channel` → `hint: the user is not a member of that channel; join it first or use a different channel.`
- `invalid_auth` / `token_revoked` → `hint: re-run "slack.py auth add" to refresh the token.`
- `account_inactive` → `hint: the Slack account is suspended.`
- Default: error code, workspace, and method.

### Transport errors

DNS / TCP / TLS / read timeout. Exit 3, empty stdout, single-line stderr.
Default timeouts: 10s connect, 30s read.

### Rate limits

| Condition | Behavior |
|-----------|----------|
| 429 + `Retry-After` ≤ 30s | Sleep, retry once. |
| 429 + `Retry-After` > 30s | Exit 1, surface wait info on stderr. |
| Still 429 after retry | Exit 1, surface error. |
| HTTP 5xx | Sleep 1s, retry once. |

The 30s cap prevents long silent hangs during the LLM's turn.

### `--debug`

Off by default. When enabled, logs every HTTP request to stderr with
elapsed time, retries, pagination cursors, and resolution cache stats.
**Token redaction is unconditional**, even with `--debug`.

### Pagination + errors

If `--all` fails mid-loop, partial results are NOT returned. The script
exits with the appropriate error code. (No `--continue-on-error` for v1.)

### `--resolve` + lookup failures

A single failed resolution (missing scope, deleted user, etc.) doesn't
fail the whole call: that ref falls back to `@U07ABC` / `#C456`, the
rest of the response is processed normally. Failures logged to stderr
only with `--debug`.

## Required Slack scopes

User Token Scopes, listed in the README (mirrors the slack2omnifocus
README style):

- `channels:history`, `groups:history`, `im:history`, `mpim:history` — read messages
- `channels:read`, `groups:read`, `im:read`, `mpim:read` — list/info channels and DMs
- `chat:write` — send messages
- `reactions:read`, `reactions:write` — reactions
- `users:read`, `users.profile:read` — user info / display names
- `search:read` — search across messages
- `files:read` — list/inspect files (write deferred — multipart out of scope for v1)
- `pins:read`, `pins:write`, `bookmarks:read`, `bookmarks:write`,
  `stars:read`, `stars:write` — niche but commonly useful

Adding scopes later requires re-clicking **Install to Workspace** to
refresh the token. README documents this.

## Testing

### Mechanical tests (`scripts/test_slack.py`, `make test`)

All offline, no network. Coverage:

- Argparse: every subcommand and flag combination, error paths.
- `--params` JSON parsing and form-encoding (incl. nested → JSON-stringified).
- `--resolve` walker: every entity-ref form (`<@U>`, `<@U|label>`,
  `<#C>`, `<#C|label>`, `<!here>`, `<!subteam^...>`, `<!date^...>`,
  `<https://...|text>`, `<mailto:...>`), with mocked lookup + fallback
  on lookup failure.
- `--all` pagination: mock HTTP returns multi-page synthetic responses,
  verify items concatenated and `--limit` truncates correctly.
- Config read/write: round-trip JSON, atomic rename, file modes,
  masking in `auth list`.
- Error formatting: every exit code, every curated hint string.
- Token redaction: confirm tokens never appear in stderr for any path,
  including `--debug`.

HTTP mocking via a stub that intercepts `urllib.request.urlopen`. Same
pattern as `slack2omnifocus`'s test suite.

### No bundled integration tests against the real Slack API

Matches obsidian-skill's pattern. Manual verification against a real
workspace is part of the release checklist, not CI.

## Evals

`evals/evals.json` — `{id, name, prompt, expected_output}` triples,
modeled directly on `omnifocus-skill/evals/evals.json`. Coverage:

| Category | Example prompt |
|----------|---------------|
| Setup | "Set up Slack for my work workspace" |
| Read recent | "What's new in #general today?" |
| Read thread | "Summarize the thread at this permalink: ..." |
| Send DM | "DM bob saying I'm running 5 late" |
| Send to channel | "Post to #ops: deploy is done" |
| React | "React to that message with eyes" |
| Mark read | "Mark #general as read up to the latest message" |
| List channels | "What channels and DMs am I in?" |
| Search | "Find messages where alice mentioned 'launch'" |
| Permalink | "Get me a link to that message" |
| Multi-workspace | "Send the same message to both my work and personal Slack" |
| Error recovery | "Read #private-channel" (LLM should detect `not_in_channel` and explain) |
| Cross-skill | "Post the result of my OmniFocus weekly review to #status" |

## Risks & dependencies

| Risk | Mitigation |
|------|-----------|
| Python 3.9 requirement | macOS ships 3.9; documented as the minimum. Stdlib only, no `tomllib`, no PEP 723. |
| Slack API changes | Methods pass through verbatim — additions/changes don't break the CLI. Doc drift handled by `make regen-reference`. |
| Token leak | File mode 0600 set at open time, masking in all output, no logging on success path, unconditional `--debug` redaction. |
| Rate limits stalling LLM turn | 30s cap on auto-retry; longer waits surface as exit-1 errors with hints. |
| Slack OpenAPI spec drift | Full reference is regen-on-demand. Cheatsheet is the primary hand-maintained doc. |
| `--resolve` lookup amplification (N+1) | Per-invocation cache + fallback to readable form on failure. Documented as a known cost on large reads. |
| Concurrent invocations against same `config.json` | Documented as unsupported. Atomic write minimizes tail risk; no locking. |

## Relationship to existing projects

- **`slack2omnifocus`** keeps running unchanged. It's a deterministic
  single-purpose daemon; this skill is a generic interactive surface.
  Recommended: separate Slack apps, separate tokens, separate
  revocation. The two never share state.
- **`obsidian-skill`** is the structural template. This skill mirrors
  its layout (Makefile, scripts/, evals/, mechanical tests).
- **`omnifocus-skill`** is the doc-tier template. This skill mirrors
  its three-tier API doc structure (cheatsheet → focused per-area files
  → full reference) and its instructional tone for inline patterns.
- **`personal-workflow`** (your existing workflow skill) layers on top
  of this skill for content routing — this skill stays generic.

## Handoff

After this design is approved, the next step is the
[`writing-plans`](../../) skill, which produces a step-by-step
implementation plan covering scaffolding, CLI implementation, config
layer, doc tiers, evals, manifest, and SKILL.md content.

Implementation then runs via `executing-plans` and/or
`subagent-driven-development`.
