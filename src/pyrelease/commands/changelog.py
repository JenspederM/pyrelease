import argparse
from argparse import _SubParsersAction
from dataclasses import asdict

from pyrelease.utils import GitRepository

DEFAULT_COMMIT_FORMAT = "- {message} ([{abbr_hash}]({remote_url}/{abbr_hash}))"


def register(subparsers: _SubParsersAction):
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "changelog",
        help="Create a changelog of commits since a specific commit",
    )
    parser.add_argument(
        "--commit",
        type=str,
        help="Commit hash to get commits since",
        required=False,
    )
    parser.add_argument(
        "--changelog-format",
        type=str,
        help="Format string for the changelog",
        default="{version} Changelog\n=========================\n{changes}",
    )
    parser.add_argument(
        "--commit-format",
        type=str,
        help="Format string for each commit in the changelog",
        default=DEFAULT_COMMIT_FORMAT,
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for the changelog (prints to stdout if not provided)",
        required=False,
    )
    return parser


def execute(args: argparse.Namespace):
    git = GitRepository(args.path)
    version = git.get_latest_tag()
    commits = git.get_commits_since(args.commit or "origin/main")
    format_str = args.commit_format or DEFAULT_COMMIT_FORMAT
    changes: list[str] = []
    for commit in commits:
        changes.append(format_str.format(**asdict(commit)))
    changelog = args.changelog_format.format(
        version=version,
        changes="\n".join(changes),
    )
    if not args.silent:
        print(changelog)  # noqa: T201
    if args.output:
        with open(args.output, "w") as f:
            f.write(changelog)
