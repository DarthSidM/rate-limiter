local key = KEYS[1]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local state = redis.call(
    "HMGET",
    key,
    "tokens",
    "timestamp"
)

local tokens = tonumber(state[1])
local timestamp = tonumber(state[2])

-- First request for this key.
if tokens == nil then
    tokens = capacity
    timestamp = now
end

-- Add tokens that accumulated since the last request.
local elapsed = math.max(0, now - timestamp)

tokens = math.min(
    capacity,
    tokens + (elapsed * refill_rate)
)

local allowed = 0
local retry_after = 0

if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
else
    -- How long until one complete token is available?
    retry_after = (1 - tokens) / refill_rate
end

-- Store the new state.
redis.call(
    "HSET",
    key,
    "tokens",
    tokens,
    "timestamp",
    now
)

-- Don't keep completely inactive buckets forever.
local ttl = math.max(
    1,
    math.ceil((capacity / refill_rate) * 2)
)

redis.call(
    "EXPIRE",
    key,
    ttl
)

return {
    allowed,
    math.floor(tokens),
    retry_after
}