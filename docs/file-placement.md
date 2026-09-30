# Where agents put files

Agent working files live in one task folder in the Obsidian vault. Project
deliverables live in the repository's task worktree. This keeps task context
available after a worktree is removed and gives other agents a stable entry point.

## Where the instructions come from

| Source | Role |
| --- | --- |
| Root [AGENTS.md](../AGENTS.md) | Directs agents developing this repository to read the standalone guidance; sets this repository's project slug |
| Root [CLAUDE.md](../CLAUDE.md) | Directs Claude Code to the same repository instructions |
| [Standalone guidance](agent-guidance.md) | Complete working-file defaults; can be copied into global or project instructions without installing a plugin |
| [Shared vault policy](../plugins/obsidian-workspace/skills/vault-workspace/references/vault-structure.md) | Detailed layout, task lifecycle, navigation, and retention rules shipped in the plugin |
| [Optional skill](../plugins/obsidian-workspace/skills/vault-workspace/SKILL.md) | Reads the shared policy and explains how to run the helper |
| [Helper](../plugins/obsidian-workspace/scripts/vault.py) | Creates the folders and notes; `context` prints the resolved vault and shared policy |
| `<vault>/agents/guide.md` | Policy copied by the helper on first initialization; existing content is preserved |

Installing the plugin alone does not install persistent instructions or grant
vault access. Repository instructions travel with commits into new worktrees;
existing worktrees on older commits still have their previous instructions.
Client-specific instruction paths and access settings are in [README](../README.md).

## Defaults

Resolve the vault from an explicit user path or helper `--vault`, then
`OBSIDIAN_AGENT_VAULT`, then `~/Documents/obsidian-vault`. Each task lives at:

```text
<vault>/agents/projects/<project>/tasks/<number>-<task>-<YYYY-MM-DD>/
```

| File | Default destination |
| --- | --- |
| Decisions, rationale, alternatives, and consequences | `decisions.md` |
| Implementation plan and checklist | `scratch/plan.md` |
| Worktree setup notes and branch context | `scratch/worktree-notes.md`; record absolute paths and branches in `README.md` too |
| Exploratory or one-off scripts | `scratch/<descriptive-name>.<ext>` |
| Disposable intermediate data and downloads | `tmp/` |
| Research notes and retained source material | `research/` |
| Reports, reviews, diagrams, and outputs for sharing | `artifacts/` |
| Captured command output and test logs | `logs/` |
| Continuation summary | `handoffs/latest.md` |
| Deliverable source, tests, reusable scripts, and project documentation | Their normal paths in the repository's task worktree |

Use a task plan for working steps; put a design document or report in the repository
when it is a requested project deliverable. Keep actual Git worktrees in the
location chosen by the repository or worktree manager. Worktree notes live in the
vault so they survive worktree removal. Link useful files from the task README.

A sequence without leading zeros records creation order across the whole project. Use numeric (natural) name sorting;
plain text sorting puts `10` before `2`. The title
comes next, followed by the UTC date: `1-fix-retries-2026-09-29`, then
`2-add-tests-2026-09-30`. Full timestamps remain in task metadata. Existing task
folders retain their original paths so earlier handoffs and links continue to work.

`README.md` is the task index: objective, status, owner, repository, absolute
worktree paths, branches, and relative links to useful files. The full destination
rules are in [the standalone guidance](agent-guidance.md). Preserve extensions and
quote paths containing spaces. Explicit user destinations take precedence.

## Decisions

Each task has a root `decisions.md`, linked from its README and handoff. Agents record
what they chose, why, alternatives, consequences, date, author, status, and evidence.
Proposed ideas stay marked as proposed; replaced decisions are marked superseded
and linked to their replacements. On resuming an older task, add the log if missing
and link existing decision notes while preserving them.

## Finding the same work from another agent

1. Start at `<vault>/agents/home.md`, open the project index, and choose the task.
   For this repository the stable project slug is `obsidian-agent-workspace`.
2. Pass the absolute task README path to the next session or delegated agent,
   along with the vault root, worktree, and branch. Read the README, decisions log, and latest
   handoff before continuing.
3. Reuse the task for the same objective, including work spanning several
   worktrees. Keep independent tasks separate and use separate notes for agents
   working concurrently.
4. Verify that the new session can read and write that vault. Access to a checkout
   does not imply access to an external vault. A symlink cannot bypass permissions.
   Report missing access instead of silently changing the destination.

The helper records placeholders for working context; the agent must fill them in.
It does not detect a repository, choose a worktree location, or update client settings.

## Existing installations

Refresh installed persistent guidance when adopting these conventions. Review an
existing `agents/guide.md` and merge changes while preserving human edits; rerunning
`init` will not update it. Existing task folders and links stay where they are.

Tool-managed plans, transcripts, caches, and required build outputs may remain in
their own storage. Put a current copy of a client-managed plan in `scratch/plan.md`
when needed for handoff. No startup hook, per-write enforcement, migration, or
cleanup job runs automatically.
