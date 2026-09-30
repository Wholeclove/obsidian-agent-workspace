# Verify an installation

1. Initialize a test vault using [the helper](cli.md) with an explicit test path. Open its home note in Obsidian.
2. Install and enable the plugin in one client; in Codex, review and trust it with
   `/hooks`. Alternatively, add [standalone guidance](agent-guidance.md) to client
   instructions. Grant access to the test vault as described in the README, set
   `OBSIDIAN_AGENT_VAULT` to that explicit test path, and start a fresh session.
   Do not use a real vault or overwrite existing client settings during testing.
   For the plugin path, confirm guidance loads without invoking its skill.
3. Ask: “Investigate a small problem. Put a scratch Python script, a JSON result, and a
   handoff in my vault, using project `workspace-smoke`. Give me the task index link.”
4. Confirm all three files are inside one task folder, have descriptive filenames,
   and are linked from its README. Check the handoff includes the next action and
   actual verification results, not just the goal. Source changes should remain in Git.
5. In Obsidian, open the task README and each link. Follow the non-default file setup
   guide if JSON or Python opens externally instead of in the code editor.
6. Start a fresh session in the other client and provide the task's absolute README
   path. Ask it to continue from the handoff. Confirm it reads and updates the existing
   task rather than creating an unrelated folder.
7. Start a fresh session in a task worktree. Confirm it can read the same task
   README and write a task note under the configured permissions. Ask it for a plan,
   worktree note, and review report; expect `scratch/plan.md`,
   `scratch/worktree-notes.md`, and `artifacts/` respectively, linked from the README.
   Check that a reusable source script still goes in the repository worktree.
   Ask the agent to record a decision and its rationale in `decisions.md`, then
   change that decision. Confirm it preserves and marks the old entry superseded,
   links its replacement, and links the log from the README and handoff.
8. Mark the task complete. Confirm no automatic cleanup moves or deletes its files.

## Check defaults and worktrees

In an isolated Git repository, with path and scope overrides unset, run the
installed helper’s `path` and `context` commands. Both must report
`<primary-checkout>/.agent-vault` without writing files. Repeat from a linked
worktree and a nested directory; all must resolve the same vault. Create a task
and confirm that Git ignores its notes, then resume it from the other checkout.

Set `git config --local obsidianWorkspace.scope global` and confirm both checkouts
resolve `~/Documents/obsidian-vault` (expanded). Use `--scope repository` to
override it for one helper command. Set `OBSIDIAN_AGENT_VAULT` to a test path and
confirm it wins over scope; pass `--vault` to override that environment path.
Outside Git, an unset scope must produce a diagnostic; `--scope global` or an
explicit path must work. Invalid paths/settings must not silently select a fallback.
Generated path components have no spaces; custom vault paths with spaces work.

## Check automatic guidance

Use a test client profile without copied vault policy. Start and resume a session,
then compact it; check that the session receives the bundled policy and correct
vault path each time. Ask a subagent to report its working-file conventions and
confirm the SubagentStart hook supplies the same policy. Check both clients.
Hook commands must not create files or read private vault notes at startup.
Test a linked worktree with access to the primary vault, and verify the actual
agent can read and write there under its normal sandbox/permission settings.

A manual model session is needed to evaluate instruction following. Automated
tests cover resolution, file operations, and packaged hook events; they do not
prove that every future agent action will comply. Startup hooks load guidance;
there are no per-write checks. See the task’s verification report for checks
actually run and any live-client checks still pending.
