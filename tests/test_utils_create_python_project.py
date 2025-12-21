import pytest

from pyrelease.utils import GitRepository, create_python_project


def test_create_python_project(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-create-python-project")
    create_python_project(tmp_path)
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / "README.md").exists()


def test_create_python_project_with_git(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-create-python-project-git")
    create_python_project(tmp_path, git=True)
    GitRepository(tmp_path)


def test_create_python_project_nonexistent_path(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-create-python-project-nonexistent")
    non_existent_path = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError):
        create_python_project(non_existent_path, git=True)


def test_create_python_project_no_uv_installed(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp("test-create-python-project-no-uv")
    monkeypatch.setattr(
        "shutil.which", lambda cmd: None if cmd == "uv" else "/usr/bin/uv"
    )
    with pytest.raises(
        RuntimeError,
        match="The 'uv' command-line tool is required to create a Python project",
    ):
        create_python_project(tmp_path, git=True)


def test_create_python_project_idempotent(tmp_path_factory, monkeypatch):
    tmp_path = tmp_path_factory.mktemp("test-create-python-project-already-initialized")
    create_python_project(tmp_path, git=True)
    with pytest.warns(UserWarning, match="is already initialized"):
        create_python_project(tmp_path, git=True)
