import secrets
import string
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Link
from app.schemas.link import CreateLinkRequest, LinkResponse


ALPHABET = string.ascii_letters + string.digits


def _generate_code(length: int = 7) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def _to_response(link: Link) -> LinkResponse:
    return LinkResponse(
        id=link.id,
        code=link.code,
        short_url=f"/r/{link.code}",
        long_url=link.long_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


def create_link(
    db: Session,
    request: CreateLinkRequest,
    principal_id: str,
) -> LinkResponse:
    for _ in range(5):
        link = Link(
            code=_generate_code(),
            long_url=request.long_url,
            created_by=principal_id,  
            expires_at=request.expires_at,
        )
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        db.refresh(link)
        return _to_response(link)

    raise RuntimeError("Could not generate a unique short code")


def list_links(
    db: Session,
    principal_id: str,
    limit: int,
    offset: int,
) -> list[LinkResponse]:
    rows = db.scalars(
        select(Link)
        .where(Link.created_by == principal_id)  
        .order_by(Link.created_at.desc(), Link.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return [_to_response(row) for row in rows]


def get_link(
    db: Session,
    link_id: int,
    principal_id: str,
) -> LinkResponse | None:
    link = db.get(Link, link_id)

    if link is None:
        return None

   
    if link.created_by != principal_id:
        return None

    return _to_response(link)


def get_redirect_url(db: Session, code: str) -> str | None:
    link = db.scalar(select(Link).where(Link.code == code))

    if link is None:
        return None

    if link.expires_at is not None:
        expires_at = (
            link.expires_at
            if link.expires_at.tzinfo
            else link.expires_at.replace(tzinfo=timezone.utc)
        )

        if expires_at <= datetime.now(timezone.utc):
            return None

    return link.long_url
def get_redirect_link(db: Session, code: str) -> Link | None:
    link = db.scalar(select(Link).where(Link.code == code))

    if link is None:
        return None

    if link.expires_at is not None:
        expires_at = (
            link.expires_at
            if link.expires_at.tzinfo
            else link.expires_at.replace(tzinfo=timezone.utc)
        )

        if expires_at <= datetime.now(timezone.utc):
            return None

    return link