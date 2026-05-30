import logging
from typing import Optional

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

REDIRECT_CACHE_TTL_SECONDS = 300

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)


def _redirect_key(code: str) -> str:
    return f"redirect:{code}"


async def get_redirect_target(code: str) -> Optional[str]:
    try:
        value = await redis_client.get(_redirect_key(code))
        return value

    except Exception as exc:
        logger.warning(
            "Redis get failed; falling back to DB",
            extra={"code": code,"error_type": type(exc).__name__,},
        )
        return None


async def set_redirect_target(
    code: str,
    long_url: str,
    ttl_seconds: int = REDIRECT_CACHE_TTL_SECONDS,
) -> None:
    try:
        await redis_client.setex(
            _redirect_key(code),
            ttl_seconds,
            long_url,
        )

    except Exception as exc:
        logger.warning(
            "Redis set failed; continuing without cache",
            extra={"code": code,"error_type": type(exc).__name__,},
            
        )


async def invalidate_redirect_target(code: str) -> None:
    # Note:
# Update/delete routes do not exist yet.
# When PATCH/DELETE is implemented,
# invalidate_redirect_target(code)
# must be called after successful DB changes.
    try:
        await redis_client.delete(_redirect_key(code))

    except Exception as exc:
        logger.warning(
            "Redis invalidate failed; continuing",
            extra={"code": code,"error_type": type(exc).__name__,},
        )