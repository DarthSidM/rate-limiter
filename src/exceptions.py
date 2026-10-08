class RateLimiterError(Exception):
    """Base exception for all rate limiter errors."""


class RateLimiterConfigError(RateLimiterError):
    """Raised when the rate limiter configuration is invalid."""


class RateLimiterUnavailableError(RateLimiterError):
    """Raised when the rate limiter's backing store is unavailable."""