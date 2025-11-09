from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from jobbot.config import WorkdaySource
from jobbot.models import JobPosting


POSTED_REGEX = re.compile(r"posted\s+(\d+)\s+day", re.IGNORECASE)


def fetch_jobs(config: WorkdaySource) -> List[JobPosting]:
    url = f"https://{config.host}/wday/cxs/{config.tenant}/{config.site}/jobs"
    payload = {
        "appliedFacets": {},
        "limit": config.limit,
        "offset": 0,
        "searchText": config.search_text or "",
    }
    with httpx.Client(timeout=20, headers={"User-Agent": "job-discord-bot/1.0"}) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    jobs: List[JobPosting] = []
    for posting in data.get("jobPostings", []):
        external_path = posting.get("externalPath")
        if not external_path:
            continue
        job_id = posting.get("bulletFields", [external_path])
        job_id_str = job_id[0] if isinstance(job_id, list) else external_path
        job_url = f"https://{config.host}{external_path}"
        jobs.append(
            JobPosting(
                uid=f"workday:{config.tenant}:{job_id_str}",
                provider="workday",
                handle=config.tenant,
                title=posting.get("title", "Unknown role"),
                company=config.tenant,
                location=posting.get("locationsText"),
                url=job_url,
                posted_at=_parse_posted_on(posting.get("postedOn")),
            )
        )
    return jobs


def _parse_posted_on(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.lower()
    now = datetime.now(timezone.utc)
    if "today" in text:
        return now
    if "yesterday" in text:
        return now - timedelta(days=1)
    match = POSTED_REGEX.search(text)
    if match:
        days = int(match.group(1))
        days = min(days, 30)
        return now - timedelta(days=days)
    if "30+" in text:
        return now - timedelta(days=30)
    return None
