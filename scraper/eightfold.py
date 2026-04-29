"""BCG careers via Eightfold AI API.

BCG is the highest-maintenance integration — this endpoint changes without notice.
If it breaks, the scraper logs a warning and returns an empty list.
"""
import logging
from datetime import datetime, timezone
from typing import List
from urllib.parse import quote

import requests

from scraper import Job, matches_filters, now_iso

logger = logging.getLogger(__name__)


def _slug(title: str) -> str:
    return title.lower().replace(" ", "-").replace("/", "-").replace("--", "-").strip("-")


def fetch_eightfold_jobs(firm_config: dict, filters: dict) -> List[Job]:
    base_url = firm_config.get("base_url", "https://careers.bcg.com/api/apply/v2/jobs")
    domain = firm_config.get("domain", "bcg.com")
    firm_name = firm_config["name"]

    jobs: List[Job] = []
    start = 0
    num = 20
    scraped_at = now_iso()

    while True:
        params = {
            "domain": domain,
            "start": start,
            "num": num,
            "Job Function": quote("Consulting"),
        }
        try:
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Eightfold request failed for %s (start %d): %s", firm_name, start, e)
            return jobs

        data = resp.json()
        positions = data.get("positions", [])
        if not positions:
            break

        for p in positions:
            title = p.get("name", "")
            if not matches_filters(title, filters):
                continue

            req_id = p.get("req_id", "") or str(p.get("id", ""))
            locations = p.get("location", [])
            location = locations[0].get("name", "") if locations else ""

            t_update = p.get("t_update")
            if t_update:
                try:
                    posted = datetime.fromtimestamp(t_update, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, OSError):
                    posted = scraped_at
            else:
                posted = scraped_at

            job_url = f"https://careers.bcg.com/global/en/job/{req_id}/{_slug(title)}"

            jobs.append(Job(
                id=req_id,
                title=title,
                firm=firm_name,
                ats="eightfold",
                url=job_url,
                location=location,
                posted_date=posted,
                is_parthenon=False,
                scraped_at=scraped_at,
            ))

        start += num
        total = data.get("count", 0)
        if start >= total or len(positions) < num:
            break

    logger.info("Eightfold: %s — %d jobs found", firm_name, len(jobs))
    return jobs
