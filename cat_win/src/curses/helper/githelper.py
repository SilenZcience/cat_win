"""
githelper
"""

import os
import subprocess
from pathlib import Path


class GitHelper:
    """
    A helper class for interacting with Git repositories.
    """
    GIT_CMD_FAILED: bool = False

    @staticmethod
    def _get_repo_root(file_path: Path) -> str:
        if GitHelper.GIT_CMD_FAILED:
            raise OSError('git command previously failed, skipping git operations')

        try:
            repo_root = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=os.path.dirname(file_path) or None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            ).stdout.decode().strip()
        except subprocess.CalledProcessError as exc:
            GitHelper.GIT_CMD_FAILED = True
            raise OSError('git command failed, skipping git operations') from exc

        if not repo_root:
            raise OSError('not a git repository (or any of the parent directories)')

        return repo_root

    @staticmethod
    def _resolve_commit_target(file_path: Path, commit_hash, repo_root: str) -> tuple:
        if isinstance(commit_hash, dict):
            actual_hash = commit_hash['hash']
            file_path_at_commit = commit_hash.get('file_path')
            if not file_path_at_commit:
                file_path_at_commit = os.path.relpath(file_path, repo_root)
            return (actual_hash, file_path_at_commit)
        return (commit_hash, os.path.relpath(file_path, repo_root))

    @staticmethod
    def get_git_file_history(file_path: Path) -> list:
        """
        Get a list of all commits that changed a specific file.

        Parameters:
        file_path (Path):
            the path to the file.

        Returns:
        (list):
            A list of dictionaries, each containing:
            - 'hash': commit hash (str)
            - 'date': commit date (str)
            - 'author': commit author (str)
            - 'message': commit message (str)
            - 'file_path': path of the file at this commit (str, accounts for renames)

        Raises:
        OSError: if not in a git repository
        """
        repo_root = GitHelper._get_repo_root(file_path)

        rel_path = os.path.relpath(file_path, repo_root)

        try:
            log_output = subprocess.run(
                ['git', 'log', '--follow', '--name-status',
                    '--pretty=format:%H|%ai|%an|%s', '--', rel_path],
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            ).stdout.decode().splitlines()
        except subprocess.CalledProcessError as exc:
            GitHelper.GIT_CMD_FAILED = True
            raise OSError('git command failed, skipping git operations') from exc

        commits = []
        i = 0
        while i < len(log_output):
            line = log_output[i].strip()

            if not line or '|' not in line:
                i += 1
                continue

            parts = line.split('|', 3)
            if len(parts) != 4 or len(parts[0]) != 40:
                i += 1
                continue

            commit_hash, commit_date, commit_author, commit_message = parts
            file_path_at_commit = rel_path
            if i + 1 < len(log_output):
                status_line = log_output[i + 1].strip()
                if status_line:
                    status_parts = status_line.split('\t')
                    if len(status_parts) >= 2:
                        file_path_at_commit = status_parts[1]

            commits.append({
                'hash': commit_hash,
                'date': commit_date,
                'author': commit_author,
                'message': commit_message,
                'file_path': file_path_at_commit
            })

            i += 1

        return commits

    @staticmethod
    def get_git_file_bytes_at_commit(file_path: Path, commit_hash) -> bytes:
        """
        Get the raw bytes of a file at a specific commit.

        Parameters:
        file_path (Path):
            the path to the file.
        commit_hash (str or dict):
            either a commit hash string, or a commit dictionary from get_git_file_history()

        Returns:
        (bytes):
            the content of the file at the specified commit as raw bytes.

        Raises:
        OSError: if not in a git repository or git command fails
        """
        repo_root = GitHelper._get_repo_root(file_path)
        actual_hash, file_path_at_commit = GitHelper._resolve_commit_target(
            file_path, commit_hash, repo_root
        )

        try:
            result = subprocess.run(
                ['git', 'show', f'{actual_hash}:{file_path_at_commit}'],
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as exc:
            GitHelper.GIT_CMD_FAILED = True
            raise OSError('git command failed, skipping git operations') from exc

    @staticmethod
    def get_git_file_content_at_commit(file_path: Path, commit_hash: str) -> list:
        """
        Get the content of a file at a specific commit.

        Parameters:
        file_path (Path):
            the path to the file.
        commit_hash (str or dict):
            either a commit hash string, or a commit dictionary from get_git_file_history()

        Returns:
        (list):
            the content of the file at the specified commit as a list of lines.
            Returns empty list if the file doesn't exist at that commit.

        Raises:
        OSError: if not in a git repository
        """
        result_bytes = GitHelper.get_git_file_bytes_at_commit(file_path, commit_hash)
        return result_bytes.decode(errors='replace').splitlines()
