from fastapi import FastAPI

from src.rate_limiter.limiter import RateLimiter
from src.rate_limiter.middleware import RateLimitMiddleware
from src.rate_limiter.redis import RedisStore


REDIS_URL = "redis://localhost:6379/15"


redis = RedisStore(REDIS_URL)
limiter = RateLimiter(redis)

app = FastAPI()

app.add_middleware(
    RateLimitMiddleware,
    limiter=limiter,
    config_path="demo/rate_limits.yaml",
)


@app.get("/api/test")
async def test():
    return {
        "message": "request allowed",
    }


@app.get("/api/public")
async def public():
    return {
        "message": "public endpoint",
    }