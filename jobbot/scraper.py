from __future__ import annotations

from typing import Iterable, List

from jobbot.models import JobPosting
from jobbot.sources import greenhouse, lever


def scrape_all(greenhouse_handles: Iterable[str], lever_handles: Iterable[str]) -> List[JobPosting]:
    jobs: List[JobPosting] = []
    for handle in greenhouse_handles:
        handle = handle.strip()
        if not handle:
            continue
        jobs.extend(greenhouse.fetch_jobs(handle))
    for handle in lever_handles:
        handle = handle.strip()
        if not handle:
            continue
        jobs.extend(lever.fetch_jobs(handle))
    return jobs
