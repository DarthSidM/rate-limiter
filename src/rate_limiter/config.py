from pathlib import Path

import yaml

from .models import (
    Algorithm,
    FailMode,
    RateLimitPolicy,
    SlidingWindowConfig,
    TokenBucketConfig,
)


class ConfigError(ValueError):
    """Raised when the rate limiter configuration is invalid."""


class RateLimitConfigLoader:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict[str, RateLimitPolicy]:
        if not self.path.exists():
            raise ConfigError(f"Config file not found: {self.path}")

        try:
            with self.path.open("r", encoding="utf-8") as file:
                raw = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigError("Config root must be a mapping")

        routes = raw.get("routes")

        if not isinstance(routes, dict):
            raise ConfigError("'routes' must be a mapping")

        return {
            route: self._parse_policy(route, value)
            for route, value in routes.items()
        }

    def _parse_policy(
        self,
        route: str,
        value: object,
    ) -> RateLimitPolicy:
        if not isinstance(value, dict):
            raise ConfigError(
                f"Configuration for '{route}' must be a mapping"
            )

        try:
            algorithm = Algorithm(value["algorithm"])
            fail_mode = FailMode(value.get("fail_mode", "closed"))
        except (KeyError, ValueError) as exc:
            raise ConfigError(
                f"Invalid configuration for '{route}'"
            ) from exc

        if algorithm == Algorithm.TOKEN_BUCKET:
            token_bucket = self._parse_token_bucket(route, value)

            return RateLimitPolicy(
                algorithm=algorithm,
                fail_mode=fail_mode,
                token_bucket=token_bucket,
            )

        if algorithm == Algorithm.SLIDING_WINDOW:
            sliding_window = self._parse_sliding_window(route, value)

            return RateLimitPolicy(
                algorithm=algorithm,
                fail_mode=fail_mode,
                sliding_window=sliding_window,
            )

        raise ConfigError(
            f"Unsupported algorithm '{algorithm}' for '{route}'"
        )

    def _parse_token_bucket(
        self,
        route: str,
        value: dict,
    ) -> TokenBucketConfig:
        try:
            capacity = int(value["capacity"])
            refill_rate = float(value["refill_rate"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(
                f"Invalid token bucket configuration for '{route}'"
            ) from exc

        try:
            return TokenBucketConfig(
                capacity=capacity,
                refill_rate=refill_rate,
            )
        except ValueError as exc:
            raise ConfigError(
                f"Invalid token bucket configuration for '{route}': {exc}"
            ) from exc

    def _parse_sliding_window(
        self,
        route: str,
        value: dict,
    ) -> SlidingWindowConfig:
        try:
            limit = int(value["limit"])
            window_seconds = int(value["window_seconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(
                f"Invalid sliding window configuration for '{route}'"
            ) from exc

        try:
            return SlidingWindowConfig(
                limit=limit,
                window_seconds=window_seconds,
            )
        except ValueError as exc:
            raise ConfigError(
                f"Invalid sliding window configuration for '{route}': {exc}"
            ) from exc