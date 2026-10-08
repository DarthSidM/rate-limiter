# benchmarks/benchmark_sliding_window.py

import asyncio
import time
import statistics

from rate_limiter.limiter import RateLimiter
from rate_limiter.models import (
    Algorithm,
    FailMode,
    RateLimitPolicy,
    SlidingWindowConfig,
)
from rate_limiter.redis import RedisStore


REQUESTS = 10_000
CONCURRENCY = 100


async def main():
    store = RedisStore("redis://localhost:6379/15")
    limiter = RateLimiter(store)

    policy = RateLimitPolicy(
        algorithm=Algorithm.SLIDING_WINDOW,
        fail_mode=FailMode.CLOSED,
        sliding_window=SlidingWindowConfig(
            limit=1_000_000,
            window_seconds=60,
        ),
    )

    latencies = []
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def one_request():
        async with semaphore:
            start = time.perf_counter()

            await limiter.check(
                "benchmark-key",
                policy,
            )

            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)

    start = time.perf_counter()

    await asyncio.gather(
        *(one_request() for _ in range(REQUESTS))
    )

    total_time = time.perf_counter() - start

    latencies.sort()

    def percentile(p):
        index = int(len(latencies) * p / 100)
        index = min(index, len(latencies) - 1)
        return latencies[index]

    print(f"Requests:       {REQUESTS}")
    print(f"Concurrency:    {CONCURRENCY}")
    print(f"Total time:     {total_time:.3f}s")
    print(f"Throughput:     {REQUESTS / total_time:.2f} req/s")
    print(f"p50 latency:    {percentile(50):.3f} ms")
    print(f"p95 latency:    {percentile(95):.3f} ms")
    print(f"p99 latency:    {percentile(99):.3f} ms")
    print(f"min latency:    {min(latencies):.3f} ms")
    print(f"max latency:    {max(latencies):.3f} ms")

    await store.close()


if __name__ == "__main__":
    asyncio.run(main())