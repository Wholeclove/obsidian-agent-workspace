# Workspace helper

The helper requires Python 3.10+ on macOS or Linux and has no third-party dependencies. After cloning
the repository, run these commands from its root. Installed skills resolve the
helper relative to the plugin, so agents do not need a separate checkout.

```sh
python3 plugins/obsidian-workspace/scripts/vault.py --help
python3 plugins/obsidian-workspace/scripts/vault.py path
python3 plugins/obsidian-workspace/scripts/vault.py init
python3 plugins/obsidian-workspace/scripts/vault.py task \
  --project billing-api --title "Investigate retry failures" --owner codex
python3 plugins/obsidian-workspace/scripts/vault.py context
```

| Command | Result |
| --- | --- |
| `init` | Creates `agents/home.md`, `agents/guide.md`, and `agents/projects/`; prints the workspace path. Existing notes are preserved. |
| `task` | Creates a unique task, subfolders, README, decision log, and handoff; prints JSON paths. Also initializes the workspace if needed. |
| `path` | Prints only the absolute vault path; does not write files. Useful for access settings. |
| `context` | Prints the resolved vault path, helper path, and policy. Does not write files. |

Select a custom vault by passing `--vault` **before** the command:

```sh
python3 plugins/obsidian-workspace/scripts/vault.py \
  --vault "$HOME/Documents/my-vault" task \
  --project billing-api --title "Investigate retry failures" --owner claude
```

Explicit `--vault` overrides `OBSIDIAN_AGENT_VAULT`; either overrides scope.
Otherwise scope is `--scope`, `OBSIDIAN_AGENT_VAULT_SCOPE`, repository-local
`obsidianWorkspace.scope`, then `repository`. The repository default is
`.agent-vault/` in the primary checkout, shared across linked worktrees. `global`
uses `~/Documents/obsidian-vault`:

```sh
python3 plugins/obsidian-workspace/scripts/vault.py --scope global context
git config --local obsidianWorkspace.scope global
```

Run the installed helper from the repository you are working on; its installation
directory does not select the vault. Outside Git, use global scope or `--vault`.
Bare-primary worktrees and layouts where Git cannot locate the primary checkout
also require an explicit choice. Paths must be absolute after expanding `~`.
Quote paths and titles in shell commands. `init` and `task` add an internal
`.gitignore` containing `*` to the default repository vault when absent; existing
notes and ignore files remain unchanged. `path` and `context` are read-only.
See [vault access](../README.md#give-repository-agents-vault-access) before writes.

Projects use lowercase ASCII letters, digits, and hyphens. Choose a stable project
slug across worktrees, and distinguish repositories with the same basename. Task
titles need at least one ASCII letter or digit; titles retain their original text
in metadata. New task folders start with a sequence without leading zeros, then the title,
then the UTC date: `tasks/1-investigate-retry-failures-2026-09-29/`. Numbers
increase across the entire project, including across days, so numeric (natural) name sorting keeps
sessions in creation order. Full UTC timestamps remain in README metadata. A hidden
`tasks/.sequence.lock` file coordinates concurrent creators on macOS/Linux. Existing folders are never renamed by the helper. `--owner` is optional and defaults to `unassigned`.

The task command's JSON includes:

- `task_dir`: absolute task directory.
- `index`: absolute task README path.
- `decisions`: absolute path to the task decision log.
- `vault_relative_index`: path to that README from the vault root.
- `obsidian_uri`: encoded URI for opening the README in Obsidian.
- `tmpdir`: directory for command-scoped temporary files.

To direct a command's temporary files, use the returned task path:

```sh
TASK_DIR=/absolute/path/to/obsidian-vault/agents/projects/billing-api/tasks/task-id
TMPDIR="$TASK_DIR/tmp" TMP="$TASK_DIR/tmp" TEMP="$TASK_DIR/tmp" your-command
```

The command must support these variables. Redirections and explicit output paths
still need to point into the task directory. No environment is changed globally.

Filesystem or input errors produce a message on stderr and a nonzero exit code.
For an invalid vault setting, `context` prints a diagnostic for the model to
explain the configuration problem. It never selects a
fallback in place of an invalid explicit path.

## Open a vault in Obsidian

The `open-vault` skill uses a separate helper from the installed plugin:

```sh
python3 plugins/obsidian-workspace/scripts/open_vault.py --task "/absolute/task/README.md"
python3 plugins/obsidian-workspace/scripts/open_vault.py --dry-run
```

`--task` selects the current task’s original vault ahead of environment/scope
defaults. For custom older layouts, pass its absolute `--vault` too. Without a
task, `--vault`, `--scope`, and environment/repository settings resolve as above.
The target is the task README, then the home note, then the vault itself.

The helper reads the desktop `obsidian.json` registry on macOS or Linux; Linux
respects `XDG_CONFIG_HOME`. For another profile, pass `--registry` with its absolute
registry path. Exact vault paths map to registered IDs. Missing, inaccessible, or
unrecognized registration uses `obsidian://choose-vault` and returns instructions
for registering the folder. `--dry-run` prints JSON without launching anything.
The helper does not write notes or app configuration, and a missing vault is an
error. Its `launch_requested` result acknowledges the OS request, not GUI success.
