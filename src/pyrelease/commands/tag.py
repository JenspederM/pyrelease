import argparse
from argparse import _SubParsersAction

from pyrelease.utils import GitRepository


def register(subparsers: _SubParsersAction):
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "tag",
        help="Create a new version tag in the git repository",
    )
    parser.add_argument(
        "--message",
        type=str,
        help="Tag message",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--message-format",
        type=str,
        help="Format string for the tag message",
    )
    return parser


def execute(args: argparse.Namespace):
    if not args.message_format and not args.message:
        args.message = input("Enter tag message: ")
    git = GitRepository(args.path, dry_run=args.dry_run)
    version = f"v{args.project_version}"
    if args.message_format:
        git.tag(version, args.message_format.format(version=args.project_version))
    else:
        git.tag(version, args.message)
    if not args.silent:
        msg = args.message or args.message_format.format(version=args.project_version)
        print(  # noqa: T201
            f"Created git tag '{args.project_version}' with message: '{msg}'"
        )
