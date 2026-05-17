"""Dependency DB and Redis for FastAPI routes"""

from db.database import get_db #get_db will return AsyncSession (from AsyncSession generator that connect the db through engine)
from booking.session_store import RedisSessionStore #session redis
from booking.stats_cache import StatsCache #booking stats cache redis
from auth.refresh_store import RefreshTokenStore #auth redis

#define both redis store value as None for the first time
_store: RedisSessionStore | None = None
_refresh_store: RefreshTokenStore | None = None
_stats_cache: StatsCache | None = None

def get_store() -> RedisSessionStore:
    global _store
    if _store is None:
        _store = RedisSessionStore()
    return _store

def get_refresh_store() -> RefreshTokenStore:
    global _refresh_store
    if _refresh_store is None:
        _refresh_store = RefreshTokenStore()
    return _refresh_store

def get_stats_cache() -> StatsCache:
    global _stats_cache
    if _stats_cache is None:
        _stats_cache = StatsCache()
    return _stats_cache

__all__ = ["get_db", "get_store", "get_refresh_store", "get_stats_cache"]