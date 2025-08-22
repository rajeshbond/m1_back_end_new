from datetime import datetime, time
from zoneinfo import ZoneInfo


def current_ist_hour():
    return datetime.now(tz=ZoneInfo("Asia/Kolkata")).hour


def is_time_in_shift_range(inspect_time: time, shift_start: time, shift_end: time) -> bool:
    """Check if inspect_time is within shift time range (handles overnight shifts)."""
    if shift_start <= shift_end:
        # Normal shift within same day, e.g., 09:00 to 17:00
        return shift_start <= inspect_time <= shift_end
    else:
        # Overnight shift, e.g., 23:00 to 06:00 next day
        return inspect_time >= shift_start or inspect_time <= shift_end