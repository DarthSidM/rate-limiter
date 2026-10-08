from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import RateLimitConfigLoader
from .exceptions import RateLimiterUnavailableError
from .limiter import RateLimiter


class RateLimitMiddleware:
    def __init__(
        self,
        app,
        limiter: RateLimiter,
        config_path: str,
    ):
        self.app = app
        self.limiter = limiter
        self.routes = RateLimitConfigLoader(
            config_path
        ).load()

    async def __call__(
        self,
        scope,
        receive,
        send,
    ):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(
            scope,
            receive=receive,
        )

        route_key = self._route_key(request)
        policy = self.routes.get(route_key)

        if policy is None:
            await self.app(scope, receive, send)
            return

        client_key = self._client_key(request)

        try:
            decision = await self.limiter.check(
                client_key,
                policy,
            )
        except RateLimiterUnavailableError:
            response = JSONResponse(
                status_code=503,
                content={
                    "detail": "Rate limiter unavailable",
                },
            )

            await response(scope, receive, send)
            return

        if not decision.allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                },
            )

            self._set_headers(
                response.headers,
                decision,
            )

            await response(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(
                    message.get("headers", [])
                )

                self._append_headers(
                    headers,
                    decision,
                )

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_headers,
        )

    @staticmethod
    def _route_key(request: Request) -> str:
        return f"{request.method} {request.url.path}"

    @staticmethod
    def _client_key(request: Request) -> str:
        if request.client is None:
            return "unknown"

        return request.client.host

    @staticmethod
    def _set_headers(headers, decision):
        headers["X-RateLimit-Limit"] = str(
            decision.limit
        )

        if decision.remaining is not None:
            headers["X-RateLimit-Remaining"] = str(
                decision.remaining
            )

        if decision.retry_after is not None:
            headers["Retry-After"] = str(
                max(1, int(decision.retry_after))
            )

    @staticmethod
    def _append_headers(headers, decision):
        headers.append(
            (
                b"x-ratelimit-limit",
                str(decision.limit).encode(),
            )
        )

        if decision.remaining is not None:
            headers.append(
                (
                    b"x-ratelimit-remaining",
                    str(decision.remaining).encode(),
                )
            )

        if decision.retry_after is not None:
            headers.append(
                (
                    b"retry-after",
                    str(
                        max(
                            1,
                            int(decision.retry_after),
                        )
                    ).encode(),
                )
            )