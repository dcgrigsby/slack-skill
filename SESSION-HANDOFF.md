# slack-skill — Session Handoff (2026-05-03)

This doc summarizes the state of the slack-skill build at the end of a long
multi-phase session: brainstorming → spec → implementation plan → 27-task
subagent-driven implementation → final whole-implementation review with
fixes. A fresh session can read this top-to-bottom and pick up.

A second session (later same day) ran the skill-creator loop on top:
description optimization, two test additions, manifest reformat, and a
live-eval pass against a real Slack workspace. See **Session 2 update**
below for diffs.

---

## TL;DR (current)

- Repo: https://github.com/dcgrigsby/slack-skill (public, Apache 2.0)
- Branch: `main`, working tree clean, all commits pushed.
- Latest commit: `2fe40e3` — "Drop two manifest keys Slack's editor rejected"
- Tests: **59 passed, 0 failed** (`make test`)
- Bundle: `make package` produces `slack-skill.skill` (~96 KB)
- Manifest is now `docs/slack-app-manifest.json` (paste-into-Slack as JSON,
  35 user scopes, app name "cli")
- Skill validated end-to-end against a real Slack workspace (Advocate);
  11 of 13 evals exercised, all passed; sandbox cleaned up.
- **Status: shipped + dogfooded.** v1.1 backlog still tracked below;
  nothing currently in flight.

---

## What was built (component summary)

### `scripts/slack.py` (~770 lines, Python 3.9+ stdlib only)

A single-file CLI exposing the Slack Web API to LLM-driven workflows.
Sections (in order, separated by `# ----` banners):

1. Token utilities — `validate_user_token`, `mask_token`, `redact`, `TOKEN_RE`
   covering `xox?-` and `xapp-` families.
2. Config layer — `config_path`, `load_config`, `save_config`. Atomic writes
   via temp+rename. File mode 0600 set at `os.open` time, not chmod after.
   Honors `$SLACK_SKILL_CONFIG` for tests.
3. Workspace resolution — `resolve_token`, `ConfigError`. Precedence:
   `--workspace NAME → cfg["default"] → ConfigError`. Defensive guard against
   missing/empty `token` field on a hand-edited config.
4. HTTP transport — `http_post`, `_encode_params`, `_consume_test_fixture`,
   `TransportError`, `SlackAPIError`. Form-encoding with nested objects/arrays
   JSON-stringified. Retries once on 5xx (1s) and 429 (Retry-After ≤ 30s).
   429 over the cap raises `SlackAPIError("ratelimited")` with `retry_after`
   in the response. Rejects non-dict JSON bodies as `TransportError`.
   Honors `$SLACK_SKILL_TEST_RESPONSES` (FIFO JSON file) for tests, fails
   loud if fixture file is missing/corrupt rather than falling through to
   real network.
5. Slack API error interpretation — `HINTS` dict (7 curated entries),
   `format_slack_error`. Hints are accurate: `not_in_channel` distinguishes
   public (call `conversations.join`) from private (must be invited);
   `ratelimited` substitutes the actual `retry_after` value.
6. Pagination — `_detect_array_field`, `paginate`. Handles cursor-based
   (`response_metadata.next_cursor`) AND simple page-based (`paging.pages` /
   `paging.page`) responses. Synthesizes `{"ok": True, "items": [...],
   "page_count": N}` envelope. Limit truncates exact. Fails loud on
   ambiguous (multi-array) responses with a hint.
7. Entity-ref resolver — `Resolver` class (per-invocation cache),
   `walk_and_resolve`. Ports `slack2omnifocus/internal/slack/client.go:195-265`.
   All entity types covered: `<@U>`, `<@U|label>`, `<#C>`, `<#C|label>`,
   `<!here>`, `<!subteam^...|label>`, `<!date^...|label>`, URLs, mailto.
   Lookup failures fall back to readable form, cached so retries don't
   stampede.
8. argparse + dispatch — `cmd_call`, `cmd_auth_{add,list,remove,default,test}`,
   `cmd_doctor`, `build_parser`, `main`.

### Helper scripts

- `scripts/test_slack.py` — 47 mechanical tests, subprocess-driven, no
  network. Tests use `make_env(tmpdir, responses=...)` to thread
  `$SLACK_SKILL_CONFIG` and `$SLACK_SKILL_TEST_RESPONSES` per case.
- `scripts/regen_reference.py` — fetches Slack's OpenAPI v2 spec and emits
  `docs/slack-api/FULL-REFERENCE.md`. Run via `make regen-reference`.
- `scripts/package_skill.py` — tars `SKILL.md`, `scripts/`, `docs/`,
  `evals/`, `LICENSE`, `NOTICE`, `README.md` into `slack-skill.skill`.

### Documentation tiers

- `SKILL.md` (409 lines) — frontmatter + 11 inline patterns + first-time
  setup walkthrough + tier discovery + error recovery + tips.
- `docs/slack-api/CHEATSHEET.md` (132 lines, 78 methods) — Tier-2 compact
  one-line-per-method map.
- `docs/slack-api/Conversations.md`, `Chat.md`, `Reactions.md`, `Users.md`,
  `Search.md`, `Files.md`, `Pins-Stars-Bookmarks.md` — Tier-3 per-namespace
  docs (1643 lines total, 52 methods covered).
- `docs/slack-api/FULL-REFERENCE.md` (2564 lines) — Tier-4 generated from
  Slack's OpenAPI v2 spec. Regenerable via `make regen-reference`.
- `docs/slack-app-manifest.yaml` — paste-into-Slack manifest with **26 user
  scopes** (expanded from the original 21 to cover SKILL.md hot paths).
- `README.md` (190 lines) — install, setup, scope walkthrough, safety,
  multi-workspace, troubleshooting.

### Evals

- `evals/evals.json` — 13 behavioral evals (`SKILLTEST_` prefix on
  side-effecting prompts).

### Build

- `Makefile` — `test`, `package`, `regen-reference`, `clean`, `help`.
- `LICENSE` — Apache 2.0.
- `NOTICE` — Slack-specific safety warning (acts AS YOU, audit logs
  attribute to user, no silent rollback for edits/deletions, etc.).
- `.gitignore` — `__pycache__/`, `*.pyc`, `*.skill`, `.test-tmp/`.

---

## What was caught and fixed during full-rigor review

The 27-task subagent-driven flow with implementer + spec reviewer + code
quality reviewer per task caught and fixed *during* the build:

1. Plan doc drift (`1 passed` → `2 passed` after smoke test had 2 case() calls)
2. `TOKEN_RE` missing `xoxc-`/`xoxe-`/`xapp-` (security gap)
3. `SystemExit("string")` exiting code 1 instead of documented 5
4. `int(Retry-After)` crashing on HTTP-date values
5. Non-dict JSON bodies (`null`, `[]`) bypassing the type contract
6. `_consume_test_fixture` silently falling through to real network
7. `entry["token"]` `KeyError` on hand-edited config (and the prior
   `if not entry:` treating empty dict as "not found")
8. `not_in_channel` hint conflating public/private channel recovery
9. `ratelimited` hint not surfacing the actual `retry_after` value

The **whole-implementation final review** then caught emergent issues no
per-task review surfaced:

10. `paginate()` only handled cursor-based — page-based methods (search,
    files, stars) silently truncated to page 1 despite docs claiming
    otherwise. **Fixed**: added page-based mode that detects `paging.pages`
    and increments `page` between calls.
11. Default manifest missing scopes for SKILL.md hot paths:
    `users:read.email`, `im:write`, `mpim:write`, `channels:write`,
    `groups:write`. **Fixed**: manifest expanded to 26 scopes.
12. SKILL.md / per-namespace docs claimed "`--all` handles both" for
    page-based shapes. **Fixed**: SKILL.md tightened to be honest about
    the `search.messages` nested-array limitation.

All fixes are in commit `2d5a07d`. The pre-fix state is `2eb4477`.

---

## Session 2 update (2026-05-03 evening)

Picked up via `/skill-creator`. Four commits on top of `2d5a07d`:

| Commit | Summary |
|---|---|
| `e5e9a12` | Restructured SKILL.md description into intent / signals / non-targets paragraphs. Selected by `skill-creator/scripts/run_loop.py` over 5 iterations on a 20-query trigger eval set (12 train / 8 test). Marginal score gain — the absolute pass rate is bottlenecked by **`agent-browser`'s description claiming Slack** ("checking Slack unreads, sending Slack messages, searching Slack conversations"), which competes for the same triggers. The rewrite is structurally clearer regardless. |
| `5499c58` | Added 3 new tests, +12 assertions: `test_call_all_page_based_merges_pages` (regression guard for the silent-truncate-to-page-1 bug fixed in `2d5a07d`), `test_doctor_reports_ok_for_healthy_workspace`, `test_doctor_reports_failure_on_auth_test_error`. Also gitignored `slack-workspace/` for skill-creator artifacts. 47 → 59 passing. |
| `0eceaa5` | Switched `docs/slack-app-manifest.yaml` → `docs/slack-app-manifest.json` (Slack's editor was rejecting the YAML form). Renamed app to `cli` with description "User API Access for Slack Skill via Command Line". Expanded scope set 26 → 36 to cover every method documented in CHEATSHEET / FULL-REFERENCE. |
| `2fe40e3` | Followup: dropped `features.bot_user: null` (Slack now rejects it; omitting the block is the correct way to declare no bot user) and `chat:write.public` (bot-only, "Illegal user scope found"). Final: **35 user scopes**, no `features` block. |

Doc-reference updates (filename `.yaml`→`.json`, "switch editor tab to JSON"
note) propagated through SKILL.md and README.md. Historical files
(`docs/specs/`, `docs/plans/`) intentionally left as snapshots.

### Live-eval pass against Advocate workspace

Installed manifest, generated `xoxp-` token, ran 11 of 13 evals
qualitatively against the real workspace. Used a self-created private
channel `#skill-sandbox` (since archived) and DM-to-self for write
evals. Skipped eval 10 (no second workspace) and eval 12 (no OmniFocus
loaded). All 11 passed end-to-end:

- Reads (1, 2, 7, 8, 11) — `conversations.history --resolve`,
  `conversations.replies`, `users.conversations`, `search.messages`,
  and the `channel_not_found` hint chain all worked first-try.
- Writes (3, 4) — DM and channel post both succeeded; messages were
  attributed to the user (verified visually by the user — `bot_profile`
  field in the API response is metadata only, not display).
- Derived (5, 6, 9) — react / mark / permalink each followed the
  `conversations.history limit=1 → act on ts` pattern cleanly.

Cleanup: 2 SKILLTEST DMs deleted via `chat.delete`, sandbox archived
via `conversations.archive`. (Slack API doesn't expose channel delete
for user tokens; archive is the equivalent.)

### What's worth knowing for the next session

- **`agent-browser` competes for Slack triggers.** Its installed
  description names Slack actions explicitly. The SKILL.md description
  optimizer hit a ceiling around 50–55% trigger rate that wording
  alone can't break through. Real fix would require editing
  `agent-browser` (out of scope for this skill).
- **Slack's manifest editor rejects `features.bot_user: null` and
  `chat:write.public` as a user scope.** Both omissions verified
  against the live editor 2026-05-03. If the manifest is regenerated
  from the spec, these need to stay omitted.
- **The skill correctly impersonates the user** even though the API
  response includes `bot_id` / `bot_profile` for the cli app. Slack
  shows the message as from the user in the client UI. The
  `as_user=true` parameter is not needed.

---

## Open issues (deferred, non-blocking)

These were noted by the final reviewer but not fixed. They're polish for
v1.1, not correctness blockers.

### Deliberately scoped out

- **`search.messages` auto-pagination** — has a nested-array shape
  (`messages.matches`) that doesn't match the simple top-level array
  detection. Documented in SKILL.md and Search.md as "use manual
  `--params page=N` stepping for now." Fix would mean teaching `paginate()`
  about nested array paths. Out of scope for v1.
- **`files.upload`** — multipart upload not implemented in v1. Documented
  in `Files.md` with a curl workaround.
- **Linux/Windows config paths** — macOS only for v1. Stdlib code is
  portable; only the install/setup docs and config-path resolution would
  need adjustment.
- **Bundled integration tests against real Slack** — by design, manual
  verification only. Mechanical tests cover the CLI surface.

### Known minor inconsistencies

- **`auth list`, `auth test`, `doctor` output goes to stdout** — they
  print human-readable status (not JSON), so arguably stderr would be
  more consistent with the file's "stdout = structured data, stderr =
  diagnostics" header. Debatable; not a bug.
- **Bundle includes `docs/specs/`, `docs/plans/`, dev-only scripts** —
  about 30 KB of dead weight in a 96 KB bundle. `package_skill.py`'s
  `INCLUDE` list whitelists `docs/` and `scripts/` wholesale.
- **`missing_scope` hint says `needed:` / `provided:`** — spec said
  `needs:` / `current:`. Trivial wording delta.
- **Synthetic 429 response on long Retry-After loses original Slack body**
  (`scripts/slack.py:273-276`). The retry_after is preserved; other
  response fields aren't.
- **Eval id 11 (`error_recovery_not_in_channel`) prompts "Read
  #private-im-not-in"** — but `conversations.history` on a private
  channel the user isn't in returns `channel_not_found`, not
  `not_in_channel`. The eval's framing still works (LLM should detect the
  error and explain) but the curated hint will be the
  `channel_not_found` one.

### Test coverage gaps the final reviewer flagged

These would tighten the test suite if added. Items closed in session 2
(`5499c58`) are crossed out.

- ~~No test for `cmd_doctor`~~ — added (happy-path + auth-test-failure).
- No test for the transport-error exit-3 path (force `urlopen` to fail).
- ~~No test for page-based pagination~~ — added; covers the
  silent-truncate-to-page-1 regression fixed in `2d5a07d`.
- No test for `--resolve` triggering an actual `users.info` lookup with a
  successful response (only inline-label and lookup-failure-fallback are
  tested).
- No test for `--all` limit boundary cases (limit lands on page boundary,
  limit > total available).
- No test verifying multi-workspace token masking in `auth list`.
- No test for `xapp-`/`xoxc-`/`xoxe-` token rejection (only `xoxb-`).
- No test for malformed `--params` JSON exit-2 path.
- No test verifying directory mode 0700.
- No test verifying argparse help contains every subcommand (regression
  guard).

### Stretch items mentioned during build

- **Direct unit tests for `format_slack_error`, `_encode_params`,
  `_consume_test_fixture`** — these are pure functions; subprocess tests
  exercise them transitively but a regression in any one would currently
  surface as a confusing downstream test failure.
- **Imports scattered through `slack.py`** — section-local imports were
  the easiest path during the build; a follow-up cleanup pass could
  consolidate at the top of the file (~5 import groups → 1).
- **Resolver should surface lookup errors on stderr** — currently
  swallows TransportError + SlackAPIError silently. A "12 of 47
  references could not be resolved (rate-limited?)" warning at the end
  of `cmd_call` would close the silent-degradation gap. Important but
  not critical per the reviewer.
- **Resolver N+1 lookup pattern** — 50 unique user mentions = 50
  sequential `users.info` calls (~10s added to a `--resolve` call).
  Could batch via `concurrent.futures` ThreadPoolExecutor (stdlib).

---

## How to verify the current state

From `/Users/dan/slack-skill`:

```bash
# Tests pass
make test                              # → 59 passed, 0 failed

# Bundle builds and cleans
make package
ls -la slack-skill.skill               # → ~96 KB
make clean

# Git state
git status                             # → clean
git log --oneline -5                   # → 2fe40e3 at top
git remote -v                          # → origin = github.com:dcgrigsby/slack-skill.git

# Smoke test the CLI (no network, fixtures)
bash -c '
TMP=$(mktemp -d)
echo "[{\"status\":200,\"headers\":{},\"body\":{\"ok\":true,\"user_id\":\"U\",\"user\":\"alice\",\"team_id\":\"T\",\"team\":\"Acme\"}}]" > "$TMP/r.json"
SLACK_SKILL_CONFIG="$TMP/c.json" SLACK_SKILL_TEST_RESPONSES="$TMP/r.json" python3 scripts/slack.py auth add --workspace smoke --token xoxp-smoke
SLACK_SKILL_CONFIG="$TMP/c.json" python3 scripts/slack.py auth list
rm -rf "$TMP"
'
```

The **manual follow-up** the test suite can't cover: install on a real
Slack workspace and exercise a real call. Steps:

1. Visit https://api.slack.com/apps?new_app=1 → **From an app manifest**.
2. Pick a workspace, **switch the editor tab to JSON**, paste
   `docs/slack-app-manifest.json`, click Create.
3. Click **Install to Workspace** → **Allow**.
4. Copy the User OAuth Token (`xoxp-...`) from OAuth & Permissions.
5. `python3 scripts/slack.py auth add --workspace test --token xoxp-...`
6. `python3 scripts/slack.py auth test --workspace test` → expect OK with
   team/user/scopes including all 35 (Slack also adds `identify`
   automatically, so `auth test` shows 36 in the scope list).
7. `python3 scripts/slack.py call conversations.list --workspace test
   --params '{"types":"public_channel","limit":5}'` → expect channel list.
8. Pick a test channel ID; post a message:
   `python3 scripts/slack.py call chat.postMessage --workspace test
   --params '{"channel":"C...","text":"SKILLTEST_smoke"}'` → expect
   `{"ok":true,"ts":"..."}` and a visible message in Slack as you.
9. Clean up the test message via Slack UI (or `chat.delete`).

If any step fails, the most likely cause is a manifest scope drift (Slack
added or renamed a required scope) or a missing scope on the install —
`auth test` will show what's granted; compare against the JSON manifest.
Slack's manifest editor will reject any user-only scope set to a
bot-only scope (e.g. `chat:write.public`) and rejects
`features.bot_user: null` — both confirmed against the live editor on
2026-05-03.

---

## How a fresh session can pick this up

In a new conversation, ideal context-load order:

1. Read this file (`SESSION-HANDOFF.md`).
2. Read `docs/specs/2026-05-02-slack-skill-design.md` for the canonical design.
3. Skim `git log --oneline` to see what shipped.
4. Run `make test` to confirm green.
5. If continuing v1.1 work: pick from the "Open issues" list above. The
   easiest remaining wins (lowest risk, highest value):
   - Add the resolver-error-surface to stderr (lookup-failure visibility) —
     resolver currently swallows TransportError + SlackAPIError silently;
     a "12 of 47 references could not be resolved" warning at end of
     `cmd_call` would close the silent-degradation gap.
   - Add a transport-error exit-3 test (force `urlopen` to fail).
   - Resolver N+1 batching via `concurrent.futures` — real perf win
     (~10s → ~1s for 50 mentions).

The repo's design and plan documents (`docs/specs/`, `docs/plans/`) are
durable references. Don't expect a fresh session to remember conversation
context — point it at this file.

---

## Notable conversational decisions (not in code)

These were resolved through brainstorming and aren't immediately obvious
from reading the code/docs alone:

- **CLI shape**: thin generic shim (option A), not curated subcommands.
  Decision driver: matches omnifocus-skill's "wrapper passes raw thing
  through" philosophy. Confirmed several times during brainstorming.
- **Output enrichment**: `--resolve` flag is opt-in (option B), default
  is raw pass-through. Decision driver: Slack's API doesn't give
  composition for free the way Omni Automation does, so enrichment is
  the equivalent of `t.containingProject.name` in OF.
- **Auth/workspace model**: named profiles in `~/.config/slack-skill/
  config.json` (option C). No `SLACK_TOKEN` env-var fallback (decided
  against during brainstorming — added complexity for no real benefit).
- **Pagination**: `--all` is opt-in, with `--limit N` cap. Default is
  single-page-with-cursor pass-through.
- **Language**: Python 3.9+ stdlib-only, JSON config (NOT TOML — decided
  against to avoid bumping Python version or needing `tomli`/`uv`).
  Original brainstorming considered Go but switched to Python to match
  obsidian-skill's "no compilation" pattern.
- **Slack app**: explicitly **create a new app**, do NOT reuse the
  `slack2omnifocus` token. Different scope sets, separate revocation,
  cleaner troubleshooting. README and SKILL.md both say this.
- **No bot tokens**: `auth add` rejects `xoxb-` with a clear error.
  This skill represents the user.
- **macOS only in v1**: Linux/Windows is straightforward future work.

---

## Files changed during this session

The full file inventory at handoff (24 tracked files):

```
.gitignore
LICENSE
Makefile
NOTICE
README.md
SKILL.md
docs/plans/2026-05-02-slack-skill-implementation.md
docs/slack-api/CHEATSHEET.md
docs/slack-api/Chat.md
docs/slack-api/Conversations.md
docs/slack-api/Files.md
docs/slack-api/FULL-REFERENCE.md
docs/slack-api/Pins-Stars-Bookmarks.md
docs/slack-api/Reactions.md
docs/slack-api/Search.md
docs/slack-api/Users.md
docs/slack-app-manifest.json
docs/specs/2026-05-02-slack-skill-design.md
evals/evals.json
scripts/package_skill.py
scripts/regen_reference.py
scripts/slack.py
scripts/test_slack.py
SESSION-HANDOFF.md      ← this file (committed; updated session 2)
```

`SESSION-HANDOFF.md` is committed and serves as the durable pickup
point for fresh sessions. Update it in place (don't replace) when
adding a new session.

---

## Workflow used

For reference if continuing in subagent-driven style:

- **Brainstorming** (`/brainstorming`) → Q&A through 6 clarifying questions
  → 6-section design → spec written and committed.
- **Plan writing** (`writing-plans`) → 27-task TDD plan with full code in
  every step.
- **Subagent-driven implementation** (`subagent-driven-development`) →
  per task: implementer subagent → spec compliance reviewer subagent →
  code quality reviewer subagent → mid-task fix loop where needed.
  Average ~3-5 subagent dispatches per task. Final whole-implementation
  reviewer caught the emergent bugs that fixed in commit `2d5a07d`.

If picking up: a fresh session can use the same `subagent-driven-
development` skill against the open-issues list, treating each polish
item as a mini-task.
