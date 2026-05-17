"""
FastAPI auth dependencies (for access token)
- get_current_user: extract jwt from authorization header, validates, return corresponding User with that token from DB.
- require_role: factory that builds role checking dependencies. 
"""
from uuid import UUID

import jwt as pyjwt  #pyjwt package, aliased to avoid shadowing
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_handler import decode_token, ACCESS_TOKEN_TYPE
from auth.repository import UserRepository
from db.database import get_db
from logger import get_logger
from models.user import User, UserRole

from collections.abc import Callable, Coroutine
from typing import Any

logger = get_logger(__name__)

#bearer token (string that carry a token), carry jwt from browser header to fastapi as verification
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") #parse the string into a specific token string with tokenUrl as the url endpoint

async def get_current_user(
    token: str = Depends(oauth2_scheme), #oauth2 look at the incoming request of auth header, extract the token string after bearer, give it to this variable.
    db: AsyncSession = Depends(get_db) #get the session generator to connect to db before running this function
) -> User:
    """
    Validate JWT access token and return the corresponding active User (user is logged in).
    Raise HTTPException(401) for missing/expired/invalid token, wrong token type, user not found, user deactivated.
    """
    #similar exception for every error so the attackers wont notice the extra details about why our system refuse that token (user enumiration).
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}, #response header to client at browser, so they kknow the problem was they need a valid bearer token
    )

    #1. decode to its payload dict form and validate jwt (signature, expiry, format, etc)
    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError: #if access token expired
        logger.info("Auth failed: token expired")
        raise credentials_exception
    except pyjwt.InvalidTokenError: #other failure
        logger.warning("Auth failed: invalid token")
        raise credentials_exception
    
    #2. verify this is an access token, not refresh token
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        logger.warning("Auth falied: wrong token type", extra={"type": payload.get("type")})
        raise credentials_exception

    #3. extract user_id from 'sub' in payload dict
    user_id_str = payload.get("sub")
    if user_id_str is None:
        logger.warning("Auth failed: token missing sub key")
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str) #convert string to UUID type for db lookup (will run error if UUID format is wrong)
    except ValueError:
        logger.warning("Auth failed: sub is not a valid UUID")
        raise credentials_exception
    
    #4. Fetch fresh user from DB (so role/active are always current) 
    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        logger.warning("Auth failed: user not found", extra={"user_id": user_id_str})
        raise credentials_exception
    
    #5. Reject deactivate users (admin could disable account without deleting them)
    if not user.is_active:
        logger.info("Auth failed: user deactivated", extra={"user_id": user_id_str})
        raise credentials_exception
    
    return user

#the type hint refers to _role_checker as an async function
def require_role(allowed_roles: list[UserRole]) -> Callable[[User], Coroutine[Any, Any, User]]: #Callable[[User] x]: function that accept 'User' as param and return 'x'; Coroutine[Any, Any, x]: async function that return x;
    """
    Factory that build a FastAPI dependency enforcing role based access.
    e.g. usage: 
    '@router.get("/admin/something")
    async def endpoint(user: User = Depends(require_role[UserRole.ADMIN]))' #meaning this endpoints could only be used by ADMIN role.
    
    return 403 when user is authenticated but lack of permission.
    """
    async def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        #depends on get_current_user, so authentication happens first (401), then role check (403)
        if current_user.role not in allowed_roles:
            logger.warning(
                "Authorization failed: insufficient role",
                extra={
                    "user_id": str(current_user.id),
                    "user_role": current_user.role.value,
                    "required_roles": [r.value for r in allowed_roles],
                },
            )
            #raise this if user is unauthorized
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    
    return _role_checker #without () bcs we dont want the function to execute now