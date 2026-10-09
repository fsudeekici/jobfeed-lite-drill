"""Shared helpers. Used by every source."""
from datetime import datetime


class SourceError(Exception):
    pass


def normalize_location(raw: str) -> str:
    """'  Berlin ,  Germany ' -> 'Berlin, Germany'"""
    parts = [p.strip() for p in raw.split(",")]
    return ", ".join(p for p in parts if p)


def parse_date(raw: str) -> datetime:
    """ISO 8601 with timezone, e.g. 2026-09-01T10:00:00+02:00."""
    value = datetime.fromisoformat(raw)
    if value.tzinfo is None:
        raise SourceError(f"date without timezone: {raw!r}")
    return value
