import pytest

from pyrelease.testing.utils import (
    assert_version_bump,
    create_git_commit,
    create_git_repo,
    create_git_tag,
    create_python_project,
    get_git_tags,
)


def test_create_python_project(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-project")
    create_python_project(tmp_path)
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / "src").exists()
    assert (tmp_path / "src" / tmp_path.name.replace("-", "_")).exists()
    assert not (tmp_path / ".git").exists(), [p for p in tmp_path.iterdir()]


def test_create_python_project_idempotent(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-project-idempotent")
    create_python_project(tmp_path)
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / "src").exists()
    assert (tmp_path / "src" / tmp_path.name.replace("-", "_")).exists()
    assert not (tmp_path / ".git").exists()
    # Run again to ensure idempotency
    with pytest.warns(UserWarning, match="is already initialized"):
        create_python_project(tmp_path)


def test_create_python_project_non_existent_path(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-nonexistent")
    non_existent_path = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        create_python_project(non_existent_path)


def test_create_git_repo(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-repo")
    create_git_repo(tmp_path)
    assert (tmp_path / ".git").exists()


def test_create_python_project_is_git_repository(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-project-failure")
    create_python_project(tmp_path, git=True)
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / "src").exists()
    assert (tmp_path / "src" / tmp_path.name.replace("-", "_")).exists()
    git_dir = tmp_path / ".git"
    assert git_dir.exists()


def test_create_git_repo_failure(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-repo-failure")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        create_git_repo(tmp_path / "nonexistent")


def test_create_git_commit_failure(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-commit-failure")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        create_git_commit(tmp_path / "nonexistent", "Initial commit")


def test_create_git_tag_failure(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-tag-failure")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        create_git_tag(tmp_path / "nonexistent", "v0.1.0", "Initial tag")


def test_create_git_tag(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-tag")
    create_git_repo(tmp_path)
    (tmp_path / "file.txt").write_text("Sample content")
    create_git_commit(tmp_path, "Initial commit")
    create_git_tag(tmp_path, "v0.1.0", "Initial tag")
    tags = get_git_tags(tmp_path)
    assert len(tags) == 1
    tag = tags[0]
    assert "v0.1.0" == tag[0]
    assert "Initial tag" == tag[1]


def test_create_git_tag_idempotent(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-tag-idempotent")
    create_git_repo(tmp_path)
    (tmp_path / "file.txt").write_text("Sample content")
    create_git_commit(tmp_path, "Initial commit")
    create_git_tag(tmp_path, "v0.1.0", "Initial tag")
    tags = get_git_tags(tmp_path)
    assert len(tags) == 1
    tag = tags[0]
    assert "v0.1.0" == tag[0]
    assert "Initial tag" == tag[1]
    # Create the same tag again to ensure idempotency
    with pytest.warns(UserWarning, match="Tag 'v0.1.0' already exists"):
        create_git_tag(tmp_path, "v0.1.0", "Initial tag")
    tags_after = get_git_tags(tmp_path)
    assert tags == tags_after


def test_get_git_tags_failure(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-git-tags-failure")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        get_git_tags(tmp_path / "nonexistent")


def test_get_git_tags_non_git_repo(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-git-tags-non-git-repo")
    with pytest.raises(RuntimeError, match="Failed to get git tags"):
        get_git_tags(tmp_path)


def test_get_git_tags_empty_repo(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-git-tags-empty-repo")
    create_git_repo(tmp_path)
    tags = get_git_tags(tmp_path)
    assert tags == []


def test_get_git_tags_with_tags(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-git-tags-with-tags")
    create_git_repo(tmp_path)
    (tmp_path / "file.txt").write_text("Sample content")
    create_git_commit(tmp_path, "Initial commit")
    create_git_tag(tmp_path, "v0.1.0")
    (tmp_path / "file2.txt").write_text("More content")
    create_git_commit(tmp_path, "Second commit")
    create_git_tag(tmp_path, "v0.2.0", "Second tag")
    tags = get_git_tags(tmp_path)
    assert len(tags) == 2
    tags_only = [tag for tag, _ in tags]
    assert "v0.1.0" in tags_only
    assert "v0.2.0" in tags_only


def test_assert_version_bump():
    # Major bump
    assert_version_bump("1.2.3", "2.0.0", "major")
    # Minor bump
    assert_version_bump("1.2.3", "1.3.0", "minor")
    # Patch bump
    assert_version_bump("1.2.3", "1.2.4", "patch")
    # Invalid bump
    with pytest.raises(ValueError):
        assert_version_bump("1.2.3", "1.2.3", "invalid")
    with pytest.raises(AssertionError):
        assert_version_bump("1.2.3", "1.2.5", "minor")
    with pytest.raises(AssertionError):
        assert_version_bump("1.2.3", "2.1.0", "patch")
