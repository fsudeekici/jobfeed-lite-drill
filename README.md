# jobfeed-lite

## About this drill

- A second Claude chat made this repo, the ticket and its hidden traps, as a practice live session.
- The names and emails in the fixtures are fake.
- My work is the 4 commits on this branch: tests first, then the fix, then stronger tests.

Two sources today: `acme` and `beta`. Both read a JSON API.

    pip install pytest
    python -m pytest -q
    python scripts/run.py tests/fixtures/acme_2026-10-09.json acme

`logs/run.log` is the log from last night's production run.
