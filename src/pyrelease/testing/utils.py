import subprocess
import warnings
from pathlib import Path


def create_python_project(path: Path, git=False) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    result = subprocess.run(
        ["uv", "init", "--package", "--vcs", "none"],
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        if "is already initialized" in err:
            warnings.warn(
                f"Python project at '{path}' is already initialized.",
                UserWarning,
            )
            return
        raise RuntimeError(f"Failed to create Python project at '{path}': {err}")
    if git:
        create_git_repo(path)


def create_git_repo(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    subprocess.run(["git", "init"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )


def create_git_commit(path: Path, message: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=path, check=True)


def create_git_tag(path: Path, tag: str, message: str = "") -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    tag_cmd = ["git", "tag", "-a", tag]
    if message:
        tag_cmd.extend(["-m", message])
    else:
        tag_cmd.extend(["-m", f"Tag {tag}"])
    result = subprocess.run(
        tag_cmd, cwd=path, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        err = result.stderr.strip()
        if "already exists" in err:
            warnings.warn(
                f"Tag '{tag}' already exists at '{path}'.",
                UserWarning,
            )
            return
        raise RuntimeError(f"Failed to create git tag '{tag}' at '{path}': {err}")


def get_git_tags(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    result = subprocess.run(
        ["git", "tag", "-l"],
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to get git tags at '{path}': {result.stderr.strip()}"
        )
    tags = result.stdout.strip().splitlines()
    return tags
