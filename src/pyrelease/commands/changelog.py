import argparse
from argparse import _SubParsersAction
from dataclasses import asdict

from pyrelease.utils import GitCommit, GitRepository

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
    changes = git.get_commits_since(args.commit or "origin/main")
    if all(isinstance(change, GitCommit) for change in changes):
        changes = format_commits(changes, args.commit_format)
    changelog = args.changelog_format.format(
        version=version,
        changes="\n".join(changes),
    )
    if not args.silent:
        print(changelog)  # noqa: T201
    if args.output:
        with open(args.output, "w") as f:
            f.write(changelog)


def format_commits(
    commits: list[GitCommit], commit_format: str | None = None
) -> list[str]:
    """Format a list of GitCommit objects into a changelog string.

    Args:
        commits (list[GitCommit]): List of GitCommit objects
        commit_format (str): Format string for each commit in the changelog

    Returns:
        list[str]: Formatted commit strings
    """

    format_str = commit_format or DEFAULT_COMMIT_FORMAT
    return [format_str.format(**asdict(commit)) for commit in commits]


def generate_changelog(
    repo: GitRepository,
    changes: list[str] | list[GitCommit],
    commit_format: str | None = None,
) -> None:
    """Generate and print the changelog since the latest tag.

    Args:
        repo (GitRepository): Git repository instance
        changes (list[str] | list[GitCommit]): List of changes
            (either formatted strings or GitCommit objects)
        commit_format (str): Format string for each commit in the changelog

    Returns:
        str: Generated changelog string
    """
    last_tag = repo.get_latest_tag()
    if all(isinstance(change, GitCommit) for change in changes):
        changes = format_commits(changes, commit_format)
    changelog_parts = [
        f"{last_tag} Changelog",
        "=========================",
        "\n".join(changes),
    ]
    return "\n".join(changelog_parts)
