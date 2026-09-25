# Verify an installation

1. Initialize a test vault using the README commands. Open its Home note in Obsidian.
2. Install one client plugin and apply the persistent instruction block. Set the vault
   environment variable or provide its path in your instructions. Start a fresh session.
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
7. Mark the task complete. Confirm no automatic cleanup moves or deletes its files.

For missing configuration, run `python3 plugins/obsidian-workspace/scripts/vault.py
context` without the vault variable: it must explain that the vault path is missing,
not silently select a scratch directory. `init` and `task` must fail without a path.

A manual model session is needed to evaluate instruction following. Automated tests
cover the helper and hook output; they do not prove that every future agent action
will comply. Hooks and skills do not intercept arbitrary filesystem writes.
