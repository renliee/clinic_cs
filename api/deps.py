"""file for singleton factory for DB and Redis session store"""

from booking.database import BookingDB
from booking.session_store import RedisSessionStore

#define _db and _store value as None for the first time
_db: BookingDB | None = None
_store: RedisSessionStore | None = None

def get_db() -> BookingDB:
    global _db
    if _db is None:
        _db = BookingDB()
    return _db

def get_store() -> RedisSessionStore:
    global _store
    if _store is None:
        _store = RedisSessionStore()
    return _store