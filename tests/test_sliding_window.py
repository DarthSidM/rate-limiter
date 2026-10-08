import pytest

from src.rate_limiter.algorithms.sliding_window import SlidingWindow
from src.rate_limiter.models import SlidingWindowConfig
from src.rate_limiter.redis import RedisStore


@pytest.mark.asyncio
async def test_sliding_window_allows_until_limit(redis_client):
    store = RedisStore(
        "redis://localhost:6379/15"
    )

    limiter = SlidingWindow(store)

    config = SlidingWindowConfig(
        limit=3,
        window_seconds=60,
    )

    try:
        first = await limiter.check(
            "test:sliding-window",
            config,
        )

        second = await limiter.check(
            "test:sliding-window",
            config,
        )

        third = await limiter.check(
            "test:sliding-window",
            config,
        )

        assert first.allowed is True
        assert second.allowed is True
        assert third.allowed is True

        assert third.remaining == 0

    finally:
        await store.close()


@pytest.mark.asyncio
async def test_sliding_window_rejects_after_limit(redis_client):
    store = RedisStore(
        "redis://localhost:6379/15"
    )

    limiter = SlidingWindow(store)

    config = SlidingWindowConfig(
        limit=2,
        window_seconds=60,
    )

    try:
        await limiter.check(
            "test:sliding-window",
            config,
        )

        await limiter.check(
            "test:sliding-window",
            config,
        )

        decision = await limiter.check(
            "test:sliding-window",
            config,
        )

        assert decision.allowed is False
        assert decision.remaining == 0
        assert decision.retry_after is not None
        assert decision.retry_after > 0

    finally:
        await store.close()