from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from fastapi import HTTPException, Request


@dataclass
class SlidingWindowLimiter:
    """
    Simple in-memory rate limiter.
    - Suitable for local/dev/single-instance deployments.
    - For production multi-instance, replace with Redis-based limiter.
    """

    limit: int
    window_seconds: int

    def __post_init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key: str) -> None:
        now = time.time()
        q = self._hits.get(key)
        if q is None:
            q = deque()
            self._hits[key] = q

        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()

        if len(q) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests")

        q.append(now)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
