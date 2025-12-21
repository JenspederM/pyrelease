import pytest

from pyrelease.utils import GitRepository


def test_git_tag(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-tag")
    git = GitRepository(tmp_path, init=True)
    (tmp_path / "file.txt").write_text("Sample content")
    git.commit("Initial commit")
    git.tag("v0.1.0", "Initial tag")
    tags = git.get_tags()
    assert len(tags) == 1
    tag = tags[0]
    assert "v0.1.0" == tag[0]
    assert "Initial tag" == tag[1]


def test_git_tag_no_message(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-tag")
    git = GitRepository(tmp_path, init=True)
    (tmp_path / "file.txt").write_text("Sample content")
    git.commit("Initial commit")
    git.tag("v0.1.0")
    tags = git.get_tags()
    assert len(tags) == 1
    tag = tags[0]
    assert "v0.1.0" == tag[0]
    assert "Tag v0.1.0" == tag[1]


def test_git_tag_idempotent(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-tag-idempotent")
    git = GitRepository(tmp_path, init=True)
    (tmp_path / "file.txt").write_text("Sample content")
    git.commit("Initial commit")
    git.tag("v0.1.0", "Initial tag")
    tags = git.get_tags()
    assert len(tags) == 1
    tag = tags[0]
    assert "v0.1.0" == tag[0]
    assert "Initial tag" == tag[1]
    # Create the same tag again to ensure idempotency
    with pytest.warns(UserWarning, match="Tag 'v0.1.0' already exists"):
        git.tag("v0.1.0", "Initial tag")
    tags_after = git.get_tags()
    assert tags == tags_after


def test_get_git_tags_failure(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-git-tags-failure")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        GitRepository(tmp_path / "nonexistent", init=True)


def test_get_git_tags_empty_repo(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-git-tags-empty-repo")
    git = GitRepository(tmp_path, init=True)
    tags = git.get_tags()
    assert tags == []


def test_get_git_tags_with_tags(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-git-tags-with-tags")
    git = GitRepository(tmp_path, init=True)
    (tmp_path / "file.txt").write_text("Sample content")
    git.commit("Initial commit")
    git.tag("v0.1.0", "Initial tag")
    (tmp_path / "file2.txt").write_text("More content")
    git.commit("Second commit")
    git.tag("v0.2.0", "Second tag")
    tags = git.get_tags()
    assert len(tags) == 2
    # Tags are returned in reverse chronological order
    tag1 = tags[0]
    assert "v0.2.0" == tag1[0]
    assert "Second tag" == tag1[1]
    tag2 = tags[1]
    assert "v0.1.0" == tag2[0]
    assert "Initial tag" == tag2[1]


def test_git_get_remote_url(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-get-remote-url")
    git = GitRepository(tmp_path, init=True)
    (tmp_path / "file.txt").write_text("Sample content")
    git.commit("Initial commit")
    remote_url = git.get_remote_url()
    assert remote_url is None


@pytest.mark.parametrize(
    "remote, expected",
    [
        ["https://example.com/repo.git", "https://example.com/repo"],
        ["git@github.com:example/repo.git", "https://github.com/example/repo"],
        ["http://example.com/repo.git", "https://example.com/repo"],
    ],
)
def test_git_get_remote_url_with_remote(remote, expected, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-get-remote-url-with-remote")
    git = GitRepository(tmp_path, init=True)
    git._run_git_command(["remote", "add", "origin", remote])
    remote_url = git.get_remote_url()
    assert remote_url == expected


def test_git_get_remote_url_invalid_format(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-git-get-remote-url-invalid-format")
    git = GitRepository(tmp_path, init=True)
    git._run_git_command(["remote", "add", "origin", "ftp://example.com/repo.git"])
    with pytest.raises(
        ValueError,
        match="Unsupported remote URL format: 'ftp://example.com/repo.git'.",
    ):
        git.get_remote_url()
