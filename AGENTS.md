# Repository development

Work in a dedicated task worktree. This repository packages one shared plugin for
Claude Code and Codex; keep both manifests at the same version. Shared instructions
live in `plugins/obsidian-workspace/skills/vault-workspace/`. Avoid copying the policy
into client-specific skill files.

Run `python3 -m unittest discover -s tests -v` after changing the helper. Never use a
real user vault or overwrite client settings during tests. The helper must preserve
existing notes, support paths with spaces, reject traversal, and resolve the default
vault consistently when no override is configured. Keep client-specific install details in README.md.
