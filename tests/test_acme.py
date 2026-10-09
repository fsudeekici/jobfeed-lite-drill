import json
from pathlib import Path

from jobfeed.sources import acme

FIXTURES = Path(__file__).parent / "fixtures"
OLD = FIXTURES / "acme_2026-09-01.json"


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
