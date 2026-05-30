import hashlib
import logging
from datetime import datetime, timedelta, timezone

from celery import Celery
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import SessionLocal
from app.models import ClickEvent


logger = logging.getLogger(__name__)

RETENTION_DAYS = 30

celery_app = Celery(
    "upsk_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    broker_connection_timeout=1,
    broker_transport_options={
        "socket_connect_timeout": 1,
        "socket_timeout": 1,
    },
    result_backend_transport_options={
        "socket_connect_timeout": 1,
        "socket_timeout": 1,
    },
    task_ignore_result=True,
)
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def record_click(
    self,
    event_id: str,
    link_id: int,
    user_agent: str | None,
    referrer: str | None,
    ip_address: str,
) -> None:
    ip_hash = hashlib.sha256(ip_address.encode("utf-8")).hexdigest()

    db = SessionLocal()
    try:
        click_event = ClickEvent(
            event_id=event_id,
            link_id=link_id,
            user_agent=user_agent,
            referrer=referrer,
            ip_hash=ip_hash,
        )
        db.add(click_event)
        db.commit()
        logger.info("Click event recorded", extra={"event_id": event_id, "link_id": link_id})

    except IntegrityError:
        db.rollback()
        logger.info("Duplicate click event skipped", extra={"event_id": event_id})

    finally:
        db.close()


@celery_app.task
def purge_old_click_events(retention_days: int = RETENTION_DAYS) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    db = SessionLocal()
    try:
        result = db.execute(delete(ClickEvent).where(ClickEvent.clicked_at < cutoff))
        db.commit()
        return result.rowcount or 0

    finally:
        db.close()