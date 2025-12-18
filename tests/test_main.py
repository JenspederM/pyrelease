import pytest

from pyrelease import load_command_module, main


def test_main_help_command(capsys):
    """Test that the help command works without errors."""
    main(["--help"])
    captured = capsys.readouterr()
    assert "PyRelease CLI" in captured.out
    assert "commands:" in captured.out
    assert "options:" in captured.out
    assert "global options:" in captured.out


def test_main_no_command(capsys):
    """Test that running main with no command shows the help message."""
    main([])
    captured = capsys.readouterr()
    assert "PyRelease CLI" in captured.out
    assert "commands:" in captured.out
    assert "options:" in captured.out
    assert "global options:" in captured.out


def test_main_invalid_command():
    """Test that running main with an invalid command shows an error message."""
    with pytest.raises(SystemExit) as e:
        main(["invalid_command"])
        assert "error: argument command: invalid choice" in str(e.value)
        assert e.value.code == 2


def test_main_valid_command(capsys):
    """Test that running main with a valid command works."""
    main(["tag", "--message", "Test tag message", "--dry-run"])
    captured = capsys.readouterr()
    assert "Test tag message" not in captured.out  # Tag creation does not print message


def test_load_command_module():
    """Test that load_command_module loads a valid command module."""
    tag_module = load_command_module("tag")
    assert hasattr(tag_module, "register")
    assert hasattr(tag_module, "execute")


def test_load_command_module_invalid():
    """Test that load_command_module raises an ImportError for an invalid command module."""
    with pytest.raises(
        ImportError,
        match="No module named 'pyrelease.commands.non_existent_command'",
    ):
        load_command_module("non_existent_command")
