"""
Test the BookingRepository class in booking/repository.py
Run: python -m scripts.test_repository
"""
import asyncio
from datetime import date, time

from db.database import AsyncSessionLocal
from booking.repository import BookingRepository, to_dict
from models.schemas import BookingStatus

async def main():
    async with AsyncSessionLocal() as session:
        booking = await BookingRepository.create(
            session,
            user_id="test_user_001",
            nama="Ren",
            lokasi="Bekasi",
            treatment="Facial",
            tanggal=date(2026, 6, 15),
            jam=time(14, 0),
        )
        await session.commit()
        print(f"Created: {booking}")
        print(f"As dict: {to_dict(booking)}")
        booking_id = booking.booking_id

        print("\nGet by booking_id")
        data = await BookingRepository.get_by_booking_id(session, booking_id)
        print(f"Fetched: {data}")
        assert data is not None, "booking id not found" #assert CONDITION, "info" (if condition false will cause error)

        print("\nDuplicate check")
        dup = await BookingRepository.find_active_duplicate(
            session, "test_user_001", date(2026, 6, 15), time(14, 0)
        )
        print(f"Duplicate found: {dup}")
        assert dup is not None and dup.id == booking.id #make sure it is the same booking id at the same time

        print("\nUpdate status (CONFIRMED)")
        updated = await BookingRepository.update_status(
            session, booking_id, BookingStatus.CONFIRMED, notes="confirmed via test"
        )
        await session.commit()
        print(f"Status: {updated.status}, confirmed_at: {updated.confirmed_at}")
        assert updated.confirmed_at is not None

        print("\nList by status")
        confirmed = await BookingRepository.list_by_status(session, BookingStatus.CONFIRMED)
        print(f"CONFIRMED count: {len(confirmed)}")

        print("\nDelete (cleanup)")
        deleted = await BookingRepository.delete(session, booking_id)
        await session.commit()
        print(f"Deleted: {deleted}")


if __name__ == "__main__":
    asyncio.run(main()) #to run an async fucntion in a sync environment (fastapi is an async environment so no need asyncio)