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
        required=True,
    )
    parser.add_argument(
        "--tag-format",
        type=str,
        help="Format string for the tag name",
    )
    return parser


def execute(args: argparse.Namespace):
    print(args)
    if not args.tag_format and not args.message:
        args.message = input("Enter tag message: ")
    git = GitRepository(args.path)
    git.create_version_tag(args.project_version, args.message, args.tag_format)
