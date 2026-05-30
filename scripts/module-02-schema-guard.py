from pathlib import Path
import subprocess
import sys


API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import inspect

from app.database import engine


def run_alembic_check() -> str:
    result = subprocess.run(
        [str(API_ROOT / ".venv" / "Scripts" / "alembic.exe"), "check"],
        cwd=API_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout + result.stderr


def assert_code_index() -> str:
    inspector = inspect(engine)
    indexes = inspector.get_indexes("links")
    code_indexes = [
        index for index in indexes
        if index["name"] == "ix_links_code" and index.get("unique") and index["column_names"] == ["code"]
    ]
    if not code_indexes:
        raise AssertionError("links.code unique index ix_links_code is missing.")
    return "links.code unique index present: ix_links_code"


def main() -> None:
    alembic_output = run_alembic_check()
    index_output = assert_code_index()
    print("alembic check: passed")
    print(index_output)
    if "No new upgrade operations detected." in alembic_output:
        print("schema drift: none")


if __name__ == "__main__":
    main()
