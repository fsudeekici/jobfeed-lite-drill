from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Job:
    source: str
    id: str
    title: str
    location: str
    posted_at: datetime
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
