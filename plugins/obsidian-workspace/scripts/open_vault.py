#!/usr/bin/env python3
"""Request that Obsidian open the current task or configured vault."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode, quote

sys.dont_write_bytecode = True
from vault import vault_root


def absolute_path(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError('Use an absolute path (or a path beginning with ~).')
    return path.resolve()


def task_root(note):
    for parent in note.parents:
        if parent.name == 'agents' and note.is_relative_to(parent / 'projects'):
            return parent.parent
    raise ValueError('Cannot infer this task\'s vault. Supply its absolute --vault path too.')


def registry_path():
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/obsidian/obsidian.json'
    if sys.platform.startswith('linux'):
        config = os.environ.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')
        return absolute_path(config) / 'obsidian/obsidian.json'
    raise ValueError('Opening vaults is supported on macOS and Linux.')


def registration(root, registry):
    """Read only: Obsidian owns this file and may update it while running."""
    try:
        data = json.loads(registry.read_text(encoding='utf-8'))
        entries = data['vaults']
        if not isinstance(entries, dict):
            raise ValueError('Expected a vault map.')
        for vault_id, item in entries.items():
            if not isinstance(item, dict) or not isinstance(item.get('path'), str):
                raise ValueError('Invalid vault entry.')
            if absolute_path(item['path']) == root:
                return 'registered', vault_id
        return 'unregistered', None
    except (OSError, ValueError, KeyError, TypeError):
        return 'unknown', None


def open_request(explicit=None, scope=None, task=None, registry=None, cwd=None):
    note = absolute_path(task) if task else None
    if note and (note.name != 'README.md' or not note.is_file()):
        raise ValueError('--task must name an existing task README.md.')
    # A resumed task may live in a different vault than today's configured default.
    root = (absolute_path(explicit) if explicit else
            task_root(note) if note else vault_root(scope=scope, cwd=cwd))
    if not root.is_dir():
        raise ValueError(f'Vault directory does not exist: {root}. Initialize it before opening.')
    if note and not note.is_relative_to(root):
        raise ValueError('The task README is outside the selected vault.')
    if note is None:
        home = root / 'agents/home.md'
        if home.is_file():
            note = home.resolve()
            if not note.is_relative_to(root):
                raise ValueError('The home note points outside the selected vault.')
    state, vault_id = registration(root, absolute_path(registry) if registry else registry_path())
    if state == 'registered':
        params = {'vault': vault_id}
        if note:
            params['file'] = note.relative_to(root).as_posix()
        uri = 'obsidian://open?' + urlencode(params, quote_via=quote, safe='')
        instruction = 'Open request prepared; an OS launch does not verify the Obsidian window.'
    else:
        uri = 'obsidian://choose-vault'
        instruction = (f'In Obsidian, choose Open folder as vault and select {root}, '
                       'then rerun this command. If the picker does not appear, open it '
                       'from Obsidian\'s vault switcher. No registry or vault files were changed.')
        if state == 'unknown':
            instruction = ('Could not read the vault registry; registration is unverified. '
                           'For a custom Obsidian profile, pass --registry. ' + instruction)
    return {'vault': str(root), 'target': str(note) if note else str(root),
            'registration': state, 'uri': uri, 'launch_requested': False,
            'instruction': instruction}


def launch(uri):
    if sys.platform == 'darwin':
        command = ['open', uri]
    elif sys.platform.startswith('linux'):
        command = ['xdg-open', uri]
    else:
        raise ValueError('Opening vaults is supported on macOS and Linux.')
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    except FileNotFoundError as exc:
        raise ValueError(f'{command[0]} is unavailable; open the returned URI on your desktop.') from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Desktop launcher timed out; check Obsidian before retrying.') from exc
    if result.returncode:
        raise ValueError(f'Desktop launcher failed: {result.stderr.strip() or result.stdout.strip()}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', help='Explicit absolute vault path')
    parser.add_argument('--scope', choices=('repository', 'global'))
    parser.add_argument('--task', help='Absolute README path of the active task; takes precedence over defaults')
    parser.add_argument('--registry', help='Alternate Obsidian obsidian.json path; read only')
    parser.add_argument('--dry-run', action='store_true', help='Resolve paths and show the request without launching')
    args = parser.parse_args()
    request = open_request(args.vault, args.scope, args.task, args.registry)
    if not args.dry_run:
        try:
            launch(request['uri'])
        except ValueError as exc:
            request['error'] = str(exc)
            print(json.dumps(request, indent=2))
            return 1
        request['launch_requested'] = True
    print(json.dumps(request, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f'open-vault: {exc}', file=sys.stderr)
        sys.exit(1)
