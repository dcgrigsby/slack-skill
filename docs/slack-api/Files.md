# files.*

File metadata access plus a write surface for uploads. Four methods
are in scope: `files.list`, `files.info`, `files.delete`, and the
`slack.py upload` subcommand (which orchestrates the modern 3-call
upload flow internally — see below). The manifest grants `files:read`;
`files.delete` and `slack.py upload` need `files:write`, which is
**not** in the default scope set.

A "file" in Slack covers many object types: classic uploads
(`filetype:pdf`, `png`, etc.), Slack-native posts, snippets, canvases,
and Slack Connect external files. Most fields are populated regardless
of type; type-specific fields appear conditionally.

## files.list

List files visible to the calling user. Pagination is page-based, not
cursor-based — slack.py's `--all` increments `page`.

| Param      | Type   | Req | Description                                                |
|------------|--------|-----|------------------------------------------------------------|
| `user`     | string | no  | filter to one uploader's files                             |
| `channel`  | string | no  | filter to one channel                                      |
| `ts_from`  | string | no  | files newer than this Unix ts                              |
| `ts_to`    | string | no  | files older than this Unix ts                              |
| `types`    | string | no  | csv: `all,spaces,snippets,images,gdocs,zips,pdfs`          |
| `count`    | int    | no  | per-page (max 1000, default 100)                           |
| `page`     | int    | no  | 1-indexed                                                  |
| `show_files_hidden_by_limit`| bool | no | include files hidden by free-tier message limit         |

Scope: `files:read`. Paginated via `page`.

All files in a channel:
```bash
python3 scripts/slack.py call files.list \
  --params '{"channel":"C0123","count":200}' --all
```

PDFs uploaded by one user this year:
```bash
python3 scripts/slack.py call files.list \
  --params '{"user":"U07","types":"pdfs","ts_from":"1704067200","count":100}' --all
```

Returns:
```json
{"ok":true,"files":[{"id":"F012345","created":1714608000,"timestamp":1714608000,"name":"roadmap.pdf","title":"2026 Roadmap","mimetype":"application/pdf","filetype":"pdf","pretty_type":"PDF","user":"U07","size":182374,"url_private":"https://files.slack.com/files-pri/T01-F012345/roadmap.pdf","url_private_download":"https://files.slack.com/files-pri/T01-F012345/download/roadmap.pdf","permalink":"https://yourteam.slack.com/files/U07/F012345/roadmap.pdf","permalink_public":"https://slack-files.com/...","channels":["C0123"],"groups":[],"ims":[]}],"paging":{"count":100,"total":237,"page":1,"pages":3}}
```

Gotchas:
- `types` is a *csv*, not a single value: `"types":"pdfs,images"`.
- `channels` / `groups` / `ims` show every place the file is shared,
  not just the channel filter you queried.
- Free-tier workspaces hide files older than the message limit; pass
  `show_files_hidden_by_limit:true` to include them.
- Slack Connect external files have `external_type` set and limited
  download URLs.

## files.info

Detailed metadata + comments + share history for one file.

| Param        | Type   | Req | Description                              |
|--------------|--------|-----|------------------------------------------|
| `file`       | string | yes | file ID (`F…`)                           |
| `count`      | int    | no  | comments per page (max 100)              |
| `page`       | int    | no  | comment page                             |
| `limit`      | int    | no  | newer cursor-style limit (use with `cursor`) |
| `cursor`     | string | no  | cursor pagination for shares             |

Scope: `files:read`. Paginated via `page` (comments) or `cursor`
(shares).

```bash
python3 scripts/slack.py call files.info --params '{"file":"F012345"}'
```

Returns:
```json
{"ok":true,"file":{"id":"F012345","name":"roadmap.pdf","filetype":"pdf","user":"U07","size":182374,"url_private":"https://files.slack.com/files-pri/T01-F012345/roadmap.pdf","permalink":"https://yourteam.slack.com/files/U07/F012345/roadmap.pdf","shares":{"public":{"C0123":[{"reply_users":["U08"],"reply_users_count":1,"reply_count":1,"ts":"1714608123.001000","channel_name":"general","team_id":"T01"}]},"private":{}}},"comments":[],"response_metadata":{"next_cursor":""}}
```

Gotchas: `comments` is mostly historical (file comments were
deprecated) — usually an empty array. `shares` is more interesting:
`public` and `private` keys, each mapping channel ID → list of share
events.

## files.delete

Delete a file. Cannot be undone.

| Param  | Type   | Req | Description |
|--------|--------|-----|-------------|
| `file` | string | yes | file ID     |

Scope: `files:write` (NOT in this skill's manifest by default).

```bash
python3 scripts/slack.py call files.delete --params '{"file":"F012345"}'
```

Returns: `{"ok":true}`.

Gotchas: a User Token can delete only its own uploads (or any if the
user is workspace admin and admin scopes are granted). Errors:
`cant_delete_file` (insufficient permission), `file_not_found`,
`file_deleted` (already gone).

## slack.py upload — modern 3-call flow

Slack deprecated the single-call `files.upload` (multipart) endpoint
in favor of a 3-call sequence:

1. `files.getUploadURLExternal` — Slack returns a one-time signed URL
   and a `file_id`.
2. `POST` the file's bytes to that URL as `multipart/form-data` (the
   `file` field carries the bytes). Slack rejects raw PUT with a 302.
3. `files.completeUploadExternal` — tell Slack the bytes are uploaded
   and (optionally) which channel to share the file in.

The `slack.py upload` subcommand orchestrates all three internally. It
does not support the deprecated `files.upload`.

```bash
python3 scripts/slack.py upload \
  --file ./report.pdf \
  --channel C0123 \
  --title "Q4 report" \
  --initial-comment "Latest draft, comments welcome."
```

Without `--channel`, the file is uploaded but not shared anywhere — the
user is the only one who can see it via `files.list`. To post into a
thread instead of a channel root, also pass `--thread-ts <ts>`. For
images, `--alt-text` provides accessibility text.

Scope: `files:write`. Errors:
- `missing_scope` — token lacks `files:write` (see scope walkthrough
  in the README to add it).
- `not_in_channel` — token holder isn't a member of `--channel`. For
  public channels, `conversations.join` first.
- `file_not_found` (during step 3) — the `file_id` from step 1 wasn't
  populated by a successful POST in step 2; usually means the upload
  itself failed with an HTTP error.

The POST step does not retry on transport failure; if it fails, the
whole subcommand exits 3 and the file_id from step 1 is wasted (Slack
will garbage-collect it within a few hours). Any non-2xx status from
step 2 is treated as failure — Slack rejects malformed uploads with a
302 redirect to https://slack.com rather than a 4xx.

## URL fields — when each is appropriate

A file response has multiple URLs. Pick the right one:

| Field                   | Auth         | Use case                                              |
|-------------------------|--------------|-------------------------------------------------------|
| `url_private`           | Bearer token | Programmatic download with the same token             |
| `url_private_download`  | Bearer token | Like `url_private` but forces `Content-Disposition: attachment` |
| `permalink`             | Browser cookie | "Open the file in Slack" — redirects to the desktop app or web client |
| `permalink_public`      | None (token-shaped URL) | Only present after `files.sharedPublicURL`. Not granted by default |
| `thumb_*`               | Bearer token | Thumbnails: `thumb_64`, `thumb_360`, etc.             |

Direct fetch:
```bash
TOKEN=...           # User OAuth Token
curl -H "Authorization: Bearer $TOKEN" \
     -o roadmap.pdf \
     "https://files.slack.com/files-pri/T01-F012345/roadmap.pdf"
```

If you forget the `Authorization` header, Slack returns the team's
sign-in HTML page — not an HTTP error, just unexpected bytes.

## Common errors

| Error             | Cause                                                  |
|-------------------|--------------------------------------------------------|
| `file_not_found`  | Wrong ID, file deleted, or token can't see it          |
| `file_deleted`    | File was deleted previously                            |
| `cant_delete_file`| Token can't delete this file (not owner / no admin)    |
| `not_in_channel`  | Listing a channel the token isn't in                   |
| `missing_scope`   | Need `files:read` (and `files:write` for `files.delete`)|

## Tip: find files referenced in a message

A message's `files[]` array gives you file IDs you can pass to
`files.info`:

```bash
python3 scripts/slack.py call conversations.history \
  --params '{"channel":"C0123","limit":50}' \
  | jq '.messages[] | select(.files) | .files[].id'
```

For each ID, fetch metadata:

```bash
python3 scripts/slack.py call files.info --params '{"file":"F012345"}'
```
