from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


def read_pyrelease_config(path: str) -> dict:
    """Read pyrelease configuration from pyproject.toml and .pyrelease.toml files.

    Args:
        path (str): Path

    Returns:
        dict: Pyrelease configuration dictionary
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
    return pyrelease_config


def get_additional_args(config: dict, command_name: str) -> list[str]:
    """Convert a configuration dictionary to a list of command-line arguments.

    Args:
        config (dict): Pyrelease configuration dictionary
        command_name (str): Command name

    Returns:
        list[str]: List of command-line arguments
    """
    global_args = [
        arg.option_strings[0]
        for arg in add_global_args(argparse.ArgumentParser())._group_actions
    ]
    additional_args = config.get(command_name, {})
    for arg in global_args:
        arg_key = arg.lstrip("--")
        if arg_key in config:
            additional_args[arg_key] = config[arg_key]
    args = []
    for key, value in additional_args.items():
        arg_key = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                args.append(arg_key)
        elif isinstance(value, list):
            for item in value:
                args.append(arg_key)
                args.append(str(item))
        else:
            args.append(arg_key)
            args.append(str(value))
    return args


def add_global_args(parser: argparse.ArgumentParser):
    global_args = parser.add_argument_group("global options")
    global_args.add_argument(
        "--project-name",
        type=str,
        help="Name of the project",
    )
    global_args.add_argument(
        "--project-version",
        type=str,
        help="Version of the project",
    )
    global_args.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the git repository",
    )
    global_args.add_argument(
        "--silent",
        action="store_true",
        help="Suppress output to stdout",
        default=False,
    )
    global_args.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
        default=False,
    )
    global_args.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a trial run with no changes made",
        default=False,
    )
    return global_args


def get_version_from_pyproject(path: Path) -> str:
    """Retrieve the version from pyproject.toml.

    Args:
        path (Path): Path to the project directory

    Returns:
        str: Version string
    """
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data["project"]["version"]


class GitRepository:
    def __init__(self, path: str = ".", dry_run: bool = False):
        self.is_git_repo(path)
        self.dry_run = dry_run
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
        self,
        version: str,
        message: str = "",
    ) -> str:
        """Create a new version tag in the git repository.

        Args:
            version (str): Version string for the tag
            message (str): Tag message

        Returns:
            str: Created tag name
        """
        version = f"v{version}"
        tag_cmd = ["git", "tag", "-a", version]
        if not message:
            message = input(f"Enter tag message for version {version}: ")
            tag_cmd.extend(["-m", message])
        else:
            tag_cmd.extend(["-m", message])
        if not self.dry_run:
            try:
                subprocess.run(tag_cmd, check=True, cwd=self.path)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to create git tag '{version}': {e}") from e
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

    def get_commits_since(
        self,
        from_ref: str | None = None,
        to_ref: str = "HEAD",
    ) -> list[GitCommit]:
        """Get a list of commit messages since a specific commit.

        Args:
            from_ref (str | None): Commit hash to get commits since,
                defaults to None (all commits)
            to_ref (str): Commit hash to get commits to, defaults to HEAD

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
        if from_ref:
            from_ref = from_ref.strip()
            between = f"{from_ref}..{to_ref}"
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
