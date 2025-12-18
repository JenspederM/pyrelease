from pyrelease import main


def test_help_command(capsys):
    """Test that the help command works without errors."""
    main(["--help"])
    captured = capsys.readouterr()
    assert "PyRelease CLI" in captured.out
    assert "commands:" in captured.out
    assert "options:" in captured.out
    assert "global options:" in captured.out
