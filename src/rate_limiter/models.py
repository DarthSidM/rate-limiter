from dataclasses import dataclass
from enum import StrEnum


class Algorithm(StrEnum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"


class FailMode(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True)
class TokenBucketConfig:
    capacity: int
    refill_rate: float

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError("capacity must be greater than 0")

        if self.refill_rate <= 0:
            raise ValueError(
                "refill_rate must be greater than 0"
            )


@dataclass(frozen=True)
class SlidingWindowConfig:
    limit: int
    window_seconds: int

    def __post_init__(self):
        if self.limit <= 0:
            raise ValueError("limit must be greater than 0")

        if self.window_seconds <= 0:
            raise ValueError(
                "window_seconds must be greater than 0"
            )


@dataclass(frozen=True)
class RateLimitPolicy:
    algorithm: Algorithm
    fail_mode: FailMode

    token_bucket: TokenBucketConfig | None = None
    sliding_window: SlidingWindowConfig | None = None

    def __post_init__(self):
        if self.algorithm == Algorithm.TOKEN_BUCKET:

            if self.token_bucket is None:
                raise ValueError(
                    "token_bucket config is required"
                )

            if self.sliding_window is not None:
                raise ValueError(
                    "sliding_window config must not be provided"
                )

        elif self.algorithm == Algorithm.SLIDING_WINDOW:

            if self.sliding_window is None:
                raise ValueError(
                    "sliding_window config is required"
                )

            if self.token_bucket is not None:
                raise ValueError(
                    "token_bucket config must not be provided"
                )


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: float | None = None


@dataclass(frozen=True)
class RateLimitKey:
    key: str
    tenant_id: str | None = None
    user_id: str | None = None
    route: str | None = None