"""FastAPI route handler that receive message from frontend, pass it to handle_message(), 
generating contextual quick reply buttons and returning both reply buttons and llm's response"""

from fastapi import APIRouter
from models.schemas import ChatRequest, QuickReply, ChatResponse
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix='/api', tags=["chat"]) #APIRouter: FastAPI method of related routes from separate files, then will be combined at main.py using include_routes

def _generate_quick_replies(reply: str) -> list[QuickReply]:
    """Analyzed llm response to suggest contextual quick reply buttons to help customers know the features"""
    text = reply.lower()

    #after successful booking
    if "booking berhasil" in text:
        return [
            QuickReply(label="Booking Lagi", payload="Mau booking treatment"),
        ]
    
    #confirming booking
    if "ketik atau pilih 'ya'" in text:
        return [
            QuickReply(label="Ya, Konfirmasi", payload="ya"),
            QuickReply(label="Ganti Info", payload="ganti"),
            QuickReply(label="Batalkan", payload="batal"),
        ]

    #ambiguous time
    if "tolong pilih salah satu dengan" in text or "balas angka '1' atau '2' aja ya kak" in text:
        return [
            QuickReply(label="1", payload="1"),
            QuickReply(label="2", payload="2"),
        ]

    #cancelled
    if "oke kak booking dibatalkan" in text:
        return [
            QuickReply(label="Booking Baru", payload="Mau booking treatment"),
            QuickReply(label="Cek Harga", payload="Berapa aja harga treatment?"),
        ]

    #FAQ interrupt when mid booking flow
    if "mau lanjut booking" in text:
        return [
            QuickReply(label="Lanjut Booking", payload="Lanjut"),
            QuickReply(label="Tanya Lagi", payload="Mau tanya lagi"),
        ]

    #UNCLEAR intent
    if "mau tanya info atau booking treatment" in text:
        return [
            QuickReply(label="Booking Treatment", payload="Mau booking treatment"),
            QuickReply(label="Tanya Info", payload="Mau tanya info"),
        ]

    #greetings from llm (intent: CHITCHAT)
    if "apa ada yang bisa saya bantu" in text:
        return [
            QuickReply(label="Booking Treatment", payload="Mau booking treatment"),
            QuickReply(label="Jenis Treatment", payload="Ada treatment apa aja?"),
            QuickReply(label="Cek Harga", payload="Berapa aja harga treatment?"),
            QuickReply(label="Jam Buka", payload="Jam operasional klinik setiap hari kapan aja?"),
            QuickReply(label="Lokasi", payload="Klinik lokasinya ada dimana aja?"),
        ]

    #default: no buttons (bot is asking for specific info like name, date, etc)
    return []

#/api/chat is the endpoint to use chat function (/api is the prefix of all router in this file)
@router.post("/chat", response_model=ChatResponse) 
async def chat(req: ChatRequest):
    """Main chat endpoint, receive user message, returns llm reply and quick replies"""
    logger.info("Chat request", extra={"user_id": req.user_id, "msg_preview": req.message[:100]})

    from chatbot import handle_message

    try:
        reply = handle_message(req.user_id, req.message)
    except Exception as e:
        logger.error("handle_message failed", extra={"user_id": req.user_id, "error": str(e)}, exc_info=True)
        reply = "Maaf kak, terjadi kesalahan. Coba lagi dalam beberapa saat ya."
    
    quick_replies = _generate_quick_replies(reply)

    return ChatResponse(
        reply=reply,
        user_id=req.user_id,
        quick_replies=quick_replies,
    )