from pathlib import Path
import time

from ..models import RateLimitDecision, SlidingWindowConfig
from ..redis import RedisStore


LUA_PATH = Path(__file__).parent / "lua" / "sliding_window.lua"
SLIDING_WINDOW_SCRIPT = LUA_PATH.read_text(encoding="utf-8")


class SlidingWindow:
    def __init__(self, redis: RedisStore):
        self.redis = redis

    async def check(
        self,
        key: str,
        config: SlidingWindowConfig,
    ) -> RateLimitDecision:
        now = time.time()

        result = await self.redis.execute(
            SLIDING_WINDOW_SCRIPT,
            keys=[key],
            args=[
                config.limit,
                config.window_seconds,
                now,
            ],
        )

        allowed = bool(result[0])
        remaining = int(result[1])
        retry_after = float(result[2])

        return RateLimitDecision(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            retry_after=retry_after if not allowed else None,
        )