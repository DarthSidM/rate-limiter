from .algorithms.sliding_window import SlidingWindow
from .algorithms.token_bucket import TokenBucket
from .exceptions import RateLimiterUnavailableError
from .models import (
    Algorithm,
    RateLimitDecision,
    RateLimitPolicy,
)
from .redis import RedisStore


class RateLimiter:
    def __init__(self, redis: RedisStore):
        self._redis = redis
        self._token_bucket = TokenBucket(redis)
        self._sliding_window = SlidingWindow(redis)

    async def check(
        self,
        key: str,
        policy: RateLimitPolicy,
    ) -> RateLimitDecision:
        try:
            return await self._check(key, policy)

        except RateLimiterUnavailableError:
            if policy.fail_mode.value == "open":
                return RateLimitDecision(
                    allowed=True,
                    limit=self._limit(policy),
                    remaining=None,
                )

            raise

    async def _check(
        self,
        key: str,
        policy: RateLimitPolicy,
    ) -> RateLimitDecision:
        if policy.algorithm == Algorithm.TOKEN_BUCKET:
            # RateLimitPolicy guarantees this is not None.
            config = policy.token_bucket
            assert config is not None

            return await self._token_bucket.check(
                key,
                config,
            )

        if policy.algorithm == Algorithm.SLIDING_WINDOW:
            # RateLimitPolicy guarantees this is not None.
            config = policy.sliding_window
            assert config is not None

            return await self._sliding_window.check(
                key,
                config,
            )

        raise ValueError(
            f"Unsupported algorithm: {policy.algorithm}"
        )

    @staticmethod
    def _limit(policy: RateLimitPolicy) -> int:
        if policy.algorithm == Algorithm.TOKEN_BUCKET:
            assert policy.token_bucket is not None
            return policy.token_bucket.capacity

        if policy.algorithm == Algorithm.SLIDING_WINDOW:
            assert policy.sliding_window is not None
            return policy.sliding_window.limit

        raise ValueError(
            f"Unsupported algorithm: {policy.algorithm}"
        )