from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jobbot.config import load_settings
from jobbot.models import JobPosting
from jobbot.scraper import scrape_all

DEFAULT_KEYWORDS = ["software", "data engineer", "data analyst"]
REPORT_PATH = Path("reports/latest.md")


def title_contains(title: str, keywords: Iterable[str]) -> bool:
    haystack = (title or "").lower()
    return any(keyword in haystack for keyword in keywords)


def build_report(jobs: list[JobPosting], keywords: list[str]) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = len(jobs)
    counts = Counter(f"{job.provider}:{job.handle}" for job in jobs)
    rows = "\n".join(
        f"| {src} | {count} |" for src, count in sorted(counts.items(), key=lambda x: x[0])
    ) or "| _None_ | 0 |"
    sample = sorted(jobs, key=_sort_key, reverse=True)[:10]
    sample_lines = "\n".join(
        f"- **{job.title}** @ {job.company or job.handle} — {job.location or 'N/A'} — {job.url}"
        for job in sample
    ) or "- No matches"
    keywords_str = ", ".join(keywords)
    return f"""# Job Alert Report

- Generated: {now}
- Keywords: {keywords_str}
- Matches: {total}

| Source | Matches |
| --- | --- |
{rows}

## Latest Matches (up to 10)
{sample_lines}
"""


def main() -> None:
    load_dotenv()
    settings = load_settings(Path("config/sources.yaml"))
    keywords = [kw.lower() for kw in DEFAULT_KEYWORDS]
    jobs = scrape_all(settings.sources.greenhouse, settings.sources.lever)
    today = datetime.utcnow().date()
    window_start = today - timedelta(days=1)
    filtered = [
        job
        for job in jobs
        if title_contains(job.title, keywords)
        and _is_within_window(job, window_start, today)
    ]
    report = build_report(filtered, keywords)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH} with {len(filtered)} matches")


def _sort_key(job: JobPosting) -> datetime:
    dt = job.posted_at
    if not dt:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_within_window(job: JobPosting, start_date, end_date) -> bool:
    if not job.posted_at:
        return False
    dt = job.posted_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    job_date = dt.date()
    return start_date <= job_date <= end_date


if __name__ == "__main__":
    main()
