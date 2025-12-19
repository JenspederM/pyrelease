import argparse
import os
import shutil
import subprocess
from argparse import _SubParsersAction

from pyrelease.utils import GitRepository, get_version_from_pyproject


def register(subparsers: _SubParsersAction):
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "bump",
        help="Bump the project version using the 'uv' tool",
    )
    parser.add_argument(
        "--bump",
        help="Type of version bump to apply",
        choices=[
            "major",
            "minor",
            "patch",
            "stable",
            "alpha",
            "beta",
            "rc",
            "post",
            "dev",
        ],
        required=False,
    )
    parser.add_argument(
        "--conventional",
        action="store_true",
        help="Use conventional commit messages to determine the version bump",
        default=False,
    )
    return parser


def execute(args: argparse.Namespace):
    if not shutil.which("uv"):
        raise RuntimeError(
            "The 'uv' command-line tool is required to run the bump command. "
            "Please install it via 'pip install uv'."
        )
    if not args.bump and not args.conventional:
        raise RuntimeError(
            "Either --bump or --conventional must be specified "
            "to determine the version bump."
        )
    if args.conventional:
        bump = determine_bump_from_conventional_commits(args)
        if bump is None:
            print(  # noqa: T201
                "No conventional commits found since the last version. "
                "Skipping version bump."
            )
            return
    else:
        bump = args.bump
    old_version = args.project_version
    bump_command = ["uv", "version", "--bump", bump]
    try:
        output = subprocess.run(
            bump_command + ["--dry-run"] if args.dry_run else bump_command,
            check=args.dry_run is False,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr.strip()) from e
    if not args.silent:
        print((output.stdout or output.stderr or "").strip())  # noqa: T201
    if not args.dry_run:
        new_version = get_version_from_pyproject(args.path)
        gh_output = os.environ.get("GITHUB_OUTPUT")
        if gh_output:
            with open(os.environ["GITHUB_OUTPUT"], "a") as gh_output_file:
                gh_output_file.write(f"old-version={old_version}\n")
                gh_output_file.write(f"new-version={new_version}\n")


def determine_bump_from_conventional_commits(args: argparse.Namespace) -> str | None:
    git = GitRepository(args.path)
    latest_tag = git.get_latest_tag()
    commits = git.get_commits_since(from_ref=latest_tag)
    bump_mapping = {
        "major": ["feat!", "fix!"],
        "minor": ["feat"],
        "patch": ["fix", "docs", "style", "refactor", "perf", "test", "chore"],
    }
    bump_level = None
    for commit in commits:
        commit_type = commit.message.split(":", 1)[0]
        for level, types in bump_mapping.items():
            if commit_type in types:
                if (
                    bump_level is None
                    or level == "major"
                    or (level == "minor" and bump_level == "patch")
                ):
                    bump_level = level
    return bump_level
