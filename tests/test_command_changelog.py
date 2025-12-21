from pyrelease import main
from pyrelease.utils import (
    GitRepository,
    create_python_project,
    get_version_from_pyproject,
)


def test_changelog(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    commit_hash = git.commit("feat: add new feature")
    main(
        [
            "changelog",
            "--path",
            str(path),
        ]
    )
    captured = capsys.readouterr()
    changelog = captured.out
    expected_changelog = f"""
# 0.1.0
=========================
- feat: add new feature ([{commit_hash}](/commit/{commit_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert changelog.strip() == expected_changelog.strip()


def test_changelog_new_version(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    commit_hash = git.commit("feat: add new feature")
    old_version = get_version_from_pyproject(path)

    # Generate changelog for old version
    main(
        [
            "changelog",
            "--path",
            str(path),
        ]
    )
    captured = capsys.readouterr()
    old_changelog = f"""
# {old_version}
=========================
- feat: add new feature ([{commit_hash}](/commit/{commit_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert captured.out.strip() == old_changelog.strip()

    # Bump version
    main(
        [
            "bump",
            "--bump",
            "minor",
            "--path",
            str(path),
            "--silent",
        ]
    )
    new_version = get_version_from_pyproject(path)
    assert new_version != old_version, "Version should have been bumped"

    # Generate changelog for new version
    main(
        [
            "changelog",
            "--path",
            str(path),
        ]
    )
    captured = capsys.readouterr()
    new_changelog = f"""
# {new_version}
=========================
- feat: add new feature ([{commit_hash}](/commit/{commit_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert captured.out.strip() == new_changelog.strip()


def test_changelog_multiple(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    feat_hash = git.commit("feat: add new feature")
    (path / "some_fix.txt").write_text("Some changes")
    fix_hash = git.commit("fix: fix a bug")
    (path / "some_docs.txt").write_text("Some changes")
    docs_hash = git.commit("docs: update documentation")
    main(
        [
            "changelog",
            "--path",
            str(path),
        ]
    )
    captured = capsys.readouterr()
    changelog = captured.out
    expected_changelog = f"""
# 0.1.0
=========================
- docs: update documentation ([{docs_hash}](/commit/{docs_hash}))
- fix: fix a bug ([{fix_hash}](/commit/{fix_hash}))
- feat: add new feature ([{feat_hash}](/commit/{feat_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert changelog.strip() == expected_changelog.strip()


def test_changelog_output(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    commit_hash = git.commit("feat: add new feature")
    main(
        [
            "changelog",
            "--path",
            str(path),
            "--output",
            str(path / "CHANGELOG.md"),
        ]
    )
    captured = capsys.readouterr()
    changelog = captured.out
    expected_changelog = f"""
# 0.1.0
=========================
- feat: add new feature ([{commit_hash}](/commit/{commit_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert changelog.strip() == expected_changelog.strip()
    with open(path / "CHANGELOG.md") as f:
        file_changelog = f.read()
    assert file_changelog.strip() == expected_changelog.strip()


def test_changelog_conventional(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    commit_hash = git.commit("feat: add new feature")
    main(
        [
            "changelog",
            "--conventional",
            "--conventional-type-mapping",
            "feat:Features,fix:Bug Fixes",
            "--path",
            str(path),
        ]
    )
    captured = capsys.readouterr()
    changelog = captured.out
    expected_changelog = f"""
# 0.1.0
=========================
### Features
- feat: add new feature ([{commit_hash}](/commit/{commit_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert changelog.strip() == expected_changelog.strip()


def test_changelog_conventional_output(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    commit_hash = git.commit("feat: add new feature")
    main(
        [
            "changelog",
            "--conventional",
            "--conventional-type-mapping",
            "feat:Features,fix:Bug Fixes",
            "--path",
            str(path),
            "--output",
            str(path / "CHANGELOG.md"),
        ]
    )
    captured = capsys.readouterr()
    changelog = captured.out
    expected_changelog = f"""
# 0.1.0
=========================
### Features
- feat: add new feature ([{commit_hash}](/commit/{commit_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert changelog.strip() == expected_changelog.strip()
    with open(path / "CHANGELOG.md") as f:
        file_changelog = f.read()
    assert file_changelog.strip() == expected_changelog.strip()


def test_changelog_conventional_multiple_sections(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    feat_hash = git.commit("feat: add new feature")
    (path / "some_fix.txt").write_text("Some changes")
    fix_hash = git.commit("fix: fix a bug")
    (path / "some_docs.txt").write_text("Some changes")
    docs_hash = git.commit("docs: update documentation")
    main(
        [
            "changelog",
            "--conventional",
            "--conventional-type-mapping",
            "feat:Features,fix:Bug Fixes",
            "--path",
            str(path),
        ]
    )
    captured = capsys.readouterr()
    changelog = captured.out
    expected_changelog = f"""
# 0.1.0
=========================
### Features
- feat: add new feature ([{feat_hash}](/commit/{feat_hash}))

### Bug Fixes
- fix: fix a bug ([{fix_hash}](/commit/{fix_hash}))

### Other Changes
- docs: update documentation ([{docs_hash}](/commit/{docs_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert changelog.strip() == expected_changelog.strip()


def test_changelog_conventional_other_changes(tmp_path_factory, capsys):
    path = tmp_path_factory.mktemp("repo")
    create_python_project(path, git=True)
    git = GitRepository(path)
    feat_hash = git.commit("feat: add new feature")
    (path / "some_file.txt").write_text("Some changes")
    docs_hash = git.commit("docs: update documentation")
    main(
        [
            "changelog",
            "--conventional",
            "--conventional-type-mapping",
            "feat:Features,fix:Bug Fixes",
            "--path",
            str(path),
        ]
    )
    captured = capsys.readouterr()
    changelog = captured.out
    expected_changelog = f"""
# 0.1.0
=========================
### Features
- feat: add new feature ([{feat_hash}](/commit/{feat_hash}))

### Other Changes
- docs: update documentation ([{docs_hash}](/commit/{docs_hash}))

See all changes at: [..HEAD](/compare/..HEAD)
"""
    assert changelog.strip() == expected_changelog.strip()
