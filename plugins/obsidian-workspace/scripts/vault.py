#!/usr/bin/env python3
"""Create discoverable agent workspaces inside an existing or new Obsidian vault."""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote

PLUGIN = Path(__file__).resolve().parents[1]
POLICY = PLUGIN / 'skills/vault-workspace/references/vault-structure.md'


def vault_root(explicit=None):
    value = (
        explicit
        or os.environ.get('OBSIDIAN_AGENT_VAULT')
        or Path.home() / 'Documents/obsidian-vault'
    )
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError('Vault path must be absolute.')
    return path.resolve()


def create_once(path, content):
    try:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(content)
    except FileExistsError:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Expected a regular file: {path}')


def safe_dir(root, relative):
    target = root / relative
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes vault: {target}')
    target.mkdir(parents=True, exist_ok=True)
    return target


def init(root):
    root.mkdir(parents=True, exist_ok=True)
    agent = safe_dir(root, 'agents')
    safe_dir(root, 'agents/projects')
    create_once(agent / 'home.md', '# Agent workspace\n\nStart here. Open [[agents/guide|the vault guide]], then browse `projects/`.\nEach project has an index; each task has a README and handoff.\n\nNo automatic cleanup: completed tasks stay at stable paths.\n')
    create_once(agent / 'guide.md', POLICY.read_text(encoding='utf-8'))
    return agent


def reserve_task(tasks_dir, slug):
    """Reserve a project sequence while concurrent agents share the same vault."""
    lock_path = tasks_dir / '.sequence.lock'
    # Refuse symlinks rather than opening arbitrary files through the lock path.
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        numbers = [int(match[1]) for child in tasks_dir.iterdir()
                   if (match := re.fullmatch(r'(\d+)-.+-\d{4}-\d{2}-\d{2}', child.name))]
        number = max(numbers, default=0) + 1
        base = tasks_dir / f'{number}-{slug}'
        base.mkdir()  # Exclusive creation: never reuse another task's folder.
        return base


def task(root, project, title, owner):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', project):
        raise ValueError('Project must be a lowercase hyphenated slug, e.g. billing-api.')
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60].rstrip('-')
    if not slug:
        raise ValueError('Task title needs at least one ASCII letter or digit.')
    init(root)
    project_dir = safe_dir(root, f'agents/projects/{project}')
    create_once(project_dir / 'index.md', f'# {project}\n\nBrowse `tasks/`; tasks are numbered in creation order, with readable titles and UTC dates at the end.\n\n```query\npath:"agents/projects/{project}/tasks" file:README\n```\n')
    now = dt.datetime.now(dt.timezone.utc)
    tasks_dir = safe_dir(root, f'agents/projects/{project}/tasks')
    base = reserve_task(tasks_dir, f'{slug}-{now:%Y-%m-%d}')
    task_id = base.name
    for folder in ('scratch', 'tmp', 'research', 'artifacts', 'logs', 'handoffs'):
        safe_dir(root, str(base.relative_to(root) / folder))
    metadata = '\n'.join(f'{key}: {json.dumps(value)}' for key, value in {
        'title': title, 'project': project, 'task_id': task_id, 'status': 'active',
        'owner': owner, 'created': now.isoformat(), 'updated': now.isoformat(),
    }.items())
    create_once(base / 'README.md', f'---\n{metadata}\n---\n\n# Task\n\n## Objective\n\nDescribe the requested outcome.\n\n## Working context\n\nRecord repository, worktree, branch, issue URL, and relevant constraints.\n\n## Current state\n\nTask created; update this before pausing.\n\n## Files\n\n- [Decisions](decisions.md) — choices, rationale, and changes of direction.\n- [Latest handoff](handoffs/latest.md) — continuation context.\n- `scratch/` — working notes and experiments.\n- `tmp/` — disposable intermediates.\n- `research/` — findings and source links.\n- `artifacts/` — reviewable outputs and attachments.\n- `logs/` — captured command output.\n\nAdd a relative Markdown link and one-line purpose for every file worth finding again.\n')
    create_once(base / 'decisions.md', """# Decisions

[Task index](README.md)

Record meaningful decisions as they are made. Append dated entries, preserve earlier
reasoning, and mark replaced decisions as superseded with a link to the new entry.

No decisions recorded yet.

<!-- Copy this template for each decision; replace the placeholders.
## YYYY-MM-DD — Short decision title

- Status: proposed / accepted / superseded
- Author: agent or person recording the decision
- Decision: what was chosen
- Rationale: why it was chosen and which constraints mattered
- Alternatives: options considered and why they were not chosen
- Consequences: tradeoffs, risks, and follow-up work
- Evidence: links to relevant notes, code, tests, or user direction
-->
""")
    create_once(base / 'handoffs/latest.md', '# Handoff\n\n[Task index](../README.md)\n\n## Goal and state\n\n## Decisions and constraints\n\nSee the [decision log](../decisions.md). Summarize active constraints here.\n\n## Files and evidence\n\n## Next actions\n\n## Blockers\n\n## Verification\n\nRecord commands, results, and remaining uncertainty.\n')
    relative = base.relative_to(root).as_posix()
    return {'task_dir': str(base), 'index': str(base / 'README.md'),
            'decisions': str(base / 'decisions.md'),
            'vault_relative_index': relative + '/README.md',
            'obsidian_uri': 'obsidian://open?path=' + quote(str(base / 'README.md'), safe=''),
            'tmpdir': str(base / 'tmp')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--vault',
        help='Absolute vault root; defaults to OBSIDIAN_AGENT_VAULT or ~/Documents/obsidian-vault',
    )
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init', help='Add the agents folder without replacing existing notes')
    new = sub.add_parser('task', help='Create a unique task with index and handoff')
    new.add_argument('--project', required=True)
    new.add_argument('--title', required=True)
    new.add_argument('--owner', default='unassigned')
    sub.add_parser('context', help='Print the vault path and working policy; does not write files')
    args = parser.parse_args()
    if args.command == 'context':
        try:
            root = vault_root(args.vault)
            location = f'Configured vault root: {root}'
        except ValueError as exc:
            location = f'Vault is not configured: {exc} Ask the user for its path before writing temporary files.'
        print(location)
        print(f'Workspace helper: {Path(__file__).resolve()}')
        print(POLICY.read_text(encoding='utf-8'))
        return
    root = vault_root(args.vault)
    if args.command == 'init':
        print(init(root))
    else:
        print(json.dumps(task(root, args.project, args.title, args.owner), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(f'vault: {exc}', file=sys.stderr)
        sys.exit(1)
