from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Job:
    id: str
    title: str
    firm: str
    ats: str
    url: str
    location: str
    posted_date: str
    is_parthenon: bool
    scraped_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        return cls(**data)


def matches_filters(title: str, filters: dict) -> bool:
    title_lower = title.lower()
    for kw in filters.get("exclusion_keywords", []):
        if kw.lower() in title_lower:
            return False
    for kw in filters.get("seniority_keywords", []):
        if kw.lower() in title_lower:
            return True
    return False


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
