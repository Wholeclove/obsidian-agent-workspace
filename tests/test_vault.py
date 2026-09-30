import concurrent.futures
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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
        note = self.root / 'agents/home.md'
        note.write_text('Human edits', encoding='utf-8')
        vault.init(self.root)
        self.assertEqual(note.read_text(), 'Human edits')

    def test_task_has_resolvable_handoff_and_native_file_folders(self):
        result = vault.task(self.root, 'billing-api', 'Fix "retry": error', 'codex')
        base = Path(result['task_dir'])
        self.assertTrue(base.is_relative_to(self.root))
        self.assertTrue(all(' ' not in part for part in base.relative_to(self.root).parts))
        self.assertEqual(base.relative_to(self.root).parts[:3], ('agents', 'projects', 'billing-api'))
        self.assertTrue((base / 'handoffs/latest.md').is_file())
        self.assertEqual(Path(result['decisions']), base / 'decisions.md')
        self.assertTrue(Path(result['decisions']).is_file())
        for note in [base / 'README.md', base / 'decisions.md', base / 'handoffs/latest.md']:
            links = re.findall(r'\]\(([^)]+)\)', note.read_text())
            self.assertTrue(links)
            for target in links:
                self.assertTrue((note.parent / target).is_file(), (note, target))
        for note in [base / 'README.md', base / 'handoffs/latest.md']:
            self.assertIn('decisions.md)', note.read_text())
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

    def test_short_names_sort_by_day_and_creation_order(self):
        times = [dt.datetime(2026, 9, 29, 23, 59, tzinfo=dt.timezone.utc),
                 dt.datetime(2026, 9, 29, 23, 59, 30, tzinfo=dt.timezone.utc),
                 dt.datetime(2026, 9, 30, 0, 0, tzinfo=dt.timezone.utc)]
        with patch.object(vault.dt, 'datetime') as clock:
            clock.now.side_effect = times
            results = [vault.task(self.root, 'app', title, 'codex')
                       for title in ['Zebra investigation', 'Alpha report', 'Next day']]
        paths = [Path(item['task_dir']).relative_to(self.root / 'agents/projects/app/tasks').as_posix()
                 for item in results]
        self.assertEqual(paths, ['1-zebra-investigation-2026-09-29',
                                 '2-alpha-report-2026-09-29',
                                 '3-next-day-2026-09-30'])
        self.assertEqual(sorted(paths, key=lambda name: int(name.split('-')[0])), paths)
        for result, created in zip(results, times):
            self.assertIn(created.isoformat(), Path(result['index']).read_text())

    def test_parallel_different_titles_receive_distinct_order_numbers(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda n: vault.task(self.root, 'app', f'Task {n}', 'codex'), range(12)))
        numbers = sorted(int(Path(item['task_dir']).name.split('-')[0]) for item in results)
        self.assertEqual(numbers, list(range(1, 13)))

    def test_sequence_sorts_across_999_and_preserves_old_tasks(self):
        tasks = self.root / 'agents/projects/app/tasks'
        old = tasks / '20260928T120000Z-old-task-abcdef12'
        old.mkdir(parents=True)
        note = old / 'README.md'
        note.write_text('Existing task and human edits')
        (tasks / '0999-earlier-task-2026-09-28').mkdir()
        now = dt.datetime(2026, 9, 29, tzinfo=dt.timezone.utc)
        with patch.object(vault.dt, 'datetime') as clock:
            clock.now.return_value = now
            result = vault.task(self.root, 'app', 'Next task', 'codex')
        self.assertEqual(Path(result['task_dir']).name, '1000-next-task-2026-09-29')
        self.assertLess(999, int(Path(result['task_dir']).name.split('-')[0]))
        self.assertEqual(note.read_text(), 'Existing task and human edits')

    def test_sequence_ignores_legacy_date_folders(self):
        tasks = self.root / 'agents/projects/app/tasks'
        legacy = tasks / '2026-09-29/001-older-task'
        legacy.mkdir(parents=True)
        result = vault.task(self.root, 'app', 'Readable name', 'codex')
        self.assertTrue(Path(result['task_dir']).name.startswith('1-readable-name-'))
        self.assertTrue(legacy.is_dir())

    def test_unpadded_sequence_continues_across_digit_boundaries(self):
        tasks = self.root / 'agents/projects/app/tasks'
        tasks.mkdir(parents=True)
        for number, expected in [(9, 10), (9999, 10000)]:
            (tasks / f'{number}-earlier-task-2026-09-28').mkdir()
            result = vault.task(self.root, 'app', 'Next task', 'codex')
            name = Path(result['task_dir']).name
            self.assertTrue(name.startswith(f'{expected}-next-task-'))
            self.assertFalse(name.startswith('0'))

    def test_sequence_lock_rejects_symlink(self):
        day = self.root / 'day'
        day.mkdir(parents=True)
        outside = Path(self.temp.name) / 'unrelated-note'
        outside.write_text('Preserve me')
        (day / '.sequence.lock').symlink_to(outside)
        with self.assertRaises(OSError):
            vault.reserve_task(day, 'new-task')
        self.assertEqual(outside.read_text(), 'Preserve me')

    def test_invalid_project_rejected_before_writes(self):
        for project in ('../escape', '/absolute', 'a/b', '..', 'with space'):
            with self.assertRaises(ValueError):
                vault.task(self.root, project, 'Task', 'codex')
        self.assertFalse(self.root.exists())

    def test_symlink_cannot_redirect_workspace_outside_vault(self):
        self.root.mkdir()
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.root / 'agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            vault.init(self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_cli_and_context(self):
        env = {key: value for key, value in os.environ.items() if key != 'OBSIDIAN_AGENT_VAULT'}
        context = subprocess.run([sys.executable, str(SCRIPT), '--scope', 'global', 'context'], env=env, capture_output=True, text=True, check=True)
        self.assertIn(str(Path.home() / 'Documents/obsidian-vault'), context.stdout)
        env['OBSIDIAN_AGENT_VAULT'] = str(self.root)
        created = subprocess.run([sys.executable, str(SCRIPT), 'task', '--project', 'demo', '--title', 'CLI smoke'], env=env, capture_output=True, text=True, check=True)
        self.assertTrue(Path(json.loads(created.stdout)['index']).is_file())
        context = subprocess.run([sys.executable, str(SCRIPT), 'context'], env=env, capture_output=True, text=True, check=True)
        self.assertIn(str(self.root), context.stdout)
        self.assertIn('handoffs/', context.stdout)

    def test_default_vault_and_override_precedence(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(Path, 'home', return_value=Path(self.temp.name)):
            expected = Path(self.temp.name) / 'Documents/obsidian-vault'
            self.assertEqual(vault.vault_root(scope='global'), expected.resolve())
            vault.init(vault.vault_root(scope='global'))
            self.assertTrue((expected / 'agents/home.md').is_file())
            with patch.dict(os.environ, {'OBSIDIAN_AGENT_VAULT': str(self.root)}):
                self.assertEqual(vault.vault_root(), self.root.resolve())
                explicit = Path(self.temp.name) / 'explicit'
                self.assertEqual(vault.vault_root(str(explicit)), explicit.resolve())

    def test_relative_vault_rejected(self):
        with self.assertRaises(ValueError):
            vault.vault_root('relative/path')


class RepositoryVaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='repository-vault-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / 'repository with spaces'
        self.repo.mkdir()
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('OBSIDIAN_AGENT_', 'GIT_'))}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
        self.env = patch.dict(os.environ, env, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.git('init')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-m', 'Initial')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args],
                              capture_output=True, text=True, check=True)

    def worktree(self):
        path = self.base / 'task worktree'
        self.git('worktree', 'add', '-b', 'task-test', str(path))
        return path

    def test_default_shared_across_worktrees_and_nested_directories(self):
        worktree = self.worktree()
        nested = worktree / 'nested'
        nested.mkdir()
        expected = self.repo / '.agent-vault'
        for cwd in (self.repo, worktree, nested):
            self.assertEqual(vault.vault_root(cwd=cwd), expected)
        self.assertFalse(expected.exists())

    def test_scope_settings_and_override_precedence(self):
        worktree = self.worktree()
        self.git('config', '--local', 'obsidianWorkspace.scope', 'global')
        with patch.object(Path, 'home', return_value=self.base):
            global_root = self.base / 'Documents/obsidian-vault'
            self.assertEqual(vault.vault_root(cwd=worktree), global_root)
            self.assertEqual(vault.vault_root(scope='repository', cwd=worktree), self.repo / '.agent-vault')
            with patch.dict(os.environ, {'OBSIDIAN_AGENT_VAULT_SCOPE': 'repository'}):
                self.assertEqual(vault.vault_root(cwd=worktree), self.repo / '.agent-vault')
                self.assertEqual(vault.vault_root(scope='global', cwd=worktree), global_root)
            with patch.dict(os.environ, {'OBSIDIAN_AGENT_VAULT': str(self.base / 'custom')}):
                self.assertEqual(vault.vault_root(scope='repository', cwd=worktree), self.base / 'custom')
                self.assertEqual(vault.vault_root(str(self.base / 'explicit'), cwd=worktree), self.base / 'explicit')

    def test_invalid_settings_never_fall_back(self):
        self.git('config', '--local', 'obsidianWorkspace.scope', 'typo')
        with self.assertRaises(ValueError):
            vault.vault_root(cwd=self.repo)
        with patch.dict(os.environ, {'OBSIDIAN_AGENT_VAULT_SCOPE': 'typo'}):
            with self.assertRaises(ValueError):
                vault.vault_root(cwd=self.repo)
        with patch.dict(os.environ, {'OBSIDIAN_AGENT_VAULT': '../escape'}):
            with self.assertRaises(ValueError):
                vault.vault_root(cwd=self.repo)
        self.assertFalse((self.repo / '.agent-vault').exists())

    def test_outside_git_requires_explicit_choice(self):
        with self.assertRaises(ValueError):
            vault.vault_root(cwd=self.base)
        self.assertEqual(vault.vault_root(str(self.base / 'custom'), cwd=self.base), self.base / 'custom')
        with patch.object(Path, 'home', return_value=self.base):
            self.assertEqual(vault.vault_root(scope='global', cwd=self.base), self.base / 'Documents/obsidian-vault')
        self.assertIn('Vault is not configured:', vault.context(cwd=self.base))

    def test_repository_vault_is_ignored_and_existing_ignore_is_preserved(self):
        root = vault.vault_root(cwd=self.repo)
        vault.task(root, 'demo', 'Ignored task', 'test')
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=all').stdout, '')
        ignore = root / '.gitignore'
        ignore.write_text('*\n# human note\n')
        vault.init(root)
        self.assertEqual(ignore.read_text(), '*\n# human note\n')

    def test_explicit_vault_does_not_receive_ignore_file(self):
        root = self.base / 'explicit'
        vault.init(root)
        self.assertFalse((root / '.gitignore').exists())

    def test_git_environment_cannot_redirect_repository_discovery(self):
        other = self.base / 'other'
        subprocess.run(['git', 'init', str(other)], check=True, capture_output=True)
        with patch.dict(os.environ, {'GIT_DIR': str(other / '.git'), 'GIT_WORK_TREE': str(other)}):
            self.assertEqual(vault.vault_root(cwd=self.repo), self.repo / '.agent-vault')

    def test_separate_git_directory(self):
        other = self.base / 'separate'
        subprocess.run(['git', 'init', '--separate-git-dir', str(self.base / 'metadata'), str(other)],
                       check=True, capture_output=True)
        self.assertEqual(vault.vault_root(cwd=other), other / '.agent-vault')

    def test_submodule_uses_its_own_checkout(self):
        source = self.base / 'submodule source'
        subprocess.run(['git', 'clone', str(self.repo), str(source)], check=True, capture_output=True)
        self.git('-c', 'protocol.file.allow=always', 'submodule', 'add', str(source), 'module')
        module = self.repo / 'module'
        self.assertEqual(vault.vault_root(cwd=module), module / '.agent-vault')

    def test_unlocatable_primary_with_separate_git_dir_requires_explicit_vault(self):
        other = self.base / 'separate'
        subprocess.run(['git', 'clone', '--separate-git-dir', str(self.base / 'metadata'),
                        str(self.repo), str(other)], check=True, capture_output=True)
        linked = self.base / 'separate linked'
        subprocess.run(['git', '-C', str(other), 'worktree', 'add', '-b', 'separate-test', str(linked)],
                       check=True, capture_output=True)
        # Git's first worktree entry points at metadata for this layout, not the checkout.
        with self.assertRaisesRegex(ValueError, 'Primary checkout cannot be located'):
            vault.vault_root(cwd=linked)
        self.assertEqual(vault.vault_root(str(other / '.agent-vault'), cwd=linked), other / '.agent-vault')

    def test_bare_primary_does_not_choose_a_linked_worktree_vault(self):
        bare = self.base / 'bare.git'
        subprocess.run(['git', 'clone', '--bare', str(self.repo), str(bare)], check=True, capture_output=True)
        linked = self.base / 'bare worktree'
        subprocess.run(['git', '-C', str(bare), 'worktree', 'add', '-b', 'linked-test', str(linked)], check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, 'no primary checkout'):
            vault.vault_root(cwd=linked)
        subprocess.run(['git', '-C', str(linked), 'config', '--local', 'obsidianWorkspace.scope', 'global'],
                       check=True, capture_output=True)
        with patch.object(Path, 'home', return_value=self.base):
            self.assertEqual(vault.vault_root(cwd=linked), self.base / 'Documents/obsidian-vault')

    def test_path_command_is_read_only_and_matches_context(self):
        worktree = self.worktree()
        path = subprocess.run([sys.executable, str(SCRIPT), 'path'], cwd=worktree,
                              capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(path, str(self.repo / '.agent-vault'))
        self.assertIn(path, vault.context(cwd=worktree))
        self.assertFalse(Path(path).exists())


if __name__ == '__main__':
    unittest.main()
