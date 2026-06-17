"""Request-local organization context for analytics tools."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar


_ACTIVE_ORG_ID: ContextVar[str | None] = ContextVar(
    "hermon_active_org_id",
    default=None,
)
_ACTIVE_TIMEZONE: ContextVar[str | None] = ContextVar(
    "hermon_active_timezone",
    default=None,
)


def get_active_org_id() -> str | None:
    """Return the organization ID scoped to the current request, if any."""

    value = _ACTIVE_ORG_ID.get()
    clean_value = str(value or "").strip()
    return clean_value or None


def get_active_timezone() -> str | None:
    """Return the timezone scoped to the current request, if any."""

    value = _ACTIVE_TIMEZONE.get()
    clean_value = str(value or "").strip()
    return clean_value or None


@contextmanager
def active_org_context(org_id: str, timezone_name: str | None = None) -> Iterator[None]:
    """Scope downstream tool execution to a single organization ID and timezone."""

    clean_org_id = str(org_id or "").strip()
    if not clean_org_id:
        raise ValueError("active organization ID is required.")

    clean_timezone = str(timezone_name or "").strip() or None
    org_token = _ACTIVE_ORG_ID.set(clean_org_id)
    timezone_token = _ACTIVE_TIMEZONE.set(clean_timezone)
    try:
        yield
    finally:
        _ACTIVE_TIMEZONE.reset(timezone_token)
        _ACTIVE_ORG_ID.reset(org_token)
