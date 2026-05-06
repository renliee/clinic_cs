"""
Get system health check for monitoring.
Checks redis and ollama availability.
"""

import httpx #HTTP request to interact with other app
from fastapi import APIRouter
from models.schemas import HealthResponse
from config import settings
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["health"])

APP_VERSION = "0.1.0"

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Return status of each components"""
    redis_status = _check_redis()
    ollama_status = _check_ollama()

    overall = "healthy" if redis_status == "ok" and ollama_status == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        redis=redis_status,
        ollama=ollama_status,
        version=APP_VERSION, 
    )

def _check_redis() -> str:
    try:
        import redis
        client = redis.from_url(settings.redis_url, decode_responses=True) #connect with redis
        client.ping() #return connection error if redis doesnt response with PONG
        return "ok"
    except Exception as e:
        logger.warning("Redis health check failed", extra={"error": str(e)})
        return f"error: {str(e)}"

def _check_ollama() -> str:
    try:
        #httpx.get: HTTP method to GET which llms are ready to use from ollama
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0) #wait time = 5 secs

        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])] #fetch every llm's name 
            if any(settings.llm_model in m for m in models):
                return "ok"
            return f"Ollama model {settings.llm_model} not loaded yet"
        
        return f"Ollama returned {response.status_code}"
    
    except Exception as e:
        logger.warning("Ollama health check failed", extra={"error": str(e)})
        return f"error: {str(e)}"
