from typing import Annotated
from uuid import uuid4
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.cache import get_redirect_target, set_redirect_target
from app.database import get_db
from app.services import links_service
from app.rate_limit import RATE_LIMITS, check_rate_limit
from app.worker import record_click

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/r", tags=["redirect"])


@router.get("/{code}", status_code=status.HTTP_302_FOUND)
async def redirect_by_code(
    code: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    client_ip = request.client.host if request.client else "unknown"

    check_rate_limit(
        "redirect",
        client_ip,
        RATE_LIMITS["redirect_per_min"],
    )
    def enqueue_click(link_id: int) -> None:
        try:
            record_click.delay(
                event_id=str(uuid4()),
                link_id=link_id,
                user_agent=request.headers.get("user-agent"),
                referrer=request.headers.get("referer"),
                ip_address=client_ip,
            )
        except Exception:
            logger.exception(
                "Failed to enqueue click analytics",
                extra={"code": code},
            )
    

    # Try Redis cache first
    cached_url = await get_redirect_target(code)

    if cached_url is not None:
        logger.info(
            "Redirect cache hit",
            extra={"code": code},
        )

        link = links_service.get_redirect_link(db, code)
        if link is not None:
            enqueue_click(link.id)

        return RedirectResponse(
            cached_url,
            status_code=status.HTTP_302_FOUND,
        )
    logger.info(
        "Redirect cache miss",
        extra={"code": code},
    )

    # Fallback to DB
    link = links_service.get_redirect_link(db, code)

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    enqueue_click(link.id)

    # Populate Redis cache
    await set_redirect_target(code, link.long_url)

    logger.info(
        "Redirect cache populated",
        extra={"code": code},
    )

    return RedirectResponse(
        link.long_url,
        status_code=status.HTTP_302_FOUND,
    )