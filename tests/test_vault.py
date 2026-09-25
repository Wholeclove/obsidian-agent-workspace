import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'plugins/obsidian-workspace/scripts/vault.py'
spec = importlib.util.spec_from_file_location('vault', SCRIPT)
vault = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vault)


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agent-vault-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Vault with spaces'

    def test_init_preserves_existing_notes(self):
        vault.init(self.root)
        note = self.root / 'Agent Workspace/Home.md'
        note.write_text('Human edits', encoding='utf-8')
        vault.init(self.root)
        self.assertEqual(note.read_text(), 'Human edits')

    def test_task_has_resolvable_handoff_and_native_file_folders(self):
        result = vault.task(self.root, 'billing-api', 'Fix "retry": error', 'codex')
        base = Path(result['task_dir'])
        self.assertTrue(base.is_relative_to(self.root))
        self.assertTrue((base / 'handoffs/latest.md').is_file())
        for folder in ('scratch', 'tmp', 'research', 'artifacts', 'logs'):
            self.assertTrue((base / folder).is_dir())
        self.assertIn('Fix \\"retry\\": error', (base / 'README.md').read_text())
        self.assertIn('%20', result['obsidian_uri'])
        self.assertEqual(self.root / result['vault_relative_index'], Path(result['index']))

    def test_parallel_tasks_do_not_collide(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: vault.task(self.root, 'app', 'Same task', 'claude'), range(8)))
        self.assertEqual(len({item['task_dir'] for item in results}), 8)
        self.assertTrue(all(Path(item['index']).is_file() for item in results))

    def test_invalid_project_rejected_before_writes(self):
        for project in ('../escape', '/absolute', 'a/b', '..', 'with space'):
            with self.assertRaises(ValueError):
                vault.task(self.root, project, 'Task', 'codex')
        self.assertFalse(self.root.exists())

    def test_symlink_cannot_redirect_workspace_outside_vault(self):
        self.root.mkdir()
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.root / 'Agent Workspace').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            vault.init(self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_cli_and_hook_context(self):
        env = {key: value for key, value in os.environ.items() if key != 'OBSIDIAN_AGENT_VAULT'}
        missing = subprocess.run([sys.executable, str(SCRIPT), 'init'], env=env, capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        context = subprocess.run([sys.executable, str(SCRIPT), 'context'], env=env, capture_output=True, text=True, check=True)
        self.assertIn('Vault is not configured', context.stdout)
        env['OBSIDIAN_AGENT_VAULT'] = str(self.root)
        created = subprocess.run([sys.executable, str(SCRIPT), 'task', '--project', 'demo', '--title', 'CLI smoke'], env=env, capture_output=True, text=True, check=True)
        self.assertTrue(Path(json.loads(created.stdout)['index']).is_file())
        context = subprocess.run([sys.executable, str(SCRIPT), 'context'], env=env, capture_output=True, text=True, check=True)
        self.assertIn(str(self.root), context.stdout)
        self.assertIn('handoffs/', context.stdout)

    def test_relative_vault_rejected(self):
        with self.assertRaises(ValueError):
            vault.vault_root('relative/path')


if __name__ == '__main__':
    unittest.main()
