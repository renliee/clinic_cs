"""
Authetication routes :
- POST /api/auth/login = verify credentials, issue token pair (refresh + access)
- POST /api/auth/refresh = rotate refresh token (delete old jti, create new jti), issue new access token
- POST /api/auth/logout = clear cookie and delete refresh token from Redis
- GET  /api/auth/me = return current user's info as orm object

Access token: returned in response body (frontend stores in memory)
Refresh token: set as httpOnly cookies (frontend never sees them)

cookie (refresh token) only available at "/api/auth*" endpoints, bcs only "/api/auth/logout" and "/api/auth/refresh" need cookie (refresh token) to search for user jti in redis (delete or refresh that jti) 
while access token is used at other restricted endpoints e.g. '/api/admin*'
"""

from uuid import UUID
import jwt as pyjwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status #usually fastapi build the response automatically from our return value, but on this one, cookies (refresh token) need to be attached to that response which normal return cant.
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_refresh_store
from auth.dependencies import get_current_user
from auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    REFRESH_TOKEN_TYPE,
)
from auth.refresh_store import RefreshTokenStore
from auth.repository import UserRepository
from auth.security import verify_password
from config import settings
from logger import get_logger
from models.schemas import LoginRequest, TokenResponse, UserResponse
from models.user import User

logger = get_logger(__name__)
#APIRouter: FastAPI method of related routes from separate files, will be combined at main.py
router = APIRouter(prefix="/api/auth", tags=["auth"]) #cookie will only works at this router endpoinds

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_MAX_AGE = settings.refresh_token_expire_days * 24 * 60 * 60 #7 days but in seconds

def _set_refresh_cookie(response: Response, token: str) -> None:
    """
    Set the refresh token as an httpOnly cookie. Used by login + refresh.
    USUALLY we just return and doesnt modify the response (response is always sent along with the body), but now we modify response by adding cookie (refresh token)
    """
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token, 
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True, #Javascript cant read this cookie (XSS protection: if attacker injects malicious javascript into this page, refresh token cant be stolen, bcs JS cant read refresh token)
        secure=False, #set True in production (requires HTTPS)
        samesite="lax", #block most CSRF
        path="/api/auth", #cookie only sent to /api/auth* (not to /api/admin*, etc)
    )

def _clear_refresh_cookie(response: Response) -> None:
    """clear the refresh cookie from the response. Used by logout"""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth", #must match path used when setting
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_store: RefreshTokenStore = Depends(get_refresh_store),
):
    """
    verify email and password, issue access and refresh token on success.
    return 401 for: unknown email, wrong password, deactivated account.
    all will raise same message to prevent user enumiration.
    """
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    #1. look up user
    user = await UserRepository.get_by_email(db, credentials.email)
    if user is None:
        logger.info("Login failed: email not found", extra={"email": credentials.email})
        raise invalid_credentials
    
    #2. verify password
    if not verify_password(credentials.password, user.hashed_password):
        logger.info("Login failed: wrong password", extra={"email": credentials.email})
        raise invalid_credentials
    
    #3. check account active
    if not user.is_active:
        logger.info("Login failed: account deactivated", extra={"email": credentials.email})
        raise invalid_credentials
    
    #4. update last_login_at
    await UserRepository.update_last_login(db, user)

    #5. generate token pair
    user_id_str = str(user.id) #convert UUID to str for jwt sub 
    access_token, _access_jti = create_access_token(user_id_str, user.role)
    refresh_token, refresh_jti = create_refresh_token(user_id_str)

    #6. store refresh jti in redis 
    refresh_ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    await refresh_store.store(refresh_jti, user_id_str, refresh_ttl_seconds)

    #7. commit DB changes (last_login_at update)
    await db.commit()

    #8. set refresh cookies
    _set_refresh_cookie(response, refresh_token)
    logger.info("Login successful", extra={"user_id": user_id_str, "email": user.email})

    #9. return access token in body to frontend
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME), #Cookie(): look at incoming request's cookies, find one named {alias}
    db: AsyncSession = Depends(get_db),
    refresh_store: RefreshTokenStore = Depends(get_refresh_store),
):
    """
    Rotate refresh token. old jti is deleted before new one  is issued.
    failures that will return 401:
    - No cookie present 
    - JWT decode failure 
    - wrong token type (access masquerading as refresh)
    - jti not in redis (already used or logout)
    - sub payload doesnt match user_id in redis
    - user no longer exist or deactivated
    """
    invalid_refresh = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    #1. cookie must be present
    if refresh_token is None:
        logger.info("Refresh failed: no cookie")
        raise invalid_refresh
    
    #2. decode JWT
    try:
        payload = decode_token(refresh_token)
    except pyjwt.ExpiredSignatureError:
        logger.info("Refresh failed: token expired")
        raise invalid_refresh
    except pyjwt.InvalidTokenError: #other error
        logger.warning("Refresh failed: invalid token")
        raise invalid_refresh
    
    #3. must be a refresh token, not access
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        logger.warning("Refresh failed: wrong token type", extra={"got": payload.get("type")})
        raise invalid_refresh

    #4. exctract payload to get user id and jti
    old_jti = payload.get("jti")
    user_id_str = payload.get("sub")
    if not old_jti or not user_id_str:
        logger.warning("Refresh failed: missing jti or sub")
        raise invalid_refresh
    
    #5. look up jti in redis 
    stored_user_id = await refresh_store.lookup(old_jti)
    if stored_user_id is None:
        logger.warning("Refresh failed: jti not in Redis (reuse or logout)", extra={"jti": old_jti})
        raise invalid_refresh
    
    #6. check (redis jti must match jwt payload sub)
    if stored_user_id != user_id_str:
        logger.error(
            "Refresh failed: sub and Redis user id mismatch",
            extra={"jwt_sub": user_id_str, "redis_user": stored_user_id, "jti": old_jti},
        )
        raise invalid_refresh
    
    #7. delete old jti 
    await refresh_store.delete(old_jti)
    
    #8. fetch fresh user (is_active)
    try: 
        user_id = UUID(user_id_str)
    except ValueError:
        logger.warning("Refresh failed: sub is not a valid UUID")
        raise invalid_refresh
    
    user = await UserRepository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        logger.warning()
        raise invalid_refresh

    #9. issue new token pair
    new_access_token, _ = create_access_token(user_id_str, user.role)
    new_refresh_token, new_refresh_jti = create_refresh_token(user_id_str) 

    #10. store new jti in redis
    refresh_ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    await refresh_store.store(new_refresh_jti, user_id_str, refresh_ttl_seconds)

    #11. set the new cookies at response
    _set_refresh_cookie(response, new_refresh_token) #add cookie to the response object
    logger.info("Token refreshed", extra={"user_id": user_id_str, "old_jti": old_jti, "new_jti": new_refresh_jti})

    #return access token in body to frontend (cookie automatically returned, bcs cookie is in Response)
    return TokenResponse(
        access_token=new_access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME), #Cookie(): look at incoming request's cookies, find one named {alias}
    refresh_store: RefreshTokenStore = Depends(get_refresh_store),
):
    """
    Logout the current session. Always return 204 (no content) even on some failures bcs logout should always succed from the client perspective.
    This endpoint only invalidates current session, other device/session for the same user remain logged in (each has its own jti in redis). Use delete_all_for_user to logout all sessions.
    """
    _clear_refresh_cookie(response) #clear the cookies no matter what will happen later. 

    #if no cookies was sent, nothing to do
    if refresh_token is None:
        logger.info("Logout: no refresh cookie to clean up")
        return
    #extract jti from refresh token and delete it from redis.
    try:
        payload = decode_token(refresh_token)
        jti = payload.get("jti")
        if jti:
            await refresh_store.delete(jti)
            logger.info("Logout: refresh token deleted from Redis", extra={"jti": jti})
    #handle invalid token, expired, no redis cleanup possible, etc. (important part cookie was already gone)
    except pyjwt.InvalidTokenError:
        logger.info("Logout: invalid token, only cleared cookie (redis jti not yet)")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)): #get_current_user: no need to pass the token through args bcs frontend will sent the bearer token through the header and will be catched by oauth2
    """
    Return current authenticated user's info as orm object. Could be used by frontend to make UI ("logged in as Ren") and verify auth status on app load.
    requires valid access token in Authorization: Bearer header.
    """ 
    return current_user