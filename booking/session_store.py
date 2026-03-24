import redis
from urllib.parse import urlparse

from config import REDIS_URL, SESSION_TTL_SECONDS
from booking.session import BookingSession
from logger import get_logger

logger = get_logger(__name__)

SESSION_PREFIX = "session:"

#convert password at the redis link to *** 
def _parse_redis_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        if parsed.password:
            return url.replace(parsed.password, "***")
        return url
    except Exception:
        return "<unparseable url>"

class RedisSessionStore:

    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True) #from_url = method from redis to make a conn with server
        self._status_check() #automaticly check the conn after being called

    #check connection of redis
    def _status_check(self) -> None:
        try:
            self.client.ping() #ping redis server, except happen if conn not working
            logger.info("Redis connection worked", extra={"url": _parse_redis_url(REDIS_URL)})
        #catch spesific ConnectionError
        except redis.ConnectionError as e:
            logger.error(
                "Redis connection failed: redis is not running",
                extra={"url": _parse_redis_url(REDIS_URL), "error": str(e)},
                exc_info=True
            )
            raise #raise will show error at the redis start up, not silently on first user request
    
    #return the key of session memory, to prevent duplication of key data on redis in the future
    def _key_session(self, user_id: str) -> str:
        return f"{SESSION_PREFIX}{user_id}"
    
    #return BookingSession if there is session, None if there isnt
    def get(self, user_id: str) -> BookingSession | None:
        try:
            raw = self.client.get(self._key_session(user_id))
            if not raw:
                return None
            return BookingSession.from_json(raw)
        except Exception as e:
            logger.error("Failed to get session", extra={"user_id": user_id, "error": str(e)}, exc_info=True)
            return None
    
    #save session to redis and set total of time saved in redis
    def save(self, session: BookingSession) -> None:
        try:
            #setex = set session and expiry 
            self.client.setex(
                self._key_session(session.user_id),
                SESSION_TTL_SECONDS,
                session.to_json()
            )
        except Exception as e:
            logger.error("Failed to save session", extra={"user_id": session.user_id, "error": str(e)}, exc_info=True)

    #delete user session at redis (cancel, booking confirmed)
    def delete(self, user_id: str) -> None:
        try:
            self.client.delete(self._key_session(user_id))
            logger.debug("Session deleted", extra={"user_id": user_id})
        except Exception as e:
            logger.error("Failed to delete session", extra={"user_id": user_id, "error": str(e)}, exc_info=True)
    
    #get user session at redis or created new session
    def get_or_create(self, user_id: str) -> BookingSession:
        session = self.get(user_id)
        if not session:
            session = BookingSession(user_id)
            logger.debug("New session created", extra={"user_id": user_id})
        return session