from pathlib import Path

import config


def test_project_root_resolves_to_repository() -> None:
    assert Path(__file__).resolve().parents[1] == config.ROOT_DIR


def test_configured_project_directories_exist() -> None:
    missing_directories = [
        path for path in config.PROJECT_DIRECTORIES if not path.exists()
    ]

    assert missing_directories == []


def test_python_version_is_312() -> None:
    assert config.PYTHON_VERSION == "3.12"
