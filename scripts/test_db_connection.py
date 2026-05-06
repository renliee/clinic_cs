"""
To verify that sqlalchemy could talk to postgres
Run: python -m scripts.test_db_connection
"""

import asyncio
from sqlalchemy import text
from db.database import engine, AsyncSessionLocal

async def main():
    print("1. Raw connection test")
    #will return '1' if connection success
    async with engine.connect() as conn: #engine.connect(): low level way to connect to db 
        result = await conn.execute(text("SELECT 1 AS num")) #text: to execute raw sql query 
        row = result.one() #.one() return a row
        print(f"Answer: {row.num}") #if connected, row = {"num": 1}
    
    #will print version of postgres if works
    print("2. Session connection test")
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT version() AS pg_version")) #raw sql to show version of postgres using session
        version = result.scalar_one() #scalar.one() return a value
        print(f"Postgres version: {version[:60]}...")
    
    print("3. Connection pool")
    print(f"Pool size: {engine.pool.size()}")
    print(f"Checked out: {engine.pool.checkedout()}") #connection that is being used

    await engine.dispose() #close all pool connection and engine. clean up purpose

if __name__ == "__main__":
    asyncio.run(main()) #a way to run an async function in a non async env (no need to do in FastAPI, it was handled)