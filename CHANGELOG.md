# Changelog

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
