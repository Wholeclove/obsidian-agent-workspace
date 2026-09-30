---
name: vault-workspace
description: Initialize an Obsidian agent workspace, create task folders with the bundled helper, or review its layout. Use for vault setup, scope selection, and task initialization; routine working-file guidance is loaded by plugin hooks.
---

The plugin loads the shared policy through SessionStart and SubagentStart hooks. This skill provides setup and helper usage. If hooks are unavailable, the repository README explains standalone guidance.

Read [the vault structure and working policy](references/vault-structure.md) before writing working files. The vault is a normal filesystem directory; no Obsidian API, server, or running desktop app is needed.

Run the helper’s `path` or `context` command from the session’s repository to resolve the vault. The default is `.agent-vault/` in the primary checkout, shared by its worktrees. `--scope global` selects `~/Documents/obsidian-vault`; explicit `--vault` or `OBSIDIAN_AGENT_VAULT` overrides scope. See the shared policy for persistent scope settings. Expand `~` to the user’s home directory. Ensure the agent has write access under its normal permissions. Use the helper at `../../scripts/vault.py` relative to this skill folder (resolve to an absolute path before invoking from another directory):

```sh
python3 /absolute/plugin/scripts/vault.py --vault "/absolute/vault" init
python3 /absolute/plugin/scripts/vault.py --vault "/absolute/vault" task \
  --project billing-api --title "Investigate retry failures" --owner codex
```

The task command prints JSON with absolute paths and an Obsidian URI. Reuse an existing task when continuing: read its README, decisions, and latest handoff first. Keep its existing vault path even when the default has changed. Create a new task only for new work. Do not write into the installed plugin directory; it may be an immutable cache.

Before ending a work session, update the task index, link useful files, and write `handoffs/latest.md`. Return a clickable absolute link to the index and its vault-relative path so both agent clients and humans can locate it.
