#!/usr/bin/env python3
"""Create discoverable agent workspaces inside an existing or new Obsidian vault."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import uuid
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


def task(root, project, title, owner):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', project):
        raise ValueError('Project must be a lowercase hyphenated slug, e.g. billing-api.')
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60].rstrip('-')
    if not slug:
        raise ValueError('Task title needs at least one ASCII letter or digit.')
    init(root)
    project_dir = safe_dir(root, f'agents/projects/{project}')
    create_once(project_dir / 'index.md', f'# {project}\n\nBrowse `tasks/`; task names start with a UTC timestamp.\n\n```query\npath:"agents/projects/{project}/tasks" file:README\n```\n')
    now = dt.datetime.now(dt.timezone.utc)
    task_id = f'{now:%Y%m%dT%H%M%SZ}-{slug}-{uuid.uuid4().hex[:8]}'
    base = safe_dir(root, f'agents/projects/{project}/tasks/{task_id}')
    for folder in ('scratch', 'tmp', 'research', 'artifacts', 'logs', 'handoffs'):
        safe_dir(root, str(base.relative_to(root) / folder))
    metadata = '\n'.join(f'{key}: {json.dumps(value)}' for key, value in {
        'title': title, 'project': project, 'task_id': task_id, 'status': 'active',
        'owner': owner, 'created': now.isoformat(), 'updated': now.isoformat(),
    }.items())
    create_once(base / 'README.md', f'---\n{metadata}\n---\n\n# Task\n\n## Objective\n\nDescribe the requested outcome.\n\n## Working context\n\nRecord repository, worktree, branch, issue URL, and relevant constraints.\n\n## Current state\n\nTask created; update this before pausing.\n\n## Files\n\n- [Latest handoff](handoffs/latest.md) — continuation context.\n- `scratch/` — working notes and experiments.\n- `tmp/` — disposable intermediates.\n- `research/` — findings and source links.\n- `artifacts/` — reviewable outputs and attachments.\n- `logs/` — captured command output.\n\nAdd a relative Markdown link and one-line purpose for every file worth finding again.\n')
    create_once(base / 'handoffs/latest.md', '# Handoff\n\n[Task index](../README.md)\n\n## Goal and state\n\n## Decisions and constraints\n\n## Files and evidence\n\n## Next actions\n\n## Blockers\n\n## Verification\n\nRecord commands, results, and remaining uncertainty.\n')
    relative = base.relative_to(root).as_posix()
    return {'task_dir': str(base), 'index': str(base / 'README.md'),
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
