"""
Async Redis storage for refresh token jti's.
- format: refresh_token:{jti} -> user_id
- TTL match refresh token expiry.
- Store on token inssuance, lookup on refresh (to generate access token), and delete on rotation/logout.
""" 
import redis.asyncio as redis
from config import settings
from logger import get_logger

logger = get_logger(__name__)

REFRESH_KEY_PREFIX = "refresh_token:" #unique prefix, same as session_store that uses 'session:' as unique prefix

class RefreshTokenStore:
    """Async redis client for refresh token jti storage"""
    #decode_response=True: redis return string instead of bytes (redis store data in bytes form)
    def __init__(self):
        self._client = redis.from_url(settings.redis_url, decode_responses=True)
        logger.info("RefreshTokenStore connected to Redis")

    def _key(self, jti: str) -> str:
        "return unique keyword 'key:jti' prevent duplication of key data"
        return f"{REFRESH_KEY_PREFIX}{jti}"
    
    async def store(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        """store a jti with ttl info"""
        await self._client.setex(
            self._key(jti), #keyword
            ttl_seconds, #expiry 
            user_id #value of user id
        )
        logger.info("Refresh token stored", extra={"jti": jti, "ttl": ttl_seconds})

    async def lookup(self, jti: str) -> str | None:
        """
        Return user_id corresponding with the jti, or None if not found.
        Not found means: token was logged out, already rotated, or never existed.
        """
        return await self._client.get(self._key(jti)) #return the value of that key
    
    async def delete(self, jti: str) -> bool:
        """
        Delete a jti. return True if exist, False otherwise.
        Used on: logout, refresh (delete old jwt before creating new tp rotate)
        """
        deleted = await self._client.delete(self._key(jti)) #return 1 if found and deleted, 0 if not found
        logger.info("Refresh token deleted", extra={"jti": jti, "existed": bool(deleted)})
        return bool(deleted)
    
    async def delete_all_for_user(self, user_id: str) -> int:
        """
        Nuke all refresh tokens for a spesific user. Used for "logout all sessions".
        Return number of tokens deleted.
        Use async at for loop bcs its iterating over async generator (each item in redis is I/O)
        """
        count = 0
        async for key in self._client.scan_iter(match=f"{REFRESH_KEY_PREFIX}*"): #scan_iter: iterate through all key that matched '{REFRESH_KEY_PREFIX}*'
            value = await self._client.get(key) #value now is user_id
            if value == user_id:
                await self._client.delete(key)
                count += 1
        logger.info("Deleted all refresh token for user", extra={"user_id": user_id, "count": count})
        return count