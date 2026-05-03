# slack-skill

A portable skill that gives Claude (or any skill-aware agent) read/write
access to Slack on your behalf via the Slack Web API, using a User OAuth
Token. The agent can read channels and DMs, send and edit messages, add
reactions, and search history — all attributed to your Slack account. No
server, no daemon, no compilation. Bundles a single Python 3 helper
script and progressive-disclosure API documentation.

This README is for humans setting the skill up. The agent-facing surface
lives in [SKILL.md](SKILL.md).

## ⛔ DANGER — READ BEFORE USE

> **By installing or using this skill, you give an AI agent the ability
> to send, edit, delete, and react to messages on your behalf in any
> Slack workspace whose User OAuth Token you configure. The agent acts
> AS YOU. Read [NOTICE](NOTICE) before proceeding.**

Specifically:

- The skill calls Slack's Web API with your User OAuth Token. Every
  request is attributed to you by Slack.
- There is no sandboxing and no per-call confirmation. Destructive-
  action guardrails are skill instructions, not enforced mechanisms.
- An agent that misinterprets a request, hallucinates a channel ID, or
  follows a prompt-injection payload can send messages to the wrong
  audience, delete or edit messages, exfiltrate private content, or
  trigger broadcasts in your name.
- Recipients and administrators cannot distinguish agent-driven
  actions from actions you took yourself.
- Slack edits and deletions are not silently reversible — edit and
  delete markers are visible, and recipients may have already read or
  quoted the original.

The authors accept no liability. See [LICENSE](LICENSE) and [NOTICE](NOTICE)
for full terms.

## Companion skills

`slack-skill` pairs naturally with two other capability skills:

- **`obsidian-skill`** — read/write notes in an Obsidian vault.
- **`omnifocus-skill`** — capture and review tasks in OmniFocus.

Together they cover the "knowledge / tasks / messaging" surface for an
agent on macOS. Each is independent — install whichever you want.

`slack2omnifocus` is a separate, unrelated project: a standalone Go
daemon that turns emoji reactions into OmniFocus inbox tasks via
launchd. It does not interact with this skill, and you should not reuse
its OAuth token here (see [Create a Slack app](#create-a-slack-app)
below).

## Install

```bash
npx skills add dcgrigsby/slack-skill -g -a claude-code -a gemini-cli -a codex -a pi -y
```

This installs the skill folder into the locations skill-aware agents
read from (Claude Code, Gemini CLI, Codex, Pi). Once installed, the
agent will discover `SKILL.md` automatically; you still need to create
a Slack app and configure a token before the skill can do anything.

## Create a Slack app

The skill talks to Slack via a **User OAuth Token** (`xoxp-...`) issued
by a Slack app you control. You only do this once per workspace.

> **Create a new Slack app for this skill.** Don't reuse a token from
> `slack2omnifocus` or any other integration. The scope sets are
> different, revocation should be independent, and troubleshooting is
> simpler when each integration has its own app.

### Recommended: from manifest

1. Go to <https://api.slack.com/apps> and click **Create New App** →
   **From an app manifest**.
2. Pick your workspace.
3. Paste the contents of [`docs/slack-app-manifest.yaml`](docs/slack-app-manifest.yaml).
4. Review the scopes Slack shows you, then click **Create**.
5. On the app's page, click **Install to Workspace** → **Allow**.
6. Open **OAuth & Permissions** in the left sidebar and copy the
   **User OAuth Token** (starts with `xoxp-...`).

### Manual fallback

If you'd rather configure the app by hand:

1. **Create New App** → **From scratch**. Name it `slack-skill`, pick
   your workspace, click **Create App**.
2. Open **OAuth & Permissions** → **Scopes** → **User Token Scopes**
   (NOT Bot Token Scopes).
3. Add every scope listed in
   [`docs/slack-app-manifest.yaml`](docs/slack-app-manifest.yaml) under
   `oauth_config.scopes.user`. The manifest is the authoritative scope
   list — adding scopes by hand is mechanical, just keep the two in
   sync.
4. Scroll up and click **Install to Workspace** → **Allow**.
5. Copy the **User OAuth Token** (`xoxp-...`) from the top of the
   OAuth & Permissions page.

If you change scopes later, Slack will require you to click **Install
to Workspace** again to refresh the token.

## Configure

Register the token with the skill:

```bash
python3 scripts/slack.py auth add --workspace <name> --token xoxp-...
```

`<name>` is a label of your choosing (e.g. `personal`, `work`). The
config is stored at `~/.config/slack-skill/config.json` with mode
`0600`. Multiple workspaces are supported — see
[Multiple workspaces](#multiple-workspaces) below.

## Usage

The agent-facing surface lives in [SKILL.md](SKILL.md). That file
documents how the agent decides between the bundled Python helper and
direct API calls, the safety rails it follows for destructive
operations, and the progressive-disclosure API reference under
`docs/slack-api/`.

This README is for setting the skill up. Once `auth add` succeeds, the
agent takes it from there.

## Doctor

```bash
python3 scripts/slack.py doctor
```

Prints config status, configured workspaces, and the result of an
`auth.test` call against each token. Use this first when something
isn't working.

## Development

```bash
make test              # run mechanical test suite
make package           # build .skill bundle for distribution
make regen-reference   # refresh docs/slack-api/FULL-REFERENCE.md from OpenAPI
make clean             # remove generated artifacts
```

Tests cover the bundled script end-to-end: argument parsing, config
add/list/remove/default, token redaction, the `call` request shape,
pagination, and error paths.

## Multiple workspaces

Run `auth add` once per workspace, with a different `--workspace` name
each time:

```bash
python3 scripts/slack.py auth add --workspace personal --token xoxp-...
python3 scripts/slack.py auth add --workspace work     --token xoxp-...
```

The first workspace added becomes the default. Change it with:

```bash
python3 scripts/slack.py auth default --workspace work
```

Every command that hits Slack accepts `--workspace <name>` to pick a
specific workspace; without it, the default is used.

## Troubleshooting

- **Logs:** the script doesn't write log files. Pass `--debug` to log
  request/response details to stderr while you reproduce the issue.
- **Token errors:** make sure you copied the **User OAuth Token**
  (`xoxp-...`), not a Bot Token (`xoxb-...`). The User OAuth Token is
  at the top of the **OAuth & Permissions** page.
- **`missing_scope` errors:** add the missing scope on the app's
  **OAuth & Permissions** page and click **Install to Workspace** again
  to refresh the token. Slack will not silently grant new scopes to an
  existing token.
- **`account_inactive`:** the underlying Slack account is suspended or
  deactivated. There's nothing the skill can do — resolve it with the
  workspace admin.

## License

Apache 2.0 — see [LICENSE](LICENSE).
