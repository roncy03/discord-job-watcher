from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from jobbot.config import WorkdaySource
from jobbot.models import JobPosting

POSTED_REGEX = re.compile(r"posted\s+(\d+)\s+day", re.IGNORECASE)
CSRF_REGEX = re.compile(r'"csrfToken":"([^"]+)"')


def fetch_jobs(config: WorkdaySource) -> List[JobPosting]:
    client_headers = {
        "User-Agent": "job-discord-bot/1.2",
        "Accept": "text/html,application/xhtml+xml",
    }
    with httpx.Client(timeout=20, headers=client_headers, follow_redirects=True) as client:
        token = _bootstrap_session(client, config)
        payload = {
            "appliedFacets": config.applied_facets or {},
            "limit": config.limit,
            "offset": 0,
            "searchText": config.search_text or "",
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if token:
            headers["wd-csrf-token"] = token
        try:
            response = client.post(
                f"https://{config.host}/wday/cxs/{config.tenant}/{config.site}/jobs",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            print(f"[workday] Failed to fetch {config.tenant}: {exc}")
            return []
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


def _bootstrap_session(client: httpx.Client, config: WorkdaySource) -> str | None:
    bootstrap_url = f"https://{config.host}/{config.locale}/{config.site}"
    try:
        resp = client.get(bootstrap_url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"[workday] Bootstrap failed for {config.tenant}: {exc}")
        return None
    cookie_token = resp.cookies.get("CALYPSO_CSRF_TOKEN")
    if cookie_token:
        return cookie_token
    match = CSRF_REGEX.search(resp.text)
    if match:
        return match.group(1)
    return None


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
