# Contributing

Report bugs and propose changes through
[GitHub issues](https://github.com/Wholeclove/obsidian-agent-workspace/issues).
For a bug, include the client and Python versions, operating system, command or
prompt, expected behavior, and actual result. Use a minimal example and remove
private vault content from logs.

## Development setup

```sh
git clone https://github.com/Wholeclove/obsidian-agent-workspace.git
cd obsidian-agent-workspace
git worktree add ../obsidian-agent-workspace-dev -b your-change
cd ../obsidian-agent-workspace-dev
python3 -m unittest discover -s tests -v
```

The helper and tests use only the Python standard library. Work in a dedicated
worktree, and keep test vaults separate from your real notes. CI runs the suite on
Linux and macOS with Python 3.10 and 3.13.

## Repository layout

| Path | Purpose |
| --- | --- |
| `.agents/plugins/marketplace.json` | Codex marketplace catalog |
| `.claude-plugin/marketplace.json` | Claude Code marketplace catalog |
| `plugins/obsidian-workspace/` | Self-contained plugin for both clients |
| `plugins/obsidian-workspace/skills/vault-workspace/` | Shared skill and vault policy |
| `plugins/obsidian-workspace/scripts/vault.py` | Workspace initialization and task creation |
| `plugins/obsidian-workspace/hooks/hooks.json` | Claude session-start context hook |
| `tests/` | Helper behavior and package integration tests |

Keep the policy in the shared skill. Client-specific manifests should identify the
same plugin version. The plugin's copy of `LICENSE` travels with installed packages
and must match the root license.

## Check a change

Run the unit and package integration tests. When Claude Code is available, also run:

```sh
claude plugin validate .
claude plugin validate ./plugins/obsidian-workspace
claude --plugin-dir ./plugins/obsidian-workspace
```

For Codex development, add this checkout as a local marketplace and install
`obsidian-workspace@obsidian-agent-workspace`. Use a separate client profile if you
already installed the GitHub marketplace with that name. Start a fresh thread after
changing the installed skill.

Follow [the walkthrough](docs/walkthrough.md) for behavior that requires an actual
agent or Obsidian. Automated tests verify file operations and startup context;
they cannot establish that a model follows every instruction or that the Obsidian
UI works. Report which checks you ran and which you could not run in your PR.

Preserve existing notes and links. New path conventions need explicit upgrade
notes; never migrate or delete a user's vault silently. Add focused tests for
behavioral changes, and update the relevant documentation and changelog.
