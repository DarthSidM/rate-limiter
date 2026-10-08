from collections.abc import Sequence

import redis.asyncio as redis
from redis.exceptions import RedisError

from .exceptions import RateLimiterUnavailableError


RedisArg = str | int | float


class RedisStore:
    def __init__(self, url: str):
        self._client = redis.from_url(
            url,
            decode_responses=False,
        )

    async def execute(
        self,
        script: str,
        *,
        keys: Sequence[str],
        args: Sequence[RedisArg],
    ):
        try:
            return await self._client.eval(
                script,
                len(keys),
                *keys,
                *args,
            )
        except RedisError as exc:
            raise RateLimiterUnavailableError(
                "Redis operation failed"
            ) from exc

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except RedisError as exc:
            raise RateLimiterUnavailableError(
                "Redis is unavailable"
            ) from exc

    async def close(self) -> None:
        await self._client.aclose()
    async def clear(self) -> None:
        try:
            await self._client.flushdb()
        except RedisError as exc:
            raise RateLimiterUnavailableError(
                "Redis operation failed"
            ) from exc