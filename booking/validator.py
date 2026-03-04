from datetime import datetime, timedelta, time as dt_time #dt_time to make a time object in py
from preprocessor import SLANG
import re

VALID_LOCATIONS = {
    "jakarta": "Jakarta (Kemang)",
    "kemang": "Jakarta (Kemang)",
    "bekasi": "Bekasi",
    "tangerang": "Tangerang",
    "bandung": "Bandung"
}

VALID_TREATMENTS = [
    "Facial", "Facial Basic", "Facial Glow", "Facial Acne", "Hydrafacial", "Facial Gold",
    "Filler", "Filler Bibir", "Filler Hidung", "Filler Dagu", "Filler Pipi",
    "Botox", "Botox Dahi", "Botox Rahang", "Botox Ketiak",
    "Tarik Benang", "Benang Hidung", "Benang Wajah",
    "DNA Salmon", "Rejuran", "Laser", "Slimming"
]

OPERATING_HOURS = {
    "weekday": {"open": "09:00", "close": "21:00"},  
    "saturday": {"open": "10:00", "close": "20:00"},
    "sunday": {"open": "10:00", "close": "17:00"}
}

MOD_RANGES = {
    "subuh": range(0, 7), #0-6
    "pagi": range(5, 12), #5-11
    "siang": range(9, 18), #9-17
    "sore": range(13, 20), #13-19
    "malam": range(17, 24), #17-23
    "am": range(0, 12),
    "pm": range(12, 24)
}

WORD_TO_NUMBER = {
    "satu": 1,
    "dua": 2,
    "tiga": 3,
    "empat": 4,
    "lima": 5,
    "enam": 6,
    "tujuh": 7,
    "delapan": 8,
    "sembilan": 9,
    "sepuluh": 10
}

#get the operating hours for some spesific date/day
def _get_operating_hours(date_obj: datetime.date):
    weekday = date_obj.weekday() #return 0-6, 0 is monday, 6 is sunday 
    if weekday == 5:
        hours = OPERATING_HOURS["saturday"]
        day_name = "Sabtu"
    elif weekday == 6:
        hours = OPERATING_HOURS["sunday"]
        day_name = "Minggu"
    else:
        hours = OPERATING_HOURS["weekday"]
        DAY = ["Senin","Selasa","Rabu","Kamis","Jumat"]
        day_name = DAY[weekday]
    
    return hours["open"], hours["close"], day_name


#return (date_obj, time_obj, None) if valid. return (None, None, "error message") if bad format or date in past
#return (date_obj/None, None, {"status":"ambiguous_time", "candidates":[], "minute":m}) if ambiguous: parser could pick/multiple valid hours
#return (date_obj/None, None, {"status":"no_valid_hours", "open":.., "close":.., "day_name":..}) if no candidates fits operating hours for that date

def parse_datetime(date_str: str, time_str: str = None) -> tuple: #default if there's no input for time_str = None 
    today = datetime.utcnow().date() #.now() = time now until millisec, but just take the date using date()

    #PARSE THE DATE
    date_obj = None
    if date_str:
        date_lower = date_str.lower().strip()

        if date_lower in ["hari ini", "today"]:
            date_obj = today
        elif date_lower in ["besok", "tomorrow"]:
            date_obj = today + timedelta(days=1) #timedelta: to add some unit of time to py date object
        elif date_lower in ["lusa", "day after tomorrow"]:
            date_obj = today + timedelta(days=2)
        elif date_lower in ["minggu depan", "next week"]:
            date_obj = today + timedelta(weeks=1)
        else:  #if absolute date : "5 januari", "01-15" or "dua hari lagi", "4 hari lagi"
            match = re.search(r'(\d+)\s+hari', date_lower)
            if match:
                days = int(match.group(1))
                date_obj = today + timedelta(days=days)
            else:
                for word, num in WORD_TO_NUMBER.items():
                    if re.search(rf'\b{word}\s+hari\b', date_lower):
                        date_obj = today + timedelta(days=num)
                        break
                else: #for-else: else will only occurs if "for" runs normally without break
                    date_obj = _parse_absolute_date(date_str, today.year) #parse robustly
    
        if not date_obj: #if bad input from ai
            return None, None, "Maaf kak, tanggalnya tidak valid"
        if date_obj < today: #if the date is in the past
            return None, None, "Maaf kak, tanggal tidak boleh di masa lalu"

    if not time_str: #if there is no information yet for the time
        return date_obj, None, None #date_obj could be None / exist
    
    #PARSE THE TIME 
    time_result = _parse_time(time_str) #call the function to parse time

    #if result of time_result is in dict (its ambiguous)
    if isinstance(time_result, dict): 
        candidates = time_result["candidates"] #extract the hour candidates
        minute = time_result["minute"] #extract the minute

        return date_obj, None, {
            "status": "ambiguous_time",
            "candidates": candidates,
            "minute": minute
        }
    
    #if the input is bad or not valid
    if time_result is None: 
        return date_obj, None, "Maaf kak, format jam tidak valid. Boleh tolong diulangi dengan lebih jelas kak?"
    
    #if both date and time valid
    time_obj = time_result
    return date_obj, time_obj, None 

def _parse_absolute_date(date_str:str, default_year: int) -> datetime.date:
    month_id = {
        "januari": 1, "jan": 1, "january": 1,
        "februari": 2, "feb": 2, "february": 2,
        "maret": 3, "mar": 3,
        "april": 4, "apr": 4,
        "mei": 5, "may": 5,
        "juni": 6, "june": 6,
        "juli": 7, "july": 7,
        "agustus": 8, "aug": 8, "august": 8,
        "september": 9, "sep": 9, "sept": 9,
        "oktober": 10, "okt": 10, "oct": 10,
        "november": 11, "nov": 11,
        "desember": 12, "des": 12, "dec": 12
    }

    try: #try iso format, if date_str = "2026-01-15". strptime = string parse to time
        return datetime.strptime(date_str, "%Y-%m-%d").date() #python reads string, convert it to datetime object with years, month, and day. ".date()": to take only the date parts (skips hours, min, etc)
    except: #if not match
        pass
    
    #try "5 januari", "10 jan 2026" 
    try:
        parts = date_str.lower().split()
        if len(parts) >= 2: #make sure there is atleast date and month 
            #day = delete every \D (\D: only number character) at parts[0] string
            day = int(re.sub(r'\D', '', parts[0])) #ex: "05 ," -> int(05) -> 5
            month_str = parts[1] 
            year = int(parts[2]) if len(parts) > 2 else default_year

            month = month_id.get(month_str) #convert month name to int, accessing dictx
            if month: #if month successfully is an int
                return datetime(year, month, day).date() #return in datetime py obj format
    except Exception as e:
        print(f"Parse Date Error: {e}")
    
    return None #if parts < 2 or month not found in dict, return None

#return datetime if valid, dict of hours candidate if unsure, None if invalid
def _parse_time(time_str: str):
    time_str = (time_str or "").lower().strip() #(time_str or "") : if time_str = None, then change it to "", so it wont error. bcs None.lower() occurs error

    WORD_TO_NUM_TIME = {
        "satu": "1", "dua": "2", "tiga": "3", "empat": "4", "lima": "5",
        "enam": "6", "tujuh": "7", "delapan": "8", "sembilan": "9",
        "sepuluh": "10", "sebelas": "11", "dua belas": "12", "duabelas": "12"
    }
    for word, num in WORD_TO_NUM_TIME.items():
        time_str = re.sub(rf'\b{re.escape(word)}\b', num, time_str) #f: to sub using {}
    
    numbers = re.findall(r'\d+', time_str) #findall: find all \d+. "\d+" means will search for int (could be 1 or 1+). ex: 10 lebih 30 -> ['10', '30']
    if not numbers: #if there isnt any nums
        return None
    
    hour = int(numbers[0]) #take the first int found (should be hours)
    minute = int(numbers[1]) if len(numbers) > 1 else 0 #if number founds > 1, means there is minutes, so take it

    if not 0 <= minute < 60: #if minute isnt within 1-59, return None
        return None
    
    #check is there any helper context
    modifier = None #modifier = help at context of time
    match = re.search(r'\b(am|pm)\b', time_str) #use regex bcs am/pm is sensitive, "jam 8": "jam" can be determined as "am"
    if match:
        modifier = match.group(1)
    else:
        for m in ["pagi", "siang", "sore", "malam", "malem", "mlm"]:
            if m in time_str:
                modifier = m
                break
    
    #if there is ":", determine as explicit time (so ambiguous wont happen 2+ times bcs of merging slots at _handle_bookng at main.py will always revalidate the hours)
    has_colon = ':' in time_str 
    if hour > 12 or hour == 0 or has_colon:
        if 0 <=  hour < 24:
            return dt_time(hour, minute)
        return None

    if 1 <= hour <= 12: #12 hours format, may be ambiguous
        if hour == 12:
            candidates = [0, 12] # 12 could be midnight 00:00 or noon 12:00
        else: #if the hours is 1-11 which is ambigous (could be am/pm)
            candidates = [hour, hour + 12] #ex: 2 -> [2, 14] (the am and pm version)
    else: #then the hour is clear (24 hours format), just add it to candidates
        candidates = [hour]

    #validate the hours shoud be between 0-23
    candidates = [h for h in candidates if 0 <= h < 24] 
    if not candidates:
        return None
    
    if modifier: #if there is a context of time
        mod_range = MOD_RANGES.get(modifier) #mod range will return the value of .get(modifier) which is a time range
        if mod_range: #if hours is valid for that session
            matched = [h for h in candidates if h in mod_range] #choose the most valid hours based on the timeframe
            if len(matched) == 1: #should be only one 
                return dt_time(matched[0], minute) #return in time object py format
            elif len(matched) > 1: #shouldnt happen, just in case
                return {"candidates": matched, "minute": minute}
        
        return {"candidates": candidates, "minute": minute} #if hours isnt valid for that session/range. ex: "jam 10 sore"
    
    #if candidate is only 1, obviously not ambiguous
    if len(candidates) == 1:
        return dt_time(candidates[0], minute)
    
    return {"candidates": candidates, "minute": minute} #if no context of time found, its ambiguous

#to validate the hours given based on operation hours
def validate_operating_hours(date_obj: datetime.date, time_obj: datetime.time) -> tuple:
    if not date_obj or not time_obj: #if no information yet, couldnt check valid/no, will then pass all hours candidates to be asked to user
        return True, None
    
    open_s, close_s, day_name = _get_operating_hours(date_obj) #get the info of the day (in string)

    #convert the string to int
    oh, om = map(int, open_s.split(":")) #"10:00" -> ["10", "30"] -> map(type, given type) -> [10, 30]
    ch, cm = map(int, close_s.split(":"))
    #convert the int to time object
    open_time = dt_time(oh, om) #dt_time(10, 30) -> 10:30
    close_time = dt_time(ch, cm)

    if not (open_time <= time_obj <= close_time): #if it doesnt match clinic operation hours
        return False, f"Maaf kak, klinik kami {day_name} buka jam {open_s} - {close_s}.\nSilahkan pilih jam lain ya kak" 

    return True, None #if match, then the hours is valid

#to validate the location based on the valid clinic location
def fuzzy_match_location(location: str) -> str:
    if not location: #if no info yet
        return None
    
    loc_lower = location.lower().strip()
    if loc_lower in SLANG: #check slang
        loc_lower = SLANG[loc_lower]
    
    if loc_lower in VALID_LOCATIONS: 
        return VALID_LOCATIONS[loc_lower]
    
    #fallback step
    for key, value in VALID_LOCATIONS.items():
        if key in loc_lower or loc_lower in key:
            return value    
    return None

 #for every treatment: make a lower dict to it. the format -> "v.lower()": "v"
_CANON_TREAT_MAP = {v.lower(): v for v in VALID_TREATMENTS} #ex: Botox Rahang -> botox rahang : Botox Rahang 

def _normalize_text(text: str) -> str:
    s = (text or "").lower().strip()
    s = re.sub(r'[^\w\s\-]', " ", s) # ^: negation. So: replace all except \w(alfhabet, nums, etc) and \s(\t, \n, " ", etc) with " " 
    s = re.sub(r'\s+', " ", s).strip() #replace excess space with just a space
    return s

#return the official treatment name or None
def match_treatment(treatment: str) -> str:
    if not treatment: #if no info yet
        return None
    
    treat = _normalize_text(treatment)
    #to normalize slang perwords, safer.
    tokens = [SLANG.get(tok, tok) for tok in treat.split()] #get(tok,tok) second tok is a default, so if there is no match in slang, use the original
    joined = " ".join(tokens) #merge again the list

    #try match
    if joined in _CANON_TREAT_MAP:
        return _CANON_TREAT_MAP[joined] #return the official name

    return None

def validate_slots(slots: dict) -> tuple:
    validated = {}
    missing = set()
    errors = [] #list of error string to user

    #validate the location
    if slots.get("lokasi"):
        validated["lokasi"] = fuzzy_match_location(slots["lokasi"]) #if location valid, add to validated dictionary 
        if not validated["lokasi"]: 
            errors.append(f"Maaf kak, Lokasi '{slots['lokasi']}' tidak tersedia. Boleh pilih cabang lain ya kak")
            missing.add("lokasi")
    else:  #if lokasi == None
        missing.add("lokasi")

    #validate treatment
    if slots.get("treatment"):
        validated["treatment"] = match_treatment(slots["treatment"]) #if treatment valid
        if not validated["treatment"]:
            errors.append(f"Maaf kak, Treatment '{slots['treatment']}' tidak tersedia. Boleh pilih treatment lain ya kak")
            missing.add("treatment")
    else: #if no info yet from the slots
        missing.add("treatment")

    #validate date/time
    if slots.get("tanggal") or slots.get("jam"):
        print(f"[DEBUG] Input: tanggal={slots.get('tanggal')}, jam={slots.get('jam')}")
        date_obj, time_obj, date_error = parse_datetime(slots.get("tanggal"), slots.get("jam"))
        print(f"[DEBUG] Parsed: date_obj={date_obj}, time_obj={time_obj}, error={date_error}")
        
        #date_error could be None, dict(ambiguous time/invalid operating hours), or string (error occurs)
        if date_error:
            if isinstance(date_error, dict): #if there is error info in dictionary
                status = date_error.get("status")
                if status == "ambiguous_time":  #if ambiguous add to validated then will be asked to user
                    validated["_time_ambiguous"] = date_error 
                elif status == "no_valid_hours": #if not valid then errors
                    errors.append(f"Maaf kak, klinik kami {date_error['day_name']} buka jam {date_error['open']} - {date_error['close']}")
            else: #if error info is in string
                errors.append(date_error)

        ambiguous_time = isinstance(date_error, dict) and date_error.get("status") == "ambiguous_time"
 
        if date_obj: #if there is a valid date, save it to validated
            validated["tanggal"] = date_obj.strftime("%Y-%m-%d")
            validated["tanggal_display"] = date_obj.strftime("%d %B %Y")
        else: #if there is no valid date
            if slots.get("tanggal"): #there is a date info
                if not date_error: #should use this, bcs will keep checking even after the "if date_error" lines
                    errors.append("Maaf kak, Tanggalnya tidak valid. Boleh pilih tanggal lain ya kak.")
            else: #if there isnt any date info
                missing.add("tanggal")
        
        if time_obj: #if there is a valid time, append to validated
            validated["jam"] = time_obj.strftime("%H:%M")
        else: #if there isnt any valid time
            if slots.get("jam"): #time info existed
                if ambiguous_time:
                    pass
                else:
                    if not date_error:
                        errors.append("Maaf kak, format jam tidak valid. Boleh pilih jam lain ya kak.")
            else: #no time info
                missing.add("jam")
        
        if date_obj and time_obj: #need to check again bcs, validate operating above is only for ambiguous case, not including all case
           is_valid, hours_error = validate_operating_hours(date_obj, time_obj)
           if not is_valid and hours_error:
               errors.append(hours_error)

    else: #if no info yet 
        if not slots.get("tanggal"):
            missing.add("tanggal")
        if not slots.get("jam"):
            missing.add("jam")

    #validate name
    if slots.get("nama"):
        validated["nama"] = slots["nama"].strip().title() #.title(): grACe burgers -> Grace Burgers
    else:
        missing.add("nama")

    return validated, list(missing), errors