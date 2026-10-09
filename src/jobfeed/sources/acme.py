import json
from typing import Any

from jobfeed.common import normalize_location, parse_date
from jobfeed.models import Job


def parse(payload: dict[str, Any]) -> list[Job]:
    jobs = []
    for item in payload.get("jobs", []):
        jobs.append(
            Job(
                source="acme",
                id=str(item["id"]),
                title=item["title"].strip(),
                location=normalize_location(item["location"]),
                posted_at=parse_date(item["published"]),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
            )
        )
    return jobs


def parse_file(path: str) -> list[Job]:
    with open(path, encoding="utf-8") as f:
        return parse(json.load(f))
