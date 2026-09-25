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
- Python 3.10 or later for the optional helper, available as `python3`.
- Plugin support only if you choose to install the optional plugin.
- A local directory for the vault, writable by your agent.
- Obsidian is optional for agents and useful for browsing the files yourself.

Examples use a POSIX shell on macOS or Linux. These platforms are covered by CI;
Windows client integration has not been verified.

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
                └── 20260925T160000Z-investigate-retry-failures-a1b2c3d4/
                    ├── README.md
                    ├── scratch/
                    ├── tmp/
                    ├── research/
                    ├── artifacts/
                    ├── logs/
                    └── handoffs/latest.md
```

The task README links to relevant files and records the objective, status, owner,
and working context. The handoff captures decisions, verification, and next steps.
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

Grant the vault write access using your client's workspace controls. For Codex CLI,
create the vault directory first, then launch with:

```sh
codex --add-dir "${OBSIDIAN_AGENT_VAULT:-$HOME/Documents/obsidian-vault}"
```

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
