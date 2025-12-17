from __future__ import annotations

import json
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


def read_pyrelease_config(path: str) -> list[str]:
    """Read pyrelease configuration from pyproject.toml and .pyrelease.toml files.

    Args:
        path (str): Path

    Returns:
        list[str]: List of command-line arguments derived from the configuration
    """
    pyproject_path = Path(f"{path}/pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found in path: {path}")
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    project_name = pyproject_data.get("project", {}).get("name")
    project_version = pyproject_data.get("project", {}).get("version")
    if not project_name or not project_version:
        raise ValueError(
            "project.name and project.version must be defined in pyproject.toml"
        )
    pyrelease_config = pyproject_data.get("tool", {}).get("pyrelease", {})
    dot_pyrelease_path = Path(f"{path}/.pyrelease.toml")
    if dot_pyrelease_path.exists():
        with open(dot_pyrelease_path, "rb") as f:
            dot_pyrelease_data = tomllib.load(f)
        pyrelease_config.update(dot_pyrelease_data.get("pyrelease", {}))
    pyrelease_config["project-name"] = project_name
    pyrelease_config["project-version"] = project_version
    return [
        f"--{key}={value}"
        for key, value in pyrelease_config.items()
        if value is not None
    ]


def get_version_from_pyproject() -> str:
    """Retrieve the version from pyproject.toml.

    Returns:
        str: Version string
    """
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data["project"]["version"]


class GitRepository:
    def __init__(self, path: str = "."):
        self.is_git_repo(path)
        self.path = path

    @staticmethod
    def is_git_repo(path: str) -> bool:
        """Check if a given path is a git repository.

        Args:
            path (str): Path to check

        Returns:
            bool: True if the path is a git repository, False otherwise
        """
        try:
            subprocess.run(
                ["git", "rev-parse"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=path,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def create_version_tag(
        self, version: str, message: str = "", format: str | None = None
    ) -> str:
        """Create a new version tag in the git repository.

        Args:
            version (str): Version string for the tag
            message (str): Tag message
            format (str | None): Format string for the tag name

        Returns:
            str: Created tag name
        """
        if format:
            version = format.format(version=version)
        else:
            version = f"v{version}"
        tag_cmd = ["git", "tag", "-a", version]
        if not message:
            message = input(f"Enter tag message for version {version}: ")
            tag_cmd.extend(["-m", message])
        subprocess.run(tag_cmd, check=True, cwd=self.path)
        return version

    def get_latest_tag(self) -> str | None:
        """Get the latest git tag in the repository.

        Returns:
            str | None: Latest git tag or None if no tags exist
        """
        try:
            tag = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                check=True,
                capture_output=True,
                text=True,
                cwd=self.path,
            ).stdout.strip()
            return tag
        except subprocess.CalledProcessError:
            return None

    def get_remote_url(self) -> str:
        """Get the remote URL of the remote origin of the git repository.

        Returns:
            str: GitHub URL of the remote origin
        """
        remote_url = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=True,
            capture_output=True,
            text=True,
            cwd=self.path,
        ).stdout.strip()
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        elif remote_url.startswith("ssh://git@"):
            remote_url = remote_url.replace("ssh://git@", "https://")
        elif remote_url.startswith("http://"):
            remote_url = remote_url.replace("http://", "https://")
        else:
            raise ValueError(
                f"Unsupported remote URL format: {remote_url}. ",
                "remote.origin.url must start with ",
                "'git@github.com:', 'ssh://git@', or 'http://'.",
            )
        return remote_url

    def get_commits_since(self, commit_id: str = "") -> list[GitCommit]:
        """Get a list of commit messages since a specific commit.

        Args:
            commit_id (str): Commit hash to get commits since, defaults to empty string (all commits)

        Returns:
            list[GitCommit]: List of commits since the specified commit
        """
        # Define the pretty format for git log output.
        # See more: https://git-scm.com/docs/pretty-formats
        remote_url = self.get_remote_url()
        commit_parts = [
            "{",
            f'"remote_url": "{remote_url}",',
            '"abbr_hash": "%h",',
            '"commit_hash": "%H",',
            '"message": "%s",',
            '"author": "%an",',
            '"author_email": "%ae",',
            '"date": "%aI",',
            '"committer_name": "%cn",',
            '"committer_email": "%ce",',
            '"committer_date": "%cI"',
            "}",
        ]
        pretty_format = "".join(commit_parts)
        if commit_id:
            commit_id = commit_id.strip()
            between = f"{commit_id}..HEAD"
            cmd = ["git", "log", between, f"--pretty=format:{pretty_format}"]
        else:
            between = ""
            cmd = ["git", "log", f"--pretty=format:{pretty_format}"]
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=self.path,
        )
        commit_strings = [
            line for line in result.stdout.strip().split("\n") if line.strip()
        ]
        commits = []
        for commit in commit_strings:
            git_commit = GitCommit(**json.loads(commit.strip()))
            commits.append(git_commit)
        return commits


@dataclass
class GitCommit:
    remote_url: str = ""
    abbr_hash: str = ""
    commit_hash: str = ""
    message: str = ""
    author: str = ""
    author_email: str = ""
    date: str = ""
    committer_name: str = ""
    committer_email: str = ""
    committer_date: str = ""
