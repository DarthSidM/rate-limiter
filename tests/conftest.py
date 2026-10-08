import os

import pytest_asyncio
import redis.asyncio as redis


@pytest_asyncio.fixture
async def redis_client():
    url = os.getenv(
        "RATE_LIMITER_REDIS_URL",
        "redis://localhost:6379/15",
    )

    client = redis.from_url(
        url,
        decode_responses=False,
    )

    await client.flushdb()

    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()