"""Structured Lead 360 context tool.

This module intentionally uses small, scoped read-only queries instead of a
single row-multiplying join. The public ``get_lead_360`` function is kept as a
plain Python function for tests and backend callers; ``get_lead_360_tool`` is
the LangChain tool wrapper registered with the agent.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import partial
from typing import Any, Optional

from langchain.tools import tool

from app.config import get_sql_agent_settings
from app.db import get_db


LOGGER = logging.getLogger(__name__)

DEFAULT_RESOLVER_LIMIT = 20
MAX_LIMIT = 100
LONG_TEXT_LIMIT = 2_000
LEAD_360_FETCH_WORKERS = 15
DEFAULT_FULL_CALL_SUMMARIES = 2
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^)]+\)")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
INTERNAL_FIELD_NAMES = {
    "lead_id",
    "opt_in_id",
    "appointment_id",
    "contract_id",
    "payment_id",
    "payment_link_id",
    "payment_proof_id",
    "fathom_record_id",
    "invoice_id",
    "refund_id",
    "subscription_id",
    "subscription_checkout_link_id",
    "assigned_to",
    "host_id",
    "closer_id",
    "setter_id",
    "created_by",
    "uploaded_by",
    "outcome_applied_by",
}
URL_FIELD_NAMES = {
    "meeting_url",
    "recording_url",
    "transcript_url",
    "payment_url",
    "checkout_url",
    "url",
}

DISPLAY_NAME_SQL = """COALESCE(
  NULLIF(TRIM(l.full_name), ''),
  NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
  l.first_name,
  'Unknown Lead'
)"""

JOURNEY_LIMITATIONS = [
    "No page-view table is available in the current schema.",
    "No webinar attendance table is available in the current schema.",
    "No email/SMS interaction table is available in the current schema.",
]
CLEAN_JOURNEY_LIMITATIONS = [
    "No page-view history is available",
    "No webinar attendance history is available",
    "No full email/SMS interaction history is available",
]


def _clean_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clamp_limit(value: Optional[int], default: int) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(parsed, MAX_LIMIT))


def _record_timing(
    timings: Optional[list[dict[str, Any]]],
    *,
    section: str,
    subsection: str,
    started_at: float,
    status: str = "ok",
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    event = {
        "section": section,
        "subsection": subsection,
        "duration_seconds": round(max(0.0, time.perf_counter() - started_at), 4),
        "status": status,
    }
    if details:
        event["details"] = details
    if timings is not None:
        timings.append(event)
    return event


def _diagnostic_payload(
    timings: list[dict[str, Any]],
    *,
    started_at: float,
) -> dict[str, Any]:
    total_seconds = round(max(0.0, time.perf_counter() - started_at), 4)
    section_query_timings = [
        item
        for item in timings
        if item.get("section") == "section_queries"
        and item.get("subsection") != "parallel_wall_time"
    ]
    slowest_query = max(
        section_query_timings,
        key=lambda item: float(item.get("duration_seconds") or 0),
        default=None,
    )
    return {
        "timings": {
            "total_seconds": total_seconds,
            "worker_count": LEAD_360_FETCH_WORKERS,
            "slowest_query": slowest_query,
            "events": timings,
        }
    }


def _attach_diagnostics(
    payload: dict[str, Any],
    timings: list[dict[str, Any]],
    *,
    started_at: float,
) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["_diagnostics"] = _diagnostic_payload(timings, started_at=started_at)
    return enriched


def _escape_like(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return False


def _serialize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(item) for item in value]
    if _is_missing(value):
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value

    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        try:
            serialized = isoformat()
            return None if serialized == "NaT" else serialized
        except (TypeError, ValueError):
            pass

    return str(value)


def _json_ready(payload: dict[str, Any]) -> dict[str, Any]:
    return _serialize_value(payload)


def _truncate_text(value: Any, max_length: int = LONG_TEXT_LIMIT) -> Any:
    if isinstance(value, str) and len(value) > max_length:
        return f"{value[:max_length].rstrip()}..."
    if isinstance(value, list):
        return [_truncate_text(item, max_length=max_length) for item in value[:MAX_LIMIT]]
    if isinstance(value, dict):
        return {
            str(key): _truncate_text(item, max_length=max_length)
            for key, item in value.items()
        }
    return value


def _truncate_fields(records: list[dict[str, Any]], fields: set[str]) -> None:
    for record in records:
        for field in fields:
            if field in record:
                record[field] = _truncate_text(record[field])


def _strip_internal_fields(records: list[dict[str, Any]]) -> None:
    for record in records:
        for key in list(record):
            if key.startswith("_"):
                record.pop(key, None)


def normalize_currency_code(currency: Any) -> str:
    """Return a normalized uppercase ISO-ish currency code."""

    code = str(currency or "").strip().upper()
    return code or "UNKNOWN"


def _decimal_or_none(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def format_money_minor(amount_minor: Any, currency: Any) -> dict[str, Any]:
    """Represent minor-unit money safely for LLM consumption."""

    currency_code = normalize_currency_code(currency)
    minor_decimal = _decimal_or_none(amount_minor) or Decimal("0")
    major_decimal = minor_decimal / Decimal("100")
    if minor_decimal == minor_decimal.to_integral_value():
        minor_value = int(minor_decimal)
    else:
        minor_value = float(minor_decimal)

    major_value = float(major_decimal)
    formatted_number = f"{major_value:,.2f}"
    symbol = {"EUR": "€", "USD": "$", "GBP": "£"}.get(currency_code)
    display = f"{symbol}{formatted_number}" if symbol else f"{currency_code} {formatted_number}"

    return {
        "amount_minor": minor_value,
        "amount_major": major_value,
        "amount_display": display,
        "currency": currency_code,
    }


def strip_markdown_links(text: str) -> str:
    """Remove markdown link targets while preserving visible text."""

    return MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)


def strip_urls(text: str) -> str:
    """Remove raw URLs from text."""

    return URL_RE.sub("", text)


def _clean_markdown_text(text: Any) -> str:
    if not text:
        return ""
    cleaned = strip_urls(strip_markdown_links(str(text)))
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"[*_`~]{2,}", "", cleaned)
    cleaned = re.sub(r"\[(?:Fathom|fathom)[^\]]*\]", "", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _clean_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = [value]

    cleaned_items: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text") or item.get("title") or item.get("summary") or json.dumps(item)
        else:
            text = item
        cleaned = _clean_markdown_text(text)
        if cleaned:
            cleaned_items.append(_truncate_text(cleaned, max_length=500))
    return cleaned_items[:MAX_LIMIT]


def clean_fathom_markdown_summary(summary: Optional[str]) -> dict[str, Any]:
    """Return cleaned, link-free Fathom summary content."""

    cleaned = _clean_markdown_text(summary)
    if not cleaned:
        return {"summary_text": ""}

    sections: dict[str, list[str]] = {"topics": []}
    current_section: Optional[str] = None

    for raw_line in cleaned.splitlines():
        line = raw_line.strip().strip("-•").strip()
        if not line:
            continue

        heading = line.lower().rstrip(":")
        if any(token in heading for token in ("purpose", "goal", "objective")):
            current_section = None
            continue
        if any(token in heading for token in ("takeaway", "key point", "summary")):
            current_section = None
            continue
        if any(token in heading for token in ("topic", "discussed")):
            current_section = "topics"
            continue
        if any(token in heading for token in ("next step", "action item", "follow up")):
            current_section = None
            continue

        if current_section:
            sections[current_section].append(line)

    result = {
        "summary_text": cleaned,
    }
    if sections["topics"]:
        result["topics"] = _unique_present(sections["topics"])[:10]
    return result


def _is_uuid_like(value: Any) -> bool:
    return isinstance(value, str) and UUID_RE.match(value.strip()) is not None


def remove_nulls_and_empty_values(
    obj: Any,
    *,
    allow_urls: bool = False,
    current_key: str = "",
) -> Any:
    """Recursively remove nulls and empty collections from LLM context."""

    if isinstance(obj, dict):
        cleaned: dict[str, Any] = {}
        for key, value in obj.items():
            if key in INTERNAL_FIELD_NAMES or key.endswith("_id"):
                continue
            item = remove_nulls_and_empty_values(
                value,
                allow_urls=allow_urls,
                current_key=key,
            )
            if item is None or item == {} or item == []:
                continue
            cleaned[key] = item
        return cleaned
    if isinstance(obj, list):
        cleaned_items = [
            remove_nulls_and_empty_values(
                item,
                allow_urls=allow_urls,
                current_key=current_key,
            )
            for item in obj
        ]
        return [item for item in cleaned_items if item is not None and item != {} and item != []]
    if isinstance(obj, str):
        if allow_urls and current_key in URL_FIELD_NAMES:
            cleaned_text = obj.strip()
        else:
            cleaned_text = strip_urls(obj).strip()
        if not cleaned_text or _is_uuid_like(cleaned_text):
            return None
        return cleaned_text
    if obj is None:
        return None
    return obj


def sanitize_for_llm(obj: dict[str, Any], *, allow_urls: bool = False) -> dict[str, Any]:
    """Final safety pass for normal Lead 360 output."""

    return remove_nulls_and_empty_values(_json_ready(obj), allow_urls=allow_urls)


def _query_records(
    db: Any,
    sql: str,
    params: dict[str, Any],
    *,
    limit: Optional[int] = None,
) -> list[dict[str, Any]]:
    if limit == 0:
        return []
    return db.query_records(sql, params=params, max_rows=limit)


def _not_found_response() -> dict[str, Any]:
    return {
        "status": "not_found",
        "message": "No matching lead found.",
        "matches": [],
        "lead_360": None,
    }


def _multiple_matches_response(matches: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "multiple_matches",
        "message": "Multiple matching leads found. Please choose one.",
        "matches": matches,
        "lead_360": None,
    }


def _safe_error_response(message: str, error: str) -> dict[str, Any]:
    return {
        "status": "error",
        "message": message,
        "error": error,
        "matches": [],
        "lead_360": None,
    }


def _resolver_select(include_contact_details: bool) -> str:
    contact_fields = ""
    if include_contact_details:
        contact_fields = """
  l.email AS email,
  l.phone_e164 AS phone_e164,"""

    return f"""
SELECT
  l.id::text AS lead_id,
  {DISPLAY_NAME_SQL} AS display_name,
  ss.name AS status_name,
  ss.role::text AS status_role,
  l.source::text AS lead_source,{contact_fields}
  l.created_at AS created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
"""


def _resolve_lead(
    db: Any,
    *,
    org_id: str,
    lead_id: Optional[str],
    lead_name: Optional[str],
    lead_email: Optional[str],
    lead_phone: Optional[str],
    include_contact_details: bool,
) -> list[dict[str, Any]]:
    sql_base = _resolver_select(include_contact_details)
    params: dict[str, Any] = {"org_id": org_id, "limit": DEFAULT_RESOLVER_LIMIT}

    if lead_id:
        if not _is_uuid_like(lead_id):
            return []
        params["lead_id"] = lead_id
        where_clause = """
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.id = CAST(:lead_id AS uuid)
ORDER BY l.created_at DESC
LIMIT :limit
"""
    elif lead_email:
        params["lead_email"] = lead_email
        where_clause = """
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND LOWER(TRIM(l.email)) = LOWER(TRIM(:lead_email))
ORDER BY l.created_at DESC
LIMIT :limit
"""
    elif lead_phone:
        params["lead_phone"] = lead_phone
        where_clause = """
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.phone_e164 = :lead_phone
ORDER BY l.created_at DESC
LIMIT :limit
"""
    elif lead_name:
        params["lead_name_pattern"] = f"%{_escape_like(lead_name)}%"
        where_clause = """
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND (
    l.full_name ILIKE :lead_name_pattern ESCAPE '\\'
    OR l.first_name ILIKE :lead_name_pattern ESCAPE '\\'
    OR l.last_name ILIKE :lead_name_pattern ESCAPE '\\'
    OR CONCAT_WS(' ', l.first_name, l.last_name) ILIKE :lead_name_pattern ESCAPE '\\'
  )
ORDER BY l.created_at DESC
LIMIT :limit
"""
    else:
        return []

    return _query_records(
        db,
        f"{sql_base}{where_clause}",
        params,
        limit=DEFAULT_RESOLVER_LIMIT,
    )


def _fetch_lead_profile(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    include_contact_details: bool,
) -> dict[str, Any]:
    contact_select = (
        "l.email AS email,\n  l.phone_e164 AS phone_e164"
        if include_contact_details
        else "NULL::text AS email,\n  NULL::text AS phone_e164"
    )
    rows = _query_records(
        db,
        f"""
SELECT
  l.id::text AS lead_id,
  {DISPLAY_NAME_SQL} AS display_name,
  {contact_select},
  ss.name AS status_name,
  ss.role::text AS status_role,
  l.source::text AS lead_source,
  l.assigned_to AS assigned_to,
  l.setter_id AS setter_id,
  l.next_touch_point_at AS next_touch_point_at,
  l.next_touch_point_type::text AS next_touch_point_type,
  l.created_at AS created_at,
  l.updated_at AS updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.id = CAST(:lead_id AS uuid)
LIMIT 1
""",
        {"org_id": org_id, "lead_id": lead_id},
        limit=1,
    )
    return rows[0] if rows else {}


def _fetch_source_context(db: Any, *, org_id: str, lead_id: str) -> dict[str, Any]:
    rows = _query_records(
        db,
        """
SELECT
  l.source::text AS lead_source,
  COALESCE(first_ms.name, NULLIF(TRIM(l.first_source_name), ''), 'Unknown') AS first_source,
  l.first_source_name AS first_source_name_raw,
  COALESCE(last_ms.name, NULLIF(TRIM(l.last_source_name), ''), 'Unknown') AS last_source,
  l.last_source_name AS last_source_name_raw,
  l.ai_source_summary AS ai_source_summary
FROM leads l
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.id = CAST(:lead_id AS uuid)
LIMIT 1
""",
        {"org_id": org_id, "lead_id": lead_id},
        limit=1,
    )
    if not rows:
        return {}
    row = rows[0]
    row["ai_source_summary"] = _truncate_text(row.get("ai_source_summary"))
    return row


def _fetch_acquisition(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    return _query_records(
        db,
        """
SELECT
  o.id::text AS opt_in_id,
  o.created_at AS created_at,
  o.source::text AS opt_in_source,
  o.provider_form_name AS provider_form_name,
  ta.utm_source AS utm_source,
  ta.utm_medium AS utm_medium,
  ta.utm_campaign AS utm_campaign,
  ta.utm_content AS utm_content,
  ta.utm_term AS utm_term,
  ta.landing_page AS landing_page,
  ta.referrer AS referrer
FROM opt_ins o
LEFT JOIN traffic_attributions ta
  ON ta.opt_in_id = o.id
WHERE o.clerk_org_id = :org_id
  AND o.lead_id = CAST(:lead_id AS uuid)
ORDER BY o.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )


def _fetch_form_answers(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = _query_records(
        db,
        """
SELECT
  o.created_at AS opt_in_created_at,
  o.provider_form_name AS provider_form_name,
  q.position AS position,
  q.question AS question,
  q.answer AS answer
FROM opt_ins o
JOIN opt_in_question_answers q
  ON q.opt_in_id = o.id
WHERE o.clerk_org_id = :org_id
  AND o.lead_id = CAST(:lead_id AS uuid)
ORDER BY o.created_at DESC, q.position ASC, q.id ASC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"question", "answer"})
    return rows


def _fetch_appointments(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    include_links: bool,
    limit: int,
) -> list[dict[str, Any]]:
    link_select = (
        "a.meeting_url AS meeting_url,\n  a.recording_url AS recording_url"
        if include_links
        else "NULL::text AS meeting_url,\n  NULL::text AS recording_url"
    )
    return _query_records(
        db,
        f"""
SELECT
  a.id::text AS appointment_id,
  a.created_at AS _created_at,
  a.schedule_time AS schedule_time,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name) AS event_name,
  COALESCE(a.snapshot_call_category::text, aet.call_category::text) AS call_category,
  ss.name AS outcome_name,
  ss.role::text AS outcome_role,
  a.no_show AS no_show,
  a.source::text AS appointment_source,
  a.host_id AS host_id,
  a.setter_id AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f
    WHERE f.appointment_id = a.id
      AND f.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record,
  {link_select}
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
LEFT JOIN sales_statuses ss
  ON ss.id = a.outcome_id
 AND ss.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.lead_id = CAST(:lead_id AS uuid)
  AND a.is_deleted = false
ORDER BY a.schedule_time DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )


def _fetch_fathom_calls(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    include_links: bool,
    limit: int,
    full_summary_limit: int,
) -> list[dict[str, Any]]:
    link_select = (
        "f.recording_url AS recording_url,\n  f.transcript_url AS transcript_url"
        if include_links
        else "NULL::text AS recording_url,\n  NULL::text AS transcript_url"
    )
    rows = _query_records(
        db,
        f"""
SELECT
  f.id::text AS fathom_record_id,
  a.id::text AS appointment_id,
  a.schedule_time AS schedule_time,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name) AS event_name,
  f.call_started_at AS call_started_at,
  f.call_ended_at AS call_ended_at,
  f.call_duration_seconds AS call_duration_seconds,
  CASE
    WHEN ROW_NUMBER() OVER (ORDER BY COALESCE(f.call_started_at, a.schedule_time) DESC)
      <= :full_summary_limit
    THEN f.summary
    ELSE NULL
  END AS summary,
  f.ai_confidence_score AS ai_confidence_score,
  f.outcome_applied AS outcome_applied,
  (f.recording_url IS NOT NULL AND TRIM(f.recording_url) <> '') AS has_recording_url,
  (f.transcript_url IS NOT NULL AND TRIM(f.transcript_url) <> '') AS has_transcript_url,
  {link_select}
FROM appointments a
JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.lead_id = CAST(:lead_id AS uuid)
  AND a.is_deleted = false
ORDER BY COALESCE(f.call_started_at, a.schedule_time) DESC
LIMIT :limit
""",
        {
            "org_id": org_id,
            "lead_id": lead_id,
            "limit": limit,
            "full_summary_limit": full_summary_limit,
        },
        limit=limit,
    )
    return rows


def _fetch_notes(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = _query_records(
        db,
        """
SELECT
  ln.id::text AS note_id,
  ln.appointment_id::text AS appointment_id,
  ln.created_at AS created_at,
  ln.note AS note
FROM lead_notes ln
WHERE ln.clerk_org_id = :org_id
  AND ln.lead_id = CAST(:lead_id AS uuid)
  AND ln.is_deleted = false
ORDER BY ln.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"note"})
    return rows


def _fetch_contracts(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = _query_records(
        db,
        """
SELECT
  c.id::text AS contract_id,
  c.created_at AS created_at,
  pr.name AS program_name,
  c.type::text AS contract_type,
  c.status::text AS contract_status,
  c.total_value AS total_value,
  c.currency AS currency,
  c.closer_id AS closer_id,
  c.setter_id AS setter_id,
  c.sent_at AS sent_at,
  c.signed_at AS signed_at,
  c.voided_at AS voided_at,
  c.voided_reason AS voided_reason
FROM contracts c
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND c.lead_id = CAST(:lead_id AS uuid)
  AND c.is_deleted = false
ORDER BY c.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"voided_reason"})
    return rows


def _fetch_payments_summary(db: Any, *, org_id: str, lead_id: str) -> list[dict[str, Any]]:
    return _query_records(
        db,
        """
SELECT
  p.currency AS currency,
  COUNT(*)::int AS payment_count,
  COUNT(*) FILTER (WHERE p.status::text = 'PAID')::int AS paid_payment_count,
  COUNT(*) FILTER (WHERE p.status::text IN ('PENDING', 'FAILED'))::int
    AS outstanding_payment_count,
  COUNT(*) FILTER (
    WHERE p.status::text IN ('PENDING', 'FAILED')
      AND p.due_date IS NOT NULL
      AND p.due_date < NOW()
  )::int AS overdue_payment_count,
  COALESCE(SUM(CASE WHEN p.status::text = 'PAID' THEN p.amount ELSE 0::numeric END), 0)::numeric(12, 2)
    AS paid_amount,
  COALESCE(SUM(CASE WHEN p.status::text IN ('PENDING', 'FAILED') THEN p.amount ELSE 0::numeric END), 0)::numeric(12, 2)
    AS outstanding_amount,
  COALESCE(SUM(CASE WHEN p.status::text IN ('PENDING', 'FAILED') AND p.due_date IS NOT NULL AND p.due_date < NOW() THEN p.amount ELSE 0::numeric END), 0)::numeric(12, 2)
    AS overdue_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.lead_id = CAST(:lead_id AS uuid)
  AND p.is_deleted = false
GROUP BY p.currency
ORDER BY p.currency
""",
        {"org_id": org_id, "lead_id": lead_id},
        limit=MAX_LIMIT,
    )


def _fetch_payments(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = _query_records(
        db,
        """
SELECT
  p.id::text AS payment_id,
  p.contract_id::text AS contract_id,
  p.subscription_id::text AS subscription_id,
  p.created_at AS created_at,
  p.updated_at AS _updated_at,
  p.type::text AS payment_type,
  p.status::text AS payment_status,
  p.payment_provider::text AS payment_provider,
  p.amount AS amount,
  p.currency AS currency,
  p.due_date AS due_date,
  p.paid_at AS paid_at,
  p.note AS note,
  p.failure_reason AS failure_reason
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.lead_id = CAST(:lead_id AS uuid)
  AND p.is_deleted = false
ORDER BY p.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"note", "failure_reason"})
    return rows


def _fetch_payment_links(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    include_links: bool,
    limit: int,
) -> list[dict[str, Any]]:
    url_select = "pl.url AS url" if include_links else "NULL::text AS url"
    rows = _query_records(
        db,
        f"""
SELECT
  pl.id::text AS payment_link_id,
  pl.payment_id::text AS payment_id,
  pl.created_at AS created_at,
  pl.status::text AS payment_link_status,
  pl.provider_invalidation_status::text AS provider_invalidation_status,
  pl.note AS note,
  {url_select}
FROM payments p
JOIN payment_links pl
  ON pl.payment_id = p.id
WHERE p.clerk_org_id = :org_id
  AND p.lead_id = CAST(:lead_id AS uuid)
  AND p.is_deleted = false
  AND pl.is_deleted = false
ORDER BY pl.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"note"})
    return rows


def _fetch_payment_proofs(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    return _query_records(
        db,
        """
SELECT
  pp.id::text AS payment_proof_id,
  pp.payment_id::text AS payment_id,
  pp.created_at AS created_at,
  pp.file_name AS file_name,
  pp.mime_type AS mime_type,
  pp.file_size_bytes AS file_size_bytes,
  pp.uploaded_by AS uploaded_by
FROM payments p
JOIN payment_proofs pp
  ON pp.payment_id = p.id
 AND pp.clerk_org_id = p.clerk_org_id
WHERE p.clerk_org_id = :org_id
  AND p.lead_id = CAST(:lead_id AS uuid)
  AND p.is_deleted = false
  AND pp.clerk_org_id = :org_id
  AND pp.is_deleted = false
ORDER BY pp.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )


def _fetch_refunds(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = _query_records(
        db,
        """
SELECT
  r.id::text AS refund_id,
  r.payment_id::text AS payment_id,
  r.created_at AS created_at,
  r.refunded_at AS refunded_at,
  r.status::text AS refund_status,
  r.amount AS amount,
  r.currency AS currency,
  r.payment_provider::text AS payment_provider,
  r.reason AS reason,
  r.failure_reason AS failure_reason
FROM refunds r
JOIN payments p
  ON p.id = r.payment_id
 AND p.clerk_org_id = r.clerk_org_id
WHERE r.clerk_org_id = :org_id
  AND p.clerk_org_id = :org_id
  AND p.lead_id = CAST(:lead_id AS uuid)
  AND p.is_deleted = false
ORDER BY COALESCE(r.refunded_at, r.created_at) DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"reason", "failure_reason"})
    return rows


def _fetch_invoices(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    return _query_records(
        db,
        """
SELECT
  i.id::text AS invoice_id,
  i.contract_id::text AS contract_id,
  i.payment_id::text AS payment_id,
  i.created_at AS created_at,
  i.issued_at AS issued_at,
  i.paid_at AS paid_at,
  i.invoice_number AS invoice_number,
  i.status::text AS invoice_status,
  i.amount AS amount,
  i.currency AS currency
FROM invoices i
WHERE i.clerk_org_id = :org_id
  AND i.to_client_id = CAST(:lead_id AS uuid)
ORDER BY i.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )


def _fetch_subscriptions(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = _query_records(
        db,
        """
SELECT
  cs.id::text AS subscription_id,
  c.id::text AS contract_id,
  COALESCE(cs.started_at, c.created_at) AS created_at,
  pr.name AS program_name,
  cs.status::text AS subscription_status,
  cs.payment_provider::text AS payment_provider,
  cs.amount_per_cycle AS amount_per_cycle,
  cs.billing_interval::text AS billing_interval,
  cs.currency AS currency,
  cs.billing_cycles_paid AS billing_cycles_paid,
  cs.total_collected AS total_collected,
  cs.next_billing_date AS next_billing_date,
  cs.started_at AS started_at,
  cs.cancel_at_period_end AS cancel_at_period_end,
  cs.cancelled_at AS cancelled_at,
  cs.cancellation_reason AS cancellation_reason
FROM contracts c
JOIN contract_subscriptions cs
  ON cs.contract_id = c.id
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND c.lead_id = CAST(:lead_id AS uuid)
  AND c.is_deleted = false
  AND cs.is_deleted = false
ORDER BY COALESCE(cs.started_at, c.created_at) DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"cancellation_reason"})
    return rows


def _fetch_subscription_checkout_links(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    include_links: bool,
    limit: int,
) -> list[dict[str, Any]]:
    url_select = "scl.url AS url" if include_links else "NULL::text AS url"
    rows = _query_records(
        db,
        f"""
SELECT
  scl.id::text AS subscription_checkout_link_id,
  scl.subscription_id::text AS subscription_id,
  scl.created_at AS created_at,
  scl.status::text AS checkout_link_status,
  scl.provider_invalidation_status::text AS provider_invalidation_status,
  scl.note AS note,
  {url_select}
FROM contracts c
JOIN contract_subscriptions cs
  ON cs.contract_id = c.id
JOIN subscription_checkout_links scl
  ON scl.subscription_id = cs.id
WHERE c.clerk_org_id = :org_id
  AND c.lead_id = CAST(:lead_id AS uuid)
  AND c.is_deleted = false
  AND cs.is_deleted = false
  AND scl.is_deleted = false
ORDER BY scl.created_at DESC
LIMIT :limit
""",
        {"org_id": org_id, "lead_id": lead_id, "limit": limit},
        limit=limit,
    )
    _truncate_fields(rows, {"note"})
    return rows


def _normalize_evidence(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _unique_present(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value:
            continue
        text = str(value).strip()
        if not text or text.lower() == "unknown":
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _evidence_fields_for_keywords(
    field_values: dict[str, list[Any]],
    keywords: set[str],
) -> list[str]:
    evidence: list[str] = []
    for field_name, values in field_values.items():
        for value in values:
            normalized = _normalize_evidence(value)
            if any(keyword in normalized for keyword in keywords):
                evidence.append(field_name)
                break
    return _unique_present(evidence)


def _build_journey_evidence(
    *,
    source_context: dict[str, Any],
    acquisition: list[dict[str, Any]],
    form_answers: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    fathom_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    utm_sources = _unique_present([row.get("utm_source") for row in acquisition])
    utm_campaigns = _unique_present([row.get("utm_campaign") for row in acquisition])
    landing_pages = _unique_present([row.get("landing_page") for row in acquisition])
    referrers = _unique_present([row.get("referrer") for row in acquisition])
    provider_forms = _unique_present([row.get("provider_form_name") for row in acquisition])
    opt_in_sources = _unique_present([row.get("opt_in_source") for row in acquisition])

    available_source_fields = {
        "lead_source": source_context.get("lead_source"),
        "first_source": source_context.get("first_source"),
        "last_source": source_context.get("last_source"),
        "ai_source_summary": source_context.get("ai_source_summary"),
        "opt_in_sources": opt_in_sources,
        "utm_sources": utm_sources,
        "utm_campaigns": utm_campaigns,
        "landing_pages": landing_pages,
        "referrers": referrers,
        "provider_forms": provider_forms,
    }

    field_values = {
        "lead_source": [source_context.get("lead_source")],
        "first_source": [source_context.get("first_source"), source_context.get("first_source_name_raw")],
        "last_source": [source_context.get("last_source"), source_context.get("last_source_name_raw")],
        "ai_source_summary": [source_context.get("ai_source_summary")],
        "opt_in_source": opt_in_sources,
        "provider_form_name": provider_forms,
        "utm_source": utm_sources,
        "utm_medium": [row.get("utm_medium") for row in acquisition],
        "utm_campaign": utm_campaigns,
        "utm_content": [row.get("utm_content") for row in acquisition],
        "landing_page": landing_pages,
        "referrer": referrers,
        "form_answers": [row.get("question") for row in form_answers] + [row.get("answer") for row in form_answers],
        "notes": [row.get("note") for row in notes],
        "fathom_summary": [row.get("summary") for row in fathom_calls],
    }

    facebook_evidence = _evidence_fields_for_keywords(
        field_values,
        {"facebook", "fb", "meta"},
    )
    youtube_evidence = _evidence_fields_for_keywords(
        field_values,
        {"youtube", "youtu", "yt"},
    )
    webinar_evidence = _evidence_fields_for_keywords(
        field_values,
        {"webinar"},
    )
    email_evidence = _evidence_fields_for_keywords(
        field_values,
        {"email", "newsletter"},
    )
    text_evidence = _evidence_fields_for_keywords(
        field_values,
        {"sms", "text", "whatsapp"},
    )

    def evidence_status(evidence: list[str], *, unknown_when_missing: bool = False) -> dict[str, Any]:
        if evidence:
            return {"status": "evidence_found", "evidence": evidence}
        if unknown_when_missing:
            return {"status": "unknown", "evidence": []}
        return {"status": "no_evidence_found", "evidence": []}

    return {
        "available_source_fields": available_source_fields,
        "interaction_signals": {
            "facebook_ads": evidence_status(facebook_evidence),
            "youtube": evidence_status(youtube_evidence),
            "webinar": evidence_status(webinar_evidence),
            "email": evidence_status(email_evidence, unknown_when_missing=True),
            "text_message": evidence_status(text_evidence, unknown_when_missing=True),
            "pages_visited": {
                "status": "limited_to_landing_page_and_referrer",
                "evidence": [
                    evidence
                    for evidence, values in (
                        ("landing_page", landing_pages),
                        ("referrer", referrers),
                    )
                    if values
                ],
            },
        },
        "limitations": JOURNEY_LIMITATIONS,
    }


def _as_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _event_time(value: Any) -> Optional[str]:
    parsed = _as_datetime(value)
    return parsed.isoformat() if parsed else None


def _format_money(amount: Any, currency: Any) -> str:
    if amount is None:
        return "unknown amount"
    return format_money_minor(amount, currency)["amount_display"]


def _add_event(
    events: list[dict[str, Any]],
    event_time: Any,
    event_type: str,
    title: str,
    summary: str,
) -> None:
    serialized_time = _event_time(event_time)
    if not serialized_time:
        return
    events.append(
        {
            "event_time": serialized_time,
            "event_type": event_type,
            "title": title,
            "summary": summary,
        }
    )


def _build_timeline(
    *,
    lead_profile: dict[str, Any],
    acquisition: list[dict[str, Any]],
    appointments: list[dict[str, Any]],
    fathom_calls: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    payment_links: list[dict[str, Any]],
    payment_proofs: list[dict[str, Any]],
    refunds: list[dict[str, Any]],
    invoices: list[dict[str, Any]],
    subscriptions: list[dict[str, Any]],
    subscription_checkout_links: list[dict[str, Any]],
    max_events: int,
) -> list[dict[str, Any]]:
    if max_events == 0:
        return []

    events: list[dict[str, Any]] = []
    display_name = lead_profile.get("display_name") or "Lead"

    _add_event(
        events,
        lead_profile.get("created_at"),
        "lead_created",
        "Lead created",
        f"{display_name} was created.",
    )
    _add_event(
        events,
        lead_profile.get("next_touch_point_at"),
        "next_touch_point",
        "Next touch point",
        f"Next touch point is {lead_profile.get('next_touch_point_type') or 'scheduled'}.",
    )

    for row in acquisition:
        source = row.get("provider_form_name") or row.get("opt_in_source") or "an opt-in"
        _add_event(
            events,
            row.get("created_at"),
            "opt_in_submitted",
            "Opt-in submitted",
            f"Lead submitted {source}.",
        )

    now = datetime.now(timezone.utc)
    for row in appointments:
        schedule_time = _as_datetime(row.get("schedule_time"))
        event_name = row.get("event_name") or "appointment"
        _add_event(
            events,
            row.get("_created_at") or row.get("schedule_time"),
            "appointment_scheduled",
            "Appointment scheduled",
            f"{event_name} was scheduled.",
        )
        if _appointment_is_canceled(row):
            event_type = "appointment_canceled"
            title = "Appointment canceled"
            summary = f"{event_name} was marked Canceled."
        elif row.get("no_show"):
            event_type = "appointment_no_show"
            title = "Appointment no-show"
            summary = f"{event_name} was marked No Show."
        elif schedule_time and schedule_time.replace(tzinfo=schedule_time.tzinfo or timezone.utc) < now:
            event_type = "appointment_completed"
            title = "Appointment completed"
            summary = f"{event_name} took place."
        else:
            event_type = "appointment_scheduled"
            title = "Appointment scheduled"
            summary = f"{event_name} is scheduled."
        _add_event(events, row.get("schedule_time"), event_type, title, summary)

    for row in fathom_calls:
        event_name = row.get("event_name") or "appointment"
        _add_event(
            events,
            row.get("call_started_at") or row.get("schedule_time"),
            "fathom_call_started",
            "Fathom call started",
            f"Fathom recorded the {event_name}.",
        )

    for row in notes:
        _add_event(
            events,
            row.get("created_at"),
            "note_created",
            "Note created",
            "A lead note was added.",
        )

    for row in contracts:
        program = row.get("program_name") or "Program"
        amount = _format_money(row.get("total_value"), row.get("currency"))
        _add_event(
            events,
            row.get("created_at"),
            "contract_created",
            "Contract created",
            f"{program} contract was created for {amount}.",
        )
        _add_event(
            events,
            row.get("sent_at"),
            "contract_sent",
            "Contract sent",
            f"{program} contract was sent for {amount}.",
        )
        _add_event(
            events,
            row.get("signed_at"),
            "contract_signed",
            "Contract signed",
            f"{program} contract was signed.",
        )
        _add_event(
            events,
            row.get("voided_at"),
            "contract_voided",
            "Contract voided",
            f"{program} contract was voided.",
        )

    for row in payments:
        amount = _format_money(row.get("amount"), row.get("currency"))
        payment_type = _readable_enum(row.get("payment_type")) or "Payment"
        if row.get("payment_status") == "PAID":
            _add_event(
                events,
                row.get("paid_at") or row.get("created_at"),
                "payment_paid",
                "Payment paid",
                f"{payment_type} payment of {amount} was paid.",
            )
        elif _payment_is_overdue(row, now=now):
            _add_event(
                events,
                row.get("due_date"),
                "payment_overdue",
                "Payment overdue",
                f"{payment_type} payment of {amount} is overdue.",
            )
        elif row.get("payment_status") == "FAILED":
            _add_event(
                events,
                row.get("_updated_at") or row.get("created_at"),
                "payment_failed",
                "Payment marked failed",
                f"{payment_type} payment of {amount} was marked failed.",
            )
        else:
            _add_event(
                events,
                row.get("due_date") or row.get("created_at"),
                "payment_due",
                "Payment due",
                f"{payment_type} payment of {amount} is due.",
            )

    for row in payment_links:
        _add_event(
            events,
            row.get("created_at"),
            "payment_link_created",
            "Payment link created",
            "A payment link was created.",
        )

    for row in payment_proofs:
        _add_event(
            events,
            row.get("created_at"),
            "payment_proof_uploaded",
            "Payment proof uploaded",
            "A payment proof was uploaded.",
        )

    for row in refunds:
        amount = _format_money(row.get("amount"), row.get("currency"))
        _add_event(
            events,
            row.get("created_at"),
            "refund_initiated",
            "Refund initiated",
            f"Refund was initiated for {amount}.",
        )
        if row.get("refund_status") == "SUCCEEDED":
            _add_event(
                events,
                row.get("refunded_at") or row.get("created_at"),
                "refund_succeeded",
                "Refund succeeded",
                f"Refund succeeded for {amount}.",
            )

    for row in invoices:
        amount = _format_money(row.get("amount"), row.get("currency"))
        _add_event(
            events,
            row.get("issued_at") or row.get("created_at"),
            "invoice_issued",
            "Invoice issued",
            f"Invoice {row.get('invoice_number') or ''} was issued for {amount}.".strip(),
        )
        _add_event(
            events,
            row.get("paid_at"),
            "invoice_paid",
            "Invoice paid",
            f"Invoice {row.get('invoice_number') or ''} was paid.".strip(),
        )

    for row in subscriptions:
        amount = _format_money(row.get("amount_per_cycle"), row.get("currency"))
        interval = row.get("billing_interval") or "cycle"
        _add_event(
            events,
            row.get("started_at") or row.get("created_at"),
            "subscription_started",
            "Subscription started",
            f"Subscription started at {amount} per {str(interval).lower()}.",
        )
        _add_event(
            events,
            row.get("next_billing_date"),
            "subscription_next_billing_date",
            "Subscription next billing date",
            f"Next subscription billing is scheduled for {amount}.",
        )
        if row.get("cancel_at_period_end"):
            _add_event(
                events,
                row.get("next_billing_date") or row.get("created_at"),
                "subscription_cancellation_scheduled",
                "Subscription cancellation scheduled",
                "Subscription is scheduled to cancel at period end.",
            )
        _add_event(
            events,
            row.get("cancelled_at"),
            "subscription_cancelled",
            "Subscription cancelled",
            "Subscription was cancelled.",
        )

    for row in subscription_checkout_links:
        _add_event(
            events,
            row.get("created_at"),
            "subscription_checkout_link_created",
            "Subscription checkout link created",
            "A subscription checkout link was created.",
        )

    deduped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for event in events:
        key = (
            event["event_time"],
            event["event_type"],
            event["title"],
            event["summary"],
        )
        deduped[key] = event

    recent = sorted(deduped.values(), key=lambda event: event["event_time"], reverse=True)[
        :max_events
    ]
    return sorted(recent, key=lambda event: event["event_time"])


def _source_evidence_level(
    source_context: dict[str, Any],
    acquisition: list[dict[str, Any]],
) -> str:
    source_values = _unique_present(
        [
            source_context.get("lead_source"),
            source_context.get("first_source"),
            source_context.get("last_source"),
            source_context.get("first_source_name_raw"),
            source_context.get("last_source_name_raw"),
        ]
    )
    acquisition_values = _unique_present(
        [row.get("utm_source") for row in acquisition]
        + [row.get("utm_campaign") for row in acquisition]
        + [row.get("referrer") for row in acquisition]
        + [row.get("landing_page") for row in acquisition]
        + [row.get("provider_form_name") for row in acquisition]
    )

    if not source_values and not acquisition_values:
        return "unknown"
    if len(source_values) >= 2 and acquisition_values:
        normalized_sources = {_normalize_evidence(value) for value in source_values}
        normalized_acquisition = {_normalize_evidence(value) for value in acquisition_values}
        has_overlap = any(
            source
            and acquisition
            and (source in acquisition or acquisition in source)
            for source in normalized_sources
            for acquisition in normalized_acquisition
        )
        if has_overlap:
            return "strong"
        return "partial"
    if source_values or acquisition_values:
        return "partial"
    return "weak"


def _build_data_quality(
    *,
    lead_profile: dict[str, Any],
    source_context: dict[str, Any],
    acquisition: list[dict[str, Any]],
    appointments: list[dict[str, Any]],
    fathom_calls: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    payment_links: list[dict[str, Any]],
    payment_proofs: list[dict[str, Any]],
    refunds: list[dict[str, Any]],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)

    def is_overdue(payment: dict[str, Any]) -> bool:
        due_date = _as_datetime(payment.get("due_date"))
        if not due_date:
            return False
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        return payment.get("payment_status") in {"PENDING", "FAILED"} and due_date < now

    first_source = source_context.get("first_source")
    last_source = source_context.get("last_source")

    return {
        "missing_source": not bool(lead_profile.get("lead_source")),
        "missing_first_source": not first_source or str(first_source).lower() == "unknown",
        "missing_last_source": not last_source or str(last_source).lower() == "unknown",
        "missing_next_touch_point": not bool(lead_profile.get("next_touch_point_at")),
        "has_no_appointments": not appointments,
        "has_no_fathom_calls": not fathom_calls,
        "has_no_notes": not notes,
        "has_no_contracts": not contracts,
        "has_no_payments": not payments,
        "has_pending_payment": any(
            payment.get("payment_status") == "PENDING" for payment in payments
        ),
        "has_overdue_payment": any(is_overdue(payment) for payment in payments),
        "has_failed_payment": any(payment.get("payment_status") == "FAILED" for payment in payments),
        "has_refund": bool(refunds),
        "has_no_show": any(bool(appointment.get("no_show")) for appointment in appointments),
        "has_unsigned_contract": any(
            contract.get("contract_status") not in {"SIGNED", "VOIDED"}
            for contract in contracts
        ),
        "has_unpaid_contract": bool(contracts)
        and (
            not payments
            or any(payment.get("payment_status") in {"PENDING", "FAILED"} for payment in payments)
        ),
        "has_payment_link": bool(payment_links),
        "has_payment_proof": bool(payment_proofs),
        "source_evidence_level": _source_evidence_level(source_context, acquisition),
        "unsupported_journey_questions": [
            "full page-view history is unavailable unless another table exists",
            "webinar attendance is unavailable unless another table exists",
            "email/SMS interaction history is unavailable unless another table exists",
        ],
    }


def _date_only(value: Any) -> Optional[str]:
    parsed = _as_datetime(value)
    return parsed.date().isoformat() if parsed else None


def _iso_or_none(value: Any) -> Any:
    return _serialize_value(value) if value is not None else None


def _readable_enum(value: Any) -> str:
    if not value:
        return ""
    return str(value).replace("_", " ").title()


def _availability_label(value: Any, present_label: str, missing_label: str) -> str:
    return present_label if value else missing_label


def _appointment_is_canceled(appointment: dict[str, Any]) -> bool:
    outcome_role = str(appointment.get("outcome_role") or "").upper()
    outcome_name = str(appointment.get("outcome_name") or "").lower()
    return outcome_role == "CANCELED" or "canceled" in outcome_name or "cancelled" in outcome_name


def _payment_is_overdue(payment: dict[str, Any], now: Optional[datetime] = None) -> bool:
    status = str(payment.get("payment_status") or "").upper()
    due_date = _as_datetime(payment.get("due_date"))
    if status not in {"PENDING", "FAILED"} or not due_date:
        return False
    effective_now = now or datetime.now(timezone.utc)
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)
    return due_date < effective_now


def _compact_matches(
    matches: list[dict[str, Any]],
    *,
    include_contact_details: bool,
) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for match in matches:
        item = {
            "display_name": match.get("display_name"),
            "status_name": match.get("status_name"),
            "status_role": match.get("status_role"),
            "lead_source": match.get("lead_source"),
            "created_at": match.get("created_at"),
        }
        if include_contact_details:
            item["email"] = match.get("email")
            item["phone_e164"] = match.get("phone_e164")
        compact.append(sanitize_for_llm(item))
    return compact


def compact_profile(
    lead_profile: dict[str, Any],
    *,
    include_contact_details: bool,
) -> dict[str, Any]:
    profile = {
        "display_name": lead_profile.get("display_name"),
        "created_at": lead_profile.get("created_at"),
        "updated_at": lead_profile.get("updated_at"),
        "status_name": lead_profile.get("status_name"),
        "status_role": lead_profile.get("status_role"),
        "lead_source": lead_profile.get("lead_source"),
        "next_touch_point_at": lead_profile.get("next_touch_point_at"),
        "next_touch_point_type": lead_profile.get("next_touch_point_type"),
        "assigned_owner": _availability_label(
            lead_profile.get("assigned_to"),
            "Assigned owner available",
            "No assigned owner",
        ),
        "setter": _availability_label(
            lead_profile.get("setter_id"),
            "Setter available",
            "No setter",
        ),
    }
    if include_contact_details:
        profile["email"] = lead_profile.get("email")
        profile["phone_e164"] = lead_profile.get("phone_e164")
    return sanitize_for_llm(profile)


def compact_acquisition(
    *,
    source_context: dict[str, Any],
    acquisition: list[dict[str, Any]],
    form_answers: list[dict[str, Any]],
    data_quality: dict[str, Any],
) -> dict[str, Any]:
    provider_forms = _unique_present([row.get("provider_form_name") for row in acquisition])
    utm_fields = [
        row.get(field)
        for row in acquisition
        for field in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")
    ]
    summary = {
        "lead_source": source_context.get("lead_source"),
        "first_source": source_context.get("first_source"),
        "last_source": source_context.get("last_source"),
        "ai_source_summary": source_context.get("ai_source_summary"),
        "opt_in_count": len(acquisition),
        "form_answer_count": len(form_answers),
        "provider_forms": provider_forms,
        "utm_available": any(bool(value) for value in utm_fields),
        "landing_page_available": any(bool(row.get("landing_page")) for row in acquisition),
        "referrer_available": any(bool(row.get("referrer")) for row in acquisition),
        "source_evidence_level": data_quality.get("source_evidence_level"),
    }
    return sanitize_for_llm(summary)


def compact_form_answers(form_answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return cleaned form answers with enough context for single-lead Q&A."""

    compact: list[dict[str, Any]] = []
    for answer in form_answers:
        compact.append(
            sanitize_for_llm(
                {
                    "created_at": answer.get("opt_in_created_at"),
                    "provider_form_name": _clean_markdown_text(
                        answer.get("provider_form_name")
                    ),
                    "question": _truncate_text(
                        _clean_markdown_text(answer.get("question")),
                        max_length=250,
                    ),
                    "answer": _truncate_text(
                        _clean_markdown_text(answer.get("answer")),
                        max_length=700,
                    ),
                }
            )
        )
    return [item for item in compact if item]


def compact_notes(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return cleaned notes without note IDs or user IDs."""

    compact: list[dict[str, Any]] = []
    for note in notes:
        compact.append(
            sanitize_for_llm(
                {
                    "created_at": note.get("created_at"),
                    "note": _truncate_text(
                        _clean_markdown_text(note.get("note")),
                        max_length=700,
                    ),
                }
            )
        )
    return [item for item in compact if item]


def _appointment_status_label(appointment: dict[str, Any]) -> str:
    if _appointment_is_canceled(appointment):
        return "canceled"
    if appointment.get("no_show"):
        return "no_show"

    schedule_time = _as_datetime(appointment.get("schedule_time"))
    if not schedule_time:
        return "scheduled"
    if schedule_time.tzinfo is None:
        schedule_time = schedule_time.replace(tzinfo=timezone.utc)
    if schedule_time > datetime.now(timezone.utc):
        return "upcoming"
    return "completed"


def compact_appointment_records(appointments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return cleaned appointment mini-records for detailed Q&A."""

    compact: list[dict[str, Any]] = []
    for appointment in appointments:
        compact.append(
            sanitize_for_llm(
                {
                    "date": _date_only(appointment.get("schedule_time")),
                    "schedule_time": appointment.get("schedule_time"),
                    "event_name": _clean_markdown_text(appointment.get("event_name")),
                    "call_category": appointment.get("call_category"),
                    "outcome": _clean_markdown_text(appointment.get("outcome_name")),
                    "outcome_role": appointment.get("outcome_role"),
                    "no_show": bool(appointment.get("no_show")),
                    "appointment_source": appointment.get("appointment_source"),
                    "has_fathom_record": bool(appointment.get("has_fathom_record")),
                    "status_label": _appointment_status_label(appointment),
                }
            )
        )
    return [item for item in compact if item]


def compact_appointments(appointments: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    total = len(appointments)
    canceled = sum(1 for appointment in appointments if _appointment_is_canceled(appointment))
    no_show = sum(1 for appointment in appointments if appointment.get("no_show"))
    completed = 0
    for appointment in appointments:
        schedule_time = _as_datetime(appointment.get("schedule_time"))
        if not schedule_time or appointment.get("no_show") or _appointment_is_canceled(appointment):
            continue
        if schedule_time.tzinfo is None:
            schedule_time = schedule_time.replace(tzinfo=timezone.utc)
        if schedule_time < now:
            completed += 1

    latest_appointment = appointments[0] if appointments else {}
    summary = {
        "total_appointments": total,
        "completed_or_attended": completed,
        "canceled": canceled,
        "no_show": no_show,
    }
    if latest_appointment:
        summary["latest_appointment"] = {
            "date": _date_only(latest_appointment.get("schedule_time")),
            "event_name": latest_appointment.get("event_name"),
            "outcome": latest_appointment.get("outcome_name"),
            "outcome_role": latest_appointment.get("outcome_role"),
            "has_fathom_record": latest_appointment.get("has_fathom_record"),
        }
    return sanitize_for_llm(summary)


def compact_call_summaries(
    fathom_calls: list[dict[str, Any]],
    *,
    include_links: bool,
    full_summary_limit: int = DEFAULT_FULL_CALL_SUMMARIES,
) -> list[dict[str, Any]]:
    """Return cleaned Fathom/call mini-records for all returned calls."""

    compact_calls: list[dict[str, Any]] = []
    for index, call in enumerate(fathom_calls):
        include_summary = index < full_summary_limit
        cleaned_summary = (
            clean_fathom_markdown_summary(call.get("summary"))
            if include_summary
            else {"summary_text": ""}
        )
        duration = call.get("call_duration_seconds")
        duration_minutes = None
        if duration is not None:
            try:
                duration_minutes = round(float(duration) / 60)
            except (TypeError, ValueError):
                duration_minutes = None

        compact = {
            "date": _date_only(call.get("call_started_at") or call.get("schedule_time")),
            "event_name": _clean_markdown_text(call.get("event_name")),
            "duration_minutes": duration_minutes,
            "ai_confidence_score": float(call["ai_confidence_score"])
            if call.get("ai_confidence_score") is not None
            else None,
            "outcome_applied": call.get("outcome_applied"),
            "has_recording_url": bool(call.get("has_recording_url") or call.get("recording_url")),
            "has_transcript_url": bool(call.get("has_transcript_url") or call.get("transcript_url")),
        }
        if include_summary:
            compact["summary_clean"] = cleaned_summary.get("summary_text")
            compact["topics"] = cleaned_summary.get("topics")
        if include_links:
            compact["recording_url"] = call.get("recording_url")
            compact["transcript_url"] = call.get("transcript_url")
        compact_calls.append(sanitize_for_llm(compact, allow_urls=include_links))

    return [item for item in compact_calls if item]


def _compact_latest_call(
    fathom_calls: list[dict[str, Any]],
    *,
    include_links: bool,
) -> dict[str, Any]:
    call_summaries = compact_call_summaries(fathom_calls, include_links=include_links)
    return call_summaries[0] if call_summaries else {}


def _compact_payment_summary(payments_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for row in payments_summary:
        currency = row.get("currency")
        item = {
            "currency": normalize_currency_code(currency),
            "payment_count": row.get("payment_count"),
            "paid_payment_count": row.get("paid_payment_count"),
            "outstanding_payment_count": row.get("outstanding_payment_count"),
            "overdue_payment_count": row.get("overdue_payment_count"),
            "paid_amount": format_money_minor(row.get("paid_amount"), currency),
            "outstanding_amount": format_money_minor(row.get("outstanding_amount"), currency),
            "overdue_amount": format_money_minor(row.get("overdue_amount"), currency),
        }
        item["paid_amount_display"] = item["paid_amount"]["amount_display"]
        item["outstanding_amount_display"] = item["outstanding_amount"]["amount_display"]
        item["overdue_amount_display"] = item["overdue_amount"]["amount_display"]
        compact.append(sanitize_for_llm(item))
    return compact


def compact_contract_payment(
    *,
    contracts: list[dict[str, Any]],
    payments_summary: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    payment_links: list[dict[str, Any]],
    payment_proofs: list[dict[str, Any]],
    refunds: list[dict[str, Any]],
    invoices: list[dict[str, Any]],
    subscriptions: list[dict[str, Any]],
) -> dict[str, Any]:
    compact_contracts: list[dict[str, Any]] = []
    for contract in contracts:
        value = format_money_minor(contract.get("total_value"), contract.get("currency"))
        compact_contracts.append(
            sanitize_for_llm(
                {
                    "program_name": contract.get("program_name"),
                    "status": contract.get("contract_status"),
                    "type": contract.get("contract_type"),
                    "value": value,
                    "value_display": value["amount_display"],
                    "signed": bool(contract.get("signed_at")),
                    "sent": bool(contract.get("sent_at")),
                    "voided": bool(contract.get("voided_at")),
                    "voided_reason": contract.get("voided_reason"),
                    "closer": _availability_label(
                        contract.get("closer_id"),
                        "Closer available",
                        "No closer",
                    ),
                    "setter": _availability_label(
                        contract.get("setter_id"),
                        "Setter available",
                        "No setter",
                    ),
                }
            )
        )

    compact_payments: list[dict[str, Any]] = []
    for payment in payments:
        amount = format_money_minor(payment.get("amount"), payment.get("currency"))
        compact_payments.append(
            sanitize_for_llm(
                {
                    "type": payment.get("payment_type"),
                    "status": payment.get("payment_status"),
                    "provider": payment.get("payment_provider"),
                    "amount": amount,
                    "amount_display": amount["amount_display"],
                    "due_date": payment.get("due_date"),
                    "paid_at": payment.get("paid_at"),
                    "paid": payment.get("payment_status") == "PAID",
                    "is_overdue": _payment_is_overdue(payment),
                    "failure_reason": payment.get("failure_reason"),
                    "note": payment.get("note"),
                }
            )
        )

    compact_refunds = [
        sanitize_for_llm(
            {
                "status": refund.get("refund_status"),
                "amount": format_money_minor(refund.get("amount"), refund.get("currency")),
                "amount_display": format_money_minor(refund.get("amount"), refund.get("currency"))[
                    "amount_display"
                ],
                "refunded_at": refund.get("refunded_at"),
                "reason": refund.get("reason"),
                "failure_reason": refund.get("failure_reason"),
            }
        )
        for refund in refunds
    ]
    compact_invoices = [
        sanitize_for_llm(
            {
                "invoice_number": invoice.get("invoice_number"),
                "status": invoice.get("invoice_status"),
                "amount": format_money_minor(invoice.get("amount"), invoice.get("currency")),
                "amount_display": format_money_minor(invoice.get("amount"), invoice.get("currency"))[
                    "amount_display"
                ],
                "issued_at": invoice.get("issued_at"),
                "paid_at": invoice.get("paid_at"),
            }
        )
        for invoice in invoices
    ]
    compact_subscriptions = [
        sanitize_for_llm(
            {
                "program_name": subscription.get("program_name"),
                "status": subscription.get("subscription_status"),
                "provider": subscription.get("payment_provider"),
                "amount_per_cycle": format_money_minor(
                    subscription.get("amount_per_cycle"),
                    subscription.get("currency"),
                ),
                "amount_per_cycle_display": format_money_minor(
                    subscription.get("amount_per_cycle"),
                    subscription.get("currency"),
                )["amount_display"],
                "billing_interval": subscription.get("billing_interval"),
                "billing_cycles_paid": subscription.get("billing_cycles_paid"),
                "total_collected": format_money_minor(
                    subscription.get("total_collected"),
                    subscription.get("currency"),
                ),
                "total_collected_display": format_money_minor(
                    subscription.get("total_collected"),
                    subscription.get("currency"),
                )["amount_display"],
                "next_billing_date": subscription.get("next_billing_date"),
                "started_at": subscription.get("started_at"),
                "cancel_at_period_end": subscription.get("cancel_at_period_end"),
                "cancelled_at": subscription.get("cancelled_at"),
                "cancellation_reason": subscription.get("cancellation_reason"),
            }
        )
        for subscription in subscriptions
    ]

    summary_by_currency = _compact_payment_summary(payments_summary)
    summary: dict[str, Any] = {
        "contracts": compact_contracts,
        "payments": compact_payments,
        "payment_summary_by_currency": summary_by_currency,
        "refunds": compact_refunds,
        "invoices": compact_invoices,
        "subscriptions": compact_subscriptions,
        "has_payment_link": bool(payment_links),
        "has_payment_proof": bool(payment_proofs),
        "has_refund": bool(refunds),
    }
    if len(summary_by_currency) == 1:
        summary["paid_amount_display"] = summary_by_currency[0].get("paid_amount_display")
        summary["outstanding_amount_display"] = summary_by_currency[0].get(
            "outstanding_amount_display"
        )
        summary["overdue_amount_display"] = summary_by_currency[0].get("overdue_amount_display")
    return sanitize_for_llm(summary)


def _add_clean_event(
    events: list[dict[str, Any]],
    event_time: Any,
    title: str,
    summary: str,
) -> None:
    date_text = _date_only(event_time)
    if not date_text:
        return
    safe_summary = _clean_markdown_text(summary)
    events.append(
        {
            "date": date_text,
            "title": title,
            "summary": safe_summary,
            "event": safe_summary,
        }
    )


def build_clean_timeline(
    *,
    lead_profile: dict[str, Any],
    acquisition: list[dict[str, Any]],
    appointments: list[dict[str, Any]],
    fathom_calls: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    payment_links: list[dict[str, Any]],
    payment_proofs: list[dict[str, Any]],
    refunds: list[dict[str, Any]],
    invoices: list[dict[str, Any]],
    subscriptions: list[dict[str, Any]],
    subscription_checkout_links: list[dict[str, Any]],
    max_events: int,
) -> list[dict[str, Any]]:
    if max_events == 0:
        return []

    events: list[dict[str, Any]] = []
    display_name = lead_profile.get("display_name") or "Lead"
    _add_clean_event(
        events,
        lead_profile.get("created_at"),
        "Lead created",
        f"{display_name} was created.",
    )

    for row in acquisition:
        source = row.get("provider_form_name") or row.get("opt_in_source") or "an opt-in"
        _add_clean_event(
            events,
            row.get("created_at"),
            "Opt-in submitted",
            f"Lead submitted {source}.",
        )

    now = datetime.now(timezone.utc)
    for appointment in appointments:
        event_name = appointment.get("event_name") or "Appointment"
        schedule_time = _as_datetime(appointment.get("schedule_time"))
        if _appointment_is_canceled(appointment):
            title = "Appointment canceled"
            summary = f"{event_name} was marked Canceled."
        elif appointment.get("no_show"):
            title = "Appointment no-show"
            summary = f"{event_name} was marked No Show."
        elif schedule_time:
            comparable_time = schedule_time
            if comparable_time.tzinfo is None:
                comparable_time = comparable_time.replace(tzinfo=timezone.utc)
            if comparable_time < now:
                title = "Appointment completed"
                summary = f"{event_name} took place."
            else:
                title = "Appointment scheduled"
                summary = f"{event_name} is scheduled."
        else:
            continue
        _add_clean_event(events, appointment.get("schedule_time"), title, summary)

    for call in fathom_calls:
        event_name = call.get("event_name") or "Call"
        _add_clean_event(
            events,
            call.get("call_started_at") or call.get("schedule_time"),
            "Fathom call recorded",
            f"{event_name} had a Fathom record.",
        )

    for note in notes:
        _add_clean_event(events, note.get("created_at"), "Note added", "A lead note was added.")

    for contract in contracts:
        program = contract.get("program_name") or "Program"
        value = format_money_minor(contract.get("total_value"), contract.get("currency"))
        _add_clean_event(
            events,
            contract.get("created_at"),
            "Contract created",
            f"{program} contract was created for {value['amount_display']}.",
        )
        _add_clean_event(
            events,
            contract.get("sent_at"),
            "Contract sent",
            f"{program} contract was sent for {value['amount_display']}.",
        )
        _add_clean_event(
            events,
            contract.get("signed_at"),
            "Contract signed",
            f"{program} contract was signed.",
        )
        _add_clean_event(
            events,
            contract.get("voided_at"),
            "Contract voided",
            f"{program} contract was voided.",
        )

    for payment in payments:
        payment_type = _readable_enum(payment.get("payment_type")) or "Payment"
        amount = format_money_minor(payment.get("amount"), payment.get("currency"))
        status = str(payment.get("payment_status") or "").upper()
        if status == "PAID":
            _add_clean_event(
                events,
                payment.get("paid_at") or payment.get("created_at"),
                "Payment paid",
                f"{payment_type} payment of {amount['amount_display']} was paid.",
            )
        elif _payment_is_overdue(payment, now=now):
            _add_clean_event(
                events,
                payment.get("due_date"),
                "Payment overdue",
                f"{payment_type} payment of {amount['amount_display']} is overdue.",
            )
        else:
            _add_clean_event(
                events,
                payment.get("due_date") or payment.get("created_at"),
                "Payment due",
                f"{payment_type} payment of {amount['amount_display']} is due.",
            )

    for row in payment_links:
        _add_clean_event(
            events,
            row.get("created_at"),
            "Payment link created",
            "A payment link was created.",
        )
    for row in payment_proofs:
        _add_clean_event(
            events,
            row.get("created_at"),
            "Payment proof uploaded",
            "A payment proof was uploaded.",
        )
    for refund in refunds:
        amount = format_money_minor(refund.get("amount"), refund.get("currency"))
        title = "Refund succeeded" if refund.get("refund_status") == "SUCCEEDED" else "Refund initiated"
        _add_clean_event(
            events,
            refund.get("refunded_at") or refund.get("created_at"),
            title,
            f"{title} for {amount['amount_display']}.",
        )
    for invoice in invoices:
        amount = format_money_minor(invoice.get("amount"), invoice.get("currency"))
        _add_clean_event(
            events,
            invoice.get("issued_at") or invoice.get("created_at"),
            "Invoice issued",
            f"Invoice was issued for {amount['amount_display']}.",
        )
        _add_clean_event(
            events,
            invoice.get("paid_at"),
            "Invoice paid",
            "Invoice was paid.",
        )
    for subscription in subscriptions:
        amount = format_money_minor(subscription.get("amount_per_cycle"), subscription.get("currency"))
        _add_clean_event(
            events,
            subscription.get("started_at") or subscription.get("created_at"),
            "Subscription started",
            f"Subscription started at {amount['amount_display']} per {_readable_enum(subscription.get('billing_interval')).lower()}.",
        )
        _add_clean_event(
            events,
            subscription.get("next_billing_date"),
            "Subscription next billing",
            f"Next subscription billing is scheduled for {amount['amount_display']}.",
        )
        if subscription.get("cancel_at_period_end"):
            _add_clean_event(
                events,
                subscription.get("next_billing_date") or subscription.get("created_at"),
                "Subscription cancellation scheduled",
                "Subscription is scheduled to cancel at period end.",
            )
        _add_clean_event(
            events,
            subscription.get("cancelled_at"),
            "Subscription cancelled",
            "Subscription was cancelled.",
        )
    for row in subscription_checkout_links:
        _add_clean_event(
            events,
            row.get("created_at"),
            "Subscription checkout link created",
            "A subscription checkout link was created.",
        )

    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in events:
        deduped[(event["date"], event["title"], event["summary"])] = event
    selected = sorted(deduped.values(), key=lambda event: event["date"], reverse=True)[:max_events]
    return [sanitize_for_llm(event) for event in sorted(selected, key=lambda event: event["date"])]


def build_data_quality_summary(
    data_quality: dict[str, Any],
    journey_evidence: dict[str, Any],
) -> dict[str, Any]:
    missing_labels = {
        "missing_source": "Lead source",
        "missing_first_source": "First source",
        "missing_last_source": "Last source",
        "missing_next_touch_point": "Next touch point",
        "has_no_notes": "Notes",
        "has_no_appointments": "Appointments",
        "has_no_contracts": "Contracts",
        "has_no_payments": "Payments",
        "has_no_fathom_calls": "Fathom calls",
    }
    risk_labels = {
        "has_pending_payment": "Pending payment",
        "has_overdue_payment": "Pending overdue payment",
        "has_unsigned_contract": "Unsigned contract",
        "has_unpaid_contract": "Unpaid contract",
        "has_refund": "Refund present",
    }
    flags_to_keep = [
        "missing_first_source",
        "missing_last_source",
        "missing_next_touch_point",
        "missing_source",
        "has_no_notes",
        "has_no_appointments",
        "has_no_contracts",
        "has_no_payments",
        "has_no_fathom_calls",
        "has_pending_payment",
        "has_overdue_payment",
        "has_unsigned_contract",
        "has_unpaid_contract",
        "has_payment_link",
        "has_payment_proof",
        "has_refund",
        "source_evidence_level",
        "unsupported_journey_questions",
    ]
    summary = {
        "source_evidence_level": data_quality.get("source_evidence_level"),
        "missing": [
            label for flag, label in missing_labels.items() if bool(data_quality.get(flag))
        ],
        "risks": [label for flag, label in risk_labels.items() if bool(data_quality.get(flag))],
        "limitations": CLEAN_JOURNEY_LIMITATIONS,
        "flags": {flag: data_quality.get(flag) for flag in flags_to_keep if flag in data_quality},
    }
    return sanitize_for_llm(summary)


def _friendly_evidence(signal_name: str, evidence: list[str]) -> list[str]:
    friendly: list[str] = []
    for item in evidence:
        label = str(item)
        if item == "fathom_summary":
            if signal_name == "text_message":
                label = "Fathom summary mentions WhatsApp or text follow-up"
            else:
                label = "Fathom summary mentions this signal"
        elif item == "notes":
            label = "Lead notes mention this signal"
        elif item == "form_answers":
            label = "Form answers mention this signal"
        elif item == "provider_form_name":
            label = "Provider form name"
        elif item == "utm_source":
            label = "UTM source"
        elif item == "utm_campaign":
            label = "UTM campaign"
        elif item == "landing_page":
            label = "Landing page"
        elif item == "referrer":
            label = "Referrer"
        else:
            label = _readable_enum(item)
        friendly.append(label)
    return _unique_present(friendly)


def _compact_journey_evidence(
    journey_evidence: dict[str, Any],
    data_quality: dict[str, Any],
) -> dict[str, Any]:
    raw_signals = journey_evidence.get("interaction_signals") or {}
    signals: dict[str, Any] = {}
    for name, signal in raw_signals.items():
        if not isinstance(signal, dict):
            continue
        evidence = signal.get("evidence") if isinstance(signal.get("evidence"), list) else []
        signals[name] = {
            "status": signal.get("status"),
            "evidence": _friendly_evidence(name, evidence),
        }

    available = journey_evidence.get("available_source_fields") or {}
    source_fields = {
        "lead_source": available.get("lead_source"),
        "first_source": available.get("first_source"),
        "last_source": available.get("last_source"),
        "opt_in_sources": available.get("opt_in_sources"),
        "provider_forms": available.get("provider_forms"),
        "utm_sources": available.get("utm_sources"),
        "utm_campaigns": available.get("utm_campaigns"),
        "landing_pages": available.get("landing_pages"),
        "referrers": available.get("referrers"),
    }
    return sanitize_for_llm(
        {
            "source_evidence_level": data_quality.get("source_evidence_level"),
            "available_source_fields": source_fields,
            "interaction_signals": signals,
            "limitations": CLEAN_JOURNEY_LIMITATIONS,
        }
    )


def _build_current_state(
    *,
    lead_profile: dict[str, Any],
    appointments: list[dict[str, Any]],
    fathom_calls: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    timeline_clean: list[dict[str, Any]],
    data_quality: dict[str, Any],
) -> dict[str, Any]:
    status_name = lead_profile.get("status_name")
    status_role = str(lead_profile.get("status_role") or "").upper()
    if status_role == "WON":
        temperature = "converted"
    elif data_quality.get("has_overdue_payment") or data_quality.get("has_unsigned_contract"):
        temperature = "warm_stalled"
    elif status_role in {"LOST", "UNQUALIFIED", "CANCELED"}:
        temperature = "cold_or_closed"
    elif appointments or fathom_calls:
        temperature = "warm"
    else:
        temperature = "new_or_unclear"

    blockers: list[str] = []
    if data_quality.get("has_unsigned_contract"):
        blockers.append("unsigned contract")
    if data_quality.get("has_overdue_payment"):
        blockers.append("overdue pending payment")
    elif data_quality.get("has_pending_payment"):
        blockers.append("pending payment")
    if data_quality.get("missing_next_touch_point"):
        blockers.append("no next touch point set")
    main_blocker = " and ".join(blockers).capitalize() if blockers else "No clear blocker in available context"

    if fathom_calls:
        latest_call = fathom_calls[0]
        latest_activity = (
            f"{latest_call.get('event_name') or 'Call'} completed on "
            f"{_date_only(latest_call.get('call_started_at') or latest_call.get('schedule_time'))} "
            "with Fathom record"
        )
    elif timeline_clean:
        latest = timeline_clean[-1]
        latest_activity = f"{latest.get('title')} on {latest.get('date')}"
    else:
        latest_activity = "No recent activity available"

    next_touch_point = lead_profile.get("next_touch_point_at")
    current_state = {
        "status": status_name,
        "temperature": temperature,
        "main_blocker": main_blocker,
        "latest_activity": latest_activity,
        "next_touch_point": _iso_or_none(next_touch_point) if next_touch_point else "Not set",
    }
    return sanitize_for_llm(current_state)


def _build_llm_lead_360(
    *,
    lead_profile: dict[str, Any],
    source_context: dict[str, Any],
    journey_evidence: dict[str, Any],
    acquisition: list[dict[str, Any]],
    form_answers: list[dict[str, Any]],
    appointments: list[dict[str, Any]],
    fathom_calls: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    payments_summary: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    payment_links: list[dict[str, Any]],
    payment_proofs: list[dict[str, Any]],
    refunds: list[dict[str, Any]],
    invoices: list[dict[str, Any]],
    subscriptions: list[dict[str, Any]],
    subscription_checkout_links: list[dict[str, Any]],
    data_quality: dict[str, Any],
    include_contact_details: bool,
    include_links: bool,
    max_full_call_summaries: int,
    max_timeline_events: int,
) -> dict[str, Any]:
    timeline_clean = build_clean_timeline(
        lead_profile=lead_profile,
        acquisition=acquisition,
        appointments=appointments,
        fathom_calls=fathom_calls,
        notes=notes,
        contracts=contracts,
        payments=payments,
        payment_links=payment_links,
        payment_proofs=payment_proofs,
        refunds=refunds,
        invoices=invoices,
        subscriptions=subscriptions,
        subscription_checkout_links=subscription_checkout_links,
        max_events=max_timeline_events,
    )

    payload = {
        "profile": compact_profile(
            lead_profile,
            include_contact_details=include_contact_details,
        ),
        "current_state": _build_current_state(
            lead_profile=lead_profile,
            appointments=appointments,
            fathom_calls=fathom_calls,
            contracts=contracts,
            payments=payments,
            timeline_clean=timeline_clean,
            data_quality=data_quality,
        ),
        "acquisition_summary": compact_acquisition(
            source_context=source_context,
            acquisition=acquisition,
            form_answers=form_answers,
            data_quality=data_quality,
        ),
        "form_answer_summary": compact_form_answers(form_answers),
        "notes_summary": compact_notes(notes),
        "appointment_summary": compact_appointments(appointments),
        "appointments": compact_appointment_records(appointments),
        "latest_call_summary": _compact_latest_call(
            fathom_calls,
            include_links=include_links,
        ),
        "call_summaries": compact_call_summaries(
            fathom_calls,
            include_links=include_links,
            full_summary_limit=max_full_call_summaries,
        ),
        "contract_payment_summary": compact_contract_payment(
            contracts=contracts,
            payments_summary=payments_summary,
            payments=payments,
            payment_links=payment_links,
            payment_proofs=payment_proofs,
            refunds=refunds,
            invoices=invoices,
            subscriptions=subscriptions,
        ),
        "timeline_clean": timeline_clean,
        "data_quality_summary": build_data_quality_summary(data_quality, journey_evidence),
        "journey_evidence": _compact_journey_evidence(journey_evidence, data_quality),
    }
    return sanitize_for_llm(payload, allow_urls=include_links)


def _fetch_lead_360_sections(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    include_links: bool,
    limits: dict[str, int],
    timings: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Fetch independent Lead 360 sections concurrently."""

    fetchers = {
        "source_context": partial(_fetch_source_context, db, org_id=org_id, lead_id=lead_id),
        "acquisition": partial(
            _fetch_acquisition,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_acquisition"],
        ),
        "form_answers": partial(
            _fetch_form_answers,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_form_answers"],
        ),
        "appointments": partial(
            _fetch_appointments,
            db,
            org_id=org_id,
            lead_id=lead_id,
            include_links=include_links,
            limit=limits["max_appointments"],
        ),
        "fathom_calls": partial(
            _fetch_fathom_calls,
            db,
            org_id=org_id,
            lead_id=lead_id,
            include_links=include_links,
            limit=limits["max_fathom_calls"],
            full_summary_limit=limits["max_full_call_summaries"],
        ),
        "notes": partial(
            _fetch_notes,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_notes"],
        ),
        "contracts": partial(
            _fetch_contracts,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_contracts"],
        ),
        "payments_summary": partial(
            _fetch_payments_summary,
            db,
            org_id=org_id,
            lead_id=lead_id,
        ),
        "payments": partial(
            _fetch_payments,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_payments"],
        ),
        "payment_links": partial(
            _fetch_payment_links,
            db,
            org_id=org_id,
            lead_id=lead_id,
            include_links=include_links,
            limit=limits["max_payment_links"],
        ),
        "payment_proofs": partial(
            _fetch_payment_proofs,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_payment_proofs"],
        ),
        "refunds": partial(
            _fetch_refunds,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_refunds"],
        ),
        "invoices": partial(
            _fetch_invoices,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_invoices"],
        ),
        "subscriptions": partial(
            _fetch_subscriptions,
            db,
            org_id=org_id,
            lead_id=lead_id,
            limit=limits["max_subscriptions"],
        ),
        "subscription_checkout_links": partial(
            _fetch_subscription_checkout_links,
            db,
            org_id=org_id,
            lead_id=lead_id,
            include_links=include_links,
            limit=limits["max_subscription_checkout_links"],
        ),
    }

    def timed_fetch(name: str, fetcher: Any) -> tuple[str, Any, dict[str, Any]]:
        started_at = time.perf_counter()
        try:
            result = fetcher()
        except Exception as exc:  # noqa: BLE001 - keep timing before bubbling up.
            event = _record_timing(
                None,
                section="section_queries",
                subsection=name,
                started_at=started_at,
                status="error",
                details={"error": type(exc).__name__},
            )
            return name, exc, event

        count = len(result) if isinstance(result, list) else 1 if result else 0
        event = _record_timing(
            None,
            section="section_queries",
            subsection=name,
            started_at=started_at,
            details={"rows": count},
        )
        return name, result, event

    results: dict[str, Any] = {}
    max_workers = min(LEAD_360_FETCH_WORKERS, len(fetchers))
    parallel_started_at = time.perf_counter()
    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="lead360-fetch",
    ) as executor:
        future_to_name = {
            executor.submit(timed_fetch, name, fetcher): name
            for name, fetcher in fetchers.items()
        }
        for future in as_completed(future_to_name):
            name, result, event = future.result()
            if timings is not None:
                timings.append(event)
            if isinstance(result, Exception):
                raise result
            results[name] = result

    _record_timing(
        timings,
        section="section_queries",
        subsection="parallel_wall_time",
        started_at=parallel_started_at,
        details={"workers": max_workers},
    )

    return results


def _build_lead_360(
    db: Any,
    *,
    org_id: str,
    lead_id: str,
    include_contact_details: bool,
    include_links: bool,
    limits: dict[str, int],
    timings: Optional[list[dict[str, Any]]] = None,
) -> Optional[dict[str, Any]]:
    profile_started_at = time.perf_counter()
    try:
        lead_profile = _fetch_lead_profile(
            db,
            org_id=org_id,
            lead_id=lead_id,
            include_contact_details=include_contact_details,
        )
    except Exception:
        _record_timing(
            timings,
            section="lead_context",
            subsection="lead_profile",
            started_at=profile_started_at,
            status="error",
        )
        raise
    _record_timing(
        timings,
        section="lead_context",
        subsection="lead_profile",
        started_at=profile_started_at,
        details={"rows": 1 if lead_profile else 0},
    )
    if not lead_profile:
        return None

    sections = _fetch_lead_360_sections(
        db,
        org_id=org_id,
        lead_id=lead_id,
        include_links=include_links,
        limits=limits,
        timings=timings,
    )
    source_context = sections["source_context"]
    acquisition = sections["acquisition"]
    form_answers = sections["form_answers"]
    appointments = sections["appointments"]
    fathom_calls = sections["fathom_calls"]
    notes = sections["notes"]
    contracts = sections["contracts"]
    payments_summary = sections["payments_summary"]
    payments = sections["payments"]
    payment_links = sections["payment_links"]
    payment_proofs = sections["payment_proofs"]
    refunds = sections["refunds"]
    invoices = sections["invoices"]
    subscriptions = sections["subscriptions"]
    subscription_checkout_links = sections["subscription_checkout_links"]

    assembly_started_at = time.perf_counter()
    journey_evidence = _build_journey_evidence(
        source_context=source_context,
        acquisition=acquisition,
        form_answers=form_answers,
        notes=notes,
        fathom_calls=fathom_calls,
    )
    data_quality = _build_data_quality(
        lead_profile=lead_profile,
        source_context=source_context,
        acquisition=acquisition,
        appointments=appointments,
        fathom_calls=fathom_calls,
        notes=notes,
        contracts=contracts,
        payments=payments,
        payment_links=payment_links,
        payment_proofs=payment_proofs,
        refunds=refunds,
    )

    _strip_internal_fields(appointments)
    _strip_internal_fields(payments)

    lead_360 = _build_llm_lead_360(
        lead_profile=lead_profile,
        source_context=source_context,
        journey_evidence=journey_evidence,
        acquisition=acquisition,
        form_answers=form_answers,
        appointments=appointments,
        fathom_calls=fathom_calls,
        notes=notes,
        contracts=contracts,
        payments_summary=payments_summary,
        payments=payments,
        payment_links=payment_links,
        payment_proofs=payment_proofs,
        refunds=refunds,
        invoices=invoices,
        subscriptions=subscriptions,
        subscription_checkout_links=subscription_checkout_links,
        data_quality=data_quality,
        include_contact_details=include_contact_details,
        include_links=include_links,
        max_full_call_summaries=limits["max_full_call_summaries"],
        max_timeline_events=limits["max_timeline_events"],
    )
    _record_timing(
        timings,
        section="context_assembly",
        subsection="build_payload",
        started_at=assembly_started_at,
    )
    return lead_360


def get_lead_360(
    org_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    lead_name: Optional[str] = None,
    lead_email: Optional[str] = None,
    lead_phone: Optional[str] = None,
    include_contact_details: bool = False,
    include_links: bool = False,
    max_notes: int = 10,
    max_appointments: int = 10,
    max_fathom_calls: int = 5,
    max_acquisition: int = 10,
    max_form_answers: int = 20,
    max_contracts: int = 10,
    max_payments: int = 20,
    max_payment_links: int = 10,
    max_payment_proofs: int = 10,
    max_refunds: int = 10,
    max_invoices: int = 10,
    max_subscriptions: int = 10,
    max_subscription_checkout_links: int = 10,
    max_full_call_summaries: int = DEFAULT_FULL_CALL_SUMMARIES,
    max_timeline_events: int = 50,
) -> dict[str, Any]:
    """Return safe structured Lead 360 context for one lead."""

    started_at = time.perf_counter()
    timings: list[dict[str, Any]] = []
    settings = get_sql_agent_settings()
    effective_org_id = _clean_string(org_id) or settings.default_org_id
    if not effective_org_id:
        return _json_ready(
            _attach_diagnostics(
                _safe_error_response(
                    "Unable to fetch Lead 360 context.",
                    "missing_org_id",
                ),
                timings,
                started_at=started_at,
            )
        )

    clean_lead_id = _clean_string(lead_id)
    clean_lead_email = _clean_string(lead_email)
    clean_lead_phone = _clean_string(lead_phone)
    clean_lead_name = _clean_string(lead_name)

    if not any([clean_lead_id, clean_lead_email, clean_lead_phone, clean_lead_name]):
        return _json_ready(
            _attach_diagnostics(
                _safe_error_response(
                    "Please provide a lead ID, email, phone, or name to fetch Lead 360 context.",
                    "missing_lead_identifier",
                ),
                timings,
                started_at=started_at,
            )
        )

    limits = {
        "max_notes": _clamp_limit(max_notes, 10),
        "max_appointments": _clamp_limit(max_appointments, 10),
        "max_fathom_calls": _clamp_limit(max_fathom_calls, 5),
        "max_acquisition": _clamp_limit(max_acquisition, 10),
        "max_form_answers": _clamp_limit(max_form_answers, 20),
        "max_contracts": _clamp_limit(max_contracts, 10),
        "max_payments": _clamp_limit(max_payments, 20),
        "max_payment_links": _clamp_limit(max_payment_links, 10),
        "max_payment_proofs": _clamp_limit(max_payment_proofs, 10),
        "max_refunds": _clamp_limit(max_refunds, 10),
        "max_invoices": _clamp_limit(max_invoices, 10),
        "max_subscriptions": _clamp_limit(max_subscriptions, 10),
        "max_subscription_checkout_links": _clamp_limit(
            max_subscription_checkout_links,
            10,
        ),
        "max_full_call_summaries": _clamp_limit(
            max_full_call_summaries,
            DEFAULT_FULL_CALL_SUMMARIES,
        ),
        "max_timeline_events": _clamp_limit(max_timeline_events, 50),
    }
    limits["max_full_call_summaries"] = min(
        limits["max_full_call_summaries"],
        limits["max_fathom_calls"],
    )

    try:
        db = get_db()
        if clean_lead_id:
            resolve_started_at = time.perf_counter()
            if not _is_uuid_like(clean_lead_id):
                _record_timing(
                    timings,
                    section="lead_resolution",
                    subsection="resolve_lead",
                    started_at=resolve_started_at,
                    details={"matches": 0, "path": "invalid_id"},
                )
                return _json_ready(
                    _attach_diagnostics(
                        _not_found_response(),
                        timings,
                        started_at=started_at,
                    )
                )

            _record_timing(
                timings,
                section="lead_resolution",
                subsection="resolve_lead",
                started_at=resolve_started_at,
                details={"matches": 1, "path": "id_fast_path"},
            )
            build_started_at = time.perf_counter()
            try:
                lead_360 = _build_lead_360(
                    db,
                    org_id=effective_org_id,
                    lead_id=clean_lead_id,
                    include_contact_details=include_contact_details,
                    include_links=include_links,
                    limits=limits,
                    timings=timings,
                )
            except Exception:
                _record_timing(
                    timings,
                    section="lead_360_tool",
                    subsection="build_lead_360",
                    started_at=build_started_at,
                    status="error",
                )
                raise
            _record_timing(
                timings,
                section="lead_360_tool",
                subsection="build_lead_360",
                started_at=build_started_at,
            )
            if lead_360 is None:
                return _json_ready(
                    _attach_diagnostics(
                        _not_found_response(),
                        timings,
                        started_at=started_at,
                    )
                )

            return _json_ready(
                _attach_diagnostics(
                    {
                        "status": "success",
                        "message": "Lead 360 context found.",
                        "matches": [],
                        "lead_360": lead_360,
                    },
                    timings,
                    started_at=started_at,
                )
            )

        resolve_started_at = time.perf_counter()
        try:
            matches = _resolve_lead(
                db,
                org_id=effective_org_id,
                lead_id=clean_lead_id,
                lead_name=clean_lead_name,
                lead_email=clean_lead_email,
                lead_phone=clean_lead_phone,
                include_contact_details=include_contact_details,
            )
        except Exception:
            _record_timing(
                timings,
                section="lead_resolution",
                subsection="resolve_lead",
                started_at=resolve_started_at,
                status="error",
            )
            raise
        _record_timing(
            timings,
            section="lead_resolution",
            subsection="resolve_lead",
            started_at=resolve_started_at,
            details={"matches": len(matches)},
        )
        if not matches:
            return _json_ready(
                _attach_diagnostics(
                    _not_found_response(),
                    timings,
                    started_at=started_at,
                )
            )
        if len(matches) > 1:
            return _json_ready(
                _attach_diagnostics(
                    _multiple_matches_response(
                        _compact_matches(
                            matches,
                            include_contact_details=include_contact_details,
                        )
                    ),
                    timings,
                    started_at=started_at,
                )
            )

        build_started_at = time.perf_counter()
        try:
            resolved_lead_id = str(matches[0]["lead_id"])
            lead_360 = _build_lead_360(
                db,
                org_id=effective_org_id,
                lead_id=resolved_lead_id,
                include_contact_details=include_contact_details,
                include_links=include_links,
                limits=limits,
                timings=timings,
            )
        except Exception:
            _record_timing(
                timings,
                section="lead_360_tool",
                subsection="build_lead_360",
                started_at=build_started_at,
                status="error",
            )
            raise
        _record_timing(
            timings,
            section="lead_360_tool",
            subsection="build_lead_360",
            started_at=build_started_at,
        )
        if lead_360 is None:
            return _json_ready(
                _attach_diagnostics(
                    _not_found_response(),
                    timings,
                    started_at=started_at,
                )
            )

        return _json_ready(
            _attach_diagnostics(
                {
                    "status": "success",
                    "message": "Lead 360 context found.",
                    "matches": [],
                    "lead_360": lead_360,
                },
                timings,
                started_at=started_at,
            )
        )
    except Exception:  # noqa: BLE001 - tool output must stay safe; details are logged.
        LOGGER.exception("Unable to fetch Lead 360 context")
        return _json_ready(
            _attach_diagnostics(
                _safe_error_response(
                    "Unable to fetch Lead 360 context.",
                    "database_error",
                ),
                timings,
                started_at=started_at,
            )
        )


def _get_lead_360_tool(
    org_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    lead_name: Optional[str] = None,
    lead_email: Optional[str] = None,
    lead_phone: Optional[str] = None,
    include_contact_details: bool = False,
    include_links: bool = False,
    max_notes: int = 10,
    max_appointments: int = 10,
    max_fathom_calls: int = 5,
    max_acquisition: int = 10,
    max_form_answers: int = 20,
    max_contracts: int = 10,
    max_payments: int = 20,
    max_payment_links: int = 10,
    max_payment_proofs: int = 10,
    max_refunds: int = 10,
    max_invoices: int = 10,
    max_subscriptions: int = 10,
    max_subscription_checkout_links: int = 10,
    max_full_call_summaries: int = DEFAULT_FULL_CALL_SUMMARIES,
    max_timeline_events: int = 50,
) -> str:
    """Fetch safe structured Lead 360 context for one specific lead.

    Provide one lead identifier: lead_id, lead_email, lead_phone, or lead_name.
    By default, full Fathom summary text is included for the latest two calls
    only. If the user explicitly asks for all call summaries, set
    max_full_call_summaries equal to max_fathom_calls.
    If org_id is omitted, the tool uses the active request organization.
    """

    payload = get_lead_360(
        org_id=org_id,
        lead_id=lead_id,
        lead_name=lead_name,
        lead_email=lead_email,
        lead_phone=lead_phone,
        include_contact_details=include_contact_details,
        include_links=include_links,
        max_notes=max_notes,
        max_appointments=max_appointments,
        max_fathom_calls=max_fathom_calls,
        max_acquisition=max_acquisition,
        max_form_answers=max_form_answers,
        max_contracts=max_contracts,
        max_payments=max_payments,
        max_payment_links=max_payment_links,
        max_payment_proofs=max_payment_proofs,
        max_refunds=max_refunds,
        max_invoices=max_invoices,
        max_subscriptions=max_subscriptions,
        max_subscription_checkout_links=max_subscription_checkout_links,
        max_full_call_summaries=max_full_call_summaries,
        max_timeline_events=max_timeline_events,
    )
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


get_lead_360_tool = tool("get_lead_360")(_get_lead_360_tool)
