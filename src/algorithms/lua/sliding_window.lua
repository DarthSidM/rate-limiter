local key = KEYS[1]

local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local window_start = now - window

-- Remove requests that are outside the window.
redis.call(
    "ZREMRANGEBYSCORE",
    key,
    0,
    window_start
)

local count = redis.call(
    "ZCARD",
    key
)

-- Limit already reached.
if count >= limit then
    local oldest = redis.call(
        "ZRANGE",
        key,
        0,
        0,
        "WITHSCORES"
    )

    local retry_after = 0

    if oldest[2] ~= nil then
        retry_after = tonumber(oldest[2]) + window - now
    end

    return {
        0,
        0,
        math.max(0, retry_after)
    }
end

-- Generate a unique request ID.
local sequence_key = key .. ":sequence"

local sequence = redis.call(
    "INCR",
    sequence_key
)

local request_id = tostring(now) .. ":" .. tostring(sequence)

-- Add this request to the window.
redis.call(
    "ZADD",
    key,
    now,
    request_id
)

-- Keep the sorted set around only while it can contain
-- requests relevant to the window.
redis.call(
    "EXPIRE",
    key,
    window + 1
)

-- The sequence key is only used to generate unique members.
redis.call(
    "EXPIRE",
    sequence_key,
    window + 1
)

local remaining = limit - count - 1

return {
    1,
    remaining,
    0
}