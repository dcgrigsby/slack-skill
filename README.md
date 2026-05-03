# slack-skill

A portable skill that gives Claude (or any skill-aware agent) read/write
access to Slack on your behalf via the Slack Web API, using a User OAuth
Token. No server, no daemon, no compilation. Bundles a single Python 3
helper script and progressive-disclosure API documentation.

## Status

Work in progress. Design specification:
[`docs/specs/2026-05-02-slack-skill-design.md`](docs/specs/2026-05-02-slack-skill-design.md).

Implementation files (`SKILL.md`, `scripts/slack.py`,
`docs/slack-api/*.md`, `docs/slack-app-manifest.yaml`, `Makefile`,
`evals/`) are not yet present in this repo.

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

## License

Apache 2.0 — see [LICENSE](LICENSE).
