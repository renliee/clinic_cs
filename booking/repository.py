"""
- Booking repository (Async data access for bookings table).
- Repository doesnt commit, caller decide when to.
- Return orm Booking object | None 
"""

from datetime import date, datetime, time
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession #AsyncSession: middleman between db and python (method: add, delete, execute, rollback, flush, commit,get)

from logger import get_logger
from models.booking import Booking
from models.schemas import BookingStatus

logger = get_logger(__name__)

def to_dict(booking: Booking | None) -> dict | None:
    """Convert booking object to dict as the rest of the app expect it"""
    if booking is None:
        return None
    
    return {
        "id": booking.id,
        "booking_id": booking.booking_id,
        "user_id": booking.user_id,
        "nama": booking.nama,
        "lokasi": booking.lokasi,
        "treatment": booking.treatment,
        "tanggal": booking.tanggal.isoformat(),
        "jam": booking.jam.strftime("%H:%M"),
        "status": booking.status.value if booking.status else None,
        "notes": booking.notes,
        "created_at": booking.created_at.isoformat() if booking.created_at else None,  #bcs of session.refresh(booking) at create, wont cause error (handle python check to DB that requires async in a sync env)
        "updated_at": booking.updated_at.isoformat() if booking.updated_at else None,
        "confirmed_at": booking.confirmed_at.isoformat() if booking.confirmed_at else None,
    }


class BookingRepository:
    """Pure database access. No business logic, etc"""

    #READ
    @staticmethod
    async def get_by_booking_id(session: AsyncSession, booking_id: str) -> Booking | None:
        """get booking filtered by booking id"""
        data = select(Booking).where(Booking.booking_id == booking_id) #select(Booking) in raw sql = SELECT * FROM bookings
        result = await session.execute(data) #execute the query to databases
        return result.scalar_one_or_none() #return 1 or 0 row result
    
    @staticmethod
    async def get_by_id(session: AsyncSession, id: int) -> Booking | None:
        """get booking filtered by primary key id"""
        return await session.get(Booking, id) #AsyncSession method to fetch using primary key: .get(databse table, primary key value)

    @staticmethod
    async def list_by_user(
        session: AsyncSession, 
        user_id: str, 
        status: BookingStatus | None = None,
    ) -> Sequence[Booking]:
        """get booking filtered by user id (each user could have multiple booking)"""
        data = select(Booking).where(Booking.user_id == user_id)
        if status is not None:
            data = data.where(Booking.status == status)

        data = data.order_by(Booking.created_at.desc()) #sort the booking by created_at (descending: newest to oldest)
        result = await session.execute(data)
        return result.scalars().all()
    
    @staticmethod
    async def list_by_status(
        session: AsyncSession, 
        status: BookingStatus | None = None,
    ) -> Sequence[Booking]:
        """get booking filtered by status (each user could have multiple booking)"""
        data = select(Booking) #select(Booking) in raw sql = SELECT * FROM bookings
        if status is not None:
            data = data.where(Booking.status == status)
        
        data = data.order_by(Booking.created_at.desc())
        result = await session.execute(data)
        return result.scalars().all()
    
    @staticmethod
    async def find_active_duplicate(
        session: AsyncSession,
        user_id: str,
        tanggal: date,
        jam: time,
    ) -> Booking | None :
        """find a booking with same user, date, and time that isnt canceled"""
        data = select(Booking).where(
            Booking.user_id == user_id,
            Booking.tanggal == tanggal,
            Booking.jam == jam,
            Booking.status != BookingStatus.CANCELED,
        )
        result = await session.execute(data)
        return result.scalar_one_or_none() 
    
    #WRITE
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: str,
        nama: str,
        lokasi: str,
        treatment: str,
        tanggal: date,
        jam: time,
    ) -> Booking:
        """
        create a new booking then autogenerate booking_id like 'BK001'.
        booking_id uses the auto increment id so we insert first (flush to get id) then set booking id.
        """
        booking = Booking(
            user_id=user_id,
            nama=nama,
            lokasi=lokasi,
            treatment=treatment,
            tanggal=tanggal,
            jam=jam,
            status=BookingStatus.PENDING,
            booking_id="",  # placeholder; set it after flush
        )
        session.add(booking)
        await session.flush() #first flush to insert booking and generate the 'id'

        booking.booking_id = f"BK{booking.id:03d}" #using that new id, generate the booking_id
        await session.flush() #second flush to fill the booking id
        await session.refresh(booking) #to update the booking (sqlalchemy object so that updated_at and created_at is not "?", but NULL) 
        return booking #return booking object 

    @staticmethod
    async def update_status(
        session: AsyncSession,
        booking_id: str,
        status: BookingStatus,
        notes: str | None = None,
    ) -> Booking | None:
        """
        Update booking status (optionally notes) and set confirmed_at when status = CONFIRMED.
        Return the updated booking or None if booking not found.
        """
        booking = await BookingRepository.get_by_booking_id(session, booking_id)
        if booking_id is None:
            return None
        
        booking.status = status
        if notes is not None:
            booking.notes = notes
        #set the confirmed time
        if status == BookingStatus.CONFIRMED and booking.confirmed_at is None:
            booking.confirmed_at = datetime.utcnow()

        await session.flush() #flush the changes now, wait for commit at the caller
        return booking #return booking object with that new status

    @staticmethod
    async def delete(session: AsyncSession, booking_id: str) -> bool:
        """return True if deleted, false if not found"""
        booking = await BookingRepository.get_by_booking_id(session, booking_id)
        if booking is None:
            return False
        
        await session.delete(booking)
        await session.flush()
        return True
    
    #Aggregates (used by stats endpoint)
    @staticmethod
    async def count_by_status(
        session: AsyncSession,
        status: BookingStatus,
    ) -> int:
        """count total booking based on status"""
        data = select(func.count()).select_from(Booking).where(Booking.status == status) #func.count(): SELECT COUNT(*); select_from(Booking): FROM bookings; WHERE status = 'PENDING;
        result = await session.execute(data)
        return result.scalar_one() #return 1 value (the number of count)