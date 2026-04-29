import json
import logging
import os
from typing import List

from scraper import Job

logger = logging.getLogger(__name__)


def load_snapshot(path: str) -> List[Job]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        data = json.load(f)
    return [Job.from_dict(j) for j in data]


def save_snapshot(jobs: List[Job], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump([j.to_dict() for j in jobs], f, indent=2)
    logger.info("Snapshot saved: %d jobs -> %s", len(jobs), path)


def diff(current: List[Job], previous: List[Job]) -> dict:
    current_ids = {j.id for j in current}
    previous_ids = {j.id for j in previous}

    new_ids = current_ids - previous_ids
    removed_ids = previous_ids - current_ids

    new_jobs = [j for j in current if j.id in new_ids]
    removed_jobs = [j for j in previous if j.id in removed_ids]

    return {
        "new": [j.to_dict() for j in new_jobs],
        "removed": [j.to_dict() for j in removed_jobs],
        "unchanged_count": len(current_ids & previous_ids),
    }
