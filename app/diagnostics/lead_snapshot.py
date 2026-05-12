"""One-time diagnostic lead snapshot builder.

This module intentionally uses write access and must not be exposed through the
chatbot or read-only SQL tools. It creates and builds a static demo snapshot for
one selected organization.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from app.config import get_database_settings


class DiagnosticSnapshotBuildError(RuntimeError):
    """Raised when the one-time diagnostic snapshot build cannot complete."""


@dataclass(frozen=True)
class DiagnosticSnapshotBuildSummary:
    organization_id: str
    force: bool
    rows_deleted: int
    rows_inserted: int
    snapshot_built_at: str | None
    duration_seconds: float
    validation_status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "force": self.force,
            "rows_deleted": self.rows_deleted,
            "rows_inserted": self.rows_inserted,
            "snapshot_built_at": self.snapshot_built_at,
            "duration_seconds": self.duration_seconds,
            "validation_status": self.validation_status,
        }


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS diagnostic_lead_snapshot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_org_id text NOT NULL,
  lead_id uuid NOT NULL,
  lead_created_at timestamptz,
  lead_updated_at timestamptz,
  snapshot_built_at timestamptz NOT NULL DEFAULT now(),

  current_status_id uuid,
  current_status_name text,
  current_status_role text,
  assigned_to text,
  setter_id text,
  next_touch_point_at timestamptz,
  next_touch_point_type text,
  is_overdue_followup boolean NOT NULL DEFAULT false,
  is_missing_next_touchpoint boolean NOT NULL DEFAULT false,

  lead_source_enum text,
  first_source_id uuid,
  first_source text,
  last_source_id uuid,
  last_source text,
  source_changed boolean NOT NULL DEFAULT false,
  source_confidence text NOT NULL DEFAULT 'low',
  source_quality_flags jsonb NOT NULL DEFAULT '[]'::jsonb,

  opt_in_count integer NOT NULL DEFAULT 0,
  first_opt_in_at timestamptz,
  latest_opt_in_at timestamptz,
  first_opt_in_source text,
  latest_opt_in_source text,
  first_provider_form_name text,
  latest_provider_form_name text,
  first_utm_source text,
  first_utm_medium text,
  first_utm_campaign text,
  first_landing_page text,
  first_referrer text,
  latest_utm_source text,
  latest_utm_medium text,
  latest_utm_campaign text,
  latest_landing_page text,
  latest_referrer text,
  has_traffic_attribution boolean NOT NULL DEFAULT false,
  missing_utm_source boolean NOT NULL DEFAULT false,
  missing_utm_campaign boolean NOT NULL DEFAULT false,
  missing_landing_page boolean NOT NULL DEFAULT false,
  missing_referrer boolean NOT NULL DEFAULT false,
  has_form_answers boolean NOT NULL DEFAULT false,
  opt_in_answer_count integer NOT NULL DEFAULT 0,

  appointment_count integer NOT NULL DEFAULT 0,
  past_appointment_count integer NOT NULL DEFAULT 0,
  upcoming_appointment_count integer NOT NULL DEFAULT 0,
  past_non_no_show_appointment_count integer NOT NULL DEFAULT 0,
  completed_call_count integer NOT NULL DEFAULT 0,
  no_show_count integer NOT NULL DEFAULT 0,
  cancelled_appointment_count integer NOT NULL DEFAULT 0,
  first_appointment_at timestamptz,
  latest_appointment_at timestamptz,
  latest_completed_call_at timestamptz,
  latest_event_type_name text,
  latest_call_category text,
  latest_host_id text,
  latest_appointment_outcome_name text,
  latest_appointment_outcome_role text,
  has_fathom_record boolean NOT NULL DEFAULT false,
  fathom_record_count integer NOT NULL DEFAULT 0,
  completed_calls_missing_fathom_count integer NOT NULL DEFAULT 0,
  completed_call_fathom_coverage_rate numeric(5,2),
  avg_call_duration_seconds numeric,
  total_call_duration_seconds numeric,

  contract_count integer NOT NULL DEFAULT 0,
  signed_contract_count integer NOT NULL DEFAULT 0,
  sent_contract_count integer NOT NULL DEFAULT 0,
  viewed_contract_count integer NOT NULL DEFAULT 0,
  voided_contract_count integer NOT NULL DEFAULT 0,
  contract_sent_lifecycle_count integer NOT NULL DEFAULT 0,
  latest_contract_status text,
  latest_contract_sent_at timestamptz,
  latest_contract_signed_at timestamptz,
  latest_contract_voided_at timestamptz,
  signed_contract_value numeric(12,2) NOT NULL DEFAULT 0,
  contract_currency text NOT NULL DEFAULT 'EUR',
  latest_program_name text,
  closer_id text,
  contract_setter_id text,

  payment_count integer NOT NULL DEFAULT 0,
  paid_payment_count integer NOT NULL DEFAULT 0,
  pending_payment_count integer NOT NULL DEFAULT 0,
  failed_payment_count integer NOT NULL DEFAULT 0,
  lost_payment_count integer NOT NULL DEFAULT 0,
  refunded_payment_count integer NOT NULL DEFAULT 0,
  gross_paid_amount numeric(12,2) NOT NULL DEFAULT 0,
  refund_amount numeric(12,2) NOT NULL DEFAULT 0,
  net_collected_amount numeric(12,2) NOT NULL DEFAULT 0,
  outstanding_amount numeric(12,2) NOT NULL DEFAULT 0,
  overdue_amount numeric(12,2) NOT NULL DEFAULT 0,
  latest_payment_status text,
  latest_paid_at timestamptz,
  latest_payment_due_date timestamptz,
  payment_currency text NOT NULL DEFAULT 'EUR',

  funnel_stage text NOT NULL,
  conversion_outcome text NOT NULL,
  lead_to_booked_days integer,
  booked_to_completed_days integer,
  completed_to_signed_days integer,
  signed_to_paid_days integer,

  has_missing_first_source boolean NOT NULL DEFAULT false,
  has_missing_last_source boolean NOT NULL DEFAULT false,
  has_orphaned_first_source_id boolean NOT NULL DEFAULT false,
  has_orphaned_last_source_id boolean NOT NULL DEFAULT false,
  has_unknown_source boolean NOT NULL DEFAULT false,
  has_multiple_opt_ins boolean NOT NULL DEFAULT false,
  has_multiple_sources boolean NOT NULL DEFAULT false,
  has_revenue_without_source boolean NOT NULL DEFAULT false,
  has_payment_without_contract boolean NOT NULL DEFAULT false,
  has_contract_without_payment boolean NOT NULL DEFAULT false,
  data_quality_flags jsonb NOT NULL DEFAULT '[]'::jsonb,

  CONSTRAINT uq_dls_org_lead UNIQUE (clerk_org_id, lead_id),
  CONSTRAINT chk_dls_source_confidence
    CHECK (source_confidence IN ('high', 'medium', 'low')),
  CONSTRAINT chk_dls_funnel_stage
    CHECK (funnel_stage IN (
      'lead_only',
      'booked_not_completed',
      'completed_not_signed',
      'signed_not_paid',
      'paid',
      'refunded',
      'lost',
      'unqualified'
    )),
  CONSTRAINT chk_dls_conversion_outcome
    CHECK (conversion_outcome IN (
      'converted_paid',
      'signed_pending_payment',
      'attended_not_signed',
      'booked_not_attended',
      'lead_not_booked',
      'lost',
      'unqualified',
      'refunded',
      'unknown'
    )),
  CONSTRAINT chk_dls_contract_currency_eur CHECK (contract_currency = 'EUR'),
  CONSTRAINT chk_dls_payment_currency_eur CHECK (payment_currency = 'EUR')
)
"""


CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_dls_org ON diagnostic_lead_snapshot (clerk_org_id)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_lead ON diagnostic_lead_snapshot (clerk_org_id, lead_id)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_lead_created_at ON diagnostic_lead_snapshot (clerk_org_id, lead_created_at)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_status_role ON diagnostic_lead_snapshot (clerk_org_id, current_status_role)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_funnel_stage ON diagnostic_lead_snapshot (clerk_org_id, funnel_stage)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_conversion_outcome ON diagnostic_lead_snapshot (clerk_org_id, conversion_outcome)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_first_source ON diagnostic_lead_snapshot (clerk_org_id, first_source)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_last_source ON diagnostic_lead_snapshot (clerk_org_id, last_source)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_source_confidence ON diagnostic_lead_snapshot (clerk_org_id, source_confidence)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_net_collected_amount ON diagnostic_lead_snapshot (clerk_org_id, net_collected_amount)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_signed_contract_value ON diagnostic_lead_snapshot (clerk_org_id, signed_contract_value)",
    "CREATE INDEX IF NOT EXISTS idx_dls_org_built_at ON diagnostic_lead_snapshot (clerk_org_id, snapshot_built_at)",
]


INSERT_SNAPSHOT_SQL = """
WITH base_leads AS (
  SELECT
    l.id AS lead_id,
    l.clerk_org_id,
    l.created_at AS lead_created_at,
    l.updated_at AS lead_updated_at,
    l.status_id AS current_status_id,
    ss.name AS current_status_name,
    ss.role::text AS current_status_role,
    COALESCE(ss.role::text, 'NO_STATUS') AS status_role_for_logic,
    l.assigned_to,
    l.setter_id,
    l.next_touch_point_at,
    l.next_touch_point_type::text AS next_touch_point_type,
    l.source::text AS lead_source_enum,
    l.first_source_id,
    l.first_source_name,
    l.last_source_id,
    l.last_source_name
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
),
lead_source_base AS (
  SELECT
    bl.lead_id,
    bl.clerk_org_id,
    bl.first_source_id,
    bl.last_source_id,
    COALESCE(first_ms.name, NULLIF(BTRIM(bl.first_source_name), ''), 'Unknown') AS first_source,
    COALESCE(last_ms.name, NULLIF(BTRIM(bl.last_source_name), ''), 'Unknown') AS last_source,
    (
      bl.first_source_id IS NULL
      AND NULLIF(BTRIM(bl.first_source_name), '') IS NULL
    ) AS has_missing_first_source,
    (
      bl.last_source_id IS NULL
      AND NULLIF(BTRIM(bl.last_source_name), '') IS NULL
    ) AS has_missing_last_source,
    (
      bl.first_source_id IS NOT NULL
      AND first_ms.id IS NULL
    ) AS has_orphaned_first_source_id,
    (
      bl.last_source_id IS NOT NULL
      AND last_ms.id IS NULL
    ) AS has_orphaned_last_source_id
  FROM base_leads bl
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = bl.first_source_id
   AND first_ms.clerk_org_id = bl.clerk_org_id
  LEFT JOIN marketing_sources last_ms
    ON last_ms.id = bl.last_source_id
   AND last_ms.clerk_org_id = bl.clerk_org_id
),
lead_sources AS (
  SELECT
    lsb.*,
    lsb.first_source IS DISTINCT FROM lsb.last_source AS source_changed,
    (
      lsb.first_source = 'Unknown'
      OR lsb.last_source = 'Unknown'
    ) AS has_unknown_source,
    CASE
      WHEN (
        lsb.first_source = 'Unknown'
        AND lsb.last_source = 'Unknown'
      )
      OR lsb.has_orphaned_first_source_id
      OR lsb.has_orphaned_last_source_id
        THEN 'low'
      WHEN lsb.first_source = 'Unknown'
        OR lsb.last_source = 'Unknown'
        OR lsb.first_source IS DISTINCT FROM lsb.last_source
        THEN 'medium'
      ELSE 'high'
    END AS source_confidence
  FROM lead_source_base lsb
),
opt_in_ranked AS (
  SELECT
    o.*,
    ROW_NUMBER() OVER (
      PARTITION BY o.lead_id
      ORDER BY o.created_at ASC, o.id ASC
    ) AS first_rank,
    ROW_NUMBER() OVER (
      PARTITION BY o.lead_id
      ORDER BY o.created_at DESC, o.id DESC
    ) AS latest_rank
  FROM opt_ins o
  WHERE o.clerk_org_id = :org_id
),
opt_in_agg AS (
  SELECT
    o.lead_id,
    COUNT(DISTINCT o.id)::int AS opt_in_count,
    MIN(o.created_at) AS first_opt_in_at,
    MAX(o.created_at) AS latest_opt_in_at,
    MAX(CASE WHEN o.first_rank = 1 THEN o.source::text END) AS first_opt_in_source,
    MAX(CASE WHEN o.latest_rank = 1 THEN o.source::text END) AS latest_opt_in_source,
    MAX(CASE WHEN o.first_rank = 1 THEN NULLIF(BTRIM(o.provider_form_name), '') END)
      AS first_provider_form_name,
    MAX(CASE WHEN o.latest_rank = 1 THEN NULLIF(BTRIM(o.provider_form_name), '') END)
      AS latest_provider_form_name
  FROM opt_in_ranked o
  GROUP BY o.lead_id
),
traffic_ranked AS (
  SELECT
    o.lead_id,
    ta.id AS attribution_id,
    ta.utm_source,
    ta.utm_medium,
    ta.utm_campaign,
    ta.landing_page,
    ta.referrer,
    ROW_NUMBER() OVER (
      PARTITION BY o.lead_id
      ORDER BY o.created_at ASC, ta.created_at ASC, o.id ASC
    ) AS first_rank,
    ROW_NUMBER() OVER (
      PARTITION BY o.lead_id
      ORDER BY o.created_at DESC, ta.created_at DESC, o.id DESC
    ) AS latest_rank
  FROM opt_ins o
  JOIN traffic_attributions ta
    ON ta.opt_in_id = o.id
  WHERE o.clerk_org_id = :org_id
),
traffic_agg AS (
  SELECT
    tr.lead_id,
    COUNT(DISTINCT tr.attribution_id)::int AS traffic_attribution_count,
    MAX(CASE WHEN tr.first_rank = 1 THEN NULLIF(BTRIM(tr.utm_source), '') END)
      AS first_utm_source,
    MAX(CASE WHEN tr.first_rank = 1 THEN NULLIF(BTRIM(tr.utm_medium), '') END)
      AS first_utm_medium,
    MAX(CASE WHEN tr.first_rank = 1 THEN NULLIF(BTRIM(tr.utm_campaign), '') END)
      AS first_utm_campaign,
    MAX(CASE WHEN tr.first_rank = 1 THEN NULLIF(BTRIM(tr.landing_page), '') END)
      AS first_landing_page,
    MAX(CASE WHEN tr.first_rank = 1 THEN NULLIF(BTRIM(tr.referrer), '') END)
      AS first_referrer,
    MAX(CASE WHEN tr.latest_rank = 1 THEN NULLIF(BTRIM(tr.utm_source), '') END)
      AS latest_utm_source,
    MAX(CASE WHEN tr.latest_rank = 1 THEN NULLIF(BTRIM(tr.utm_medium), '') END)
      AS latest_utm_medium,
    MAX(CASE WHEN tr.latest_rank = 1 THEN NULLIF(BTRIM(tr.utm_campaign), '') END)
      AS latest_utm_campaign,
    MAX(CASE WHEN tr.latest_rank = 1 THEN NULLIF(BTRIM(tr.landing_page), '') END)
      AS latest_landing_page,
    MAX(CASE WHEN tr.latest_rank = 1 THEN NULLIF(BTRIM(tr.referrer), '') END)
      AS latest_referrer,
    BOOL_OR(NULLIF(BTRIM(tr.utm_source), '') IS NOT NULL) AS has_nonblank_utm_source,
    BOOL_OR(NULLIF(BTRIM(tr.utm_campaign), '') IS NOT NULL) AS has_nonblank_utm_campaign,
    BOOL_OR(NULLIF(BTRIM(tr.landing_page), '') IS NOT NULL) AS has_nonblank_landing_page,
    BOOL_OR(NULLIF(BTRIM(tr.referrer), '') IS NOT NULL) AS has_nonblank_referrer
  FROM traffic_ranked tr
  GROUP BY tr.lead_id
),
question_answer_agg AS (
  SELECT
    o.lead_id,
    COUNT(q.id)::int AS opt_in_answer_count
  FROM opt_in_question_answers q
  JOIN opt_ins o
    ON o.id = q.opt_in_id
  WHERE o.clerk_org_id = :org_id
  GROUP BY o.lead_id
),
appointment_rows AS (
  SELECT
    a.id AS appointment_id,
    a.lead_id,
    a.clerk_org_id,
    a.schedule_time,
    a.created_at,
    a.no_show,
    COALESCE(
      NULLIF(BTRIM(a.snapshot_event_name), ''),
      aet.event_type_name,
      'Unknown Event Type'
    ) AS event_type_name,
    a.snapshot_call_category::text AS call_category,
    a.host_id,
    outcome.name AS outcome_name,
    outcome.role::text AS outcome_role,
    (
      a.schedule_time < NOW()
      AND a.no_show = false
    ) AS is_past_non_no_show,
    (
      a.schedule_time < NOW()
      AND a.no_show = false
      AND COALESCE(outcome.role::text, 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED')
    ) AS is_completed_call,
    ROW_NUMBER() OVER (
      PARTITION BY a.lead_id
      ORDER BY a.schedule_time DESC, a.created_at DESC, a.id DESC
    ) AS latest_rank
  FROM appointments a
  LEFT JOIN sales_statuses outcome
    ON outcome.id = a.outcome_id
   AND outcome.clerk_org_id = a.clerk_org_id
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
),
appointment_agg AS (
  SELECT
    ar.lead_id,
    COUNT(*)::int AS appointment_count,
    COUNT(*) FILTER (WHERE ar.schedule_time < NOW())::int AS past_appointment_count,
    COUNT(*) FILTER (WHERE ar.schedule_time >= NOW())::int AS upcoming_appointment_count,
    COUNT(*) FILTER (WHERE ar.is_past_non_no_show)::int AS past_non_no_show_appointment_count,
    COUNT(*) FILTER (WHERE ar.is_completed_call)::int AS completed_call_count,
    COUNT(*) FILTER (WHERE ar.no_show = true)::int AS no_show_count,
    COUNT(*) FILTER (WHERE ar.outcome_role = 'CANCELED')::int AS cancelled_appointment_count,
    MIN(ar.schedule_time) AS first_appointment_at,
    MAX(ar.schedule_time) AS latest_appointment_at,
    MAX(ar.schedule_time) FILTER (WHERE ar.is_completed_call) AS latest_completed_call_at,
    MAX(CASE WHEN ar.latest_rank = 1 THEN ar.event_type_name END) AS latest_event_type_name,
    MAX(CASE WHEN ar.latest_rank = 1 THEN ar.call_category END) AS latest_call_category,
    MAX(CASE WHEN ar.latest_rank = 1 THEN ar.host_id END) AS latest_host_id,
    MAX(CASE WHEN ar.latest_rank = 1 THEN ar.outcome_name END) AS latest_appointment_outcome_name,
    MAX(CASE WHEN ar.latest_rank = 1 THEN ar.outcome_role END) AS latest_appointment_outcome_role
  FROM appointment_rows ar
  GROUP BY ar.lead_id
),
fathom_agg AS (
  SELECT
    ar.lead_id,
    COUNT(DISTINCT f.id)::int AS fathom_record_count,
    COUNT(DISTINCT ar.appointment_id) FILTER (
      WHERE ar.is_completed_call
        AND f.id IS NULL
    )::int AS completed_calls_missing_fathom_count,
    AVG(f.call_duration_seconds)::numeric AS avg_call_duration_seconds,
    SUM(f.call_duration_seconds)::numeric AS total_call_duration_seconds
  FROM appointment_rows ar
  LEFT JOIN fathom_call_records f
    ON f.appointment_id = ar.appointment_id
   AND f.clerk_org_id = ar.clerk_org_id
  GROUP BY ar.lead_id
),
contract_ranked AS (
  SELECT
    c.*,
    pr.name AS program_name,
    ROW_NUMBER() OVER (
      PARTITION BY c.lead_id
      ORDER BY
        GREATEST(
          COALESCE(c.signed_at, '-infinity'::timestamptz),
          COALESCE(c.voided_at, '-infinity'::timestamptz),
          COALESCE(c.sent_at, '-infinity'::timestamptz),
          c.created_at
        ) DESC,
        c.created_at DESC,
        c.id DESC
    ) AS latest_rank
  FROM contracts c
  LEFT JOIN programs pr
    ON pr.id = c.program_id
   AND pr.clerk_org_id = c.clerk_org_id
   AND pr.is_deleted = false
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
),
contract_agg AS (
  SELECT
    cr.lead_id,
    COUNT(DISTINCT cr.id)::int AS contract_count,
    COUNT(DISTINCT cr.id) FILTER (WHERE cr.status::text = 'SIGNED')::int AS signed_contract_count,
    COUNT(DISTINCT cr.id) FILTER (WHERE cr.status::text = 'SENT')::int AS sent_contract_count,
    COUNT(DISTINCT cr.id) FILTER (WHERE cr.status::text = 'VIEWED')::int AS viewed_contract_count,
    COUNT(DISTINCT cr.id) FILTER (WHERE cr.status::text = 'VOIDED')::int AS voided_contract_count,
    COUNT(DISTINCT cr.id) FILTER (WHERE cr.sent_at IS NOT NULL)::int AS contract_sent_lifecycle_count,
    COALESCE(
      SUM(COALESCE(cr.total_value, 0)) FILTER (WHERE cr.status::text = 'SIGNED') / 100.0,
      0
    )::numeric(12,2) AS signed_contract_value,
    MAX(CASE WHEN cr.latest_rank = 1 THEN cr.status::text END) AS latest_contract_status,
    MAX(CASE WHEN cr.latest_rank = 1 THEN cr.sent_at END) AS latest_contract_sent_at,
    MAX(CASE WHEN cr.latest_rank = 1 THEN cr.signed_at END) AS latest_contract_signed_at,
    MAX(CASE WHEN cr.latest_rank = 1 THEN cr.voided_at END) AS latest_contract_voided_at,
    MAX(CASE WHEN cr.latest_rank = 1 THEN cr.program_name END) AS latest_program_name,
    MAX(CASE WHEN cr.latest_rank = 1 THEN cr.closer_id END) AS closer_id,
    MAX(CASE WHEN cr.latest_rank = 1 THEN cr.setter_id END) AS contract_setter_id
  FROM contract_ranked cr
  GROUP BY cr.lead_id
),
payment_ranked AS (
  SELECT
    p.*,
    ROW_NUMBER() OVER (
      PARTITION BY p.lead_id
      ORDER BY
        GREATEST(
          COALESCE(p.paid_at, '-infinity'::timestamptz),
          COALESCE(p.due_date, '-infinity'::timestamptz),
          p.created_at
        ) DESC,
        p.created_at DESC,
        p.id DESC
    ) AS latest_rank
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
),
payment_agg AS (
  SELECT
    pr.lead_id,
    COUNT(DISTINCT pr.id)::int AS payment_count,
    COUNT(DISTINCT pr.id) FILTER (WHERE pr.status::text = 'PAID')::int AS paid_payment_count,
    COUNT(DISTINCT pr.id) FILTER (WHERE pr.status::text = 'PENDING')::int AS pending_payment_count,
    COUNT(DISTINCT pr.id) FILTER (WHERE pr.status::text = 'FAILED')::int AS failed_payment_count,
    COUNT(DISTINCT pr.id) FILTER (WHERE pr.status::text = 'LOST')::int AS lost_payment_count,
    COUNT(DISTINCT pr.id) FILTER (WHERE pr.status::text = 'REFUNDED')::int AS refunded_payment_count,
    COALESCE(
      SUM(COALESCE(pr.amount, 0)) FILTER (WHERE pr.status::text = 'PAID') / 100.0,
      0
    )::numeric(12,2) AS gross_paid_amount,
    COALESCE(
      SUM(COALESCE(pr.amount, 0)) FILTER (WHERE pr.status::text IN ('PENDING', 'FAILED')) / 100.0,
      0
    )::numeric(12,2) AS outstanding_amount,
    COALESCE(
      SUM(COALESCE(pr.amount, 0)) FILTER (
        WHERE pr.status::text IN ('PENDING', 'FAILED')
          AND pr.due_date IS NOT NULL
          AND pr.due_date < NOW()
      ) / 100.0,
      0
    )::numeric(12,2) AS overdue_amount,
    MAX(CASE WHEN pr.latest_rank = 1 THEN pr.status::text END) AS latest_payment_status,
    MAX(pr.paid_at) AS latest_paid_at,
    MAX(CASE WHEN pr.latest_rank = 1 THEN pr.due_date END) AS latest_payment_due_date
  FROM payment_ranked pr
  GROUP BY pr.lead_id
),
refund_agg AS (
  SELECT
    p.lead_id,
    COALESCE(
      SUM(COALESCE(r.amount, 0)) FILTER (WHERE r.status::text = 'SUCCEEDED') / 100.0,
      0
    )::numeric(12,2) AS refund_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
  GROUP BY p.lead_id
),
snapshot_metrics AS (
  SELECT
    bl.*,
    ls.first_source,
    ls.last_source,
    ls.has_missing_first_source,
    ls.has_missing_last_source,
    ls.has_orphaned_first_source_id,
    ls.has_orphaned_last_source_id,
    ls.has_unknown_source,
    ls.source_changed,
    ls.source_confidence,

    COALESCE(oi.opt_in_count, 0) AS opt_in_count,
    oi.first_opt_in_at,
    oi.latest_opt_in_at,
    oi.first_opt_in_source,
    oi.latest_opt_in_source,
    oi.first_provider_form_name,
    oi.latest_provider_form_name,
    ta.first_utm_source,
    ta.first_utm_medium,
    ta.first_utm_campaign,
    ta.first_landing_page,
    ta.first_referrer,
    ta.latest_utm_source,
    ta.latest_utm_medium,
    ta.latest_utm_campaign,
    ta.latest_landing_page,
    ta.latest_referrer,
    COALESCE(ta.traffic_attribution_count, 0) > 0 AS has_traffic_attribution,
    (
      COALESCE(oi.opt_in_count, 0) > 0
      AND NOT COALESCE(ta.has_nonblank_utm_source, false)
    ) AS missing_utm_source,
    (
      COALESCE(oi.opt_in_count, 0) > 0
      AND NOT COALESCE(ta.has_nonblank_utm_campaign, false)
    ) AS missing_utm_campaign,
    (
      COALESCE(oi.opt_in_count, 0) > 0
      AND NOT COALESCE(ta.has_nonblank_landing_page, false)
    ) AS missing_landing_page,
    (
      COALESCE(oi.opt_in_count, 0) > 0
      AND NOT COALESCE(ta.has_nonblank_referrer, false)
    ) AS missing_referrer,
    COALESCE(qa.opt_in_answer_count, 0) > 0 AS has_form_answers,
    COALESCE(qa.opt_in_answer_count, 0) AS opt_in_answer_count,

    COALESCE(ap.appointment_count, 0) AS appointment_count,
    COALESCE(ap.past_appointment_count, 0) AS past_appointment_count,
    COALESCE(ap.upcoming_appointment_count, 0) AS upcoming_appointment_count,
    COALESCE(ap.past_non_no_show_appointment_count, 0) AS past_non_no_show_appointment_count,
    COALESCE(ap.completed_call_count, 0) AS completed_call_count,
    COALESCE(ap.no_show_count, 0) AS no_show_count,
    COALESCE(ap.cancelled_appointment_count, 0) AS cancelled_appointment_count,
    ap.first_appointment_at,
    ap.latest_appointment_at,
    ap.latest_completed_call_at,
    ap.latest_event_type_name,
    ap.latest_call_category,
    ap.latest_host_id,
    ap.latest_appointment_outcome_name,
    ap.latest_appointment_outcome_role,
    COALESCE(fa.fathom_record_count, 0) > 0 AS has_fathom_record,
    COALESCE(fa.fathom_record_count, 0) AS fathom_record_count,
    COALESCE(fa.completed_calls_missing_fathom_count, 0) AS completed_calls_missing_fathom_count,
    CASE
      WHEN COALESCE(ap.completed_call_count, 0) > 0
      THEN ROUND(
        100.0
        * (COALESCE(ap.completed_call_count, 0) - COALESCE(fa.completed_calls_missing_fathom_count, 0))
        / COALESCE(ap.completed_call_count, 0),
        2
      )
      ELSE NULL
    END::numeric(5,2) AS completed_call_fathom_coverage_rate,
    fa.avg_call_duration_seconds,
    fa.total_call_duration_seconds,

    COALESCE(ca.contract_count, 0) AS contract_count,
    COALESCE(ca.signed_contract_count, 0) AS signed_contract_count,
    COALESCE(ca.sent_contract_count, 0) AS sent_contract_count,
    COALESCE(ca.viewed_contract_count, 0) AS viewed_contract_count,
    COALESCE(ca.voided_contract_count, 0) AS voided_contract_count,
    COALESCE(ca.contract_sent_lifecycle_count, 0) AS contract_sent_lifecycle_count,
    ca.latest_contract_status,
    ca.latest_contract_sent_at,
    ca.latest_contract_signed_at,
    ca.latest_contract_voided_at,
    COALESCE(ca.signed_contract_value, 0)::numeric(12,2) AS signed_contract_value,
    'EUR'::text AS contract_currency,
    ca.latest_program_name,
    ca.closer_id,
    ca.contract_setter_id,

    COALESCE(pa.payment_count, 0) AS payment_count,
    COALESCE(pa.paid_payment_count, 0) AS paid_payment_count,
    COALESCE(pa.pending_payment_count, 0) AS pending_payment_count,
    COALESCE(pa.failed_payment_count, 0) AS failed_payment_count,
    COALESCE(pa.lost_payment_count, 0) AS lost_payment_count,
    COALESCE(pa.refunded_payment_count, 0) AS refunded_payment_count,
    COALESCE(pa.gross_paid_amount, 0)::numeric(12,2) AS gross_paid_amount,
    COALESCE(ra.refund_amount, 0)::numeric(12,2) AS refund_amount,
    (
      COALESCE(pa.gross_paid_amount, 0) - COALESCE(ra.refund_amount, 0)
    )::numeric(12,2) AS net_collected_amount,
    COALESCE(pa.outstanding_amount, 0)::numeric(12,2) AS outstanding_amount,
    COALESCE(pa.overdue_amount, 0)::numeric(12,2) AS overdue_amount,
    pa.latest_payment_status,
    pa.latest_paid_at,
    pa.latest_payment_due_date,
    'EUR'::text AS payment_currency
  FROM base_leads bl
  JOIN lead_sources ls
    ON ls.lead_id = bl.lead_id
  LEFT JOIN opt_in_agg oi
    ON oi.lead_id = bl.lead_id
  LEFT JOIN traffic_agg ta
    ON ta.lead_id = bl.lead_id
  LEFT JOIN question_answer_agg qa
    ON qa.lead_id = bl.lead_id
  LEFT JOIN appointment_agg ap
    ON ap.lead_id = bl.lead_id
  LEFT JOIN fathom_agg fa
    ON fa.lead_id = bl.lead_id
  LEFT JOIN contract_agg ca
    ON ca.lead_id = bl.lead_id
  LEFT JOIN payment_agg pa
    ON pa.lead_id = bl.lead_id
  LEFT JOIN refund_agg ra
    ON ra.lead_id = bl.lead_id
),
snapshot_enriched AS (
  SELECT
    sm.*,
    (
      sm.next_touch_point_at IS NULL
      AND sm.status_role_for_logic NOT IN ('WON', 'LOST', 'UNQUALIFIED', 'CANCELED')
    ) AS is_missing_next_touchpoint,
    (
      sm.next_touch_point_at IS NOT NULL
      AND sm.next_touch_point_at < NOW()
      AND sm.status_role_for_logic NOT IN ('WON', 'LOST', 'UNQUALIFIED', 'CANCELED')
    ) AS is_overdue_followup,
    (
      sm.opt_in_count > 1
    ) AS has_multiple_opt_ins,
    (
      sm.first_source IS DISTINCT FROM sm.last_source
      OR sm.first_utm_source IS DISTINCT FROM sm.latest_utm_source
      OR sm.first_utm_campaign IS DISTINCT FROM sm.latest_utm_campaign
    ) AS has_multiple_sources,
    (
      sm.net_collected_amount > 0
      AND sm.has_unknown_source
    ) AS has_revenue_without_source,
    (
      sm.payment_count > 0
      AND sm.contract_count = 0
    ) AS has_payment_without_contract,
    (
      sm.contract_count > 0
      AND sm.payment_count = 0
    ) AS has_contract_without_payment,
    CASE
      WHEN sm.net_collected_amount > 0 THEN 'paid'
      WHEN sm.refund_amount > 0 AND sm.net_collected_amount <= 0 THEN 'refunded'
      WHEN sm.current_status_role = 'LOST' THEN 'lost'
      WHEN sm.current_status_role = 'UNQUALIFIED' THEN 'unqualified'
      WHEN sm.signed_contract_count > 0 THEN 'signed_not_paid'
      WHEN sm.completed_call_count > 0 THEN 'completed_not_signed'
      WHEN sm.appointment_count > 0 THEN 'booked_not_completed'
      ELSE 'lead_only'
    END AS funnel_stage
  FROM snapshot_metrics sm
),
final_snapshot AS (
  SELECT
    se.*,
    CASE se.funnel_stage
      WHEN 'paid' THEN 'converted_paid'
      WHEN 'signed_not_paid' THEN 'signed_pending_payment'
      WHEN 'completed_not_signed' THEN 'attended_not_signed'
      WHEN 'booked_not_completed' THEN 'booked_not_attended'
      WHEN 'lead_only' THEN 'lead_not_booked'
      WHEN 'lost' THEN 'lost'
      WHEN 'unqualified' THEN 'unqualified'
      WHEN 'refunded' THEN 'refunded'
      ELSE 'unknown'
    END AS conversion_outcome,
    to_jsonb(array_remove(ARRAY[
      CASE WHEN se.has_missing_first_source THEN 'missing_first_source'::text END,
      CASE WHEN se.has_missing_last_source THEN 'missing_last_source'::text END,
      CASE WHEN se.has_orphaned_first_source_id THEN 'orphaned_first_source_id'::text END,
      CASE WHEN se.has_orphaned_last_source_id THEN 'orphaned_last_source_id'::text END,
      CASE WHEN se.has_unknown_source THEN 'unknown_source'::text END,
      CASE WHEN se.source_changed THEN 'source_changed'::text END,
      CASE WHEN se.has_multiple_sources THEN 'multiple_sources'::text END
    ], NULL)) AS source_quality_flags,
    to_jsonb(array_remove(ARRAY[
      CASE WHEN se.has_missing_first_source THEN 'missing_first_source'::text END,
      CASE WHEN se.has_missing_last_source THEN 'missing_last_source'::text END,
      CASE WHEN se.has_orphaned_first_source_id THEN 'orphaned_first_source_id'::text END,
      CASE WHEN se.has_orphaned_last_source_id THEN 'orphaned_last_source_id'::text END,
      CASE WHEN se.has_unknown_source THEN 'unknown_source'::text END,
      CASE WHEN se.source_changed THEN 'source_changed'::text END,
      CASE WHEN se.has_multiple_opt_ins THEN 'multiple_opt_ins'::text END,
      CASE WHEN se.has_multiple_sources THEN 'multiple_sources'::text END,
      CASE WHEN se.has_revenue_without_source THEN 'revenue_without_source'::text END,
      CASE WHEN se.has_payment_without_contract THEN 'payment_without_contract'::text END,
      CASE WHEN se.has_contract_without_payment THEN 'contract_without_payment'::text END,
      CASE WHEN se.missing_utm_source THEN 'missing_utm_source'::text END,
      CASE WHEN se.missing_utm_campaign THEN 'missing_utm_campaign'::text END,
      CASE WHEN se.missing_landing_page THEN 'missing_landing_page'::text END,
      CASE WHEN se.missing_referrer THEN 'missing_referrer'::text END,
      CASE WHEN se.completed_calls_missing_fathom_count > 0 THEN 'no_fathom_record'::text END
    ], NULL)) AS data_quality_flags
  FROM snapshot_enriched se
)
INSERT INTO diagnostic_lead_snapshot (
  clerk_org_id,
  lead_id,
  lead_created_at,
  lead_updated_at,
  snapshot_built_at,
  current_status_id,
  current_status_name,
  current_status_role,
  assigned_to,
  setter_id,
  next_touch_point_at,
  next_touch_point_type,
  is_overdue_followup,
  is_missing_next_touchpoint,
  lead_source_enum,
  first_source_id,
  first_source,
  last_source_id,
  last_source,
  source_changed,
  source_confidence,
  source_quality_flags,
  opt_in_count,
  first_opt_in_at,
  latest_opt_in_at,
  first_opt_in_source,
  latest_opt_in_source,
  first_provider_form_name,
  latest_provider_form_name,
  first_utm_source,
  first_utm_medium,
  first_utm_campaign,
  first_landing_page,
  first_referrer,
  latest_utm_source,
  latest_utm_medium,
  latest_utm_campaign,
  latest_landing_page,
  latest_referrer,
  has_traffic_attribution,
  missing_utm_source,
  missing_utm_campaign,
  missing_landing_page,
  missing_referrer,
  has_form_answers,
  opt_in_answer_count,
  appointment_count,
  past_appointment_count,
  upcoming_appointment_count,
  past_non_no_show_appointment_count,
  completed_call_count,
  no_show_count,
  cancelled_appointment_count,
  first_appointment_at,
  latest_appointment_at,
  latest_completed_call_at,
  latest_event_type_name,
  latest_call_category,
  latest_host_id,
  latest_appointment_outcome_name,
  latest_appointment_outcome_role,
  has_fathom_record,
  fathom_record_count,
  completed_calls_missing_fathom_count,
  completed_call_fathom_coverage_rate,
  avg_call_duration_seconds,
  total_call_duration_seconds,
  contract_count,
  signed_contract_count,
  sent_contract_count,
  viewed_contract_count,
  voided_contract_count,
  contract_sent_lifecycle_count,
  latest_contract_status,
  latest_contract_sent_at,
  latest_contract_signed_at,
  latest_contract_voided_at,
  signed_contract_value,
  contract_currency,
  latest_program_name,
  closer_id,
  contract_setter_id,
  payment_count,
  paid_payment_count,
  pending_payment_count,
  failed_payment_count,
  lost_payment_count,
  refunded_payment_count,
  gross_paid_amount,
  refund_amount,
  net_collected_amount,
  outstanding_amount,
  overdue_amount,
  latest_payment_status,
  latest_paid_at,
  latest_payment_due_date,
  payment_currency,
  funnel_stage,
  conversion_outcome,
  lead_to_booked_days,
  booked_to_completed_days,
  completed_to_signed_days,
  signed_to_paid_days,
  has_missing_first_source,
  has_missing_last_source,
  has_orphaned_first_source_id,
  has_orphaned_last_source_id,
  has_unknown_source,
  has_multiple_opt_ins,
  has_multiple_sources,
  has_revenue_without_source,
  has_payment_without_contract,
  has_contract_without_payment,
  data_quality_flags
)
SELECT
  fs.clerk_org_id,
  fs.lead_id,
  fs.lead_created_at,
  fs.lead_updated_at,
  NOW() AS snapshot_built_at,
  fs.current_status_id,
  fs.current_status_name,
  fs.current_status_role,
  fs.assigned_to,
  fs.setter_id,
  fs.next_touch_point_at,
  fs.next_touch_point_type,
  fs.is_overdue_followup,
  fs.is_missing_next_touchpoint,
  fs.lead_source_enum,
  fs.first_source_id,
  fs.first_source,
  fs.last_source_id,
  fs.last_source,
  fs.source_changed,
  fs.source_confidence,
  fs.source_quality_flags,
  fs.opt_in_count,
  fs.first_opt_in_at,
  fs.latest_opt_in_at,
  fs.first_opt_in_source,
  fs.latest_opt_in_source,
  fs.first_provider_form_name,
  fs.latest_provider_form_name,
  fs.first_utm_source,
  fs.first_utm_medium,
  fs.first_utm_campaign,
  fs.first_landing_page,
  fs.first_referrer,
  fs.latest_utm_source,
  fs.latest_utm_medium,
  fs.latest_utm_campaign,
  fs.latest_landing_page,
  fs.latest_referrer,
  fs.has_traffic_attribution,
  fs.missing_utm_source,
  fs.missing_utm_campaign,
  fs.missing_landing_page,
  fs.missing_referrer,
  fs.has_form_answers,
  fs.opt_in_answer_count,
  fs.appointment_count,
  fs.past_appointment_count,
  fs.upcoming_appointment_count,
  fs.past_non_no_show_appointment_count,
  fs.completed_call_count,
  fs.no_show_count,
  fs.cancelled_appointment_count,
  fs.first_appointment_at,
  fs.latest_appointment_at,
  fs.latest_completed_call_at,
  fs.latest_event_type_name,
  fs.latest_call_category,
  fs.latest_host_id,
  fs.latest_appointment_outcome_name,
  fs.latest_appointment_outcome_role,
  fs.has_fathom_record,
  fs.fathom_record_count,
  fs.completed_calls_missing_fathom_count,
  fs.completed_call_fathom_coverage_rate,
  fs.avg_call_duration_seconds,
  fs.total_call_duration_seconds,
  fs.contract_count,
  fs.signed_contract_count,
  fs.sent_contract_count,
  fs.viewed_contract_count,
  fs.voided_contract_count,
  fs.contract_sent_lifecycle_count,
  fs.latest_contract_status,
  fs.latest_contract_sent_at,
  fs.latest_contract_signed_at,
  fs.latest_contract_voided_at,
  fs.signed_contract_value,
  fs.contract_currency,
  fs.latest_program_name,
  fs.closer_id,
  fs.contract_setter_id,
  fs.payment_count,
  fs.paid_payment_count,
  fs.pending_payment_count,
  fs.failed_payment_count,
  fs.lost_payment_count,
  fs.refunded_payment_count,
  fs.gross_paid_amount,
  fs.refund_amount,
  fs.net_collected_amount,
  fs.outstanding_amount,
  fs.overdue_amount,
  fs.latest_payment_status,
  fs.latest_paid_at,
  fs.latest_payment_due_date,
  fs.payment_currency,
  fs.funnel_stage,
  fs.conversion_outcome,
  CASE
    WHEN fs.first_appointment_at IS NOT NULL
      AND fs.lead_created_at IS NOT NULL
      AND fs.first_appointment_at >= fs.lead_created_at
    THEN FLOOR(EXTRACT(EPOCH FROM (fs.first_appointment_at - fs.lead_created_at)) / 86400)::int
    ELSE NULL
  END AS lead_to_booked_days,
  CASE
    WHEN fs.latest_completed_call_at IS NOT NULL
      AND fs.first_appointment_at IS NOT NULL
      AND fs.latest_completed_call_at >= fs.first_appointment_at
    THEN FLOOR(EXTRACT(EPOCH FROM (fs.latest_completed_call_at - fs.first_appointment_at)) / 86400)::int
    ELSE NULL
  END AS booked_to_completed_days,
  CASE
    WHEN fs.latest_contract_signed_at IS NOT NULL
      AND fs.latest_completed_call_at IS NOT NULL
      AND fs.latest_contract_signed_at >= fs.latest_completed_call_at
    THEN FLOOR(EXTRACT(EPOCH FROM (fs.latest_contract_signed_at - fs.latest_completed_call_at)) / 86400)::int
    ELSE NULL
  END AS completed_to_signed_days,
  CASE
    WHEN fs.latest_paid_at IS NOT NULL
      AND fs.latest_contract_signed_at IS NOT NULL
      AND fs.latest_paid_at >= fs.latest_contract_signed_at
    THEN FLOOR(EXTRACT(EPOCH FROM (fs.latest_paid_at - fs.latest_contract_signed_at)) / 86400)::int
    ELSE NULL
  END AS signed_to_paid_days,
  fs.has_missing_first_source,
  fs.has_missing_last_source,
  fs.has_orphaned_first_source_id,
  fs.has_orphaned_last_source_id,
  fs.has_unknown_source,
  fs.has_multiple_opt_ins,
  fs.has_multiple_sources,
  fs.has_revenue_without_source,
  fs.has_payment_without_contract,
  fs.has_contract_without_payment,
  fs.data_quality_flags
FROM final_snapshot fs
RETURNING 1
"""


INSERT_COUNT_SQL = f"""
WITH inserted AS (
{INSERT_SNAPSHOT_SQL}
)
SELECT COUNT(*)::int AS rows_inserted
FROM inserted
"""


VALIDATION_SQL = """
WITH active_leads AS (
  SELECT id AS lead_id
  FROM leads
  WHERE clerk_org_id = :org_id
    AND is_deleted = false
),
snapshot_rows AS (
  SELECT *
  FROM diagnostic_lead_snapshot
  WHERE clerk_org_id = :org_id
),
count_columns AS (
  SELECT *
  FROM snapshot_rows
  WHERE opt_in_count < 0
     OR opt_in_answer_count < 0
     OR appointment_count < 0
     OR past_appointment_count < 0
     OR upcoming_appointment_count < 0
     OR past_non_no_show_appointment_count < 0
     OR completed_call_count < 0
     OR no_show_count < 0
     OR cancelled_appointment_count < 0
     OR fathom_record_count < 0
     OR completed_calls_missing_fathom_count < 0
     OR contract_count < 0
     OR signed_contract_count < 0
     OR sent_contract_count < 0
     OR viewed_contract_count < 0
     OR voided_contract_count < 0
     OR contract_sent_lifecycle_count < 0
     OR payment_count < 0
     OR paid_payment_count < 0
     OR pending_payment_count < 0
     OR failed_payment_count < 0
     OR lost_payment_count < 0
     OR refunded_payment_count < 0
),
amount_columns AS (
  SELECT *
  FROM snapshot_rows
  WHERE signed_contract_value < 0
     OR gross_paid_amount < 0
     OR refund_amount < 0
     OR outstanding_amount < 0
     OR overdue_amount < 0
),
flag_nulls AS (
  SELECT sr.id
  FROM snapshot_rows sr
  WHERE EXISTS (
      SELECT 1
      FROM jsonb_array_elements(
        CASE
          WHEN jsonb_typeof(sr.source_quality_flags) = 'array'
          THEN sr.source_quality_flags
          ELSE '[]'::jsonb
        END
      ) AS elem(value)
      WHERE elem.value = 'null'::jsonb
    )
     OR EXISTS (
      SELECT 1
      FROM jsonb_array_elements(
        CASE
          WHEN jsonb_typeof(sr.data_quality_flags) = 'array'
          THEN sr.data_quality_flags
          ELSE '[]'::jsonb
        END
      ) AS elem(value)
      WHERE elem.value = 'null'::jsonb
    )
)
SELECT 'row_count_mismatch' AS check_name, COUNT(*)::int AS failure_count
FROM (
  SELECT
    (SELECT COUNT(*) FROM active_leads) AS active_count,
    (SELECT COUNT(*) FROM snapshot_rows) AS snapshot_count
) counts
WHERE active_count <> snapshot_count
HAVING COUNT(*) > 0

UNION ALL
SELECT 'missing_active_lead_snapshot', COUNT(*)::int
FROM active_leads al
LEFT JOIN snapshot_rows sr
  ON sr.lead_id = al.lead_id
WHERE sr.lead_id IS NULL
HAVING COUNT(*) > 0

UNION ALL
SELECT 'extra_snapshot_without_active_lead', COUNT(*)::int
FROM snapshot_rows sr
LEFT JOIN active_leads al
  ON al.lead_id = sr.lead_id
WHERE al.lead_id IS NULL
HAVING COUNT(*) > 0

UNION ALL
SELECT 'duplicate_org_lead_rows', COUNT(*)::int
FROM (
  SELECT clerk_org_id, lead_id
  FROM snapshot_rows
  GROUP BY clerk_org_id, lead_id
  HAVING COUNT(*) > 1
) duplicates
HAVING COUNT(*) > 0

UNION ALL
SELECT 'null_clerk_org_id', COUNT(*)::int
FROM snapshot_rows
WHERE clerk_org_id IS NULL
HAVING COUNT(*) > 0

UNION ALL
SELECT 'null_lead_id', COUNT(*)::int
FROM snapshot_rows
WHERE lead_id IS NULL
HAVING COUNT(*) > 0

UNION ALL
SELECT 'negative_count_column', COUNT(*)::int
FROM count_columns
HAVING COUNT(*) > 0

UNION ALL
SELECT 'negative_amount_column', COUNT(*)::int
FROM amount_columns
HAVING COUNT(*) > 0

UNION ALL
SELECT 'invalid_funnel_stage', COUNT(*)::int
FROM snapshot_rows
WHERE funnel_stage NOT IN (
  'lead_only',
  'booked_not_completed',
  'completed_not_signed',
  'signed_not_paid',
  'paid',
  'refunded',
  'lost',
  'unqualified'
)
HAVING COUNT(*) > 0

UNION ALL
SELECT 'invalid_conversion_outcome', COUNT(*)::int
FROM snapshot_rows
WHERE conversion_outcome NOT IN (
  'converted_paid',
  'signed_pending_payment',
  'attended_not_signed',
  'booked_not_attended',
  'lead_not_booked',
  'lost',
  'unqualified',
  'refunded',
  'unknown'
)
HAVING COUNT(*) > 0

UNION ALL
SELECT 'invalid_source_confidence', COUNT(*)::int
FROM snapshot_rows
WHERE source_confidence NOT IN ('high', 'medium', 'low')
HAVING COUNT(*) > 0

UNION ALL
SELECT 'invalid_contract_currency', COUNT(*)::int
FROM snapshot_rows
WHERE contract_currency <> 'EUR'
HAVING COUNT(*) > 0

UNION ALL
SELECT 'invalid_payment_currency', COUNT(*)::int
FROM snapshot_rows
WHERE payment_currency <> 'EUR'
HAVING COUNT(*) > 0

UNION ALL
SELECT 'source_quality_flags_not_array', COUNT(*)::int
FROM snapshot_rows
WHERE jsonb_typeof(source_quality_flags) <> 'array'
HAVING COUNT(*) > 0

UNION ALL
SELECT 'data_quality_flags_not_array', COUNT(*)::int
FROM snapshot_rows
WHERE jsonb_typeof(data_quality_flags) <> 'array'
HAVING COUNT(*) > 0

UNION ALL
SELECT 'json_flag_array_contains_null', COUNT(*)::int
FROM flag_nulls
HAVING COUNT(*) > 0

UNION ALL
SELECT 'wrong_org_snapshot_row', COUNT(*)::int
FROM snapshot_rows
WHERE clerk_org_id <> :org_id
HAVING COUNT(*) > 0
"""


SNAPSHOT_COUNT_SQL = """
SELECT COUNT(*)::int
FROM diagnostic_lead_snapshot
WHERE clerk_org_id = :org_id
"""


DELETE_SNAPSHOT_SQL = """
DELETE FROM diagnostic_lead_snapshot
WHERE clerk_org_id = :org_id
"""


BUILD_TIMESTAMP_SQL = """
SELECT MAX(snapshot_built_at)::text
FROM diagnostic_lead_snapshot
WHERE clerk_org_id = :org_id
"""


def build_diagnostic_lead_snapshot_once(
    org_id: str,
    *,
    force: bool = False,
    engine: Engine | None = None,
) -> dict[str, Any]:
    """Build the static diagnostic lead snapshot for one organization.

    Without ``force``, this function fails if the organization already has
    snapshot rows. With ``force``, existing rows for the organization are
    deleted and rebuilt inside the same transaction.
    """

    clean_org_id = str(org_id or "").strip()
    if not clean_org_id:
        raise DiagnosticSnapshotBuildError("org_id is required.")

    effective_engine = engine or _create_engine_from_settings()
    started_at = time.monotonic()
    rows_deleted = 0
    rows_inserted = 0
    snapshot_built_at: str | None = None

    try:
        with effective_engine.begin() as conn:
            _ensure_schema(conn)

            existing_count = _scalar_int(conn, SNAPSHOT_COUNT_SQL, {"org_id": clean_org_id})
            if existing_count and not force:
                raise DiagnosticSnapshotBuildError(
                    "diagnostic_lead_snapshot rows already exist for "
                    f"organization {clean_org_id!r}. Rerun with force=True for a local/demo rebuild."
                )

            if force:
                delete_result = conn.execute(text(DELETE_SNAPSHOT_SQL), {"org_id": clean_org_id})
                rows_deleted = int(delete_result.rowcount or 0)

            rows_inserted = _scalar_int(conn, INSERT_COUNT_SQL, {"org_id": clean_org_id})

            validation_failures = _validation_failures(conn, clean_org_id)
            if validation_failures:
                formatted = ", ".join(
                    f"{row['check_name']}={row['failure_count']}" for row in validation_failures
                )
                raise DiagnosticSnapshotBuildError(
                    f"diagnostic_lead_snapshot validation failed: {formatted}"
                )

            snapshot_built_at = conn.execute(
                text(BUILD_TIMESTAMP_SQL),
                {"org_id": clean_org_id},
            ).scalar_one_or_none()
    except DiagnosticSnapshotBuildError:
        raise
    except Exception as exc:
        _raise_friendly_database_error(exc)

    if snapshot_built_at is None:
        raise DiagnosticSnapshotBuildError(
            "diagnostic_lead_snapshot build finished but no snapshot_built_at was found."
        )

    duration_seconds = round(time.monotonic() - started_at, 3)
    return DiagnosticSnapshotBuildSummary(
        organization_id=clean_org_id,
        force=force,
        rows_deleted=rows_deleted,
        rows_inserted=rows_inserted,
        snapshot_built_at=snapshot_built_at,
        duration_seconds=duration_seconds,
        validation_status="passed",
    ).as_dict()


def _raise_friendly_database_error(exc: Exception) -> None:
    message = str(exc)
    if "permission denied for schema" in message or "InsufficientPrivilege" in message:
        raise DiagnosticSnapshotBuildError(
            "database role does not have permission to create/write diagnostic_lead_snapshot. "
            "This admin script needs a write/admin database URL. Set "
            "HERMON_DIAGNOSTIC_DATABASE_URL or SUPABASE_DB_URL in .env, or run with a database "
            "role that can CREATE TABLE, CREATE INDEX, INSERT, DELETE, and SELECT in public."
        ) from exc

    raise exc


def _create_engine_from_settings() -> Engine:
    database_url = _diagnostic_database_url()
    if not database_url:
        raise DiagnosticSnapshotBuildError(
            "Missing admin/write database URL. Set HERMON_DIAGNOSTIC_DATABASE_URL, "
            "SUPABASE_DB_URL, HERMON_DATABASE_URL, or DATABASE_URL in .env."
        )
    return create_engine(_sqlalchemy_psycopg_url(database_url), pool_pre_ping=True, future=True)


def _sqlalchemy_psycopg_url(database_url: str) -> str:
    """Prefer the installed psycopg v3 driver for plain Postgres URLs."""

    clean_url = database_url.strip()
    if clean_url.startswith("postgresql://"):
        return clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if clean_url.startswith("postgres://"):
        return clean_url.replace("postgres://", "postgresql+psycopg://", 1)
    return clean_url


def _diagnostic_database_url() -> str | None:
    """Return the preferred write/admin URL for the one-time diagnostic build."""

    settings = get_database_settings()
    return (
        os.getenv("HERMON_DIAGNOSTIC_DATABASE_URL")
        or os.getenv("SUPABASE_DB_URL")
        or settings.database_url
        or os.getenv("DATABASE_URL")
    )


def _ensure_schema(conn: Connection) -> None:
    conn.execute(text(CREATE_TABLE_SQL))
    for statement in CREATE_INDEX_SQL:
        conn.execute(text(statement))


def _scalar_int(conn: Connection, sql: str, params: dict[str, Any]) -> int:
    value = conn.execute(text(sql), params).scalar_one()
    return int(value or 0)


def _validation_failures(conn: Connection, org_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(text(VALIDATION_SQL), {"org_id": org_id}).mappings().all()
    return [dict(row) for row in rows]
