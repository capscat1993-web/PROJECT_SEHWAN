import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CSV_DIR = PROJECT_ROOT / "csv"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
LOG_DIR = RUNTIME_DIR / "logs"
EXPORT_DIR = RUNTIME_DIR / "exports"
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "reports.db")))


def ensure_project_dirs() -> None:
    for path in (DATA_DIR, RUNTIME_DIR, LOG_DIR, EXPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
