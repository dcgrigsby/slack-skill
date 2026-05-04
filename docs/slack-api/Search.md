# search.*

Workspace-wide message and file search. Three methods:
`search.messages`, `search.files`, and `search.all` (the union).
Search is User-Token-only — Bot Tokens cannot search and will fail
with `not_allowed_token_type`. The skill's manifest grants
`search:read`.

Search uses *page-based* pagination, not cursor-based. The CLI's
`--all` understands this and increments `page` instead of walking
`next_cursor`.

## Query syntax (works for all three methods)

Slack's query DSL mirrors the in-app search bar:

| Filter                 | Example                          | Notes                                       |
|------------------------|----------------------------------|---------------------------------------------|
| Channel                | `in:#general`                    | Or `in:C0123`                               |
| User                   | `from:@alice`                    | Or `from:U07`                               |
| Date range             | `before:2026-01-01`              | ISO date                                    |
|                        | `after:2026-01-01`               |                                             |
|                        | `during:2026`                    | year, month, or YYYY-MM                     |
|                        | `on:2026-05-02`                  | exact day                                   |
| Has                    | `has:link`, `has:star`, `has:pin`, `has:reaction` |                          |
| File type              | `has:image`, `has:document`      |                                             |
| Reactions              | `hasmy::thumbsup:`               | items the *caller* reacted to              |
| Threads                | `is:thread`                      | thread parents only                         |
| Phrase                 | `"deploy is green"`              | exact match                                 |
| Negation               | `-from:@alice`                   |                                             |
| Boolean OR             | `deploy OR rollout`              | uppercase OR                                |

Combine freely: `deploy in:#engineering from:@alice after:2026-04-01`.

## search.messages

Search messages.

| Param      | Type   | Req | Description                                          |
|------------|--------|-----|------------------------------------------------------|
| `query`    | string | yes | query string (see above)                             |
| `count`    | int    | no  | per-page (max 100, default 20)                       |
| `page`     | int    | no  | 1-indexed page number                                |
| `sort`     | string | no  | `score` (default) or `timestamp`                     |
| `sort_dir` | string | no  | `asc` or `desc` (default `desc`)                     |
| `highlight`| bool   | no  | wrap matches in `…` markers              |

Scope: `search:read`. Paginated via `page`.

```bash
python3 scripts/slack.py call search.messages \
  --params '{"query":"deploy in:#engineering from:@alice after:2026-04-01","sort":"timestamp","sort_dir":"desc","count":50}' --all
```

Returns:
```json
{"ok":true,"query":"deploy in:#engineering ...","messages":{"total":143,"pagination":{"total_count":143,"page":1,"per_page":50,"page_count":3,"first":1,"last":50},"paging":{"count":50,"total":143,"page":1,"pages":3},"matches":[{"type":"message","channel":{"id":"C0123","name":"engineering"},"user":"U07","username":"alice","ts":"1714608999.003000","text":"Deploy is green.","permalink":"https://...","previous":{"text":"...","ts":"..."},"next":{"text":"...","ts":"..."}}]}}
```

Gotchas:
- Each match includes `previous` / `next` snippets (single-message
  before/after context). For full thread context, separate
  `conversations.replies` call.
- `total` may exceed what's actually retrievable — Slack caps at
  ~1000 results regardless of pagination.
- `sort=score` ranks by relevance; `sort=timestamp` is a chronological
  feed.

## search.files

Search files. Same query DSL, results in `files.matches[]`.

| Param      | Type   | Req | Description                          |
|------------|--------|-----|--------------------------------------|
| `query`    | string | yes | query string                         |
| `count`    | int    | no  | per-page (max 100)                   |
| `page`     | int    | no  | 1-indexed                            |
| `sort`     | string | no  | `score` or `timestamp`               |
| `sort_dir` | string | no  | `asc` / `desc`                       |
| `highlight`| bool   | no  | wrap match markers                   |

Scope: `search:read`. Paginated via `page`.

```bash
python3 scripts/slack.py call search.files \
  --params '{"query":"name:roadmap.pdf in:#planning","count":20}' --all
```

Returns:
```json
{"ok":true,"query":"name:roadmap.pdf ...","files":{"total":7,"pagination":{"page":1,"page_count":1,"total_count":7},"matches":[{"id":"F012345","name":"roadmap.pdf","title":"2026 Roadmap","filetype":"pdf","size":182374,"user":"U07","url_private":"https://...","permalink":"https://..."}]}}
```

File-specific filter: `name:something.pdf` matches the filename
field. `filetype:pdf` matches any PDF.

## search.all

Combined search across messages *and* files. Useful when you don't
know which kind of object holds the answer.

| Param   | Type   | Req | Description                |
|---------|--------|-----|----------------------------|
| `query` | string | yes | query string               |
| `count` | int    | no  | per-page                   |
| `page`  | int    | no  | 1-indexed                  |
| `sort`  | string | no  | `score` or `timestamp`     |
| `sort_dir`| string| no | `asc` / `desc`             |

Scope: `search:read`. Paginated via `page`.

```bash
python3 scripts/slack.py call search.all \
  --params '{"query":"q3 retro","count":50}'
```

Returns:
```json
{"ok":true,"query":"q3 retro","messages":{"total":12,"matches":[...]},"files":{"total":3,"matches":[...]},"posts":{"total":0,"matches":[]}}
```

Gotchas: `posts` is the legacy "Slack Posts" surface (largely
replaced by canvas) — almost always empty. Iterate the `messages` and
`files` arrays separately.

## Pagination

`page` starts at 1. The response carries pagination state at
`messages.pagination.page_count` (or `files.pagination`,
`messages.paging.pages`). With `--all`, slack.py walks the nested
`messages.matches` / `files.matches` array and increments `page` until
exhausted, returning a flat `{ok, items, page_count}` envelope.

```bash
python3 scripts/slack.py call search.messages \
  --params '{"query":"deploy","count":100}' --all --limit 1000
```

`search.all` is the exception. It returns both `messages.matches` and
`files.matches`, which is genuinely ambiguous — `--all` errors out
rather than silently picking one. To paginate `search.all`, either
iterate each namespace separately (`search.messages` / `search.files`),
or step `page` manually:

```bash
for p in 1 2 3; do
  python3 scripts/slack.py call search.all \
    --params "{\"query\":\"deploy\",\"page\":$p,\"count\":100}"
done
```

## Common errors

| Error                     | Cause                                                 |
|---------------------------|-------------------------------------------------------|
| `not_allowed_token_type`  | Bot Token used; only User Tokens may search          |
| `invalid_arg_name`        | Misspelled query operator (e.g. `from:`→`form:`)     |
| `missing_scope`           | Token lacks `search:read`                            |
| `query_too_short`         | Empty or single-character query                      |

## Tip: thread context

Search returns flat messages. To assemble a thread around a hit:

```bash
# 1. Find the hit
python3 scripts/slack.py call search.messages \
  --params '{"query":"deploy is green from:@alice","count":1}'

# 2. If hit.thread_ts is set, fetch the thread
python3 scripts/slack.py call conversations.replies \
  --params '{"channel":"C0123","ts":"1714608123.001000"}' --all
```

If `thread_ts` is absent, the hit is a top-level message — no thread
to fetch.
