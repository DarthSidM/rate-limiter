import pytest

from rate_limiter.exceptions import RateLimiterUnavailableError
from rate_limiter.limiter import RateLimiter
from src.rate_limiter.models import (
    Algorithm,
    FailMode,
    RateLimitPolicy,
    SlidingWindowConfig,
)
from src.rate_limiter.redis import RedisStore


@pytest.mark.asyncio
async def test_limiter_uses_sliding_window(redis_client):
    store = RedisStore(
        "redis://localhost:6379/15"
    )

    limiter = RateLimiter(store)

    policy = RateLimitPolicy(
        algorithm=Algorithm.SLIDING_WINDOW,
        fail_mode=FailMode.CLOSED,
        sliding_window=SlidingWindowConfig(
            limit=2,
            window_seconds=60,
        ),
    )

    try:
        first = await limiter.check(
            "test:limiter",
            policy,
        )

        second = await limiter.check(
            "test:limiter",
            policy,
        )

        third = await limiter.check(
            "test:limiter",
            policy,
        )

        assert first.allowed is True
        assert second.allowed is True
        assert third.allowed is False

    finally:
        await store.close()