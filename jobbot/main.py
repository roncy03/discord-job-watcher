from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from jobbot.config import load_settings
from jobbot.notifier import DiscordNotifier
from jobbot.scraper import scrape_all
from jobbot.store import DedupeStore
from jobbot.models import JobPosting

SOFTWARE_KEYWORDS = ["software"]
DATA_KEYWORDS = ["data engineer", "data analyst", "data scientist"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape job boards and post to Discord")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/sources.yaml"),
        help="Path to sources yaml",
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=Path("data/sent_jobs.json"),
        help="Path to dedupe store",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not send Discord messages")
    parser.add_argument(
        "--keyword",
        dest="keywords",
        action="append",
        help="Only send jobs whose title contains this keyword (case-insensitive). "
        "Specify multiple times for OR logic. Defaults to 'software,data engineer,data analyst'.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    load_dotenv()
    settings = load_settings(args.config)
    store = DedupeStore(args.store)
    jobs = scrape_all(settings.sources.greenhouse, settings.sources.lever)
    print(f"Fetched {len(jobs)} postings from configured sources")

    new_jobs = [job for job in jobs if not store.has(job.uid)]
    if not new_jobs:
        print("No new jobs found")
        return 0
    default_keywords = sorted(set(SOFTWARE_KEYWORDS + DATA_KEYWORDS))
    user_keywords = args.keywords if args.keywords else default_keywords
    keywords = [kw.lower() for kw in user_keywords]
    if keywords:
        filtered_jobs = [job for job in new_jobs if _title_contains(job.title, keywords)]
        print(f"{len(filtered_jobs)} of {len(new_jobs)} new postings matched keywords {keywords}")
    else:
        filtered_jobs = new_jobs

    today = datetime.now(timezone.utc).date()
    window_start = today - timedelta(days=1)
    filtered_jobs = [job for job in filtered_jobs if _is_within_window(job, window_start, today)]
    print(
        f"{len(filtered_jobs)} postings remain after filtering to jobs posted between "
        f"{window_start.isoformat()} and {today.isoformat()} (UTC)"
    )

    if not filtered_jobs:
        print("No new jobs match the keyword filter")
        return 0

    data_jobs, software_jobs, other_jobs = _partition_jobs(filtered_jobs)
    print(
        f"Routing {len(software_jobs)} software jobs, {len(data_jobs)} data jobs, "
        f"{len(other_jobs)} uncategorized jobs"
    )

    sent_total = 0
    stored_ids: set[str] = set()

    def send_jobs(jobs: list[JobPosting], webhook: str | None, label: str) -> int:
        if not jobs or not webhook:
            if jobs:
                print(f"No webhook configured for {label}; skipping {len(jobs)} jobs")
            return 0
        notifier = DiscordNotifier(str(webhook))
        jobs.sort(key=lambda job: job.posted_at or datetime.min.replace(tzinfo=timezone.utc))
        sent = notifier.send(jobs, dry_run=args.dry_run)
        stored_ids.update(job.uid for job in jobs)
        print(f"Sent {sent} {label} job(s) to Discord")
        return sent

    sent_total += send_jobs(
        data_jobs,
        settings.discord_webhook_url_data or settings.discord_webhook_url,
        "data",
    )
    sent_total += send_jobs(
        software_jobs,
        settings.discord_webhook_url_software or settings.discord_webhook_url,
        "software",
    )
    sent_total += send_jobs(
        other_jobs,
        settings.discord_webhook_url,
        "general",
    )

    if sent_total == 0:
        print("No jobs were sent to Discord")
        return 0

    now_ts = datetime.now(timezone.utc).isoformat()
    for job_id in stored_ids:
        store.add(job_id, now_ts)
    store.save()
    print(f"Notified Discord about {sent_total} jobs")
    return 0


def _title_contains(title: str, keywords: list[str]) -> bool:
    haystack = (title or "").lower()
    return any(keyword in haystack for keyword in keywords)


def _is_within_window(job: "JobPosting", start_date, end_date) -> bool:
    if not job.posted_at:
        return False
    dt = job.posted_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    job_date = dt.date()
    return start_date <= job_date <= end_date


def _is_software_job(job: JobPosting) -> bool:
    return _title_contains(job.title, [kw.lower() for kw in SOFTWARE_KEYWORDS])


def _is_data_job(job: JobPosting) -> bool:
    return _title_contains(job.title, [kw.lower() for kw in DATA_KEYWORDS])


def _partition_jobs(jobs: list[JobPosting]) -> tuple[list[JobPosting], list[JobPosting], list[JobPosting]]:
    data_jobs: list[JobPosting] = []
    software_jobs: list[JobPosting] = []
    other_jobs: list[JobPosting] = []
    for job in jobs:
        if _is_data_job(job):
            data_jobs.append(job)
        elif _is_software_job(job):
            software_jobs.append(job)
        else:
            other_jobs.append(job)
    return data_jobs, software_jobs, other_jobs


if __name__ == "__main__":
    raise SystemExit(main())
