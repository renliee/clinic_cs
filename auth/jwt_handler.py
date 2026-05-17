"""
JWT using pyjwt. (jwt seperated by 3 parts: "Header.Payload.Signature"); Header: token info like algo and type; Payload: information the jwt brings on; Signature: HMAC (need to know secret key to modify this, even if attacker manage to break in, he cant modify to get other roles, extend the expiry, etc)
- access token: short lived (15 min), sent in response body, stored in memory by frontend.
- refresh token: long lived (7 days), sent as httpOnly cookie, stored in redis.
- jti used by redis for refresh validation.
"""

import jwt
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from config import settings
from models.user import UserRole

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_info: dict | None = None,    
) -> tuple[str, str]:
    """
    internal helper tha create jwt token and return (token_string, jti).
    jti then will be stored at redis.
    """
    jti = str(uuid4()) #generate unique id using uuid4
    now = datetime.now(timezone.utc)

    #defining the payload that the token carry on (type as the extra info, not official args from jwt)
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now, #issued at (when the token is made)
        "exp": now + expires_delta, 
    }

    #add extra info if there is
    if extra_info:
        payload.update(extra_info)

    #encode the payload into jwt token, we need the secret key and name of algorithm that will be used
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm, #no need to make a whitelist bcs this is system to system 
    )

    return token, jti

def create_access_token(user_id: str, role: UserRole) -> tuple[str, str]:
    """
    create access token that carry user id and role.
    returns (token, jti). jti isnt frequently used for acces token, consistentcy purpose.
    """
    expires = timedelta(minutes=settings.access_token_expire_minutes) #set expiry

    #create then return that token with role as an extra info 
    return _create_token(
        subject=user_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=expires,
        extra_info={"role": role.value}, #.value to access str in enum types
    )

def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    create refresh token (no need role, role is fetched from DB on refresh).
    returns (token, jti) then caller must store jti in redis.
    """
    expires = timedelta(days=settings.refresh_token_expire_days)

    #create then return that token
    return _create_token(
        subject=user_id,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=expires,
    )

def decode_token(token: str) -> dict:
    """
    decode and validate jwt token then returns the payload dict if valid.
    raises jwt.ExpiredSignatureError if expired, jwt.InvalidTokenError for other failure
    caller must catch this exception.
    """
    #decode('the token', 'secret key', 'algorithm in list')
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm], #use list as a way to define a whitelist (so attacker can't modify the header of jwt to downgrade the algorithm)
    )