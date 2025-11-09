# Vendor Map & API Notes

Run `python scripts/verify_vendor_map.py` to refresh the Status column. The table reflects the latest probe (UTC).

| Company | Stack | Endpoint | Status |
| --- | --- | --- | --- |
| Stripe | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/stripe/jobs` | ✅ 522 jobs returned |
| Datadog | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/datadog/jobs` | ✅ 443 jobs returned |
| Figma | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/figma/jobs` | ✅ 129 jobs returned |
| DoorDash | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/doordashusa/jobs` | ✅ 546 jobs returned |
| Spotify | Lever | `https://api.lever.co/v0/postings/spotify?mode=json` | ✅ 99 jobs returned |
| Medium | Lever | `https://api.lever.co/v0/postings/medium?mode=json` | ⚠️ API reachable but currently 0 jobs |
| Walmart | Workday | `https://walmart.wd5.myworkdayjobs.com/wday/cxs/walmart/WalmartExternal/jobs` | ✅ JSON API used in bot (search filter configurable) |
| Apple | Custom Site | `https://jobs.apple.com/en-us/search?team=software-and-services-SFTWR` | ✅ Loads HTML (needs scraper) |
| Microsoft | Custom Site | `https://jobs.careers.microsoft.com/global/en/search?q=software` | ✅ Loads HTML |
| Alphabet / Google | Custom Site | `https://careers.google.com/jobs/results/?q=software` | ⚠️ HTTP 301 redirect (follow manually) |
| Amazon | Amazon Jobs JSON | `https://www.amazon.jobs/en/search.json?result_limit=1&offset=0` | ✅ Returns JSON |
| Meta | Custom Site | `https://www.metacareers.com/jobs/?departments[0]=Software%20Engineering` | ⚠️ HTTP 302 (login redirect) |
| Nvidia | Custom Site | `https://www.nvidia.com/en-us/about-nvidia/careers/` | ✅ Loads HTML |
| Tesla | Custom Site | `https://www.tesla.com/careers/search/?query=software` | ❌ HTTP 403 (blocked) |
| GitHub | Custom Site | `https://www.github.careers/careers-home/jobs/4686?lang=en-us` | ✅ Loads HTML |
| Asana | Custom Site | `https://asana.com/jobs/all` | ✅ Loads HTML |
| Airbnb | Custom Site | `https://careers.airbnb.com/positions/` | ✅ Loads HTML |
| Netflix | Custom Site | `https://explore.jobs.netflix.net/careers?query=software&Teams=Engineering` | ✅ Loads HTML |
| OpenAI | Ashby | `https://api.ashbyhq.com/graphql` | ⏸️ Requires Ashby token |
| SpaceX | Ashby | `https://api.ashbyhq.com/graphql` | ⏸️ Requires Ashby token |
| Discord | Ashby | `https://api.ashbyhq.com/graphql` | ⏸️ Requires Ashby token |

**Summary**
- Only the confirmed Greenhouse/Lever handles (Stripe, Datadog, Figma, DoorDash, Spotify) emit JSON today. `config/sources.yaml` mirrors this.
- Custom-site entries respond with HTML pages—scrapers must parse DOM or follow redirects/cookies.
- Ashby boards need a company-specific public token for their GraphQL API; they remain skipped until such credentials are available.
