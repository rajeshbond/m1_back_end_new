from datetime import datetime, time, timedelta
from typing import List

from fastapi import HTTPException
import pandas as pd

from app import schemas

def calculate_duration(start: str, end: str) -> float:
    fmt = "%H:%M"
    start_dt = datetime.strptime(start, fmt)
    end_dt = datetime.strptime(end, fmt)
    if end_dt <= start_dt:  # Overnight shift handling
        end_dt = end_dt.replace(day=end_dt.day + 1)
    return (end_dt - start_dt).seconds / 3600  # hours

def check_overlap(timings):
    for i, t1 in enumerate(timings):
        for j, t2 in enumerate(timings):
            if i >= j:
                continue
            if t1.weekday == t2.weekday and is_overlap(t1.shift_start, t1.shift_end, t2.shift_start, t2.shift_end):
                raise Exception(f"Overlap detected between timings on weekday {t1.weekday}")

def is_overlap(start1, end1, start2, end2):
    fmt = "%H:%M"
    s1, e1 = datetime.strptime(start1, fmt), datetime.strptime(end1, fmt)
    s2, e2 = datetime.strptime(start2, fmt), datetime.strptime(end2, fmt)
    if e1 <= s1: e1 = e1.replace(day=e1.day + 1)
    if e2 <= s2: e2 = e2.replace(day=e2.day + 1)
    return s1 < e2 and s2 < e1


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
