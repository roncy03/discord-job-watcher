from __future__ import annotations

from datetime import datetime
from typing import List

import httpx

from jobbot.models import JobPosting

API_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{handle}/jobs"


def fetch_jobs(handle: str) -> List[JobPosting]:
    url = API_TEMPLATE.format(handle=handle)
    with httpx.Client(timeout=20.0, headers={"User-Agent": "job-discord-bot/1.0"}) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    jobs: List[JobPosting] = []
    for job in payload.get("jobs", []):
        job_id = f"greenhouse:{handle}:{job.get('id')}"
        jobs.append(
            JobPosting(
                uid=job_id,
                provider="greenhouse",
                handle=handle,
                title=job.get("title", "Unknown role"),
                company=(job.get("company") or {}).get("name") or handle,
                location=(job.get("location") or {}).get("name"),
                url=job.get("absolute_url"),
                posted_at=_parse_dt(job.get("updated_at") or job.get("created_at")),
            )
        )
    return jobs


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None
