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
        required=True,
        help="Tag message",
    )
    return parser


def execute(args: argparse.Namespace):
    git = GitRepository(args.path)
    git.create_version_tag(args.message)
