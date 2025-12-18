import argparse
import os
import shutil
import subprocess
from argparse import _SubParsersAction

from pyrelease.utils import get_version_from_pyproject


def register(subparsers: _SubParsersAction):
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "bump",
        help="Bump the project version using the 'uv' tool",
    )
    parser.add_argument(
        "BUMP",
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
    )
    parser.add_argument(
        "--version-files",
        type=str,
        nargs="*",
        help="List of version files to update",
        required=False,
    )
    parser.set_defaults(func=execute)
    return parser


def execute(args: argparse.Namespace):
    if not shutil.which("uv"):
        raise RuntimeError(
            "The 'uv' command-line tool is required to run the bump command. "
            "Please install it via 'pip install uv'."
        )
    old_version = args.project_version
    bump_command = ["uv", "version", "--bump", args.BUMP]
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
                gh_output_file.write(f"old_version={old_version}\n")
                gh_output_file.write(f"new_version={new_version}\n")
