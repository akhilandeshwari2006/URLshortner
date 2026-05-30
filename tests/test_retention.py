from datetime import datetime, timedelta, timezone

from app.models import ClickEvent, Link
from app.worker import purge_old_click_events
import app.worker as worker


def test_purge_old_click_events_removes_old_rows(db_session, monkeypatch):
    from app.database import engine as app_engine

    assert db_session.bind.engine.url.database == "bootcamp_test"
    assert app_engine.url.database != "bootcamp_test"

    monkeypatch.setattr(worker, "SessionLocal", lambda: db_session)

    link = Link(
        code="retention-old",
        long_url="https://example.com/old",
        created_by="dev-user-a",
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    old_event = ClickEvent(
        event_id="retention-event-1",
        link_id=link.id,
        clicked_at=datetime.now(timezone.utc) - timedelta(days=31),
        ip_hash="test-ip-hash",
    )
    db_session.add(old_event)
    db_session.commit()

    deleted_count = purge_old_click_events(retention_days=30)

    assert deleted_count == 1
    assert db_session.query(ClickEvent).filter_by(event_id="retention-event-1").first() is None