import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "clinic_cs.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()      # override: LOG_LEVEL=DEBUG python main.py
MAX_BYTES = 5 * 1024 * 1024                             # 5MB per file
BACKUP_COUNT = 3                                        # keep last 3 rotated files

# Known standard LogRecord fields — anything outside this is treated as extra
_STANDARD_FIELDS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}

class JsonFormatter(logging.Formatter): #inherit from logging.Formatter

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "module": record.name,
            "msg": record.getMessage(),
        }
        # Attach exception info if present
        if record.exc_info:
            log_obj["exc"] = self.formatException(record.exc_info)
        # Attach extra fields passed via extra={} — whitelist guards against leaking internal fields
        for key, val in record.__dict__.items():
            if key not in _STANDARD_FIELDS and not key.startswith("_"):
                log_obj[key] = val 
        return json.dumps(log_obj, ensure_ascii=False) #json.dumps connvert dict to json string

# --- Console Formatter (human readable) ---
CONSOLE_FMT = "%(asctime)s [%(levelname)-8s] %(name)-20s | %(message)s"
DATE_FMT = "%H:%M:%S"

# --- Setup (runs once at import) ---
_initialized = False

def _setup() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True

    LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(CONSOLE_FMT, datefmt=DATE_FMT))
    root.addHandler(console)

    # Rotating file handler (JSON)
    file_h = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_h.setFormatter(JsonFormatter())
    root.addHandler(file_h)

_setup()

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)