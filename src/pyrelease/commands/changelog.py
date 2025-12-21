import argparse
from argparse import _SubParsersAction
from dataclasses import asdict

from pyrelease.utils import (
    CustomFormatter,
    GitCommit,
    GitRepository,
    get_version_from_pyproject,
)

DEFAULT_COMMIT_FORMAT = "- {message} ([{abbr_hash}]({remote_url}/commit/{abbr_hash}))"
DEFAULT_CHANGELOG_FORMAT = (
    "# {version}\n"
    "=========================\n"
    "{changes}\n\n"
    "See all changes at: "
    "[{from_ref}..{to_ref}]({remote_url}/compare/{from_ref}..{to_ref})"
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
        default="",
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
        "--conventional",
        action="store_true",
        help="Use conventional commit format for the changelog",
    )
    parser.add_argument(
        "--conventional-type-mapping",
        type=str,
        help="Mapping of conventional commit types to changelog sections "
        "(e.g., feat:Features,fix:Bug Fixes)",
        default="feat:Features,fix:Bug Fixes,docs:Documentation,style:Styling,",
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
    changelog = generate_changelog_increment(git, args.from_ref, args.to_ref, args)
    if not args.silent:
        print(changelog)  # noqa: T201
    if args.output:
        with open(args.output, "w") as f:
            f.write(changelog)


def generate_changelog_increment(
    git: GitRepository, from_ref: str, to_ref: str, args: argparse.Namespace
) -> None:
    commits = git.get_commits_since(from_ref=from_ref, to_ref=to_ref)
    commit_format = args.commit_format or DEFAULT_COMMIT_FORMAT
    if args.conventional:
        type_mapping = dict(
            item.split(":", 1)
            for item in args.conventional_type_mapping.split(",")
            if ":" in item
        )
        changes = generate_conventional_changelog(
            commits,
            type_mapping=type_mapping,
            commit_format=commit_format,
        )
    else:
        changes = "\n".join(
            [format_commit(commit, commit_format) for commit in commits]
        )
    changelog = format_changelog(
        changelog_format=args.changelog_format or DEFAULT_CHANGELOG_FORMAT,
        version=get_version_from_pyproject(args.path),
        changes=changes,
        remote_url=git.get_remote_url(),
        from_ref=args.from_ref,
        to_ref=args.to_ref,
    )
    return changelog


def format_commit(commit: GitCommit, commit_format: str) -> str:
    formatter = CustomFormatter(commit_format)
    mapping = asdict(commit)
    formatter.check_format_string(mapping=mapping)
    return formatter.format(**mapping)


def format_changelog(changelog_format: str, **kwargs) -> str:
    formatter = CustomFormatter(changelog_format)
    formatter.check_format_string(mapping=kwargs)
    return formatter.format(**kwargs)


def generate_conventional_changelog(
    commits: list[GitCommit],
    type_mapping: dict[str, str],
    commit_format: str,
) -> str:
    other_changes = []
    sections: dict[str, list[str]] = {section: [] for section in type_mapping.values()}
    for commit in commits:
        commit_type = commit.message.split(":", 1)[0]
        section = type_mapping.get(commit_type)
        if section:
            formatted_commit = format_commit(commit, commit_format)
            sections[section].append(formatted_commit)
        else:
            formatted_commit = format_commit(commit, commit_format)
            other_changes.append(formatted_commit)
    changelog_sections: list[str] = []
    for section, entries in sections.items():
        if entries:
            changelog_sections.append(f"### {section}\n" + "\n".join(entries))
    if other_changes:
        changelog_sections.append("### Other Changes\n" + "\n".join(other_changes))
    return "\n\n".join(changelog_sections)
