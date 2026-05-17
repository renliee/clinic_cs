"""Pydantic schemas for API request (Backend) and response validation"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum #to validate only valid answer

#request chat from frontend (user)
class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100, description="Unique user identifier") #Field(...) means required
    message: str = Field(..., min_length=1, max_length=2000, description="User message text")

#quick button reply from backend to user and if clicked, sent payload messaga to backend
class QuickReply(BaseModel):
    label: str #text shown on the button
    payload: str #message that is sent to backend(llm)

#response chat from backend (llm) to user (default_factory only accept function as its value)
class ChatResponse(BaseModel):
    reply: str
    user_id: str
    quick_replies: list[QuickReply] = [] #[] as a default answer if there is no QuickReply button
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat()) #lambda: function without a name that could be write in single line. 

#every bookings data return by backend (mirrors DB column except for 'id' column)
class Booking(BaseModel):
    model_config = {"extra": "ignore"} #attribute that configures how the model behaves, such as handling extra fields not defined in schema (in this case 'id')

    booking_id: str | None = None #None as a default answer
    user_id: str
    nama: str
    lokasi: str
    treatment: str
    tanggal: str
    jam: str
    status: str
    notes: str | None = None
    created_at: str
    updated_at: str | None = None
    confirmed_at: str | None = None

#defining the only valid status that client could choose using Enum inheritance (str inheritance define final value of BookingStatus as a string)
class BookingStatus(str, Enum): 
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"

#update the status of a booking from admin
class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    notes: str | None = None

#list of bookings to frontend
class BookingListResponse(BaseModel):
    bookings: list[Booking]
    total: int

#health status of used components to frontend
class HealthResponse(BaseModel):
    status: str
    redis: str
    ollama: str
    version: str


"""Pydantic schemas for API request (Auth) and response validation"""
from uuid import UUID
from models.user import UserRole

class LoginRequest(BaseModel):
    """login credentials submitted by the frontend"""
    email: str = Field(..., min_length=3, max_length=255, description="User email")
    password: str = Field(..., min_length=1, max_length=255, description="User password")

class TokenResponse(BaseModel):
    """
    Response from /login and /refresh (backend) to frontend.
    Access token is returned here so frontend will store in memory.
    """
    access_token: str 
    token_type: str = "bearer" #bearer: standard OAuth convension, tell frontend that this is bearer type that carry token
    expires_in: int #access token TTL in seconds, help frontend schedule refresh

class UserResponse(BaseModel):
    """
    user representation for API response.
    never include hashed_password, schemas wont leak it.
    we dont use model_config = {"extra": "ignore"} bcs Pydantic reads the ORM object by pulling specific attributes by name (so other field wont cause error)
    """
    model_config = {"from_attributes": True} #let pydantic read an orm object instead of its default: dictionary

    id: UUID
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


"""Pydantic schemas for admin stats schemas"""
class StatsResponse(BaseModel):
    """stats response (from backend to frontend) for the admin dashboard overview"""
    today_bookings: int
    this_week_total: int
    pending_count: int
    confirmed_count: int