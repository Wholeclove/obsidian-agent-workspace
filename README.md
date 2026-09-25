# Obsidian Agent Workspace

[![Tests](https://github.com/Wholeclove/obsidian-agent-workspace/actions/workflows/tests.yml/badge.svg)](https://github.com/Wholeclove/obsidian-agent-workspace/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Keep Claude Code and Codex working files in an Obsidian vault: scratch notes,
temporary scripts, research, logs, and handoffs, organized by project and task.

Each task has a readable index and a handoff note. You can inspect the work in
Obsidian, or give another agent the task index to continue from the same context.
Both clients share one skill and a dependency-free Python helper.

## Requirements

- Python 3.10 or later, available as `python3`.
- Claude Code or Codex with plugin support. For Codex CLI, check that
  `codex plugin marketplace add --help` is available.
- A local directory for the vault, writable by your agent.
- Obsidian is optional for agents and useful for browsing the files yourself.

Examples use a POSIX shell on macOS or Linux. These platforms are covered by CI;
Windows client integration has not been verified.

## Install

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

> Use the vault-workspace skill to initialize my vault and create a task for
> billing-api called Investigate retry failures.

The default vault is **`~/Documents/obsidian-vault`**. The helper creates its
workspace when invoked; installing the plugin does not write to the vault.
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

## Use for every task

Claude's startup hook loads the workspace policy; Codex selects the skill on demand.
To make the workflow a persistent preference, append this block to
`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, or your project's instructions. Adjust
the vault path and preserve the file's existing content.

```markdown
## Working files

Use the obsidian-workspace plugin's vault-workspace skill for agent-created
scratch files, temporary scripts, research, logs, artifacts, and handoffs.
My vault is ~/Documents/obsidian-vault. Expand ~ to my home directory.
Initialize it if needed, then follow agents/guide.md.
Reuse the current task and keep its README links and handoffs/latest.md current.
At handoff, provide the task README's absolute link and vault-relative path.
Keep deliverable source code and required project files in the repository.
If the vault is inaccessible, report the issue before writing working files.
```

## Scope

The plugin guides agent behavior; it does not intercept filesystem writes.
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
