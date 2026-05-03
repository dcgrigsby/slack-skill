# reactions.*

Emoji reactions on messages and files. Four methods: two writes
(`add`, `remove`) and two reads (`get`, `list`). Names of emoji are
passed *without* surrounding colons — `thumbsup`, not `:thumbsup:`.
Skin tones are appended with `::`: `wave::skin-tone-3`.

The skill's manifest grants `reactions:read` and `reactions:write`.

## reactions.add

React to a message (or file) with an emoji.

| Param      | Type   | Req | Description                                           |
|------------|--------|-----|-------------------------------------------------------|
| `name`     | string | yes | emoji name without colons (`thumbsup`, `tada`)        |
| `channel`  | string | yes | channel containing the message                        |
| `timestamp`| string | yes | message `ts`                                          |

Scope: `reactions:write`.

```bash
python3 scripts/slack.py call reactions.add \
  --params '{"name":"thumbsup","channel":"C0123","timestamp":"1714608999.003000"}'
```

Returns: `{"ok":true}`.

Gotchas:
- `:thumbsup:` (with colons) returns `invalid_name`. Strip them.
- `already_reacted` if the user already added that exact emoji.
  `reactions.add` is *not* fully idempotent — re-adding the same
  emoji errors instead of silently succeeding.
- Custom workspace emoji work (e.g. `:partyparrot:` → `partyparrot`),
  but skin-tone modifiers must be appended in API form
  (`thumbsup::skin-tone-3`, not `thumbsup_tone3`).
- `invalid_name` for emoji that don't exist in the workspace; check
  `emoji.list` for the full list of custom emoji.
- `channel_not_found` if the user can't see the channel (private
  channel they're not a member of, archived channel, etc.).

## reactions.remove

Remove a reaction the user previously added. Only removes the
caller's own reactions.

| Param      | Type   | Req | Description                                           |
|------------|--------|-----|-------------------------------------------------------|
| `name`     | string | yes | emoji name without colons                             |
| `channel`  | string | yes | channel containing the message                        |
| `timestamp`| string | yes | message `ts`                                          |

Scope: `reactions:write`.

```bash
python3 scripts/slack.py call reactions.remove \
  --params '{"name":"thumbsup","channel":"C0123","timestamp":"1714608999.003000"}'
```

Returns: `{"ok":true}`.

Gotchas: `no_reaction` if the user hadn't added that reaction. Like
`add`, this is per-user — it never strips other users' reactions.

## reactions.get

Reactions on a single item (message or file). One round-trip, returns
the full message (with its reactions) — no pagination.

| Param         | Type   | Req | Description                                       |
|---------------|--------|-----|---------------------------------------------------|
| `channel`     | string | no\*| channel ID (with `timestamp`)                    |
| `timestamp`   | string | no\*| message `ts` (with `channel`)                    |
| `file`        | string | no\*| file ID (alternative to channel/timestamp)       |
| `file_comment`| string | no\*| file-comment ID                                  |
| `full`        | bool   | no  | return the full reactor list (default truncated)  |

\* exactly one of `channel`+`timestamp`, `file`, or `file_comment`.

Scope: `reactions:read`.

Message:
```bash
python3 scripts/slack.py call reactions.get \
  --params '{"channel":"C0123","timestamp":"1714608999.003000","full":true}'
```

Returns:
```json
{"ok":true,"type":"message","channel":"C0123","message":{"ts":"1714608999.003000","text":"Deploy is green.","reactions":[{"name":"thumbsup","users":["U07","U08"],"count":2},{"name":"tada","users":["U09"],"count":1}]}}
```

File:
```bash
python3 scripts/slack.py call reactions.get \
  --params '{"file":"F012345","full":true}'
```

Gotchas: without `full=true`, the `users` array is capped (often at 25
users); the `count` is always exact. If the message has no reactions,
`message.reactions` is absent (not an empty array).

## reactions.list

Items the *calling user* has reacted to. Useful for "what have I
liked recently" workflows. Paginated (cursor-based).

| Param   | Type   | Req | Description                                       |
|---------|--------|-----|---------------------------------------------------|
| `user`  | string | no  | filter by a different user (rarely allowed)       |
| `full`  | bool   | no  | full reactor lists                                |
| `count` | int    | no  | per-page count (legacy; prefer `limit`)           |
| `limit` | int    | no  | per-page                                          |
| `cursor`| string | no  | pagination                                        |

Scope: `reactions:read`. Paginated.

```bash
python3 scripts/slack.py call reactions.list \
  --params '{"limit":100}' --all
```

Returns:
```json
{"ok":true,"items":[{"type":"message","channel":"C0123","message":{"ts":"1714608999.003000","text":"...","reactions":[{"name":"thumbsup","count":2}]}},{"type":"file","file":{"id":"F012345","name":"design.png","reactions":[{"name":"tada","count":1}]}}],"response_metadata":{"next_cursor":""}}
```

Gotchas: each item has a `type` discriminator (`message`, `file`,
`file_comment`); the relevant fields differ. Only your own reactions
appear unless workspace policy permits the `user` filter (it usually
doesn't on a User Token).

## Common error patterns

| Error             | Cause                                                  | Fix                                        |
|-------------------|--------------------------------------------------------|--------------------------------------------|
| `invalid_name`    | Emoji doesn't exist, or you sent `:name:` with colons  | Strip colons; check `emoji.list`           |
| `already_reacted` | You've already added that emoji                        | Treat as success, or check before adding   |
| `no_reaction`     | Trying to remove a reaction you never added            | Treat as success                           |
| `channel_not_found`| Private channel you're not a member of                | Join, or use a token from a member         |
| `message_not_found`| Wrong `ts` or message was deleted                     | Re-fetch via `conversations.history`       |
| `not_reactable`   | Workspace policy blocks reactions on that item         | Inspect `team.preferences.list`            |

## Tip: discover available emoji

```bash
python3 scripts/slack.py call emoji.list
```

Returns `{"ok":true,"emoji":{"partyparrot":"https://...","alias:thumbsup":"alias:+1",...}}`.
The keys are the names you pass to `reactions.add` (drop any `alias:`
prefix and follow the alias to the canonical name).
