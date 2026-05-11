# First-time setup / adding a workspace

Load when the user wants to use Slack but has no workspaces configured, when adding another workspace, or when re-doing OAuth after a token rotation. The flow takes about two minutes.

## Step 1 — Check what's already configured

```bash
python3 scripts/slack.py auth list
```

If this prints an empty list, or doesn't include the workspace they want, continue to step 2. If the workspace is already there, jump to step 5 to verify it.

## Step 2 — Create the Slack app from a manifest

Tell the user:

1. Visit https://api.slack.com/apps?new_app=1 in a browser.
2. Click **From an app manifest**.
3. Pick the workspace they want to integrate (e.g. their work Slack).
4. When prompted for the manifest, switch the editor tab to **JSON** and paste the contents of `docs/slack-app-manifest.json` from this skill. (Open that file and read it to them, or have them open it themselves.)
5. Click **Next**, review the scopes, then **Create**.
6. On the app's **Basic Information** page, click **Install to Workspace**, then **Allow** on the OAuth confirmation screen.
7. On the **OAuth & Permissions** page, copy the **User OAuth Token** (it starts with `xoxp-`).

The manifest at `docs/slack-app-manifest.json` is preconfigured with the user scopes this skill needs (channel and message reads, chat write, reactions, search, etc.). Don't tell the user to add scopes manually — the manifest does it.

## Step 3 — User pastes the token into chat

Have the user paste the `xoxp-...` token. Treat it as sensitive — do not echo it back to them in plaintext, do not log it.

## Step 4 — Add it to the config

```bash
python3 scripts/slack.py auth add --workspace work --token xoxp-REDACTED
```

Pick a short, memorable workspace name (`work`, `personal`, `acme`, etc.). The user will reuse this name for every subsequent invocation.

## Step 5 — Verify

```bash
python3 scripts/slack.py auth test --workspace work
```

This calls Slack's `auth.test` endpoint and should return the authenticated user and team. If it returns `invalid_auth`, the token was pasted incorrectly or has been revoked — re-do step 2's last sub-step and try again. If it returns `missing_scope`, the manifest in `docs/slack-app-manifest.json` may be out of sync with what this skill needs — read that file and reinstall.

If the user has more than one Slack workspace they want to use, repeat steps 2–5 for each, with a different `--workspace <name>` per workspace.
