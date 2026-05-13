I checked the latest snapshot design and repo pattern. Your snapshot is explicitly meant for controlled diagnostic tools and supports funnel/source/source-quality diagnostics, but not true payment-period revenue trends, revenue by UTM, ad spend, ROAS, or multi-touch attribution.   Your current repo already has a tool pattern using `app/tools`, `get_db()`, and LangChain `tool`. 

````markdown
# Codex Task: Build Read-Only Diagnostic Tools for `diagnostic_lead_snapshot`

## Goal

Create read-only diagnostic tools over the existing `diagnostic_lead_snapshot` table.

These tools must support the future `diagnostic_analytics` agent without allowing the LLM to generate free-form SQL.

Build only the tool layer now.

Do not build the full diagnostic agent yet.
Do not build diagnostic text extraction yet.
Do not use raw notes, raw Fathom text, raw form answers, raw payloads, API keys, credentials, webhook payloads, or URLs.
Do not add write/update/delete logic.
Do not refresh or rebuild `diagnostic_lead_snapshot` from these tools.

---

## Required Tools

Create these 4 tools:

```text
get_diagnostic_funnel_snapshot
get_diagnostic_source_snapshot
get_diagnostic_source_quality_snapshot
get_diagnostic_business_change_snapshot
````

All tools must read only from:

```text
diagnostic_lead_snapshot
```

Do not join source tables inside these tools.

---

## Required Files

Create:

```text
app/tools/diagnostic_tools.py
```

Update:

```text
app/tools/__init__.py
app/db/postgres.py
```

Do not modify SQL analytics skills yet.
Do not modify Lead 360 yet.
Do not wire orchestrator yet unless explicitly asked later.

---

## Important DB Safety Update

In `app/db/postgres.py`, add this table to `BUSINESS_TABLES`:

```python
"diagnostic_lead_snapshot",
```

Reason:

Every diagnostic tool query must be tenant-scoped by:

```sql
WHERE dls.clerk_org_id = :org_id
```

Adding the table to `BUSINESS_TABLES` keeps the existing org-scope validation behavior consistent.

---

## Tool Design Rules

Each tool must:

1. Use `get_db().query_records(...)`.
2. Use only SELECT/WITH queries.
3. Always filter by `dls.clerk_org_id = :org_id`.
4. Never use `SELECT *`.
5. Never use `dls.*` or any alias wildcard.
6. Never expose raw IDs unless necessary for technical debugging.
7. Never return email, phone, raw text, URLs, payloads, or provider IDs.
8. Return JSON-serializable dictionaries.
9. Include a clear `scope_note`.
10. Include `status = "success"` or `status = "error"`.
11. Use `HERMON_DEFAULT_CLERK_ORG_ID` when `org_id` is omitted.
12. Use deterministic sorting.
13. Use safe hardcoded SQL templates only.
14. Do not allow arbitrary SQL input.

---

## Period Logic

These tools operate on lead cohorts using:

```sql
dls.lead_created_at
```

This means:

```text
Metrics are lifetime outcomes for leads created in the selected period.
```

Example:

If current period is May 2026, then `net_collected_amount` means lifetime net collected revenue from leads created in May 2026, not necessarily money collected during May 2026.

Add this warning in every tool response:

```text
This diagnostic snapshot uses lead_created_at cohort logic. Revenue and payment fields are lifetime outcomes for those leads, not true payment-period revenue.
```

Do not claim exact payment-period revenue trends from this snapshot.

## Money Unit Rules

All money fields read from `diagnostic_lead_snapshot` are already business-facing major-unit EUR values.

Do not divide these fields by `100` in diagnostic tool SQL, diagnostic tool responses, or future diagnostic agent prompts:

```text
signed_contract_value
gross_paid_amount
refund_amount
net_collected_amount
outstanding_amount
overdue_amount
net_collected_per_lead
net_collected_per_completed_call
current_gross_paid_amount
previous_gross_paid_amount
current_refund_amount
previous_refund_amount
current_net_collected_amount
previous_net_collected_amount
current_outstanding_amount
previous_outstanding_amount
```

The source revenue tables use minor units, but `diagnostic_lead_snapshot` receives the already-converted major-unit values during the snapshot build. Dividing snapshot values again would understate money by 100x.

---

## Date Inputs

The single-period tools should accept:

```python
org_id: str | None = None
current_start_date: str | None = None
current_end_date: str | None = None
```

This applies to:

```text
get_diagnostic_funnel_snapshot
get_diagnostic_source_snapshot
get_diagnostic_source_quality_snapshot
```

The period-comparison tool should accept:

```python
org_id: str | None = None
current_start_date: str | None = None
current_end_date: str | None = None
previous_start_date: str | None = None
previous_end_date: str | None = None
```

Dates must be strings in `YYYY-MM-DD` format.

If dates are omitted, use this default:

```text
anchor date = max(diagnostic_lead_snapshot.lead_created_at)::date for the selected org
current period = rolling 6-month window ending at anchor date + 1 day
previous period = rolling 6-month window immediately before the current period
```

Implementation must use a fixed read-only SQL query to find the snapshot anchor date. Do not use `date.today()` for MVP defaults because the static demo snapshot can lag behind the real calendar.

If the selected org has no rows in `diagnostic_lead_snapshot`, return `status = "error"` with a clear message instead of returning an empty default period.

---

## Source Basis Input

For source-based tools, accept:

```python
source_basis: str = "first"
```

Allowed values:

```text
first
last
```

Mapping:

```text
first -> first_source
last -> last_source
```

Do not allow arbitrary column names.

If invalid value is passed, return status error.

---

## Limit Input

For source ranking tools, accept:

```python
limit: int = 10
```

Rules:

```text
minimum = 1
maximum = 50
default = 10
```

Clamp the limit safely in Python.

---

# Implementation Script

Create `app/tools/diagnostic_tools.py` with this structure.

```python
"""Read-only diagnostic tools over diagnostic_lead_snapshot.

These tools provide controlled evidence for the future diagnostic analytics agent.
They intentionally use fixed SQL templates instead of LLM-generated SQL.
"""

from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any

from langchain.tools import tool

from app.config import get_sql_agent_settings
from app.db import get_db


SCOPE_NOTE = (
    "This diagnostic snapshot uses lead_created_at cohort logic. "
    "Revenue and payment fields are lifetime outcomes for leads created in the selected period, "
    "not true payment-period revenue."
)

SUPPORTED_SOURCE_BASIS = {
    "first": "first_source",
    "last": "last_source",
}


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


def _parse_date(value: str | None) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


DEFAULT_LOOKBACK_MONTHS = 6


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    target_year = month_index // 12
    target_month = month_index % 12 + 1
    target_day = min(value.day, monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def _snapshot_date_bounds(org_id: str) -> dict[str, date]:
    rows = _query_records(SNAPSHOT_DATE_BOUNDS_SQL, {"org_id": org_id}, max_rows=1)
    if not rows or rows[0].get("max_lead_created_date") is None:
        raise ValueError(
            "diagnostic_lead_snapshot has no rows for this org, so default periods cannot be derived."
        )

    min_lead_created_date = _parse_date(str(rows[0]["min_lead_created_date"]))
    max_lead_created_date = _parse_date(str(rows[0]["max_lead_created_date"]))
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


def _query_records(sql: str, params: dict[str, Any], *, max_rows: int = 200) -> list[dict[str, Any]]:
    return get_db().query_records(sql, params=params, max_rows=max_rows)


def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def _error_response(tool_name: str, error: Exception) -> str:
    return _json_response(
        {
            "status": "error",
            "tool": tool_name,
            "error": str(error),
        }
    )


FUNNEL_SQL = """
WITH scoped AS (
  SELECT
    dls.funnel_stage,
    dls.conversion_outcome,
    dls.first_source,
    dls.last_source,
    dls.lead_created_at,
    dls.appointment_count,
    dls.completed_call_count,
    dls.no_show_count,
    dls.signed_contract_count,
    dls.paid_payment_count,
    dls.gross_paid_amount,
    dls.refund_amount,
    dls.net_collected_amount,
    dls.outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :start_date
    AND dls.lead_created_at < :end_date
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
    dls.source_confidence,
    dls.lead_created_at,
    dls.appointment_count,
    dls.completed_call_count,
    dls.no_show_count,
    dls.signed_contract_count,
    dls.paid_payment_count,
    dls.gross_paid_amount,
    dls.refund_amount,
    dls.net_collected_amount,
    dls.outstanding_amount,
    dls.has_unknown_source,
    dls.has_multiple_sources,
    dls.has_revenue_without_source
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :start_date
    AND dls.lead_created_at < :end_date
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
    ROUND(net_collected_amount / NULLIF(completed_call_count, 0), 2) AS net_collected_per_completed_call
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
    dls.source_confidence,
    dls.has_missing_first_source,
    dls.has_missing_last_source,
    dls.has_orphaned_first_source_id,
    dls.has_orphaned_last_source_id,
    dls.has_unknown_source,
    dls.has_multiple_sources,
    dls.has_revenue_without_source,
    dls.missing_utm_source,
    dls.missing_utm_campaign,
    dls.missing_landing_page,
    dls.missing_referrer,
    dls.completed_calls_missing_fathom_count,
    dls.lead_created_at,
    dls.net_collected_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :start_date
    AND dls.lead_created_at < :end_date
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
    COUNT(*) FILTER (WHERE completed_calls_missing_fathom_count > 0)::int AS leads_with_completed_calls_missing_fathom,
    COUNT(*) FILTER (
      WHERE source_confidence = 'low'
         OR has_unknown_source
         OR has_orphaned_first_source_id
         OR has_orphaned_last_source_id
         OR has_multiple_sources
    )::int AS issue_leads
  FROM scoped
),
source_quality AS (
  SELECT
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
    COUNT(*) FILTER (
      WHERE source_confidence = 'low'
         OR has_unknown_source
         OR has_orphaned_first_source_id
         OR has_orphaned_last_source_id
         OR has_multiple_sources
    )::int AS issue_leads,
    ROUND(
      100.0 * COUNT(*) FILTER (
        WHERE source_confidence = 'low'
           OR has_unknown_source
           OR has_orphaned_first_source_id
           OR has_orphaned_last_source_id
           OR has_multiple_sources
      ) / NULLIF(COUNT(*), 0),
      2
    ) AS issue_rate
  FROM scoped
  GROUP BY source_name
),
ranked_source_quality AS (
  SELECT
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
    issue_rate,
    ROW_NUMBER() OVER (
      ORDER BY
        issue_rate DESC NULLS LAST,
        net_collected_amount DESC,
        lead_count DESC,
        source_name ASC
    ) AS source_rank
  FROM source_quality
)
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
  ROUND(100.0 * issue_leads / NULLIF(total_leads, 0), 2) AS issue_rate
FROM totals

UNION ALL

SELECT
  'source' AS row_type,
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
  NULL::int AS missing_utm_source_leads,
  NULL::int AS missing_utm_campaign_leads,
  NULL::int AS missing_landing_page_leads,
  NULL::int AS missing_referrer_leads,
  NULL::int AS leads_with_completed_calls_missing_fathom,
  issue_rate
FROM ranked_source_quality
WHERE source_rank <= :limit

ORDER BY
  row_type ASC,
  issue_rate DESC NULLS LAST,
  net_collected_amount DESC,
  lead_count DESC,
  source_name ASC
"""


BUSINESS_CHANGE_SQL = """
WITH period_rows AS (
  SELECT
    'current' AS period_name,
    dls.appointment_count,
    dls.completed_call_count,
    dls.no_show_count,
    dls.signed_contract_count,
    dls.paid_payment_count,
    dls.gross_paid_amount,
    dls.refund_amount,
    dls.net_collected_amount,
    dls.outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :current_start_date
    AND dls.lead_created_at < :current_end_date

  UNION ALL

  SELECT
    'previous' AS period_name,
    dls.appointment_count,
    dls.completed_call_count,
    dls.no_show_count,
    dls.signed_contract_count,
    dls.paid_payment_count,
    dls.gross_paid_amount,
    dls.refund_amount,
    dls.net_collected_amount,
    dls.outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :previous_start_date
    AND dls.lead_created_at < :previous_end_date
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
    ROUND(100.0 * COALESCE(SUM(appointment_count), 0) / NULLIF(COUNT(*), 0), 2) AS lead_to_appointment_rate,
    ROUND(100.0 * COALESCE(SUM(completed_call_count), 0) / NULLIF(SUM(appointment_count), 0), 2) AS appointment_to_completed_rate,
    ROUND(100.0 * COALESCE(SUM(signed_contract_count), 0) / NULLIF(SUM(completed_call_count), 0), 2) AS completed_to_signed_rate,
    ROUND(100.0 * COALESCE(SUM(paid_payment_count), 0) / NULLIF(SUM(signed_contract_count), 0), 2) AS signed_to_paid_rate,
    ROUND(COALESCE(SUM(net_collected_amount), 0) / NULLIF(COUNT(*), 0), 2) AS net_collected_per_lead
  FROM period_rows
  GROUP BY period_name
),
pivoted AS (
  SELECT
    MAX(CASE WHEN period_name = 'current' THEN lead_count END) AS current_lead_count,
    MAX(CASE WHEN period_name = 'previous' THEN lead_count END) AS previous_lead_count,

    MAX(CASE WHEN period_name = 'current' THEN appointment_count END) AS current_appointment_count,
    MAX(CASE WHEN period_name = 'previous' THEN appointment_count END) AS previous_appointment_count,

    MAX(CASE WHEN period_name = 'current' THEN completed_call_count END) AS current_completed_call_count,
    MAX(CASE WHEN period_name = 'previous' THEN completed_call_count END) AS previous_completed_call_count,

    MAX(CASE WHEN period_name = 'current' THEN no_show_count END) AS current_no_show_count,
    MAX(CASE WHEN period_name = 'previous' THEN no_show_count END) AS previous_no_show_count,

    MAX(CASE WHEN period_name = 'current' THEN signed_contract_count END) AS current_signed_contract_count,
    MAX(CASE WHEN period_name = 'previous' THEN signed_contract_count END) AS previous_signed_contract_count,

    MAX(CASE WHEN period_name = 'current' THEN paid_payment_count END) AS current_paid_payment_count,
    MAX(CASE WHEN period_name = 'previous' THEN paid_payment_count END) AS previous_paid_payment_count,

    MAX(CASE WHEN period_name = 'current' THEN net_collected_amount END) AS current_net_collected_amount,
    MAX(CASE WHEN period_name = 'previous' THEN net_collected_amount END) AS previous_net_collected_amount,

    MAX(CASE WHEN period_name = 'current' THEN outstanding_amount END) AS current_outstanding_amount,
    MAX(CASE WHEN period_name = 'previous' THEN outstanding_amount END) AS previous_outstanding_amount,

    MAX(CASE WHEN period_name = 'current' THEN lead_to_appointment_rate END) AS current_lead_to_appointment_rate,
    MAX(CASE WHEN period_name = 'previous' THEN lead_to_appointment_rate END) AS previous_lead_to_appointment_rate,

    MAX(CASE WHEN period_name = 'current' THEN appointment_to_completed_rate END) AS current_appointment_to_completed_rate,
    MAX(CASE WHEN period_name = 'previous' THEN appointment_to_completed_rate END) AS previous_appointment_to_completed_rate,

    MAX(CASE WHEN period_name = 'current' THEN completed_to_signed_rate END) AS current_completed_to_signed_rate,
    MAX(CASE WHEN period_name = 'previous' THEN completed_to_signed_rate END) AS previous_completed_to_signed_rate,

    MAX(CASE WHEN period_name = 'current' THEN signed_to_paid_rate END) AS current_signed_to_paid_rate,
    MAX(CASE WHEN period_name = 'previous' THEN signed_to_paid_rate END) AS previous_signed_to_paid_rate,

    MAX(CASE WHEN period_name = 'current' THEN net_collected_per_lead END) AS current_net_collected_per_lead,
    MAX(CASE WHEN period_name = 'previous' THEN net_collected_per_lead END) AS previous_net_collected_per_lead
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
    ('completed_call_count', current_completed_call_count::numeric, previous_completed_call_count::numeric),
    ('no_show_count', current_no_show_count::numeric, previous_no_show_count::numeric),
    ('signed_contract_count', current_signed_contract_count::numeric, previous_signed_contract_count::numeric),
    ('paid_payment_count', current_paid_payment_count::numeric, previous_paid_payment_count::numeric),
    ('net_collected_amount', current_net_collected_amount::numeric, previous_net_collected_amount::numeric),
    ('outstanding_amount', current_outstanding_amount::numeric, previous_outstanding_amount::numeric),
    ('lead_to_appointment_rate', current_lead_to_appointment_rate::numeric, previous_lead_to_appointment_rate::numeric),
    ('appointment_to_completed_rate', current_appointment_to_completed_rate::numeric, previous_appointment_to_completed_rate::numeric),
    ('completed_to_signed_rate', current_completed_to_signed_rate::numeric, previous_completed_to_signed_rate::numeric),
    ('signed_to_paid_rate', current_signed_to_paid_rate::numeric, previous_signed_to_paid_rate::numeric),
    ('net_collected_per_lead', current_net_collected_per_lead::numeric, previous_net_collected_per_lead::numeric)
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
    clean_org_id = _default_org_id(org_id)
    periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
    params = {
        "org_id": clean_org_id,
        "start_date": periods["current_start_date"],
        "end_date": periods["current_end_date"],
    }
    rows = _query_records(FUNNEL_SQL, params, max_rows=100)
    return {
        "status": "success",
        "tool": "get_diagnostic_funnel_snapshot",
        "scope_note": SCOPE_NOTE,
        "period": {
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "anchor_date": periods["period_anchor_date"],
            "date_field": "lead_created_at",
        },
        "rows": rows,
    }


def get_diagnostic_source_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 10,
) -> dict[str, Any]:
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
    return {
        "status": "success",
        "tool": "get_diagnostic_source_snapshot",
        "scope_note": SCOPE_NOTE,
        "source_basis": source_basis,
        "period": {
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "anchor_date": periods["period_anchor_date"],
            "date_field": "lead_created_at",
        },
        "rows": rows,
    }


def get_diagnostic_source_quality_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 20,
) -> dict[str, Any]:
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
    # The SQL returns one overall row plus up to safe_limit source rows.
    rows = _query_records(sql, params, max_rows=safe_limit + 1)
    return {
        "status": "success",
        "tool": "get_diagnostic_source_quality_snapshot",
        "scope_note": SCOPE_NOTE,
        "source_basis": source_basis,
        "period": {
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "anchor_date": periods["period_anchor_date"],
            "date_field": "lead_created_at",
        },
        "rows": rows,
    }


def get_diagnostic_business_change_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
) -> dict[str, Any]:
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
    return {
        "status": "success",
        "tool": "get_diagnostic_business_change_snapshot",
        "scope_note": SCOPE_NOTE,
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


def _get_diagnostic_funnel_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
) -> str:
    """Return funnel-stage evidence from diagnostic_lead_snapshot.

    Use this for questions like:
    - Where are we losing people in the funnel?
    - Why are leads not converting?
    - Why are leads increasing but revenue is not?

    Dates use lead_created_at cohort logic.
    """
    try:
        return _json_response(
            get_diagnostic_funnel_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
            )
        )
    except Exception as exc:
        return _error_response("get_diagnostic_funnel_snapshot", exc)


def _get_diagnostic_source_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 10,
) -> str:
    """Return source performance evidence from diagnostic_lead_snapshot.

    Use this for questions like:
    - Which source looks good but may be misleading?
    - Which source has high lead volume but low paid revenue?
    - Which source creates booked calls but not sales?

    source_basis must be first or last.
    Dates use lead_created_at cohort logic.
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
    except Exception as exc:
        return _error_response("get_diagnostic_source_snapshot", exc)


def _get_diagnostic_source_quality_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 20,
) -> str:
    """Return source trust and data-quality evidence from diagnostic_lead_snapshot.

    Use this for questions like:
    - Can we trust source performance?
    - Can we trust the revenue-by-source answer?
    - Why is source attribution incomplete?

    source_basis must be first or last.
    Dates use lead_created_at cohort logic.
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
    except Exception as exc:
        return _error_response("get_diagnostic_source_quality_snapshot", exc)


def _get_diagnostic_business_change_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
) -> str:
    """Return current-vs-previous business change evidence from diagnostic_lead_snapshot.

    Use this for questions like:
    - What changed this month?
    - Why are leads increasing but revenue is not?
    - What is the biggest change in the funnel?

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
    except Exception as exc:
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
```

---

## Update `app/tools/__init__.py`

Add imports:

```python
from app.tools.diagnostic_tools import (
    DIAGNOSTIC_TOOLS,
    get_diagnostic_business_change_snapshot,
    get_diagnostic_business_change_snapshot_tool,
    get_diagnostic_funnel_snapshot,
    get_diagnostic_funnel_snapshot_tool,
    get_diagnostic_source_quality_snapshot,
    get_diagnostic_source_quality_snapshot_tool,
    get_diagnostic_source_snapshot,
    get_diagnostic_source_snapshot_tool,
)
```

Add these to `__all__`:

```python
"DIAGNOSTIC_TOOLS",
"get_diagnostic_business_change_snapshot",
"get_diagnostic_business_change_snapshot_tool",
"get_diagnostic_funnel_snapshot",
"get_diagnostic_funnel_snapshot_tool",
"get_diagnostic_source_quality_snapshot",
"get_diagnostic_source_quality_snapshot_tool",
"get_diagnostic_source_snapshot",
"get_diagnostic_source_snapshot_tool",
```

---

## Tool Selection Guidance For Future Diagnostic Agent

Later, the diagnostic agent should use tools like this:

```text
Question: Where are we losing people in the funnel?
Tool: get_diagnostic_funnel_snapshot

Question: Why are leads increasing but revenue is not?
Tools:
1. get_diagnostic_business_change_snapshot
2. get_diagnostic_funnel_snapshot
3. get_diagnostic_source_snapshot if source-level explanation is needed

Question: Which source looks good but may be misleading?
Tools:
1. get_diagnostic_source_snapshot
2. get_diagnostic_source_quality_snapshot

Question: Can we trust source performance?
Tool:
1. get_diagnostic_source_quality_snapshot
```

---

## Important Limitations To Keep In Tool Responses

Every tool response must keep this limitation clear:

```text
This diagnostic snapshot uses lead_created_at cohort logic. Revenue and payment fields are lifetime outcomes for leads created in the selected period, not true payment-period revenue.
```

Do not answer these from diagnostic snapshot tools:

```text
true payment-period revenue trend
exact revenue collected last month by payment date
exact refund-period trend
revenue by UTM campaign
revenue by landing page
revenue by referrer
revenue by provider form
revenue by form answer
ad spend
ROAS
cost per lead
cost per appointment
cost per sale
multi-touch attribution
scientific attribution
Facebook Ads ROAS
YouTube video attribution
```

---

## Minimum Tests

Add simple tests or manual checks for plain Python functions.

Test:

```python
get_diagnostic_funnel_snapshot(org_id="ORG_ID")
get_diagnostic_source_snapshot(org_id="ORG_ID", source_basis="first", limit=5)
get_diagnostic_source_quality_snapshot(org_id="ORG_ID", source_basis="first", limit=5)
get_diagnostic_business_change_snapshot(org_id="ORG_ID")
```

Expected:

```text
status = success
scope_note exists
rows is a list
all SQL queries include dls.clerk_org_id = :org_id
no SQL contains SELECT *
no SQL contains dls.* or alias.*
no write SQL is used
invalid source_basis returns status error from tool wrapper
default periods use MAX(lead_created_at) from diagnostic_lead_snapshot, not date.today()
default current period returns non-empty rows for the static demo org
source-quality returns 1 overall row plus up to limit source rows
```

---

## Completion Criteria

Task is complete only when:

```text
1. app/tools/diagnostic_tools.py exists.
2. DIAGNOSTIC_TOOLS contains exactly 4 tools.
3. app/tools/__init__.py exports the tools.
4. diagnostic_lead_snapshot is added to BUSINESS_TABLES in app/db/postgres.py.
5. All diagnostic tool SQL is read-only.
6. All diagnostic tool SQL is tenant-scoped.
7. No tool accepts arbitrary SQL.
8. No tool reads raw text or sensitive fields.
9. Tool responses include scope_note.
10. No diagnostic tool SQL uses `SELECT *`, `dls.*`, or alias wildcards.
11. Default date windows cover the last 6 months anchored to max snapshot lead_created_at.
12. Source-quality output returns the overall row without consuming the source limit.
13. Basic function-level tests/manual calls pass.
```

```

After Codex builds this, the next step is `diagnostic_analytics.md` + `app/agents/diagnostic_agent/builder.py`, then replace the current static diagnostic unsupported branch in `orchestrator.py`.
```
