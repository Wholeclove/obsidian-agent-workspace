---
name: vault-workspace
description: Organize agent-created temporary files, scratch notes, research, logs, artifacts, and handoffs in an Obsidian vault. Use before creating working files or resuming work from a vault handoff.
---

Read [the vault structure and working policy](references/vault-structure.md) before writing working files. The vault is a normal filesystem directory; no Obsidian API, server, or running desktop app is needed.

Resolve the vault in order: the user's explicit path, `OBSIDIAN_AGENT_VAULT`, then `~/Documents/obsidian-vault`. Expand `~` to the user's home directory. The helper uses the same default when `--vault` and the environment variable are omitted. Ensure the agent has write access under its normal permissions. Use the helper at `../../scripts/vault.py` relative to this skill folder (resolve to an absolute path before invoking from another directory):

```sh
python3 /absolute/plugin/scripts/vault.py --vault "/absolute/vault" init
python3 /absolute/plugin/scripts/vault.py --vault "/absolute/vault" task \
  --project billing-api --title "Investigate retry failures" --owner codex
```

The task command prints JSON with absolute paths and an Obsidian URI. Reuse an existing task when continuing: read its README and latest handoff first. Create a new task only for new work. Do not write into the installed plugin directory; it may be an immutable cache.

Before ending a work session, update the task index, link useful files, and write `handoffs/latest.md`. Return a clickable absolute link to the index and its vault-relative path so both agent clients and humans can locate it.
