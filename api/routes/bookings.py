"""Admin API routes for booking management.
These endpoints are for clinic admin dashboard"""

from fastapi import APIRouter, HTTPException, Depends, Query #Depends: before executing this endpoint, execute the function first (get the dependency ready first). 
from sqlalchemy.ext.asyncio import AsyncSession
from models.schemas import(
    Booking,
    BookingStatus,
    BookingStatusUpdate,
    BookingListResponse,
)
from booking.repository import BookingRepository, to_dict
from api.deps import get_db
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    status: BookingStatus | None = Query(None, description="Filter by status"), #Query: set None as default and add description at the parameter (help knowing what to fill this with)
    db: AsyncSession = Depends(get_db),
):
    """List all bookings, optionally filtered by status"""
    bookings = await BookingRepository.list_by_status(db, status) #sequence of booking object
    booking_dicts = [to_dict(b) for b in bookings] #convert every booking object to dict 
    return BookingListResponse(bookings=booking_dicts, total=len(booking_dicts))


@router.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(
    booking_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """Get a single booking by booking id"""
    booking = await BookingRepository.get_by_booking_id(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail=f"Booking id {booking_id} not found")
    
    return to_dict(booking)

#not using query bcs BookingStatusUpdate make the url too long and unsafe
@router.patch("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    update: BookingStatusUpdate,
    db: AsyncSession = Depends(get_db), 
):
    """
    Update booking status
    - Admin confirms a pending booking: PENDING -> CONFIRMED
    - Admin cancels: any -> CANCELED
    - Admin marks as done: CONFIRMED -> COMPLETED
    """
    existing = await BookingRepository.get_by_booking_id(db, booking_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")

    old_status = existing.status.value
    await BookingRepository.update_status(db, booking_id, update.status, update.notes)
    await db.commit() #commit the flush

    logger.info("Admin updated booking status", extra={
        "booking_id": booking_id,
        "old_status": old_status,
        "new_status": update.status.value,
    })

    return {"message": f"Booking id {booking_id} updated to {update.status.value}"}


@router.delete("/bookings/{booking_id}")
async def delete_booking(
    booking_id: str, 
    db: AsyncSession = Depends(get_db),
):
    """Delete a booking by booking id"""
    deleted = await BookingRepository.delete(db, booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Booking id {booking_id} not found")
    await db.commit() #commit the flush

    logger.info("Admin deleted booking", extra={"booking_id": booking_id})
    return {"message": f"Booking id {booking_id} deleted"}