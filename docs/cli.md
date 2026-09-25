# Workspace helper

The helper requires Python 3.10+ and has no third-party dependencies. After cloning
the repository, run these commands from its root. Installed skills resolve the
helper relative to the plugin, so agents do not need a separate checkout.

```sh
python3 plugins/obsidian-workspace/scripts/vault.py --help
python3 plugins/obsidian-workspace/scripts/vault.py init
python3 plugins/obsidian-workspace/scripts/vault.py task \
  --project billing-api --title "Investigate retry failures" --owner codex
python3 plugins/obsidian-workspace/scripts/vault.py context
```

| Command | Result |
| --- | --- |
| `init` | Creates `agents/home.md`, `agents/guide.md`, and `agents/projects/`; prints the workspace path. Existing notes are preserved. |
| `task` | Creates a unique task, subfolders, README, and handoff; prints JSON paths. Also initializes the workspace if needed. |
| `context` | Prints the resolved vault path, helper path, and policy. Does not write files. |

Select a custom vault by passing `--vault` **before** the command:

```sh
python3 plugins/obsidian-workspace/scripts/vault.py \
  --vault "$HOME/Documents/my-vault" task \
  --project billing-api --title "Investigate retry failures" --owner claude
```

An explicit path takes precedence over `OBSIDIAN_AGENT_VAULT`, which takes
precedence over `~/Documents/obsidian-vault`. Paths must be absolute after expanding
`~`. Quote paths and titles in shell commands.

Projects use lowercase ASCII letters, digits, and hyphens. Choose a stable project
slug across worktrees, and distinguish repositories with the same basename. Task
titles need at least one ASCII letter or digit; titles retain their original text
in metadata, while folder names use a normalized slug, UTC timestamp, and random
suffix. `--owner` is optional and defaults to `unassigned`.

The task command's JSON includes:

- `task_dir`: absolute task directory.
- `index`: absolute task README path.
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
For an invalid vault setting, `context` prints a diagnostic for the model so the
startup hook can still explain the configuration problem. It never selects a
fallback in place of an invalid explicit path.
