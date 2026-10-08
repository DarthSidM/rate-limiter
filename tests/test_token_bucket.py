import pytest

from src.rate_limiter.algorithms.token_bucket import TokenBucket
from src.rate_limiter.models import TokenBucketConfig
from src.rate_limiter.redis import RedisStore


@pytest.mark.asyncio
async def test_token_bucket_allows_requests(redis_client):
    store = RedisStore(
        "redis://localhost:6379/15"
    )

    limiter = TokenBucket(store)

    config = TokenBucketConfig(
        capacity=3,
        refill_rate=1,
    )

    try:
        first = await limiter.check(
            "test:token-bucket",
            config,
        )

        second = await limiter.check(
            "test:token-bucket",
            config,
        )

        third = await limiter.check(
            "test:token-bucket",
            config,
        )

        assert first.allowed is True
        assert second.allowed is True
        assert third.allowed is True

        assert third.remaining == 0

    finally:
        await store.close()


@pytest.mark.asyncio
async def test_token_bucket_rejects_when_empty(redis_client):
    store = RedisStore(
        "redis://localhost:6379/15"
    )

    limiter = TokenBucket(store)

    config = TokenBucketConfig(
        capacity=2,
        refill_rate=0.001,
    )

    try:
        await limiter.check(
            "test:token-bucket",
            config,
        )

        await limiter.check(
            "test:token-bucket",
            config,
        )

        decision = await limiter.check(
            "test:token-bucket",
            config,
        )

        assert decision.allowed is False
        assert decision.remaining == 0
        assert decision.retry_after is not None
        assert decision.retry_after > 0

    finally:
        await store.close()