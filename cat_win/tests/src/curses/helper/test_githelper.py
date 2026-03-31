from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, Mock
import subprocess
import os

from cat_win.src.curses.helper.githelper import GitHelper


class GithelperTest(TestCase):
    def setUp(self):
        GitHelper.GIT_CMD_FAILED = False

    def tearDown(self):
        GitHelper.GIT_CMD_FAILED = False

    def test_get_repo_root_previous_failure(self):
        GitHelper.GIT_CMD_FAILED = True

        with self.assertRaises(OSError) as err:
            GitHelper._get_repo_root(Path('file.txt'))

        self.assertIn('previously failed', str(err.exception))

    @patch('subprocess.run')
    def test_get_repo_root_success(self, mock_run):
        mock_run.return_value = Mock(stdout=b'/repo/root\n')

        result = GitHelper._get_repo_root(Path('folder/file.txt'))

        self.assertEqual(result, '/repo/root')

    @patch('subprocess.run')
    def test_get_repo_root_empty(self, mock_run):
        mock_run.return_value = Mock(stdout=b'')

        with self.assertRaises(OSError) as err:
            GitHelper._get_repo_root(Path('file.txt'))

        self.assertIn('not a git repository', str(err.exception))

    @patch('subprocess.run')
    def test_get_repo_root_git_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

        with self.assertRaises(OSError) as err:
            GitHelper._get_repo_root(Path('file.txt'))

        self.assertIn('git command failed', str(err.exception))
        self.assertTrue(GitHelper.GIT_CMD_FAILED)

    def test_resolve_commit_target_dict_with_file_path(self):
        result = GitHelper._resolve_commit_target(
            Path('/repo/a/b/file.txt'),
            {'hash': 'abc123', 'file_path': 'old/path.txt'},
            '/repo'
        )

        self.assertEqual(result, ('abc123', 'old/path.txt'))

    def test_resolve_commit_target_dict_without_file_path(self):
        expected_rel = os.path.relpath('/repo/a/b/file.txt', '/repo')
        result = GitHelper._resolve_commit_target(
            Path('/repo/a/b/file.txt'),
            {'hash': 'abc123'},
            '/repo'
        )

        self.assertEqual(result, ('abc123', expected_rel))

    def test_resolve_commit_target_plain_hash(self):
        expected_rel = os.path.relpath('/repo/a/b/file.txt', '/repo')
        result = GitHelper._resolve_commit_target(
            Path('/repo/a/b/file.txt'),
            'deadbeef',
            '/repo'
        )

        self.assertEqual(result, ('deadbeef', expected_rel))

    @patch('cat_win.src.curses.helper.githelper.GitHelper._get_repo_root', return_value='/repo')
    @patch('subprocess.run')
    def test_get_git_file_history_success(self, mock_run, _):
        rel_path = os.path.relpath('/repo/src/file.txt', '/repo')
        h1 = 'a' * 40
        h2 = 'b' * 40
        mock_run.return_value = Mock(stdout=(
            f'{h1}|2024-01-01 10:00:00 +0000|User A|Msg A\n'
            f'M\t{rel_path}\n'
            'nonsense line\n'
            f'{h2}|2024-01-02 10:00:00 +0000|User B|Msg B\n'
        ).encode())

        commits = GitHelper.get_git_file_history(Path('/repo/src/file.txt'))

        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]['hash'], h1)
        self.assertEqual(commits[0]['file_path'], rel_path)
        self.assertEqual(commits[1]['hash'], h2)
        self.assertEqual(commits[1]['file_path'], rel_path)

    @patch('cat_win.src.curses.helper.githelper.GitHelper._get_repo_root', return_value='/repo')
    @patch('subprocess.run')
    def test_get_git_file_history_skips_invalid_hash_line(self, mock_run, _):
        rel_path = os.path.relpath('/repo/src/file.txt', '/repo')
        h1 = 'a' * 40
        mock_run.return_value = Mock(stdout=(
            'short-hash|2024-01-01 10:00:00 +0000|User A|Msg A\n'
            f'{h1}|2024-01-02 10:00:00 +0000|User B|Msg B\n'
        ).encode())

        commits = GitHelper.get_git_file_history(Path('/repo/src/file.txt'))

        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]['hash'], h1)
        self.assertEqual(commits[0]['file_path'], rel_path)

    @patch('cat_win.src.curses.helper.githelper.GitHelper._get_repo_root', return_value='/repo')
    @patch('subprocess.run')
    def test_get_git_file_history_git_failure(self, mock_run, _):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

        with self.assertRaises(OSError) as err:
            GitHelper.get_git_file_history(Path('/repo/src/file.txt'))

        self.assertIn('git command failed', str(err.exception))
        self.assertTrue(GitHelper.GIT_CMD_FAILED)

    @patch('cat_win.src.curses.helper.githelper.GitHelper._get_repo_root', return_value='/repo')
    @patch('subprocess.run')
    def test_get_git_file_bytes_at_commit_success(self, mock_run, _):
        mock_run.return_value = Mock(stdout=b'file-bytes')

        result = GitHelper.get_git_file_bytes_at_commit(
            Path('/repo/src/file.txt'),
            {'hash': 'abc123', 'file_path': 'src/file.txt'}
        )

        self.assertEqual(result, b'file-bytes')

    @patch('cat_win.src.curses.helper.githelper.GitHelper._get_repo_root', return_value='/repo')
    @patch('subprocess.run')
    def test_get_git_file_bytes_at_commit_git_failure(self, mock_run, _):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

        with self.assertRaises(OSError) as err:
            GitHelper.get_git_file_bytes_at_commit(Path('/repo/src/file.txt'), 'abc123')

        self.assertIn('git command failed', str(err.exception))
        self.assertTrue(GitHelper.GIT_CMD_FAILED)

    @patch('cat_win.src.curses.helper.githelper.GitHelper.get_git_file_bytes_at_commit', return_value=b'a\nb\n')
    def test_get_git_file_content_at_commit(self, _):
        result = GitHelper.get_git_file_content_at_commit(Path('/repo/src/file.txt'), 'abc123')

        self.assertEqual(result, ['a', 'b'])
