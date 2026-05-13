"""Read-only diagnostic tools over diagnostic_lead_snapshot.

These tools provide controlled evidence for the future diagnostic analytics
agent. They intentionally use fixed SQL templates instead of LLM-generated SQL.

Money fields in diagnostic_lead_snapshot are already major-unit EUR values.
Do not divide diagnostic money fields by 100 in these tools or in the
diagnostic agent prompt.
"""

from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from langchain.tools import tool

from app.config import get_sql_agent_settings
from app.db import get_db


SCOPE_NOTE = (
    "This diagnostic snapshot uses lead_created_at cohort logic. "
    "Revenue and payment fields are lifetime outcomes for leads created in the selected period, "
    "not true payment-period revenue. "
    "Monetary fields returned by this tool are already major-unit EUR values, "
    "not raw minor-unit source values."
)

SUPPORTED_SOURCE_BASIS = {
    "first": "first_source",
    "last": "last_source",
}
DEFAULT_LOOKBACK_MONTHS = 6

SNAPSHOT_DATE_BOUNDS_SQL = """
SELECT
  MIN(dls.lead_created_at)::date AS min_lead_created_date,
  MAX(dls.lead_created_at)::date AS max_lead_created_date
FROM diagnostic_lead_snapshot dls
WHERE dls.clerk_org_id = :org_id
"""


def _default_org_id(org_id: str | None) -> str:
    clean_org_id = str(org_id or "").strip()
    if clean_org_id:
        return clean_org_id

    settings = get_sql_agent_settings()
    clean_default = str(settings.default_org_id or "").strip()
    if not clean_default:
        raise ValueError("org_id is required because HERMON_DEFAULT_CLERK_ORG_ID is not set.")
    return clean_default


def _parse_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    clean_value = str(value).strip()
    if not clean_value:
        return None
    return datetime.strptime(clean_value, "%Y-%m-%d").date()


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    target_year = month_index // 12
    target_month = month_index % 12 + 1
    target_day = min(value.day, monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def _query_records(
    sql: str,
    params: dict[str, Any],
    *,
    max_rows: int = 200,
) -> list[dict[str, Any]]:
    return get_db().query_records(sql, params=params, max_rows=max_rows)


def _snapshot_date_bounds(org_id: str) -> dict[str, date]:
    rows = _query_records(SNAPSHOT_DATE_BOUNDS_SQL, {"org_id": org_id}, max_rows=1)
    if not rows or rows[0].get("max_lead_created_date") is None:
        raise ValueError(
            "diagnostic_lead_snapshot has no rows for this org, so default periods cannot be derived."
        )

    min_lead_created_date = _parse_date(rows[0].get("min_lead_created_date"))
    max_lead_created_date = _parse_date(rows[0].get("max_lead_created_date"))
    if min_lead_created_date is None or max_lead_created_date is None:
        raise ValueError("diagnostic_lead_snapshot date bounds could not be parsed.")

    return {
        "min_lead_created_date": min_lead_created_date,
        "max_lead_created_date": max_lead_created_date,
    }


def _default_periods(
    org_id: str,
    current_start_date: str | None,
    current_end_date: str | None,
    previous_start_date: str | None,
    previous_end_date: str | None,
) -> dict[str, str]:
    bounds = _snapshot_date_bounds(org_id)
    anchor_date = bounds["max_lead_created_date"]

    current_start = _parse_date(current_start_date)
    current_end = _parse_date(current_end_date)
    previous_start = _parse_date(previous_start_date)
    previous_end = _parse_date(previous_end_date)

    current_start_was_defaulted = current_start is None
    current_end_was_defaulted = current_end is None

    if current_end is None:
        current_end = anchor_date + timedelta(days=1)
    if current_start is None:
        current_start = _add_months(current_end, -DEFAULT_LOOKBACK_MONTHS)

    if previous_start is None or previous_end is None:
        previous_end_default = current_start
        if current_start_was_defaulted and current_end_was_defaulted:
            previous_start_default = _add_months(
                previous_end_default,
                -DEFAULT_LOOKBACK_MONTHS,
            )
        else:
            previous_start_default = previous_end_default - (current_end - current_start)
        previous_start = previous_start or previous_start_default
        previous_end = previous_end or previous_end_default

    if current_start >= current_end:
        raise ValueError("current_start_date must be earlier than current_end_date.")
    if previous_start >= previous_end:
        raise ValueError("previous_start_date must be earlier than previous_end_date.")

    return {
        "current_start_date": current_start.isoformat(),
        "current_end_date": current_end.isoformat(),
        "previous_start_date": previous_start.isoformat(),
        "previous_end_date": previous_end.isoformat(),
        "period_anchor_date": anchor_date.isoformat(),
    }


def _safe_limit(limit: int | None, *, default: int = 10, maximum: int = 50) -> int:
    try:
        parsed = int(limit if limit is not None else default)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def _source_column(source_basis: str) -> str:
    basis = str(source_basis or "first").strip().lower()
    if basis not in SUPPORTED_SOURCE_BASIS:
        raise ValueError("source_basis must be one of: first, last.")
    return SUPPORTED_SOURCE_BASIS[basis]


def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _error_response(tool_name: str, error: Exception) -> str:
    return _json_response(
        {
            "status": "error",
            "tool": tool_name,
            "scope_note": SCOPE_NOTE,
            "row_count": 0,
            "error": str(error),
        }
    )


def _error_payload(tool_name: str, error: Exception) -> dict[str, Any]:
    return {
        "status": "error",
        "tool": tool_name,
        "scope_note": SCOPE_NOTE,
        "row_count": 0,
        "error": str(error),
    }


FUNNEL_SQL = """
WITH scoped AS (
  SELECT
    dls.funnel_stage AS funnel_stage,
    dls.conversion_outcome AS conversion_outcome,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
totals AS (
  SELECT
    COUNT(*)::int AS lead_count,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(no_show_count), 0)::int AS no_show_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(gross_paid_amount), 0)::numeric(12,2) AS gross_paid_amount,
    COALESCE(SUM(refund_amount), 0)::numeric(12,2) AS refund_amount,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COALESCE(SUM(outstanding_amount), 0)::numeric(12,2) AS outstanding_amount
  FROM scoped
),
stage_breakdown AS (
  SELECT
    funnel_stage,
    conversion_outcome,
    COUNT(*)::int AS lead_count,
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT lead_count FROM totals), 0), 2) AS pct_of_leads,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount
  FROM scoped
  GROUP BY funnel_stage, conversion_outcome
)
SELECT
  'total' AS row_type,
  NULL::text AS funnel_stage,
  NULL::text AS conversion_outcome,
  lead_count,
  NULL::numeric AS pct_of_leads,
  appointment_count,
  completed_call_count,
  no_show_count,
  signed_contract_count,
  paid_payment_count,
  gross_paid_amount,
  refund_amount,
  net_collected_amount,
  outstanding_amount
FROM totals
UNION ALL
SELECT
  'stage' AS row_type,
  funnel_stage,
  conversion_outcome,
  lead_count,
  pct_of_leads,
  appointment_count,
  completed_call_count,
  NULL::int AS no_show_count,
  signed_contract_count,
  paid_payment_count,
  NULL::numeric AS gross_paid_amount,
  NULL::numeric AS refund_amount,
  net_collected_amount,
  NULL::numeric AS outstanding_amount
FROM stage_breakdown
ORDER BY
  row_type DESC,
  lead_count DESC,
  funnel_stage ASC,
  conversion_outcome ASC
"""

SOURCE_SNAPSHOT_SQL_TEMPLATE = """
WITH scoped AS (
  SELECT
    COALESCE(NULLIF(BTRIM(dls.{source_column}), ''), 'Unknown') AS source_name,
    dls.source_confidence AS source_confidence,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount,
    dls.has_unknown_source AS has_unknown_source,
    dls.has_multiple_sources AS has_multiple_sources,
    dls.has_revenue_without_source AS has_revenue_without_source
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
source_rollup AS (
  SELECT
    source_name,
    COUNT(*)::int AS lead_count,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(no_show_count), 0)::int AS no_show_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(gross_paid_amount), 0)::numeric(12,2) AS gross_paid_amount,
    COALESCE(SUM(refund_amount), 0)::numeric(12,2) AS refund_amount,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COALESCE(SUM(outstanding_amount), 0)::numeric(12,2) AS outstanding_amount,
    COUNT(*) FILTER (WHERE source_confidence = 'high')::int AS high_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'medium')::int AS medium_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'low')::int AS low_confidence_leads,
    COUNT(*) FILTER (WHERE has_unknown_source)::int AS unknown_source_leads,
    COUNT(*) FILTER (WHERE has_multiple_sources)::int AS multiple_source_leads,
    COUNT(*) FILTER (WHERE has_revenue_without_source)::int AS revenue_without_source_leads
  FROM scoped
  GROUP BY source_name
),
scored AS (
  SELECT
    source_name,
    lead_count,
    appointment_count,
    completed_call_count,
    no_show_count,
    signed_contract_count,
    paid_payment_count,
    gross_paid_amount,
    refund_amount,
    net_collected_amount,
    outstanding_amount,
    high_confidence_leads,
    medium_confidence_leads,
    low_confidence_leads,
    unknown_source_leads,
    multiple_source_leads,
    revenue_without_source_leads,
    ROUND(100.0 * appointment_count / NULLIF(lead_count, 0), 2) AS lead_to_appointment_rate,
    ROUND(100.0 * completed_call_count / NULLIF(appointment_count, 0), 2) AS appointment_to_completed_rate,
    ROUND(100.0 * signed_contract_count / NULLIF(completed_call_count, 0), 2) AS completed_to_signed_rate,
    ROUND(100.0 * paid_payment_count / NULLIF(signed_contract_count, 0), 2) AS signed_to_paid_rate,
    ROUND(net_collected_amount / NULLIF(lead_count, 0), 2) AS net_collected_per_lead,
    ROUND(net_collected_amount / NULLIF(completed_call_count, 0), 2)
      AS net_collected_per_completed_call
  FROM source_rollup
)
SELECT
  source_name,
  lead_count,
  appointment_count,
  completed_call_count,
  no_show_count,
  signed_contract_count,
  paid_payment_count,
  gross_paid_amount,
  refund_amount,
  net_collected_amount,
  outstanding_amount,
  lead_to_appointment_rate,
  appointment_to_completed_rate,
  completed_to_signed_rate,
  signed_to_paid_rate,
  net_collected_per_lead,
  net_collected_per_completed_call,
  high_confidence_leads,
  medium_confidence_leads,
  low_confidence_leads,
  unknown_source_leads,
  multiple_source_leads,
  revenue_without_source_leads
FROM scored
ORDER BY
  net_collected_amount DESC,
  signed_contract_count DESC,
  completed_call_count DESC,
  lead_count DESC,
  source_name ASC
LIMIT :limit
"""

SOURCE_QUALITY_SQL_TEMPLATE = """
WITH scoped AS (
  SELECT
    COALESCE(NULLIF(BTRIM(dls.{source_column}), ''), 'Unknown') AS source_name,
    dls.source_confidence AS source_confidence,
    dls.has_missing_first_source AS has_missing_first_source,
    dls.has_missing_last_source AS has_missing_last_source,
    dls.has_orphaned_first_source_id AS has_orphaned_first_source_id,
    dls.has_orphaned_last_source_id AS has_orphaned_last_source_id,
    dls.has_unknown_source AS has_unknown_source,
    dls.has_multiple_sources AS has_multiple_sources,
    dls.has_revenue_without_source AS has_revenue_without_source,
    dls.missing_utm_source AS missing_utm_source,
    dls.missing_utm_campaign AS missing_utm_campaign,
    dls.missing_landing_page AS missing_landing_page,
    dls.missing_referrer AS missing_referrer,
    dls.completed_calls_missing_fathom_count AS completed_calls_missing_fathom_count,
    dls.net_collected_amount AS net_collected_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
totals AS (
  SELECT
    COUNT(*)::int AS total_leads,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS total_net_collected_amount,
    COUNT(*) FILTER (WHERE source_confidence = 'high')::int AS high_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'medium')::int AS medium_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'low')::int AS low_confidence_leads,
    COUNT(*) FILTER (WHERE has_unknown_source)::int AS unknown_source_leads,
    COUNT(*) FILTER (WHERE has_missing_first_source)::int AS missing_first_source_leads,
    COUNT(*) FILTER (WHERE has_missing_last_source)::int AS missing_last_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_first_source_id)::int AS orphaned_first_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_last_source_id)::int AS orphaned_last_source_leads,
    COUNT(*) FILTER (WHERE has_multiple_sources)::int AS multiple_source_leads,
    COUNT(*) FILTER (WHERE has_revenue_without_source)::int AS revenue_without_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_source)::int AS missing_utm_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_campaign)::int AS missing_utm_campaign_leads,
    COUNT(*) FILTER (WHERE missing_landing_page)::int AS missing_landing_page_leads,
    COUNT(*) FILTER (WHERE missing_referrer)::int AS missing_referrer_leads,
    COUNT(*) FILTER (WHERE completed_calls_missing_fathom_count > 0)::int
      AS leads_with_completed_calls_missing_fathom,
    COUNT(*) FILTER (
      WHERE source_confidence = 'low'
         OR has_unknown_source
         OR has_orphaned_first_source_id
         OR has_orphaned_last_source_id
         OR has_multiple_sources
    )::int AS issue_leads
  FROM scoped
),
overall AS (
  SELECT
    'overall' AS row_type,
    NULL::text AS source_name,
    total_leads AS lead_count,
    total_net_collected_amount AS net_collected_amount,
    high_confidence_leads,
    medium_confidence_leads,
    low_confidence_leads,
    unknown_source_leads,
    missing_first_source_leads,
    missing_last_source_leads,
    orphaned_first_source_leads,
    orphaned_last_source_leads,
    multiple_source_leads,
    revenue_without_source_leads,
    missing_utm_source_leads,
    missing_utm_campaign_leads,
    missing_landing_page_leads,
    missing_referrer_leads,
    leads_with_completed_calls_missing_fathom,
    issue_leads,
    ROUND(100.0 * issue_leads / NULLIF(total_leads, 0), 2) AS issue_lead_rate
  FROM totals
),
source_quality AS (
  SELECT
    'source' AS row_type,
    source_name,
    COUNT(*)::int AS lead_count,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COUNT(*) FILTER (WHERE source_confidence = 'high')::int AS high_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'medium')::int AS medium_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'low')::int AS low_confidence_leads,
    COUNT(*) FILTER (WHERE has_unknown_source)::int AS unknown_source_leads,
    COUNT(*) FILTER (WHERE has_missing_first_source)::int AS missing_first_source_leads,
    COUNT(*) FILTER (WHERE has_missing_last_source)::int AS missing_last_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_first_source_id)::int AS orphaned_first_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_last_source_id)::int AS orphaned_last_source_leads,
    COUNT(*) FILTER (WHERE has_multiple_sources)::int AS multiple_source_leads,
    COUNT(*) FILTER (WHERE has_revenue_without_source)::int AS revenue_without_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_source)::int AS missing_utm_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_campaign)::int AS missing_utm_campaign_leads,
    COUNT(*) FILTER (WHERE missing_landing_page)::int AS missing_landing_page_leads,
    COUNT(*) FILTER (WHERE missing_referrer)::int AS missing_referrer_leads,
    COUNT(*) FILTER (WHERE completed_calls_missing_fathom_count > 0)::int
      AS leads_with_completed_calls_missing_fathom,
    COUNT(*) FILTER (
      WHERE source_confidence = 'low'
         OR has_unknown_source
         OR has_orphaned_first_source_id
         OR has_orphaned_last_source_id
         OR has_multiple_sources
    )::int AS issue_leads
  FROM scoped
  GROUP BY source_name
),
ranked_sources AS (
  SELECT
    row_type,
    source_name,
    lead_count,
    net_collected_amount,
    high_confidence_leads,
    medium_confidence_leads,
    low_confidence_leads,
    unknown_source_leads,
    missing_first_source_leads,
    missing_last_source_leads,
    orphaned_first_source_leads,
    orphaned_last_source_leads,
    multiple_source_leads,
    revenue_without_source_leads,
    missing_utm_source_leads,
    missing_utm_campaign_leads,
    missing_landing_page_leads,
    missing_referrer_leads,
    leads_with_completed_calls_missing_fathom,
    issue_leads,
    ROUND(100.0 * issue_leads / NULLIF(lead_count, 0), 2) AS issue_lead_rate
  FROM source_quality
  ORDER BY
    issue_leads DESC,
    low_confidence_leads DESC,
    unknown_source_leads DESC,
    lead_count DESC,
    source_name ASC
  LIMIT :limit
)
SELECT
  row_type,
  source_name,
  lead_count,
  net_collected_amount,
  high_confidence_leads,
  medium_confidence_leads,
  low_confidence_leads,
  unknown_source_leads,
  missing_first_source_leads,
  missing_last_source_leads,
  orphaned_first_source_leads,
  orphaned_last_source_leads,
  multiple_source_leads,
  revenue_without_source_leads,
  missing_utm_source_leads,
  missing_utm_campaign_leads,
  missing_landing_page_leads,
  missing_referrer_leads,
  leads_with_completed_calls_missing_fathom,
  issue_leads,
  issue_lead_rate
FROM overall
UNION ALL
SELECT
  row_type,
  source_name,
  lead_count,
  net_collected_amount,
  high_confidence_leads,
  medium_confidence_leads,
  low_confidence_leads,
  unknown_source_leads,
  missing_first_source_leads,
  missing_last_source_leads,
  orphaned_first_source_leads,
  orphaned_last_source_leads,
  multiple_source_leads,
  revenue_without_source_leads,
  missing_utm_source_leads,
  missing_utm_campaign_leads,
  missing_landing_page_leads,
  missing_referrer_leads,
  leads_with_completed_calls_missing_fathom,
  issue_leads,
  issue_lead_rate
FROM ranked_sources
ORDER BY
  row_type ASC,
  issue_leads DESC,
  source_name ASC
"""

BUSINESS_CHANGE_SQL = """
WITH period_rows AS (
  SELECT
    'current' AS period_name,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:current_start_date AS date)
    AND dls.lead_created_at < CAST(:current_end_date AS date)
  UNION ALL
  SELECT
    'previous' AS period_name,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:previous_start_date AS date)
    AND dls.lead_created_at < CAST(:previous_end_date AS date)
),
period_totals AS (
  SELECT
    period_name,
    COUNT(*)::int AS lead_count,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(no_show_count), 0)::int AS no_show_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(gross_paid_amount), 0)::numeric(12,2) AS gross_paid_amount,
    COALESCE(SUM(refund_amount), 0)::numeric(12,2) AS refund_amount,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COALESCE(SUM(outstanding_amount), 0)::numeric(12,2) AS outstanding_amount,
    ROUND(100.0 * COALESCE(SUM(appointment_count), 0) / NULLIF(COUNT(*), 0), 2)
      AS lead_to_appointment_rate,
    ROUND(100.0 * COALESCE(SUM(completed_call_count), 0)
      / NULLIF(SUM(appointment_count), 0), 2) AS appointment_to_completed_rate,
    ROUND(100.0 * COALESCE(SUM(signed_contract_count), 0)
      / NULLIF(SUM(completed_call_count), 0), 2) AS completed_to_signed_rate,
    ROUND(100.0 * COALESCE(SUM(paid_payment_count), 0)
      / NULLIF(SUM(signed_contract_count), 0), 2) AS signed_to_paid_rate,
    ROUND(COALESCE(SUM(net_collected_amount), 0) / NULLIF(COUNT(*), 0), 2)
      AS net_collected_per_lead
  FROM period_rows
  GROUP BY period_name
),
pivoted AS (
  SELECT
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN lead_count END), 0) AS current_lead_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN lead_count END), 0) AS previous_lead_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN appointment_count END), 0)
      AS current_appointment_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN appointment_count END), 0)
      AS previous_appointment_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN completed_call_count END), 0)
      AS current_completed_call_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN completed_call_count END), 0)
      AS previous_completed_call_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN no_show_count END), 0)
      AS current_no_show_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN no_show_count END), 0)
      AS previous_no_show_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN signed_contract_count END), 0)
      AS current_signed_contract_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN signed_contract_count END), 0)
      AS previous_signed_contract_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN paid_payment_count END), 0)
      AS current_paid_payment_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN paid_payment_count END), 0)
      AS previous_paid_payment_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN gross_paid_amount END), 0)
      AS current_gross_paid_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN gross_paid_amount END), 0)
      AS previous_gross_paid_amount,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN refund_amount END), 0)
      AS current_refund_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN refund_amount END), 0)
      AS previous_refund_amount,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN net_collected_amount END), 0)
      AS current_net_collected_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN net_collected_amount END), 0)
      AS previous_net_collected_amount,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN outstanding_amount END), 0)
      AS current_outstanding_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN outstanding_amount END), 0)
      AS previous_outstanding_amount,
    MAX(CASE WHEN period_name = 'current' THEN lead_to_appointment_rate END)
      AS current_lead_to_appointment_rate,
    MAX(CASE WHEN period_name = 'previous' THEN lead_to_appointment_rate END)
      AS previous_lead_to_appointment_rate,
    MAX(CASE WHEN period_name = 'current' THEN appointment_to_completed_rate END)
      AS current_appointment_to_completed_rate,
    MAX(CASE WHEN period_name = 'previous' THEN appointment_to_completed_rate END)
      AS previous_appointment_to_completed_rate,
    MAX(CASE WHEN period_name = 'current' THEN completed_to_signed_rate END)
      AS current_completed_to_signed_rate,
    MAX(CASE WHEN period_name = 'previous' THEN completed_to_signed_rate END)
      AS previous_completed_to_signed_rate,
    MAX(CASE WHEN period_name = 'current' THEN signed_to_paid_rate END)
      AS current_signed_to_paid_rate,
    MAX(CASE WHEN period_name = 'previous' THEN signed_to_paid_rate END)
      AS previous_signed_to_paid_rate,
    MAX(CASE WHEN period_name = 'current' THEN net_collected_per_lead END)
      AS current_net_collected_per_lead,
    MAX(CASE WHEN period_name = 'previous' THEN net_collected_per_lead END)
      AS previous_net_collected_per_lead
  FROM period_totals
)
SELECT
  metric_name,
  current_value,
  previous_value,
  current_value - previous_value AS absolute_change,
  CASE
    WHEN previous_value = 0 THEN NULL
    ELSE ROUND(100.0 * (current_value - previous_value) / previous_value, 2)
  END AS percentage_change
FROM pivoted,
LATERAL (
  VALUES
    ('lead_count', current_lead_count::numeric, previous_lead_count::numeric),
    ('appointment_count', current_appointment_count::numeric, previous_appointment_count::numeric),
    (
      'completed_call_count',
      current_completed_call_count::numeric,
      previous_completed_call_count::numeric
    ),
    ('no_show_count', current_no_show_count::numeric, previous_no_show_count::numeric),
    (
      'signed_contract_count',
      current_signed_contract_count::numeric,
      previous_signed_contract_count::numeric
    ),
    (
      'paid_payment_count',
      current_paid_payment_count::numeric,
      previous_paid_payment_count::numeric
    ),
    ('gross_paid_amount', current_gross_paid_amount::numeric, previous_gross_paid_amount::numeric),
    ('refund_amount', current_refund_amount::numeric, previous_refund_amount::numeric),
    (
      'net_collected_amount',
      current_net_collected_amount::numeric,
      previous_net_collected_amount::numeric
    ),
    (
      'outstanding_amount',
      current_outstanding_amount::numeric,
      previous_outstanding_amount::numeric
    ),
    (
      'lead_to_appointment_rate',
      current_lead_to_appointment_rate::numeric,
      previous_lead_to_appointment_rate::numeric
    ),
    (
      'appointment_to_completed_rate',
      current_appointment_to_completed_rate::numeric,
      previous_appointment_to_completed_rate::numeric
    ),
    (
      'completed_to_signed_rate',
      current_completed_to_signed_rate::numeric,
      previous_completed_to_signed_rate::numeric
    ),
    (
      'signed_to_paid_rate',
      current_signed_to_paid_rate::numeric,
      previous_signed_to_paid_rate::numeric
    ),
    (
      'net_collected_per_lead',
      current_net_collected_per_lead::numeric,
      previous_net_collected_per_lead::numeric
    )
) AS metrics(metric_name, current_value, previous_value)
ORDER BY
  ABS(current_value - previous_value) DESC NULLS LAST,
  metric_name ASC
"""


def get_diagnostic_funnel_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
        params = {
            "org_id": clean_org_id,
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
        }
        rows = _query_records(FUNNEL_SQL, params, max_rows=100)
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_funnel_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": len(rows),
                "period": {
                    "start_date": periods["current_start_date"],
                    "end_date": periods["current_end_date"],
                    "anchor_date": periods["period_anchor_date"],
                    "date_field": "lead_created_at",
                },
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_funnel_snapshot", exc)


def get_diagnostic_source_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 10,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
        safe_limit = _safe_limit(limit)
        source_column = _source_column(source_basis)
        sql = SOURCE_SNAPSHOT_SQL_TEMPLATE.format(source_column=source_column)
        params = {
            "org_id": clean_org_id,
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "limit": safe_limit,
        }
        rows = _query_records(sql, params, max_rows=safe_limit)
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_source_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": len(rows),
                "source_basis": str(source_basis or "first").strip().lower(),
                "period": {
                    "start_date": periods["current_start_date"],
                    "end_date": periods["current_end_date"],
                    "anchor_date": periods["period_anchor_date"],
                    "date_field": "lead_created_at",
                },
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_source_snapshot", exc)


def get_diagnostic_source_quality_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 20,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
        safe_limit = _safe_limit(limit, default=20)
        source_column = _source_column(source_basis)
        sql = SOURCE_QUALITY_SQL_TEMPLATE.format(source_column=source_column)
        params = {
            "org_id": clean_org_id,
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "limit": safe_limit,
        }
        rows = _query_records(sql, params, max_rows=safe_limit + 1)
        overall = next((row for row in rows if row.get("row_type") == "overall"), None)
        sources = [row for row in rows if row.get("row_type") == "source"]
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_source_quality_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": len(rows),
                "source_basis": str(source_basis or "first").strip().lower(),
                "period": {
                    "start_date": periods["current_start_date"],
                    "end_date": periods["current_end_date"],
                    "anchor_date": periods["period_anchor_date"],
                    "date_field": "lead_created_at",
                },
                "overall": overall,
                "sources": sources,
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_source_quality_snapshot", exc)


def get_diagnostic_business_change_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(
            clean_org_id,
            current_start_date,
            current_end_date,
            previous_start_date,
            previous_end_date,
        )
        params = {
            "org_id": clean_org_id,
            "current_start_date": periods["current_start_date"],
            "current_end_date": periods["current_end_date"],
            "previous_start_date": periods["previous_start_date"],
            "previous_end_date": periods["previous_end_date"],
        }
        rows = _query_records(BUSINESS_CHANGE_SQL, params, max_rows=100)
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_business_change_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": len(rows),
                "periods": {
                    "current": {
                        "start_date": periods["current_start_date"],
                        "end_date": periods["current_end_date"],
                        "anchor_date": periods["period_anchor_date"],
                        "date_field": "lead_created_at",
                    },
                    "previous": {
                        "start_date": periods["previous_start_date"],
                        "end_date": periods["previous_end_date"],
                        "anchor_date": periods["period_anchor_date"],
                        "date_field": "lead_created_at",
                    },
                },
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_business_change_snapshot", exc)


def _get_diagnostic_funnel_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
) -> str:
    """Return funnel-stage evidence from diagnostic_lead_snapshot.

    Dates use lead_created_at cohort logic. If org_id is omitted, the tool uses
    HERMON_DEFAULT_CLERK_ORG_ID.
    """

    try:
        return _json_response(
            get_diagnostic_funnel_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_funnel_snapshot", exc)


def _get_diagnostic_source_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 10,
) -> str:
    """Return source performance evidence from diagnostic_lead_snapshot.

    source_basis must be first or last. Dates use lead_created_at cohort logic.
    """

    try:
        return _json_response(
            get_diagnostic_source_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                source_basis=source_basis,
                limit=limit,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_source_snapshot", exc)


def _get_diagnostic_source_quality_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 20,
) -> str:
    """Return source trust and data-quality evidence from diagnostic_lead_snapshot.

    source_basis must be first or last. Dates use lead_created_at cohort logic.
    """

    try:
        return _json_response(
            get_diagnostic_source_quality_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                source_basis=source_basis,
                limit=limit,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_source_quality_snapshot", exc)


def _get_diagnostic_business_change_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
) -> str:
    """Return current-vs-previous business change evidence from the snapshot.

    Dates use lead_created_at cohort logic.
    """

    try:
        return _json_response(
            get_diagnostic_business_change_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                previous_start_date=previous_start_date,
                previous_end_date=previous_end_date,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_business_change_snapshot", exc)


get_diagnostic_funnel_snapshot_tool = tool("get_diagnostic_funnel_snapshot")(
    _get_diagnostic_funnel_snapshot_tool
)
get_diagnostic_source_snapshot_tool = tool("get_diagnostic_source_snapshot")(
    _get_diagnostic_source_snapshot_tool
)
get_diagnostic_source_quality_snapshot_tool = tool("get_diagnostic_source_quality_snapshot")(
    _get_diagnostic_source_quality_snapshot_tool
)
get_diagnostic_business_change_snapshot_tool = tool("get_diagnostic_business_change_snapshot")(
    _get_diagnostic_business_change_snapshot_tool
)

DIAGNOSTIC_TOOLS = [
    get_diagnostic_funnel_snapshot_tool,
    get_diagnostic_source_snapshot_tool,
    get_diagnostic_source_quality_snapshot_tool,
    get_diagnostic_business_change_snapshot_tool,
]
