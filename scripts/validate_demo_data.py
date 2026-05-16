#!/usr/bin/env python3
"""Read-only end-to-end validation for the seeded client-demo dataset."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_database_settings  # noqa: E402


DUMMY_ORG_ID = "org_dummy_client_demo_001"
BLOCKED_ORG_IDS = {
    "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
}

EXPECTED_COUNTS = {
    "sales_statuses": 10,
    "marketing_sources": 10,
    "programs": 5,
    "appointment_event_types": 5,
    "leads": 500,
    "opt_ins": 650,
    "traffic_attributions": 650,
    "opt_in_question_answers": 6500,
    "appointments": 445,
    "fathom_call_records": 285,
    "contracts": 178,
    "payments": 190,
    "refunds": 12,
    "diagnostic_text_insights": 405,
    "diagnostic_lead_snapshot": 500,
}

MONTHLY_LEADS = {
    "2025-11": 55,
    "2025-12": 70,
    "2026-01": 95,
    "2026-02": 82,
    "2026-03": 90,
    "2026-04": 108,
}

SOURCE_COUNTS = {
    "Facebook": 90,
    "Instagram": 60,
    "YouTube": 65,
    "Google Search": 70,
    "Webinar": 60,
    "Referral": 40,
    "Email Campaign": 35,
    "Calendly": 30,
    "Landing Page": 30,
    "Organic Search": 20,
}

SCENARIO_COUNTS = {
    "paid_converted": 110,
    "completed_not_signed": 150,
    "booked_not_completed": 90,
    "lead_only": 75,
    "signed_not_paid": 25,
    "lost": 30,
    "unqualified": 20,
}

EXPECTED_QUESTIONS = (
    "What do you do for work?",
    "What is your employment status?",
    "Which country are you from?",
    "Which city or region are you based in?",
    "What is your main goal?",
    "What is your biggest challenge right now?",
    "How soon do you want to get started?",
    "What is your current experience level?",
    "What budget range are you comfortable with?",
    "Are you the final decision maker?",
)

OPTIONAL_TABLES = (
    "invoices",
    "payment_links",
    "payment_proofs",
    "contract_subscriptions",
    "subscription_checkout_links",
    "unmatched_payments",
)

ADMIN_TABLES = (
    "provider_integrations",
    "provider_credentials",
    "webhook_events",
    "integration_health_checks",
    "audit_logs",
    "notification_logs",
)

ALLOWED_DTI_REASON_CATEGORIES = {
    "price_or_budget",
    "timing_issue",
    "not_decision_maker",
    "needs_partner_approval",
    "trust_issue",
    "low_intent",
    "unclear_need",
    "poor_fit",
    "competition",
    "too_busy",
    "needs_more_information",
    "payment_friction",
    "contract_friction",
    "no_show",
    "ghosted",
    "follow_up_pending",
    "operational_delay",
    "technical_issue",
    "language_or_communication_issue",
    "location_or_timezone_issue",
    "already_solved",
    "unknown",
}

ALLOWED_DTI_REASON_SUBCATEGORIES = {
    "price_too_high",
    "budget_not_available",
    "wants_discount",
    "needs_payment_plan",
    "not_ready_now",
    "needs_more_time",
    "waiting_for_partner",
    "waiting_for_team",
    "waiting_for_finance",
    "does_not_trust_offer",
    "needs_proof_or_case_study",
    "unclear_value",
    "comparing_competitor",
    "not_enough_need",
    "wrong_customer_fit",
    "not_qualified",
    "missed_call",
    "cancelled_call",
    "stopped_responding",
    "needs_more_information",
    "contract_not_signed",
    "payment_not_completed",
    "payment_failed",
    "refund_requested",
    "internal_team_delay",
    "system_or_link_issue",
    "language_barrier",
    "timezone_issue",
    "issue_already_solved",
    "other",
    "unknown",
}

ALLOWED_DTI_BUYING_INTENT = {"very_high", "high", "medium", "low", "very_low", "unknown"}
ALLOWED_DTI_LEAD_QUALITY = {
    "high_quality",
    "medium_quality",
    "low_quality",
    "unqualified",
    "unknown",
}
ALLOWED_DTI_PROFESSION = {
    "student",
    "employee",
    "self_employed",
    "business_owner",
    "entrepreneur",
    "freelancer",
    "trader_or_investor",
    "finance_or_accounting",
    "sales_or_marketing",
    "healthcare",
    "education",
    "technology",
    "engineering",
    "construction_or_trades",
    "hospitality",
    "retail",
    "real_estate",
    "transport_or_logistics",
    "creative_or_media",
    "government_or_public_sector",
    "unemployed",
    "retired",
    "other",
    "unknown",
}
ALLOWED_DTI_EMPLOYMENT = {
    "full_time",
    "part_time",
    "self_employed",
    "student",
    "business_owner",
    "unemployed",
    "retired",
    "unknown",
}


@dataclass
class ValidationCheck:
    name: str
    severity: str
    passed: bool
    expected: str
    actual: str
    details: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the seeded Hermon demo dataset.")
    parser.add_argument("--org-id", required=True)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--export-json")
    parser.add_argument("--denylist-file")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> str:
    org_id = str(args.org_id or "").strip()
    if not org_id:
        raise ValueError("--org-id is required and cannot be empty.")
    if org_id != DUMMY_ORG_ID:
        raise ValueError(f"Refusing to validate {org_id!r}; only {DUMMY_ORG_ID!r} is allowed.")
    if org_id in BLOCKED_ORG_IDS:
        raise ValueError("Refusing to validate a known live client organization.")
    if not BLOCKED_ORG_IDS:
        print("Warning: BLOCKED_ORG_IDS is empty. Running for dummy org only.")
    return org_id


def get_engine() -> Engine:
    settings = get_database_settings()
    database_url = (
        os.getenv("SUPABASE_READONLY_DB_URL")
        or settings.database_url
        or os.getenv("DATABASE_URL")
    )
    if not database_url:
        raise RuntimeError("Missing read-only database URL.")
    return create_engine(_sqlalchemy_psycopg_url(database_url), pool_pre_ping=True, future=True)


def _sqlalchemy_psycopg_url(database_url: str) -> str:
    clean = database_url.strip()
    if clean.startswith("postgresql://"):
        return clean.replace("postgresql://", "postgresql+psycopg://", 1)
    if clean.startswith("postgres://"):
        return clean.replace("postgres://", "postgresql+psycopg://", 1)
    return clean


class DemoValidator:
    def __init__(self, conn: Connection, org_id: str, *, verbose: bool = False) -> None:
        self.conn = conn
        self.org_id = org_id
        self.verbose = verbose
        self.checks: list[ValidationCheck] = []
        self.row_counts: dict[str, int] = {}
        self.money_totals_minor: dict[str, int] = {}
        self.money_totals_eur: dict[str, str] = {}
        self._table_exists_cache: dict[str, bool] = {}

    def table_exists(self, table: str) -> bool:
        if table not in self._table_exists_cache:
            self._table_exists_cache[table] = bool(
                self.conn.execute(
                    text(
                        """
                        SELECT EXISTS (
                          SELECT 1
                          FROM information_schema.tables
                          WHERE table_schema = 'public'
                            AND table_name = :table
                        )
                        """
                    ),
                    {"table": table},
                ).scalar_one()
            )
        return self._table_exists_cache[table]

    def scalar(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        clean_params = {"org_id": self.org_id}
        if params:
            clean_params.update(params)
        return self.conn.execute(text(sql), clean_params).scalar_one()

    def rows(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        clean_params = {"org_id": self.org_id}
        if params:
            clean_params.update(params)
        return [dict(row) for row in self.conn.execute(text(sql), clean_params).mappings()]

    def add(
        self,
        name: str,
        severity: str,
        passed: bool,
        expected: str,
        actual: str,
        details: str | None = None,
    ) -> None:
        check = ValidationCheck(name, severity, passed, expected, actual, details)
        self.checks.append(check)
        if self.verbose:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {severity}: {name} - {actual}")

    def check_zero(self, name: str, severity: str, sql: str, *, expected: str = "0 offending rows") -> None:
        count = int(self.scalar(sql) or 0)
        self.add(name, severity, count == 0, expected, f"{count} offending rows")

    def check_count(self, name: str, severity: str, sql: str, expected_count: int) -> int:
        count = int(self.scalar(sql) or 0)
        self.add(name, severity, count == expected_count, str(expected_count), str(count))
        return count

    def check_distribution(
        self,
        name: str,
        severity: str,
        sql: str,
        expected: dict[str, int],
    ) -> None:
        rows = self.rows(sql)
        actual = {str(row["bucket"]): int(row["row_count"]) for row in rows}
        self.add(name, severity, actual == expected, json.dumps(expected, sort_keys=True), json.dumps(actual, sort_keys=True))

    def count_sql(self, table: str) -> str:
        if table == "traffic_attributions":
            return """
            SELECT COUNT(*)::int
            FROM traffic_attributions ta
            JOIN opt_ins o ON o.id = ta.opt_in_id
            WHERE o.clerk_org_id = :org_id
            """
        if table == "opt_in_question_answers":
            return """
            SELECT COUNT(*)::int
            FROM opt_in_question_answers qa
            JOIN opt_ins o ON o.id = qa.opt_in_id
            WHERE o.clerk_org_id = :org_id
            """
        return f"SELECT COUNT(*)::int FROM {table} WHERE clerk_org_id = :org_id"

    def optional_count_sql(self, table: str) -> str | None:
        if table == "payment_links":
            return """
            SELECT COUNT(*)::int
            FROM payment_links pl
            JOIN payments p ON p.id = pl.payment_id
            WHERE p.clerk_org_id = :org_id
            """
        if table == "contract_subscriptions":
            return """
            SELECT COUNT(*)::int
            FROM contract_subscriptions cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.clerk_org_id = :org_id
            """
        if table == "subscription_checkout_links":
            if not self.table_exists("contract_subscriptions"):
                return None
            return """
            SELECT COUNT(*)::int
            FROM subscription_checkout_links scl
            JOIN contract_subscriptions cs ON cs.id = scl.subscription_id
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.clerk_org_id = :org_id
            """
        return f"SELECT COUNT(*)::int FROM {table} WHERE clerk_org_id = :org_id"

    def admin_count_sql(self, table: str) -> str | None:
        if table in {"provider_integrations", "audit_logs", "notification_logs"}:
            return f"SELECT COUNT(*)::int FROM {table} WHERE clerk_org_id = :org_id"
        if table == "provider_credentials":
            if not self.table_exists("provider_integrations"):
                return None
            return """
            SELECT COUNT(*)::int
            FROM provider_credentials pc
            JOIN provider_integrations pi ON pi.id = pc.integration_id
            WHERE pi.clerk_org_id = :org_id
            """
        if table == "webhook_events":
            if not self.table_exists("provider_integrations"):
                return None
            return """
            SELECT COUNT(*)::int
            FROM webhook_events we
            JOIN provider_integrations pi ON pi.id = we.integration_id
            WHERE pi.clerk_org_id = :org_id
            """
        if table == "integration_health_checks":
            if not self.table_exists("provider_integrations"):
                return None
            return """
            SELECT COUNT(*)::int
            FROM integration_health_checks ihc
            JOIN provider_integrations pi ON pi.id = ihc.integration_id
            WHERE pi.clerk_org_id = :org_id
            """
        return None

    def validate(self, denylist: list[str]) -> None:
        self.organization_and_counts()
        self.monthly_trend()
        self.source_quality()
        self.scenario_and_funnel()
        self.relationship_integrity()
        self.date_sequence()
        self.appointment_fathom()
        self.contracts()
        self.payments_and_revenue()
        self.refunds()
        self.diagnostic_snapshot()
        self.diagnostic_text_insights()
        self.acquisition()
        self.safe_data(denylist)
        self.chatbot_reconciliations()
        self.unsupported_metric_guardrails()
        self.collect_money_totals()

    def organization_and_counts(self) -> None:
        for table in EXPECTED_COUNTS:
            if not self.table_exists(table):
                self.add(f"{table}_exists", "critical", False, "required table exists", "missing")
                continue
            self.add(f"{table}_exists", "critical", True, "required table exists", "exists")
            count = self.check_count(
                f"{table}_row_count",
                "critical",
                self.count_sql(table),
                EXPECTED_COUNTS[table],
            )
            self.row_counts[table] = count

        for table in OPTIONAL_TABLES:
            if not self.table_exists(table):
                self.add(f"{table}_optional_exists", "info", True, "optional table may be absent", "absent")
                continue
            sql = self.optional_count_sql(table)
            if not sql:
                self.add(f"{table}_optional_count", "info", True, "skipped missing dependency", "skipped")
                continue
            self.check_zero(f"{table}_not_seeded", "high", sql)

        for table in ADMIN_TABLES:
            if not self.table_exists(table):
                self.add(f"{table}_admin_exists", "info", True, "admin/raw table may be absent", "absent")
                continue
            sql = self.admin_count_sql(table)
            if sql:
                self.check_zero(f"{table}_not_seeded", "high", sql)

        self.check_zero(
            "no_demo_created_rows_under_other_org",
            "critical",
            """
            WITH demo_rows AS (
              SELECT clerk_org_id FROM sales_statuses WHERE created_by = 'demo_seed_script'
              UNION ALL SELECT clerk_org_id FROM marketing_sources WHERE created_by = 'demo_seed_script'
              UNION ALL SELECT clerk_org_id FROM programs WHERE created_by = 'demo_seed_script'
              UNION ALL SELECT clerk_org_id FROM appointment_event_types WHERE created_by = 'demo_seed_script'
              UNION ALL SELECT clerk_org_id FROM leads WHERE external_reference LIKE 'demo:%'
              UNION ALL SELECT clerk_org_id FROM opt_ins WHERE external_reference LIKE 'demo-optin-%'
              UNION ALL SELECT clerk_org_id FROM appointments WHERE external_reference LIKE 'demo-appointment-%'
              UNION ALL SELECT clerk_org_id FROM fathom_call_records WHERE fathom_call_id LIKE 'demo_fathom_%'
              UNION ALL SELECT clerk_org_id FROM contracts WHERE created_by = 'demo_seed_script'
              UNION ALL SELECT clerk_org_id FROM payments WHERE created_by = 'demo_seed_script'
              UNION ALL SELECT clerk_org_id FROM refunds WHERE created_by = 'demo_seed_script'
              UNION ALL SELECT clerk_org_id FROM diagnostic_text_insights WHERE clerk_org_id = :org_id
            )
            SELECT COUNT(*)::int
            FROM demo_rows
            WHERE clerk_org_id <> :org_id
            """,
        )

    def monthly_trend(self) -> None:
        self.check_distribution(
            "monthly_lead_distribution",
            "critical",
            """
            SELECT to_char(date_trunc('month', created_at), 'YYYY-MM') AS bucket, COUNT(*)::int AS row_count
            FROM leads
            WHERE clerk_org_id = :org_id AND is_deleted = false
            GROUP BY 1 ORDER BY 1
            """,
            MONTHLY_LEADS,
        )
        self.check_zero(
            "lead_created_at_within_demo_window",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM leads
            WHERE clerk_org_id = :org_id
              AND is_deleted = false
              AND (created_at < '2025-11-01'::timestamptz OR created_at >= '2026-05-01'::timestamptz)
            """,
        )
        trend_rows = self.rows(
            """
            SELECT to_char(date_trunc('month', created_at), 'YYYY-MM') AS bucket, COUNT(*)::int AS row_count
            FROM leads
            WHERE clerk_org_id = :org_id AND is_deleted = false
            GROUP BY 1 ORDER BY 1
            """
        )
        trend = {str(row["bucket"]): int(row["row_count"]) for row in trend_rows}
        trend_ok = (
            len(set(trend.values())) > 1
            and trend.get("2026-01", 0) > trend.get("2025-12", 0)
            and trend.get("2026-02", 0) < trend.get("2026-01", 0)
            and trend.get("2026-03", 0) >= trend.get("2026-02", 0)
            and trend.get("2026-04", 0) > trend.get("2026-03", 0)
        )
        self.add("monthly_trend_shape", "high", trend_ok, "growth/drop/recovery story", json.dumps(trend, sort_keys=True))

    def source_quality(self) -> None:
        self.check_distribution(
            "source_distribution",
            "critical",
            """
            SELECT first_source_name AS bucket, COUNT(*)::int AS row_count
            FROM leads
            WHERE clerk_org_id = :org_id AND is_deleted = false
            GROUP BY first_source_name ORDER BY first_source_name
            """,
            SOURCE_COUNTS,
        )
        self.check_zero(
            "lead_source_quality",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM leads l
            LEFT JOIN marketing_sources first_ms
              ON first_ms.id = l.first_source_id AND first_ms.clerk_org_id = l.clerk_org_id
            LEFT JOIN marketing_sources last_ms
              ON last_ms.id = l.last_source_id AND last_ms.clerk_org_id = l.clerk_org_id
            WHERE l.clerk_org_id = :org_id
              AND (
                NULLIF(BTRIM(l.first_source_name), '') IS NULL
                OR NULLIF(BTRIM(l.last_source_name), '') IS NULL
                OR l.first_source_name IN ('Unknown', 'Not Set', 'N/A', 'Blank', 'No Source', 'Other Unknown')
                OR l.last_source_name IN ('Unknown', 'Not Set', 'N/A', 'Blank', 'No Source', 'Other Unknown')
                OR first_ms.id IS NULL
                OR last_ms.id IS NULL
              )
            """,
        )
        self.check_zero(
            "snapshot_source_quality_flags",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM diagnostic_lead_snapshot
            WHERE clerk_org_id = :org_id
              AND (
                has_missing_first_source
                OR has_missing_last_source
                OR has_orphaned_first_source_id
                OR has_orphaned_last_source_id
                OR has_unknown_source
                OR has_revenue_without_source
                OR source_confidence NOT IN ('high', 'medium')
                OR (source_confidence = 'medium' AND source_changed = false)
              )
            """,
        )

    def scenario_and_funnel(self) -> None:
        self.check_distribution(
            "scenario_distribution_from_seed_markers",
            "critical",
            """
            SELECT split_part(external_reference, ':', 2) AS bucket, COUNT(*)::int AS row_count
            FROM leads
            WHERE clerk_org_id = :org_id AND external_reference LIKE 'demo:%'
            GROUP BY 1 ORDER BY 1
            """,
            SCENARIO_COUNTS,
        )
        self.check_zero(
            "scenario_behavior_consistency",
            "critical",
            """
            WITH base AS (
              SELECT
                l.id,
                split_part(l.external_reference, ':', 2) AS scenario,
                ss.role::text AS status_role,
                COUNT(DISTINCT a.id)::int AS appointment_count,
                COUNT(DISTINCT a.id) FILTER (
                  WHERE a.schedule_time < NOW()
                    AND a.no_show = false
                    AND outcome.role::text NOT IN ('CANCELED', 'RESCHEDULED')
                )::int AS completed_count,
                COUNT(DISTINCT c.id)::int AS contract_count,
                COUNT(DISTINCT c.id) FILTER (WHERE c.status::text = 'SIGNED')::int AS signed_count,
                COUNT(DISTINCT p.id)::int AS payment_count,
                COUNT(DISTINCT p.id) FILTER (WHERE p.status::text = 'PAID')::int AS paid_count
              FROM leads l
              LEFT JOIN sales_statuses ss ON ss.id = l.status_id AND ss.clerk_org_id = l.clerk_org_id
              LEFT JOIN appointments a ON a.lead_id = l.id AND a.clerk_org_id = l.clerk_org_id AND a.is_deleted = false
              LEFT JOIN sales_statuses outcome ON outcome.id = a.outcome_id AND outcome.clerk_org_id = a.clerk_org_id
              LEFT JOIN contracts c ON c.lead_id = l.id AND c.clerk_org_id = l.clerk_org_id AND c.is_deleted = false
              LEFT JOIN payments p ON p.lead_id = l.id AND p.clerk_org_id = l.clerk_org_id AND p.is_deleted = false
              WHERE l.clerk_org_id = :org_id AND l.external_reference LIKE 'demo:%'
              GROUP BY l.id, scenario, ss.role
            )
            SELECT COUNT(*)::int
            FROM base
            WHERE (
              scenario = 'paid_converted' AND (paid_count = 0 OR signed_count = 0)
            ) OR (
              scenario = 'completed_not_signed' AND (completed_count = 0 OR signed_count > 0 OR paid_count > 0)
            ) OR (
              scenario = 'signed_not_paid' AND (signed_count = 0 OR paid_count > 0 OR payment_count = 0)
            ) OR (
              scenario = 'booked_not_completed' AND (appointment_count = 0 OR completed_count > 0 OR contract_count > 0 OR payment_count > 0)
            ) OR (
              scenario = 'lead_only' AND (appointment_count > 0 OR contract_count > 0 OR payment_count > 0)
            ) OR (
              scenario = 'lost' AND status_role <> 'LOST'
            ) OR (
              scenario = 'unqualified' AND (status_role <> 'UNQUALIFIED' OR payment_count > 0)
            )
            """,
        )
        self.check_zero(
            "snapshot_funnel_behavior",
            "high",
            """
            SELECT COUNT(*)::int
            FROM diagnostic_lead_snapshot
            WHERE clerk_org_id = :org_id
              AND (
                (funnel_stage = 'paid' AND net_collected_amount <= 0)
                OR (funnel_stage = 'completed_not_signed' AND (completed_call_count = 0 OR signed_contract_count > 0))
                OR (funnel_stage = 'signed_not_paid' AND (signed_contract_count = 0 OR paid_payment_count > 0))
                OR (funnel_stage = 'booked_not_completed' AND (appointment_count = 0 OR completed_call_count > 0))
                OR (funnel_stage = 'lead_only' AND appointment_count > 0)
                OR (funnel_stage = 'lost' AND current_status_role <> 'LOST')
                OR (funnel_stage = 'unqualified' AND current_status_role <> 'UNQUALIFIED')
              )
            """,
        )
        stage_count = int(
            self.scalar(
                """
                SELECT COUNT(DISTINCT funnel_stage)::int
                FROM diagnostic_lead_snapshot
                WHERE clerk_org_id = :org_id
                """
            )
            or 0
        )
        self.add("snapshot_has_multiple_funnel_stages", "medium", stage_count >= 6, "at least 6 stages", str(stage_count))

    def relationship_integrity(self) -> None:
        checks = {
            "lead_status_join": """
              SELECT COUNT(*)::int FROM leads l
              LEFT JOIN sales_statuses ss ON ss.id = l.status_id AND ss.clerk_org_id = l.clerk_org_id
              WHERE l.clerk_org_id = :org_id AND ss.id IS NULL
            """,
            "lead_first_source_join": """
              SELECT COUNT(*)::int FROM leads l
              LEFT JOIN marketing_sources ms ON ms.id = l.first_source_id AND ms.clerk_org_id = l.clerk_org_id
              WHERE l.clerk_org_id = :org_id AND ms.id IS NULL
            """,
            "lead_last_source_join": """
              SELECT COUNT(*)::int FROM leads l
              LEFT JOIN marketing_sources ms ON ms.id = l.last_source_id AND ms.clerk_org_id = l.clerk_org_id
              WHERE l.clerk_org_id = :org_id AND ms.id IS NULL
            """,
            "opt_in_lead_join": """
              SELECT COUNT(*)::int FROM opt_ins o
              LEFT JOIN leads l ON l.id = o.lead_id AND l.clerk_org_id = o.clerk_org_id
              WHERE o.clerk_org_id = :org_id AND l.id IS NULL
            """,
            "traffic_opt_in_join": """
              SELECT COUNT(*)::int FROM traffic_attributions ta
              LEFT JOIN opt_ins o ON o.id = ta.opt_in_id
              WHERE o.clerk_org_id = :org_id AND o.id IS NULL
            """,
            "answer_opt_in_join": """
              SELECT COUNT(*)::int FROM opt_in_question_answers qa
              LEFT JOIN opt_ins o ON o.id = qa.opt_in_id
              WHERE o.clerk_org_id = :org_id AND o.id IS NULL
            """,
            "appointment_relationships": """
              SELECT COUNT(*)::int FROM appointments a
              LEFT JOIN leads l ON l.id = a.lead_id AND l.clerk_org_id = a.clerk_org_id
              LEFT JOIN appointment_event_types aet ON aet.id = a.appointment_event_type_id AND aet.clerk_org_id = a.clerk_org_id
              LEFT JOIN sales_statuses ss ON ss.id = a.outcome_id AND ss.clerk_org_id = a.clerk_org_id
              WHERE a.clerk_org_id = :org_id AND (l.id IS NULL OR aet.id IS NULL OR ss.id IS NULL)
            """,
            "fathom_appointment_join": """
              SELECT COUNT(*)::int FROM fathom_call_records f
              LEFT JOIN appointments a ON a.id = f.appointment_id AND a.clerk_org_id = f.clerk_org_id
              WHERE f.clerk_org_id = :org_id AND a.id IS NULL
            """,
            "contract_relationships": """
              SELECT COUNT(*)::int FROM contracts c
              LEFT JOIN leads l ON l.id = c.lead_id AND l.clerk_org_id = c.clerk_org_id
              LEFT JOIN programs p ON p.id = c.program_id AND p.clerk_org_id = c.clerk_org_id
              WHERE c.clerk_org_id = :org_id AND (l.id IS NULL OR p.id IS NULL)
            """,
            "payment_relationships": """
              SELECT COUNT(*)::int FROM payments p
              LEFT JOIN leads l ON l.id = p.lead_id AND l.clerk_org_id = p.clerk_org_id
              LEFT JOIN contracts c ON c.id = p.contract_id AND c.clerk_org_id = p.clerk_org_id
              WHERE p.clerk_org_id = :org_id AND (l.id IS NULL OR c.id IS NULL)
            """,
            "refund_payment_join": """
              SELECT COUNT(*)::int FROM refunds r
              LEFT JOIN payments p ON p.id = r.payment_id AND p.clerk_org_id = r.clerk_org_id
              WHERE r.clerk_org_id = :org_id AND p.id IS NULL
            """,
            "diagnostic_text_lead_join": """
              SELECT COUNT(*)::int FROM diagnostic_text_insights d
              LEFT JOIN leads l ON l.id = d.lead_id AND l.clerk_org_id = d.clerk_org_id
              WHERE d.clerk_org_id = :org_id AND l.id IS NULL
            """,
            "diagnostic_snapshot_lead_join": """
              SELECT COUNT(*)::int FROM diagnostic_lead_snapshot d
              LEFT JOIN leads l ON l.id = d.lead_id AND l.clerk_org_id = d.clerk_org_id
              WHERE d.clerk_org_id = :org_id AND l.id IS NULL
            """,
            "cross_org_parent_child_mismatch": """
              WITH mismatches AS (
                SELECT a.id::text FROM appointments a JOIN leads l ON l.id = a.lead_id WHERE a.clerk_org_id = :org_id AND a.clerk_org_id <> l.clerk_org_id
                UNION ALL SELECT f.id::text FROM fathom_call_records f JOIN appointments a ON a.id = f.appointment_id WHERE f.clerk_org_id = :org_id AND f.clerk_org_id <> a.clerk_org_id
                UNION ALL SELECT c.id::text FROM contracts c JOIN leads l ON l.id = c.lead_id WHERE c.clerk_org_id = :org_id AND c.clerk_org_id <> l.clerk_org_id
                UNION ALL SELECT p.id::text FROM payments p JOIN leads l ON l.id = p.lead_id WHERE p.clerk_org_id = :org_id AND p.clerk_org_id <> l.clerk_org_id
                UNION ALL SELECT p.id::text FROM payments p JOIN contracts c ON c.id = p.contract_id WHERE p.clerk_org_id = :org_id AND p.clerk_org_id <> c.clerk_org_id
                UNION ALL SELECT r.id::text FROM refunds r JOIN payments p ON p.id = r.payment_id WHERE r.clerk_org_id = :org_id AND r.clerk_org_id <> p.clerk_org_id
              )
              SELECT COUNT(*)::int FROM mismatches
            """,
        }
        for name, sql in checks.items():
            self.check_zero(name, "critical", sql)

    def date_sequence(self) -> None:
        date_checks = {
            "opt_in_after_lead": """
              SELECT COUNT(*)::int FROM opt_ins o JOIN leads l ON l.id = o.lead_id
              WHERE o.clerk_org_id = :org_id AND o.created_at < l.created_at
            """,
            "traffic_after_opt_in": """
              SELECT COUNT(*)::int FROM traffic_attributions ta JOIN opt_ins o ON o.id = ta.opt_in_id
              WHERE o.clerk_org_id = :org_id AND ta.created_at < o.created_at
            """,
            "appointment_after_lead": """
              SELECT COUNT(*)::int FROM appointments a JOIN leads l ON l.id = a.lead_id
              WHERE a.clerk_org_id = :org_id AND (a.schedule_time < l.created_at OR a.created_at < l.created_at)
            """,
            "fathom_timeline": """
              SELECT COUNT(*)::int
              FROM fathom_call_records f JOIN appointments a ON a.id = f.appointment_id
              WHERE f.clerk_org_id = :org_id
                AND (
                  f.call_started_at < a.schedule_time
                  OR f.call_ended_at <= f.call_started_at
                  OR f.created_at < f.call_started_at
                  OR COALESCE(f.call_duration_seconds, 0) <= 0
                  OR ABS(EXTRACT(EPOCH FROM (f.call_ended_at - f.call_started_at)) - f.call_duration_seconds) > 60
                )
            """,
            "contract_timeline": """
              WITH latest_completed AS (
                SELECT a.lead_id, MAX(f.call_ended_at) AS latest_call_ended_at
                FROM appointments a JOIN fathom_call_records f ON f.appointment_id = a.id AND f.clerk_org_id = a.clerk_org_id
                WHERE a.clerk_org_id = :org_id
                GROUP BY a.lead_id
              )
              SELECT COUNT(*)::int
              FROM contracts c
              JOIN leads l ON l.id = c.lead_id
              LEFT JOIN latest_completed lc ON lc.lead_id = c.lead_id
              WHERE c.clerk_org_id = :org_id
                AND (
                  c.created_at < l.created_at
                  OR (lc.latest_call_ended_at IS NOT NULL AND c.sent_at < lc.latest_call_ended_at)
                  OR (c.signed_at IS NOT NULL AND c.signed_at < c.sent_at)
                  OR (c.voided_at IS NOT NULL AND c.voided_at < c.sent_at)
                  OR (c.status::text = 'SIGNED' AND c.signed_at IS NULL)
                  OR (c.status::text IN ('SENT', 'VIEWED') AND c.sent_at IS NULL)
                  OR (c.status::text = 'VOIDED' AND c.voided_at IS NULL)
                )
            """,
            "payment_timeline": """
              SELECT COUNT(*)::int
              FROM payments p JOIN contracts c ON c.id = p.contract_id
              WHERE p.clerk_org_id = :org_id
                AND (
                  p.created_at < c.created_at
                  OR (c.signed_at IS NOT NULL AND p.due_date IS NOT NULL AND p.due_date < c.signed_at)
                  OR (p.status::text = 'PAID' AND (p.paid_at IS NULL OR p.paid_at < c.signed_at))
                  OR (p.status::text = 'PENDING' AND p.due_date IS NULL)
                  OR (p.status::text = 'FAILED' AND p.due_date IS NULL AND NULLIF(BTRIM(p.failure_reason), '') IS NULL)
                )
            """,
            "refund_timeline": """
              SELECT COUNT(*)::int
              FROM refunds r JOIN payments p ON p.id = r.payment_id
              WHERE r.clerk_org_id = :org_id
                AND (
                  r.created_at < p.paid_at
                  OR (r.refunded_at IS NOT NULL AND r.refunded_at < p.paid_at)
                  OR r.amount > p.amount
                  OR p.status::text NOT IN ('PAID', 'REFUNDED')
                )
            """,
        }
        for name, sql in date_checks.items():
            self.check_zero(name, "critical", sql)
        answer_timing_rows = self.rows(
            """
            SELECT qa.question AS bucket, COUNT(*)::int AS row_count
            FROM opt_in_question_answers qa
            JOIN opt_ins o ON o.id = qa.opt_in_id
            WHERE o.clerk_org_id = :org_id AND qa.created_at < o.created_at
            GROUP BY qa.question
            ORDER BY qa.question
            """
        )
        answer_timing_total = sum(int(row["row_count"]) for row in answer_timing_rows)
        answer_timing_details = None
        if answer_timing_total:
            answer_timing_details = "by_question: " + ", ".join(
                f"{row['bucket']}={int(row['row_count'])}" for row in answer_timing_rows
            )
        self.add(
            "answers_after_opt_in",
            "critical",
            answer_timing_total == 0,
            "0 offending rows",
            f"{answer_timing_total} offending rows",
            answer_timing_details,
        )

    def appointment_fathom(self) -> None:
        self.check_zero(
            "strict_fathom_coverage",
            "critical",
            """
            WITH appointment_rows AS (
              SELECT
                a.id,
                a.schedule_time,
                a.no_show,
                a.is_deleted,
                ss.role::text AS outcome_role,
                COUNT(f.id)::int AS fathom_count
              FROM appointments a
              JOIN sales_statuses ss ON ss.id = a.outcome_id AND ss.clerk_org_id = a.clerk_org_id
              LEFT JOIN fathom_call_records f ON f.appointment_id = a.id AND f.clerk_org_id = a.clerk_org_id
              WHERE a.clerk_org_id = :org_id
              GROUP BY a.id, a.schedule_time, a.no_show, a.is_deleted, ss.role
            )
            SELECT COUNT(*)::int
            FROM appointment_rows
            WHERE (
              schedule_time < NOW()
              AND no_show = false
              AND is_deleted = false
              AND outcome_role NOT IN ('CANCELED', 'RESCHEDULED')
              AND fathom_count <> 1
            )
            OR (
              (no_show = true OR is_deleted = true OR outcome_role IN ('CANCELED', 'RESCHEDULED') OR schedule_time >= NOW())
              AND fathom_count <> 0
            )
            """,
        )
        self.check_count(
            "completed_appointment_count",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM appointments a
            JOIN sales_statuses ss ON ss.id = a.outcome_id AND ss.clerk_org_id = a.clerk_org_id
            WHERE a.clerk_org_id = :org_id
              AND a.schedule_time < NOW()
              AND a.no_show = false
              AND a.is_deleted = false
              AND ss.role::text NOT IN ('CANCELED', 'RESCHEDULED')
            """,
            285,
        )
        self.check_zero(
            "fathom_content_quality",
            "high",
            """
            SELECT COUNT(*)::int
            FROM fathom_call_records
            WHERE clerk_org_id = :org_id
              AND (
                NULLIF(BTRIM(summary), '') IS NULL
                OR jsonb_array_length(COALESCE(key_points::jsonb, '[]'::jsonb)) = 0
                OR jsonb_array_length(COALESCE(action_items::jsonb, '[]'::jsonb)) = 0
                OR jsonb_typeof(COALESCE(objections::jsonb, '[]'::jsonb)) <> 'array'
                OR NULLIF(BTRIM(ai_generated_title), '') IS NULL
                OR ai_confidence_score < 0
                OR ai_confidence_score > 1
                OR call_duration_seconds < 600
                OR call_duration_seconds > 4500
                OR raw_payload IS NOT NULL
                OR recording_url IS NOT NULL
                OR transcript_url IS NOT NULL
              )
            """,
        )

    def contracts(self) -> None:
        self.check_zero(
            "contract_business_rules",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM contracts c
            JOIN leads l ON l.id = c.lead_id AND l.clerk_org_id = c.clerk_org_id
            LEFT JOIN sales_statuses ss ON ss.id = l.status_id AND ss.clerk_org_id = l.clerk_org_id
            WHERE c.clerk_org_id = :org_id
              AND (
                c.currency <> 'EUR'
                OR COALESCE(c.total_value, 0) <= 0
                OR (c.status::text = 'SIGNED' AND c.signed_at IS NULL)
                OR (c.status::text IN ('SENT', 'VIEWED') AND c.sent_at IS NULL)
                OR (c.status::text = 'VOIDED' AND c.voided_at IS NULL)
                OR ss.role::text = 'UNQUALIFIED'
                OR l.external_reference LIKE 'demo:lead_only:%'
                OR l.external_reference LIKE 'demo:booked_not_completed:%'
                OR (l.external_reference LIKE 'demo:completed_not_signed:%' AND c.status::text = 'SIGNED')
              )
            """,
        )
        self.check_zero(
            "paid_and_signed_not_paid_have_signed_contracts",
            "critical",
            """
            WITH lead_contracts AS (
              SELECT l.id, l.external_reference, COUNT(c.id) FILTER (WHERE c.status::text = 'SIGNED')::int AS signed_count
              FROM leads l LEFT JOIN contracts c ON c.lead_id = l.id AND c.clerk_org_id = l.clerk_org_id
              WHERE l.clerk_org_id = :org_id
              GROUP BY l.id, l.external_reference
            )
            SELECT COUNT(*)::int
            FROM lead_contracts
            WHERE (external_reference LIKE 'demo:paid_converted:%' OR external_reference LIKE 'demo:signed_not_paid:%')
              AND signed_count = 0
            """,
        )
        self.reconcile_sum(
            "signed_contract_value_breakdowns",
            "high",
            "contracts",
            "total_value",
            "status::text = 'SIGNED'",
            [
                "program_id",
                "date_trunc('month', signed_at)",
                "lead_id",
            ],
        )

    def payments_and_revenue(self) -> None:
        self.check_zero(
            "payment_business_rules",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM payments p
            JOIN leads l ON l.id = p.lead_id AND l.clerk_org_id = p.clerk_org_id
            WHERE p.clerk_org_id = :org_id
              AND (
                p.currency <> 'EUR'
                OR p.amount <= 0
                OR (p.status::text = 'PAID' AND p.paid_at IS NULL)
                OR (p.status::text = 'PENDING' AND p.due_date IS NULL)
                OR (p.status::text = 'FAILED' AND p.due_date IS NULL AND NULLIF(BTRIM(p.failure_reason), '') IS NULL)
                OR (l.external_reference LIKE 'demo:completed_not_signed:%' AND p.status::text = 'PAID')
                OR l.external_reference LIKE 'demo:lead_only:%'
                OR l.external_reference LIKE 'demo:booked_not_completed:%'
                OR l.external_reference LIKE 'demo:unqualified:%'
              )
            """,
        )
        self.check_zero(
            "scenario_payment_requirements",
            "critical",
            """
            WITH lead_payments AS (
              SELECT
                l.id,
                l.external_reference,
                COUNT(p.id) FILTER (WHERE p.status::text = 'PAID')::int AS paid_count,
                COUNT(p.id) FILTER (WHERE p.status::text IN ('PENDING', 'FAILED'))::int AS open_count
              FROM leads l
              LEFT JOIN payments p ON p.lead_id = l.id AND p.clerk_org_id = l.clerk_org_id
              WHERE l.clerk_org_id = :org_id
              GROUP BY l.id, l.external_reference
            )
            SELECT COUNT(*)::int
            FROM lead_payments
            WHERE (external_reference LIKE 'demo:paid_converted:%' AND paid_count = 0)
               OR (external_reference LIKE 'demo:signed_not_paid:%' AND open_count = 0)
            """,
        )
        for date_part in ("day", "week", "month"):
            self.reconcile_period_net_revenue(date_part)
        self.reconcile_sum("paid_revenue_by_source", "high", "payments", "amount", "status::text = 'PAID'", ["lead_id", "payment_provider", "type"])
        self.check_zero(
            "payment_status_amounts_reconcile",
            "high",
            """
            WITH total AS (
              SELECT COALESCE(SUM(amount),0) AS amount FROM payments WHERE clerk_org_id = :org_id
            ),
            by_status AS (
              SELECT COALESCE(SUM(amount),0) AS amount
              FROM (
                SELECT status, SUM(amount) AS amount
                FROM payments
                WHERE clerk_org_id = :org_id
                GROUP BY status
              ) grouped
            )
            SELECT CASE WHEN (SELECT amount FROM total) = (SELECT amount FROM by_status) THEN 0 ELSE 1 END::int
            """,
        )

    def refunds(self) -> None:
        self.check_zero(
            "refund_business_rules",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM refunds r
            JOIN payments p ON p.id = r.payment_id AND p.clerk_org_id = r.clerk_org_id
            WHERE r.clerk_org_id = :org_id
              AND (
                p.status::text NOT IN ('PAID', 'REFUNDED')
                OR r.amount <= 0
                OR r.amount > p.amount
                OR r.currency <> p.currency
                OR r.payment_provider <> p.payment_provider
                OR (r.status::text = 'SUCCEEDED' AND r.refunded_at IS NULL)
                OR r.refunded_at < p.paid_at
              )
            """,
        )
        self.reconcile_sum("refund_amount_breakdowns", "high", "refunds", "amount", "status::text = 'SUCCEEDED'", ["date_trunc('month', COALESCE(refunded_at, created_at))", "payment_provider"])

    def diagnostic_snapshot(self) -> None:
        self.check_count("snapshot_matches_active_leads", "critical", "SELECT COUNT(*)::int FROM diagnostic_lead_snapshot WHERE clerk_org_id = :org_id", 500)
        self.check_zero(
            "snapshot_base_table_consistency",
            "critical",
            """
            WITH lead_base AS (
              SELECT id AS lead_id
              FROM leads
              WHERE clerk_org_id = :org_id AND is_deleted = false
            ),
            opt_ins_by_lead AS (
              SELECT lead_id, COUNT(*)::int AS opt_in_count
              FROM opt_ins
              WHERE clerk_org_id = :org_id
              GROUP BY lead_id
            ),
            appointments_by_lead AS (
              SELECT
                a.lead_id,
                COUNT(*)::int AS appointment_count,
                COUNT(*) FILTER (
                  WHERE a.schedule_time < NOW()
                    AND a.no_show = false
                    AND outcome.role::text NOT IN ('CANCELED','RESCHEDULED')
                )::int AS completed_call_count
              FROM appointments a
              LEFT JOIN sales_statuses outcome
                ON outcome.id = a.outcome_id AND outcome.clerk_org_id = a.clerk_org_id
              WHERE a.clerk_org_id = :org_id AND a.is_deleted = false
              GROUP BY a.lead_id
            ),
            fathom_by_lead AS (
              SELECT a.lead_id, COUNT(f.id)::int AS fathom_record_count
              FROM fathom_call_records f
              JOIN appointments a ON a.id = f.appointment_id AND a.clerk_org_id = f.clerk_org_id
              WHERE f.clerk_org_id = :org_id
              GROUP BY a.lead_id
            ),
            contracts_by_lead AS (
              SELECT
                lead_id,
                COUNT(*)::int AS contract_count,
                COALESCE(SUM(total_value) FILTER (WHERE status::text = 'SIGNED') / 100.0, 0)::numeric(12,2) AS signed_contract_value
              FROM contracts
              WHERE clerk_org_id = :org_id AND is_deleted = false
              GROUP BY lead_id
            ),
            payments_by_lead AS (
              SELECT
                lead_id,
                COUNT(*)::int AS payment_count,
                COALESCE(SUM(amount) FILTER (WHERE status::text = 'PAID') / 100.0, 0)::numeric(12,2) AS gross_paid_amount
              FROM payments
              WHERE clerk_org_id = :org_id AND is_deleted = false
              GROUP BY lead_id
            ),
            refunds_by_lead AS (
              SELECT
                p.lead_id,
                COALESCE(SUM(r.amount) FILTER (WHERE r.status::text = 'SUCCEEDED') / 100.0, 0)::numeric(12,2) AS refund_amount
              FROM refunds r
              JOIN payments p ON p.id = r.payment_id AND p.clerk_org_id = r.clerk_org_id
              WHERE r.clerk_org_id = :org_id
              GROUP BY p.lead_id
            ),
            base AS (
              SELECT
                l.lead_id,
                COALESCE(o.opt_in_count, 0) AS opt_in_count,
                COALESCE(a.appointment_count, 0) AS appointment_count,
                COALESCE(a.completed_call_count, 0) AS completed_call_count,
                COALESCE(f.fathom_record_count, 0) AS fathom_record_count,
                COALESCE(c.contract_count, 0) AS contract_count,
                COALESCE(p.payment_count, 0) AS payment_count,
                COALESCE(p.gross_paid_amount, 0)::numeric(12,2) AS gross_paid_amount,
                COALESCE(r.refund_amount, 0)::numeric(12,2) AS refund_amount,
                COALESCE(c.signed_contract_value, 0)::numeric(12,2) AS signed_contract_value
              FROM lead_base l
              LEFT JOIN opt_ins_by_lead o ON o.lead_id = l.lead_id
              LEFT JOIN appointments_by_lead a ON a.lead_id = l.lead_id
              LEFT JOIN fathom_by_lead f ON f.lead_id = l.lead_id
              LEFT JOIN contracts_by_lead c ON c.lead_id = l.lead_id
              LEFT JOIN payments_by_lead p ON p.lead_id = l.lead_id
              LEFT JOIN refunds_by_lead r ON r.lead_id = l.lead_id
            )
            SELECT COUNT(*)::int
            FROM diagnostic_lead_snapshot d
            JOIN base b ON b.lead_id = d.lead_id
            WHERE d.clerk_org_id = :org_id
              AND (
                d.opt_in_count <> b.opt_in_count
                OR d.appointment_count <> b.appointment_count
                OR d.completed_call_count <> b.completed_call_count
                OR d.fathom_record_count <> b.fathom_record_count
                OR d.contract_count <> b.contract_count
                OR d.payment_count <> b.payment_count
                OR d.gross_paid_amount <> b.gross_paid_amount
                OR d.refund_amount <> b.refund_amount
                OR d.net_collected_amount <> (b.gross_paid_amount - b.refund_amount)
                OR d.signed_contract_value <> b.signed_contract_value
              )
            """,
        )
        self.check_zero(
            "snapshot_quality_flags",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM diagnostic_lead_snapshot
            WHERE clerk_org_id = :org_id
              AND (
                completed_calls_missing_fathom_count <> 0
                OR (completed_call_count > 0 AND completed_call_fathom_coverage_rate <> 100.00)
                OR has_unknown_source
                OR has_missing_first_source
                OR has_missing_last_source
                OR has_orphaned_first_source_id
                OR has_orphaned_last_source_id
                OR has_revenue_without_source
                OR has_payment_without_contract
              )
            """,
        )

    def diagnostic_text_insights(self) -> None:
        self.check_count("diagnostic_text_insights_count", "critical", "SELECT COUNT(*)::int FROM diagnostic_text_insights WHERE clerk_org_id = :org_id", 405)
        self.check_zero(
            "diagnostic_text_insight_relationships",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM diagnostic_text_insights d
            LEFT JOIN leads l ON l.id = d.lead_id AND l.clerk_org_id = d.clerk_org_id AND l.is_deleted = false
            LEFT JOIN fathom_call_records f ON f.id = d.source_record_id AND f.clerk_org_id = d.clerk_org_id AND d.source_table = 'fathom_call_records'
            WHERE d.clerk_org_id = :org_id
              AND (
                l.id IS NULL
                OR NULLIF(BTRIM(d.source_text_hash), '') IS NULL
                OR COALESCE(d.source_text_length, 0) <= 0
                OR d.extraction_status <> 'success'
                OR (d.source_table = 'fathom_call_records' AND (f.id IS NULL OR d.source_event_at IS DISTINCT FROM f.call_started_at))
              )
            """,
        )
        self.check_zero(
            "diagnostic_text_insight_allowed_values",
            "critical",
            f"""
            SELECT COUNT(*)::int
            FROM diagnostic_text_insights
            WHERE clerk_org_id = :org_id
              AND (
                reason_category NOT IN ({quoted_csv(ALLOWED_DTI_REASON_CATEGORIES)})
                OR reason_subcategory NOT IN ({quoted_csv(ALLOWED_DTI_REASON_SUBCATEGORIES)})
                OR buying_intent_level NOT IN ({quoted_csv(ALLOWED_DTI_BUYING_INTENT)})
                OR lead_quality_level NOT IN ({quoted_csv(ALLOWED_DTI_LEAD_QUALITY)})
                OR profession_category NOT IN ({quoted_csv(ALLOWED_DTI_PROFESSION)})
                OR employment_status NOT IN ({quoted_csv(ALLOWED_DTI_EMPLOYMENT)})
              )
            """,
        )
        unknown_pct = Decimal(
            self.scalar(
                """
                SELECT COALESCE(
                  100.0 * COUNT(*) FILTER (WHERE reason_category = 'unknown') / NULLIF(COUNT(*), 0),
                  0
                )::numeric(8,3)
                FROM diagnostic_text_insights
                WHERE clerk_org_id = :org_id
                """
            )
            or 0
        )
        unknown_detail_rows = self.rows(
            """
            SELECT split_part(l.external_reference, ':', 2) AS scenario, COUNT(*)::int AS row_count
            FROM diagnostic_text_insights d
            JOIN leads l ON l.id = d.lead_id AND l.clerk_org_id = d.clerk_org_id
            WHERE d.clerk_org_id = :org_id AND d.reason_category = 'unknown'
            GROUP BY 1
            ORDER BY 1
            """
        )
        unknown_details = None
        if unknown_detail_rows:
            unknown_details = "unknown_by_scenario: " + ", ".join(
                f"{row['scenario']}={int(row['row_count'])}" for row in unknown_detail_rows
            )
        self.add(
            "diagnostic_text_unknown_reason_threshold",
            "high",
            unknown_pct < Decimal("5"),
            "< 5%",
            f"{unknown_pct}%",
            unknown_details,
        )
        self.check_zero(
            "diagnostic_text_scenario_consistency",
            "high",
            """
            SELECT COUNT(*)::int
            FROM diagnostic_text_insights d
            JOIN leads l ON l.id = d.lead_id AND l.clerk_org_id = d.clerk_org_id
            WHERE d.clerk_org_id = :org_id
              AND (
                (l.external_reference LIKE 'demo:completed_not_signed:%'
                  AND d.reason_category NOT IN ('timing_issue','needs_partner_approval','price_or_budget','needs_more_information','unknown'))
                OR (l.external_reference LIKE 'demo:signed_not_paid:%'
                  AND d.reason_category <> 'payment_friction')
                OR (l.external_reference LIKE 'demo:booked_not_completed:%'
                  AND d.reason_category NOT IN ('no_show','timing_issue'))
                OR (l.external_reference LIKE 'demo:lost:%'
                  AND d.reason_category NOT IN ('low_intent','ghosted','no_show','timing_issue'))
                OR (l.external_reference LIKE 'demo:unqualified:%'
                  AND d.reason_category <> 'poor_fit')
              )
            """,
        )

    def acquisition(self) -> None:
        self.check_zero(
            "acquisition_completeness",
            "critical",
            """
            WITH opt_in_answers AS (
              SELECT o.id AS opt_in_id, COUNT(qa.id)::int AS answer_count
              FROM opt_ins o
              LEFT JOIN opt_in_question_answers qa ON qa.opt_in_id = o.id
              WHERE o.clerk_org_id = :org_id
              GROUP BY o.id
            )
            SELECT COUNT(*)::int
            FROM opt_ins o
            LEFT JOIN traffic_attributions ta ON ta.opt_in_id = o.id
            LEFT JOIN opt_in_answers oa ON oa.opt_in_id = o.id
            WHERE o.clerk_org_id = :org_id
              AND (ta.id IS NULL OR oa.answer_count <> 10)
            """,
        )
        self.check_zero(
            "every_lead_has_opt_in",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM (
              SELECT l.id
              FROM leads l
              LEFT JOIN opt_ins o ON o.lead_id = l.id AND o.clerk_org_id = l.clerk_org_id
              WHERE l.clerk_org_id = :org_id AND l.is_deleted = false
              GROUP BY l.id
              HAVING COUNT(o.id) = 0
            ) missing
            """,
        )
        self.check_zero(
            "form_question_answer_quality",
            "high",
            """
            SELECT COUNT(*)::int
            FROM opt_in_question_answers qa
            JOIN opt_ins o ON o.id = qa.opt_in_id
            WHERE o.clerk_org_id = :org_id
              AND (
                NULLIF(BTRIM(qa.question), '') IS NULL
                OR NULLIF(BTRIM(qa.answer), '') IS NULL
                OR qa.answer ~* '([0-9]{4}\\s?[A-Z]{2}|\\b(street|straat|road|avenue|postcode|zip)\\b)'
              )
            """,
        )
        for question in EXPECTED_QUESTIONS:
            count = int(
                self.scalar(
                    """
                    SELECT COUNT(*)::int
                    FROM opt_in_question_answers qa
                    JOIN opt_ins o ON o.id = qa.opt_in_id
                    WHERE o.clerk_org_id = :org_id AND qa.question = :question
                    """,
                    {"question": question},
                )
                or 0
            )
            self.add(f"form_question_present:{question}", "medium", count == 650, "650 answers", str(count))

    def safe_data(self, denylist: list[str]) -> None:
        unsafe_rows = self.rows(
            """
            SELECT bucket, row_count
            FROM (
              SELECT 'opt_ins_raw_or_client' AS bucket, COUNT(*)::int AS row_count
              FROM opt_ins
              WHERE clerk_org_id = :org_id
                AND (raw_payload IS NOT NULL OR ip_address IS NOT NULL OR user_agent IS NOT NULL)
              UNION ALL SELECT 'appointments_urls', COUNT(*)::int
              FROM appointments
              WHERE clerk_org_id = :org_id
                AND (meeting_url IS NOT NULL OR recording_url IS NOT NULL)
              UNION ALL SELECT 'fathom_raw_or_urls', COUNT(*)::int
              FROM fathom_call_records
              WHERE clerk_org_id = :org_id
                AND (raw_payload IS NOT NULL OR recording_url IS NOT NULL OR transcript_url IS NOT NULL)
              UNION ALL SELECT 'payments_external_id', COUNT(*)::int
              FROM payments
              WHERE clerk_org_id = :org_id
                AND NULLIF(BTRIM(external_payment_id), '') IS NOT NULL
              UNION ALL SELECT 'refunds_external_id', COUNT(*)::int
              FROM refunds
              WHERE clerk_org_id = :org_id
                AND NULLIF(BTRIM(external_refund_id), '') IS NOT NULL
            ) unsafe
            WHERE row_count > 0
            ORDER BY bucket
            """,
        )
        unsafe_total = sum(int(row["row_count"]) for row in unsafe_rows)
        unsafe_details = None
        if unsafe_total:
            unsafe_details = "breakdown: " + ", ".join(
                f"{row['bucket']}={int(row['row_count'])}" for row in unsafe_rows
            )
        self.add(
            "unsafe_payloads_urls_and_provider_ids",
            "high",
            unsafe_total == 0,
            "0 offending rows",
            f"{unsafe_total} offending rows",
            unsafe_details,
        )
        self.check_zero(
            "synthetic_lead_identity",
            "critical",
            """
            SELECT COUNT(*)::int
            FROM leads
            WHERE clerk_org_id = :org_id
              AND (
                email !~* '^[a-z0-9._%+-]+@example\\.com$'
                OR phone_e164 !~ '^\\+3197000[0-9]{6}$'
              )
            """,
        )
        if denylist:
            self.check_denylist(denylist)
        else:
            self.add("denylist_scan", "info", True, "optional denylist not provided", "skipped")

    def check_denylist(self, denylist: list[str]) -> None:
        haystack = "\n".join(
            str(row["value"] or "")
            for row in self.rows(
                """
                SELECT first_name || ' ' || COALESCE(last_name,'') AS value FROM leads WHERE clerk_org_id = :org_id
                UNION ALL SELECT email FROM leads WHERE clerk_org_id = :org_id
                UNION ALL SELECT COALESCE(summary,'') FROM fathom_call_records WHERE clerk_org_id = :org_id
                UNION ALL SELECT COALESCE(notes,'') FROM contracts WHERE clerk_org_id = :org_id
                UNION ALL SELECT COALESCE(note,'') FROM payments WHERE clerk_org_id = :org_id
                """
            )
        ).lower()
        hits = [term for term in denylist if term.lower() in haystack]
        self.add("denylist_scan", "high", not hits, "0 denylist hits", f"{len(hits)} hit(s)")

    def chatbot_reconciliations(self) -> None:
        reconciliations = {
            "lead_source_sums": """
              SELECT CASE WHEN COALESCE(SUM(row_count),0) = 500 THEN 0 ELSE 1 END::int
              FROM (
                SELECT first_source_name, COUNT(*) AS row_count
                FROM leads WHERE clerk_org_id = :org_id AND is_deleted = false
                GROUP BY first_source_name
              ) grouped
            """,
            "lead_status_sums": """
              SELECT CASE WHEN COALESCE(SUM(row_count),0) = 500 THEN 0 ELSE 1 END::int
              FROM (
                SELECT status_id, COUNT(*) AS row_count
                FROM leads WHERE clerk_org_id = :org_id AND is_deleted = false
                GROUP BY status_id
              ) grouped
            """,
            "appointment_breakdown_sums": """
              SELECT CASE WHEN
                (SELECT COUNT(*) FROM appointments WHERE clerk_org_id = :org_id)
                =
                (SELECT COALESCE(SUM(row_count),0) FROM (
                  SELECT snapshot_event_name, COUNT(*) AS row_count FROM appointments WHERE clerk_org_id = :org_id GROUP BY snapshot_event_name
                ) grouped)
              THEN 0 ELSE 1 END::int
            """,
            "opt_in_provider_form_sums": """
              SELECT CASE WHEN
                (SELECT COUNT(*) FROM opt_ins WHERE clerk_org_id = :org_id)
                =
                (SELECT COALESCE(SUM(row_count),0) FROM (
                  SELECT provider_form_name, COUNT(*) AS row_count FROM opt_ins WHERE clerk_org_id = :org_id GROUP BY provider_form_name
                ) grouped)
              THEN 0 ELSE 1 END::int
            """,
            "diagnostic_funnel_sums": """
              SELECT CASE WHEN
                (SELECT COUNT(*) FROM diagnostic_lead_snapshot WHERE clerk_org_id = :org_id)
                =
                (SELECT COALESCE(SUM(row_count),0) FROM (
                  SELECT funnel_stage, COUNT(*) AS row_count FROM diagnostic_lead_snapshot WHERE clerk_org_id = :org_id GROUP BY funnel_stage
                ) grouped)
              THEN 0 ELSE 1 END::int
            """,
            "diagnostic_source_sums": """
              SELECT CASE WHEN
                (SELECT COUNT(*) FROM diagnostic_lead_snapshot WHERE clerk_org_id = :org_id)
                =
                (SELECT COALESCE(SUM(row_count),0) FROM (
                  SELECT first_source, COUNT(*) AS row_count FROM diagnostic_lead_snapshot WHERE clerk_org_id = :org_id GROUP BY first_source
                ) grouped)
              THEN 0 ELSE 1 END::int
            """,
        }
        for name, sql in reconciliations.items():
            self.check_zero(name, "high", sql, expected="reconciles")
        self.check_zero(
            "diagnostic_source_quality_issue_count",
            "high",
            """
            SELECT COUNT(*)::int
            FROM diagnostic_lead_snapshot d
            WHERE d.clerk_org_id = :org_id
              AND EXISTS (
                SELECT 1
                FROM jsonb_array_elements_text(d.source_quality_flags) AS flag(value)
                WHERE flag.value NOT IN ('multiple_sources', 'source_changed')
              )
            """,
            expected="0 unexpected source quality flags",
        )

    def unsupported_metric_guardrails(self) -> None:
        for metric in (
            "Revenue by UTM campaign is not supported without an explicit attribution rule.",
            "Revenue by landing page is not supported without an explicit attribution rule.",
            "Revenue by form answer is not supported without an explicit attribution rule.",
            "ROAS, ad spend, and cost per lead are not available in this dataset.",
        ):
            self.add(f"guardrail:{metric[:32]}", "info", True, "warning only", metric)

    def reconcile_sum(
        self,
        name: str,
        severity: str,
        table: str,
        amount_column: str,
        where_clause: str,
        breakdown_columns: list[str],
    ) -> None:
        failures = 0
        for column in breakdown_columns:
            failures += int(
                self.scalar(
                    f"""
                    WITH total AS (
                      SELECT COALESCE(SUM({amount_column}), 0) AS amount
                      FROM {table}
                      WHERE clerk_org_id = :org_id AND {where_clause}
                    ),
                    breakdown AS (
                      SELECT COALESCE(SUM(amount), 0) AS amount
                      FROM (
                        SELECT {column}, SUM({amount_column}) AS amount
                        FROM {table}
                        WHERE clerk_org_id = :org_id AND {where_clause}
                        GROUP BY {column}
                      ) grouped
                    )
                    SELECT CASE WHEN ABS((SELECT amount FROM total) - (SELECT amount FROM breakdown)) <= 1 THEN 0 ELSE 1 END::int
                    """
                )
                or 0
            )
        self.add(name, severity, failures == 0, "all breakdown sums reconcile", f"{failures} failed breakdown(s)")

    def reconcile_period_net_revenue(self, date_part: str) -> None:
        self.check_zero(
            f"{date_part}_gross_refund_net_revenue_reconcile",
            "high",
            f"""
            WITH bounds AS (
              SELECT
                LEAST(
                  (SELECT MIN(paid_at) FROM payments WHERE clerk_org_id = :org_id AND status::text = 'PAID'),
                  (SELECT MIN(COALESCE(refunded_at, created_at)) FROM refunds WHERE clerk_org_id = :org_id AND status::text = 'SUCCEEDED')
                ) AS start_at,
                GREATEST(
                  (SELECT MAX(paid_at) FROM payments WHERE clerk_org_id = :org_id AND status::text = 'PAID'),
                  (SELECT MAX(COALESCE(refunded_at, created_at)) FROM refunds WHERE clerk_org_id = :org_id AND status::text = 'SUCCEEDED')
                ) AS end_at
            ),
            gross_total AS (
              SELECT COALESCE(SUM(amount),0) AS amount FROM payments WHERE clerk_org_id = :org_id AND status::text = 'PAID'
            ),
            refund_total AS (
              SELECT COALESCE(SUM(amount),0) AS amount FROM refunds WHERE clerk_org_id = :org_id AND status::text = 'SUCCEEDED'
            ),
            gross_by_period AS (
              SELECT COALESCE(SUM(amount),0) AS amount FROM (
                SELECT date_trunc('{date_part}', paid_at) AS bucket, SUM(amount) AS amount
                FROM payments WHERE clerk_org_id = :org_id AND status::text = 'PAID'
                GROUP BY 1
              ) grouped
            ),
            refund_by_period AS (
              SELECT COALESCE(SUM(amount),0) AS amount FROM (
                SELECT date_trunc('{date_part}', COALESCE(refunded_at, created_at)) AS bucket, SUM(amount) AS amount
                FROM refunds WHERE clerk_org_id = :org_id AND status::text = 'SUCCEEDED'
                GROUP BY 1
              ) grouped
            )
            SELECT CASE
              WHEN (SELECT amount FROM gross_total) <> (SELECT amount FROM gross_by_period) THEN 1
              WHEN (SELECT amount FROM refund_total) <> (SELECT amount FROM refund_by_period) THEN 1
              WHEN ((SELECT amount FROM gross_total) - (SELECT amount FROM refund_total))
                <> ((SELECT amount FROM gross_by_period) - (SELECT amount FROM refund_by_period)) THEN 1
              ELSE 0
            END::int
            """,
        )

    def collect_money_totals(self) -> None:
        row = self.rows(
            """
            SELECT
              COALESCE(SUM(amount) FILTER (WHERE status::text = 'PAID'), 0)::numeric AS gross_paid,
              COALESCE(SUM(amount) FILTER (WHERE status::text = 'PENDING'), 0)::numeric AS pending_amount,
              COALESCE(SUM(amount) FILTER (WHERE status::text = 'FAILED'), 0)::numeric AS failed_amount
            FROM payments
            WHERE clerk_org_id = :org_id
            """
        )[0]
        refund = self.scalar(
            """
            SELECT COALESCE(SUM(amount), 0)::numeric
            FROM refunds
            WHERE clerk_org_id = :org_id AND status::text = 'SUCCEEDED'
            """
        )
        gross = int(Decimal(row["gross_paid"] or 0))
        pending = int(Decimal(row["pending_amount"] or 0))
        failed = int(Decimal(row["failed_amount"] or 0))
        refunds = int(Decimal(refund or 0))
        self.money_totals_minor = {
            "gross_paid": gross,
            "pending": pending,
            "failed": failed,
            "succeeded_refunds": refunds,
            "net_collected": gross - refunds,
        }
        self.money_totals_eur = {
            key: f"{Decimal(value) / Decimal(100):.2f}"
            for key, value in self.money_totals_minor.items()
        }


def quoted_csv(values: set[str]) -> str:
    return ", ".join("'" + value.replace("'", "''") + "'" for value in sorted(values))


def read_denylist(path: str | None) -> list[str]:
    if not path:
        return []
    denylist_path = Path(path)
    if not denylist_path.exists():
        raise FileNotFoundError(f"denylist file not found: {denylist_path}")
    return [
        line.strip()
        for line in denylist_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def summarize(checks: list[ValidationCheck]) -> tuple[str, dict[str, dict[str, int]]]:
    summary: dict[str, dict[str, int]] = {}
    for severity in ("critical", "high", "medium", "info"):
        severity_checks = [check for check in checks if check.severity == severity]
        failed = [check for check in severity_checks if not check.passed]
        summary[severity] = {"failed": len(failed), "checked": len(severity_checks)}
    overall = "FAILED" if summary["critical"]["failed"] or summary["high"]["failed"] else "PASSED"
    return overall, summary


def print_report(checks: list[ValidationCheck], overall: str, summary: dict[str, dict[str, int]]) -> None:
    print("Demo data validation completed.")
    print("")
    print(f"Overall status: {overall}")
    print("")
    print("Summary:")
    for severity in ("critical", "high", "medium", "info"):
        item = summary[severity]
        print(f"- {severity}: {item['failed']} failed / {item['checked']} checked")

    failed_checks = [check for check in checks if not check.passed]
    print("")
    print("Failed checks:")
    if failed_checks:
        for check in failed_checks:
            detail = f" - {check.details}" if check.details else ""
            print(f"- {check.name} ({check.severity}): expected {check.expected}, got {check.actual}{detail}")
    else:
        print("- none")


def export_json_report(
    path: str,
    *,
    org_id: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    overall: str,
    checks: list[ValidationCheck],
    row_counts: dict[str, int],
    money_totals_minor: dict[str, int],
    money_totals_eur: dict[str, str],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failed_checks = [check for check in checks if not check.passed]
    payload = {
        "org_id": org_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "overall_status": overall,
        "checks": [asdict(check) for check in checks],
        "failed_checks": [asdict(check) for check in failed_checks],
        "row_counts": row_counts,
        "money_totals_minor": money_totals_minor,
        "money_totals_eur": money_totals_eur,
    }
    output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main() -> int:
    args = parse_args()
    org_id = validate_args(args)
    denylist = read_denylist(args.denylist_file)
    started_monotonic = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    engine = get_engine()

    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            conn.exec_driver_sql("SET TRANSACTION READ ONLY")
            validator = DemoValidator(conn, org_id, verbose=bool(args.verbose))
            validator.validate(denylist)
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise

    finished_at = datetime.now(timezone.utc).isoformat()
    duration_seconds = round(time.monotonic() - started_monotonic, 3)
    overall, summary = summarize(validator.checks)
    print_report(validator.checks, overall, summary)

    if args.export_json:
        export_json_report(
            args.export_json,
            org_id=org_id,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
            overall=overall,
            checks=validator.checks,
            row_counts=validator.row_counts,
            money_totals_minor=validator.money_totals_minor,
            money_totals_eur=validator.money_totals_eur,
        )
        print("")
        print(f"JSON report written to: {args.export_json}")

    return 0 if overall == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
