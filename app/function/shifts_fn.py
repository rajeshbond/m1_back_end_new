


from datetime import datetime, time, timedelta
from typing import List

from fastapi import HTTPException
import pandas as pd

from app import schemas


def _normalize_to_str(val) -> str:
    """Ensure we always have HH:MM string whether input is str or datetime.time."""
    if isinstance(val, time):
        return val.strftime("%H:%M")
    return str(val)


def calculate_duration(start, end) -> float:
    """Return duration in hours, handling overnight shifts."""
    fmt = "%H:%M"
    start_dt = datetime.strptime(_normalize_to_str(start), fmt)
    end_dt = datetime.strptime(_normalize_to_str(end), fmt)
    if end_dt <= start_dt:  # overnight shift (crosses midnight)
        end_dt += timedelta(days=1)
    return (end_dt - start_dt).seconds / 3600  # hours


def is_overlap(start1, end1, start2, end2) -> bool:
    """Check if two time ranges overlap, handling overnight shifts."""
    fmt = "%H:%M"
    s1, e1 = datetime.strptime(_normalize_to_str(start1), fmt), datetime.strptime(_normalize_to_str(end1), fmt)
    s2, e2 = datetime.strptime(_normalize_to_str(start2), fmt), datetime.strptime(_normalize_to_str(end2), fmt)

    if e1 <= s1:  # shift 1 crosses midnight
        e1 += timedelta(days=1)
    if e2 <= s2:  # shift 2 crosses midnight
        e2 += timedelta(days=1)

    return s1 < e2 and s2 < e1


def check_overlap(timings: List[schemas.ShiftTimingCreate]):
    """Check for internal overlaps within the provided timings list."""
    for i, t1 in enumerate(timings):
        for j, t2 in enumerate(timings):
            if i >= j:
                continue
            if t1.weekday == t2.weekday and is_overlap(
                t1.shift_start, t1.shift_end, t2.shift_start, t2.shift_end
            ):
                raise HTTPException(
                    400,
                    f"Overlap detected between timings on weekday {t1.weekday}"
                )



# def calculate_duration(start: str, end: str) -> float:
#     fmt = "%H:%M"
#     start_dt = datetime.strptime(start, fmt)
#     end_dt = datetime.strptime(end, fmt)
#     if end_dt <= start_dt:  # Overnight shift handling
#         end_dt = end_dt.replace(day=end_dt.day + 1)
#     return (end_dt - start_dt).seconds / 3600  # hours

# def check_overlap(timings):
#     for i, t1 in enumerate(timings):
#         for j, t2 in enumerate(timings):
#             if i >= j:
#                 continue
#             if t1.weekday == t2.weekday and is_overlap(t1.shift_start, t1.shift_end, t2.shift_start, t2.shift_end):
#                 raise Exception(f"Overlap detected between timings on weekday {t1.weekday}")

# def is_overlap(start1, end1, start2, end2):
#     fmt = "%H:%M"
#     s1, e1 = datetime.strptime(start1, fmt), datetime.strptime(end1, fmt)
#     s2, e2 = datetime.strptime(start2, fmt), datetime.strptime(end2, fmt)
#     if e1 <= s1: e1 = e1.replace(day=e1.day + 1)
#     if e2 <= s2: e2 = e2.replace(day=e2.day + 1)
#     return s1 < e2 and s2 < e1


# def calculate_duration(start: time, end: time) -> float:
#     start_dt = datetime.combine(datetime.today(), start)
#     end_dt = datetime.combine(datetime.today(), end)
#     if end_dt <= start_dt:
#         end_dt += timedelta(days=1)
#     return (end_dt - start_dt).total_seconds() / 3600

# def check_overlap(timings: List[schemas.ShiftTimingCreate]):
#     df = pd.DataFrame([t.model_dump() for t in timings])
#     df = df.sort_values(by=["weekday", "shift_start"])
#     for day, group in df.groupby("weekday"):
#         for i in range(1, len(group)):
#             prev = group.iloc[i - 1]
#             curr = group.iloc[i]
#             if prev.shift_end > curr.shift_start:
#                 raise HTTPException(400, f"Overlapping shifts on weekday {day}")
