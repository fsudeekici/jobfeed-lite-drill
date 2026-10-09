import json
from typing import Any

from jobfeed.common import SourceError, normalize_location, parse_date
from jobfeed.models import Job


def parse(payload: dict[str, Any]) -> list[Job]:
    items = payload.get("results")
    if not items:
        raise SourceError("beta: no 'results' in response")
    return [
        Job(
            source="beta",
            id=item["ref"],
            title=item["name"].strip(),
            location=normalize_location(item["city"] + ", " + item["country"]),
            posted_at=parse_date(item["created"]),
        )
        for item in items
    ]


def parse_file(path: str) -> list[Job]:
    with open(path, encoding="utf-8") as f:
        return parse(json.load(f))
