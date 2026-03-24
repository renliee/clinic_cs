"""
FastAPI main endpoints.
Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, bookings, health
from api.deps import get_db, get_store
from logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize dependencies on startup and clean up things after shutdown"""
    logger.info("Starting Clinic CS API")

    #will raise error on start up if Redis/DB is down
    get_db()
    get_store()

    logger.info("All dependencies initialized")
    yield 

    logger.info("Shutting down Clinic CS API")


#initialize app with FastAPI object
app = FastAPI(
    title="CLINIC CS API",
    description="AI powered booking chatbot for aesthetic clinics",
    version="0.1.0",
    lifespan=lifespan,
)

#CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", #react ports 
        "http://localhost:5173", #vite ports
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#group all the routers into app
app.include_router(chat.router)
app.include_router(bookings.router)
app.include_router(health.router)

#default FastAPI info
@app.get("/")
async def root():
    return {
        "service": "Clinic CS API",
        "version": "0.1.0",
        "docs": "/docs",
    }