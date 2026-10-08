import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.rate_limiter.limiter import RateLimiter
from src.rate_limiter.middleware import RateLimitMiddleware
from src.rate_limiter.redis import RedisStore


@pytest.fixture
def app(tmp_path):
    config = tmp_path / "rate_limits.yaml"

    config.write_text(
        """
routes:
  "GET /test":
    algorithm: sliding_window
    limit: 3
    window_seconds: 60
    fail_mode: closed
""",
        encoding="utf-8",
    )

    redis = RedisStore(
        "redis://localhost:6379/15"
    )

    limiter = RateLimiter(redis)

    app = FastAPI()

    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter,
        config_path=str(config),
    )

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    return app, redis


@pytest.mark.asyncio
async def test_middleware_allows_requests(app):
    application, redis = app

    try:
        await redis._client.flushdb()

        transport = ASGITransport(
            app=application,
        )

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:

            response = await client.get("/test")

            assert response.status_code == 200
            assert response.json() == {"ok": True}

            assert (
                response.headers["X-RateLimit-Limit"]
                == "3"
            )

            assert (
                response.headers["X-RateLimit-Remaining"]
                == "2"
            )

    finally:
        await redis.close()


@pytest.mark.asyncio
async def test_middleware_returns_429_after_limit(app):
    application, redis = app

    try:
        await redis._client.flushdb()

        transport = ASGITransport(
            app=application,
        )

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:

            for _ in range(3):
                response = await client.get("/test")

                assert response.status_code == 200

            response = await client.get("/test")

            assert response.status_code == 429

            assert response.json() == {
                "detail": "Too many requests"
            }

            assert (
                response.headers["X-RateLimit-Limit"]
                == "3"
            )

            assert (
                response.headers["X-RateLimit-Remaining"]
                == "0"
            )

            assert "Retry-After" in response.headers

    finally:
        await redis.close()