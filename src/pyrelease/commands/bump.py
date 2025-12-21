import argparse
import os
import shutil
import subprocess
from argparse import _SubParsersAction
from enum import Enum

from pyrelease.utils import GitRepository, get_version_from_pyproject


class BumpLevel(Enum):
    MAJOR = 1
    MINOR = 2
    PATCH = 3
    STABLE = 4
    ALPHA = 5
    BETA = 6
    RC = 7
    POST = 8
    DEV = 9


def register(subparsers: _SubParsersAction):
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "bump",
        help="Bump the project version using the 'uv' tool",
    )
    parser.add_argument(
        "--bump",
        help="Type of version bump to apply",
        choices=[b.name.lower() for b in BumpLevel],
        required=False,
    )
    parser.add_argument(
        "--conventional",
        action="store_true",
        help="Use conventional commit messages to determine the version bump",
        default=False,
    )
    parser.add_argument(
        "--bump-mapping",
        type=str,
        help="Mapping of conventional commit types to version bumps "
        "(e.g., feat:minor,fix:patch)",
        default="feat!:major,fix!:major,feat:minor,fix:patch,docs:patch,style:patch,",
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
    bump_mapping = collect_bump_mapping(args.bump_mapping)
    highest_bump_level = None
    for commit in commits:
        commit_type = commit.message.split(":", 1)[0]
        for level, types in bump_mapping.items():
            if commit_type in types:
                if (
                    highest_bump_level is None
                    or BumpLevel[level.upper()].value
                    < BumpLevel[highest_bump_level.upper()].value
                ):
                    highest_bump_level = level
    return highest_bump_level


def collect_bump_mapping(bump_mapping_str: str) -> dict[str, list[str]]:
    if bump_mapping_str.strip() == "":
        raise ValueError("Bump mapping string cannot be empty.")
    bump_mapping = {}
    for mapping in bump_mapping_str.split(","):
        if not mapping.strip():
            continue
        check_mapping_format(mapping)
        commit_type, level = mapping.split(":")
        check_valid_level(level, mapping)
        check_no_duplicate_commit_type(bump_mapping, commit_type, level)
        bump_mapping.setdefault(level.strip(), []).append(commit_type.strip())
    return bump_mapping


def check_mapping_format(mapping: str):
    if ":" not in mapping:
        raise ValueError(
            f"Invalid bump mapping '{mapping}'. Expected format 'type:level'."
        )


def check_valid_level(level: str, mapping: str):
    if level.strip() not in [b.name.lower() for b in BumpLevel]:
        raise ValueError(f"Invalid bump level '{level}' in mapping '{mapping}'.")


def check_no_duplicate_commit_type(bump_mapping: dict, commit_type: str, level: str):
    for existing_level, commit_types in bump_mapping.items():
        if commit_type.strip() in commit_types:
            raise ValueError(
                f"Duplicate commit type '{commit_type}' both mapped to "
                f"'{existing_level}' and '{level}'."
            )
