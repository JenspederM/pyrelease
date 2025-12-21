import pytest

from pyrelease.commands.bump import collect_bump_mapping


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
