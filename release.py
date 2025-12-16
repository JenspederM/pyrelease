import subprocess

commit_id = "b2538099522380761a0a08edd00df629910be713"


def is_git_repo(path: str) -> bool:
    """Check if a given path is a git repository.

    Args:
        path (str): Path to check
    Returns:
        bool: True if the path is a git repository, False otherwise
    """
    try:
        subprocess.run(
            ["git", "rev-parse"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=path,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_commits_since(
    since_commit: str,
    repo_path: str = ".",
    remote_url: str | None = None,
) -> list[dict]:
    """Get a list of commits since a specific commit.

    Args:
        since_commit (str): Commit hash to get commits since
        repo_path (str): Path to the git repository
        remote_url (str | None): Remote URL of the git repository

    Returns:
        list[dict]: List of commits since the specified commit
    """
    format_string = "- %s (%h)"
    if remote_url is not None:
        format_string = f"- %s ({remote_url}/%h)"

    commits = (
        subprocess.run(
            [
                "git",
                "log",
                f"{since_commit}..HEAD",
                f'--pretty=format:"{format_string}"',
                "--abbrev-commit",
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=repo_path,
        )
        .stdout.strip()
        .splitlines()
    )
    commit_list = []
    for commit in commits:
        print(commit)
    return commit_list


def get_github_url(repo_path: str) -> str:
    """Get the GitHub URL of the remote origin of a git repository.

    Args:
        repo_path (str): Path to the git repository

    Returns:
        str: GitHub URL of the remote origin
    """
    remote_url = subprocess.run(
        ["git", "-C", repo_path, "config", "--get", "remote.origin.url"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    if remote_url.startswith("git@github.com:"):
        remote_url = remote_url.replace("git@github.com:", "https://github.com/")
    elif remote_url.startswith("ssh://git@"):
        remote_url = remote_url.replace("ssh://git@", "https://")
    elif remote_url.startswith("http://"):
        remote_url = remote_url.replace("http://", "https://")
    else:
        raise ValueError(
            f"Unsupported remote URL format: {remote_url}. ",
            "remote.origin.url must start with ",
            "'git@github.com:', 'ssh://git@', or 'http://'.",
        )
    return remote_url


def create_changelog_since_commit(
    commit_id: str,
    repo_path: str = ".",
) -> None:
    """Create a changelog of commits since a specific commit.

    Args:
        commit_id (str): Commit hash to get commits since
        repo_path (str): Path to the git repository
    """
    if not is_git_repo(repo_path):
        raise ValueError(f"The path '{repo_path}' is not a git repository.")
    remote_url = get_github_url(repo_path)
    commits = get_commits_since(commit_id, repo_path, remote_url)
    changelog = "\n".join(commits)
    print("Changelog since commit", commit_id)
    print(changelog)


if __name__ == "__main__":
    repo_path = "."
    if is_git_repo(repo_path):
        changelog = create_changelog_since_commit(commit_id, repo_path)
        print(changelog)
    else:
        print(f"The path '{repo_path}' is not a git repository.")
