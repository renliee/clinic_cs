"""
Redis cache for booking dashboard stats (Key: stats:admin:overview; Value: JSON-serialized stats dict)
Why we need cache: stats endpoint hits Postgres with 4 queries per call, admin dashboard stats refresh automatically every few seconds. 
Without caching = unnecessary DB load. With 30s TTL = at most 2 DB calls per minute, stats lag by max 30s.

FLOW: every DB change made, redis cache will be invalidated and redis cache is empty by that time.
next if admin click a button (action) to see the stats, query fresh data from db. If in 30 secs theres no action/change, 
delete the cache and no further actions, untill the admin click the view stats again and will fetch fresh data again.
"""
import json
import redis.asyncio as redis

from config import settings
from logger import get_logger

logger = get_logger(__name__)

#key prefix
STATS_KEY = "stats:admin:overview"
DEFAULT_TTL_SECONDS = 30

class StatsCache:
    """Redis Cache helper for the admin dashboard stats"""
    
    def __init__(self):
        self._client = redis.from_url(settings.redis_url, decode_responses=True)
        logger.info("StatsCache connected to Redis")

    async def get(self) -> dict | None:
        """
        Return cached stats dict if present, else None.
        Treats json deserialization errors as cache miss, caller then will fetch fresh from db.
        """
        raw = await self._client.get(STATS_KEY) #get the value of stats:admin:overview
        if raw is None:
            return None

        try:
            return json.loads(raw) #convert json string to python dict
        except json.JSONDecodeError:
            logger.warning("StatsCache value not parseable as JSON, treating as miss")
            return None
    
    async def set(self, stats: dict, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        """store stats as long as agreed TTL. caller decides whether to call this"""
        payload = json.dumps(stats) #convert python dict to json string
        await self._client.setex(STATS_KEY, ttl_seconds, payload) #setex: set and expiry. payload is the value inside the key. (format: STATS_KEY: payload)
        logger.debug("StatsCache was set", extra={"ttl": ttl_seconds})

    async def invalidate(self) -> bool:
        """
        Delete cached stats. Called when bookings changed so the next read shows fresh data instead of stale numbers.
        Returns True if a value was deleted, False if cache was already empty.
        """
        deleted = await self._client.delete(STATS_KEY)
        logger.info("StatsCache invalidated", extra={"existed": bool(deleted)})
        return bool(deleted)