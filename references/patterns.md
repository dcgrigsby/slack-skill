# Common patterns

Load when you need the canonical invocation for a specific Slack operation. The SKILL.md has the command shape, exit codes, and `--resolve` / `--all` semantics; this file has the 11 hot-path recipes.

Eleven hot-path patterns. Each one shows the canonical invocation. Real method names, sensible param values; copy and adapt.

## 1. Resolve channel / user names to IDs

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

## 2. Read recent messages from a channel or DM

```bash
python3 scripts/slack.py call conversations.history \
  --workspace work \
  --params '{"channel":"C0123ABCD","limit":50}' \
  --resolve
```

Returns the most recent N messages. Add `"oldest":"<unix_ts>"` to bound by time (e.g. messages since this morning). Use `--resolve` so mentions render as names. For DMs, `channel` is the DM channel ID (starts with `D`), which you get from `conversations.open` or `users.conversations`.

## 3. Read a full thread

A thread is rooted on a parent message's `ts`. Once you have it (from `conversations.history`, a permalink, or search), pull the replies:

```bash
python3 scripts/slack.py call conversations.replies \
  --workspace work \
  --params '{"channel":"C0123ABCD","ts":"1714612345.123456"}' \
  --resolve --all
```

Use `--all` because long threads can span multiple pages. The first message in the result is the parent; subsequent ones are replies in chronological order.

## 4. Send a message — channel, DM, or thread reply

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

## 5. React / unreact

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

## 6. Mark a channel read up to a message

```bash
python3 scripts/slack.py call conversations.mark \
  --workspace work \
  --params '{"channel":"C0123ABCD","ts":"1714612345.123456"}'
```

The `ts` is the message you want to be the new last-read marker — everything at or before this timestamp will be considered read.

## 7. List the user's channels and DMs

```bash
python3 scripts/slack.py call users.conversations \
  --workspace work \
  --params '{"types":"public_channel,private_channel,im,mpim","exclude_archived":true}' \
  --all --resolve
```

`users.conversations` is scoped to the authenticated user (only channels they're in), which is almost always what the user means by "list my channels." Use `conversations.list` only if the user explicitly wants the full workspace channel directory.

## 8. List members of a channel

```bash
python3 scripts/slack.py call conversations.members \
  --workspace work \
  --params '{"channel":"C0123ABCD"}' \
  --all
```

Returns user IDs. To turn them into names, either run with `--resolve` or chain a `users.info` per ID. For large channels, prefer `--resolve` — it batches resolution.

## 9. Search across messages

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

## 10. Get a permalink for a message

```bash
python3 scripts/slack.py call chat.getPermalink \
  --workspace work \
  --params '{"channel":"C0123ABCD","message_ts":"1714612345.123456"}'
```

Returns a `permalink` field — a URL that opens the message directly in the Slack client. Note the parameter name is `message_ts`, not `ts`, only on this one method.

## 11. Multi-workspace — same operation across workspaces

There is no built-in multi-workspace fan-out — loop the call yourself, varying `--workspace`:

```bash
for ws in work personal; do
  python3 scripts/slack.py call chat.postMessage \
    --workspace "$ws" \
    --params '{"channel":"C_STATUS","text":"Heads down for the next hour."}'
done
```

The same channel ID typically won't exist in two workspaces, so for cross-workspace posts you usually need to resolve a channel name to an ID inside each workspace first (pattern 1).
