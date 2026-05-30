from pathlib import Path
import sys


API_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = API_ROOT.parents[1]
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Link


CODE = "upsk02"
LONG_URL = "https://www.upsk.to/"
CREATED_BY = "module-02"


def main() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(Link).where(Link.code == CODE))
        if existing is None:
            link = Link(code=CODE, long_url=LONG_URL, created_by=CREATED_BY)
            db.add(link)
            db.commit()
        else:
            link = existing

        matched = db.scalar(select(Link).where(Link.code == CODE))
        if matched is None:
            raise RuntimeError("Expected query by code to return a link.")

    lines = [
        f"inserted code: {link.code}",
        f"selected code: {matched.code}",
        f"matched long_url: {matched.long_url}",
    ]
    output = "\n".join(lines)

    evidence_path = WORKSPACE_ROOT / "progress" / "evidence" / "module-02" / "query-by-code.txt"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(output + "\n", encoding="utf-8")

    print(output)
    print(f"saved evidence: {evidence_path}")


if __name__ == "__main__":
    main()
