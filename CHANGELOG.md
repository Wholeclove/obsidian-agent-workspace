# Changelog

## Unreleased

- Add `open-vault` to open the current task’s existing vault or the configured
  home note. Check registration, target exact vault IDs, and provide the vault
  picker for unregistered folders without editing Obsidian settings.

## 0.5.0

- Load shared guidance automatically through SessionStart and SubagentStart hooks
  for Claude Code and Codex. Codex users must review and trust the hooks.
- Default new tasks to an ignored `.agent-vault/` in the primary checkout, shared
  across worktrees. Add repository/global scope settings and a read-only `path` command.
- Keep explicit vault overrides and existing task locations. Outside Git, select
  global scope or an explicit vault. No notes or client settings are migrated.
- Separate plugin and standalone installation; document vault permissions and
  verification from both primary checkouts and linked worktrees.

### Upgrading from 0.4.0 or earlier

Update the plugin, review its hooks in Codex with `/hooks`, then start a new session.
Once automatic guidance loading is verified, remove only the old copied vault
policy from client instructions; preserve unrelated rules and explicit vault choices.
To keep the former shared default, set `OBSIDIAN_AGENT_VAULT_SCOPE=global` or
`git config --local obsidianWorkspace.scope global` in each repository.
Explicit `OBSIDIAN_AGENT_VAULT` paths continue to take precedence. Existing vault
guides are preserved; merge desired policy changes explicitly. Reopen old tasks
using their existing README paths.

### Earlier unreleased changes

- Add a task-level `decisions.md` with a decision template, README/handoff links,
  and an absolute path in helper output. Agents add a missing log when resuming
  older tasks, preserving existing decision notes.

- Shorten new task paths to `tasks/number-title-YYYY-MM-DD/`; retain full UTC timestamps
  in metadata and allocate project sequence numbers safely for concurrent agents.
- Existing task folders are preserved. Old and new naming formats may appear in
  separate groups when sorted together; resume older tasks at their original paths.
  Refresh installed guidance and merge the new naming rule into existing vault guides.

- Document default destinations for plans, worktree notes, scripts, and reports.
- Connect repository agent instructions to the shared working-file guidance.
- Document persistent vault access for both clients and continuation across worktrees.
- Refresh installed guidance and merge updates into existing vault guides explicitly;
  `init` preserves those guides.

## 0.3.0

- Make standalone `AGENTS.md` / `CLAUDE.md` guidance the primary setup.
- Keep the plugin skill and workspace helper optional.
- Remove the Claude session-start hook; no background or per-write checks run.

### Upgrading from 0.2.0

Add the guidance from `docs/agent-guidance.md` to your client instructions. Refresh
or reinstall the plugin and start a new session to stop loading the old startup
hook. The repository does not edit your global client settings. Existing vaults
and task paths are unchanged.

## 0.2.0

- Install both clients directly from the public GitHub repository.
- Use `obsidian-agent-workspace` as the marketplace name for both clients.
- Default to `~/Documents/obsidian-vault`, with an `agents/projects/.../tasks/` layout.
- Preserve support for custom vault paths, including paths containing spaces.
- Add community documentation, MIT licensing, and automated package checks.

### Upgrading from 0.1.0

The Codex catalog was previously named `personal`. Add the GitHub marketplace and
install using the README commands. If you installed `obsidian-workspace@personal`,
remove that old plugin entry after switching to avoid loading both copies. Preserve
any unrelated plugins and your existing personal marketplace.

The workspace directory was previously `Agent Workspace/`. Existing files remain
where they are; continue older tasks through their original README and handoff.
New tasks use `agents/`. The helper does not rename files, rewrite links, or replace
existing guide notes. Review your persistent client instructions for old paths.

## 0.1.0

- Shared vault skill for Claude Code and Codex.
- Python helper for creating workspaces and tasks without overwriting notes.
- Claude startup hook, task indexes, handoff templates, and Obsidian setup guide.
