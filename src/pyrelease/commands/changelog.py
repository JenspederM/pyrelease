import argparse
from argparse import _SubParsersAction
from dataclasses import asdict

from pyrelease.utils import GitRepository

DEFAULT_COMMIT_FORMAT = "- {message} ([{abbr_hash}]({remote_url}/{abbr_hash}))"
DEFAULT_CHANGELOG_FORMAT = (
    "{version} Changelog\n"
    "=========================\n"
    "{changes}\n\n"
    "See all changes at: "
    "[{from_ref}..{to_ref}]({remote_url}/compare/{from_ref}...{to_ref})"
)


def register(subparsers: _SubParsersAction):
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "changelog",
        help="Create a changelog of commits since a specific commit",
    )
    parser.add_argument(
        "--from-ref",
        type=str,
        help="Commit hash to get commits since",
        default="origin/main",
    )
    parser.add_argument(
        "--to-ref",
        type=str,
        help="Commit hash to get commits to (defaults to HEAD)",
        default="HEAD",
    )
    parser.add_argument(
        "--changelog-format",
        type=str,
        help="Format string for the changelog",
        default=DEFAULT_CHANGELOG_FORMAT,
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
    latest_tag = git.get_latest_tag()
    commits = git.get_commits_since(from_ref=args.from_ref, to_ref=args.to_ref)
    format_str = args.commit_format or DEFAULT_COMMIT_FORMAT
    changes: list[str] = []
    for commit in commits:
        changes.append(format_str.format(**asdict(commit)))
    changelog = args.changelog_format.format(
        version=latest_tag,
        changes="\n".join(changes),
        remote_url=git.get_remote_url(),
        from_ref=args.from_ref,
        to_ref=args.to_ref,
    )
    if not args.silent:
        print(changelog)  # noqa: T201
    if args.output:
        with open(args.output, "w") as f:
            f.write(changelog)
