import logging
import time
from typing import List

import requests

from scraper import Job, matches_filters, now_iso

logger = logging.getLogger(__name__)


def fetch_workday_jobs(firm_config: dict, filters: dict) -> List[Job]:
    tenant = firm_config["tenant"]
    wd_server = firm_config["wd_server"]
    site = firm_config["site"]
    firm_name = firm_config["name"]
    base = f"https://{tenant}.{wd_server}.myworkdayjobs.com"
    api_url = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    page_url = f"{base}/en-US/{site}"

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })

    try:
        session.get(page_url, timeout=15)
    except requests.RequestException as e:
        logger.warning("Workday session init failed for %s: %s", firm_name, e)
        return []

    jobs: List[Job] = []
    offset = 0
    limit = 20
    scraped_at = now_iso()
    is_ey = "eyglobal" in tenant.lower()

    while True:
        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": "Consultant",
        }
        try:
            resp = session.post(api_url, json=payload, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Workday request failed for %s (offset %d): %s", firm_name, offset, e)
            return jobs

        data = resp.json()
        postings = data.get("jobPostings", [])
        if not postings:
            break

        for p in postings:
            title = p.get("title", "")
            if not matches_filters(title, filters):
                continue

            external_path = p.get("externalPath", "")
            job_url = f"{base}/en-US/{site}{external_path}"
            location = p.get("locationsText", "") or ""
            posted = p.get("postedOn", scraped_at)

            is_parthenon = False
            if is_ey:
                bullet_fields = p.get("bulletFields", [])
                combined = (title + " " + " ".join(bullet_fields)).lower()
                if "parthenon" in combined:
                    is_parthenon = True

            job_id = ""
            bullet_fields = p.get("bulletFields", [])
            if bullet_fields:
                job_id = bullet_fields[0]
            if not job_id:
                job_id = external_path

            jobs.append(Job(
                id=job_id,
                title=title,
                firm=firm_name,
                ats="workday",
                url=job_url,
                location=location,
                posted_date=posted,
                is_parthenon=is_parthenon,
                scraped_at=scraped_at,
            ))

        offset += limit
        if len(postings) < limit:
            break
        time.sleep(1.5)

    logger.info("Workday: %s — %d jobs found", firm_name, len(jobs))
    return jobs
