# jobfeed-lite

Collects job postings from company job APIs into one `Job` model.

## Rules
- Python 3.10+. Only standard library in `src/`. Tests use pytest.
- Every source has tests on saved real responses in `tests/fixtures/`.
- Never edit an existing fixture. A site change means a new fixture file with a new date.
- Never weaken or delete a test to make it pass.
- A source must never return 0 jobs silently. Raise `SourceError` with a clear message.
- Do not store or log personal data (names, emails, phones).
- `src/jobfeed/common.py` is shared by all sources. Check every source after changing it.
- One branch per task. Small commits.
