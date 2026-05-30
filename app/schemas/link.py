from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, Field, field_validator


class CreateLinkRequest(BaseModel):
    long_url: str = Field(min_length=1, max_length=2048)
    expires_at: datetime | None = None
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("long_url")
    @classmethod
    def validate_long_url(cls, value: str) -> str:
        trimmed = value.strip()
        if any(ord(char) < 32 for char in trimmed):
            raise ValueError("long_url cannot contain control characters")

        decoded = unquote(trimmed)
        if decoded != trimmed:
            raise ValueError("long_url cannot contain encoded URL syntax")

        parsed = urlparse(trimmed)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("long_url must use http or https")
        if not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("long_url must include a valid host without userinfo")
        if "\\" in trimmed:
            raise ValueError("long_url cannot contain backslashes")
        return trimmed

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        now = datetime.now(timezone.utc)
        comparable = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if comparable <= now:
            raise ValueError("expires_at must be in the future")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for tag in value:
            trimmed = tag.strip()
            if not trimmed or len(trimmed) > 32:
                raise ValueError("tags must be 1-32 characters")
            cleaned.append(trimmed)
        return cleaned


class LinkResponse(BaseModel):
    id: int
    code: str
    short_url: str
    long_url: str
    created_at: datetime
    expires_at: datetime | None = None


class LinkListResponse(BaseModel):
    items: list[LinkResponse]
    limit: int
    offset: int
