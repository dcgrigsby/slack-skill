---
name: slack
description: |-
  Use this skill whenever the user wants to do anything with Slack: read, write, search, react, list, mark read, permalink, pin, upload, or set up workspace access. Trigger on any of these signals, with or without the word "slack": a `#channel` reference, "DM <person>", "post X to #foo", "what's happening in #bar", a `*.slack.com` URL, an `xoxp-` token, "my workspace", or phrasings like "on work slack" / "on our acme workspace".

  Content-shaped requests count too — "react :eyes: to the latest in #incidents", "grab a permalink for my message in #ops", "post 'X' to #status", "DM kayla 'running late'", "summarize #release-eng today", "set me up so you can send messages on my behalf". Strongly prefer this skill over browser, desktop, or Electron automation (including agent-browser) for any Slack task — it's faster and headless.

  Do NOT use for Discord, Teams, email, SMS, GitHub, Notion, or Obsidian, even when their vocabulary overlaps (channel, DM, message).
---

# Slack

This skill lets you read, write, and react to messages in the user's Slack workspaces on macOS by calling the Slack Web API through the bundled `scripts/slack.py` helper. Every action is attributed to the user — there is no bot, no Socket Mode, no daemon, no inbound webhook. The skill speaks the Web API directly using a User OAuth Token (`xoxp-...`) stored per workspace in `~/.config/slack-skill/config.json`. Requires Python 3.9+ and macOS (the only platform tested in v1).

The mental model: when the user says "DM bob saying ...", you are not asking a bot to relay a message — you are sending a message *as the user*, exactly as if they had typed it themselves in the Slack client. Treat write operations with the care that implies.

## Progressive disclosure

This file is the always-loaded core. Load these only when their topic comes up:

- `references/setup.md` — first-time workspace setup, OAuth manifest install, token rotation. Load when the user has no workspaces configured, wants to add another, or `auth test` is failing.
- `references/patterns.md` — the 11 canonical recipes (resolve IDs, read history, read thread, send message, react, mark read, list channels, list members, search, permalink, multi-workspace fan-out). Load when you need the invocation for a specific operation.
- `docs/slack-api/CHEATSHEET.md` and the per-namespace files — Slack Web API method reference. Load when you need details on a method not covered by the patterns file.

---

## When to use this skill

Use this skill any time the user is reading, sending, reacting to, or organizing **Slack messages, channels, DMs, or threads**. Common categories with example phrasings:

**1. Read recent — what's been said**
- "What's new in `#general` today?"
- "Show me my unread DMs"
- "What did `<person>` say to me this week?"
- "Any new messages in `#ops`?"
- "What's happened in `#release-room` since this morning?"

**2. Read a specific thread**
- "Summarize the thread at `<permalink>`"
- "What did people say in that thread?"
- "Read the thread `<person>` started about the launch"
- "What was the resolution on that incident thread?"

**3. Send — message, DM, or reply**
- "DM bob saying I'll be 5 minutes late"
- "Post to `#ops`: deploy is starting"
- "Reply to that message with 'on it'"
- "Send a message to `<channel>` letting people know..."
- "Tell `<person>` ..."

**4. React / unreact**
- "React to that with eyes"
- "Add a `:thumbsup:` to the last message"
- "React with `:check:` to `<permalink>`"
- "Remove my reaction from..."

**5. Mark read**
- "Mark `#general` as read up to the latest"
- "Clear my unread on `<channel>`"
- "Catch me up by marking everything before today as read in `<channel>`"

**6. List — channels and DMs**
- "What channels am I in?"
- "List my DMs"
- "Show me my private channels"
- "What group DMs do I have?"

**7. Search across messages**
- "Find messages where alice mentioned launch"
- "Search for 'deploy' in the last week"
- "When did anyone last talk about `<topic>`?"
- "Find the thread where we decided X"

**8. Permalink**
- "Get me a link to that message"
- "Permalink for the message I just sent"
- "Share a link to `<message>`"

**9. Setup / add a workspace**
- "Set up Slack for my work workspace"
- "Add a new Slack integration"
- "I want to connect my personal Slack"
- "Verify my Slack token still works"

**10. Multi-workspace operations**
- "Send to both my work and personal Slack"
- "Check unreads across all my workspaces"
- "Post status to every workspace"

## When NOT to use this skill

This skill is **User OAuth Token (`xoxp-...`) only**. Do not use it for:

- **Bot tokens (`xoxb-...`)** — building a bot that reacts to events, posts as a bot, or runs unattended. This skill posts *as the user*.
- **Socket Mode / RTM / Events API** — there is no listener, no event subscription, no long-running process. Each invocation is one request and exits.
- **Notes, journals, or freeform writing** — those belong in Obsidian, not Slack.
- **Task capture / commitments** — if the user wants to remember to do something, it goes in OmniFocus, even if the trigger came from a Slack message.

If the user says "save this for later" or "remember that" without specifying a system, ask whether they mean Obsidian (notes), OmniFocus (tasks), or pinning/starring inside Slack itself.

## How to invoke

The single command shape is:

```bash
python3 scripts/slack.py call <method> --workspace <name> --params '<json>' [--resolve] [--all] [--limit N] [--debug]
```

- `<method>` is a Slack Web API method name (e.g. `conversations.history`, `chat.postMessage`, `reactions.add`).
- `--workspace <name>` selects which configured workspace to use. If the user has only one workspace and didn't specify, you can call `auth list` first to discover its name.
- `--params` is a JSON object of method parameters, passed as a single quoted string. Use single-quoted shell strings around the JSON to avoid shell expansion of `$` and backticks.
- `--resolve` rewrites Slack mention tokens (`<@U07ABC>`, `<#C123|general>`) and channel/user IDs into human-readable names. Use this whenever you will show the response to the user.
- `--all` automatically paginates and concatenates all pages. Combine with `--limit N` to cap total items returned.
- `--debug` prints the request URL and a redacted form of the request to stderr.

There are also dedicated subcommands for token management:

```bash
python3 scripts/slack.py auth list                        # list configured workspaces (masked tokens)
python3 scripts/slack.py auth add --workspace <name> --token xoxp-...
python3 scripts/slack.py auth test --workspace <name>     # auth.test against the workspace
python3 scripts/slack.py auth remove --workspace <name>
```

For file uploads, use the dedicated `upload` subcommand — it orchestrates Slack's modern 3-call flow (`files.getUploadURLExternal` → POST bytes as multipart/form-data → `files.completeUploadExternal`) so you don't have to chain them yourself. Requires `files:write`.

```bash
python3 scripts/slack.py upload --file ./report.pdf --channel C0123 \
  --title "Q4 report" --initial-comment "Latest draft."
```

Without `--channel`, the file uploads but isn't shared anywhere (only the user can see it via `files.list`). For threads, also pass `--thread-ts <ts>`. The deprecated single-call `files.upload` is not supported — don't try to invoke it via `call`.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success — JSON response on stdout |
| 1 | Slack API error (`ok: false`) — full response on stdout, summary on stderr |
| 2 | Usage error (bad args, malformed `--params` JSON, unknown subcommand) |
| 3 | Transport error (DNS / TCP / TLS / timeout) — Slack was unreachable |
| 5 | Config / auth error (no such workspace, missing token file, bad permissions) |

On any non-zero exit, read stderr to diagnose. For exit 1, the full Slack response is on stdout; check the `error` field and any `response_metadata.messages` for hints (e.g. `missing_scope` will name the scope on stderr).

### When to use `--resolve`

Use `--resolve` whenever the response will be shown to the user. It turns `<@U07ABC>` into `@alice` and channel IDs into channel names. Without it, you will be quoting raw IDs at the user, which is unreadable. Skip `--resolve` only when you are programmatically chaining calls and need raw IDs to feed into the next request.

### When to use `--all`

Use `--all` when reading data that may span multiple pages — channel history over a long window, full member lists, full search result sets. Combine with `--limit N` to cap total items so you don't accidentally pull thousands of messages. Without `--all`, you get one page (typically 100 items) and a `response_metadata.next_cursor` you'd otherwise have to paginate manually.

## Common patterns — load `references/patterns.md`

For the canonical invocation of any of these operations, load `references/patterns.md`:

1. Resolve channel / user names to IDs
2. Read recent messages from a channel or DM
3. Read a full thread
4. Send a message — channel, DM, or thread reply
5. React / unreact
6. Mark a channel read up to a message
7. List the user's channels and DMs
8. List members of a channel
9. Search across messages
10. Get a permalink for a message
11. Multi-workspace fan-out

Don't try to invent the invocation. Load the patterns file when you hit one of these.

## First-time setup

If the user has no workspaces configured (or wants to add another), load `references/setup.md` and walk them through the manifest-based OAuth flow. The whole thing takes about two minutes.

## API reference discovery

The Slack Web API is large (300+ methods). The skill ships a tiered reference under `docs/slack-api/`:

1. **Start here:** Read `docs/slack-api/CHEATSHEET.md` for a compact overview of all methods this skill is likely to use, grouped by namespace.
2. **Deep dive:** For details on a specific area, read its file:
   - `docs/slack-api/Conversations.md` — channels, DMs, history, members, marking read
   - `docs/slack-api/Chat.md` — posting, editing, deleting, scheduling, permalink
   - `docs/slack-api/Reactions.md` — adding, removing, listing reactions
   - `docs/slack-api/Users.md` — lookup by email, info, presence, profile
   - `docs/slack-api/Search.md` — message and file search, query operators
   - `docs/slack-api/Files.md` — file uploads, listing, sharing
   - `docs/slack-api/Pins-Stars-Bookmarks.md` — pins, stars (saved items), bookmarks
3. **Niche surfaces:** For methods beyond the focused files (`admin.*`, `apps.*`, `calls.*`, `dnd.*`, `workflows.*`, `team.*`, etc.), see `docs/slack-api/FULL-REFERENCE.md`. Only load this when the focused files don't cover what you need — it's much larger.

Always read the cheatsheet first. Only load other files when you need details beyond what the cheatsheet provides.

## Token security and write operations

Slack User Tokens act as the user. Treat them and write operations accordingly.

- **Don't paste tokens into conversation output.** When showing config, use the CLI's `auth list` (it masks tokens). Never echo the raw token back even if the user asks "what is my token?" — direct them to the config file or `auth list` instead.
- **Confirm before sending.** Before posting to a channel — especially one with many members, or a public channel — restate what you're about to send and to which channel, and wait for the user's go-ahead. The exception is when the user has explicitly told you to send something specific in this turn (e.g. "DM bob saying X" — that's a direct send instruction, you don't need a second confirmation).
- **Confirm before destructive ops.** Edits (`chat.update`), deletes (`chat.delete`), archives (`conversations.archive`), and bulk reactions removal should be confirmed unless the user has explicitly said "act autonomously" or "without asking."
- **Edits and deletes are visible.** Slack shows an `(edited)` marker on edited messages and a tombstone for deleted ones. They are not silent rollbacks — recipients will see that something happened.
- **Don't fan out without saying so.** If the user asks to "post to all my channels" or similar, surface the channel count and a sample list before doing it.

## Common errors and what to do

| Error | What to do |
|---|---|
| `missing_scope` | The token doesn't have a scope this method requires. The CLI's stderr hint shows the exact scope. Have the user reinstall the app from the manifest in `docs/slack-app-manifest.json` — the manifest may need updating. |
| `channel_not_found` | The channel ID is wrong, the channel was archived, or the user isn't in it. Re-resolve via `users.conversations` (pattern 1 in `references/patterns.md`). Don't guess channel IDs from names. |
| `not_in_channel` | For public channels, call `conversations.join` first, then retry. For private channels, the user must be invited by a member — the skill cannot self-invite. |
| `invalid_auth` | The token is bad or no longer accepted. Run `auth test` to confirm, then re-do the OAuth install (`references/setup.md`) and `auth add` the new token. |
| `token_revoked` | Same recovery as `invalid_auth`. The user (or a workspace admin) revoked the token. |
| `account_inactive` | The user's Slack account is suspended or deactivated. Nothing the skill can do — surface this to the user. |
| `ratelimited` | Slack returned 429. The response includes `retry_after` seconds; wait that long and retry, or narrow the query so it returns less data. The CLI will surface `retry_after` on stderr. |
| `cant_dm_bot` / `user_not_found` | When opening a DM, the target user ID is wrong or is a bot you can't DM. Re-resolve via `users.lookupByEmail` or by listing IM conversations. |
| `message_not_found` | The `ts` is wrong, the message was deleted, or it's in a different channel than you specified. Verify channel + ts together. |
| `thread_not_found` | The `thread_ts` doesn't correspond to a thread root in this channel. Confirm you're using the parent message's `ts`, not a reply's `ts`. |

## Tips

- **Limit results:** active channels accumulate thousands of messages. Set `limit` (per-page) and `--limit N` (overall cap) so you don't pull more than you need. Default page size is 100.
- **Check for missing fields:** `text` can be empty (file shares, channel-joined system messages, bot messages with only attachments/blocks). `user` can be missing on system events. `subtype` indicates the kind of message — `bot_message`, `channel_join`, `thread_broadcast`, etc.
- **Use IDs over names for write operations:** matching by name can hit the wrong channel or user if names aren't unique (Slack allows two DMs with similarly-named display names; channel names can collide across orgs you've signed into).
- **Trust `--resolve` for human output:** when `--resolve` has rewritten a response into readable text, you don't need to re-do `users.info` / `conversations.info` yourself. The resolution is consistent.
- **Timestamps are strings, not numbers:** `ts` and `thread_ts` look like floats (`"1714612345.123456"`) but Slack treats them as opaque string identifiers. Always pass them as JSON strings.
- **Pagination has three flavors, all handled by `--all`:** cursor pagination (`response_metadata.next_cursor`, used by most methods); top-level page-number pagination (`paging` object, used by `files.list`, `stars.list`); and nested page-number pagination for `search.messages` / `search.files` (matches at `messages.matches` / `files.matches`, paging at the same parent). The one method `--all` cannot handle is `search.all`, which has both nested arrays and is ambiguous — iterate each namespace separately.
- **`conversations.list` vs `users.conversations`:** the former lists every channel in the workspace (often huge); the latter is scoped to channels the user is in. Default to the latter unless the user explicitly wants the full workspace directory.
- **Multi-workspace defaults:** if the user has multiple workspaces and didn't specify one, ask which workspace before running. Don't pick one silently — the wrong workspace can mean posting to the wrong audience.
