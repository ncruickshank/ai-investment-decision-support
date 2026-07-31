import subprocess
from pathlib import Path

import config


def test_data_subfolder_placeholders_exist() -> None:
    assert (config.RAW_DATA_DIR / ".gitkeep").exists()
    assert (config.PROCESSED_DATA_DIR / ".gitkeep").exists()


def test_generated_data_files_are_ignored_but_placeholders_are_not() -> None:
    generated = subprocess.run(
        ["git", "check-ignore", "data/raw/example.json"],
        cwd=config.ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    placeholder = subprocess.run(
        ["git", "check-ignore", "data/raw/.gitkeep"],
        cwd=config.ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )

    assert generated.returncode == 0
    assert Path(generated.stdout.strip()) == Path("data/raw/example.json")
    assert placeholder.returncode == 1
