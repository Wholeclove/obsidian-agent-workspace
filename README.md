# Obsidian Agent Workspace

[![Tests](https://github.com/Wholeclove/obsidian-agent-workspace/actions/workflows/tests.yml/badge.svg)](https://github.com/Wholeclove/obsidian-agent-workspace/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Keep Claude Code and Codex working files in an Obsidian vault: scratch notes,
temporary scripts, research, logs, and handoffs, organized by project and task.

Each task has a readable index and a handoff note. You can inspect the work in
Obsidian, or give another agent the task index to continue from the same context.
Persistent guidance establishes the workflow in both clients. An optional plugin
and dependency-free Python helper create the workspace and task folders.

## Requirements

- Claude Code or Codex with access to your filesystem.
- Python 3.10 or later on macOS or Linux for the optional helper, available as `python3`.
- Plugin support only if you choose to install the optional plugin.
- A local directory for the vault, writable by your agent.
- Obsidian is optional for agents and useful for browsing the files yourself.

Examples use a POSIX shell on macOS or Linux. These platforms are covered by CI.
The helper uses POSIX file locking; Windows is not supported by the helper.

## Add the guidance

Copy [the agent guidance](docs/agent-guidance.md) into your existing instruction
file, preserving its other content:

| Client | All projects | One project |
| --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | `CLAUDE.md` at the project root |
| Codex | `~/.codex/AGENTS.md` | `AGENTS.md` at the project root |

Set a custom vault path in those instructions if needed, then start a new session.
The guidance covers destinations, navigation, updates, and handoffs directly; it
requires no skill invocation. It asks the agent to check file destinations as it
works. There are no startup hooks or per-write checks running in the background.

Installing the optional plugin does **not** install these persistent instructions.
The guidance is usable on its own; an agent can create the documented layout with
its normal filesystem tools.

See [where agents put files](docs/file-placement.md) for the instruction sources,
file destinations, and how agents share context across repository worktrees.
This repository's `AGENTS.md` and `CLAUDE.md` point to the same guidance.

## Optional plugin

The plugin supplies the `vault-workspace` skill and helper for initializing a vault
and creating task folders. Install directly from GitHub:

**Claude Code** — run inside a session:

```text
/plugin marketplace add Wholeclove/obsidian-agent-workspace
/plugin install obsidian-workspace@obsidian-agent-workspace
```

**Codex** — run in your terminal:

```sh
codex plugin marketplace add https://github.com/Wholeclove/obsidian-agent-workspace.git
codex plugin add obsidian-workspace@obsidian-agent-workspace
```

Start a new session or thread after installation. Invoke
`/obsidian-workspace:vault-workspace` in Claude Code or `$vault-workspace` in Codex.
No manual clone is needed to install either plugin.

## First task

Ask your agent:

> Follow my vault guidance and create a task for billing-api called Investigate
> retry failures. Use the workspace helper if available.

The default vault is **`~/Documents/obsidian-vault`**. The agent or helper creates
the workspace when asked; installing the plugin does not write to the vault.
Open that directory as a vault in Obsidian and start at `agents/home.md`.

```text
obsidian-vault/
└── agents/
    ├── home.md
    ├── guide.md
    └── projects/
        └── billing-api/
            ├── index.md
            └── tasks/
                └── 1-investigate-retry-failures-2026-09-29/
                    ├── README.md
                    ├── decisions.md
                    ├── scratch/
                    ├── tmp/
                    ├── research/
                    ├── artifacts/
                    ├── logs/
                    └── handoffs/latest.md
```

Task names start with a short project sequence, followed by the readable title and
UTC date. Numbers increase across days. Use numeric (natural) name sorting for chronological order. Full
timestamps stay in README metadata. Existing task paths are preserved.

The task README links to relevant files and records the objective, status, owner,
and working context. The decision log records choices, rationale, alternatives, and consequences.
The handoff links to that log and captures current constraints, verification, and next steps.
Resume a task from its README instead of creating a new folder for each session.
Completed tasks stay at stable paths; nothing is automatically deleted.

See [Obsidian setup](docs/obsidian-setup.md) for opening code, JSON, logs, and other
non-default file types, and [the walkthrough](docs/walkthrough.md) for a complete
cross-client check.

## Configuration

Vault selection follows this order:

1. An explicit vault path supplied to the agent or the helper's `--vault` option.
2. The `OBSIDIAN_AGENT_VAULT` environment variable.
3. `~/Documents/obsidian-vault`.

For an existing vault:

```sh
export OBSIDIAN_AGENT_VAULT="$HOME/Documents/my-vault"
```

Desktop applications may not inherit your shell environment. Put the path in your
agent's persistent instructions when needed. Generated folder names have no spaces;
custom vault paths containing spaces are supported.

### Give repository agents vault access

Persistent instructions choose destinations; filesystem settings provide access.
Create the vault directory before adding it to either client. Use the same absolute
path in access settings as in your instructions, including when starting in a
separate Git worktree. Keep machine-specific absolute paths in personal settings.

For **Codex**, merge the vault into `~/.codex/config.toml`:

```toml
[sandbox_workspace_write]
writable_roots = ["/absolute/path/to/obsidian-vault"]
```

Preserve existing entries and avoid duplicate TOML tables. This setting applies to
`workspace-write` sessions. For one CLI session, use:

```sh
codex --add-dir "${OBSIDIAN_AGENT_VAULT:-$HOME/Documents/obsidian-vault}"
```

See the official [Codex configuration reference](https://developers.openai.com/codex/config-reference).

For **Claude Code**, merge the vault into `~/.claude/settings.json`:

```json
{
  "permissions": {
    "additionalDirectories": ["/absolute/path/to/obsidian-vault"]
  }
}
```

Preserve other permission settings and existing directories. For one CLI session,
use `claude --add-dir "/absolute/path/to/obsidian-vault"`. The directory follows the
session's normal edit permissions; see [Claude Code working directories](https://code.claude.com/docs/en/permissions#working-directories).

Start a new session after changing global instructions or access settings. In a
managed desktop session, check its effective workspace permissions too: host policy
can restrict access beyond these settings. Verify access from each client and from
a task worktree using [the walkthrough](docs/walkthrough.md). An inaccessible vault
needs a path or permission fix; a repository symlink does not grant access.

## Scope

The guidance directs agent behavior; it does not intercept filesystem writes.
Tool-managed caches, transcripts, and required build outputs may remain elsewhere.
Agent-controlled working files belong in the vault, while source changes belong in
their repository. The helper does not change permissions, configure sync, or install
Obsidian community plugins. Avoid putting credentials or unredacted secrets in a
vault, particularly one that syncs to other devices.

## Contributing

Bug reports and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md)
for local development and checks, [CLI usage](docs/cli.md) for the helper, and
[CHANGELOG.md](CHANGELOG.md) for changes and upgrade notes.

Licensed under the [MIT License](LICENSE).
