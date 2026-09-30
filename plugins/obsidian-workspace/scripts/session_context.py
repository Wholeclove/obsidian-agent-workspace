#!/usr/bin/env python3
"""Supply bundled guidance to either client's session and subagent start hooks."""
import json
from pathlib import Path
import sys

# Avoid writing bytecode into an installed plugin cache.
sys.dont_write_bytecode = True
from vault import context


def main():
    event = json.load(sys.stdin)
    name = event.get('hook_event_name')
    if name not in ('SessionStart', 'SubagentStart'):
        raise ValueError('Expected SessionStart or SubagentStart.')
    cwd = event.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        raise ValueError('Hook cwd must be an absolute path.')
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': name,
        'additionalContext': context(cwd=cwd),
    }}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, AttributeError) as exc:
        print(f'obsidian-workspace: {exc}', file=sys.stderr)
        sys.exit(1)
