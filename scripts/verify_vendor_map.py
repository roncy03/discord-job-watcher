from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Optional

import httpx


@dataclass
class VendorEntry:
    company: str
    vendor: str
    kind: str
    handle: str | None = None
    url: str | None = None


GREENHOUSE_HANDLES = [
    VendorEntry("Stripe", "Greenhouse", "gh", handle="stripe"),
    VendorEntry("Datadog", "Greenhouse", "gh", handle="datadog"),
    VendorEntry("Figma", "Greenhouse", "gh", handle="figma"),
    VendorEntry("DoorDash", "Greenhouse", "gh", handle="doordashusa"),
]

LEVER_HANDLES = [
    VendorEntry("Spotify", "Lever", "lever", handle="spotify"),
    VendorEntry("Medium", "Lever", "lever", handle="medium"),
]

MAG7_AND_OTHERS = [
    VendorEntry("Apple", "Custom Site", "html", url="https://jobs.apple.com/en-us/search?team=software-and-services-SFTWR"),
    VendorEntry("Microsoft", "Custom Site", "html", url="https://jobs.careers.microsoft.com/global/en/search?q=software"),
    VendorEntry("Alphabet/Google", "Custom Site", "html", url="https://careers.google.com/jobs/results/?q=software"),
    VendorEntry("Amazon", "Amazon Jobs", "amazon", url="https://www.amazon.jobs/en/search.json?result_limit=1&offset=0"),
    VendorEntry("Meta", "Custom Site", "html", url="https://www.metacareers.com/jobs/?departments[0]=Software%20Engineering"),
    VendorEntry("Nvidia", "Custom Site", "html", url="https://www.nvidia.com/en-us/about-nvidia/careers/"),
    VendorEntry("Tesla", "Custom Site", "html", url="https://www.tesla.com/careers/search/?query=software"),
]

OTHER_ENTRIES = [
    VendorEntry("GitHub", "Custom Site", "html", url="https://www.github.careers/careers-home/jobs/4686?lang=en-us"),
    VendorEntry("Asana", "Custom Site", "html", url="https://asana.com/jobs/all"),
    VendorEntry("Airbnb", "Custom Site", "html", url="https://careers.airbnb.com/positions/"),
    VendorEntry("Netflix", "Custom Site", "html", url="https://explore.jobs.netflix.net/careers?query=software&Teams=Engineering"),
    VendorEntry("OpenAI", "Ashby", "skip"),
    VendorEntry("SpaceX", "Ashby", "skip"),
    VendorEntry("Discord", "Ashby", "skip"),
]

ENTRIES = GREENHOUSE_HANDLES + LEVER_HANDLES + MAG7_AND_OTHERS + OTHER_ENTRIES


def check_greenhouse(entry: VendorEntry) -> tuple[str, Optional[int]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{entry.handle}/jobs"
    resp = httpx.get(url, timeout=15)
    if resp.is_success:
        data = resp.json()
        return "OK", len(data.get("jobs", []))
    return f"HTTP {resp.status_code}", None


def check_lever(entry: VendorEntry) -> tuple[str, Optional[int]]:
    url = f"https://api.lever.co/v0/postings/{entry.handle}?mode=json"
    resp = httpx.get(url, timeout=15)
    if resp.is_success:
        data = resp.json()
        return "OK", len(data)
    return f"HTTP {resp.status_code}", None


def check_amazon(entry: VendorEntry) -> tuple[str, Optional[int]]:
    resp = httpx.get(entry.url, timeout=15)
    if resp.is_success:
        data = resp.json()
        return "OK", len(data.get("jobs", []))
    return f"HTTP {resp.status_code}", None


def check_html(entry: VendorEntry) -> tuple[str, Optional[int]]:
    resp = httpx.get(entry.url, timeout=15)
    if resp.is_success:
        return "OK", None
    return f"HTTP {resp.status_code}", None


DISPATCH: dict[str, Callable[[VendorEntry], tuple[str, Optional[int]]]] = {
    "gh": check_greenhouse,
    "lever": check_lever,
    "amazon": check_amazon,
    "html": check_html,
}


def main() -> None:
    results = []
    for entry in ENTRIES:
        handler = DISPATCH.get(entry.kind)
        if not handler:
            results.append({"company": entry.company, "vendor": entry.vendor, "status": "SKIPPED"})
            continue
        try:
            status, count = handler(entry)
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "company": entry.company,
                    "vendor": entry.vendor,
                    "status": "ERROR",
                    "detail": repr(exc),
                }
            )
        else:
            payload = {
                "company": entry.company,
                "vendor": entry.vendor,
                "status": status,
            }
            if count is not None:
                payload["jobs"] = count
            results.append(payload)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
