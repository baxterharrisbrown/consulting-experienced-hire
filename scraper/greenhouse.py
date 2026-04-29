import logging
from typing import List

import requests

from scraper import Job, matches_filters, now_iso

logger = logging.getLogger(__name__)


def fetch_greenhouse_jobs(firm_config: dict, filters: dict) -> List[Job]:
    slug = firm_config["slug"]
    slug_alt = firm_config.get("slug_alt")
    firm_name = firm_config["name"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

    scraped_at = now_iso()

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404 and slug_alt:
            logger.info("Greenhouse: slug '%s' returned 404, trying '%s'", slug, slug_alt)
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug_alt}/jobs?content=true"
            resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Greenhouse request failed for %s (slug: %s): %s", firm_name, slug, e)
        return []

    data = resp.json()
    postings = data.get("jobs", [])
    jobs: List[Job] = []

    for p in postings:
        title = p.get("title", "")
        if not matches_filters(title, filters):
            continue

        location_obj = p.get("location", {})
        location = location_obj.get("name", "") if isinstance(location_obj, dict) else ""
        posted = p.get("updated_at", scraped_at)

        abs_url = p.get("absolute_url", "")

        jobs.append(Job(
            id=str(p.get("id", "")),
            title=title,
            firm=firm_name,
            ats="greenhouse",
            url=abs_url,
            location=location,
            posted_date=posted,
            is_parthenon=False,
            scraped_at=scraped_at,
        ))

    logger.info("Greenhouse: %s — %d jobs found", firm_name, len(jobs))
    return jobs
