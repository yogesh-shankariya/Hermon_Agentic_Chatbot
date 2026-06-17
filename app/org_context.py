"""Request-local organization context for analytics tools."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_ACTIVE_ORG_ID: ContextVar[str | None] = ContextVar(
    "hermon_active_org_id",
    default=None,
)
_ACTIVE_TIMEZONE_NAME: ContextVar[str | None] = ContextVar(
    "hermon_active_timezone_name",
    default=None,
)


def get_active_org_id() -> str | None:
    """Return the organization ID scoped to the current request, if any."""

    value = _ACTIVE_ORG_ID.get()
    clean_value = str(value or "").strip()
    return clean_value or None


def get_active_timezone_name() -> str | None:
    """Return the timezone scoped to the current request, if any."""

    value = _ACTIVE_TIMEZONE_NAME.get()
    clean_value = str(value or "").strip()
    return clean_value or None


@contextmanager
def active_org_context(org_id: str) -> Iterator[None]:
    """Scope downstream tool execution to a single organization ID."""

    clean_org_id = str(org_id or "").strip()
    if not clean_org_id:
        raise ValueError("active organization ID is required.")

    token = _ACTIVE_ORG_ID.set(clean_org_id)
    try:
        yield
    finally:
        _ACTIVE_ORG_ID.reset(token)


@contextmanager
def active_timezone_context(timezone_name: str) -> Iterator[None]:
    """Scope downstream SQL execution to a single IANA timezone."""

    clean_timezone = str(timezone_name or "").strip()
    if not clean_timezone:
        raise ValueError("active timezone is required.")
    try:
        ZoneInfo(clean_timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid IANA timezone: {clean_timezone}") from exc

    token = _ACTIVE_TIMEZONE_NAME.set(clean_timezone)
    try:
        yield
    finally:
        _ACTIVE_TIMEZONE_NAME.reset(token)
