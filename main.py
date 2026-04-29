import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import yaml

from scraper import Job
from scraper.workday import fetch_workday_jobs
from scraper.greenhouse import fetch_greenhouse_jobs
from scraper.eightfold import fetch_eightfold_jobs
from scraper.differ import load_snapshot, save_snapshot, diff

SNAPSHOT_PATH = "data/snapshot.json"

ATS_FETCHERS = {
    "workday": fetch_workday_jobs,
    "greenhouse": fetch_greenhouse_jobs,
    "eightfold": fetch_eightfold_jobs,
}


def scrape_firm(firm_config: dict, filters: dict) -> List[Job]:
    ats = firm_config["ats"]
    fetcher = ATS_FETCHERS.get(ats)
    if not fetcher:
        logging.warning("Unknown ATS '%s' for %s", ats, firm_config["name"])
        return []
    return fetcher(firm_config, filters)


def main():
    parser = argparse.ArgumentParser(description="Consulting Firm Job Scraper")
    parser.add_argument("--dry-run", action="store_true", help="Scrape and diff but do not write snapshot")
    parser.add_argument("--firms", nargs="*", help="Firm names to scrape (default: all)")
    parser.add_argument("--verbose", action="store_true", help="Set log level to DEBUG")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    with open("config/firms.yaml", "r") as f:
        config = yaml.safe_load(f)

    filters = config.get("filters", {})
    firms = config.get("firms", [])

    if args.firms:
        target_names = {n.lower() for n in args.firms}
        firms = [f for f in firms if f["name"].lower() in target_names]

    all_jobs: List[Job] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(scrape_firm, fc, filters): fc["name"] for fc in firms}
        for future in as_completed(futures):
            firm_name = futures[future]
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
            except Exception:
                logging.exception("Scraper crashed for %s", firm_name)

    previous = load_snapshot(SNAPSHOT_PATH)
    changes = diff(all_jobs, previous)

    logging.info("=== Scrape Summary ===")
    logging.info("Firms scraped: %d", len(firms))
    logging.info("Total jobs:    %d", len(all_jobs))
    logging.info("New jobs:      %d", len(changes["new"]))
    logging.info("Removed jobs:  %d", len(changes["removed"]))
    logging.info("Unchanged:     %d", changes["unchanged_count"])

    if args.dry_run:
        logging.info("Dry run — snapshot not updated.")
    else:
        save_snapshot(all_jobs, SNAPSHOT_PATH)


if __name__ == "__main__":
    main()
