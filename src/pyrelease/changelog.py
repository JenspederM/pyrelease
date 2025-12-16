from pyrelease.git import GitCommit, GitRepository
from dataclasses import asdict

commit_template = """- {message} ([{abbr_hash}]({remote_url}/{abbr_hash}))"""


def format_commits(commits: list[GitCommit]) -> list[str]:
    """Format a list of GitCommit objects into a changelog string.

    Args:
        commits (list[GitCommit]): List of GitCommit objects

    Returns:
        list[str]: Formatted commit strings
    """
    return [commit_template.format(**asdict(commit)) for commit in commits]


def generate_changelog(repo: GitRepository, changes: list[str]) -> None:
    """Generate and print the changelog since the latest tag.

    Args:
        repo (GitRepository): Git repository instance
    """
    last_tag = repo.get_latest_tag()
    changelog_parts = [
        f"{last_tag} Changelog",
        "=========================",
        "\n".join(changes),
    ]
    return "\n".join(changelog_parts)


if __name__ == "__main__":
    repo = GitRepository(".")
    changes = format_commits(repo.get_commits_since("main"))
    print("Changes since HEAD~2:")
    changelog = generate_changelog(repo, changes)
    print(changelog)
