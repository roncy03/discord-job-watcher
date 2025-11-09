from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import httpx

from jobbot.models import JobPosting

API_TEMPLATE = "https://api.lever.co/v0/postings/{handle}?mode=json"


def fetch_jobs(handle: str) -> List[JobPosting]:
    url = API_TEMPLATE.format(handle=handle)
    with httpx.Client(timeout=20.0, headers={"User-Agent": "job-discord-bot/1.0"}) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    jobs: List[JobPosting] = []
    for job in payload:
        job_id = f"lever:{handle}:{job.get('id')}"
        jobs.append(
            JobPosting(
                uid=job_id,
                provider="lever",
                handle=handle,
                title=job.get("text", "Unknown role"),
                company=(job.get("categories") or {}).get("team") or handle,
                location=(job.get("categories") or {}).get("location"),
                url=job.get("hostedUrl"),
                posted_at=_parse_ms(job.get("createdAt")),
            )
        )
    return jobs


def _parse_ms(value):
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    except (ValueError, OSError, TypeError):
        return None
