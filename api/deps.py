"""Dependency DB and Redis for FastAPI routes"""

from db.database import get_db #get_db will return AsyncSession (from AsyncSession generator that connect the db through engine)
from booking.session_store import RedisSessionStore

#define _store value as None for the first time
_store: RedisSessionStore | None = None

def get_store() -> RedisSessionStore:
    global _store
    if _store is None:
        _store = RedisSessionStore()
    return _store

__all__ = ["get_db", "get_store"]