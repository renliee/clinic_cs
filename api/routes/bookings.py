"""Admin API routes for booking management.
These endpoints are for clinic owner dashboard"""

from fastapi import APIRouter, HTTPException, Depends, Query
from models.schemas import(
    Booking,
    BookingStatus,
    BookingStatusUpdate,
    BookingListResponse,
)
from booking.database import BookingDB
from api.deps import get_db
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    status: BookingStatus | None = Query(None, description="Filter by status"),
    db: BookingDB = Depends(get_db),
):
    """List all bookings, optionally by status"""
    booking = db.get_bookings_status(status.value if status else None) #BookingStatus.<STATUS>.value will return string

    return BookingListResponse(bookings=booking, total=len(booking))


@router.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(booking_id: str, db: BookingDB = Depends(get_db)):
    """Get a single booking by booking id"""
    booking = db.get_booking(booking_id)

    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking id {booking_id} not found")
    
    return booking

#not using query bcs BookingStatusUpdate make the url too long and unsafe
@router.patch("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    update: BookingStatusUpdate,
    db: BookingDB = Depends(get_db), 
):
    """
    Update booking status
    - Admin confirms a pending booking: PENDING -> CONFIRMED
    - Admin cancels: any -> CANCELED
    - Admin marks as done: CONFIRMED -> COMPLETED
    """
    existing = db.get_booking(booking_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")

    db.update_status(booking_id, update.status.value, update.notes)
    logger.info("Admin updated booking status", extra={
        "booking_id": booking_id,
        "old_status": existing["status"],
        "new_status": update.status.value,
    })

    return {"message": f"Booking id {booking_id} updated to {update.status.value}"}


@router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, db: BookingDB = Depends(get_db)):
    """Delete a booking by booking id"""
    existing = db.get_booking(booking_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Booking id {booking_id} not found")
    
    db.delete_booking(booking_id)
    logger.info("Admin deleted booking", extra={"booking_id": booking_id})

    return {"message": f"Booking id {booking_id} deleted"}