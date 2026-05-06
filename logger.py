import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from config import settings

#location of log folder and files
LOG_DIR = Path("logs") 
LOG_FILE = LOG_DIR / "clinic_cs.log"

MAX_BYTES = 5 * 1024 * 1024 # 5 mb each file
BACKUP_COUNT = 3 #3 backup files, total = 4

#internal fields of logging, out of these treated as
_STANDARD_FIELDS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}

#file formatter
class JsonFormatter(logging.Formatter): #this class inherit from logging.Formatter
    #the function must use "format" as a name and LogRecord as param, bcs logger will search that keyword
    def format(self, record: logging.LogRecord) -> str:
        log_obj = { 
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", # T: separator sign; Z: signifies time is in utc + 0.
            "level": record.levelname,
            "module": record.name,
            "msg": record.getMessage(),
        }
        #if error from except
        if record.exc_info: 
            log_obj["exc"] = self.formatException(record.exc_info)
        #add extra info to json (will be shown in files)
        for key, val in record.__dict__.items():
            if key not in _STANDARD_FIELDS and not key.startswith("_"):
                log_obj[key] = val
        return json.dumps(log_obj, ensure_ascii=False) #json.dumps: convert py object tp json string, json.loads vice versa
    
#console formatter (does not show the extra info)
CONSOLE_FMT = "%(asctime)s [%(levelname)-8s] %(name)-22s | %(message)s"
DATE_FMT = "%H:%M:%S"

#to set up only once when importing
_initialized = False

def _setup():
    global _initialized
    if _initialized:
        return
    _initialized = True

    LOG_DIR.mkdir(exist_ok=True) #make logs dir

    root = logging.getLogger() #call the main root using getLogger, root will have a child of handler 
    root.setLevel(getattr(logging, settings.log_level, logging.INFO)) #set the level to be shown, INFO as default

    #set where the files are going to and set the formatter, then add handler to main root
    console_handler = logging.StreamHandler() #handler to terminal
    console_handler.setFormatter(logging.Formatter(CONSOLE_FMT, datefmt=DATE_FMT))
    root.addHandler(console_handler)

    #handler to rotating files
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)

    #set level on httpx and httpcore to only show log after INFO
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)    

_setup()

#flow: make a handler at main root, when get_logger(__name__), check if there is any handler on that module or no. if no, go & check the main root which is there is. Then that LogRecord will be handled to file and console.
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name) 