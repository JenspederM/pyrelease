import pytest

from pyrelease import main
from pyrelease.commands.bump import collect_bump_mapping
from pyrelease.utils import (
    GitRepository,
    create_python_project,
    get_version_from_pyproject,
)


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


def test_bump_mapping_str_empty():
    with pytest.raises(ValueError, match="Bump mapping string cannot be empty."):
        collect_bump_mapping("")


def test_bump_mapping_str_valid():
    bump_mapping_str = "feat!:major,feat:minor,fix:patch,docs:patch"
    expected_mapping = {
        "major": ["feat!"],
        "minor": ["feat"],
        "patch": ["fix", "docs"],
    }
    result = collect_bump_mapping(bump_mapping_str)
    assert result == expected_mapping


def test_bump_mapping_str_invalid_format():
    bump_mapping_str = "feat-major,fix:patch"
    with pytest.raises(
        ValueError,
        match="Invalid bump mapping 'feat-major'. Expected format 'type:level'.",
    ):
        collect_bump_mapping(bump_mapping_str)


def test_bump_mapping_str_invalid_level():
    bump_mapping_str = "feat:invalid,fix:patch"
    with pytest.raises(
        ValueError,
        match="Invalid bump level 'invalid' in mapping 'feat:invalid'.",
    ):
        collect_bump_mapping(bump_mapping_str)


def test_bump_mapping_str_with_extra_commas():
    bump_mapping_str = "feat:minor,,fix:patch,,docs:patch,"
    expected_mapping = {
        "minor": ["feat"],
        "patch": ["fix", "docs"],
    }
    result = collect_bump_mapping(bump_mapping_str)
    assert result == expected_mapping


def test_bump_mapping_str_with_whitespace():
    bump_mapping_str = "  feat:minor , fix:patch , docs:patch  "
    expected_mapping = {
        "minor": ["feat"],
        "patch": ["fix", "docs"],
    }
    result = collect_bump_mapping(bump_mapping_str)
    assert result == expected_mapping


def test_bump_mapping_str_duplicate_types():
    bump_mapping_str = "feat:minor,feat:patch,fix:patch"
    with pytest.raises(
        ValueError,
        match="Duplicate commit type 'feat' both mapped to 'minor' and 'patch'.",
    ):
        collect_bump_mapping(bump_mapping_str)


def test_bump_command_fails():
    with pytest.raises(
        RuntimeError, match="Either --bump or --conventional must be specified"
    ):
        main(
            ["bump", "--conventional-bump-mapping", "feat:minor,fix:patch", "--dry-run"]
        )


def test_bump_command_uv_missing(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda cmd: None if cmd == "uv" else "/usr/bin/uv"
    )
    with pytest.raises(
        RuntimeError,
        match="The 'uv' command-line tool is required to run the bump command.",
    ):
        main(["bump", "--bump", "minor", "--dry-run"])


def test_bump_manual(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_manual_bump")
    create_python_project(repo_path, git=True)
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--bump",
            "minor",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version


def test_bump_manual_invalid_level(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_manual_bump_invalid")
    create_python_project(repo_path, git=True)
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "bump",
                "--bump",
                "invalid",
                "--path",
                str(repo_path),
            ]
        )
        assert exc_info.value.code == 2
        assert "invalid choice: 'invalid'" in str(exc_info.value)


def test_bump_manual_github_actions_output(tmp_path_factory, monkeypatch):
    repo_path = tmp_path_factory.mktemp("repo_manual_bump_github")
    create_python_project(repo_path, git=True)
    old_version = get_version_from_pyproject(repo_path)
    gh_output_file = repo_path / "gh_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(gh_output_file))
    main(
        [
            "bump",
            "--bump",
            "minor",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version
    with open(gh_output_file) as f:
        gh_output_content = f.read()
    assert f"old-version={old_version}" in gh_output_content
    assert f"new-version={new_version}" in gh_output_content


def test_bump_manual_dry_run(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_manual_bump_dry_run")
    create_python_project(repo_path, git=True)
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--bump",
            "minor",
            "--dry-run",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version == new_version


def test_bump_manual_multiple_release_components(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_manual_bump_multiple_levels")
    create_python_project(repo_path, git=True)
    with pytest.raises(RuntimeError, match="Only one release version component"):
        main(
            [
                "bump",
                "--bump",
                "minor",
                "--bump",
                "patch",
                "--path",
                str(repo_path),
            ]
        )


def test_bump_manual_no_release_components(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_manual_bump_no_levels")
    create_python_project(repo_path, git=True)
    with pytest.raises(
        RuntimeError, match="you also need to increase a release version component"
    ):
        main(
            [
                "bump",
                "--bump",
                "rc",
                "--path",
                str(repo_path),
            ]
        )


def test_bump_manual_additional_component(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_manual_bump_no_levels")
    create_python_project(repo_path, git=True)
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--bump",
            "minor",
            "--bump",
            "rc",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version
    assert new_version.endswith("rc1")
    new_version_main = new_version.rsplit("rc", 1)[0]
    assert_version_bump(old_version, new_version_main, "minor")


def test_bump_conventional_no_valid_commits(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_no_commits")
    create_python_project(repo_path, git=True)
    with pytest.raises(RuntimeError, match="does not have any commits yet"):
        main(
            [
                "bump",
                "--conventional",
                "--conventional-bump-mapping",
                "feat:minor,fix:patch",
                "--dry-run",
                "--path",
                str(repo_path),
            ]
        )


def test_bump_conventional(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_conventional_bump")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some conventional commits
    git.commit("feat: add new feature")
    (repo_path / "file.txt").write_text("Some content")
    git.commit("fix: fix a bug")
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--conventional",
            "--conventional-bump-mapping",
            "feat:minor,fix:patch",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version
    assert_version_bump(old_version, new_version, "minor")


def test_bump_conventional_additional_component(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_conventional_bump_additional")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some conventional commits
    git.commit("feat: add new feature")
    (repo_path / "file.txt").write_text("Some content")
    git.commit("fix: fix a bug")
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--conventional",
            "--conventional-bump-mapping",
            "feat:minor,fix:patch",
            "--bump",
            "rc",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version
    assert new_version.endswith("rc1")
    new_version_main = new_version.rsplit("rc", 1)[0]
    assert_version_bump(old_version, new_version_main, "minor")


def test_bump_conventional_dry_run(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_conventional_bump_dry_run")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some conventional commits
    git.commit("feat: add new feature")
    (repo_path / "file.txt").write_text("Some content")
    git.commit("fix: fix a bug")
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--conventional",
            "--conventional-bump-mapping",
            "feat:minor,fix:patch",
            "--dry-run",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version == new_version


def test_bump_conventional_custom_mapping(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_conventional_bump_custom_mapping")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some conventional commits
    git.commit("chore: update dependencies")
    (repo_path / "file.txt").write_text("Some content")
    git.commit("refactor: improve code structure")
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--conventional",
            "--conventional-bump-mapping",
            "chore:patch,refactor:minor",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version
    assert_version_bump(old_version, new_version, "minor")


def test_bump_conventional_no_conventional_commits(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_no_conventional_commits")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some non-conventional commits
    git.commit("Initial commit")
    (repo_path / "file.txt").write_text("Some content")
    git.commit("Update file.txt")
    with pytest.warns(
        UserWarning,
        match="No conventional commits found since the last version.",
    ):
        main(
            [
                "bump",
                "--conventional",
                "--conventional-bump-mapping",
                "feat:minor,fix:patch",
                "--dry-run",
                "--path",
                str(repo_path),
            ]
        )


def test_bump_conventional_no_tags(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_conventional_bump_no_tags")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some conventional commits
    git.commit("feat: add new feature")
    (repo_path / "file.txt").write_text("Some content")
    git.commit("fix: fix a bug")
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--conventional",
            "--conventional-bump-mapping",
            "feat:minor,fix:patch",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version
    assert_version_bump(old_version, new_version, "minor")


def test_bump_conventional_multiple_tags(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_conventional_bump_multiple_tags")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some conventional commits and tags
    git.commit("feat: add new feature")
    git.tag("v0.1.0", "First release")
    (repo_path / "file.txt").write_text("Some content")
    git.commit("fix: fix a bug")
    git.tag("v0.2.0", "Second release")
    (repo_path / "file2.txt").write_text("More content")
    git.commit("fix: another bug fix")
    old_version = get_version_from_pyproject(repo_path)
    main(
        [
            "bump",
            "--conventional",
            "--conventional-bump-mapping",
            "feat:minor,fix:patch",
            "--path",
            str(repo_path),
        ]
    )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version != new_version
    assert_version_bump(old_version, new_version, "patch")


def test_bump_conventional_no_commits_since_tag(tmp_path_factory):
    repo_path = tmp_path_factory.mktemp("repo_conventional_bump_no_commits_since_tag")
    create_python_project(repo_path, git=True)
    git = GitRepository(repo_path)
    # Create some conventional commits and a tag
    git.commit("feat: add new feature")
    git.tag("v0.1.0", "First release")
    old_version = get_version_from_pyproject(repo_path)
    with pytest.warns(
        UserWarning,
        match="No conventional commits found since the last version.",
    ):
        main(
            [
                "bump",
                "--conventional",
                "--conventional-bump-mapping",
                "feat:minor,fix:patch",
                "--dry-run",
                "--path",
                str(repo_path),
            ]
        )
    new_version = get_version_from_pyproject(repo_path)
    assert old_version == new_version
