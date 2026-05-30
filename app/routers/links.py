from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.database import get_db
from app.schemas.link import CreateLinkRequest, LinkListResponse, LinkResponse
from app.services import links_service
from app.rate_limit import RATE_LIMITS, check_rate_limit
from datetime import datetime
from sqlalchemy import func, or_, select
from app.models import ClickEvent, Link
router = APIRouter(prefix="/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
def create_link(
    request_body: CreateLinkRequest,
    request: Request,
    principal_id: Annotated[str, Depends(require_api_key)],
    db: Annotated[Session, Depends(get_db)],
) -> LinkResponse:

    check_rate_limit("create_link", principal_id, RATE_LIMITS["create_link_per_min"])

    response = links_service.create_link(db, request_body, principal_id)
    response.short_url = str(request.base_url).rstrip("/") + response.short_url
    return response


@router.get("", response_model=LinkListResponse)
def list_links(
    principal_id: Annotated[str, Depends(require_api_key)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LinkListResponse:

    check_rate_limit("list_links", principal_id, RATE_LIMITS["list_links_per_min"])

    return LinkListResponse(
        items=links_service.list_links(db, principal_id, limit, offset),
        limit=limit,
        offset=offset,
    )
@router.get("/search")
def search_links(
    principal_id: Annotated[str, Depends(require_api_key)],
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    tag: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1)] = 20,
    sort: Annotated[str, Query()] = "created_at",
) -> dict:
    check_rate_limit("list_links", principal_id, RATE_LIMITS["list_links_per_min"])

    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    allowed_sorts = {
        "created_at": Link.created_at.desc(),
        "long_url": Link.long_url.asc(),
    }

    order_by = allowed_sorts.get(sort)
    if order_by is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort field")

    filters = [Link.created_by == principal_id]

    if q:
        pattern = f"%{q}%"
        filters.append(
            or_(
                Link.long_url.ilike(pattern),
                Link.code.ilike(pattern),
            )
        )

    query = select(Link).where(*filters)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    rows = db.scalars(
        query.order_by(order_by).limit(page_size).offset(offset)
    ).all()

    return {
        "items": [links_service._to_response(row).model_dump(mode="json") for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
@router.get("/{link_id}", response_model=LinkResponse)
def get_link(
    link_id: int,
    principal_id: Annotated[str, Depends(require_api_key)],
    db: Annotated[Session, Depends(get_db)],
) -> LinkResponse:

    check_rate_limit("get_link", principal_id, RATE_LIMITS["get_link_per_min"])

    response = links_service.get_link(db, link_id, principal_id)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return response
@router.get("/{link_id}/analytics")
def get_link_analytics(
    link_id: int,
    principal_id: Annotated[str, Depends(require_api_key)],
    db: Annotated[Session, Depends(get_db)],
    from_: Annotated[datetime, Query(alias="from")],
    to: Annotated[datetime, Query()],
) -> dict[str, int | str | None]:

    check_rate_limit("get_link", principal_id, RATE_LIMITS["get_link_per_min"])

    link = db.get(Link, link_id)
    if link is None or link.created_by != principal_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    result = db.execute(
        select(
            func.count(ClickEvent.id),
            func.max(ClickEvent.clicked_at),
        ).where(
            ClickEvent.link_id == link_id,
            ClickEvent.clicked_at >= from_,
            ClickEvent.clicked_at <= to,
        )
    ).one()

    click_count, last_clicked_at = result

    return {
        "link_id": link_id,
        "click_count": click_count,
        "last_clicked_at": last_clicked_at.isoformat() if last_clicked_at else None,
    }