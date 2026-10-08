from pathlib import Path
import time

from ..models import RateLimitDecision, TokenBucketConfig
from ..redis import RedisStore


LUA_PATH = Path(__file__).parent / "lua" / "token_bucket.lua"
TOKEN_BUCKET_SCRIPT = LUA_PATH.read_text(encoding="utf-8")


class TokenBucket:
    def __init__(self, redis: RedisStore):
        self.redis = redis

    async def check(
        self,
        key: str,
        config: TokenBucketConfig,
    ) -> RateLimitDecision:
        now = time.time()

        result = await self.redis.execute(
            TOKEN_BUCKET_SCRIPT,
            keys=[key],
            args=[
                config.capacity,
                config.refill_rate,
                now,
            ],
        )

        allowed = bool(result[0])
        remaining = int(result[1])
        retry_after = float(result[2])

        return RateLimitDecision(
            allowed=allowed,
            limit=config.capacity,
            remaining=remaining,
            retry_after=retry_after if not allowed else None,
        )