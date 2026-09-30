---
name: open-vault
description: Open the current session's Obsidian vault and active task note. Use when the user asks to open or show the vault, session notes, or current task files in Obsidian. Handles repository worktrees, older tasks in another vault, and unregistered vaults.
---

Open the vault for the work already active in this conversation. The user's
explicit destination takes precedence. Otherwise use the current task README and
its vault from session context or a handoff. Do not select the newest task on disk,
the last active Obsidian vault, or create a task just to open a vault. If several
tasks are plausible, ask which one. With no active task, use the configured vault.

Resolve `../../scripts/open_vault.py` relative to this skill to an absolute path.
Run it from the session's repository/worktree using the normal filesystem tools:

```sh
python3 /absolute/plugin/scripts/open_vault.py --task "/absolute/current-task/README.md"
```

For a task in an older/custom layout, pass its known `--vault` as well. If the user
explicitly selects another vault, omit the unrelated task. With no active task:

```sh
python3 /absolute/plugin/scripts/open_vault.py
```

The helper shares the workspace helper's repository/global resolution. It opens
the task README, or `agents/home.md` when no task is known, or the vault itself
when no home note exists. Paths must be absolute; quote paths with spaces.
`--dry-run` inspects the request without opening the desktop app.

Read the JSON result:

- If `error` is present, report the launcher failure and provide the returned URI
  and path. `launch_requested: false` means no successful launch request was sent
  (and is expected during `--dry-run`).
- `registered`: the exact vault was found. The helper uses its ID to avoid
  confusing identically named repository vaults.
- `unregistered` or `unknown`: the helper requests the vault picker. Tell the
  user to choose **Open folder as vault** with the returned absolute `vault`
  path, then retry after registration. On macOS, Command-Shift-G enters a hidden
  `.agent-vault` path in the file picker. An alternate desktop profile can use
  `--registry "/absolute/obsidian.json"`.
- A missing vault or task is an error. Report it; do not create or migrate notes
  unless the user also requested setup.

The helper reads Obsidian's registry but never modifies it or the vault. Do not
edit the live registry, install community plugins, or change permissions just to
open a vault. For a remote/headless session, provide the returned URI and path for
the user's desktop instead of claiming it opened locally.

Report that the open request was sent, with a clickable task/home note path. A
successful launcher exit does not prove the correct Obsidian window appeared;
claim a verified open only with direct UI evidence or user confirmation.
