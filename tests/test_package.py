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

    def test_hook_runs_from_standalone_install_without_writing_vault(self):
        with tempfile.TemporaryDirectory(prefix='plugin-package-test-') as temp:
            root = Path(temp).resolve()
            installed = root / 'plugin cache' / PLUGIN.name
            shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns('__pycache__'))
            hooks = json.loads((installed / 'hooks/hooks.json').read_text())
            command = hooks['hooks']['SessionStart'][0]['hooks'][0]['command']
            env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(installed),
                       OBSIDIAN_AGENT_VAULT=str(root / 'test-vault'))
            result = subprocess.run(command, shell=True, cwd=root, env=env,
                                    capture_output=True, text=True, check=True)
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

    def test_relative_documentation_links_resolve(self):
        paths = [*REPO.glob('*.md'), *REPO.joinpath('docs').glob('*.md'),
                 *PLUGIN.joinpath('skills').rglob('*.md')]
        for path in paths:
            for target in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                with self.subTest(document=path.relative_to(REPO), target=target):
                    self.assertTrue((path.parent / target.split('#')[0]).exists())


if __name__ == '__main__':
    unittest.main()
