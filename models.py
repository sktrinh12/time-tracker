from dataclasses import dataclass
from datetime import date, time

@dataclass
class TimeEntry:
    work_date: date
    start_time: time
    end_time: time
    hours: float
    category: str = ""
    description: str = ""
