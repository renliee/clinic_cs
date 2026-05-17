"""
seed the initial admin users from env vars (ADMIN_EMAIL, ADMIN_PASSWORD).
- running multiple times is safe
- if admin doesnt exist, creates it 
- if admin already exist, print status and exits without changes
run: python -m scripts.seed_admin
"""
import asyncio
import sys

from db.database import AsyncSessionLocal
from auth.repository import UserRepository
from auth.security import hash_password
from config import settings
from logger import get_logger
from models.user import UserRole

logger = get_logger(__name__)

async def seed_admin() -> int:
    """return 0 on success, 1 on configuration error, 2 on db error"""
    #1. validate env vars are present
    if not settings.admin_email or not settings.admin_password:
        logger.error(
            "Seed failed: ADMIN_EMAIL and ADMIN_PASSWORD must be set in env"
        )
        return 1

    #2. Validate password is not weak
    if len(settings.admin_password) < 8:
        logger.error("Seed failed: ADMIN_PASSWORD must be at least 8 characters")
        return 1

    email = settings.admin_email
    plain_password = settings.admin_password

    #3. Check if admin already exists
    async with AsyncSessionLocal() as session:
        existing = await UserRepository.get_by_email(session, email)
        if existing is not None:
            logger.info(
                "Admin already exists, skipping",
                extra={
                    "email": email,
                    "id": str(existing.id),
                    "role": existing.role.value,
                    "is_active": existing.is_active,
                },
            )
            print(f"Admin already exists: {email} (id={existing.id})")
            print(f"Role: {existing.role.value}")
            return 0
        
     #4. admin account has not been created, creating new admin account
        try:
            hashed = hash_password(plain_password)
            user = await UserRepository.create_user(
                session=session,
                email=email,
                hashed_password=hashed,
                role=UserRole.ADMIN,
            )
            await session.commit()
            logger.info("Admin user created", extra={"email": email, "id": str(user.id)})

            print(f"Admin created successfully:")
            print(f"Email: {user.email}")
            print(f"ID: {user.id}")
            print(f"Role: {user.role.value}")
            print(f"Created at: {user.created_at}")
            print(f"Login to that admin account is now possible")
            return 0
        
        except Exception as e:
            logger.error("Seed failed: db error", exc_info=True)
            print(f"Failed to create admin: {e}")
            return 2


if __name__ == "__main__":
    exit_code = asyncio.run(seed_admin()) #value either be 0/1/2
    sys.exit(exit_code) #exit code convention: 0 = success, other = failure. used to define other files (e.g. run login_admin_account.py only if this file returns 0)