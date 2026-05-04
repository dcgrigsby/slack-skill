# Slack Web API Cheatsheet

Compact one-line-per-method map of the Slack Web API surface that's
useful with a User OAuth Token (`xoxp-...`). For full per-method
detail, see the per-namespace file (`Conversations.md`, `Chat.md`,
etc.). For methods not covered here, see `FULL-REFERENCE.md`.

Conventions:
- `param*` = required.
- `[paginated]` = uses `cursor` / `response_metadata.next_cursor`; pass `--all` to auto-loop.
- Scope columns reflect User Token Scopes.

## auth

- `auth.test`         Check token validity. Params: (none). Scope: (none).
- `auth.revoke`       Revoke the token. Params: (none). Scope: (none).

## conversations

- `conversations.list`         List channels / DMs. Params: types, exclude_archived. Scope: channels:read,groups:read,im:read,mpim:read. [paginated]
- `conversations.history`      Get messages in a channel/DM. Params: channel*, oldest, latest, inclusive, limit. Scope: channels:history (groups:/im:/mpim: variants). [paginated]
- `conversations.replies`      Get a thread (parent + replies). Params: channel*, ts*, oldest, latest. Scope: as conversations.history. [paginated]
- `conversations.info`         Channel / DM metadata. Params: channel*, include_locale, include_num_members. Scope: channels:read (groups:/im:/mpim:).
- `conversations.members`      List members of a channel. Params: channel*, limit. Scope: as conversations.info. [paginated]
- `conversations.mark`         Mark a channel read up to ts. Params: channel*, ts*. Scope: channels:write (or im:write etc).
- `conversations.open`         Open a DM (1:1 or group). Params: users (csv) OR channel. Scope: im:write,mpim:write.
- `conversations.close`        Close a DM. Params: channel*. Scope: im:write,mpim:write.
- `conversations.create`       Create a public/private channel. Params: name*, is_private, team_id. Scope: channels:write,groups:write.
- `conversations.archive`      Archive a channel. Params: channel*. Scope: channels:write,groups:write.
- `conversations.unarchive`    Unarchive a channel. Params: channel*. Scope: channels:write,groups:write.
- `conversations.invite`       Invite users to a channel. Params: channel*, users (csv)*. Scope: channels:write,groups:write.
- `conversations.kick`         Remove a user from a channel. Params: channel*, user*. Scope: channels:write,groups:write.
- `conversations.join`         Join a public channel. Params: channel*. Scope: channels:write.
- `conversations.leave`        Leave a channel. Params: channel*. Scope: channels:write,groups:write,im:write,mpim:write.
- `conversations.rename`       Rename a channel. Params: channel*, name*. Scope: channels:write,groups:write.
- `conversations.setPurpose`   Set channel purpose. Params: channel*, purpose*. Scope: channels:write,groups:write.
- `conversations.setTopic`     Set channel topic. Params: channel*, topic*. Scope: channels:write,groups:write.

## chat

- `chat.postMessage`     Send a message. Params: channel*, text or blocks*, thread_ts, reply_broadcast, mrkdwn, parse, link_names, unfurl_links, unfurl_media. Scope: chat:write.
- `chat.postEphemeral`   Post a message visible only to user. Params: channel*, user*, text or blocks*. Scope: chat:write.
- `chat.update`          Edit a message. Params: channel*, ts*, text or blocks*. Scope: chat:write.
- `chat.delete`          Delete a message. Params: channel*, ts*. Scope: chat:write.
- `chat.meMessage`       Post a /me message. Params: channel*, text*. Scope: chat:write.
- `chat.scheduleMessage` Schedule a future message. Params: channel*, post_at*, text or blocks*. Scope: chat:write.
- `chat.deleteScheduledMessage` Delete a scheduled message. Params: channel*, scheduled_message_id*. Scope: chat:write.
- `chat.scheduledMessages.list` List scheduled messages. Params: channel, latest, oldest. Scope: none. [paginated]
- `chat.getPermalink`    Get a permalink for a message. Params: channel*, message_ts*. Scope: (none).
- `chat.unfurl`          Provide custom unfurl content. Params: channel*, ts*, unfurls*. Scope: links:write.

## reactions

- `reactions.add`     Add a reaction. Params: name*, channel*, timestamp*. Scope: reactions:write.
- `reactions.remove`  Remove a reaction. Params: name*, channel*, timestamp*. Scope: reactions:write.
- `reactions.get`     List reactions on a single item. Params: channel, timestamp, file, file_comment, full. Scope: reactions:read.
- `reactions.list`    List items the user has reacted to. Params: user, full. Scope: reactions:read. [paginated]

## users

- `users.list`              List all users. Params: limit, include_locale. Scope: users:read. [paginated]
- `users.info`              User profile by ID. Params: user*, include_locale. Scope: users:read.
- `users.lookupByEmail`     User by email. Params: email*. Scope: users:read.email.
- `users.identity`          The token's user identity. Params: (none). Scope: identity.basic.
- `users.conversations`     Channels / DMs the token's user is in. Params: types, exclude_archived. Scope: channels:read,groups:read,im:read,mpim:read. [paginated]
- `users.profile.get`       User's profile fields. Params: user. Scope: users.profile:read.
- `users.profile.set`       Update the token's user profile. Params: name, value, profile (json). Scope: users.profile:write.
- `users.setActive`         Mark active. Params: (none). Scope: users:write.
- `users.setPresence`       Set auto/away. Params: presence*. Scope: users:write.
- `users.getPresence`       Get user presence. Params: user. Scope: users:read.

## search

- `search.messages`  Search messages across the workspace. Params: query*, count, page, sort, sort_dir. Scope: search:read. [paginated via page]
- `search.files`     Search files. Params: query*, count, page, sort, sort_dir. Scope: search:read. [paginated via page]
- `search.all`       Combined search. Params: query*, count, page. Scope: search:read. [paginated via page]

## files

- `files.list`     List files. Params: user, channel, ts_from, ts_to, types, count, page. Scope: files:read. [paginated via page]
- `files.info`     File metadata + comments. Params: file*, count, page. Scope: files:read. [paginated via page]
- `files.delete`   Delete a file. Params: file*. Scope: files:write.
- `slack.py upload`   Upload a file via the modern 3-call flow (getUploadURLExternal → POST multipart → completeUploadExternal). Args: --file, [--channel, --title, --initial-comment, --thread-ts, --alt-text]. Scope: files:write. (Deprecated single-call `files.upload` is not supported.)

## pins

- `pins.add`     Pin a message. Params: channel*, timestamp*. Scope: pins:write.
- `pins.remove`  Unpin a message. Params: channel*, timestamp*. Scope: pins:write.
- `pins.list`    List pins for a channel. Params: channel*. Scope: pins:read.

## stars

- `stars.add`     Star a message/file. Params: channel, timestamp, file, file_comment. Scope: stars:write.
- `stars.remove`  Unstar. Params: channel, timestamp, file, file_comment. Scope: stars:write.
- `stars.list`    List the user's stars. Params: count, page. Scope: stars:read. [paginated via page]

## bookmarks

- `bookmarks.add`     Add a channel bookmark. Params: channel_id*, title*, type*, link, emoji, entity_id, parent_id. Scope: bookmarks:write.
- `bookmarks.edit`    Edit a bookmark. Params: bookmark_id*, channel_id*, title, link, emoji. Scope: bookmarks:write.
- `bookmarks.remove`  Remove a bookmark. Params: bookmark_id*, channel_id*. Scope: bookmarks:write.
- `bookmarks.list`    List bookmarks for a channel. Params: channel_id*. Scope: bookmarks:read.

## team

- `team.info`             Workspace metadata. Params: team. Scope: team:read.
- `team.profile.get`      Custom profile field schema. Params: visibility. Scope: users.profile:read.
- `team.preferences.list` Workspace preferences. Params: (none). Scope: team:read.
- `team.billableInfo`     Billable users. Params: user. Scope: admin (rare).

## dnd

- `dnd.info`           User's DND status. Params: user. Scope: dnd:read.
- `dnd.teamInfo`       Team-wide DND. Params: users (csv). Scope: dnd:read.
- `dnd.setSnooze`      Snooze the user's DND. Params: num_minutes*. Scope: dnd:write.
- `dnd.endSnooze`      End snooze early. Params: (none). Scope: dnd:write.
- `dnd.endDnd`         End DND. Params: (none). Scope: dnd:write.

## reminders

- `reminders.add`       Create a reminder. Params: text*, time* (Unix or natural), user. Scope: reminders:write.
- `reminders.complete`  Mark complete. Params: reminder*. Scope: reminders:write.
- `reminders.delete`    Delete. Params: reminder*. Scope: reminders:write.
- `reminders.info`      Reminder by ID. Params: reminder*. Scope: reminders:read.
- `reminders.list`      All reminders. Params: (none). Scope: reminders:read.

## emoji

- `emoji.list`  List custom emoji. Params: (none). Scope: emoji:read.

For methods not in this cheatsheet (admin.*, calls.*, workflows.*,
canvas.*, etc.), see `FULL-REFERENCE.md`.
