import json
import logging
from typing import Any

from jobfeed.common import SourceError, normalize_location, parse_date
from jobfeed.models import Job

log = logging.getLogger(__name__)


def parse(payload: dict[str, Any]) -> list[Job]:
    if payload.get("api_version") == "2":
        jobs = _parse_v2(payload)
    elif "jobs" in payload:
        jobs = _parse_v1(payload)
    else:
        raise SourceError(
            f"acme: unknown response format (api_version={payload.get('api_version')!r})"
        )
    if not jobs:
        total = payload.get("meta", {}).get("total")
        raise SourceError(f"acme: parsed 0 jobs (meta.total={total!r})")
    return jobs


def _parse_v1(payload: dict[str, Any]) -> list[Job]:
    return [
        Job(
            source="acme",
            id=str(item["id"]),
            title=item["title"].strip(),
            location=normalize_location(item["location"]),
            posted_at=parse_date(item["published"]),
            salary_min=item.get("salary_min"),
            salary_max=item.get("salary_max"),
        )
        for item in payload["jobs"]
    ]


def _parse_v2(payload: dict[str, Any]) -> list[Job]:
    postings = payload.get("data", {}).get("postings")
    if postings is None:
        raise SourceError("acme: api_version 2 response has no 'data.postings'")
    jobs = []
    for item in postings:
        # Only read the fields we need. 'recruiter' holds personal data.
        try:
            posted_at = parse_date(item["published_at"])
        except SourceError as e:
            log.warning("acme: skipping posting %s: %s", item["id"], e)
            continue
        pay = item.get("compensation") or {}
        jobs.append(
            Job(
                source="acme",
                id=str(item["id"]),
                title=item["title"].strip(),
                location=_join_locations(item["locations"]),
                posted_at=posted_at,
                salary_min=pay.get("min"),
                salary_max=pay.get("max"),
                currency=pay.get("currency"),
            )
        )
    return jobs


def _join_locations(locations: list) -> str:
    """["Berlin", "Germany"] -> "Berlin, Germany"
    [["Berlin", "Germany"], ["Lisbon", "Portugal"]] -> "Berlin, Germany; Lisbon, Portugal"
    """
    if locations and all(isinstance(loc, list) for loc in locations):
        return "; ".join(_join_locations(loc) for loc in locations)
    return normalize_location(", ".join(locations))


def parse_file(path: str) -> list[Job]:
    with open(path, encoding="utf-8") as f:
        return parse(json.load(f))
