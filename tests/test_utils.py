import pytest

from pyrelease.utils import (
    create_python_project,
    get_configured_args,
    get_version_from_pyproject,
    read_pyrelease_config,
)


def test_read_pyrelease_config(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-read-pyrelease-config")
    create_python_project(tmp_path)
    config = read_pyrelease_config(tmp_path)
    required_keys = ["project-version", "project-name"]
    assert all(key in config for key in required_keys), (
        "Config is missing required keys"
        + ",".join(set(required_keys) - set(config.keys()))
    )


def test_read_pyrelease_config_no_file(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-read-pyrelease-config-no-file")
    with pytest.raises(FileNotFoundError, match="pyproject.toml not found"):
        read_pyrelease_config(tmp_path)


def test_read_pyrelease_config_invalid_pyproject(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-read-pyrelease-config-invalid-pyproject")
    (tmp_path / "pyproject.toml").write_text("")
    with pytest.raises(
        ValueError, match="project.name and project.version must be defined"
    ):
        read_pyrelease_config(tmp_path)


def test_read_pyrelease_config_with_dot_pyrelease(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-read-pyrelease-config-with-dot-pyrelease")
    create_python_project(tmp_path)
    (tmp_path / ".pyrelease.toml").write_text(
        """[pyrelease]
custom-key = "custom-value"
"""
    )
    config = read_pyrelease_config(tmp_path)
    assert config.get("custom-key") == "custom-value", (
        "Config did not read custom key from .pyrelease file"
    )


def test_get_configured_args():
    pyrelease_config = {
        "tag": {
            "message-format": "Release v{version}",
            "silent": True,
            "bump": ["minor", "rc"],
        }
    }
    args = get_configured_args(pyrelease_config, "tag")
    message_format_index = args.index("--message-format")
    assert message_format_index != -1, "Expected --message-format in args"
    assert args[message_format_index + 1] == "Release v{version}", (
        "Expected correct message format value"
    )
    assert "--silent" in args, "Expected --silent in args"
    assert sum(1 for arg in args if arg == "--bump") == 2, (
        "Expected two --bump entries in args"
    )


def test_get_version_from_pyproject(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-version-from-pyproject")
    create_python_project(tmp_path)
    version = get_version_from_pyproject(tmp_path)
    assert version == "0.1.0", "Expected version 0.1.0 from pyproject.toml"


def test_get_version_from_pyproject_no_file(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-version-from-pyproject-no-file")
    with pytest.raises(FileNotFoundError, match="pyproject.toml not found"):
        get_version_from_pyproject(tmp_path)


def test_get_version_from_pyproject_invalid_pyproject(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp(
        "test-get-version-from-pyproject-invalid-pyproject"
    )
    (tmp_path / "pyproject.toml").write_text("")
    with pytest.raises(ValueError, match="project.version not found in pyproject.toml"):
        get_version_from_pyproject(tmp_path)


def test_get_version_from_pyproject_nonexistent_path(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("test-get-version-from-pyproject-nonexistent")
    non_existent_path = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError):
        get_version_from_pyproject(non_existent_path)
