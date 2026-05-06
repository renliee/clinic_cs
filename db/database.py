"""
SQLAlchemy async engine + session management.
Engine is global (1 per app).
"""

from typing import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings
from logger import get_logger

logger = get_logger(__name__)

#engine that make a connection to db
engine = create_async_engine(
    settings.database_url,
    echo=False, #debugging purpose (print the form of sql query from the sqlalchemy)
    pool_size=5, #5 connection (using session) is always ready and 10 as extra if busy
    max_overflow=10,
    pool_pre_ping = True, #check connection first before using
)

#session generator (AsyncSessionLocal is a class bcs of async_sessionmaker) 
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession, #will use AsyncSession instead of Session only
    expire_on_commit=False,  #after commit, could still access the data (by default, python consider that data as stale and cant be access without session)
    autoflush=False, #do flush manually, not automatically  
)

#function with DeclarativeBase is a table class (determine a table consist of what column)
class Base(DeclarativeBase):
    pass

#FastAPI dependency
async def get_db() -> AsyncIterator[AsyncSession]: #asynciterator: this function type is async generator; asyncsession: this function return AsyncSession 
    #at the end, close session automatically bcs of with
    async with AsyncSessionLocal() as session:
        try:
            yield session #give sessin to caller
        except Exception:
            #rollback to previous state (atomic transaction), then raise an error
            await session.rollback() 
            raise