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
        raise RuntimeError(
            f"Failed to create Python project at '{path}': {err}"
        )  # pragma: no cover - dont know how to trigger this in tests
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
        raise RuntimeError(
            f"Failed to create git tag '{tag}' at '{path}': {err}"
        )  # pragma: no cover - dont know how to trigger this in tests


def get_git_tags(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist.")
    result = subprocess.run(
        ["git", "tag", "-l", "-n99"],
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to get git tags at '{path}': {result.stderr.strip()}"
        )
    tags = [
        [part.strip() for part in line.split(" ", 1)]
        for line in result.stdout.strip().splitlines()
        if line
    ]
    return tags


def assert_version_bump(old_version: str, new_version: str, expected_bump: str) -> None:
    old_parts = list(map(int, old_version.split(".")))
    new_parts = list(map(int, new_version.split(".")))

    if expected_bump == "major":
        assert new_parts[0] == old_parts[0] + 1
        assert new_parts[1] == 0
        assert new_parts[2] == 0
    elif expected_bump == "minor":
        assert new_parts[0] == old_parts[0]
        assert new_parts[1] == old_parts[1] + 1
        assert new_parts[2] == 0
    elif expected_bump == "patch":
        assert new_parts[0] == old_parts[0]
        assert new_parts[1] == old_parts[1]
        assert new_parts[2] == old_parts[2] + 1
    else:
        raise ValueError(f"Unknown expected bump type: {expected_bump}")
