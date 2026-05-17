"""
Admin API routes for booking management.
These endpoints are for clinic admin dashboard
"""
from fastapi import APIRouter, HTTPException, Depends, Query #Depends: before executing this endpoint, execute the function first (get the dependency ready first). 
from sqlalchemy.ext.asyncio import AsyncSession
from models.schemas import(
    Booking,
    BookingStatus,
    BookingStatusUpdate,
    BookingListResponse,
    StatsResponse,
)
from booking.repository import BookingRepository, to_dict
from api.deps import get_db
from auth.dependencies import require_role, get_current_user
from models.user import User, UserRole

#redis stats cache 
from booking.stats_cache import StatsCache
from api.deps import get_stats_cache 

from logger import get_logger
logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/admin", 
    tags=["admin"],
    #router level auth: every endpoints here requires a valid admin access token.
    #run the depends first, if user is authorized, then run the endpoints.
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)


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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db), 
    stats_cache: StatsCache = Depends(get_stats_cache),
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
    await stats_cache.invalidate() #invalidate the redis cache, bcs it has became a stale data due to this DB changes


    logger.info("Admin updated booking status", extra={
        "booking_id": booking_id,
        "old_status": old_status,
        "new_status": update.status.value,
        "by_admin_id": str(current_user.id),
        "by_admin_email": current_user.email,
    })

    return {"message": f"Booking id {booking_id} updated to {update.status.value}"}


@router.delete("/bookings/{booking_id}")
async def delete_booking(
    booking_id: str, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    stats_cache: StatsCache = Depends(get_stats_cache),
):
    """Delete a booking by booking id"""
    deleted = await BookingRepository.delete(db, booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Booking id {booking_id} not found")
    await db.commit() #commit the flush
    await stats_cache.invalidate() #invalidate the redis cache, bcs it has became a stale data due to this DB changes

    logger.info("Admin deleted booking", extra={
        "booking_id": booking_id,
        "by_admin_id": str(current_user.id),
        "by_admin_email": current_user.email,
    })
    return {"message": f"Booking id {booking_id} deleted"}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    stats_cache: StatsCache = Depends(get_stats_cache),
):
    """
    return booking stats for the admin dashboard. cache valid for 30s TTL in Redis. If cache hit while still active, no DB query.
    Cache is also invalidated explicitly when bookings change (see update_booking_status, delete_booking, and chatbot _confirm_booking).
    """
    #1. try cache first
    cached = await stats_cache.get()
    if cached is not None:
        logger.debug("Stats cache HIT")
        return cached #return dict of booking stats

    #2. cache miss, compute from DB
    logger.debug("Stats cache MISS: computing from DB")
    stats = await BookingRepository.get_stats(db) #query fresh data from DB

    #3. set the cache for next request (30s default TTL)
    await stats_cache.set(stats)

    return stats