from __future__ import annotations

import argparse
import json
import shutil
import string
import subprocess
import tomllib
import warnings
from dataclasses import dataclass
from pathlib import Path


def create_python_project(path: Path, git=False) -> None:
    """Create a new Python project at the specified path.

    Args:
        path (Path): Path to create the Python project
        git (bool): Whether to initialize a git repository
    """
    if not shutil.which("uv"):
        raise RuntimeError(
            "The 'uv' command-line tool is required to create a Python project. "
            "Please install it via 'pip install uv'."
        )
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    result = subprocess.run(
        ["uv", "init", "--package", "--vcs", "none"],
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        if "is already initialized" in err:
            warnings.warn(
                f"Python project at '{path}' is already initialized.",
                UserWarning,
            )
            return
        raise RuntimeError(
            f"Failed to create Python project at '{path}': {err}"
        )  # pragma: no cover - dont know how to trigger this in tests
    if git:
        GitRepository(path, init=True)


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


def get_configured_args(config: dict, command_name: str) -> list[str]:
    """Get additional command-line arguments from the pyrelease configuration.

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
        if arg_key in config and arg_key not in additional_args:
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


def add_global_args(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    """Add global arguments to the parser.

    Args:
        parser (argparse.ArgumentParser): Argument parser

    Returns:
        argparse._ArgumentGroup: The global arguments group
    """
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
        type=Path,
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
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    pyproject_path = path / "pyproject.toml"
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found in path: {path}")
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    try:
        return pyproject_data["project"]["version"]
    except KeyError:
        raise ValueError("project.version not found in pyproject.toml") from None


class CustomFormatter(string.Formatter):
    def __init__(self, string=None):
        """Custom string formatter to extract keys from format strings.

        Args:
            string (str | None): Format string to analyze.
        """
        super().__init__()
        self._string = string

    def get_keys(self, format_string=None):
        """Get the set of keys used in the format string.

        Args:
            format_string (str | None): Format string to analyze.
                If None, uses the instance's string.

        Returns:
            set: Set of keys used in the format string.
        """
        if format_string is None:
            if self._string is None:
                raise ValueError("No format string provided.")
            format_string = self._string
        return {item[1] for item in self.parse(format_string) if item[1] is not None}

    def format(self, /, *args, **kwargs) -> str:
        if self._string is None:
            raise ValueError("No format string provided.")
        return super().format(self._string, *args, **kwargs)

    def check_format_string(self, mapping: dict, format_string=None):
        """Check if the format string contains unsupported keys.

        Args:
            mapping (dict): Mapping of supported keys.
            format_string (str | None): Format string to analyze.
                If None, uses the instance's string.

        Raises:
            ValueError: If unsupported keys are found in the format string.
        """
        if format_string is None:
            if self._string is None:
                raise ValueError("No format string provided.")
            format_string = self._string
        if not mapping:
            raise ValueError("No mapping provided to check format string against.")
        keys = self.get_keys(format_string=format_string)
        valid_keys = set(mapping.keys())
        unsupported_keys = keys - valid_keys
        if unsupported_keys:
            err = [
                "Found invalid keys in format string:",
                ", ".join(f"'{key}'" for key in unsupported_keys) + ".\n",
                "Valid keys are:",
                ", ".join(f"'{key}'" for key in valid_keys) + ".",
            ]
            raise ValueError(" ".join(err))


class GitRepository:
    def __init__(
        self,
        path: Path = Path("."),
        init=False,
        init_user=None,
        init_email=None,
        dry_run: bool = False,
    ):
        if not Path(path).exists():
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        self.path = path
        self.dry_run = dry_run
        if init and not self._is_git_repo():
            self.init(
                user=init_user or "PyRelease",
                email=init_email or "pyrelease@example.com",
            )

    def _is_git_repo(self) -> bool:
        """Check if a given path is a git repository.

        Args:
            path (str): Path to check

        Returns:
            bool: True if the path is a git repository, False otherwise
        """
        result = self._run_git_command(["rev-parse"])
        return result.returncode == 0

    def _run_git_command(
        self, command: list[str], check: bool = False
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command in the repository.

        Args:
            command (list[str]): Git command and arguments
            check (bool): Whether to raise an exception on non-zero exit

        Returns:
            subprocess.CompletedProcess: Completed process object
        """
        result = subprocess.run(
            ["git"] + command,
            check=check,
            capture_output=True,
            text=True,
            cwd=self.path,
        )
        return result

    def init(self, user: str = "PyRelease", email: str = "pyrelease@example.com"):
        """Initialize a git repository at the specified path.

        Args:
            user (str): Git user name
            email (str): Git user email
        """
        self._run_git_command(["init"], check=True)
        self._run_git_command(["config", "user.name", user], check=True)
        self._run_git_command(["config", "user.email", email], check=True)

    def commit(self, message: str) -> str:
        """Create a new git commit in the repository.

        Args:
            message (str): Commit message

        Returns:
            str: Created commit hash
        """
        self._run_git_command(["add", "."], check=True)
        self._run_git_command(["commit", "-m", message], check=True)
        result = self._run_git_command(["rev-parse", "--short", "HEAD"], check=True)
        commit_hash = result.stdout.strip()
        return commit_hash

    def tag(self, tag: str, message: str = "") -> None:
        """Create a new git tag in the repository.

        Args:
            tag (str): Tag name
            message (str): Tag message

        Raises:
            RuntimeError: If tag creation fails for reasons other than existing tag
        """
        tag_cmd = ["tag", "-a", tag]
        if message:
            tag_cmd.extend(["-m", message])
        else:
            tag_cmd.extend(["-m", f"Tag {tag}"])
        if self.dry_run:
            return
        result = self._run_git_command(tag_cmd)
        if result.returncode != 0:
            err = result.stderr.strip()
            if "already exists" in err:
                warnings.warn(
                    f"Tag '{tag}' already exists at '{self.path}'.",
                    UserWarning,
                )
                return
            raise RuntimeError(
                f"Failed to create git tag '{tag}' at '{self.path}': {err}"
            )  # pragma: no cover - dont know how to trigger this in tests

    def get_tags(self, latest: bool = False) -> list[list[str]]:
        """Get a list of git tags in the repository.

        Args:
            latest (bool): Whether to return only the latest tag

        Returns:
            list[list[str]]: List of git tags with their messages
        """
        result = self._run_git_command(
            ["tag", "-l", "--format=%(refname:short) %(contents)"]
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to get git tags at '{self.path}': {result.stderr.strip()}"
            )  # pragma: no cover - dont know how to trigger this in tests
        tags = [
            [part.strip() for part in line.split(" ", 1)]
            for line in result.stdout.strip().splitlines()
            if line
        ]
        if latest and tags:
            return [tags[0]]
        return tags

    def get_remote_url(self) -> str | None:
        """Get the remote URL of the remote origin of the git repository.

        Returns:
            str | None: GitHub URL of the remote origin or None if not set
        """
        result = self._run_git_command(["config", "--get", "remote.origin.url"])
        if result.returncode != 0:
            warnings.warn(
                f"Failed to get remote URL for git repository at '{self.path}': "
                f"{result.stderr.strip()}",
                UserWarning,
            )
            return None

        remote_url = result.stdout.strip()
        if not remote_url.startswith(
            (
                "https://",
                "git@github.com:",
                "http://",
            )
        ):
            raise ValueError(
                f"Unsupported remote URL format: '{result.stdout.strip()}'. "
                "remote.origin.url must start with 'git@github.com:' or 'https://'.",
            )

        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        if remote_url.startswith("git@github.com:"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        elif remote_url.startswith("http://"):
            remote_url = remote_url.replace("http://", "https://")

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
            f'"remote_url": "{remote_url}",' if remote_url else None,
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
        commit_parts = [part for part in commit_parts if part is not None]
        pretty_format = "".join(commit_parts)
        between = "" if not from_ref else f"{from_ref}..{to_ref}"
        if from_ref:
            cmd = ["git", "log", between, f"--pretty=format:{pretty_format}"]
        else:
            cmd = ["git", "log", f"--pretty=format:{pretty_format}"]
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd=self.path,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to get git commits for range '{between}': "
                f"{result.stderr.strip()}"
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
