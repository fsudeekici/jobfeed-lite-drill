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
    assert payload["meta"]["total"] == 7
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


def test_v2_no_personal_data(caplog):
    with caplog.at_level(logging.DEBUG):
        jobs = acme.parse_file(str(NEW))
    for job in jobs:
        assert "recruiter" not in asdict(job)
        assert "@" not in repr(job)
    assert "@" not in caplog.text


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
