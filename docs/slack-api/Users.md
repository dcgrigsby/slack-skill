# users.*

Workspace member directory: identity, profiles, presence, and the
list of conversations a user belongs to. Most reads need `users:read`;
email lookup needs the separate `users:read.email` (the manifest does
not grant it by default — request it explicitly if you need it).
Profile reads need `users.profile:read`; presence/active writes need
`users:write` (likewise not granted by default).

## users.list

Every member of the workspace. On large workspaces (10k+) this is
slow — paginate, and consider caching.

| Param           | Type   | Req | Description                          |
|-----------------|--------|-----|--------------------------------------|
| `limit`         | int    | no  | per-page (max 200, soft cap)         |
| `include_locale`| bool   | no  | include `locale` field per user      |
| `team_id`       | string | no  | Enterprise Grid: which workspace     |
| `cursor`        | string | no  | pagination                           |

Scope: `users:read`. Paginated.

```bash
python3 scripts/slack.py call users.list --params '{"limit":200}' --all --limit 5000
```

Returns:
```json
{"ok":true,"members":[{"id":"U07","team_id":"T01","name":"alice","real_name":"Alice Liu","deleted":false,"is_bot":false,"profile":{"display_name":"alice","real_name":"Alice Liu","email":"alice@example.com","image_72":"https://..."}}],"response_metadata":{"next_cursor":""}}
```

Gotchas: includes deactivated users (`deleted:true`) and bots
(`is_bot:true`) — filter client-side. Slackbot has id `USLACKBOT`. The
`team_id` differs across Enterprise Grid workspaces.

## users.info

Profile and metadata for one user.

| Param           | Type   | Req | Description                |
|-----------------|--------|-----|----------------------------|
| `user`          | string | yes | user ID                    |
| `include_locale`| bool   | no  | include `locale`           |

Scope: `users:read`.

```bash
python3 scripts/slack.py call users.info --params '{"user":"U07"}'
```

Returns:
```json
{"ok":true,"user":{"id":"U07","name":"alice","real_name":"Alice Liu","tz":"America/Los_Angeles","tz_offset":-25200,"profile":{"display_name":"alice","real_name":"Alice Liu","title":"Eng Lead","status_text":"on vacation","status_emoji":":palm_tree:","email":"alice@example.com"},"is_admin":false,"is_owner":false,"updated":1714000000}}
```

Gotchas: pick a display name with a sensible fallback chain — Slack
clients use roughly:
`profile.display_name || profile.real_name || real_name || name`.
Don't show `name` (the legacy login handle) when better fields exist.

## users.lookupByEmail

Resolve a user by email.

| Param   | Type   | Req | Description |
|---------|--------|-----|-------------|
| `email` | string | yes | full email  |

Scope: `users:read.email` (NOT in this skill's manifest by default).

```bash
python3 scripts/slack.py call users.lookupByEmail \
  --params '{"email":"alice@example.com"}'
```

Returns:
```json
{"ok":true,"user":{"id":"U07","name":"alice","profile":{"display_name":"alice","email":"alice@example.com"}}}
```

Gotchas: `users_not_found` for emails the workspace doesn't recognize.
Add `users:read.email` to the manifest's user scopes before using.

## users.identity

The token's own user identity (minimal). Available with the
`identity.basic` scope, which is granted by Sign-In-with-Slack.

| Param  | Type | Req | Description |
|--------|------|-----|-------------|
| (none) |      |     |             |

Scope: `identity.basic`.

```bash
python3 scripts/slack.py call users.identity
```

Returns:
```json
{"ok":true,"user":{"name":"Alice Liu","id":"U07"},"team":{"id":"T01"}}
```

Gotchas: `users.identity` is a different scope path from `users:read`
and is mostly for SIWA-flow apps. For regular skill usage, prefer
`auth.test` (no scope) plus `users.info` on the resulting `user_id`.

## users.conversations

Conversations the *token's user* belongs to. Scoped per-type by
`*:read` scopes; defaults to `public_channel`.

| Param            | Type   | Req | Description                                                |
|------------------|--------|-----|------------------------------------------------------------|
| `types`          | string | no  | csv of `public_channel,private_channel,im,mpim`            |
| `exclude_archived`| bool  | no  | hide archived                                              |
| `user`           | string | no  | filter to a specific user (limited utility on User Token)  |
| `limit`          | int    | no  | per-page                                                   |
| `cursor`         | string | no  | pagination                                                 |

Scope: `channels:read,groups:read,im:read,mpim:read`. Paginated.

```bash
python3 scripts/slack.py call users.conversations \
  --params '{"types":"public_channel,private_channel,im,mpim","exclude_archived":true,"limit":1000}' --all
```

Returns:
```json
{"ok":true,"channels":[{"id":"C0123","name":"general","is_channel":true,"is_member":true},{"id":"D023","is_im":true,"user":"U08"}],"response_metadata":{"next_cursor":""}}
```

Gotchas: `users.conversations` is *the token's* memberships, not the
workspace's full channel list. To enumerate all channels visible to
the token (members of or not), use `conversations.list`.

## users.profile.get

Profile fields for a user, including custom (workspace-defined) fields.

| Param            | Type   | Req | Description                  |
|------------------|--------|-----|------------------------------|
| `user`           | string | no  | user ID; defaults to caller  |
| `include_labels` | bool   | no  | include label metadata       |

Scope: `users.profile:read`.

```bash
python3 scripts/slack.py call users.profile.get --params '{"user":"U07","include_labels":true}'
```

Returns:
```json
{"ok":true,"profile":{"display_name":"alice","real_name":"Alice Liu","email":"alice@example.com","status_text":"","status_emoji":"","fields":{"Xf01ABCD":{"value":"Eng","alt":""},"Xf01EFGH":{"value":"SF","alt":""}}}}
```

Gotchas: custom fields are keyed by `Xf…` IDs, not human names. Map
IDs to labels with `team.profile.get`.

## users.profile.set

Update the *caller's* profile. Either set one field
(`name`+`value`) or push a JSON `profile` object containing many.

| Param    | Type   | Req | Description                                |
|----------|--------|-----|--------------------------------------------|
| `name`   | string | no\*| field name (`status_text`, `display_name`) |
| `value`  | string | no\*| new value                                  |
| `profile`| string | no\*| JSON-encoded full profile object           |
| `user`   | string | no  | admin only — set someone else's profile    |

\* either (`name`+`value`) or `profile` required.

Scope: `users.profile:write` (NOT in this skill's manifest by default).

Set status:
```bash
python3 scripts/slack.py call users.profile.set --params '{
  "profile":"{\"status_text\":\"deep work\",\"status_emoji\":\":dart:\",\"status_expiration\":1714694400}"
}'
```

Returns: `{"ok":true,"profile":{...full updated profile...}}`.

Gotchas: `status_expiration` is a Unix epoch (seconds), not minutes.
Setting it to `0` clears the expiration (status persists).
`name`+`value` is convenient for one field; `profile` is required for
nested fields.

## users.setActive

Mark the user as active (defeats away-on-idle for ~5 minutes).

| Param  | Type | Req | Description |
|--------|------|-----|-------------|
| (none) |      |     |             |

Scope: `users:write` (NOT in this skill's manifest by default).

```bash
python3 scripts/slack.py call users.setActive
```

Returns: `{"ok":true}`.

Gotchas: deprecated by Slack but still functional. Prefer
`users.setPresence` with `auto`.

## users.setPresence

Set the user's presence to `auto` (Slack-managed) or `away`
(force-away).

| Param      | Type   | Req | Description           |
|------------|--------|-----|-----------------------|
| `presence` | string | yes | `auto` or `away`      |

Scope: `users:write` (NOT in this skill's manifest by default).

```bash
python3 scripts/slack.py call users.setPresence --params '{"presence":"away"}'
```

Returns: `{"ok":true}`.

## users.getPresence

Read presence for any user (or yourself).

| Param  | Type   | Req | Description                  |
|--------|--------|-----|------------------------------|
| `user` | string | no  | user ID; defaults to caller  |

Scope: `users:read`.

```bash
python3 scripts/slack.py call users.getPresence --params '{"user":"U07"}'
```

Returns:
```json
{"ok":true,"presence":"active","online":true,"auto_away":false,"manual_away":false,"connection_count":1,"last_activity":1714608000}
```

Gotchas: `presence` is `active` or `away`. `manual_away` distinguishes
"set to away" from "auto-away from idle". Slack throttles
`getPresence` aggressively — batch with `dnd.teamInfo` for many users
at once.

## Tip: from `<@U..>` mentions to display names

Use the CLI's `--resolve` flag to walk the response and expand
mention refs to readable names without extra round-trips:

```bash
python3 scripts/slack.py call conversations.history \
  --params '{"channel":"C0123","limit":20}' --resolve
```

The walker hits `users.info` and `conversations.info` on demand and
caches per-call.
