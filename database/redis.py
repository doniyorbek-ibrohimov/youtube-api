import redis
import os

redis_blacklist = redis.Redis.from_url(
    os.getenv("REDIS_BLACKLIST_URL", "redis://localhost:6380/0"),
    decode_responses=True
)

redis_broker_url = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")