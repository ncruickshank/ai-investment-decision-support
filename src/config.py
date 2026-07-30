"""Project-level configuration for the scaffold branch."""

from pathlib import Path

PROJECT_NAME = "AI Investment Decision Support"
PROJECT_SLUG = "ai-investment-decision-support"
PYTHON_VERSION = "3.12"

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
NOTEBOOKS_DIR = ROOT_DIR / "notebooks"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
SCRIPTS_DIR = ROOT_DIR / "scripts"
SRC_DIR = ROOT_DIR / "src"
TESTS_DIR = ROOT_DIR / "tests"

PROJECT_DIRECTORIES = (
    DATA_DIR,
    MODELS_DIR,
    NOTEBOOKS_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
    SCRIPTS_DIR,
    SRC_DIR,
    TESTS_DIR,
)
