# pins.* / stars.* / bookmarks.*

Three small, related namespaces grouped together. They all attach
extra context to messages or channels but with different semantics:

- **Pins** — channel-scoped, *visible to all members*. The "important
  message in this channel" mechanism.
- **Stars** — user-private (deprecated in modern Slack, replaced by
  Saved Items in the UI, but the API still works). Each star points
  at a message, file, or file-comment.
- **Bookmarks** — channel-scoped, structured (link / file / etc.),
  shown as a row at the top of the channel. Use these when you want
  *named* references rather than message pins.

The manifest grants `pins:read`, `pins:write`, `stars:read`,
`stars:write`, `bookmarks:read`, `bookmarks:write`.

---

## pins

### pins.add

Pin a message to a channel.

| Param      | Type   | Req | Description       |
|------------|--------|-----|-------------------|
| `channel`  | string | yes | channel ID        |
| `timestamp`| string | yes | message `ts`      |

Scope: `pins:write`.

```bash
python3 scripts/slack.py call pins.add \
  --params '{"channel":"C0123","timestamp":"1714608999.003000"}'
```

Returns: `{"ok":true}`.

Gotchas: `already_pinned` if the message is already pinned. The 100-pin
limit per channel is enforced as `too_many_pins` once you cross it.

### pins.remove

Unpin a message.

| Param      | Type   | Req | Description       |
|------------|--------|-----|-------------------|
| `channel`  | string | yes | channel ID        |
| `timestamp`| string | yes | message `ts`      |

Scope: `pins:write`.

```bash
python3 scripts/slack.py call pins.remove \
  --params '{"channel":"C0123","timestamp":"1714608999.003000"}'
```

Returns: `{"ok":true}`.

Gotchas: `no_pin` if the message wasn't pinned. Anyone with
`pins:write` can unpin (it's not restricted to the original pinner).

### pins.list

List pins in a channel.

| Param     | Type   | Req | Description |
|-----------|--------|-----|-------------|
| `channel` | string | yes | channel ID  |

Scope: `pins:read`. Not paginated (the channel limit caps at ~100).

```bash
python3 scripts/slack.py call pins.list --params '{"channel":"C0123"}'
```

Returns:
```json
{"ok":true,"items":[{"type":"message","channel":"C0123","created":1714610000,"created_by":"U07","message":{"ts":"1714608999.003000","text":"Deploy is green.","user":"U07","permalink":"https://..."}}]}
```

Gotchas: `type` discriminates `message` vs (legacy) `file` /
`file_comment` pins. New pins are message-only; older workspaces may
have file pins still surfaced.

---

## stars

Stars are this user's private "save for later" list. Slack's UI now
calls these *Saved Items*; the API name is still `stars`.

### stars.add

Star an item — a message, a file, or a file comment. Pass exactly
*one* of `(channel,timestamp)`, `file`, or `file_comment`.

| Param         | Type   | Req | Description                            |
|---------------|--------|-----|----------------------------------------|
| `channel`     | string | no\*| channel for a message star             |
| `timestamp`   | string | no\*| message `ts` (with `channel`)          |
| `file`        | string | no\*| file ID                                |
| `file_comment`| string | no\*| file-comment ID (legacy)               |

\* one of the three identifying tuples required.

Scope: `stars:write`.

Star a message:
```bash
python3 scripts/slack.py call stars.add \
  --params '{"channel":"C0123","timestamp":"1714608999.003000"}'
```

Star a file:
```bash
python3 scripts/slack.py call stars.add --params '{"file":"F012345"}'
```

Returns: `{"ok":true}`.

Gotchas: `already_starred` is the most common error. Slack's modern UI
labels these "Saved Items"; if a user expects the saved list to
update, this method does it.

### stars.remove

Inverse of `stars.add`. Same param shape.

```bash
python3 scripts/slack.py call stars.remove \
  --params '{"channel":"C0123","timestamp":"1714608999.003000"}'
```

Scope: `stars:write`. Returns: `{"ok":true}`.

Gotchas: `not_starred` if the item wasn't starred to begin with.

### stars.list

List the caller's stars. Page-based pagination.

| Param   | Type | Req | Description                  |
|---------|------|-----|------------------------------|
| `count` | int  | no  | per-page (max 1000)          |
| `page`  | int  | no  | 1-indexed                    |
| `limit` | int  | no  | cursor-style (newer)         |
| `cursor`| string| no | cursor pagination            |

Scope: `stars:read`. Paginated (page-based; `--all` handles both).

```bash
python3 scripts/slack.py call stars.list --params '{"count":100}' --all
```

Returns:
```json
{"ok":true,"items":[{"type":"message","channel":"C0123","message":{"ts":"1714608999.003000","text":"Deploy is green."}},{"type":"file","file":{"id":"F012345","name":"roadmap.pdf"}}],"paging":{"count":100,"total":42,"page":1,"pages":1}}
```

Gotchas: cannot list someone else's stars — they're private. The
`type` discriminator differs per item: `message`, `file`,
`file_comment`, `channel` (legacy), `im`, `group`.

---

## bookmarks

Channel bookmarks are structured links surfaced at the top of a
channel — a "tabs row". Each bookmark has a type and a stable id.

### bookmarks.add

Add a bookmark to a channel.

| Param       | Type   | Req | Description                                                  |
|-------------|--------|-----|--------------------------------------------------------------|
| `channel_id`| string | yes | channel ID                                                   |
| `title`     | string | yes | display title                                                |
| `type`      | string | yes | `link` (most common) or `file` etc.                          |
| `link`      | string | no  | URL (for `type:link`)                                        |
| `emoji`     | string | no  | emoji shortname (e.g. `:books:`) — **with** colons here      |
| `entity_id` | string | no  | linked Slack entity (rare)                                   |
| `parent_id` | string | no  | parent bookmark id (folder/grouping; rarely used)            |

Scope: `bookmarks:write`.

```bash
python3 scripts/slack.py call bookmarks.add --params '{
  "channel_id":"C0123",
  "title":"Runbooks",
  "type":"link",
  "link":"https://example.com/runbooks",
  "emoji":":books:"
}'
```

Returns:
```json
{"ok":true,"bookmark":{"id":"Bk012345","channel_id":"C0123","title":"Runbooks","type":"link","link":"https://example.com/runbooks","emoji":":books:","date_created":1714610000,"date_updated":1714610000,"last_updated_by_user_id":"U07"}}
```

Gotchas:
- `emoji` *does* take colons here, unlike `reactions.add`. Yes, it's
  inconsistent.
- Only `type:link` is broadly supported in v1 of this skill.
- `bad_request` if `link` is missing on a `type:link` bookmark.

### bookmarks.edit

Edit a bookmark's display fields. Cannot change `type`.

| Param        | Type   | Req | Description                |
|--------------|--------|-----|----------------------------|
| `bookmark_id`| string | yes | bookmark id (`Bk…`)        |
| `channel_id` | string | yes | channel ID                 |
| `title`      | string | no  | new title                  |
| `link`       | string | no  | new URL                    |
| `emoji`      | string | no  | new emoji (with colons)    |

Scope: `bookmarks:write`.

```bash
python3 scripts/slack.py call bookmarks.edit --params '{
  "bookmark_id":"Bk012345",
  "channel_id":"C0123",
  "title":"On-Call Runbooks",
  "emoji":":fire:"
}'
```

Returns: same shape as `bookmarks.add`'s response, with
`date_updated` advanced.

### bookmarks.remove

Delete a bookmark. No undo.

| Param        | Type   | Req | Description       |
|--------------|--------|-----|-------------------|
| `bookmark_id`| string | yes | bookmark id       |
| `channel_id` | string | yes | channel ID        |

Scope: `bookmarks:write`.

```bash
python3 scripts/slack.py call bookmarks.remove \
  --params '{"bookmark_id":"Bk012345","channel_id":"C0123"}'
```

Returns: `{"ok":true}`.

### bookmarks.list

List bookmarks for a channel.

| Param        | Type   | Req | Description |
|--------------|--------|-----|-------------|
| `channel_id` | string | yes | channel ID  |

Scope: `bookmarks:read`. Not paginated.

```bash
python3 scripts/slack.py call bookmarks.list --params '{"channel_id":"C0123"}'
```

Returns:
```json
{"ok":true,"bookmarks":[{"id":"Bk012345","channel_id":"C0123","title":"Runbooks","type":"link","link":"https://example.com/runbooks","emoji":":books:","date_created":1714610000,"last_updated_by_user_id":"U07"}]}
```

Gotchas: a "Channel Canvas" auto-bookmark may appear with
`type:bookmark` and a Slack-internal link — leave it alone unless you
have a specific reason to edit.

---

## When to use which

| Need                                           | Use                |
|------------------------------------------------|--------------------|
| Highlight a message everyone in a channel should see | **pins**     |
| Save a personal note for later                 | **stars**          |
| Surface a named link / doc at the channel header | **bookmarks**    |
| "Important docs" navigation row                | **bookmarks**      |
| Deep-link a permalink from search results       | **stars** (private) or **pins** (public) |

The functional overlap is real — pins and bookmarks both attach to
channels — but pins are tied to *messages*, and bookmarks are tied to
*links / titles*. Pick the one that matches the natural identity of
the thing.
