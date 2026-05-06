"""
SQLAlchemy orm model for the users table.
Used for admin authentification
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base

class UserRole(str, PyEnum):
    """User roles Enum. Admin only for now"""
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    VIEWER = "VIEWER"

class User(Base):
    __tablename__ = "users"

    #primary key using UUID (not int)
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), #postgres save this column as UUID object, not UUID string
        primary_key=True, #constraint that is unique, not null, indexed
        default=uuid4, #how to generate diff UUID for every admin
    )

    #login credentials
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    #authorization
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"), #postgres save this column as Enum object (named 'user_role')
        default = UserRole.ADMIN,
    )

    #status
    is_active: Mapped[bool] = mapped_column(default=True) #to easily deactivate/activate admin

    #timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), #postgres automatically generate value of time right now on the first insert
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True, #null is allowed bcs first time login doesnt generate last_login_at
    )
    
    def __repr__(self) -> str:
        return f"<User_id={self.id} email={self.email} role={self.role}>" #this will be printed if we print 'User' class as an object