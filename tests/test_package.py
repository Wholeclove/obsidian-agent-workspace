"""Check the distributable package without requiring either agent client."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / 'plugins/obsidian-workspace'


class PackageTests(unittest.TestCase):
    def test_catalogs_resolve_same_licensed_plugin(self):
        codex_catalog = json.loads((REPO / '.agents/plugins/marketplace.json').read_text())
        claude_catalog = json.loads((REPO / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(codex_catalog['name'], claude_catalog['name'])
        codex_entry = codex_catalog['plugins'][0]
        claude_entry = claude_catalog['plugins'][0]
        self.assertEqual((REPO / codex_entry['source']['path']).resolve(), PLUGIN)
        self.assertEqual((REPO / claude_entry['source']).resolve(), PLUGIN)
        manifests = [json.loads((PLUGIN / kind / 'plugin.json').read_text())
                     for kind in ('.codex-plugin', '.claude-plugin')]
        for manifest in manifests:
            self.assertEqual(manifest['name'], PLUGIN.name)
            self.assertEqual(manifest['license'], 'MIT')
            self.assertEqual(manifest['version'], manifests[0]['version'])
            self.assertEqual(manifest['name'], codex_entry['name'])
            self.assertEqual(manifest['name'], claude_entry['name'])
        self.assertEqual((PLUGIN / 'LICENSE').read_text(), (REPO / 'LICENSE').read_text())

    def test_helper_runs_from_standalone_install(self):
        with tempfile.TemporaryDirectory(prefix='plugin-package-test-') as temp:
            root = Path(temp).resolve()
            installed = root / 'plugin cache' / PLUGIN.name
            shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns('__pycache__'))
            helper = installed / 'scripts/vault.py'
            env = dict(os.environ, OBSIDIAN_AGENT_VAULT=str(root / 'test-vault'))
            result = subprocess.run(
                ['python3', str(helper), 'context'], cwd=root, env=env,
                capture_output=True, text=True, check=True,
            )
            self.assertIn(str(root / 'test-vault'), result.stdout)
            policy = installed / 'skills/vault-workspace/references/vault-structure.md'
            self.assertIn(policy.read_text(), result.stdout)
            self.assertIn(str(installed / 'scripts/vault.py'), result.stdout)
            self.assertFalse((root / 'test-vault').exists())
            skill = installed / 'skills/vault-workspace/SKILL.md'
            self.assertTrue(skill.is_file())
            helper = skill.parent / '../../scripts/vault.py'
            created = subprocess.run(
                ['python3', str(helper), 'task', '--project', 'package-smoke',
                 '--title', 'Installed package'],
                cwd=root, env=env, capture_output=True, text=True, check=True,
            )
            index = Path(json.loads(created.stdout)['index'])
            self.assertTrue(index.is_file())
            self.assertTrue(index.is_relative_to(root / 'test-vault'))
            registry = root / 'obsidian.json'
            registry.write_text(json.dumps({'vaults': {'installed-test': {'path': str(root / 'test-vault')}}}))
            opened = subprocess.run(
                ['python3', str(installed / 'scripts/open_vault.py'), '--task', str(index),
                 '--registry', str(registry), '--dry-run'], cwd=root, env=env,
                capture_output=True, text=True, check=True,
            )
            request = json.loads(opened.stdout)
            self.assertEqual(request['target'], str(index))
            self.assertEqual(request['registration'], 'registered')
            self.assertFalse(request['launch_requested'])
            self.assertTrue((installed / 'skills/open-vault/SKILL.md').is_file())

    def test_relative_documentation_links_resolve(self):
        paths = [*REPO.glob('*.md'), *REPO.joinpath('docs').glob('*.md'),
                 *PLUGIN.joinpath('skills').rglob('*.md')]
        for path in paths:
            for target in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                with self.subTest(document=path.relative_to(REPO), target=target):
                    self.assertTrue((path.parent / target.split('#')[0]).exists())

    def test_installed_hooks_use_event_cwd_and_do_not_write(self):
        with tempfile.TemporaryDirectory(prefix='plugin-hooks-test-') as temp:
            root = Path(temp).resolve()
            installed = root / 'plugin cache' / PLUGIN.name
            shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns('__pycache__'))
            repo = root / 'project with spaces'
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith(('OBSIDIAN_AGENT_', 'GIT_'))}
            env.update(CLAUDE_PLUGIN_ROOT=str(installed),
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
            subprocess.run(['git', 'init', str(repo)], env=env, capture_output=True, check=True)
            before = set(root.rglob('*'))
            hooks = json.loads((installed / 'hooks/hooks.json').read_text())['hooks']
            self.assertEqual(set(hooks), {'SessionStart', 'SubagentStart'})
            for name, source in [('SessionStart', s) for s in ('startup', 'resume', 'clear', 'compact')] + [('SubagentStart', None)]:
                with self.subTest(event=name, source=source):
                    group = hooks[name][0]
                    self.assertNotIn('matcher', group)  # All start sources and agent types.
                    command = group['hooks'][0]['command']
                    result = subprocess.run(command, shell=True, cwd=root, env=env,
                                            input=json.dumps({'hook_event_name': name, 'cwd': str(repo),
                                                              'source': source, 'agent_type': 'test'}),
                                            capture_output=True, text=True, check=True)
                    output = json.loads(result.stdout)['hookSpecificOutput']
                    self.assertEqual(output['hookEventName'], name)
                    context = output['additionalContext']
                    policy = installed / 'skills/vault-workspace/references/vault-structure.md'
                    self.assertIn(policy.read_text(), context)
                    self.assertIn(str(repo / '.agent-vault'), context)
                    self.assertIn(str(installed / 'scripts/vault.py'), context)
                    self.assertLess(len(context), 10000)  # Avoid Claude's large-context file indirection.
            self.assertEqual(set(root.rglob('*')), before)

    def test_hook_configuration_errors_and_bad_events(self):
        with tempfile.TemporaryDirectory(prefix='hook-errors-test-') as temp:
            root = Path(temp).resolve()
            command = ['python3', str(PLUGIN / 'scripts/session_context.py')]
            env = dict(os.environ, OBSIDIAN_AGENT_VAULT='relative/path')
            result = subprocess.run(command, cwd=root, env=env,
                                    input=json.dumps({'hook_event_name': 'SessionStart', 'cwd': str(root)}),
                                    capture_output=True, text=True, check=True)
            context = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
            self.assertIn('Vault is not configured:', context)
            self.assertIn('must be absolute', context)
            for payload in ('not json', '[]', '{}', '{"hook_event_name":"Stop"}',
                            '{"hook_event_name":"SessionStart","cwd":"relative"}'):
                result = subprocess.run(command, cwd=root, env=env, input=payload,
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertIn('obsidian-workspace:', result.stderr)
            self.assertEqual(list(root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
