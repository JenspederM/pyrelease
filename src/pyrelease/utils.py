import tomllib


def get_version_from_pyproject() -> str:
    """Retrieve the version from pyproject.toml.

    Returns:
        str: Version string
    """
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data["project"]["version"]
