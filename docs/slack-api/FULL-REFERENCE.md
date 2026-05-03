# Slack Web API — Full Reference

Generated from https://api.slack.com/specs/openapi/v2/slack_web.json.

Loaded only when CHEATSHEET.md and the per-namespace files don't cover what you need.

---

## admin.apps.approve

Approve an app for installation on a workspace.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.apps:write`
- `app_id` (formData): The id of the app to approve.
- `request_id` (formData): The id of the request to approve.
- `team_id` (formData): 

Tags: admin.apps, admin

---

## admin.apps.approved.list

List approved apps for an org or workspace.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.apps:read`
- `limit` (query): The maximum number of items to return. Must be between 1 - 1000 both inclusive.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page
- `team_id` (query): 
- `enterprise_id` (query): 

Tags: admin.apps.approved, admin

---

## admin.apps.requests.list

List app requests for a team/workspace.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.apps:read`
- `limit` (query): The maximum number of items to return. Must be between 1 - 1000 both inclusive.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page
- `team_id` (query): 

Tags: admin.apps.requests, admin

---

## admin.apps.restrict

Restrict an app for installation on a workspace.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.apps:write`
- `app_id` (formData): The id of the app to restrict.
- `request_id` (formData): The id of the request to restrict.
- `team_id` (formData): 

Tags: admin.apps, admin

---

## admin.apps.restricted.list

List restricted apps for an org or workspace.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.apps:read`
- `limit` (query): The maximum number of items to return. Must be between 1 - 1000 both inclusive.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page
- `team_id` (query): 
- `enterprise_id` (query): 

Tags: admin.apps.restricted, admin

---

## admin.conversations.archive

Archive a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The channel to archive.

Tags: admin.conversations, admin

---

## admin.conversations.convertToPrivate

Convert a public channel to a private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The channel to convert to private.

Tags: admin.conversations, admin

---

## admin.conversations.create

Create a public or private channel-based conversation.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `name` (formData) (required): Name of the public or private channel to create.
- `description` (formData): Description of the public or private channel to create.
- `is_private` (formData) (required): When `true`, creates a private channel instead of a public channel
- `org_wide` (formData): When `true`, the channel will be available org-wide. Note: if the channel is not `org_wide=true`, you must specify a `team_id` for this channel
- `team_id` (formData): The workspace to create the channel in. Note: this argument is required unless you set `org_wide=true`.

Tags: admin.conversations, admin

---

## admin.conversations.delete

Delete a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The channel to delete.

Tags: admin.conversations, admin

---

## admin.conversations.disconnectShared

Disconnect a connected channel from one or more workspaces.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The channel to be disconnected from some workspaces.
- `leaving_team_ids` (formData): The team to be removed from the channel. Currently only a single team id can be specified.

Tags: admin.conversations, admin

---

## admin.conversations.ekm.listOriginalConnectedChannelInfo

List all disconnected channels—i.e., channels that were once connected to other workspaces and then disconnected—and the corresponding original channel IDs for key revocation with EKM.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.conversations:read`
- `channel_ids` (query): A comma-separated list of channels to filter to.
- `team_ids` (query): A comma-separated list of the workspaces to which the channels you would like returned belong.
- `limit` (query): The maximum number of items to return. Must be between 1 - 1000 both inclusive.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page.

Tags: admin.conversations.ekm, admin

---

## admin.conversations.getConversationPrefs

Get conversation preferences for a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:read`
- `channel_id` (query) (required): The channel to get preferences for.

Tags: admin.conversations, admin

---

## admin.conversations.getTeams

Get all the workspaces a given public or private channel is connected to within this Enterprise org.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:read`
- `channel_id` (query) (required): The channel to determine connected workspaces within the organization for.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page
- `limit` (query): The maximum number of items to return. Must be between 1 - 1000 both inclusive.

Tags: admin.conversations, admin

---

## admin.conversations.invite

Invite a user to a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `user_ids` (formData) (required): The users to invite.
- `channel_id` (formData) (required): The channel that the users will be invited to.

Tags: admin.conversations, admin

---

## admin.conversations.rename

Rename a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The channel to rename.
- `name` (formData) (required): 

Tags: admin.conversations, admin

---

## admin.conversations.restrictAccess.addGroup

Add an allowlist of IDP groups for accessing a channel

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.conversations:write`
- `team_id` (formData): The workspace where the channel exists. This argument is required for channels only tied to one workspace, and optional for channels that are shared across an organization.
- `group_id` (formData) (required): The [IDP Group](https://slack.com/help/articles/115001435788-Connect-identity-provider-groups-to-your-Enterprise-Grid-org) ID to be an allowlist for the private channel.
- `channel_id` (formData) (required): The channel to link this group to.

Tags: admin.conversations.restrictAccess, admin

---

## admin.conversations.restrictAccess.listGroups

List all IDP Groups linked to a channel

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.conversations:read`
- `channel_id` (query) (required): 
- `team_id` (query): The workspace where the channel exists. This argument is required for channels only tied to one workspace, and optional for channels that are shared across an organization.

Tags: admin.conversations.restrictAccess, admin

---

## admin.conversations.restrictAccess.removeGroup

Remove a linked IDP group linked from a private channel

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.conversations:write`
- `team_id` (formData) (required): The workspace where the channel exists. This argument is required for channels only tied to one workspace, and optional for channels that are shared across an organization.
- `group_id` (formData) (required): The [IDP Group](https://slack.com/help/articles/115001435788-Connect-identity-provider-groups-to-your-Enterprise-Grid-org) ID to remove from the private channel.
- `channel_id` (formData) (required): The channel to remove the linked group from.

Tags: admin.conversations.restrictAccess, admin

---

## admin.conversations.search

Search for public or private channels in an Enterprise organization.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:read`
- `team_ids` (query): Comma separated string of team IDs, signifying the workspaces to search through.
- `query` (query): Name of the the channel to query by.
- `limit` (query): Maximum number of items to be returned. Must be between 1 - 20 both inclusive. Default is 10.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page.
- `search_channel_types` (query): The type of channel to include or exclude in the search. For example `private` will search private channels, while `private_exclude` will exclude them. For a full list of types, check the [Types section](#types).
- `sort` (query): Possible values are `relevant` (search ranking based on what we think is closest), `name` (alphabetical), `member_count` (number of users in the channel), and `created` (date channel was created). You can optionally pair this with the `sort_dir` arg to change how it is sorted
- `sort_dir` (query): Sort direction. Possible values are `asc` for ascending order like (1, 2, 3) or (a, b, c), and `desc` for descending order like (3, 2, 1) or (c, b, a)

Tags: admin.conversations, admin

---

## admin.conversations.setConversationPrefs

Set the posting permissions for a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The channel to set the prefs for
- `prefs` (formData) (required): The prefs for this channel in a stringified JSON format.

Tags: admin.conversations, admin

---

## admin.conversations.setTeams

Set the workspaces in an Enterprise grid org that connect to a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The encoded `channel_id` to add or remove to workspaces.
- `team_id` (formData): The workspace to which the channel belongs. Omit this argument if the channel is a cross-workspace shared channel.
- `target_team_ids` (formData): A comma-separated list of workspaces to which the channel should be shared. Not required if the channel is being shared org-wide.
- `org_channel` (formData): True if channel has to be converted to an org channel

Tags: admin.conversations, admin

---

## admin.conversations.unarchive

Unarchive a public or private channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.conversations:write`
- `channel_id` (formData) (required): The channel to unarchive.

Tags: admin.conversations, admin

---

## admin.emoji.add

Add an emoji.

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.teams:write`
- `name` (formData) (required): The name of the emoji to be removed. Colons (`:myemoji:`) around the value are not required, although they may be included.
- `url` (formData) (required): The URL of a file to use as an image for the emoji. Square images under 128KB and with transparent backgrounds work best.

Tags: admin.emoji, admin

---

## admin.emoji.addAlias

Add an emoji alias.

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.teams:write`
- `name` (formData) (required): The name of the emoji to be aliased. Colons (`:myemoji:`) around the value are not required, although they may be included.
- `alias_for` (formData) (required): The alias of the emoji.

Tags: admin.emoji, admin

---

## admin.emoji.list

List emoji for an Enterprise Grid organization.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.teams:read`
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page
- `limit` (query): The maximum number of items to return. Must be between 1 - 1000 both inclusive.

Tags: admin.emoji, admin

---

## admin.emoji.remove

Remove an emoji across an Enterprise Grid organization

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.teams:write`
- `name` (formData) (required): The name of the emoji to be removed. Colons (`:myemoji:`) around the value are not required, although they may be included.

Tags: admin.emoji, admin

---

## admin.emoji.rename

Rename an emoji.

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.teams:write`
- `name` (formData) (required): The name of the emoji to be renamed. Colons (`:myemoji:`) around the value are not required, although they may be included.
- `new_name` (formData) (required): The new name of the emoji.

Tags: admin.emoji, admin

---

## admin.inviteRequests.approve

Approve a workspace invite request.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.invites:write`
- `team_id` (formData): ID for the workspace where the invite request was made.
- `invite_request_id` (formData) (required): ID of the request to invite.

Tags: admin.inviteRequests, admin

---

## admin.inviteRequests.approved.list

List all approved workspace invite requests.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.invites:read`
- `team_id` (query): ID for the workspace where the invite requests were made.
- `cursor` (query): Value of the `next_cursor` field sent as part of the previous API response
- `limit` (query): The number of results that will be returned by the API on each invocation. Must be between 1 - 1000, both inclusive

Tags: admin.inviteRequests.approved, admin

---

## admin.inviteRequests.denied.list

List all denied workspace invite requests.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.invites:read`
- `team_id` (query): ID for the workspace where the invite requests were made.
- `cursor` (query): Value of the `next_cursor` field sent as part of the previous api response
- `limit` (query): The number of results that will be returned by the API on each invocation. Must be between 1 - 1000 both inclusive

Tags: admin.inviteRequests.denied, admin

---

## admin.inviteRequests.deny

Deny a workspace invite request.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.invites:write`
- `team_id` (formData): ID for the workspace where the invite request was made.
- `invite_request_id` (formData) (required): ID of the request to invite.

Tags: admin.inviteRequests, admin

---

## admin.inviteRequests.list

List all pending workspace invite requests.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.invites:read`
- `team_id` (query): ID for the workspace where the invite requests were made.
- `cursor` (query): Value of the `next_cursor` field sent as part of the previous API response
- `limit` (query): The number of results that will be returned by the API on each invocation. Must be between 1 - 1000, both inclusive

Tags: admin.inviteRequests, admin

---

## admin.teams.admins.list

List all of the admins on a given workspace.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.teams:read`
- `limit` (query): The maximum number of items to return.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page.
- `team_id` (query) (required): 

Tags: admin.teams.admins, admin

---

## admin.teams.create

Create an Enterprise team.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.teams:write`
- `team_domain` (formData) (required): Team domain (for example, slacksoftballteam).
- `team_name` (formData) (required): Team name (for example, Slack Softball Team).
- `team_description` (formData): Description for the team.
- `team_discoverability` (formData): Who can join the team. A team's discoverability can be `open`, `closed`, `invite_only`, or `unlisted`.

Tags: admin.teams, admin

---

## admin.teams.list

List all teams on an Enterprise organization

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.teams:read`
- `limit` (query): The maximum number of items to return. Must be between 1 - 100 both inclusive.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page.

Tags: admin.teams, admin

---

## admin.teams.owners.list

List all of the owners on a given workspace.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin.teams:read`
- `team_id` (query) (required): 
- `limit` (query): The maximum number of items to return. Must be between 1 - 1000 both inclusive.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page.

Tags: admin.teams.owners, admin

---

## admin.teams.settings.info

Fetch information about settings in a workspace

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.teams:read`
- `team_id` (query) (required): 

Tags: admin.teams.settings, admin

---

## admin.teams.settings.setDefaultChannels

Set the default channels of a workspace.

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.teams:write`
- `team_id` (formData) (required): ID for the workspace to set the default channel for.
- `channel_ids` (formData) (required): An array of channel IDs.

Tags: admin.teams.settings, admin

---

## admin.teams.settings.setDescription

Set the description of a given workspace.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.teams:write`
- `team_id` (formData) (required): ID for the workspace to set the description for.
- `description` (formData) (required): The new description for the workspace.

Tags: admin.teams.settings, admin

---

## admin.teams.settings.setDiscoverability

An API method that allows admins to set the discoverability of a given workspace

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.teams:write`
- `team_id` (formData) (required): The ID of the workspace to set discoverability on.
- `discoverability` (formData) (required): This workspace's discovery setting. It must be set to one of `open`, `invite_only`, `closed`, or `unlisted`.

Tags: admin.teams.settings, admin

---

## admin.teams.settings.setIcon

Sets the icon of a workspace.

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `admin.teams:write`
- `image_url` (formData) (required): Image URL for the icon
- `team_id` (formData) (required): ID for the workspace to set the icon for.

Tags: admin.teams.settings, admin

---

## admin.teams.settings.setName

Set the name of a given workspace.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.teams:write`
- `team_id` (formData) (required): ID for the workspace to set the name for.
- `name` (formData) (required): The new name of the workspace.

Tags: admin.teams.settings, admin

---

## admin.usergroups.addChannels

Add one or more default channels to an IDP group.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.usergroups:write`
- `usergroup_id` (formData) (required): ID of the IDP group to add default channels for.
- `team_id` (formData): The workspace to add default channels in.
- `channel_ids` (formData) (required): Comma separated string of channel IDs.

Tags: admin.usergroups, admin

---

## admin.usergroups.addTeams

Associate one or more default workspaces with an organization-wide IDP group.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.teams:write`
- `usergroup_id` (formData) (required): An encoded usergroup (IDP Group) ID.
- `team_ids` (formData) (required): A comma separated list of encoded team (workspace) IDs. Each workspace *MUST* belong to the organization associated with the token.
- `auto_provision` (formData): When `true`, this method automatically creates new workspace accounts for the IDP group members.

Tags: admin.usergroups, admin

---

## admin.usergroups.listChannels

List the channels linked to an org-level IDP group (user group).

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.usergroups:read`
- `usergroup_id` (query) (required): ID of the IDP group to list default channels for.
- `team_id` (query): ID of the the workspace.
- `include_num_members` (query): Flag to include or exclude the count of members per channel.

Tags: admin.usergroups, admin

---

## admin.usergroups.removeChannels

Remove one or more default channels from an org-level IDP group (user group).

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.usergroups:write`
- `usergroup_id` (formData) (required): ID of the IDP Group
- `channel_ids` (formData) (required): Comma-separated string of channel IDs

Tags: admin.usergroups, admin

---

## admin.users.assign

Add an Enterprise user to a workspace.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): The ID (`T1234`) of the workspace.
- `user_id` (formData) (required): The ID of the user to add to the workspace.
- `is_restricted` (formData): True if user should be added to the workspace as a guest.
- `is_ultra_restricted` (formData): True if user should be added to the workspace as a single-channel guest.
- `channel_ids` (formData): Comma separated values of channel IDs to add user in the new workspace.

Tags: admin.users, admin

---

## admin.users.invite

Invite a user to a workspace.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): The ID (`T1234`) of the workspace.
- `email` (formData) (required): The email address of the person to invite.
- `channel_ids` (formData) (required): A comma-separated list of `channel_id`s for this user to join. At least one channel is required.
- `custom_message` (formData): An optional message to send to the user in the invite email.
- `real_name` (formData): Full name of the user.
- `resend` (formData): Allow this invite to be resent in the future if a user has not signed up yet. (default: false)
- `is_restricted` (formData): Is this user a multi-channel guest user? (default: false)
- `is_ultra_restricted` (formData): Is this user a single channel guest user? (default: false)
- `guest_expiration_ts` (formData): Timestamp when guest account should be disabled. Only include this timestamp if you are inviting a guest user and you want their account to expire on a certain date.

Tags: admin.users, admin

---

## admin.users.list

List users on a workspace

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:read`
- `team_id` (query) (required): The ID (`T1234`) of the workspace.
- `cursor` (query): Set `cursor` to `next_cursor` returned by the previous call to list items in the next page.
- `limit` (query): Limit for how many users to be retrieved per page

Tags: admin.users, admin

---

## admin.users.remove

Remove a user from a workspace.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): The ID (`T1234`) of the workspace.
- `user_id` (formData) (required): The ID of the user to remove.

Tags: admin.users, admin

---

## admin.users.session.invalidate

Invalidate a single session for a user by session_id

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): ID of the team that the session belongs to
- `session_id` (formData) (required): 

Tags: admin.users.session, admin

---

## admin.users.session.reset

Wipes all valid sessions on all devices for a given user

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `user_id` (formData) (required): The ID of the user to wipe sessions for
- `mobile_only` (formData): Only expire mobile sessions (default: false)
- `web_only` (formData): Only expire web sessions (default: false)

Tags: admin.users.session, admin

---

## admin.users.setAdmin

Set an existing guest, regular user, or owner to be an admin user.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): The ID (`T1234`) of the workspace.
- `user_id` (formData) (required): The ID of the user to designate as an admin.

Tags: admin.users, admin

---

## admin.users.setExpiration

Set an expiration for a guest user

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): The ID (`T1234`) of the workspace.
- `user_id` (formData) (required): The ID of the user to set an expiration for.
- `expiration_ts` (formData) (required): Timestamp when guest account should be disabled.

Tags: admin.users, admin

---

## admin.users.setOwner

Set an existing guest, regular user, or admin user to be a workspace owner.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): The ID (`T1234`) of the workspace.
- `user_id` (formData) (required): Id of the user to promote to owner.

Tags: admin.users, admin

---

## admin.users.setRegular

Set an existing guest user, admin user, or owner to be a regular user.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `admin.users:write`
- `team_id` (formData) (required): The ID (`T1234`) of the workspace.
- `user_id` (formData) (required): The ID of the user to designate as a regular user.

Tags: admin.users, admin

---

## api.test

Checks API calling code.

**Parameters:**

- `error` (query): Error response to return
- `foo` (query): example property to return

Tags: api

---

## apps.event.authorizations.list

Get a list of authorizations for the given event context. Each authorization represents an app installation that the event is visible to.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `authorizations:read`
- `event_context` (query) (required): 
- `cursor` (query): 
- `limit` (query): 

Tags: apps.event.authorizations, apps

---

## apps.permissions.info

Returns list of permissions this app has on a team.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `none`

Tags: apps.permissions, apps

---

## apps.permissions.request

Allows an app to request additional scopes

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `none`
- `scopes` (query) (required): A comma separated list of scopes to request for
- `trigger_id` (query) (required): Token used to trigger the permissions API

Tags: apps.permissions, apps

---

## apps.permissions.resources.list

Returns list of resource grants this app has on a team.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `none`
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.
- `limit` (query): The maximum number of items to return.

Tags: apps.permissions.resources, apps

---

## apps.permissions.scopes.list

Returns list of scopes this app has on a team.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `none`

Tags: apps.permissions.scopes, apps

---

## apps.uninstall

Uninstalls your app from a workspace.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `none`
- `client_id` (query): Issued when you created your application.
- `client_secret` (query): Issued when you created your application.

Tags: apps

---

## auth.revoke

Revokes a token.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `none`
- `test` (query): Setting this parameter to `1` triggers a _testing mode_ where the specified token will not actually be revoked.

Tags: auth

---

## auth.test

Checks authentication & identity.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `none`

Tags: auth

---

## bots.info

Gets information about a bot user.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `users:read`
- `bot` (query): Bot user to get info on

Tags: bots

---

## calls.add

Registers a new Call.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `calls:write`
- `external_unique_id` (formData) (required): An ID supplied by the 3rd-party Call provider. It must be unique across all Calls from that service.
- `external_display_id` (formData): An optional, human-readable ID supplied by the 3rd-party Call provider. If supplied, this ID will be displayed in the Call object.
- `join_url` (formData) (required): The URL required for a client to join the Call.
- `desktop_app_join_url` (formData): When supplied, available Slack clients will attempt to directly launch the 3rd-party Call with this URL.
- `date_start` (formData): Call start time in UTC UNIX timestamp format
- `title` (formData): The name of the Call.
- `created_by` (formData): The valid Slack user ID of the user who created this Call. When this method is called with a user token, the `created_by` field is optional and defaults to the authed user of the token. Otherwise, the field is required.
- `users` (formData): The list of users to register as participants in the Call. [Read more on how to specify users here](/apis/calls#users).

Tags: calls

---

## calls.end

Ends a Call.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `calls:write`
- `id` (formData) (required): `id` returned when registering the call using the [`calls.add`](/methods/calls.add) method.
- `duration` (formData): Call duration in seconds

Tags: calls

---

## calls.info

Returns information about a Call.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `calls:read`
- `id` (query) (required): `id` of the Call returned by the [`calls.add`](/methods/calls.add) method.

Tags: calls

---

## calls.participants.add

Registers new participants added to a Call.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `calls:write`
- `id` (formData) (required): `id` returned by the [`calls.add`](/methods/calls.add) method.
- `users` (formData) (required): The list of users to add as participants in the Call. [Read more on how to specify users here](/apis/calls#users).

Tags: calls.participants, calls

---

## calls.participants.remove

Registers participants removed from a Call.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `calls:write`
- `id` (formData) (required): `id` returned by the [`calls.add`](/methods/calls.add) method.
- `users` (formData) (required): The list of users to remove as participants in the Call. [Read more on how to specify users here](/apis/calls#users).

Tags: calls.participants, calls

---

## calls.update

Updates information about a Call.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `calls:write`
- `id` (formData) (required): `id` returned by the [`calls.add`](/methods/calls.add) method.
- `title` (formData): The name of the Call.
- `join_url` (formData): The URL required for a client to join the Call.
- `desktop_app_join_url` (formData): When supplied, available Slack clients will attempt to directly launch the 3rd-party Call with this URL.

Tags: calls

---

## chat.delete

Deletes a message.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `chat:write`
- `ts` (formData): Timestamp of the message to be deleted.
- `channel` (formData): Channel containing the message to be deleted.
- `as_user` (formData): Pass true to delete the message as the authed user with `chat:write:user` scope. [Bot users](/bot-users) in this context are considered authed users. If unused or false, the message will be deleted with `chat:write:bot` scope.

Tags: chat

---

## chat.deleteScheduledMessage

Deletes a pending scheduled message from the queue.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `chat:write`
- `as_user` (formData): Pass true to delete the message as the authed user with `chat:write:user` scope. [Bot users](/bot-users) in this context are considered authed users. If unused or false, the message will be deleted with `chat:write:bot` scope.
- `channel` (formData) (required): The channel the scheduled_message is posting to
- `scheduled_message_id` (formData) (required): `scheduled_message_id` returned from call to chat.scheduleMessage

Tags: chat

---

## chat.getPermalink

Retrieve a permalink URL for a specific extant message

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `none`
- `channel` (query) (required): The ID of the conversation or channel containing the message
- `message_ts` (query) (required): A message's `ts` value, uniquely identifying it within a channel

Tags: chat

---

## chat.meMessage

Share a me message into a channel.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `chat:write`
- `channel` (formData): Channel to send message to. Can be a public channel, private group or IM channel. Can be an encoded ID, or a name.
- `text` (formData): Text of the message to send.

Tags: chat

---

## chat.postEphemeral

Sends an ephemeral message to a user in a channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `chat:write`
- `as_user` (formData): Pass true to post the message as the authed user. Defaults to true if the chat:write:bot scope is not included. Otherwise, defaults to false.
- `attachments` (formData): A JSON-based array of structured attachments, presented as a URL-encoded string.
- `blocks` (formData): A JSON-based array of structured blocks, presented as a URL-encoded string.
- `channel` (formData) (required): Channel, private group, or IM channel to send message to. Can be an encoded ID, or a name.
- `icon_emoji` (formData): Emoji to use as the icon for this message. Overrides `icon_url`. Must be used in conjunction with `as_user` set to `false`, otherwise ignored. See [authorship](#authorship) below.
- `icon_url` (formData): URL to an image to use as the icon for this message. Must be used in conjunction with `as_user` set to false, otherwise ignored. See [authorship](#authorship) below.
- `link_names` (formData): Find and link channel names and usernames.
- `parse` (formData): Change how messages are treated. Defaults to `none`. See [below](#formatting).
- `text` (formData): How this field works and whether it is required depends on other fields you use in your API call. [See below](#text_usage) for more detail.
- `thread_ts` (formData): Provide another message's `ts` value to post this message in a thread. Avoid using a reply's `ts` value; use its parent's value instead. Ephemeral messages in threads are only shown if there is already an active thread.
- `user` (formData) (required): `id` of the user who will receive the ephemeral message. The user should be in the channel specified by the `channel` argument.
- `username` (formData): Set your bot's user name. Must be used in conjunction with `as_user` set to false, otherwise ignored. See [authorship](#authorship) below.

Tags: chat

---

## chat.postMessage

Sends a message to a channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `chat:write`
- `as_user` (formData): Pass true to post the message as the authed user, instead of as a bot. Defaults to false. See [authorship](#authorship) below.
- `attachments` (formData): A JSON-based array of structured attachments, presented as a URL-encoded string.
- `blocks` (formData): A JSON-based array of structured blocks, presented as a URL-encoded string.
- `channel` (formData) (required): Channel, private group, or IM channel to send message to. Can be an encoded ID, or a name. See [below](#channels) for more details.
- `icon_emoji` (formData): Emoji to use as the icon for this message. Overrides `icon_url`. Must be used in conjunction with `as_user` set to `false`, otherwise ignored. See [authorship](#authorship) below.
- `icon_url` (formData): URL to an image to use as the icon for this message. Must be used in conjunction with `as_user` set to false, otherwise ignored. See [authorship](#authorship) below.
- `link_names` (formData): Find and link channel names and usernames.
- `mrkdwn` (formData): Disable Slack markup parsing by setting to `false`. Enabled by default.
- `parse` (formData): Change how messages are treated. Defaults to `none`. See [below](#formatting).
- `reply_broadcast` (formData): Used in conjunction with `thread_ts` and indicates whether reply should be made visible to everyone in the channel or conversation. Defaults to `false`.
- `text` (formData): How this field works and whether it is required depends on other fields you use in your API call. [See below](#text_usage) for more detail.
- `thread_ts` (formData): Provide another message's `ts` value to make this message a reply. Avoid using a reply's `ts` value; use its parent instead.
- `unfurl_links` (formData): Pass true to enable unfurling of primarily text-based content.
- `unfurl_media` (formData): Pass false to disable unfurling of media content.
- `username` (formData): Set your bot's user name. Must be used in conjunction with `as_user` set to false, otherwise ignored. See [authorship](#authorship) below.

Tags: chat

---

## chat.scheduleMessage

Schedules a message to be sent to a channel.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `chat:write`
- `channel` (formData): Channel, private group, or DM channel to send message to. Can be an encoded ID, or a name. See [below](#channels) for more details.
- `text` (formData): How this field works and whether it is required depends on other fields you use in your API call. [See below](#text_usage) for more detail.
- `post_at` (formData): Unix EPOCH timestamp of time in future to send the message.
- `parse` (formData): Change how messages are treated. Defaults to `none`. See [chat.postMessage](chat.postMessage#formatting).
- `as_user` (formData): Pass true to post the message as the authed user, instead of as a bot. Defaults to false. See [chat.postMessage](chat.postMessage#authorship).
- `link_names` (formData): Find and link channel names and usernames.
- `attachments` (formData): A JSON-based array of structured attachments, presented as a URL-encoded string.
- `blocks` (formData): A JSON-based array of structured blocks, presented as a URL-encoded string.
- `unfurl_links` (formData): Pass true to enable unfurling of primarily text-based content.
- `unfurl_media` (formData): Pass false to disable unfurling of media content.
- `thread_ts` (formData): Provide another message's `ts` value to make this message a reply. Avoid using a reply's `ts` value; use its parent instead.
- `reply_broadcast` (formData): Used in conjunction with `thread_ts` and indicates whether reply should be made visible to everyone in the channel or conversation. Defaults to `false`.

Tags: chat

---

## chat.scheduledMessages.list

Returns a list of scheduled messages.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `none`
- `channel` (query): The channel of the scheduled messages
- `latest` (query): A UNIX timestamp of the latest value in the time range
- `oldest` (query): A UNIX timestamp of the oldest value in the time range
- `limit` (query): Maximum number of original entries to return.
- `cursor` (query): For pagination purposes, this is the `cursor` value returned from a previous call to `chat.scheduledmessages.list` indicating where you want to start this call from.

Tags: chat.scheduledMessages, chat

---

## chat.unfurl

Provide custom unfurl behavior for user-posted URLs

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `links:write`
- `channel` (formData) (required): Channel ID of the message
- `ts` (formData) (required): Timestamp of the message to add unfurl behavior to.
- `unfurls` (formData): URL-encoded JSON map with keys set to URLs featured in the the message, pointing to their unfurl blocks or message attachments.
- `user_auth_message` (formData): Provide a simply-formatted string to send as an ephemeral message to the user as invitation to authenticate further and enable full unfurling behavior
- `user_auth_required` (formData): Set to `true` or `1` to indicate the user must install your Slack app to trigger unfurls for this domain
- `user_auth_url` (formData): Send users to this custom URL where they will complete authentication in your app to fully trigger unfurling. Value should be properly URL-encoded.

Tags: chat

---

## chat.update

Updates a message.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `chat:write`
- `as_user` (formData): Pass true to update the message as the authed user. [Bot users](/bot-users) in this context are considered authed users.
- `attachments` (formData): A JSON-based array of structured attachments, presented as a URL-encoded string. This field is required when not presenting `text`. If you don't include this field, the message's previous `attachments` will be retained. To remove previous `attachments`, include an empty array for this field.
- `blocks` (formData): A JSON-based array of [structured blocks](/block-kit/building), presented as a URL-encoded string. If you don't include this field, the message's previous `blocks` will be retained. To remove previous `blocks`, include an empty array for this field.
- `channel` (formData) (required): Channel containing the message to be updated.
- `link_names` (formData): Find and link channel names and usernames. Defaults to `none`. If you do not specify a value for this field, the original value set for the message will be overwritten with the default, `none`.
- `parse` (formData): Change how messages are treated. Defaults to `client`, unlike `chat.postMessage`. Accepts either `none` or `full`. If you do not specify a value for this field, the original value set for the message will be overwritten with the default, `client`.
- `text` (formData): New text for the message, using the [default formatting rules](/reference/surfaces/formatting). It's not required when presenting `blocks` or `attachments`.
- `ts` (formData) (required): Timestamp of the message to be updated.

Tags: chat

---

## conversations.archive

Archives a conversation.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): ID of conversation to archive

Tags: conversations

---

## conversations.close

Closes a direct message or multi-person direct message.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): Conversation to close.

Tags: conversations

---

## conversations.create

Initiates a public or private channel-based conversation

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `name` (formData): Name of the public or private channel to create
- `is_private` (formData): Create a private channel instead of a public one

Tags: conversations

---

## conversations.history

Fetches a conversation's history of messages and events.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `conversations:history`
- `channel` (query): Conversation ID to fetch history for.
- `latest` (query): End of time range of messages to include in results.
- `oldest` (query): Start of time range of messages to include in results.
- `inclusive` (query): Include messages with latest or oldest timestamp in results only when either timestamp is specified.
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the users list hasn't been reached.
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.

Tags: conversations

---

## conversations.info

Retrieve information about a conversation.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `conversations:read`
- `channel` (query): Conversation ID to learn more about
- `include_locale` (query): Set this to `true` to receive the locale for this conversation. Defaults to `false`
- `include_num_members` (query): Set to `true` to include the member count for the specified conversation. Defaults to `false`

Tags: conversations

---

## conversations.invite

Invites users to a channel.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): The ID of the public or private channel to invite user(s) to.
- `users` (formData): A comma separated list of user IDs. Up to 1000 users may be listed.

Tags: conversations

---

## conversations.join

Joins an existing conversation.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `channels:write`
- `channel` (formData): ID of conversation to join

Tags: conversations

---

## conversations.kick

Removes a user from a conversation.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): ID of conversation to remove user from.
- `user` (formData): User ID to be removed.

Tags: conversations

---

## conversations.leave

Leaves a conversation.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): Conversation to leave

Tags: conversations

---

## conversations.list

Lists all channels in a Slack team.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `conversations:read`
- `exclude_archived` (query): Set to `true` to exclude archived channels from the list
- `types` (query): Mix and match channel types by providing a comma-separated list of any combination of `public_channel`, `private_channel`, `mpim`, `im`
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the list hasn't been reached. Must be an integer no larger than 1000.
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.

Tags: conversations

---

## conversations.mark

Sets the read cursor in a channel.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): Channel or conversation to set the read cursor for.
- `ts` (formData): Unique identifier of message you want marked as most recently seen in this conversation.

Tags: conversations

---

## conversations.members

Retrieve members of a conversation.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `conversations:read`
- `channel` (query): ID of the conversation to retrieve members for
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the users list hasn't been reached.
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.

Tags: conversations

---

## conversations.open

Opens or resumes a direct message or multi-person direct message.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): Resume a conversation by supplying an `im` or `mpim`'s ID. Or provide the `users` field instead.
- `users` (formData): Comma separated lists of users. If only one user is included, this creates a 1:1 DM.  The ordering of the users is preserved whenever a multi-person direct message is returned. Supply a `channel` when not supplying `users`.
- `return_im` (formData): Boolean, indicates you want the full IM channel definition in the response.

Tags: conversations

---

## conversations.rename

Renames a conversation.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): ID of conversation to rename
- `name` (formData): New name for conversation.

Tags: conversations

---

## conversations.replies

Retrieve a thread of messages posted to a conversation

**Parameters:**

- `token` (query): Authentication token. Requires scope: `conversations:history`
- `channel` (query): Conversation ID to fetch thread from.
- `ts` (query): Unique identifier of a thread's parent message. `ts` must be the timestamp of an existing message with 0 or more replies. If there are no replies then just the single message referenced by `ts` will return - it is just an ordinary, unthreaded message.
- `latest` (query): End of time range of messages to include in results.
- `oldest` (query): Start of time range of messages to include in results.
- `inclusive` (query): Include messages with latest or oldest timestamp in results only when either timestamp is specified.
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the users list hasn't been reached.
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.

Tags: conversations

---

## conversations.setPurpose

Sets the purpose for a conversation.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): Conversation to set the purpose of
- `purpose` (formData): A new, specialer purpose

Tags: conversations

---

## conversations.setTopic

Sets the topic for a conversation.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): Conversation to set the topic of
- `topic` (formData): The new topic string. Does not support formatting or linkification.

Tags: conversations

---

## conversations.unarchive

Reverses conversation archival.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `conversations:write`
- `channel` (formData): ID of conversation to unarchive

Tags: conversations

---

## dialog.open

Open a dialog with a user

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `none`
- `dialog` (query) (required): The dialog definition. This must be a JSON-encoded string.
- `trigger_id` (query) (required): Exchange a trigger to post to the user.

Tags: dialog

---

## dnd.endDnd

Ends the current user's Do Not Disturb session immediately.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `dnd:write`

Tags: dnd

---

## dnd.endSnooze

Ends the current user's snooze mode immediately.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `dnd:write`

Tags: dnd

---

## dnd.info

Retrieves a user's current Do Not Disturb status.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `dnd:read`
- `user` (query): User to fetch status for (defaults to current user)

Tags: dnd

---

## dnd.setSnooze

Turns on Do Not Disturb mode for the current user, or changes its duration.

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `dnd:write`
- `num_minutes` (formData) (required): Number of minutes, from now, to snooze until.

Tags: dnd

---

## dnd.teamInfo

Retrieves the Do Not Disturb status for up to 50 users on a team.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `dnd:read`
- `users` (query): Comma-separated list of users to fetch Do Not Disturb status for

Tags: dnd

---

## emoji.list

Lists custom emoji for a team.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `emoji:read`

Tags: emoji

---

## files.comments.delete

Deletes an existing comment on a file.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `files:write:user`
- `file` (formData): File to delete a comment from.
- `id` (formData): The comment to delete.

Tags: files.comments, files

---

## files.delete

Deletes a file.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `files:write:user`
- `file` (formData): ID of file to delete.

Tags: files

---

## files.info

Gets information about a file.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `files:read`
- `file` (query): Specify a file by providing its ID.
- `count` (query): 
- `page` (query): 
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the list hasn't been reached.
- `cursor` (query): Parameter for pagination. File comments are paginated for a single file. Set `cursor` equal to the `next_cursor` attribute returned by the previous request's `response_metadata`. This parameter is optional, but pagination is mandatory: the default value simply fetches the first "page" of the collection of comments. See [pagination](/docs/pagination) for more details.

Tags: files

---

## files.list

List for a team, in a channel, or from a user with applied filters.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `files:read`
- `user` (query): Filter files created by a single user.
- `channel` (query): Filter files appearing in a specific channel, indicated by its ID.
- `ts_from` (query): Filter files created after this timestamp (inclusive).
- `ts_to` (query): Filter files created before this timestamp (inclusive).
- `types` (query): Filter files by type ([see below](#file_types)). You can pass multiple values in the types argument, like `types=spaces,snippets`.The default value is `all`, which does not filter the list.
- `count` (query): 
- `page` (query): 
- `show_files_hidden_by_limit` (query): Show truncated file info for files hidden due to being too old, and the team who owns the file being over the file limit.

Tags: files

---

## files.remote.add

Adds a file from a remote service

**Parameters:**

- `token` (formData): Authentication token. Requires scope: `remote_files:write`
- `external_id` (formData): Creator defined GUID for the file.
- `title` (formData): Title of the file being shared.
- `filetype` (formData): type of file
- `external_url` (formData): URL of the remote file.
- `preview_image` (formData): Preview of the document via `multipart/form-data`.
- `indexable_file_contents` (formData): A text file (txt, pdf, doc, etc.) containing textual search terms that are used to improve discovery of the remote file.

Tags: files.remote, files

---

## files.remote.info

Retrieve information about a remote file added to Slack

**Parameters:**

- `token` (query): Authentication token. Requires scope: `remote_files:read`
- `file` (query): Specify a file by providing its ID.
- `external_id` (query): Creator defined GUID for the file.

Tags: files.remote, files

---

## files.remote.list

Retrieve information about a remote file added to Slack

**Parameters:**

- `token` (query): Authentication token. Requires scope: `remote_files:read`
- `channel` (query): Filter files appearing in a specific channel, indicated by its ID.
- `ts_from` (query): Filter files created after this timestamp (inclusive).
- `ts_to` (query): Filter files created before this timestamp (inclusive).
- `limit` (query): The maximum number of items to return.
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.

Tags: files.remote, files

---

## files.remote.remove

Remove a remote file.

**Parameters:**

- `token` (formData): Authentication token. Requires scope: `remote_files:write`
- `file` (formData): Specify a file by providing its ID.
- `external_id` (formData): Creator defined GUID for the file.

Tags: files.remote, files

---

## files.remote.share

Share a remote file into a channel.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `remote_files:share`
- `file` (query): Specify a file registered with Slack by providing its ID. Either this field or `external_id` or both are required.
- `external_id` (query): The globally unique identifier (GUID) for the file, as set by the app registering the file with Slack.  Either this field or `file` or both are required.
- `channels` (query): Comma-separated list of channel IDs where the file will be shared.

Tags: files.remote, files

---

## files.remote.update

Updates an existing remote file.

**Parameters:**

- `token` (formData): Authentication token. Requires scope: `remote_files:write`
- `file` (formData): Specify a file by providing its ID.
- `external_id` (formData): Creator defined GUID for the file.
- `title` (formData): Title of the file being shared.
- `filetype` (formData): type of file
- `external_url` (formData): URL of the remote file.
- `preview_image` (formData): Preview of the document via `multipart/form-data`.
- `indexable_file_contents` (formData): File containing contents that can be used to improve searchability for the remote file.

Tags: files.remote, files

---

## files.revokePublicURL

Revokes public/external sharing access for a file

**Parameters:**

- `token` (header): Authentication token. Requires scope: `files:write:user`
- `file` (formData): File to revoke

Tags: files

---

## files.sharedPublicURL

Enables a file for public/external sharing.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `files:write:user`
- `file` (formData): File to share

Tags: files

---

## files.upload

Uploads or creates a file.

**Parameters:**

- `token` (formData): Authentication token. Requires scope: `files:write:user`
- `file` (formData): File contents via `multipart/form-data`. If omitting this parameter, you must submit `content`.
- `content` (formData): File contents via a POST variable. If omitting this parameter, you must provide a `file`.
- `filetype` (formData): A [file type](/types/file#file_types) identifier.
- `filename` (formData): Filename of file.
- `title` (formData): Title of file.
- `initial_comment` (formData): The message text introducing the file in specified `channels`.
- `channels` (formData): Comma-separated list of channel names or IDs where the file will be shared.
- `thread_ts` (formData): Provide another message's `ts` value to upload this file as a reply. Never use a reply's `ts` value; use its parent instead.

Tags: files

---

## migration.exchange

For Enterprise Grid workspaces, map local user IDs to global user IDs

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `tokens.basic`
- `users` (query) (required): A comma-separated list of user ids, up to 400 per request
- `team_id` (query): Specify team_id starts with `T` in case of Org Token
- `to_old` (query): Specify `true` to convert `W` global user IDs to workspace-specific `U` IDs. Defaults to `false`.

Tags: migration

---

## oauth.access

Exchanges a temporary OAuth verifier code for an access token.

**Parameters:**

- `client_id` (query): Issued when you created your application.
- `client_secret` (query): Issued when you created your application.
- `code` (query): The `code` param returned via the OAuth callback.
- `redirect_uri` (query): This must match the originally submitted URI (if one was sent).
- `single_channel` (query): Request the user to add your app only to a single channel. Only valid with a [legacy workspace app](https://api.slack.com/legacy-workspace-apps).

Tags: oauth

---

## oauth.token

Exchanges a temporary OAuth verifier code for a workspace token.

**Parameters:**

- `client_id` (query): Issued when you created your application.
- `client_secret` (query): Issued when you created your application.
- `code` (query): The `code` param returned via the OAuth callback.
- `redirect_uri` (query): This must match the originally submitted URI (if one was sent).
- `single_channel` (query): Request the user to add your app only to a single channel.

Tags: oauth

---

## oauth.v2.access

Exchanges a temporary OAuth verifier code for an access token.

**Parameters:**

- `client_id` (query): Issued when you created your application.
- `client_secret` (query): Issued when you created your application.
- `code` (query) (required): The `code` param returned via the OAuth callback.
- `redirect_uri` (query): This must match the originally submitted URI (if one was sent).

Tags: oauth.v2, oauth

---

## pins.add

Pins an item to a channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `pins:write`
- `channel` (formData) (required): Channel to pin the item in.
- `timestamp` (formData): Timestamp of the message to pin.

Tags: pins

---

## pins.list

Lists items pinned to a channel.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `pins:read`
- `channel` (query) (required): Channel to get pinned items for.

Tags: pins

---

## pins.remove

Un-pins an item from a channel.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `pins:write`
- `channel` (formData) (required): Channel where the item is pinned to.
- `timestamp` (formData): Timestamp of the message to un-pin.

Tags: pins

---

## reactions.add

Adds a reaction to an item.

**Parameters:**

- `channel` (formData) (required): Channel where the message to add reaction to was posted.
- `name` (formData) (required): Reaction (emoji) name.
- `timestamp` (formData) (required): Timestamp of the message to add reaction to.
- `token` (header) (required): Authentication token. Requires scope: `reactions:write`

Tags: reactions

---

## reactions.get

Gets reactions for an item.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `reactions:read`
- `channel` (query): Channel where the message to get reactions for was posted.
- `file` (query): File to get reactions for.
- `file_comment` (query): File comment to get reactions for.
- `full` (query): If true always return the complete reaction list.
- `timestamp` (query): Timestamp of the message to get reactions for.

Tags: reactions

---

## reactions.list

Lists reactions made by a user.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `reactions:read`
- `user` (query): Show reactions made by this user. Defaults to the authed user.
- `full` (query): If true always return the complete reaction list.
- `count` (query): 
- `page` (query): 
- `cursor` (query): Parameter for pagination. Set `cursor` equal to the `next_cursor` attribute returned by the previous request's `response_metadata`. This parameter is optional, but pagination is mandatory: the default value simply fetches the first "page" of the collection. See [pagination](/docs/pagination) for more details.
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the list hasn't been reached.

Tags: reactions

---

## reactions.remove

Removes a reaction from an item.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `reactions:write`
- `name` (formData) (required): Reaction (emoji) name.
- `file` (formData): File to remove reaction from.
- `file_comment` (formData): File comment to remove reaction from.
- `channel` (formData): Channel where the message to remove reaction from was posted.
- `timestamp` (formData): Timestamp of the message to remove reaction from.

Tags: reactions

---

## reminders.add

Creates a reminder.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `reminders:write`
- `text` (formData) (required): The content of the reminder
- `time` (formData) (required): When this reminder should happen: the Unix timestamp (up to five years from now), the number of seconds until the reminder (if within 24 hours), or a natural language description (Ex. "in 15 minutes," or "every Thursday")
- `user` (formData): The user who will receive the reminder. If no user is specified, the reminder will go to user who created it.

Tags: reminders

---

## reminders.complete

Marks a reminder as complete.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `reminders:write`
- `reminder` (formData): The ID of the reminder to be marked as complete

Tags: reminders

---

## reminders.delete

Deletes a reminder.

**Parameters:**

- `token` (header): Authentication token. Requires scope: `reminders:write`
- `reminder` (formData): The ID of the reminder

Tags: reminders

---

## reminders.info

Gets information about a reminder.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `reminders:read`
- `reminder` (query): The ID of the reminder

Tags: reminders

---

## reminders.list

Lists all reminders created by or for a given user.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `reminders:read`

Tags: reminders

---

## rtm.connect

Starts a Real Time Messaging session.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `rtm:stream`
- `batch_presence_aware` (query): Batch presence deliveries via subscription. Enabling changes the shape of `presence_change` events. See [batch presence](/docs/presence-and-status#batching).
- `presence_sub` (query): Only deliver presence events when requested by subscription. See [presence subscriptions](/docs/presence-and-status#subscriptions).

Tags: rtm

---

## search.messages

Searches for messages matching a query.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `search:read`
- `count` (query): Pass the number of results you want per "page". Maximum of `100`.
- `highlight` (query): Pass a value of `true` to enable query highlight markers (see below).
- `page` (query): 
- `query` (query) (required): Search query.
- `sort` (query): Return matches sorted by either `score` or `timestamp`.
- `sort_dir` (query): Change sort direction to ascending (`asc`) or descending (`desc`).

Tags: search

---

## stars.add

Adds a star to an item.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `stars:write`
- `channel` (formData): Channel to add star to, or channel where the message to add star to was posted (used with `timestamp`).
- `file` (formData): File to add star to.
- `file_comment` (formData): File comment to add star to.
- `timestamp` (formData): Timestamp of the message to add star to.

Tags: stars

---

## stars.list

Lists stars for a user.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `stars:read`
- `count` (query): 
- `page` (query): 
- `cursor` (query): Parameter for pagination. Set `cursor` equal to the `next_cursor` attribute returned by the previous request's `response_metadata`. This parameter is optional, but pagination is mandatory: the default value simply fetches the first "page" of the collection. See [pagination](/docs/pagination) for more details.
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the list hasn't been reached.

Tags: stars

---

## stars.remove

Removes a star from an item.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `stars:write`
- `channel` (formData): Channel to remove star from, or channel where the message to remove star from was posted (used with `timestamp`).
- `file` (formData): File to remove star from.
- `file_comment` (formData): File comment to remove star from.
- `timestamp` (formData): Timestamp of the message to remove star from.

Tags: stars

---

## team.accessLogs

Gets the access logs for the current team.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin`
- `before` (query): End of time range of logs to include in results (inclusive).
- `count` (query): 
- `page` (query): 

Tags: team

---

## team.billableInfo

Gets billable users information for the current team.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin`
- `user` (query): A user to retrieve the billable information for. Defaults to all users.

Tags: team

---

## team.info

Gets information about the current team.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `team:read`
- `team` (query): Team to get info on, if omitted, will return information about the current team. Team to get info about; if omitted, will return information about the current team.

Tags: team

---

## team.integrationLogs

Gets the integration logs for the current team.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `admin`
- `app_id` (query): Filter logs to this Slack app. Defaults to all logs.
- `change_type` (query): Filter logs with this change type. Defaults to all logs.
- `count` (query): 
- `page` (query): 
- `service_id` (query): Filter logs to this service. Defaults to all logs.
- `user` (query): Filter logs generated by this user’s actions. Defaults to all logs.

Tags: team

---

## team.profile.get

Retrieve a team's profile.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `users.profile:read`
- `visibility` (query): Filter by visibility.

Tags: team.profile, team

---

## usergroups.create

Create a User Group

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `usergroups:write`
- `channels` (formData): A comma separated string of encoded channel IDs for which the User Group uses as a default.
- `description` (formData): A short description of the User Group.
- `handle` (formData): A mention handle. Must be unique among channels, users and User Groups.
- `include_count` (formData): Include the number of users in each User Group.
- `name` (formData) (required): A name for the User Group. Must be unique among User Groups.

Tags: usergroups

---

## usergroups.disable

Disable an existing User Group

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `usergroups:write`
- `include_count` (formData): Include the number of users in the User Group.
- `usergroup` (formData) (required): The encoded ID of the User Group to disable.

Tags: usergroups

---

## usergroups.enable

Enable a User Group

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `usergroups:write`
- `include_count` (formData): Include the number of users in the User Group.
- `usergroup` (formData) (required): The encoded ID of the User Group to enable.

Tags: usergroups

---

## usergroups.list

List all User Groups for a team

**Parameters:**

- `include_users` (query): Include the list of users for each User Group.
- `token` (query) (required): Authentication token. Requires scope: `usergroups:read`
- `include_count` (query): Include the number of users in each User Group.
- `include_disabled` (query): Include disabled User Groups.

Tags: usergroups

---

## usergroups.update

Update an existing User Group

**Parameters:**

- `handle` (formData): A mention handle. Must be unique among channels, users and User Groups.
- `description` (formData): A short description of the User Group.
- `channels` (formData): A comma separated string of encoded channel IDs for which the User Group uses as a default.
- `token` (header) (required): Authentication token. Requires scope: `usergroups:write`
- `include_count` (formData): Include the number of users in the User Group.
- `usergroup` (formData) (required): The encoded ID of the User Group to update.
- `name` (formData): A name for the User Group. Must be unique among User Groups.

Tags: usergroups

---

## usergroups.users.list

List all users in a User Group

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `usergroups:read`
- `include_disabled` (query): Allow results that involve disabled User Groups.
- `usergroup` (query) (required): The encoded ID of the User Group to update.

Tags: usergroups.users, usergroups

---

## usergroups.users.update

Update the list of users for a User Group

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `usergroups:write`
- `include_count` (formData): Include the number of users in the User Group.
- `usergroup` (formData) (required): The encoded ID of the User Group to update.
- `users` (formData) (required): A comma separated string of encoded user IDs that represent the entire list of users for the User Group.

Tags: usergroups.users, usergroups

---

## users.conversations

List conversations the calling user may access.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `conversations:read`
- `user` (query): Browse conversations by a specific user ID's membership. Non-public channels are restricted to those where the calling user shares membership.
- `types` (query): Mix and match channel types by providing a comma-separated list of any combination of `public_channel`, `private_channel`, `mpim`, `im`
- `exclude_archived` (query): Set to `true` to exclude archived channels from the list
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the list hasn't been reached. Must be an integer no larger than 1000.
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.

Tags: users

---

## users.deletePhoto

Delete the user profile photo

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `users.profile:write`

Tags: users

---

## users.getPresence

Gets user presence information.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `users:read`
- `user` (query): User to get presence info on. Defaults to the authed user.

Tags: users

---

## users.identity

Get a user's identity.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `identity.basic`

Tags: users

---

## users.info

Gets information about a user.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `users:read`
- `include_locale` (query): Set this to `true` to receive the locale for this user. Defaults to `false`
- `user` (query): User to get info on

Tags: users

---

## users.list

Lists all users in a Slack team.

**Parameters:**

- `token` (query): Authentication token. Requires scope: `users:read`
- `limit` (query): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the users list hasn't been reached. Providing no `limit` value will result in Slack attempting to deliver you the entire result set. If the collection is too large you may experience `limit_required` or HTTP 500 errors.
- `cursor` (query): Paginate through collections of data by setting the `cursor` parameter to a `next_cursor` attribute returned by a previous request's `response_metadata`. Default value fetches the first "page" of the collection. See [pagination](/docs/pagination) for more detail.
- `include_locale` (query): Set this to `true` to receive the locale for users. Defaults to `false`

Tags: users

---

## users.lookupByEmail

Find a user with an email address.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `users:read.email`
- `email` (query) (required): An email address belonging to a user in the workspace

Tags: users

---

## users.profile.get

Retrieves a user's profile information.

**Parameters:**

- `token` (query) (required): Authentication token. Requires scope: `users.profile:read`
- `include_labels` (query): Include labels for each ID in custom profile fields
- `user` (query): User to retrieve profile info for

Tags: users.profile, users

---

## users.profile.set

Set the profile information for a user.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `users.profile:write`
- `name` (formData): Name of a single key to set. Usable only if `profile` is not passed.
- `profile` (formData): Collection of key:value pairs presented as a URL-encoded JSON hash. At most 50 fields may be set. Each field name is limited to 255 characters.
- `user` (formData): ID of user to change. This argument may only be specified by team admins on paid teams.
- `value` (formData): Value to set a single key to. Usable only if `profile` is not passed.

Tags: users.profile, users

---

## users.setActive

Marked a user as active. Deprecated and non-functional.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `users:write`

Tags: users

---

## users.setPhoto

Set the user profile photo

**Parameters:**

- `token` (formData) (required): Authentication token. Requires scope: `users.profile:write`
- `crop_w` (formData): Width/height of crop box (always square)
- `crop_x` (formData): X coordinate of top-left corner of crop box
- `crop_y` (formData): Y coordinate of top-left corner of crop box
- `image` (formData): File contents via `multipart/form-data`.

Tags: users

---

## users.setPresence

Manually sets user presence.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `users:write`
- `presence` (formData) (required): Either `auto` or `away`

Tags: users

---

## views.open

Open a view for a user.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `none`
- `trigger_id` (query) (required): Exchange a trigger to post to the user.
- `view` (query) (required): A [view payload](/reference/surfaces/views). This must be a JSON-encoded string.

Tags: views

---

## views.publish

Publish a static view for a User.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `none`
- `user_id` (query) (required): `id` of the user you want publish a view to.
- `view` (query) (required): A [view payload](/reference/surfaces/views). This must be a JSON-encoded string.
- `hash` (query): A string that represents view state to protect against possible race conditions.

Tags: views

---

## views.push

Push a view onto the stack of a root view.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `none`
- `trigger_id` (query) (required): Exchange a trigger to post to the user.
- `view` (query) (required): A [view payload](/reference/surfaces/views). This must be a JSON-encoded string.

Tags: views

---

## views.update

Update an existing view.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `none`
- `view_id` (query): A unique identifier of the view to be updated. Either `view_id` or `external_id` is required.
- `external_id` (query): A unique identifier of the view set by the developer. Must be unique for all views on a team. Max length of 255 characters. Either `view_id` or `external_id` is required.
- `view` (query): A [view object](/reference/surfaces/views). This must be a JSON-encoded string.
- `hash` (query): A string that represents view state to protect against possible race conditions.

Tags: views

---

## workflows.stepCompleted

Indicate that an app's step in a workflow completed execution.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `workflow.steps:execute`
- `workflow_step_execute_id` (query) (required): Context identifier that maps to the correct workflow step execution.
- `outputs` (query): Key-value object of outputs from your step. Keys of this object reflect the configured `key` properties of your [`outputs`](/reference/workflows/workflow_step#output) array from your `workflow_step` object.

Tags: workflows

---

## workflows.stepFailed

Indicate that an app's step in a workflow failed to execute.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `workflow.steps:execute`
- `workflow_step_execute_id` (query) (required): Context identifier that maps to the correct workflow step execution.
- `error` (query) (required): A JSON-based object with a `message` property that should contain a human readable error message.

Tags: workflows

---

## workflows.updateStep

Update the configuration for a workflow extension step.

**Parameters:**

- `token` (header) (required): Authentication token. Requires scope: `workflow.steps:execute`
- `workflow_step_edit_id` (query) (required): A context identifier provided with `view_submission` payloads used to call back to `workflows.updateStep`.
- `inputs` (query): A JSON key-value map of inputs required from a user during configuration. This is the data your app expects to receive when the workflow step starts. **Please note**: the embedded variable format is set and replaced by the workflow system. You cannot create custom variables that will be replaced at runtime. [Read more about variables in workflow steps here](/workflows/steps#variables).
- `outputs` (query): An JSON array of output objects used during step execution. This is the data your app agrees to provide when your workflow step was executed.
- `step_name` (query): An optional field that can be used to override the step name that is shown in the Workflow Builder.
- `step_image_url` (query): An optional field that can be used to override app image that is shown in the Workflow Builder.

Tags: workflows

---

