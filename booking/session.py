from datetime import datetime, timedelta

class BookingSession:
    
    #ATTRIBUTES of the class
    def __init__(self, user_id: str): #manage each user booking data by their unique id (use "user_id" as input)
        self.user_id = user_id
        self.slots = {
            "lokasi": None,
            "treatment": None,
            "tanggal": None,
            "tanggal_display": None,  
            "jam": None,
            "nama": None
        }
        self.active = False #false id booking has not started yet or already done
        self.created_at = datetime.utcnow() #extra info
        self.last_activity = datetime.utcnow()
        self.errors = [] #store all the erros occured 
        self.time_ambiguous = None #store the info of ambiguous time (status, candidates, minute), will be asked to user before update to self.slots
        self.time_ambiguous_when = None

    #METHOD of the class

    def update(self, validated_slots: dict, errors: list = None): #validated_slots and errors is from validate_slots function from validator.py
        self.last_activity = datetime.utcnow()

        #update the newest version of the slots        
        for key, value in validated_slots.items():
            if key == "_time_ambiguous": #if ambiguous, save to self.time_ambiguous (dont save to self.slots)
                if not errors: #only update ambiguous if all valid, so user wont get the second phase of ambiguous message after fixing errors 
                    self.time_ambiguous = value
                    self.time_ambiguous_when = datetime.utcnow()
            else:
                if isinstance(value, str): #if the value is a string, clean it
                    value = value.strip()

                if value is not None and value != "": #if there is value, update the slots
                    self.slots[key] = value

        #if there is errors, save it
        if errors:
            self.errors = errors 
        
        #mark active if any slot is filled
        if any(value for key, value in self.slots.items() if key != "tanggal_display" and value): #ignore "tanggal_display and the value is there"
            self.active = True

    def get_missing_slots(self) -> list: #return a list of missing information (not including tanggal_display)
        required = ["treatment", "lokasi", "tanggal", "jam", "nama"]
        return [key for key in required if self.slots.get(key) is None or self.slots.get(key) == ""]
    
    def is_complete(self) -> bool:  #check is the booking done yet 
        return len(self.get_missing_slots()) == 0 #either return True / False
        
    def is_active(self) -> bool: #check if booking is in progress or no
        return self.active
    
    def is_stale(self): #check if user conversation/session stale or not
        return datetime.utcnow() - self.last_activity > timedelta(minutes=30)

    def has_errors(self) -> bool: #check if the booking has error or no
        return len(self.errors) > 0 #return True / False
    
    def get_errors(self) -> list:
        return self.errors.copy() #so could modify the copy without erasing original info
    
    def clear_errors(self): #clear the errors after showing to user
        self.errors = []

    def set_errors(self, errors: list): #to set a new error after user sent a new message
        self.errors = errors

    def clear(self): #reset session to initial state
        self.slots = {key: None for key in self.slots}
        self.active = False
        self.errors = []
        self.time_ambiguous = None
        self.time_ambiguous_when = None

    def to_dict(self) -> dict: #convert to dict (excluding display), used for database storage info
        return {key: value for key, value in self.slots.items() if key != "tanggal_display" and value is not None and value != ""}

    def get_summary(self) -> str: #generate human readable summary to confirm to user
        s = self.slots
        date_display = s.get("tanggal_display") or s.get("tanggal", "?")
        summary = ( #its a string, not a tuple bcs tuple must be a () and a coma within it
            f"• Treatment: {s.get('treatment', '?')}\n"
            f"• Lokasi: {s.get('lokasi', '?')}\n"
            f"• Tanggal: {date_display}\n"
            f"• Jam: {s.get('jam', '?')}\n"
            f"• Nama: {s.get('nama', '?')}\n"
        )
        return summary
    
    #magic method: similar to "__str__" but "__repr__" is for developer (debug/check), while "__str__" for user
    def __repr__(self): 
        return f"<BookingSession user = {self.user_id}, active = {self.active}, complete = {self.is_complete()}>"
        #if the object with this class (BookingSession) is printed, will return line above. 