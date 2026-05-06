"""
SQLAlchemy orm for booking table.
This file is for booking schema.
"""

from datetime import datetime, date, time
from sqlalchemy import Date, DateTime, Enum as SQLEnum, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column #Mapped: alchemy orm 2.0 type annotation (used at postgres type also), mapped_column: sql spesific options eg: primary_key, unique, index, onupdate etc

from db.database import Base
from models.schemas import BookingStatus

class Booking(Base):
    __tablename__ = "bookings"

    #primary key and id
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)

    #booking details
    nama: Mapped[str] = mapped_column(String(100))
    lokasi: Mapped[str] = mapped_column(String(100))
    treatment: Mapped[str] = mapped_column(String(100))

    #real date and time columns
    tanggal: Mapped[date] = mapped_column(Date)
    jam: Mapped[time] = mapped_column(Time)

    #status (using Enum from BookingStatus)
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name="booking_status"), #sql verify status column using the enum from BookingStatus (now validated by sql dan python) 
        default=BookingStatus.PENDING,
        index = True,
    )

    #optional
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    #db generate "created_at" automatically after a new row is sent
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), #store timezone aware datetime (utc)
        server_default=func.now(), #func.now(): sqlalchemy method to fill current database time (representative of SQL NOW() function)
        index=True,
    )
    #db generate "updated_at" automatically if an info in that row is updated
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        onupdate=func.now(), 
        nullable=True,
    )
    #update manually when the booking is confirmed
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,  
    )

    #magic method: similar to "__str__" but "__repr__" is for developer (debug/check), while "__str__" for user
    def __repr__(self) -> str:
        return f"<Booking id={self.id} booking_id={self.booking_id} status={self.status}>" 
        #if the object with this class (Booking) is printed, will return line above. 