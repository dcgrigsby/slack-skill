---
name: slack
description: |-
  Slack workspace operations on the user's behalf. Invoke this skill whenever the user wants to act inside Slack — posting to or reading a channel, DMing a person, replying in a thread, reacting with an emoji, fetching a permalink, marking read, listing channels/DMs, searching messages, pinning, or connecting/verifying a workspace token (xoxp-).

  Treat these as Slack signals even when the word "slack" is absent: a `#channel` reference, "DM <name>", phrasings like "post X to #foo" or "what's happening in #bar", a `*.slack.com` workspace mention, or pasting an `xoxp-` token. If the user combines such a signal with a read/send/react/search/permalink/setup intent, this is the right skill — content-focused phrasings ("post 'X' to #status", "react :eyes: to the latest in #incidents") still count.

  Do not use for Discord, Teams, email, SMS, GitHub, Notion, Obsidian, or other non-Slack platforms, even if the surface vocabulary (channel, DM, message) is similar.
---

# Slack

This skill lets you read, write, and react to messages in the user's Slack workspaces on macOS by calling the Slack Web API through the bundled `scripts/slack.py` helper. Every action is attributed to the user — there is no bot, no Socket Mode, no daemon, no inbound webhook. The skill speaks the Web API directly using a User OAuth Token (`xoxp-...`) stored per workspace in `~/.config/slack-skill/config.json`. Requires Python 3.9+ and macOS (the only platform tested in v1).

The mental model: when the user says "DM bob saying ...", you are not asking a bot to relay a message — you are sending a message *as the user*, exactly as if they had typed it themselves in the Slack client. Treat write operations with the care that implies.

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

## First-time setup / adding a workspace

If the user wants to use Slack and they have no workspaces configured (or want to add another one), walk them through the following. The whole flow takes about two minutes.

### Step 1 — Check what's already configured

```bash
python3 scripts/slack.py auth list
```

If this prints an empty list, or doesn't include the workspace they want, continue to step 2. If the workspace is already there, jump to step 5 to verify it.

### Step 2 — Create the Slack app from a manifest

Tell the user:

1. Visit https://api.slack.com/apps?new_app=1 in a browser.
2. Click **From an app manifest**.
3. Pick the workspace they want to integrate (e.g. their work Slack).
4. When prompted for the manifest, switch the editor tab to **JSON** and paste the contents of `docs/slack-app-manifest.json` from this skill. (Open that file and read it to them, or have them open it themselves.)
5. Click **Next**, review the scopes, then **Create**.
6. On the app's **Basic Information** page, click **Install to Workspace**, then **Allow** on the OAuth confirmation screen.
7. On the **OAuth & Permissions** page, copy the **User OAuth Token** (it starts with `xoxp-`).

The manifest at `docs/slack-app-manifest.json` is preconfigured with the user scopes this skill needs (channel and message reads, chat write, reactions, search, etc.). Don't tell the user to add scopes manually — the manifest does it.

### Step 3 — User pastes the token into chat

Have the user paste the `xoxp-...` token. Treat it as sensitive — do not echo it back to them in plaintext, do not log it.

### Step 4 — Add it to the config

```bash
python3 scripts/slack.py auth add --workspace work --token xoxp-REDACTED
```

Pick a short, memorable workspace name (`work`, `personal`, `acme`, etc.). The user will reuse this name for every subsequent invocation.

### Step 5 — Verify

```bash
python3 scripts/slack.py auth test --workspace work
```

This calls Slack's `auth.test` endpoint and should return the authenticated user and team. If it returns `invalid_auth`, the token was pasted incorrectly or has been revoked — re-do step 2's last sub-step and try again. If it returns `missing_scope`, the manifest in `docs/slack-app-manifest.json` may be out of sync with what this skill needs — read that file and reinstall.

If the user has more than one Slack workspace they want to use, repeat steps 2–5 for each, with a different `--workspace <name>` per workspace.

## Common patterns

Eleven hot-path patterns. Each one shows the canonical invocation. Real method names, sensible param values; copy and adapt.

### 1. Resolve channel / user names to IDs

Slack's API takes IDs (`C0123ABCD` for channels, `U07ABCDEF` for users), not names. When the user says "post to `#ops`," you need to find the channel ID first.

For users, if you have an email:

```bash
python3 scripts/slack.py call users.lookupByEmail \
  --workspace work \
  --params '{"email":"alice@example.com"}'
```

For channels, list the user's conversations and filter by name:

```bash
python3 scripts/slack.py call users.conversations \
  --workspace work \
  --params '{"types":"public_channel,private_channel,im,mpim","exclude_archived":true}' \
  --all
# Then pick the one whose `name` field equals "ops"
```

Cache the resulting ID in your scratchpad for the rest of the session — you don't need to re-resolve it on every call.

### 2. Read recent messages from a channel or DM

```bash
python3 scripts/slack.py call conversations.history \
  --workspace work \
  --params '{"channel":"C0123ABCD","limit":50}' \
  --resolve
```

Returns the most recent N messages. Add `"oldest":"<unix_ts>"` to bound by time (e.g. messages since this morning). Use `--resolve` so mentions render as names. For DMs, `channel` is the DM channel ID (starts with `D`), which you get from `conversations.open` or `users.conversations`.

### 3. Read a full thread

A thread is rooted on a parent message's `ts`. Once you have it (from `conversations.history`, a permalink, or search), pull the replies:

```bash
python3 scripts/slack.py call conversations.replies \
  --workspace work \
  --params '{"channel":"C0123ABCD","ts":"1714612345.123456"}' \
  --resolve --all
```

Use `--all` because long threads can span multiple pages. The first message in the result is the parent; subsequent ones are replies in chronological order.

### 4. Send a message — channel, DM, or thread reply

Channel:

```bash
python3 scripts/slack.py call chat.postMessage \
  --workspace work \
  --params '{"channel":"C0123ABCD","text":"Deploy is starting now."}'
```

DM (open the IM channel first to get its ID):

```bash
# Step 1: open the DM channel
python3 scripts/slack.py call conversations.open \
  --workspace work \
  --params '{"users":"U07BOB"}'
# response includes channel.id, e.g. "D0456XYZ"

# Step 2: send to it
python3 scripts/slack.py call chat.postMessage \
  --workspace work \
  --params '{"channel":"D0456XYZ","text":"Hey, I will be 5 minutes late."}'
```

Thread reply:

```bash
python3 scripts/slack.py call chat.postMessage \
  --workspace work \
  --params '{"channel":"C0123ABCD","thread_ts":"1714612345.123456","text":"On it."}'
```

Add `"reply_broadcast":true` if the user wants the reply to also surface in the channel, not just inside the thread.

### 5. React / unreact

`reactions.add` takes the emoji `name` *without* surrounding colons (`thumbsup`, not `:thumbsup:`):

```bash
python3 scripts/slack.py call reactions.add \
  --workspace work \
  --params '{"channel":"C0123ABCD","timestamp":"1714612345.123456","name":"eyes"}'
```

To remove:

```bash
python3 scripts/slack.py call reactions.remove \
  --workspace work \
  --params '{"channel":"C0123ABCD","timestamp":"1714612345.123456","name":"eyes"}'
```

### 6. Mark a channel read up to a message

```bash
python3 scripts/slack.py call conversations.mark \
  --workspace work \
  --params '{"channel":"C0123ABCD","ts":"1714612345.123456"}'
```

The `ts` is the message you want to be the new last-read marker — everything at or before this timestamp will be considered read.

### 7. List the user's channels and DMs

```bash
python3 scripts/slack.py call users.conversations \
  --workspace work \
  --params '{"types":"public_channel,private_channel,im,mpim","exclude_archived":true}' \
  --all --resolve
```

`users.conversations` is scoped to the authenticated user (only channels they're in), which is almost always what the user means by "list my channels." Use `conversations.list` only if the user explicitly wants the full workspace channel directory.

### 8. List members of a channel

```bash
python3 scripts/slack.py call conversations.members \
  --workspace work \
  --params '{"channel":"C0123ABCD"}' \
  --all
```

Returns user IDs. To turn them into names, either run with `--resolve` or chain a `users.info` per ID. For large channels, prefer `--resolve` — it batches resolution.

### 9. Search across messages

```bash
python3 scripts/slack.py call search.messages \
  --workspace work \
  --params '{"query":"from:@alice deploy","count":20,"sort":"timestamp","sort_dir":"desc"}' \
  --resolve
```

Slack's search query syntax supports useful operators:

- `from:@alice` — messages from a specific user
- `in:#general` or `in:@bob` — restrict to a channel or DM
- `before:2026-04-01`, `after:2026-04-25`, `on:2026-05-01` — date filters
- `has:link`, `has:reaction` — message attribute filters

Search is page-based (`page` param), not cursor-based — different pagination model than `conversations.history`. `--all` handles `search.messages` and `search.files` directly (the matches at `messages.matches` / `files.matches` are walked automatically). It does **not** handle `search.all`, which returns both `messages.matches` and `files.matches` and is therefore ambiguous — iterate each namespace separately with `search.messages` or `search.files`.

### 10. Get a permalink for a message

```bash
python3 scripts/slack.py call chat.getPermalink \
  --workspace work \
  --params '{"channel":"C0123ABCD","message_ts":"1714612345.123456"}'
```

Returns a `permalink` field — a URL that opens the message directly in the Slack client. Note the parameter name is `message_ts`, not `ts`, only on this one method.

### 11. Multi-workspace — same operation across workspaces

There is no built-in multi-workspace fan-out — loop the call yourself, varying `--workspace`:

```bash
for ws in work personal; do
  python3 scripts/slack.py call chat.postMessage \
    --workspace "$ws" \
    --params '{"channel":"C_STATUS","text":"Heads down for the next hour."}'
done
```

The same channel ID typically won't exist in two workspaces, so for cross-workspace posts you usually need to resolve a channel name to an ID inside each workspace first (pattern 1).

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
| `channel_not_found` | The channel ID is wrong, the channel was archived, or the user isn't in it. Re-resolve via `users.conversations` (pattern 1). Don't guess channel IDs from names. |
| `not_in_channel` | For public channels, call `conversations.join` first, then retry. For private channels, the user must be invited by a member — the skill cannot self-invite. |
| `invalid_auth` | The token is bad or no longer accepted. Run `auth test` to confirm, then re-do the OAuth install in the Slack app and `auth add` the new token. |
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
