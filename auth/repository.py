"""
- User repository (Async data access for users table).
- Repository does not commit, the caller decide when to.
- Return orm User object | None.
"""
from uuid import UUID #type check for uuid4 at primary key users column
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from logger import get_logger
#User is orm database table that point to 'users' table
from models.user import User, UserRole

class UserRepository:
    """Pure database access for user ('users' table). No business logic"""

    #READ
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: UUID) -> User | None:
        """get user filtered by primary key (UUID)"""
        return await session.get(User, user_id) #asyncsession common method to fetch using primary key; .get(databse table, primary key value)
    
    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        """get user filtered by email (used at login)"""
        data = select(User).where(User.email == email)
        result = await session.execute(data)
        return result.scalar_one_or_none() 
    
    #WRITE
    @staticmethod
    async def update_last_login(session: AsyncSession, user: User) -> User:
        """set user last_login_at to newest timestamp (now). Caller commits."""
        user.last_login_at = datetime.now(timezone.utc)
        await session.flush()
        return user
    
    @staticmethod
    async def create_user(
        session: AsyncSession,
        email: str,
        hashed_password: str,
        role: UserRole,
    ):
        """
        create new user. caller commits.
        raise sqlalchemy.exc.IntegrityError if email already exists (unique constraint).
        """
        #define user as User object
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
        )
        session.add(user) #add to 'users' table, bcs user is User object which is from 'users' table
        await session.flush()
        await session.refresh(user) #generate auto generated fields (id and create_at)
        return user