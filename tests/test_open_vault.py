"""Opening a vault must select the right task without modifying app state."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from urllib.parse import parse_qs, urlparse

SCRIPTS = Path(__file__).resolve().parents[1] / 'plugins/obsidian-workspace/scripts'
spec = importlib.util.spec_from_file_location('open_vault', SCRIPTS / 'open_vault.py')
opener = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(SCRIPTS))
try:
    spec.loader.exec_module(opener)
finally:
    sys.path.pop(0)


class OpenVaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='open-vault-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'Vault with spaces & unicode é'
        self.note = self.root / 'agents/projects/demo/tasks/old-session/README.md'
        self.note.parent.mkdir(parents=True)
        self.note.write_text('Existing task')
        self.registry = self.base / 'obsidian.json'
        self.registry.write_text(json.dumps({'vaults': {
            'wrong-vault-id': {'path': str(self.base / 'elsewhere' / self.root.name)},
            'right-vault-id': {'path': str(self.root)},
        }}))

    def request(self, **kwargs):
        return opener.open_request(registry=str(self.registry), **kwargs)

    def test_current_task_wins_over_new_default_and_duplicate_vault_names(self):
        with patch.dict(os.environ, {'OBSIDIAN_AGENT_VAULT': str(self.base / 'new default')}):
            result = self.request(task=str(self.note), scope='repository')
        self.assertEqual(result['vault'], str(self.root))
        self.assertEqual(result['target'], str(self.note))
        self.assertEqual(result['registration'], 'registered')
        params = parse_qs(urlparse(result['uri']).query)
        self.assertEqual(params, {'vault': ['right-vault-id'],
                                 'file': ['agents/projects/demo/tasks/old-session/README.md']})
        self.assertFalse(result['launch_requested'])

    def test_custom_task_layout_with_explicit_vault_and_encoded_file(self):
        note = self.root / 'Older layout #1 & é/README.md'
        note.parent.mkdir(); note.write_text('Preserve legacy task')
        result = self.request(explicit=str(self.root), task=str(note))
        self.assertIn('%20', result['uri'])
        self.assertIn('%23', result['uri'])
        self.assertIn('%26', result['uri'])
        self.assertEqual(parse_qs(urlparse(result['uri']).query)['file'],
                         ['Older layout #1 & é/README.md'])

    def test_default_opens_home_or_bare_vault_without_creating_notes(self):
        with patch.object(opener, 'vault_root', return_value=self.root) as resolve:
            result = self.request(cwd=self.base, scope='repository')
        resolve.assert_called_once_with(scope='repository', cwd=self.base)
        self.assertEqual(parse_qs(urlparse(result['uri']).query), {'vault': ['right-vault-id']})
        home = self.root / 'agents/home.md'; home.write_text('Home')
        result = self.request(explicit=str(self.root))
        self.assertEqual(result['target'], str(home))
        self.assertEqual(parse_qs(urlparse(result['uri']).query)['file'], ['agents/home.md'])

    def test_unregistered_or_unreadable_registry_uses_picker_without_writes(self):
        for raw, expected in [('{}', 'unknown'), ('not json', 'unknown'),
                              ('{"vaults": []}', 'unknown'), ('{"vaults": {}}', 'unregistered')]:
            with self.subTest(raw=raw):
                self.registry.write_text(raw)
                before = {p: p.read_bytes() for p in self.base.rglob('*') if p.is_file()}
                result = self.request(task=str(self.note))
                self.assertEqual(result['registration'], expected)
                self.assertEqual(result['uri'], 'obsidian://choose-vault')
                self.assertIn(str(self.root), result['instruction'])
                self.assertEqual(before, {p: p.read_bytes() for p in self.base.rglob('*') if p.is_file()})
        self.registry.unlink()
        self.assertEqual(self.request(task=str(self.note))['registration'], 'unknown')
        self.assertFalse(self.registry.exists())

    def test_bad_paths_and_conflicting_vault_do_not_fall_back(self):
        for args in [dict(task='relative/README.md'), dict(task=str(self.base / 'missing/README.md')),
                     dict(explicit=str(self.base / 'missing')), dict(explicit='relative'),
                     dict(explicit=str(self.base / 'other'), task=str(self.note))]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.request(**args)
        other = self.base / 'other'; other.mkdir()
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.request(explicit=str(other), task=str(self.note))
        self.assertEqual(self.note.read_text(), 'Existing task')

    def test_symlink_cannot_open_note_outside_selected_vault(self):
        outside = self.base / 'README.md'; outside.write_text('Outside')
        self.note.unlink(); self.note.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.request(explicit=str(self.root), task=str(self.note))
        home = self.root / 'agents/home.md'; home.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.request(explicit=str(self.root))

    def test_launch_uses_argument_list_and_reports_failures(self):
        uri = 'obsidian://open?vault=some-id&file=note%20name'
        for platform, command in [('darwin', 'open'), ('linux', 'xdg-open')]:
            with patch.object(opener.sys, 'platform', platform), \
                 patch.object(opener.subprocess, 'run') as run:
                run.return_value = subprocess.CompletedProcess([], 0, '', '')
                opener.launch(uri)
                run.assert_called_once_with([command, uri], capture_output=True, text=True, timeout=15)
                run.return_value = subprocess.CompletedProcess([], 1, '', 'No URI handler')
                with self.assertRaisesRegex(ValueError, 'No URI handler'):
                    opener.launch(uri)
                run.side_effect = FileNotFoundError()
                with self.assertRaisesRegex(ValueError, 'unavailable'):
                    opener.launch(uri)

    def test_registry_location_matches_platform_and_xdg_config(self):
        with patch.object(Path, 'home', return_value=self.base):
            with patch.object(opener.sys, 'platform', 'darwin'):
                self.assertEqual(opener.registry_path(), self.base / 'Library/Application Support/obsidian/obsidian.json')
            with patch.object(opener.sys, 'platform', 'linux'), \
                 patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.base / 'custom config')}):
                self.assertEqual(opener.registry_path(), self.base / 'custom config/obsidian/obsidian.json')

    def test_launch_failure_keeps_uri_and_reports_no_success(self):
        args = ['open_vault.py', '--task', str(self.note), '--registry', str(self.registry)]
        stream = io.StringIO()
        with patch.object(sys, 'argv', args), patch.object(opener, 'launch', side_effect=ValueError('No handler')), \
             redirect_stdout(stream):
            self.assertEqual(opener.main(), 1)
        result = json.loads(stream.getvalue())
        self.assertFalse(result['launch_requested'])
        self.assertEqual(result['error'], 'No handler')
        self.assertTrue(result['uri'].startswith('obsidian://open?'))

    def test_dry_run_cli_does_not_launch(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'open_vault.py'), '--task', str(self.note),
                                 '--registry', str(self.registry), '--dry-run'],
                                capture_output=True, text=True, check=True, cwd=self.base)
        data = json.loads(result.stdout)
        self.assertFalse(data['launch_requested'])
        self.assertEqual(data['registration'], 'registered')
        self.assertEqual(self.note.read_text(), 'Existing task')


if __name__ == '__main__':
    unittest.main()
