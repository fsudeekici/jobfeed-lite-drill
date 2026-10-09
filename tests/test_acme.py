import json
import logging
from dataclasses import asdict
from pathlib import Path

import pytest

from jobfeed.common import SourceError
from jobfeed.sources import acme

FIXTURES = Path(__file__).parent / "fixtures"
OLD = FIXTURES / "acme_2026-09-01.json"
NEW = FIXTURES / "acme_2026-10-09.json"


def test_parses_all_jobs():
    payload = json.loads(OLD.read_text())
    jobs = acme.parse(payload)
    assert len(jobs) == payload["meta"]["total"] == 6


def test_known_job():
    job = {j.id: j for j in acme.parse_file(str(OLD))}["101"]
    assert job.title == "Backend Engineer"
    assert job.location == "Berlin, Germany"
    assert job.salary_min == 60000
    assert job.salary_max == 75000
    assert job.posted_at.isoformat() == "2026-08-20T09:00:00+02:00"


def test_missing_salary_is_none():
    job = {j.id: j for j in acme.parse_file(str(OLD))}["103"]
    assert job.salary_min is None
    assert job.salary_max is None


def test_old_format_has_no_currency():
    job = {j.id: j for j in acme.parse_file(str(OLD))}["101"]
    assert job.currency is None


# --- API v2 (TICKET-142) ---


def v2_jobs():
    return {j.id: j for j in acme.parse_file(str(NEW))}


def test_v2_parses_all_valid_jobs():
    payload = json.loads(NEW.read_text())
    jobs = acme.parse(payload)
    # 7 postings, 206 is skipped because its date has no timezone
    assert len(jobs) == payload["meta"]["total"] - 1
    assert sorted(j.id for j in jobs) == ["201", "202", "203", "204", "205", "207"]


def test_v2_known_job():
    job = v2_jobs()["201"]
    assert job.source == "acme"
    assert job.title == "Backend Engineer"
    assert job.location == "Berlin, Germany"
    assert job.salary_min == 62000
    assert job.salary_max == 78000
    assert job.currency == "EUR"
    assert job.posted_at.isoformat() == "2026-10-01T09:00:00+02:00"


def test_v2_multiple_locations_are_joined():
    assert v2_jobs()["205"].location == "Berlin, Germany; Lisbon, Portugal"


def test_v2_null_compensation_is_none():
    job = v2_jobs()["203"]
    assert job.salary_min is None
    assert job.salary_max is None
    assert job.currency is None


def test_v2_keeps_currency():
    assert v2_jobs()["207"].currency == "GBP"


def test_v2_date_without_timezone_is_skipped_with_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="jobfeed.sources.acme"):
        jobs = v2_jobs()
    assert "206" not in jobs
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "206" in warnings[0].getMessage()


JOB_FIELDS = {
    "source", "id", "title", "location", "posted_at",
    "salary_min", "salary_max", "currency",
}


def test_v2_no_personal_data(caplog):
    # Read personal data from the fixture so it is never written in this file.
    postings = json.loads(NEW.read_text())["data"]["postings"]
    personal = {p["recruiter"][k] for p in postings for k in ("name", "email")}
    assert personal

    with caplog.at_level(logging.DEBUG):
        jobs = acme.parse_file(str(NEW))
    assert len(jobs) == 6
    for job in jobs:
        # A new Job field must be reviewed for personal data before it is added here.
        assert set(asdict(job)) == JOB_FIELDS
        # any() keeps pytest from printing the personal data on failure.
        assert not any(v in repr(job) for v in personal), f"personal data in job {job.id}"
    assert not any(v in caplog.text for v in personal), "personal data in logs"


# --- never return 0 jobs silently ---


def test_old_format_with_no_jobs_raises():
    with pytest.raises(SourceError, match="0 jobs"):
        acme.parse({"jobs": [], "meta": {"total": 0}})


def test_v2_with_no_postings_raises():
    with pytest.raises(SourceError, match="0 jobs"):
        acme.parse({"api_version": "2", "data": {"postings": []}, "meta": {"total": 0}})


def test_v2_with_all_postings_skipped_raises():
    posting = {
        "id": 1,
        "title": "X",
        "locations": ["Berlin", "Germany"],
        "published_at": "2026-10-06T09:45:00",
        "compensation": None,
    }
    payload = {"api_version": "2", "data": {"postings": [posting]}, "meta": {"total": 1}}
    with pytest.raises(SourceError, match="0 jobs"):
        acme.parse(payload)


def test_unknown_format_raises():
    with pytest.raises(SourceError, match="unknown response format"):
        acme.parse({"api_version": "3", "items": []})


# --- malformed v2 postings are skipped with a warning ---


GOOD_POSTING = {
    "id": 1,
    "title": "X",
    "locations": ["Berlin", "Germany"],
    "published_at": "2026-10-06T09:45:00+02:00",
    "compensation": None,
}


def _v2_payload(*postings):
    return {"api_version": "2", "data": {"postings": list(postings)}, "meta": {"total": len(postings)}}


def _bad_posting(changes):
    posting = {**GOOD_POSTING, "id": 2, **changes}
    return {k: v for k, v in posting.items() if v is not ...}


BAD_POSTINGS = pytest.mark.parametrize(
    "changes",
    [
        {"title": ...},
        {"locations": ...},
        {"published_at": ...},
        {"published_at": "not a date"},
        {"locations": ["Berlin", ["Lisbon", "Portugal"]]},
    ],
    ids=["no-title", "no-locations", "no-date", "bad-date", "mixed-locations"],
)


@BAD_POSTINGS
def test_v2_malformed_posting_is_skipped_with_warning(changes, caplog):
    with caplog.at_level(logging.WARNING, logger="jobfeed.sources.acme"):
        jobs = acme.parse(_v2_payload(GOOD_POSTING, _bad_posting(changes)))
    assert [j.id for j in jobs] == ["1"]
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "skipping posting 2" in warnings[0].getMessage()


@BAD_POSTINGS
def test_v2_only_malformed_postings_raises(changes):
    with pytest.raises(SourceError, match="0 jobs"):
        acme.parse(_v2_payload(_bad_posting(changes)))
