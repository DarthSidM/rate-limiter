from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

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

        request = Request(scope, receive=receive)

        route_key = self._get_route_key(request)
        policy = self.routes.get(route_key)

        # No rate limit configured for this route.
        if policy is None:
            await self.app(scope, receive, send)
            return

        client_key = self._get_client_key(request)

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

            self._add_rate_limit_headers(
                response,
                decision,
            )

            await response(scope, receive, send)
            return

        response = await self._call_next(
            scope,
            receive,
            send,
        )

        self._add_rate_limit_headers(
            response,
            decision,
        )

        await response(scope, receive, send)

    @staticmethod
    def _get_route_key(request: Request) -> str:
        return f"{request.method} {request.url.path}"

    @staticmethod
    def _get_client_key(request: Request) -> str:
        client = request.client

        if client is None:
            return "unknown"

        return client.host

    async def _call_next(
        self,
        scope,
        receive,
        send,
    ) -> Response:
        body = []

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response = Response()

                response.status_code = message["status"]

                response.raw_headers = message.get(
                    "headers",
                    [],
                )

                body.append(response)

            elif message["type"] == "http.response.body":
                body.append(message.get("body", b""))

        await self.app(
            scope,
            receive,
            send_wrapper,
        )

        response = body[0]

        if len(body) > 1:
            response.body = b"".join(body[1:])

        return response

    @staticmethod
    def _add_rate_limit_headers(
        response: Response,
        decision,
    ) -> None:
        response.headers[
            "X-RateLimit-Limit"
        ] = str(decision.limit)

        if decision.remaining is not None:
            response.headers[
                "X-RateLimit-Remaining"
            ] = str(decision.remaining)

        if decision.retry_after is not None:
            response.headers[
                "Retry-After"
            ] = str(
                max(
                    1,
                    int(decision.retry_after),
                )
            )