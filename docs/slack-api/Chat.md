# chat.*

The `chat` namespace is how messages enter, change, and leave Slack.
Posting, editing, deleting, scheduling, ephemeral notes,
slash-command-style /me messages, permalinks, and link unfurls all
live here. Every write needs `chat:write`; reads of scheduled-message
state are scope-free.

A note on token identity: `chat.postMessage` from a User OAuth Token
posts *as the user who installed the app*. There is no
`as_user`/`username`/`icon_url` impersonation on a User Token — those
parameters were Bot-Token-era and are silently ignored or rejected.

## chat.postMessage

Send a message to a channel or DM. Supports plain text, `blocks` (Block
Kit JSON), or legacy `attachments`. At least one of `text`/`blocks` is
required.

| Param            | Type    | Req | Description                                              |
|------------------|---------|-----|----------------------------------------------------------|
| `channel`        | string  | yes | channel ID or channel name (`#general`)                  |
| `text`           | string  | no\*| message text (mrkdwn by default)                         |
| `blocks`         | string  | no\*| JSON-encoded array of Block Kit blocks                   |
| `attachments`    | string  | no  | JSON-encoded array of legacy attachments                 |
| `thread_ts`      | string  | no  | reply in a thread (parent's `ts`)                        |
| `reply_broadcast`| bool    | no  | also surface the threaded reply to the channel           |
| `mrkdwn`         | bool    | no  | enable mrkdwn parsing (default `true`)                   |
| `parse`          | string  | no  | `"full"` to auto-link, `"none"` to skip                  |
| `link_names`     | bool    | no  | linkify `@user` and `#channel` mentions                  |
| `unfurl_links`   | bool    | no  | unfurl URLs (default off for plain links)                |
| `unfurl_media`   | bool    | no  | unfurl media (default on for media URLs)                 |

\* one of `text` / `blocks` / `attachments` required.

Scope: `chat:write`.

Plain text:
```bash
python3 scripts/slack.py call chat.postMessage \
  --params '{"channel":"C0123","text":"Deploy is green."}'
```

Threaded reply, also broadcast to channel:
```bash
python3 scripts/slack.py call chat.postMessage \
  --params '{"channel":"C0123","thread_ts":"1714608123.001000","text":"Resolved.","reply_broadcast":true}'
```

Block Kit (note `blocks` must be a JSON-encoded *string* — slack.py
form-encodes the params, and Slack expects a stringified array):
```bash
python3 scripts/slack.py call chat.postMessage --params '{
  "channel":"C0123",
  "text":"Deploy is green.",
  "blocks":"[{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"*Deploy* is green.\"}}]"
}'
```

Returns:
```json
{"ok":true,"channel":"C0123","ts":"1714608999.003000","message":{"text":"Deploy is green.","user":"U07","ts":"1714608999.003000"}}
```

Gotchas: always include a `text` even when sending `blocks` — it's the
fallback shown in notifications and screen readers. mrkdwn (Slack's
flavor: `*bold*`, `_italic_`, `~strike~`, `<url|label>`) is *not*
CommonMark — don't pipe arbitrary GFM through it. `[paginated]` does
not apply.

## chat.postEphemeral

Post a message visible only to a single user in a channel. Useful for
"hey, only you can see this" coaching/debugging surfaces.

| Param      | Type   | Req | Description                          |
|------------|--------|-----|--------------------------------------|
| `channel`  | string | yes | channel ID                           |
| `user`     | string | yes | user ID who should see it            |
| `text`     | string | no\*| message text                         |
| `blocks`   | string | no\*| JSON-encoded blocks                  |
| `thread_ts`| string | no  | thread context                       |

\* one of `text`/`blocks` required.

Scope: `chat:write`.

```bash
python3 scripts/slack.py call chat.postEphemeral \
  --params '{"channel":"C0123","user":"U07","text":"Heads up — your token expires tomorrow."}'
```

Returns: `{"ok":true,"message_ts":"1714608999.003000"}`.

Gotchas: ephemerals can't be edited or deleted via `chat.update` /
`chat.delete`. They vanish on reload. The user must already be a
member of the channel.

## chat.update

Edit a message you posted. The `ts` is the message's original `ts`
(same field returned by `chat.postMessage`).

| Param   | Type   | Req | Description           |
|---------|--------|-----|-----------------------|
| `channel`| string| yes | channel ID            |
| `ts`    | string | yes | original message `ts` |
| `text`  | string | no\*| new text              |
| `blocks`| string | no\*| new blocks            |

\* one of `text`/`blocks` required.

Scope: `chat:write`.

```bash
python3 scripts/slack.py call chat.update \
  --params '{"channel":"C0123","ts":"1714608999.003000","text":"Deploy is green. (updated)"}'
```

Returns:
```json
{"ok":true,"channel":"C0123","ts":"1714608999.003000","text":"Deploy is green. (updated)"}
```

Gotchas: a User Token can edit only messages that user posted. Slack
sets `edited.ts` and `edited.user` on the message — clients show "(edited)".

## chat.delete

Delete a message. With a User Token this is a hard delete for the
caller's own messages.

| Param   | Type   | Req | Description           |
|---------|--------|-----|-----------------------|
| `channel`| string| yes | channel ID            |
| `ts`    | string | yes | message `ts`          |

Scope: `chat:write`.

```bash
python3 scripts/slack.py call chat.delete \
  --params '{"channel":"C0123","ts":"1714608999.003000"}'
```

Returns: `{"ok":true,"channel":"C0123","ts":"1714608999.003000"}`.

Gotchas: workspace admin policy may prevent message deletion entirely
(`cant_delete_message`). There's no undo.

## chat.meMessage

The `/me` slash-command equivalent. Posts an italicized
third-person-style message ("U07 reboots the server").

| Param   | Type   | Req | Description    |
|---------|--------|-----|----------------|
| `channel`| string| yes | channel ID     |
| `text`  | string | yes | the action text|

Scope: `chat:write`.

```bash
python3 scripts/slack.py call chat.meMessage \
  --params '{"channel":"C0123","text":"reboots the server"}'
```

Returns: `{"ok":true,"channel":"C0123","ts":"1714608999.003000"}`.

## chat.scheduleMessage

Schedule a message for the future. Useful for off-hours notifications.

| Param           | Type   | Req | Description                                  |
|-----------------|--------|-----|----------------------------------------------|
| `channel`       | string | yes | channel ID                                   |
| `post_at`       | int    | yes | Unix epoch seconds (UTC)                     |
| `text`          | string | no\*| message text                                 |
| `blocks`        | string | no\*| Block Kit JSON                               |
| `thread_ts`     | string | no  | thread reply                                 |
| `reply_broadcast`| bool  | no  | broadcast to channel                         |
| `unfurl_links`  | bool   | no  | (as `chat.postMessage`)                      |
| `unfurl_media`  | bool   | no  | (as `chat.postMessage`)                      |

\* one of `text`/`blocks` required.

Scope: `chat:write`.

```bash
python3 scripts/slack.py call chat.scheduleMessage \
  --params '{"channel":"C0123","post_at":1714694400,"text":"Standup in 5 minutes."}'
```

Returns:
```json
{"ok":true,"channel":"C0123","scheduled_message_id":"Q12345","post_at":1714694400}
```

Gotchas: `post_at` must be at least ~1 minute in the future and at
most 120 days out. `time_in_past` and `time_too_far` are common.

## chat.deleteScheduledMessage

Cancel a pending scheduled message.

| Param                 | Type   | Req | Description                |
|-----------------------|--------|-----|----------------------------|
| `channel`             | string | yes | channel ID                 |
| `scheduled_message_id`| string | yes | the `Q…` id from schedule  |

Scope: `chat:write`.

```bash
python3 scripts/slack.py call chat.deleteScheduledMessage \
  --params '{"channel":"C0123","scheduled_message_id":"Q12345"}'
```

Returns: `{"ok":true}`.

Gotchas: returns `bad_request` if the message has already been sent.

## chat.scheduledMessages.list

List the user's pending scheduled messages.

| Param   | Type   | Req | Description           |
|---------|--------|-----|-----------------------|
| `channel`| string| no  | filter to one channel |
| `latest`| string | no  | window upper bound    |
| `oldest`| string | no  | window lower bound    |
| `limit` | int    | no  | per-page              |
| `cursor`| string | no  | pagination            |

Scope: none beyond user token. Paginated.

```bash
python3 scripts/slack.py call chat.scheduledMessages.list --all
```

Returns:
```json
{"ok":true,"scheduled_messages":[{"id":"Q12345","channel_id":"C0123","post_at":1714694400,"date_created":1714608000,"text":"Standup in 5 minutes."}]}
```

## chat.getPermalink

Build a shareable permalink for a message. Cheap; no scope needed.

| Param        | Type   | Req | Description |
|--------------|--------|-----|-------------|
| `channel`    | string | yes | channel ID  |
| `message_ts` | string | yes | message `ts`|

```bash
python3 scripts/slack.py call chat.getPermalink \
  --params '{"channel":"C0123","message_ts":"1714608999.003000"}'
```

Returns:
```json
{"ok":true,"channel":"C0123","permalink":"https://yourteam.slack.com/archives/C0123/p1714608999003000"}
```

Gotchas: the URL has the `ts` with the dot stripped and `p` prepended.
The permalink works only for users who have access to the channel.

## chat.unfurl

Provide custom unfurl content for a link your app posted. Niche;
mostly used by Bot integrations responding to `link_shared` events. On
a User Token the practical use is rare — prefer letting Slack
auto-unfurl.

| Param      | Type   | Req | Description                        |
|------------|--------|-----|------------------------------------|
| `channel`  | string | yes | channel ID                         |
| `ts`       | string | yes | message `ts` containing the link   |
| `unfurls`  | string | yes | JSON-encoded `{url: {blocks: ...}}`|

Scope: `links:write` (NOT in this skill's manifest by default).

```bash
python3 scripts/slack.py call chat.unfurl --params '{
  "channel":"C0123",
  "ts":"1714608999.003000",
  "unfurls":"{\"https://example.com/x\":{\"blocks\":[{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"Custom unfurl.\"}}]}}"
}'
```

Returns: `{"ok":true}`.

Gotchas: needs the `links:write` scope, which the manifest does not
grant. Add it explicitly if you actually need this method.
