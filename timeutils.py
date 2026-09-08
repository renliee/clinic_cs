"""
Time helpers.
Business logic (dates customers pick, dashboard day/week windows) runs on WIB.
Audit instants and token expiry stay UTC. see auth/ and repository.confirmed_at.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

JAKARTA = ZoneInfo("Asia/Jakarta")


def now_wib() -> datetime:
    """Current clock time is in Jakarta. Use for all business logic."""
    return datetime.now(JAKARTA)