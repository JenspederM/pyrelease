import pytest

from pyrelease.utils import (
    CustomFormatter,
    GitRepository,
    create_python_project,
    get_configured_args,
    get_version_from_pyproject,
    read_pyrelease_config,
)


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


@pytest.mark.parametrize(
    "format_string,expected_keys",
    [
        (
            "{version} - {changes} - {remote_url} - {from_ref} - {to_ref}",
            {"version", "changes", "remote_url", "from_ref", "to_ref"},
        ),
        ("Version: {version}\nChanges:\n{changes}", {"version", "changes"}),
        ("{remote_url} | {from_ref} -> {to_ref}", {"remote_url", "from_ref", "to_ref"}),
    ],
)
def test_custom_formatter_get_keys(format_string, expected_keys):
    formatter = CustomFormatter(format_string)
    keys = formatter.get_keys()
    assert keys == expected_keys
    formatter = CustomFormatter()
    keys = formatter.get_keys(format_string=format_string)
    assert keys == expected_keys


def test_custom_formatter_no_string():
    formatter = CustomFormatter()
    with pytest.raises(ValueError, match="No format string provided."):
        formatter.get_keys()


def test_custom_formatter_check_keys():
    format_string = "{version} - {changes}"
    formatter = CustomFormatter(format_string)
    mapping = {"version": "1.0.0", "changes": "Initial release"}
    formatter.check_format_string(mapping=mapping)


def test_custom_formatter_check_keys_no_string():
    formatter = CustomFormatter()
    with pytest.raises(ValueError, match="No format string provided."):
        formatter.check_format_string({})


def test_custom_formatter_check_keys_partial_used_mapping():
    format_string = "{version}"
    formatter = CustomFormatter(format_string)
    formatter.check_format_string({"version": "value", "extra_key": "value"})


def test_custom_formatter_check_keys_invalid_string():
    format_string = "{version} - {changes}"
    formatter = CustomFormatter(format_string)
    with pytest.raises(ValueError) as exc_info:
        formatter.check_format_string({"my_variable": "value"})
        err = str(exc_info.value)
        assert "Found invalid keys in format string: 'version', 'changes'." in err
        assert "Valid keys are: 'my_variable'." in err


def test_custom_formatter_check_keys_missing_mapping():
    format_string = "{version} - {changes} - {date}"
    formatter = CustomFormatter(format_string)
    with pytest.raises(
        ValueError, match="No mapping provided to check format string against."
    ):
        formatter.check_format_string({})


def test_custom_formatter_format():
    format_string = "Version: {version}, Changes: {changes}"
    formatter = CustomFormatter(format_string)
    result = formatter.format(version="1.0.0", changes="Initial release")
    expected = "Version: 1.0.0, Changes: Initial release"
    assert result == expected, "Formatted string does not match expected output"


def test_custom_formatter_format_no_string():
    formatter = CustomFormatter()
    with pytest.raises(ValueError, match="No format string provided."):
        formatter.format(version="1.0.0")
