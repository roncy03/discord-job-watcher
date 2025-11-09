from __future__ import annotations

from datetime import datetime
from typing import Iterable
import time

import httpx

from jobbot.models import JobPosting


class DiscordNotifier:
    def __init__(
        self,
        webhook_url: str,
        *,
        timeout: float = 10.0,
        max_retries: int = 5,
        fallback_sleep: float = 2.0,
        per_message_delay: float = 0.5,
    ) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.fallback_sleep = fallback_sleep
        self.per_message_delay = per_message_delay

    def send(self, jobs: Iterable[JobPosting], *, dry_run: bool = False) -> int:
        count = 0
        with httpx.Client(timeout=self.timeout) as client:
            for job in jobs:
                if dry_run:
                    print(f"[DRY RUN] Would notify Discord about {job.title} @ {job.company}")
                    count += 1
                    continue
                payload = self._build_payload(job)
                self._post_with_retry(client, payload)
                if self.per_message_delay:
                    time.sleep(self.per_message_delay)
                count += 1
        return count

    def _post_with_retry(self, client: httpx.Client, payload: dict) -> None:
        last_response: httpx.Response | None = None
        for attempt in range(self.max_retries):
            response = client.post(self.webhook_url, json=payload)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                try:
                    sleep_for = float(retry_after)
                except (TypeError, ValueError):
                    sleep_for = self.fallback_sleep
                sleep_for = max(sleep_for, self.fallback_sleep)
                time.sleep(sleep_for)
                last_response = response
                continue
            response.raise_for_status()
            return
        if last_response is not None:
            last_response.raise_for_status()
        raise httpx.HTTPStatusError(
            "Exceeded max retries posting to Discord",
            request=None,
            response=last_response,
        )

    def _build_payload(self, job: JobPosting) -> dict:
        timestamp = job.posted_at.isoformat() if job.posted_at else datetime.utcnow().isoformat()
        description_lines = [
            f"**Company:** {job.company}",
            f"**Location:** {job.location or 'Not listed'}",
            f"**Source:** {job.provider}/{job.handle}",
            f"**Posted:** {timestamp}",
        ]
        return {
            "content": None,
            "embeds": [
                {
                    "title": job.title,
                    "url": job.url,
                    "description": "\n".join(description_lines),
                    "color": 5814783,
                }
            ],
        }
