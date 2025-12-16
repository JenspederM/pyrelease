from pyrelease.git import GitRepository


def cli():
    import argparse

    parser = argparse.ArgumentParser(prog="pyrelease", description="PyRelease CLI")
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the git repository (default: current directory)",
    )

    subparsers = parser.add_subparsers(dest="command")
    changelog_parser = subparsers.add_parser(
        "changelog", help="Create a changelog of commits since a specific commit"
    )
    changelog_parser.add_argument(
        "--commit",
        type=str,
        required=True,
        help="Commit hash to get commits since",
    )

    tag_parser = subparsers.add_parser("tag", help="Create a new version tag")
    tag_parser.add_argument(
        "--message",
        type=str,
        default="",
        help="Tag message (default: empty)",
    )
    return parser.parse_args()


def main():
    args = cli()
    git = GitRepository(args.path)
    if args.command == "changelog":
        git.create_changelog_since_commit(args.commit)
    elif args.command == "tag":
        git.create_version_tag(args.message)
    else:
        raise ValueError("No valid command provided. Use 'changelog' or 'tag'.")
