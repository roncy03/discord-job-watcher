from __future__ import annotations

from typing import Iterable, List

from jobbot.config import WorkdaySource
from jobbot.models import JobPosting
from jobbot.sources import greenhouse, lever, workday


def scrape_all(
    greenhouse_handles: Iterable[str],
    lever_handles: Iterable[str],
    workday_sources: Iterable[WorkdaySource] | None = None,
) -> List[JobPosting]:
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
    if workday_sources:
        for source in workday_sources:
            jobs.extend(workday.fetch_jobs(source))
    return jobs
