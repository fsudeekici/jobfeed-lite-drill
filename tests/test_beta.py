from pathlib import Path

from jobfeed.sources import beta

FIXTURE = Path(__file__).parent / "fixtures" / "beta_2026-09-01.json"


def test_parses_all_jobs():
    assert len(beta.parse_file(str(FIXTURE))) == 3


def test_location_is_cleaned():
    jobs = {j.id: j for j in beta.parse_file(str(FIXTURE))}
    assert jobs["B-2"].location == "Paris, France"
    assert jobs["B-3"].location == "Madrid, Spain"
