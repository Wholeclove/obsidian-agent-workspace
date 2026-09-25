# Obsidian Agent Workspace

Claude Code and Codex plugins that put agent-created scratch files, temporary scripts,
research, logs, artifacts, and handoffs in an Obsidian vault. Both clients use the same
skill, helper, and directory conventions. Python 3.9+ is the only helper dependency.

## Start with a vault

Use an existing vault or choose a new directory. From this repository:

```sh
export OBSIDIAN_AGENT_VAULT="$HOME/Documents/Agent Vault"
python3 plugins/obsidian-workspace/scripts/vault.py init
python3 plugins/obsidian-workspace/scripts/vault.py task \
  --project my-project --title "Investigate a bug" --owner human
```

`init` creates a starter workspace under `Agent Workspace/` and preserves existing
notes. Open the chosen directory as a vault in Obsidian and start at
`Agent Workspace/Home.md`. The task command returns JSON with paths and an Obsidian
URI. Use a task's README and handoff to resume it; don't create another task on each turn.

Set `OBSIDIAN_AGENT_VAULT` in the environment that launches your agent, or put the
absolute vault path in the persistent instruction below. Desktop apps may not inherit
shell startup files. The helper also accepts `--vault "/absolute/path"` **before** its
subcommand. No hidden config or guessed default vault is used.

## Install for Claude Code

From Claude Code, replace the path below with this checkout's absolute path:

```text
/plugin marketplace add /absolute/path/to/obsidian-agent-workspace
/plugin install obsidian-workspace@obsidian-agent-workspace
```

Start a new session. For a one-session local development load:

```sh
claude --plugin-dir /absolute/path/to/obsidian-agent-workspace/plugins/obsidian-workspace
```

The plugin's `SessionStart` hook prints the vault policy on startup, resume, and
compaction. The `/obsidian-workspace:vault-workspace` skill provides the same workflow.
The hook is read-only and never creates folders or edits client settings.

## Install for Codex

This repository contains a local Codex marketplace named `personal`, generated with
the Codex plugin scaffold. Add this checkout and install the plugin:

```sh
codex plugin marketplace add /absolute/path/to/obsidian-agent-workspace
codex plugin add obsidian-workspace@personal
```

If you already have a marketplace named `personal`, give this repository's
`.agents/plugins/marketplace.json` a unique top-level `name` before adding it, and use
that name after `@`. This changes only this repository's catalog, not your existing
marketplace. Start a new Codex thread after installation; invoke `$vault-workspace`
if needed. The package uses the `.codex-plugin/plugin.json` format supported by the
locally validated Codex CLI. Codex and Claude have separate marketplace manifests;
the actual plugin content is shared.

## Make it the default for every task

Skills are selected on demand. For the requested always-use-the-vault behavior,
append the following block to your existing global `~/.codex/AGENTS.md` and
`~/.claude/CLAUDE.md`, or to the corresponding instructions in each project. Replace
the example vault path. Preserve all existing instructions.

```markdown
## Agent working files

Use the obsidian-workspace plugin's vault-workspace skill before creating any
agent-controlled temporary file, scratch note/script, research file, captured log,
artifact, or handoff. My vault is `/absolute/path/to/Agent Vault`.
Read `Agent Workspace/Guide.md` in that vault. Keep these files under
`Agent Workspace/Projects/<project>/Tasks/<task-id>/`, following its structure.
Reuse the current task; keep its README file links and handoffs/latest.md current.
Return an absolute link and vault-relative path to the task README when handing off.
Keep deliverable source code and required project files in their repository.
If the vault is inaccessible, report the issue instead of silently writing elsewhere.
```

Grant vault write access through each client's normal workspace/sandbox controls.
For Codex CLI, `codex --add-dir "$OBSIDIAN_AGENT_VAULT"` adds that directory to the
writable workspace. The plugin does not change permissions. No credentials, server,
or running Obsidian app are required for filesystem access.

This provides model instructions and scoped temp-directory guidance, **not OS-level
enforcement**. Tool-internal caches, agent transcripts, and mandatory build outputs
can still live elsewhere. Actual project changes remain in the appropriate Git
worktree. See [the full policy](plugins/obsidian-workspace/skills/vault-workspace/references/vault-structure.md).

## Find files as a human

```text
Agent Workspace/Home.md
  Projects/<project>/Index.md
    Tasks/<timestamp>-<title>-<id>/README.md
      scratch/  tmp/  research/  artifacts/  logs/  handoffs/latest.md
```

The README links to useful files and records status, owner, timestamps, repository,
worktree, and branch. Handoffs record what happened and what to do next. Completed
tasks stay at stable paths, marked complete or archived. Nothing is auto-deleted.

Follow [Obsidian setup](docs/obsidian-setup.md) to open and edit non-default file types.
Use [the walkthrough](docs/walkthrough.md) to verify the workflow after installing.

## Development

```sh
python3 -m unittest discover -s tests -v
claude plugin validate ./plugins/obsidian-workspace
```

The tests use isolated directories and never alter your real vault or client config.
This repository does not install plugins globally or modify your existing vault by
itself. Install and configure it using the steps above.

## References

- [Claude plugin manifests](https://code.claude.com/docs/en/plugins-reference)
- [Claude startup hook behavior](https://code.claude.com/docs/en/hooks#sessionstart)
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Codex persistent instructions](https://developers.openai.com/codex/guides/agents-md)

Installation commands were also checked against the locally installed CLI help.
