from collections import defaultdict, deque
from time import time
from typing import Deque

from fastapi import HTTPException, status


WINDOW_SECONDS = 60

BUCKETS: dict[str, Deque[float]] = defaultdict(deque)

RATE_LIMITS = {
    "create_link_per_min": 30,
    "list_links_per_min": 60,
    "get_link_per_min": 60,
    "redirect_per_min": 120,
}


def check_rate_limit(bucket: str, key: str, limit: int) -> None:
    now = time()
    request_times = BUCKETS[f"{bucket}:{key}"]

    while request_times and now - request_times[0] >= WINDOW_SECONDS:
        request_times.popleft()

    if len(request_times) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )

    request_times.append(now)