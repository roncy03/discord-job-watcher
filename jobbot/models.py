from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class JobPosting:
    uid: str
    provider: str
    handle: str
    title: str
    company: str
    location: str | None
    url: str
    posted_at: datetime | None
