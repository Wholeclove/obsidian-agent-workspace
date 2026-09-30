# Obsidian Agent Workspace

[![Tests](https://github.com/Wholeclove/obsidian-agent-workspace/actions/workflows/tests.yml/badge.svg)](https://github.com/Wholeclove/obsidian-agent-workspace/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Keep Claude Code and Codex working files in an Obsidian vault: scratch notes,
temporary scripts, research, logs, and handoffs, organized by project and task.

Each task has a readable index and a handoff note. You can inspect the work in
Obsidian, or give another agent the task index to continue from the same context.
The plugin loads working-file guidance automatically in both clients. New work uses
an ignored `.agent-vault/` in the repository’s primary checkout, shared by its Git
worktrees. You can also select a shared vault for all repositories.

## Requirements

- Claude Code or Codex with access to your filesystem.
- Python 3.10 or later on macOS or Linux, available as `python3`, for plugin hooks and the helper.
- Git with `worktree list --porcelain -z` and `rev-parse --path-format=absolute` support.
- A current client with plugin and hook support, or use the standalone setup below.
- A local directory for the vault, writable by your agent.
- Obsidian is optional for agents and useful for browsing the files yourself.

Examples use a POSIX shell on macOS or Linux. These platforms are covered by CI.
The helper uses POSIX file locking; Windows is not supported by the helper.

## Install the plugin

No manual guidance copy is needed. The plugin loads its shared policy at session
start, resume, and after compaction, and supplies it to new subagents. The bundled
skill and helper are available for setup and task creation.

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

In Codex, open `/hooks` to review and trust the plugin’s `SessionStart` and
`SubagentStart` commands. Installation alone does not trust them; changes to hook
definitions require review again. See [Codex hook trust](https://learn.chatgpt.com/docs/hooks).
In Claude Code, use `/hooks` to inspect the loaded hooks. Start a new session or
thread after installation and trust review. If your client or organization disables
hooks, use the standalone setup below.

Next, [configure vault access](#give-repository-agents-vault-access). The hooks
read the packaged policy and resolve the vault path; they do not create a vault,
change client settings, or grant access. There are no per-write checks.
The shared hook file is automatically discovered by
[Codex](https://developers.openai.com/plugins/build/plugins) and
[Claude Code](https://code.claude.com/docs/en/plugins-reference).

For setup help, invoke `/obsidian-workspace:vault-workspace` in Claude Code or
`$vault-workspace` in Codex. Routine tasks do not require invoking the skill.
No manual clone is needed to install either plugin.

### Standalone setup without a plugin

Copy [the agent guidance](docs/agent-guidance.md) into an instruction file,
preserving its other content:

| Client | All projects | One project |
| --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | `CLAUDE.md` at the project root |
| Codex | `~/.codex/AGENTS.md` | `AGENTS.md` at the project root |

Set an explicit vault path there if needed, configure filesystem access below, and
start a new session. Agents can create the layout with ordinary filesystem tools.
When switching to the plugin, verify that its hooks load first, then remove only
the old copied vault guidance. Preserve unrelated rules and intentional overrides.

See [where agents put files](docs/file-placement.md) for the instruction sources,
destinations, and worktree handoffs. This repository’s `AGENTS.md` and `CLAUDE.md`
point to the standalone guidance for agents developing the package.

## First task

Ask your agent:

> Create a task for billing-api called Investigate retry failures. Use the
> configured vault and give me its task README path.

The default vault is **`<primary-checkout>/.agent-vault/`**. The helper creates it
when asked and adds an internal `.gitignore` containing `*` to exclude its contents
from Git. Existing notes and ignore files are preserved. Open that directory with
Obsidian’s **Open folder as vault** and start at `agents/home.md`. Installing the
plugin does not register an Obsidian vault.

```text
<primary-checkout>/.agent-vault/
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

An explicit user path or helper `--vault` takes precedence, then
`OBSIDIAN_AGENT_VAULT`. Both select a custom vault independently of scope.
Paths must be absolute after expanding `~`; paths containing spaces are supported.

When no path override is set, scope is chosen in this order:

1. Helper `--scope repository` or `--scope global` for that command.
2. `OBSIDIAN_AGENT_VAULT_SCOPE` in the client’s environment.
3. The repository-local Git setting `obsidianWorkspace.scope`.
4. `repository` by default.

| Scope | Vault | Worktrees |
| --- | --- | --- |
| `repository` (default) | `<primary-checkout>/.agent-vault/` | All linked worktrees use the primary checkout’s vault |
| `global` | `~/Documents/obsidian-vault` | All repositories share this vault, with separate project folders |
| Explicit path | The path you supplied | Sessions must use the same setting or existing task README |

Choose a scope for this repository and all its worktrees:

```sh
git config --local obsidianWorkspace.scope repository
# Or keep the former shared-vault behavior:
git config --local obsidianWorkspace.scope global
```

This setting lives in local Git configuration; it does not travel with a clone.
To select the shared vault across sessions, including outside Git:

```sh
export OBSIDIAN_AGENT_VAULT_SCOPE=global
```

For a custom vault:

```sh
export OBSIDIAN_AGENT_VAULT="$HOME/Documents/my-vault"
```

Launch the client from the shell that sets these variables. Desktop applications
may not inherit them; repository-local Git scope settings also work from desktop
sessions. For a custom desktop path, put the explicit path in personal instructions.
The hook cannot read those instructions, so its reported path is a default that the
agent must override when the user specified another destination.

Outside a Git working repository, select global scope or an explicit path.
Repositories with a bare primary or a primary checkout that Git cannot locate
also need an explicit choice. Invalid settings produce a diagnostic, with no
silent fallback. Existing tasks stay in their original vault: resume them through
their README even after changing the default. No migration or cleanup runs.

### Give repository agents vault access

Instructions choose destinations; filesystem permissions provide access. Resolve
the vault from the session’s repository first. Ask the agent to report the path,
or run the installed helper’s `path` command. From this source checkout:

```sh
python3 plugins/obsidian-workspace/scripts/vault.py path
```

Create that directory before adding it to the client’s allowed directories. In the
primary checkout, the default `.agent-vault/` is within the workspace and normally
needs no extra directory grant. **A linked worktree is a separate directory:** its
shared vault is in the primary checkout, so allow that exact absolute vault path.
Global and custom vaults outside the workspace need the same treatment.

For a single CLI session, substitute the resolved path:

```sh
mkdir -p "/absolute/primary-checkout/.agent-vault"
codex --add-dir "/absolute/primary-checkout/.agent-vault"
# Or:
claude --add-dir "/absolute/primary-checkout/.agent-vault"
```

For persistent **Codex** access, merge the path into `~/.codex/config.toml`:

```toml
[sandbox_workspace_write]
writable_roots = ["/absolute/primary-checkout/.agent-vault"]
```

Preserve existing entries and avoid duplicate TOML tables. This applies to
`workspace-write` sessions. Use the shared or custom vault’s absolute path if you
selected one. See the [Codex configuration reference](https://developers.openai.com/codex/config-reference).

For persistent **Claude Code** access, merge the path into
`~/.claude/settings.json`:

```json
{
  "permissions": {
    "additionalDirectories": ["/absolute/primary-checkout/.agent-vault"]
  }
}
```

Preserve existing permissions and directories. To limit configuration to one
repository, the same setting can go in `.claude/settings.local.json` in the primary
checkout. Current Claude Code uses that primary local file for ordinary macOS/Linux
worktrees; older versions and other environments may differ. Keep the file ignored
if you create it manually. See [local settings and worktrees](https://code.claude.com/docs/en/settings#where-claude-code-keeps-the-local-file-in-a-git-repository).
Additional directories follow the session’s normal edit permissions; see [Claude Code working directories](https://code.claude.com/docs/en/permissions#working-directories).

Start a fresh session after changes. From **each client and a linked worktree**,
ask the agent to resolve the vault, read an existing task README, and create and
read back a small note in that task’s `scratch/` folder. Have it report the absolute
path and actual result. Confirm that `git status --short` does not list vault notes.
A successful terminal command or startup hook does not prove that the agent’s
sandbox can write there. Managed desktop policy may require an additional workspace
grant. Report denied access and fix the path or permissions; symlinks do not grant
access. See [the walkthrough](docs/walkthrough.md) for the full check.

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
