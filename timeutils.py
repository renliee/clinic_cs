"""
Time helpers.
Business logic (dates customers pick, admin stats dashboard) runs on WIB.
Audit instants (session.py) and token expiry stay UTC. see auth/, repository.confirmed_at and session.py. 
"""

from datetime import datetime
from zoneinfo import ZoneInfo

JAKARTA = ZoneInfo("Asia/Jakarta")


def now_wib() -> datetime:
    """Current clock time is in Jakarta. Use for all business logic."""
    return datetime.now(JAKARTA)