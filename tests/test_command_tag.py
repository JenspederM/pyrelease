import sys

import pytest

from pyrelease import main
from pyrelease.testing.utils import (
    create_git_commit,
    create_python_project,
    get_git_tags,
)


@pytest.mark.skipif(
    "-s" in sys.argv or "--capture" in sys.argv,
    reason="Cannot test stdin input when output is captured",
)
def test_tag_invalid():
    with pytest.raises(OSError, match="reading from stdin while output is captured"):
        main(["tag"])


def test_tag_with_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "Test tag message")
    try:
        main(["tag", "--dry-run"])
    except SystemExit as e:
        assert e.code == 0


def test_tag_with_message(tmp_path_factory):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    create_git_commit(path, "feat: add new feature")
    main(["tag", "--message", "Direct tag message", "--path", str(path)])
    tag, message = get_git_tags(path)[0]
    assert "v0.1.0" in tag
    assert message == "Direct tag message"


def test_tag_with_message_format(tmp_path_factory):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    create_git_commit(path, "feat: add new feature")
    main(
        [
            "tag",
            "--message-format",
            "Release v{version}",
            "--path",
            str(path),
        ]
    )
    tag, message = get_git_tags(path)[0]
    assert "v0.1.0" in tag
    assert message == "Release v0.1.0"


def test_tag_dry_run(tmp_path_factory):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    create_git_commit(path, "feat: add new feature")
    main(["tag", "--message", "My message", "--dry-run", "--path", str(path)])
    tags = get_git_tags(path)
    assert len(tags) == 0
