from typing import Annotated

from fastapi import Header, HTTPException, status

from app.config import settings


def _api_keys() -> dict[str, str]:
    return {
        settings.api_key_a: "principal-a",
        settings.api_key_b: "principal-b",
    }


def require_api_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None) -> str:
    principal_id = _api_keys().get(x_api_key)

    if principal_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    return principal_id
