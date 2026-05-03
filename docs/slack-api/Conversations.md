# conversations.*

The `conversations` namespace is the unified surface for everything
that holds messages: public channels, private channels, direct
messages, and multi-party DMs. One namespace, four kinds of objects,
distinguished by the channel-ID prefix:

- `C…` — public channel (and, in newer workspaces, sometimes private)
- `G…` — private channel or MPIM (legacy form)
- `D…` — direct message (1:1)

Most reads accept any of these; most writes are scoped by sub-scope
(`channels:write` for public channels, `groups:write` for private,
`im:write` / `mpim:write` for DMs and MPIMs). When in doubt, request
all four read scopes — they're cheap.

This skill's manifest already grants the `*:history` and `*:read`
scopes; write methods (`mark`, `create`, `archive`, etc.) require
adding `channels:write` / `groups:write` / `im:write` / `mpim:write`
to the manifest before they'll work — they are intentionally omitted
from the default scope set.

## conversations.list

List every channel / DM the token can see. Returns an array of channel
objects (no messages). Filter by `types`; default is `public_channel`.

| Param              | Type    | Req | Description                                                              |
|--------------------|---------|-----|--------------------------------------------------------------------------|
| `types`            | string  | no  | csv of `public_channel,private_channel,im,mpim`                          |
| `exclude_archived` | bool    | no  | hide archived (default `false`)                                          |
| `limit`            | int     | no  | per-page, max 1000                                                       |
| `cursor`           | string  | no  | pagination cursor (or use `--all`)                                       |

Scope: `channels:read,groups:read,im:read,mpim:read`. Paginated.

```bash
python3 scripts/slack.py call conversations.list \
  --params '{"types":"public_channel,private_channel","exclude_archived":true,"limit":200}' \
  --all
```

Returns:
```json
{"ok":true,"channels":[{"id":"C0123","name":"general","is_channel":true,"is_private":false,"num_members":42,...}],"response_metadata":{"next_cursor":""}}
```

Gotchas: workspaces with thousands of channels can take many round-trips
even with `limit=1000`; use `--limit` on the CLI to cap. The `name`
field is absent for IMs (use `user` to look up the other party).

## conversations.history

Top-level messages in a channel/DM — *not* threaded replies. To get a
thread, call `conversations.replies` with the parent's `ts`.

| Param       | Type   | Req | Description                                  |
|-------------|--------|-----|----------------------------------------------|
| `channel`   | string | yes | channel ID                                   |
| `oldest`    | string | no  | Unix ts; messages strictly newer             |
| `latest`    | string | no  | Unix ts; messages strictly older             |
| `inclusive` | bool   | no  | include messages exactly at `oldest`/`latest`|
| `limit`     | int    | no  | per-page, max 999                            |
| `cursor`    | string | no  | pagination cursor                            |

Scope: `channels:history` (or `groups:history` / `im:history` /
`mpim:history` — pick by channel type). Paginated.

```bash
python3 scripts/slack.py call conversations.history \
  --params '{"channel":"C0123","limit":50,"oldest":"1714608000.000000"}'
```

Returns:
```json
{"ok":true,"messages":[{"type":"message","user":"U07","text":"hi","ts":"1714608123.001000","thread_ts":"1714608123.001000","reply_count":3}],"has_more":true,"response_metadata":{"next_cursor":"bmV4dF90czoxNzE0NjA4MDAw"}}
```

Gotchas: `ts` values are strings, not numbers — never JSON-coerce them.
A message with `thread_ts == ts` is a thread parent; threaded replies
are *not* returned here.

## conversations.replies

Fetch a thread: parent message + its replies. The parent's `ts` is the
`thread_ts` of every reply.

| Param     | Type   | Req | Description           |
|-----------|--------|-----|-----------------------|
| `channel` | string | yes | channel ID            |
| `ts`      | string | yes | parent message `ts`   |
| `oldest`  | string | no  | filter window         |
| `latest`  | string | no  | filter window         |
| `limit`   | int    | no  | per-page              |
| `cursor`  | string | no  | pagination cursor     |

Scope: same as `conversations.history`. Paginated.

```bash
python3 scripts/slack.py call conversations.replies \
  --params '{"channel":"C0123","ts":"1714608123.001000"}' --all
```

Returns:
```json
{"ok":true,"messages":[{"ts":"1714608123.001000","text":"parent",...},{"ts":"1714608456.002000","text":"reply 1","thread_ts":"1714608123.001000"}],"has_more":false}
```

Gotchas: the parent message is always element 0 of `messages`. If `ts`
isn't a thread, you get the single message back with no replies.

## conversations.info

Metadata for one channel/DM. Cheap; safe to call repeatedly.

| Param                | Type   | Req | Description                       |
|----------------------|--------|-----|-----------------------------------|
| `channel`            | string | yes | channel ID                        |
| `include_locale`     | bool   | no  | include preferred locale          |
| `include_num_members`| bool   | no  | include member count              |

Scope: `channels:read` (or per-type variant).

```bash
python3 scripts/slack.py call conversations.info \
  --params '{"channel":"C0123","include_num_members":true}'
```

Returns:
```json
{"ok":true,"channel":{"id":"C0123","name":"general","is_channel":true,"is_private":false,"created":1700000000,"creator":"U07","topic":{"value":"..."},"purpose":{"value":"..."},"num_members":42}}
```

## conversations.members

User IDs that belong to a channel. IDs only — call `users.info` for
display names. Paginated.

| Param     | Type   | Req | Description |
|-----------|--------|-----|-------------|
| `channel` | string | yes | channel ID  |
| `limit`   | int    | no  | per-page    |
| `cursor`  | string | no  | cursor      |

Scope: `channels:read` (or per-type variant).

```bash
python3 scripts/slack.py call conversations.members \
  --params '{"channel":"C0123"}' --all
```

Returns:
```json
{"ok":true,"members":["U07","U08","U09"],"response_metadata":{"next_cursor":""}}
```

## conversations.mark

Move the read marker forward to `ts`. The `ts` is the *latest message
the user has seen* — not a deletion point. Messages with newer `ts`
remain unread. Mark is idempotent.

| Param     | Type   | Req | Description       |
|-----------|--------|-----|-------------------|
| `channel` | string | yes | channel ID        |
| `ts`      | string | yes | last-seen `ts`    |

Scope: `channels:write` (or per-type variant).

```bash
python3 scripts/slack.py call conversations.mark \
  --params '{"channel":"C0123","ts":"1714608123.001000"}'
```

Returns: `{"ok":true}`.

## conversations.open

Open a DM or MPIM. Pass `users` (csv of user IDs, 1 = DM, 2-8 = MPIM)
to start a new one, or `channel` (a `D…` ID) to reopen an existing DM.

| Param           | Type   | Req | Description                                   |
|-----------------|--------|-----|-----------------------------------------------|
| `users`         | string | no\* | csv of user IDs                              |
| `channel`       | string | no\* | existing DM channel ID                       |
| `return_im`     | bool   | no  | include full IM object in response            |
| `prevent_creation`| bool | no  | only reopen, don't create                    |

\* exactly one of `users` or `channel` required.

Scope: `im:write` (1:1) or `mpim:write` (group).

```bash
python3 scripts/slack.py call conversations.open \
  --params '{"users":"U07,U08","return_im":true}'
```

Returns:
```json
{"ok":true,"channel":{"id":"D023","is_im":true,"user":"U07"}}
```

## conversations.close

Close (hide) a DM. Doesn't delete history — just removes the DM from
the user's sidebar.

| Param     | Type   | Req | Description       |
|-----------|--------|-----|-------------------|
| `channel` | string | yes | DM/MPIM channel ID|

Scope: `im:write` / `mpim:write`.

```bash
python3 scripts/slack.py call conversations.close --params '{"channel":"D023"}'
```

## conversations.create

Create a public or private channel. Names must be lowercase, no spaces,
under 80 chars.

| Param        | Type   | Req | Description                          |
|--------------|--------|-----|--------------------------------------|
| `name`       | string | yes | channel name (lowercase, hyphenated) |
| `is_private` | bool   | no  | create as private channel            |
| `team_id`    | string | no  | Enterprise Grid: which workspace     |

Scope: `channels:write` or `groups:write`.

```bash
python3 scripts/slack.py call conversations.create \
  --params '{"name":"proj-launch-2026","is_private":false}'
```

Returns: `{"ok":true,"channel":{"id":"C0999","name":"proj-launch-2026",...}}`.

Gotchas: `name_taken` is the most common error. Slack normalizes names
(spaces → hyphens, uppercase → lowercase) — pre-normalize to avoid
surprises.

## conversations.archive / unarchive

Toggle archived state. Archived channels are read-only and hidden from
default searches.

```bash
python3 scripts/slack.py call conversations.archive --params '{"channel":"C0123"}'
python3 scripts/slack.py call conversations.unarchive --params '{"channel":"C0123"}'
```

Scope: `channels:write` or `groups:write`. Cannot archive `#general`.

## conversations.invite / kick

Add or remove users from a channel.

```bash
python3 scripts/slack.py call conversations.invite \
  --params '{"channel":"C0123","users":"U07,U08"}'
python3 scripts/slack.py call conversations.kick \
  --params '{"channel":"C0123","user":"U08"}'
```

Note `invite` takes csv `users`; `kick` takes a single `user`. Scope:
`channels:write` or `groups:write`.

## conversations.join / leave

```bash
python3 scripts/slack.py call conversations.join --params '{"channel":"C0123"}'
python3 scripts/slack.py call conversations.leave --params '{"channel":"C0123"}'
```

Scope: `channels:write` (join, public only); `channels:write` /
`groups:write` / `im:write` / `mpim:write` for leave. Joining a private
channel requires an invite; `conversations.join` will fail with
`channel_not_found` for those.

## conversations.rename

```bash
python3 scripts/slack.py call conversations.rename \
  --params '{"channel":"C0123","name":"general-renamed"}'
```

Scope: `channels:write` / `groups:write`. Same naming rules as `create`.

## conversations.setPurpose / setTopic

Purpose ≈ "what this channel is for". Topic ≈ "what's happening right
now". Both display in the channel header.

```bash
python3 scripts/slack.py call conversations.setPurpose \
  --params '{"channel":"C0123","purpose":"Coordinating the 2026 launch."}'
python3 scripts/slack.py call conversations.setTopic \
  --params '{"channel":"C0123","topic":"Launch day: 2026-06-01"}'
```

Scope: `channels:write` / `groups:write`. Topic and purpose accept up
to 250 chars; text is plain (no mrkdwn).
