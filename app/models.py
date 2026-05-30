from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    long_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    click_events: Mapped[list["ClickEvent"]] = relationship(back_populates="link", cascade="all, delete-orphan")


class ClickEvent(Base):
    __tablename__ = "click_events"
    __table_args__ = (
    Index("ix_click_events_link_id_clicked_at", "link_id", "clicked_at"),
    UniqueConstraint("event_id", name="uq_click_events_event_id"),
)
    

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id", ondelete="CASCADE"), nullable=False)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    link: Mapped[Link] = relationship(back_populates="click_events")
