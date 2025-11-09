# Discord Job Watcher

Lightweight Python bot that polls Greenhouse + Lever job boards, deduplicates postings, and pushes fresh roles to a Discord channel via a webhook. A scheduled GitHub Actions workflow runs every 20 minutes, so you get near real-time alerts without keeping a server online.

## Features
- Config-driven list of Greenhouse and Lever handles (`config/sources.yaml`).
- Workday support (`workday` block in `config/sources.yaml`) so you can track tenants like Walmart that expose a Workday JSON API.
- Vendor map (`docs/vendor_map.md`) outlining which large companies use Greenhouse, Lever, Workday, Amazon Jobs, or Ashby along with public endpoints.
- Persistent dedupe store (`data/sent_jobs.json`) committed back to the repo so posted jobs aren’t repeated.
- Discord notifier with embeds showing title, company, location, source, and timestamp.
- GitHub Actions workflow that installs dependencies, runs the scraper, commits store updates, and stays in the free tier.
- Only alerts on roles whose `posted_at` date matches the current UTC day, so channels stay focused on fresh postings.

## Setup
1. **Clone repo & install deps**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure sources** – edit `config/sources.yaml` with the Greenhouse/Lever handles you care about. Add Workday entries under the `workday` list; each entry needs a tenant, site, and host (see the Walmart example).
3. **Set Discord webhook(s)** – copy `.env.example` to `.env` (for local runs) and set at least one of:
   - `DISCORD_WEBHOOK_URL_SOFTWARE` – channel for software-engineering roles.
   - `DISCORD_WEBHOOK_URL_DATA` – channel for data roles (data engineering / analyst / scientist).
   - `DISCORD_WEBHOOK_URL` – optional fallback/general channel (used if a category-specific webhook isn’t provided).
   In GitHub, add the same values as repository secrets so the workflow can post.
   > Tip: `config/webhooks.yaml` contains hard-coded fallbacks for local testing; environment variables always take precedence.
4. **Test locally**
   ```bash
   export DISCORD_WEBHOOK_URL=...
   python -m jobbot.main --dry-run
   ```
   Dry-run prints to stdout instead of notifying Discord so you can verify scraping works. Remove `--dry-run` to send real alerts.
5. **GitHub Actions** – the workflow `.github/workflows/post-jobs.yml` is already wired. It runs every 20 minutes and on manual dispatch. Ensure `DISCORD_WEBHOOK_URL` secret is set before enabling.

## Extending Sources
- Greenhouse & Lever are implemented in `jobbot/sources/`. Add Workday/Ashby/etc. clients there and register them in `jobbot/scraper.py`.
- `docs/vendor_map.md` lists high-profile companies and their ATS vendors plus public endpoints to guide future connectors.
- `scripts/verify_vendor_map.py` probes the vendor map endpoints and reports which ones currently return jobs (see the Status column in the doc).

## Dedupe Store
`data/sent_jobs.json` tracks job IDs (`provider:handle:external_id`). The workflow commits this file whenever new jobs are posted so every run knows what was already sent. If you need a clean slate, delete the file and commit the change.

## Tests
Use pytest for the small unit test covering the dedupe store:
```bash
pip install -r requirements.txt pytest
pytest
```

## Manual execution
```bash
python -m jobbot.main --config config/sources.yaml --store data/sent_jobs.json
```
Use `--dry-run` to avoid sending Discord messages.

### Filtering to software roles
By default the bot only posts jobs whose title contains `software`, `data engineer`, or `data analyst`, **and** whose `posted_at` date is today (UTC). Matching jobs are automatically routed to the corresponding Discord webhook (software vs data). Override or add more keywords via repeated `--keyword` flags, e.g.:
```bash
python -m jobbot.main --keyword software --keyword engineer
```
Older postings are ignored unless you modify the script.

## Notes
- GitHub-hosted runners get outbound internet, so the workflow can hit Greenhouse/Lever APIs for free.
- Avoid committing real webhook URLs; always rely on environment variables/secrets.
- When adding more vendors, remember to document rate limits and authentication needs in the vendor map.
