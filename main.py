from typing import Optional, Dict #data type hint
import re 
from datetime import datetime, timedelta, time as dt_time

from booking.intent import classify_intent
from booking.extractor import extract_slots
from booking.validator import validate_slots, validate_operating_hours
from booking.session import BookingSession
from booking.session_store import RedisSessionStore
from booking.database import BookingDB

from logger import get_logger
logger = get_logger(__name__)

store = RedisSessionStore() #as an object to use redis store method
db = BookingDB() #initialize the db connection

def handle_message(user_id: str, message: str) -> str:
    
    session = store.get_or_create(user_id) #make session or get user session at redis
    
    ambig = getattr(session, "time_ambiguous", None) #getattr: get the attributes value, if null wont crash
    ambig_time = getattr(session, "time_ambiguous_when", None) #get the time when ambiguous was noticed
    existing_date = session.slots.get("tanggal")

    if ambig: 
        #if no date yet, ask for date first (wont ask user to pick 1 or 2)
        if not existing_date:
            session.time_ambiguous = None
            session.time_ambiguous_when = None
            store.save(session) #save every edited session to redis
            return "Tanggal belum dipilih kak, silakan pilih tanggal dulu ya"
        
        #ambiguous expired (> 30 minutes)
        if ambig_time and (datetime.utcnow() - ambig_time > timedelta(minutes=30)): #if already ambiguous more than 30 minutes, cancel it
            session.time_ambiguous = None #NOTES: use "." to access the attributes of a class or to use a method of a class
            session.time_ambiguous_when = None 
            logger.info("Ambiguous time expired", extra={"user_id": user_id})
            store.save(session)
            return "Halo kak! Tadi kita lagi pilih jam, tapi sudah lama. Jam berapa kak?"
        
        #handle ambiguous
        else:
            resolved = _try_resolve_ambiguous_time(message, ambig) #return None or dict("jam")
            if resolved is not None: #user picked 
                selected_time = resolved.get("jam")
                existing_date = session.slots.get("tanggal")

                #convert string to time object without 'parse_datetime' from validator.py (bcs parse_datetime has a smart system that auto picked 19::00 instead of 07:00 bcs 07:00 is outside of operating hours) -> this block of code is for explicit time asked by user, autocorrect will ruin it
                hour, minute = map(int, selected_time.split(':'))
                time_obj = dt_time(hour, minute)

                #convert string to date object
                date_obj = datetime.strptime(existing_date, "%Y-%m-%d").date()

                #check operating hours (occurs after picked an option of ambiguous)
                is_valid, hours_error = validate_operating_hours(date_obj, time_obj)

                if not is_valid:
                    session.time_ambiguous = None
                    session.time_ambiguous_when = None
                    logger.info(
                        "Resolved ambiguous time was outside of operating hours",
                        extra={"user_id": user_id, "selected_time": selected_time}
                    )
                    store.save(session)
                    return hours_error

                #update if everything is valid
                session.update({"jam": selected_time}) #update the user self.session.slots("jam"), self.errors, and self.active
                session.time_ambiguous = None
                session.time_ambiguous_when = None
                logger.info("Ambiguous time was resolved", extra={"user_id": user_id, "selected_time": selected_time})
                store.save(session)

                #continue the flow
                missing = session.get_missing_slots() 
                if missing:
                    return _ask_missing_slot(missing[0]) #generate questions for missing slots, one question a time
                return _show_confirmation(session)
            
            else: #user didnt choose valid index, show the options again
                candidates = ambig.get("candidates", [])    
                minute = ambig.get("minute", 0)
                options = "\n".join([
                            f"{i+1}. {h:02d}:{minute:02d}" #i+1: convert index to general nums
                            for i, h in enumerate(candidates) #enum: generate index number for every candidates
                        ])
                return f"Tolong pilih salah satu dengan mengetik hanya angka '1' atau '2' ya kak:\n{options}"
    
    #classify user intent
    if session.is_active():
        logger.debug("Active session: context aware", extra={"user_id": user_id})

        #if user want to cancel
        if re.search(r'\b(batal|batalkan|cancel|stop|ga jadi|gak jadi|gajadi|batalin)\b', message, re.I):
            session.clear()
            store.delete(user_id) #delete user session at redis
            logger.info("Booking cancelled by user", extra={"user_id": user_id})
            return "Oke kak booking dibatalkan. Ada yang bisa saya bantu lagi?"
        
        #user want to edit (mid booking)
        if _is_edit_request(message):
            response = _handle_edit(session, message) 
            store.save(session) #save edited session to redis
            return response #return response (string)
         
        #confirmation: if user says "yes" then confirm the booking
        if session.is_complete() and _is_confirmation(message):
            return _confirm_booking(session, user_id) #save to DB and clear session

        FAQ_SPESIFIC = r'\b(berapa|harga|jam buka|jam tutup|alamat|apa itu)\b'
        QUESTION_WORD = r'\b(kapan|dimana|bagaimana|kenapa|apa|gimana|mengapa)\b'

        #FAQ interrupt while booking
        if re.search(FAQ_SPESIFIC, message, re.I) or (re.search(QUESTION_WORD, message, re.I)): 
            logger.debug("FAQ interrupt detected", extra={"user_id": user_id})
            from rag import get_response
            faq_response = get_response(message)
            return f"{faq_response}\n\nMau lanjut booking kak?"
        
        logger.debug("Treating as booking continuation", extra={"user_id": user_id})
        response = _handle_booking(session, message)
        store.save(session) #save change to redis
        return response
    
    intent = classify_intent(message)
    logger.info("Intent classified", extra={"user_id": user_id, "intent": intent})
    
    #should be after or before main session (if within, can cause ambiguity)
    if intent == "CHITCHAT":
        return "Halo kak, apa ada yang bisa saya bantu? Jika ingin booking bilang saja ya kak"
    
    #user want to book an appointment
    if intent == "BOOKING":
        session.active = True 
        response = _handle_booking(session, message)
        store.save(session) 
        return response

    #FAQ before bookings flow
    if intent == "FAQ": 
        from rag import get_response
        return get_response(message)
    
    #if user want to reschedule
    if intent == "RESCHEDULE":
        from config import PHONE_NUMBER
        return f"Untuk reschedule, bisa tolong hubungi nomor WA {PHONE_NUMBER} ya kak"
    
    #if unclear
    return "Maaf kak saya kurang paham. Mau lanjut booking treatment atau tanya info?"

def _try_resolve_ambiguous_time(message: str, ambig: dict) -> Optional[Dict[str, str]]: #return None or Dict with key value as a string 
    msg = message.strip() 
    clean = re.sub(r'[^\d]', '', msg) #^ = negation, delete all char except for integers. ("1.", "no 1", "pick 1" -> "1")
    if not re.fullmatch(r'\d+', clean): #the string must consist only numbers, first or second choice
        return None
    
    idx = int(clean) - 1 #convert to index number
    candidates = ambig.get("candidates", []) # [] as default
    minute = ambig.get("minute", 0) # 0 as default

    if 0 <= idx < len(candidates): #if idx is between the choice
        h = candidates[idx] 
        return {"jam": f"{h:02d}:{minute:02d}"} #return valid info, ex: {"jam": "20:30"}
    
    return None

def _ask_missing_slot(slot_name: str) -> str: #ask the missing slots to user
    questions = {
        "lokasi": "Mau booking di cabang mana kak? (Jakarta/Bekasi/Tangerang/Bandung)",
        "treatment": "Treatment apa yang mau dibooking kak? (Facial/Filler/Botox/dll)",
        "tanggal": "Tanggal berapa kak?",
        "jam": "Jam berapa kak?",
        "nama": "Boleh minta nama kak?"
    }

    return questions.get(slot_name, "Ada info yang kurang kak")

def _show_confirmation(session: BookingSession) -> str: #show confirmation if there's no missing value
    summary = session.get_summary()
    name = session.slots.get("nama", None)
    full_name = f"kak {name}" if name is not None else "kak"

    return f"""Baik {full_name}, saya bantu booking: 
{summary}

Sudah benar ya kak? ketik 'ya' untuk konfirmasi atau 'ganti X' untuk ubah informasi booking."""

def _is_edit_request(message: str) -> bool: #check if the user wanted to edit or no
    return bool(re.search(r'\b(ganti|ubah|ralat|edit|sunting|salah|keliru)\b', message, flags=re.I)) #\b: word boundary, so "kredit" is not match (edit). flags = for special condition

def _is_confirmation(message: str) -> bool:
    msg = message.strip().lower()
    valid_words = ["ya", "iya", "yes", "ok", "oke", "betul", "benar", "confirm", "lanjut"]
    
    #exact match
    if msg in valid_words:
        return True
    
    #fallback: the prefix must be one of valid_words (some space before that words still valid)
    pattern = r'^\s*(?:' + '|'.join(re.escape(w) for w in valid_words) + r')\b(?:[\s,!.]|$)' #suffix is \b and with \s,!. or $ (means end of string) still valid
    return bool(re.search(pattern, msg, flags = re.I))

def _handle_edit(session: BookingSession, message: str) -> str: #extract user's new message and update it to that user's session
    new_slots = extract_slots(message) #extract user message to json/dict

    if new_slots.get("_parse_error"): #if the message is unable to be extracted
        return "Maaf kak saya kurang paham, mau ganti apa ya?"
    
    clean_new_slots = {k: v for k, v in new_slots.items() if v is not None}
    merged = {**session.slots, **clean_new_slots}
    validated, missing, errors = validate_slots(merged)

    if errors:
        return "\n".join(errors) #show message to user
    
    updates = {} #updated values in dict
    updated_info = [] #updated value (the name of info)

    for key, value in validated.items():
        if key.startswith("_"): #skip internal info: _time_ambiguous bcs already handled (asked to user) at session.py (method of "def update()")
            continue
        else: #if main slots/info
            if value and value != session.slots.get(key): #if different
                old_value = session.slots.get(key)
                updates[key] = value
                updated_info.append(f"{key}: {old_value} → {value}")

    if updates: 
        session.update(updates) #update the user self.session.slots, self.errors, and self.active
        logger.info("Booking slots edited", extra={"user_id": session.user_id, "updates": updates})
        return f"Oke kak, diubah:\n" + "\n".join(updated_info) + "\n\nLanjut kak?"
    
    return "Mau ganti apa kak?" #fallback: user ask to edit a same value or user ask edit without saying a value to be edited, etc

def _confirm_booking(session: BookingSession, user_id: str) -> str: #save booking to DB and clear session
    try:
        booking_data = session.to_dict() #convert BookingSession to clean dictionary
        booking_id = db.create_booking(user_id, booking_data) #save to DB and will return booking_id (raise error is handled by the try block)

        session.clear() #clear the user session in active_sessions
        store.delete(user_id) #delete session after user confirmed
        logger.info("Booking confirmed", extra={"user_id": user_id, "booking_id": booking_id})
        
        #return confirmation messages
        return f"""✅ Booking berhasil!

ID Booking: #{booking_id}

Tim kami akan konfirmasi via WhatsApp dalam beberapa jam ya kak.
Terima kasih! 🙏"""
    
    except Exception as e:
        logger.error("Booking confirmation failed", extra={"user_id": user_id, "error": str(e)}, exc_info=True)
        from config import PHONE_NUMBER
        return f"Maaf kak, terjadi kesalahan. Bisa coba lagi atau hubungi WA {PHONE_NUMBER}"

#HANDLE BOOKING: extract messagae -> validate -> update -> ask missing
def _handle_booking(session: BookingSession, message: str) -> str:
    #1. EXTRACT
    new_slots = extract_slots(message)
    logger.debug("Slots extracted", extra={"user_id": session.user_id, "slots": new_slots}) #debug extractor result

    if new_slots.get("_parse_error"): #if extractor failed
        return "Maaf kak, saya gagal memproses pesan. Boleh tolong diulang lagi dengan lebih jelas?"
    
    #prevent None value, especially for the date
    clean_new_slots = {key: value for key, value in new_slots.items() if value is not None} 

    #re-validate all: merge user session with new input (if hour isnt within the operational hours and there is no date at user new message, merge with the date at user session. bcs validate operating hours need both date and time)
    merged = {**session.slots, **clean_new_slots} #UNIQUE case = user edit date from A to B so the operational hours now is different, then will check the hours again so could notify it its outside of the new operating hours

    #2. VALIDATE
    validated, missing, errors = validate_slots(merged)
    logger.debug(
        "Validation result",
        extra={"user_id": session.user_id, "validated": validated, "missing": missing, "errors": errors}
    )
 
    #3. UPDATE (session.py)
    session.update(validated)

    #4. if validator has errors
    if errors:  
        session.set_errors(errors) #set the previous errors to current errors
        session.time_ambiguous = None #prioritize the error first, user will enter time again later
        session.time_ambiguous_when = None
    
    if session.has_errors(): #if there is errors, show to user
        errors = session.get_errors()
        cleaned_errors = [e.replace("Maaf kak, ", "") for e in errors]

        if len(cleaned_errors) == 1:
            error_msg = errors[0]
        else:
            error_msg = "Maaf kak, ada beberapa informasi yang perlu diperbaiki:\n" + "\n".join(f"• {e}" for e in cleaned_errors)
            
        session.clear_errors() #clear errors after showing the errors to user
        return error_msg  
        
    #5. handle ambiguous time (ask user to clarify)
    if getattr(session, "time_ambiguous", None): #if there is time_ambiguous

        if "tanggal" in session.get_missing_slots(): #if tanggal is missing and ambig, dont ask user to pick ambiguous
            session.time_ambiguous = None
            session.time_ambiguous_when = None
            return "Tanggal belum dipilih kak, silakan pilih tanggal dulu ya. Nanti kita lanjut atur jamnya."
        
        ambig = session.time_ambiguous
        candidates = ambig.get("candidates", [])
        minute = ambig.get("minute", 0)

        #option message to user
        options = "\n".join([
            f"{i+1}. {h:02d}:{minute:02d}"
            for i, h in enumerate(candidates)
        ])

        #if there is no info about when the ambiguous started at
        if not getattr(session, "time_ambiguous_when", None):
            session.time_ambiguous_when = datetime.utcnow()
        
        logger.debug("Ambiguous time: asking user", extra={"user_id": session.user_id, "candidates": candidates})
        return f"Maksud kakak jam berapa ya?\n{options}\n\nBalas angka '1' atau '2' aja ya kak"

    #6. check if all slots is filled
    missing_slots = session.get_missing_slots() #return list of missing slots
    if missing_slots:
        return _ask_missing_slot(missing_slots[0]) #clarify missing slots one by one

    #7. show confirmation message (all slots filled)
    return _show_confirmation(session)