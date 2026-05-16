#!/usr/bin/env python3
"""Seed deterministic dummy data for the first Hermon client demo.

The script is intentionally guarded. It only allows the fixed dummy
organization by default, supports dry-run planning, and never touches optional
or admin integration tables for this first demo dataset.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from app.config import get_database_settings
from app.diagnostics.lead_snapshot import build_diagnostic_lead_snapshot_once


DUMMY_ORG_ID = "org_dummy_client_demo_001"
BLOCKED_ORG_IDS = {
    "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
}
BLOCKED_ORG_PLACEHOLDER = "REPLACE_WITH_LIVE_CLIENT_ORG_ID_BEFORE_RUNNING"

RANDOM_SEED = 42
DEMO_REFERENCE_DATE = datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)
DEMO_CREATED_BY = "demo_seed_script"
DEMO_CLOSER_ID = "demo_closer_001"
DEMO_SETTER_ID = "demo_setter_001"
DEMO_OWNER_ID = "demo_owner_001"

REQUIRED_TABLES = (
    "sales_statuses",
    "marketing_sources",
    "programs",
    "appointment_event_types",
    "leads",
    "opt_ins",
    "traffic_attributions",
    "opt_in_question_answers",
    "appointments",
    "fathom_call_records",
    "contracts",
    "payments",
    "refunds",
    "diagnostic_text_insights",
)

OPTIONAL_TABLES = (
    "invoices",
    "payment_links",
    "payment_proofs",
    "contract_subscriptions",
    "subscription_checkout_links",
    "unmatched_payments",
)

TABLE_COLUMNS: dict[str, set[str]] = {
    "sales_statuses": {
        "id",
        "clerk_org_id",
        "name",
        "description",
        "text_color",
        "bg_color",
        "role",
        "is_default",
        "is_system",
        "created_by",
        "created_at",
        "updated_at",
    },
    "marketing_sources": {
        "id",
        "clerk_org_id",
        "name",
        "aliases",
        "description",
        "is_archived",
        "created_by",
        "created_at",
        "updated_at",
    },
    "programs": {
        "id",
        "clerk_org_id",
        "name",
        "price_minor",
        "payment_type",
        "billing_interval",
        "notes",
        "template_id",
        "template_name",
        "send_without_payment",
        "is_archived",
        "created_by",
        "created_at",
        "updated_at",
        "is_deleted",
        "deleted_at",
    },
    "appointment_event_types": {
        "id",
        "clerk_org_id",
        "provider",
        "external_event_type_id",
        "event_type_name",
        "call_category",
        "is_favourite",
        "is_ignored",
        "owner_name",
        "owner_ref",
        "kind",
        "source",
        "metadata",
        "created_by",
        "is_deleted",
        "deleted_at",
        "created_at",
        "updated_at",
    },
    "leads": {
        "id",
        "clerk_org_id",
        "first_name",
        "last_name",
        "email",
        "phone_e164",
        "phone_country",
        "source",
        "assigned_to",
        "setter_id",
        "external_reference",
        "status_id",
        "next_touch_point_at",
        "next_touch_point_type",
        "mollie_customer_id",
        "first_source_id",
        "first_source_name",
        "last_source_id",
        "last_source_name",
        "ai_source_summary",
        "created_by",
        "created_at",
        "updated_at",
        "is_deleted",
        "deleted_at",
    },
    "opt_ins": {
        "id",
        "lead_id",
        "clerk_org_id",
        "source",
        "setter_id",
        "provider_form_id",
        "provider_form_name",
        "external_reference",
        "raw_payload",
        "ip_address",
        "user_agent",
        "created_at",
    },
    "traffic_attributions": {
        "id",
        "opt_in_id",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "referrer",
        "landing_page",
        "created_at",
    },
    "opt_in_question_answers": {
        "id",
        "opt_in_id",
        "question",
        "answer",
        "position",
        "created_at",
    },
    "appointments": {
        "id",
        "lead_id",
        "clerk_org_id",
        "schedule_time",
        "snapshot_event_name",
        "snapshot_call_category",
        "appointment_event_type_id",
        "host_id",
        "setter_id",
        "meeting_url",
        "outcome_id",
        "notes",
        "recording_url",
        "no_show",
        "source",
        "external_reference",
        "created_by",
        "created_at",
        "updated_at",
        "is_deleted",
        "deleted_at",
    },
    "fathom_call_records": {
        "id",
        "appointment_id",
        "clerk_org_id",
        "fathom_call_id",
        "fathom_meeting_id",
        "summary",
        "key_points",
        "action_items",
        "objections",
        "transcript_url",
        "recording_url",
        "ai_suggested_outcome",
        "ai_confidence_score",
        "ai_rationale",
        "ai_generated_title",
        "outcome_applied",
        "outcome_applied_by",
        "match_strategy",
        "raw_payload",
        "call_duration_seconds",
        "call_started_at",
        "call_ended_at",
        "created_at",
        "updated_at",
    },
    "contracts": {
        "id",
        "clerk_org_id",
        "lead_id",
        "program_id",
        "closer_id",
        "setter_id",
        "type",
        "total_value",
        "currency",
        "status",
        "created_with_template",
        "notes",
        "esign_template_id",
        "esign_contract_id",
        "voided_reason",
        "voided_by",
        "voided_at",
        "sent_at",
        "signed_at",
        "created_by",
        "created_at",
        "updated_at",
        "is_deleted",
        "deleted_at",
    },
    "payments": {
        "id",
        "contract_id",
        "subscription_id",
        "lead_id",
        "clerk_org_id",
        "type",
        "payment_provider",
        "status",
        "amount",
        "due_date",
        "paid_at",
        "currency",
        "note",
        "failure_reason",
        "external_payment_id",
        "billing_cycle_number",
        "created_by",
        "created_at",
        "updated_at",
        "is_deleted",
        "deleted_at",
    },
    "refunds": {
        "id",
        "payment_id",
        "clerk_org_id",
        "amount",
        "currency",
        "status",
        "reason",
        "external_refund_id",
        "payment_provider",
        "refunded_at",
        "failure_reason",
        "created_by",
        "created_at",
        "updated_at",
    },
    "diagnostic_text_insights": {
        "id",
        "clerk_org_id",
        "lead_id",
        "source_table",
        "source_record_id",
        "source_text_type",
        "source_event_at",
        "source_text_hash",
        "source_text_length",
        "reason_category",
        "reason_subcategory",
        "is_conversion_blocker",
        "buying_intent_level",
        "lead_quality_level",
        "profession_category",
        "employment_status",
        "extraction_status",
        "extracted_at",
        "created_at",
    },
}

SALES_STATUSES = (
    ("NEW_LEAD", "New Lead", "#1f2937", "#e5e7eb"),
    ("APPOINTMENT_BOOKED", "Appointment Booked", "#1d4ed8", "#dbeafe"),
    ("NO_SHOW", "No Show", "#92400e", "#fef3c7"),
    ("RESCHEDULED", "Rescheduled", "#7c3aed", "#ede9fe"),
    ("CANCELED", "Canceled", "#9f1239", "#ffe4e6"),
    ("PARTIAL_PAYMENT", "Partial Payment", "#0f766e", "#ccfbf1"),
    ("WON", "Won", "#166534", "#dcfce7"),
    ("UNQUALIFIED", "Unqualified", "#525252", "#f5f5f5"),
    ("FOLLOW_UP", "No Sale - Follow Up", "#0369a1", "#e0f2fe"),
    ("LOST", "Lost", "#991b1b", "#fee2e2"),
)

MARKETING_SOURCES = (
    "Facebook",
    "Instagram",
    "YouTube",
    "Google Search",
    "Webinar",
    "Referral",
    "Email Campaign",
    "Organic Search",
    "Calendly",
    "Landing Page",
)

SOURCE_DISTRIBUTION = {
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

SCENARIO_DISTRIBUTION = {
    "paid_converted": 110,
    "completed_not_signed": 150,
    "booked_not_completed": 90,
    "lead_only": 75,
    "signed_not_paid": 25,
    "lost": 30,
    "unqualified": 20,
}

SOURCE_SCENARIO_DISTRIBUTION = {
    "Facebook": {
        "paid_converted": 12,
        "completed_not_signed": 28,
        "booked_not_completed": 22,
        "lead_only": 16,
        "signed_not_paid": 3,
        "lost": 6,
        "unqualified": 3,
    },
    "Instagram": {
        "paid_converted": 8,
        "completed_not_signed": 17,
        "booked_not_completed": 12,
        "lead_only": 11,
        "signed_not_paid": 5,
        "lost": 4,
        "unqualified": 3,
    },
    "YouTube": {
        "paid_converted": 12,
        "completed_not_signed": 30,
        "booked_not_completed": 9,
        "lead_only": 5,
        "signed_not_paid": 4,
        "lost": 3,
        "unqualified": 2,
    },
    "Google Search": {
        "paid_converted": 25,
        "completed_not_signed": 16,
        "booked_not_completed": 8,
        "lead_only": 8,
        "signed_not_paid": 4,
        "lost": 5,
        "unqualified": 4,
    },
    "Webinar": {
        "paid_converted": 15,
        "completed_not_signed": 18,
        "booked_not_completed": 8,
        "lead_only": 7,
        "signed_not_paid": 6,
        "lost": 3,
        "unqualified": 3,
    },
    "Referral": {
        "paid_converted": 22,
        "completed_not_signed": 7,
        "booked_not_completed": 3,
        "lead_only": 3,
        "signed_not_paid": 2,
        "lost": 2,
        "unqualified": 1,
    },
    "Email Campaign": {
        "paid_converted": 8,
        "completed_not_signed": 11,
        "booked_not_completed": 6,
        "lead_only": 5,
        "signed_not_paid": 1,
        "lost": 3,
        "unqualified": 1,
    },
    "Calendly": {
        "paid_converted": 5,
        "completed_not_signed": 8,
        "booked_not_completed": 10,
        "lead_only": 3,
        "signed_not_paid": 0,
        "lost": 2,
        "unqualified": 2,
    },
    "Landing Page": {
        "paid_converted": 2,
        "completed_not_signed": 10,
        "booked_not_completed": 8,
        "lead_only": 8,
        "signed_not_paid": 0,
        "lost": 1,
        "unqualified": 1,
    },
    "Organic Search": {
        "paid_converted": 1,
        "completed_not_signed": 5,
        "booked_not_completed": 4,
        "lead_only": 9,
        "signed_not_paid": 0,
        "lost": 1,
        "unqualified": 0,
    },
}

MONTHLY_LEAD_DISTRIBUTION = {
    "2025-11": 55,
    "2025-12": 70,
    "2026-01": 95,
    "2026-02": 82,
    "2026-03": 90,
    "2026-04": 108,
}

PROGRAMS = (
    ("Starter Program", 150000),
    ("Growth Program", 300000),
    ("Premium Coaching Program", 500000),
    ("Freedom Academy", 250000),
    ("Trading Accelerator", 400000),
)

APPOINTMENT_EVENT_TYPES = (
    ("Qualification Call", "TRIAGE_CALL"),
    ("Strategy Call", "SALES_CALL"),
    ("Discovery Call", "SALES_CALL"),
    ("Follow-up Call", "SALES_CALL"),
    ("Payment Support Call", "COACHING_CALL"),
)

PROVIDER_FORM_NAMES = (
    "Qualification Form",
    "Strategy Call Form",
    "Webinar Registration Form",
    "Newsletter Signup Form",
    "Landing Page Lead Form",
)

UTM_CAMPAIGNS = (
    "jan_growth_campaign",
    "webinar_q1_promo",
    "youtube_strategy_series",
    "facebook_leadgen_q1",
    "google_search_brand",
    "email_followup_sequence",
)

LANDING_PAGES = (
    "/freedom-academy",
    "/trading-accelerator",
    "/strategy-call",
    "/webinar-registration",
    "/free-training",
)

PROFESSIONS = (
    "Business Owner",
    "Employee",
    "Self-employed",
    "Student",
    "Trader / Investor",
    "Sales or Marketing",
    "Technology",
    "Healthcare",
    "Retired",
    "Unemployed",
)

EMPLOYMENT_STATUSES = (
    "Full-time",
    "Part-time",
    "Self-employed",
    "Student",
    "Business Owner",
    "Unemployed",
    "Retired",
)

COUNTRIES_OR_REGIONS = (
    "Netherlands",
    "Belgium",
    "Germany",
    "United Kingdom",
    "Spain",
    "France",
    "Dubai",
    "Amsterdam",
    "Rotterdam",
    "Brussels",
    "Berlin",
    "London",
    "Barcelona",
)

GOALS = (
    "Grow income",
    "Start online business",
    "Improve trading skills",
    "Change career",
    "Build side income",
    "Get financial confidence",
)

CHALLENGES = (
    "No clear plan",
    "Lack of time",
    "Budget concern",
    "Needs partner approval",
    "Not confident yet",
    "Needs more information",
)

START_TIMELINES = (
    "Immediately",
    "This month",
    "In 1-3 months",
    "Later this year",
    "Not sure yet",
)

EXPERIENCE_LEVELS = (
    "Beginner",
    "Some experience",
    "Intermediate",
    "Advanced",
    "Returning after a break",
)

BUDGET_RANGES = (
    "Below EUR 1,000",
    "EUR 1,000-EUR 2,500",
    "EUR 2,500-EUR 5,000",
    "Above EUR 5,000",
    "Not sure yet",
)

DECISION_MAKER_ANSWERS = (
    "Yes, I decide myself",
    "I need partner approval",
    "I need team approval",
    "I need finance approval",
    "Not sure yet",
)

PROFESSION_TO_ENUM = {
    "Business Owner": "business_owner",
    "Employee": "employee",
    "Self-employed": "self_employed",
    "Student": "student",
    "Trader / Investor": "trader_or_investor",
    "Sales or Marketing": "sales_or_marketing",
    "Technology": "technology",
    "Healthcare": "healthcare",
    "Retired": "retired",
    "Unemployed": "unemployed",
}

EMPLOYMENT_TO_ENUM = {
    "Full-time": "full_time",
    "Part-time": "part_time",
    "Self-employed": "self_employed",
    "Student": "student",
    "Business Owner": "business_owner",
    "Unemployed": "unemployed",
    "Retired": "retired",
}

STORY_REASON_MAP = {
    "converted_strong_intent": ("unknown", "unknown", False),
    "converted_after_payment_plan": ("price_or_budget", "needs_payment_plan", False),
    "completed_not_signed_partner_approval": (
        "needs_partner_approval",
        "waiting_for_partner",
        True,
    ),
    "completed_not_signed_budget": ("price_or_budget", "budget_not_available", True),
    "completed_not_signed_needs_more_time": ("timing_issue", "needs_more_time", True),
    "signed_not_paid_payment_link_issue": ("payment_friction", "system_or_link_issue", True),
    "signed_not_paid_payment_timing": ("payment_friction", "payment_not_completed", True),
    "lost_low_intent": ("low_intent", "not_ready_now", True),
    "unqualified_poor_fit": ("poor_fit", "wrong_customer_fit", True),
    "follow_up_needs_more_information": (
        "needs_more_information",
        "needs_more_information",
        True,
    ),
}


@dataclass
class LeadProfile:
    index: int
    id: uuid.UUID
    scenario: str
    primary_source: str
    first_source: str
    last_source: str
    source_changed: bool
    lead_source_enum: str
    created_at: datetime
    updated_at: datetime
    first_name: str
    last_name: str
    email: str
    phone_e164: str
    status_role: str
    status_id: uuid.UUID
    assigned_to: str | None
    setter_id: str | None
    next_touch_point_at: datetime | None
    next_touch_point_type: str | None
    profession: str
    employment_status: str
    country_or_region: str
    city_or_region: str
    goal: str
    challenge: str
    start_timeline: str
    experience_level: str
    budget_range: str
    decision_maker: str
    program_name: str | None = None


@dataclass
class SeedState:
    rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    status_ids_by_role: dict[str, uuid.UUID] = field(default_factory=dict)
    status_ids_by_name: dict[str, uuid.UUID] = field(default_factory=dict)
    marketing_source_ids_by_name: dict[str, uuid.UUID] = field(default_factory=dict)
    program_ids_by_name: dict[str, uuid.UUID] = field(default_factory=dict)
    appointment_event_type_ids_by_name: dict[str, uuid.UUID] = field(default_factory=dict)
    lead_ids_by_scenario: dict[str, list[uuid.UUID]] = field(default_factory=dict)
    lead_profile_by_id: dict[uuid.UUID, LeadProfile] = field(default_factory=dict)
    opt_in_ids_by_lead_id: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)
    traffic_attribution_ids_by_opt_in_id: dict[uuid.UUID, uuid.UUID] = field(default_factory=dict)
    question_answer_ids_by_opt_in_id: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)
    appointment_ids_by_lead_id: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)
    completed_appointment_ids_by_lead_id: dict[uuid.UUID, list[uuid.UUID]] = field(
        default_factory=dict
    )
    fathom_ids_by_appointment_id: dict[uuid.UUID, uuid.UUID] = field(default_factory=dict)
    contract_ids_by_lead_id: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)
    payment_ids_by_contract_id: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)
    payment_ids_by_lead_id: dict[uuid.UUID, list[uuid.UUID]] = field(default_factory=dict)
    refund_ids_by_payment_id: dict[uuid.UUID, uuid.UUID] = field(default_factory=dict)
    diagnostic_text_insight_ids_by_lead_id: dict[uuid.UUID, list[uuid.UUID]] = field(
        default_factory=dict
    )
    appointment_kind_by_id: dict[uuid.UUID, str] = field(default_factory=dict)
    appointment_scenario_by_id: dict[uuid.UUID, str] = field(default_factory=dict)
    fathom_template_by_appointment_id: dict[uuid.UUID, str] = field(default_factory=dict)
    fathom_summary_by_appointment_id: dict[uuid.UUID, str] = field(default_factory=dict)
    paid_payment_rows: list[dict[str, Any]] = field(default_factory=list)

    def add_rows(self, table: str, rows: list[dict[str, Any]]) -> None:
        self.rows.setdefault(table, []).extend(rows)

    def row_count(self, table: str) -> int:
        return len(self.rows.get(table, []))


@dataclass(frozen=True)
class ValidationResult:
    check_name: str
    passed: bool
    details: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Hermon first-demo dummy data.")
    parser.add_argument("--org-id", required=True, help="Must be org_dummy_client_demo_001.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and validate safety/schema without deleting or inserting rows.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Safely rebuild only dummy org data before seeding.",
    )
    return parser.parse_args()


def get_engine() -> Engine:
    settings = get_database_settings()
    database_url = (
        os.getenv("HERMON_DIAGNOSTIC_DATABASE_URL")
        or os.getenv("SUPABASE_DB_URL")
        or settings.database_url
        or os.getenv("DATABASE_URL")
    )
    if not database_url:
        raise RuntimeError(
            "Missing database URL. Set HERMON_DIAGNOSTIC_DATABASE_URL, "
            "SUPABASE_DB_URL, HERMON_DATABASE_URL, or DATABASE_URL."
        )
    return create_engine(_sqlalchemy_psycopg_url(database_url), pool_pre_ping=True, future=True)


def _sqlalchemy_psycopg_url(database_url: str) -> str:
    clean_url = database_url.strip()
    if clean_url.startswith("postgresql://"):
        return clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if clean_url.startswith("postgres://"):
        return clean_url.replace("postgres://", "postgresql+psycopg://", 1)
    return clean_url


def validate_safety_args(args: argparse.Namespace) -> None:
    org_id = str(args.org_id or "").strip()
    if not org_id:
        raise ValueError("--org-id is required and cannot be empty.")

    # Safety guard: never allow live org seeding.
    blocked_real_orgs = {org for org in BLOCKED_ORG_IDS if org != BLOCKED_ORG_PLACEHOLDER}
    if org_id in blocked_real_orgs:
        raise ValueError(f"Refusing to run for blocked live organization: {org_id}")

    if org_id != DUMMY_ORG_ID:
        raise ValueError(
            f"Refusing to run for {org_id!r}. This script only allows {DUMMY_ORG_ID!r}."
        )

    if args.force and BLOCKED_ORG_PLACEHOLDER in BLOCKED_ORG_IDS:
        raise ValueError(
            "BLOCKED_ORG_IDS still contains the placeholder. Replace it with the known "
            "live client org ID before running with --force."
        )


def schema_smoke_check(engine: Engine) -> None:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = ANY(:table_names)
                """
            ),
            {"table_names": list(REQUIRED_TABLES)},
        ).mappings()

        columns_by_table: dict[str, set[str]] = {}
        for row in rows:
            columns_by_table.setdefault(str(row["table_name"]), set()).add(str(row["column_name"]))

    missing_tables = [table for table in REQUIRED_TABLES if table not in columns_by_table]
    if missing_tables:
        if "diagnostic_text_insights" in missing_tables:
            raise RuntimeError(
                "diagnostic_text_insights table is missing. Run the diagnostic text "
                "insights migration before seeding demo data."
            )
        raise RuntimeError(
            "Schema smoke check failed. Missing required table(s): "
            + ", ".join(missing_tables)
        )

    missing_columns: list[str] = []
    for table, expected_columns in TABLE_COLUMNS.items():
        actual_columns = columns_by_table.get(table, set())
        missing = sorted(expected_columns.difference(actual_columns))
        if missing:
            missing_columns.append(f"{table}: {', '.join(missing)}")

    if missing_columns:
        raise RuntimeError(
            "Schema smoke check failed. Missing required column(s): "
            + " | ".join(missing_columns)
        )


def stable_uuid(org_id: str, table: str, logical_key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{org_id}:{table}:{logical_key}")


def choose(sequence: tuple[str, ...], index: int) -> str:
    return sequence[index % len(sequence)]


def utc_dt(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def spread_datetimes(year: int, month: int, count: int) -> list[datetime]:
    days_in_month = calendar.monthrange(year, month)[1]
    values: list[datetime] = []
    for index in range(count):
        day = 1 + int(index * days_in_month / count)
        day = min(max(day, 1), days_in_month)
        hour = 9 + ((index * 3) % 8)
        minute = (index * 11) % 60
        values.append(utc_dt(year, month, day, hour, minute))
    return values


def lead_source_enum(source_name: str) -> str:
    mapping = {
        "Calendly": "CALENDLY",
        "Webinar": "WEBINAR",
        "Email Campaign": "NEWSLETTER",
        "Landing Page": "LANDING_PAGE",
    }
    return mapping.get(source_name, "OTHER")


def source_referrer(source_name: str) -> str:
    mapping = {
        "Facebook": "facebook.com",
        "Instagram": "instagram.com",
        "YouTube": "youtube.com",
        "Google Search": "google.com",
        "Organic Search": "google.com",
        "Email Campaign": "email",
        "Referral": "referral",
        "Webinar": "email",
        "Calendly": "referral",
        "Landing Page": "google.com",
    }
    return mapping[source_name]


def source_utm(source_name: str) -> tuple[str, str]:
    mapping = {
        "Facebook": ("facebook", "paid_social"),
        "Instagram": ("instagram", "paid_social"),
        "YouTube": ("youtube", "video"),
        "Google Search": ("google", "paid_search"),
        "Webinar": ("webinar", "webinar"),
        "Referral": ("referral", "partner"),
        "Email Campaign": ("email", "email"),
        "Organic Search": ("google", "organic_search"),
        "Calendly": ("calendly", "direct_booking"),
        "Landing Page": ("landing_page", "paid_search"),
    }
    return mapping[source_name]


def scenario_status_role(scenario: str, index: int) -> str:
    if scenario == "paid_converted":
        return "WON"
    if scenario == "signed_not_paid":
        return "PARTIAL_PAYMENT" if index % 5 else "FOLLOW_UP"
    if scenario == "completed_not_signed":
        return "LOST" if index % 8 == 0 else "FOLLOW_UP"
    if scenario == "booked_not_completed":
        roles = ("NO_SHOW", "CANCELED", "RESCHEDULED")
        return choose(roles, index)
    if scenario == "lead_only":
        return "NEW_LEAD" if index % 4 else "FOLLOW_UP"
    if scenario == "lost":
        return "LOST"
    if scenario == "unqualified":
        return "UNQUALIFIED"
    raise ValueError(f"Unsupported scenario: {scenario}")


def lead_follow_up(status_role: str, created_at: datetime, index: int) -> tuple[datetime | None, str | None]:
    if status_role in {"WON", "LOST", "UNQUALIFIED", "CANCELED"}:
        return None, None
    touch_types = ("PHONE_CALL", "WHATSAPP", "EMAIL", "FOLLOW_UP_CALL", "PROPOSAL_REVIEW")
    return created_at + timedelta(days=3 + (index % 10), hours=2), choose(touch_types, index)


def generate_source_scenario_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for source_name, scenario_counts in SOURCE_SCENARIO_DISTRIBUTION.items():
        for scenario, count in scenario_counts.items():
            pairs.extend((source_name, scenario) for _ in range(count))
    random.shuffle(pairs)
    return pairs


def generate_monthly_dates() -> list[datetime]:
    dates: list[datetime] = []
    for month_key, count in MONTHLY_LEAD_DISTRIBUTION.items():
        year_str, month_str = month_key.split("-")
        dates.extend(spread_datetimes(int(year_str), int(month_str), count))
    return dates


def build_seed_state(org_id: str) -> SeedState:
    random.seed(RANDOM_SEED)
    state = SeedState()
    seed_sales_statuses(state, org_id)
    seed_marketing_sources(state, org_id)
    seed_programs(state, org_id)
    seed_appointment_event_types(state, org_id)
    generate_lead_plan(state, org_id)
    seed_leads(state, org_id)
    seed_opt_ins(state, org_id)
    seed_traffic_attributions(state, org_id)
    seed_opt_in_question_answers(state, org_id)
    seed_appointments(state, org_id)
    seed_fathom_call_records(state, org_id)
    seed_contracts(state, org_id)
    seed_payments(state, org_id)
    seed_refunds(state, org_id)
    seed_diagnostic_text_insights(state, org_id)
    return state


def seed_sales_statuses(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    now = DEMO_REFERENCE_DATE
    for index, (role, name, text_color, bg_color) in enumerate(SALES_STATUSES, start=1):
        status_id = stable_uuid(org_id, "sales_statuses", role)
        state.status_ids_by_role[role] = status_id
        state.status_ids_by_name[name] = status_id
        rows.append(
            {
                "id": status_id,
                "clerk_org_id": org_id,
                "name": name,
                "description": f"Demo pipeline status for {name.lower()}.",
                "text_color": text_color,
                "bg_color": bg_color,
                "role": role,
                "is_default": index == 1,
                "is_system": False,
                "created_by": DEMO_CREATED_BY,
                "created_at": now,
                "updated_at": now,
            }
        )
    state.add_rows("sales_statuses", rows)


def seed_marketing_sources(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    now = DEMO_REFERENCE_DATE
    for source_name in MARKETING_SOURCES:
        source_id = stable_uuid(org_id, "marketing_sources", source_name)
        state.marketing_source_ids_by_name[source_name] = source_id
        aliases = [
            source_name.lower().replace(" ", "_"),
            source_name.lower().replace(" ", "-"),
        ]
        rows.append(
            {
                "id": source_id,
                "clerk_org_id": org_id,
                "name": source_name,
                "aliases": aliases,
                "description": f"Demo marketing source for {source_name}.",
                "is_archived": False,
                "created_by": DEMO_CREATED_BY,
                "created_at": now,
                "updated_at": now,
            }
        )
    state.add_rows("marketing_sources", rows)


def seed_programs(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    now = DEMO_REFERENCE_DATE
    for program_name, price_minor in PROGRAMS:
        program_id = stable_uuid(org_id, "programs", program_name)
        state.program_ids_by_name[program_name] = program_id
        rows.append(
            {
                "id": program_id,
                "clerk_org_id": org_id,
                "name": program_name,
                "price_minor": price_minor,
                "payment_type": "ONE_TIME",
                "billing_interval": None,
                "notes": "Safe first-demo program in EUR minor units.",
                "template_id": None,
                "template_name": None,
                "send_without_payment": False,
                "is_archived": False,
                "created_by": DEMO_CREATED_BY,
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
                "deleted_at": None,
            }
        )
    state.add_rows("programs", rows)


def seed_appointment_event_types(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    now = DEMO_REFERENCE_DATE
    for event_name, call_category in APPOINTMENT_EVENT_TYPES:
        event_type_id = stable_uuid(org_id, "appointment_event_types", event_name)
        state.appointment_event_type_ids_by_name[event_name] = event_type_id
        rows.append(
            {
                "id": event_type_id,
                "clerk_org_id": org_id,
                "provider": "CALENDLY",
                "external_event_type_id": f"demo-{event_name.lower().replace(' ', '-')}",
                "event_type_name": event_name,
                "call_category": call_category,
                "is_favourite": event_name in {"Strategy Call", "Qualification Call"},
                "is_ignored": False,
                "owner_name": "Demo Sales Team",
                "owner_ref": "demo_sales_team",
                "kind": "one_on_one",
                "source": "MANUAL",
                "metadata": json.dumps({"demo": True, "first_demo": True}),
                "created_by": DEMO_CREATED_BY,
                "is_deleted": False,
                "deleted_at": None,
                "created_at": now,
                "updated_at": now,
            }
        )
    state.add_rows("appointment_event_types", rows)


def generate_lead_plan(state: SeedState, org_id: str) -> None:
    pairs = generate_source_scenario_pairs()
    dates = generate_monthly_dates()
    if len(pairs) != 500 or len(dates) != 500:
        raise RuntimeError("Internal distribution error: expected exactly 500 lead inputs.")

    first_names = (
        "Ava",
        "Noah",
        "Mila",
        "Liam",
        "Sofia",
        "Lucas",
        "Emma",
        "Finn",
        "Nora",
        "Owen",
        "Lena",
        "Ethan",
        "Iris",
        "Mason",
        "Zara",
        "Adam",
    )
    last_names = (
        "Demo",
        "Sample",
        "River",
        "Stone",
        "Fields",
        "Parker",
        "Morris",
        "Vale",
        "Brooks",
        "Hayes",
        "West",
        "Lane",
    )

    for index, ((primary_source, scenario), created_at) in enumerate(zip(pairs, dates), start=1):
        source_changed = index % 8 == 0
        first_source = primary_source
        if source_changed:
            other_sources = [source for source in MARKETING_SOURCES if source != primary_source]
            last_source = choose(tuple(other_sources), index)
        else:
            last_source = primary_source

        status_role = scenario_status_role(scenario, index)
        next_touch_point_at, next_touch_point_type = lead_follow_up(status_role, created_at, index)
        lead_id = stable_uuid(org_id, "leads", f"lead-{index:03d}")
        first_name = choose(first_names, index)
        last_name = f"{choose(last_names, index)}{index:03d}"
        program_name = choose(tuple(program_name for program_name, _ in PROGRAMS), index)

        profile = LeadProfile(
            index=index,
            id=lead_id,
            scenario=scenario,
            primary_source=primary_source,
            first_source=first_source,
            last_source=last_source,
            source_changed=source_changed,
            lead_source_enum=lead_source_enum(last_source),
            created_at=created_at,
            updated_at=created_at + timedelta(hours=4 + (index % 30)),
            first_name=first_name,
            last_name=last_name,
            email=f"lead{index:03d}@example.com",
            phone_e164=f"+3197000{index:06d}",
            status_role=status_role,
            status_id=state.status_ids_by_role[status_role],
            assigned_to=DEMO_CLOSER_ID if scenario != "lead_only" else None,
            setter_id=DEMO_SETTER_ID if index % 3 else DEMO_OWNER_ID,
            next_touch_point_at=next_touch_point_at,
            next_touch_point_type=next_touch_point_type,
            profession=choose(PROFESSIONS, index),
            employment_status=choose(EMPLOYMENT_STATUSES, index + 2),
            country_or_region=choose(COUNTRIES_OR_REGIONS, index),
            city_or_region=choose(COUNTRIES_OR_REGIONS, index + 5),
            goal=choose(GOALS, index),
            challenge=choose(CHALLENGES, index + (0 if scenario == "paid_converted" else 2)),
            start_timeline=choose(START_TIMELINES, index),
            experience_level=choose(EXPERIENCE_LEVELS, index),
            budget_range=choose(BUDGET_RANGES, index + 1),
            decision_maker=choose(DECISION_MAKER_ANSWERS, index),
            program_name=program_name,
        )
        state.lead_profile_by_id[lead_id] = profile
        state.lead_ids_by_scenario.setdefault(scenario, []).append(lead_id)


def seed_leads(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    for profile in state.lead_profile_by_id.values():
        first_source_id = state.marketing_source_ids_by_name[profile.first_source]
        last_source_id = state.marketing_source_ids_by_name[profile.last_source]
        rows.append(
            {
                "id": profile.id,
                "clerk_org_id": org_id,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email": profile.email,
                "phone_e164": profile.phone_e164,
                "phone_country": "NL",
                "source": profile.lead_source_enum,
                "assigned_to": profile.assigned_to,
                "setter_id": profile.setter_id,
                "external_reference": f"demo:{profile.scenario}:lead-{profile.index:03d}",
                "status_id": profile.status_id,
                "next_touch_point_at": profile.next_touch_point_at,
                "next_touch_point_type": profile.next_touch_point_type,
                "mollie_customer_id": None,
                "first_source_id": first_source_id,
                "first_source_name": profile.first_source,
                "last_source_id": last_source_id,
                "last_source_name": profile.last_source,
                "ai_source_summary": (
                    f"Demo attribution: first source {profile.first_source}; "
                    f"last source {profile.last_source}."
                ),
                "created_by": DEMO_CREATED_BY,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "is_deleted": False,
                "deleted_at": None,
            }
        )
    state.add_rows("leads", rows)


def seed_opt_ins(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    profiles = list(state.lead_profile_by_id.values())
    for profile in profiles:
        opt_in_count = 2 if profile.index <= 150 else 1
        for number in range(1, opt_in_count + 1):
            opt_in_id = stable_uuid(org_id, "opt_ins", f"lead-{profile.index:03d}-{number}")
            source = lead_source_enum(profile.first_source if number == 1 else profile.last_source)
            created_at = profile.created_at + timedelta(hours=number - 1, minutes=profile.index % 45)
            row = {
                "id": opt_in_id,
                "lead_id": profile.id,
                "clerk_org_id": org_id,
                "source": source,
                "setter_id": profile.setter_id,
                "provider_form_id": f"demo_form_{(profile.index + number) % 5 + 1}",
                "provider_form_name": choose(PROVIDER_FORM_NAMES, profile.index + number),
                "external_reference": f"demo-optin-{profile.index:03d}-{number}",
                "raw_payload": None,
                "ip_address": None,
                "user_agent": None,
                "created_at": created_at,
            }
            rows.append(row)
            state.opt_in_ids_by_lead_id.setdefault(profile.id, []).append(opt_in_id)
    state.add_rows("opt_ins", rows)


def seed_traffic_attributions(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    for profile in state.lead_profile_by_id.values():
        opt_in_ids = state.opt_in_ids_by_lead_id[profile.id]
        for position, opt_in_id in enumerate(opt_in_ids, start=1):
            attribution_id = stable_uuid(org_id, "traffic_attributions", str(opt_in_id))
            source_for_attribution = profile.first_source if position == 1 else profile.last_source
            utm_source, utm_medium = source_utm(source_for_attribution)
            rows.append(
                {
                    "id": attribution_id,
                    "opt_in_id": opt_in_id,
                    "utm_source": utm_source,
                    "utm_medium": utm_medium,
                    "utm_campaign": choose(UTM_CAMPAIGNS, profile.index + position),
                    "utm_content": f"demo_content_{(profile.index + position) % 4 + 1}",
                    "utm_term": "demo_offer",
                    "referrer": source_referrer(source_for_attribution),
                    "landing_page": choose(LANDING_PAGES, profile.index + position),
                    "created_at": profile.created_at + timedelta(hours=position, minutes=5),
                }
            )
            state.traffic_attribution_ids_by_opt_in_id[opt_in_id] = attribution_id
    state.add_rows("traffic_attributions", rows)


def seed_opt_in_question_answers(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    questions = (
        ("What do you do for work?", "profession"),
        ("What is your employment status?", "employment_status"),
        ("Which country are you from?", "country_or_region"),
        ("Which city or region are you based in?", "city_or_region"),
        ("What is your main goal?", "goal"),
        ("What is your biggest challenge right now?", "challenge"),
        ("How soon do you want to get started?", "start_timeline"),
        ("What is your current experience level?", "experience_level"),
        ("What budget range are you comfortable with?", "budget_range"),
        ("Are you the final decision maker?", "decision_maker"),
    )
    for profile in state.lead_profile_by_id.values():
        for opt_in_id in state.opt_in_ids_by_lead_id[profile.id]:
            answer_ids: list[uuid.UUID] = []
            for position, (question, attribute_name) in enumerate(questions, start=1):
                answer_id = stable_uuid(
                    org_id,
                    "opt_in_question_answers",
                    f"{opt_in_id}-{position}",
                )
                answer_ids.append(answer_id)
                rows.append(
                    {
                        "id": answer_id,
                        "opt_in_id": opt_in_id,
                        "question": question,
                        "answer": getattr(profile, attribute_name),
                        "position": position,
                        "created_at": profile.created_at + timedelta(hours=1, minutes=position),
                    }
                )
            state.question_answer_ids_by_opt_in_id[opt_in_id] = answer_ids
    state.add_rows("opt_in_question_answers", rows)


def seed_appointments(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    completed_scenarios = {"paid_converted", "completed_not_signed", "signed_not_paid"}
    for profile in state.lead_profile_by_id.values():
        if profile.scenario in completed_scenarios:
            appointment_time = profile.created_at + timedelta(days=1 + (profile.index % 14), hours=1)
            rows.append(
                appointment_row(
                    state,
                    org_id,
                    profile,
                    appointment_time,
                    kind="completed",
                    event_name="Strategy Call",
                    outcome_role=profile.status_role,
                    no_show=False,
                    number=1,
                )
            )

    booked_profiles = [
        state.lead_profile_by_id[lead_id]
        for lead_id in state.lead_ids_by_scenario["booked_not_completed"]
    ]
    booked_kind_by_status = {
        "NO_SHOW": ("no_show", True),
        "CANCELED": ("canceled", False),
        "RESCHEDULED": ("rescheduled", False),
    }
    for profile in booked_profiles:
        kind, no_show = booked_kind_by_status[profile.status_role]
        appointment_time = profile.created_at + timedelta(days=2 + (profile.index % 10), hours=2)
        rows.append(
            appointment_row(
                state,
                org_id,
                profile,
                appointment_time,
                kind=kind,
                event_name="Qualification Call",
                outcome_role=profile.status_role,
                no_show=no_show,
                number=1,
            )
        )

    lost_profiles = [state.lead_profile_by_id[lead_id] for lead_id in state.lead_ids_by_scenario["lost"]]
    lost_kinds = ("no_show", "canceled", "rescheduled")
    for offset, profile in enumerate(lost_profiles, start=1):
        kind = choose(lost_kinds, offset)
        outcome_role = {
            "no_show": "NO_SHOW",
            "canceled": "CANCELED",
            "rescheduled": "RESCHEDULED",
        }[kind]
        appointment_time = profile.created_at + timedelta(days=2 + (profile.index % 10), hours=2)
        rows.append(
            appointment_row(
                state,
                org_id,
                profile,
                appointment_time,
                kind=kind,
                event_name="Qualification Call",
                outcome_role=outcome_role,
                no_show=kind == "no_show",
                number=1,
            )
        )

    future_candidates = [
        state.lead_profile_by_id[lead_id]
        for lead_id in (
            state.lead_ids_by_scenario["completed_not_signed"][:30]
            + state.lead_ids_by_scenario["signed_not_paid"][:10]
        )
    ]
    runtime_now = datetime.now(timezone.utc)
    future_base = max(DEMO_REFERENCE_DATE, runtime_now)
    for offset, profile in enumerate(future_candidates, start=1):
        future_time = future_base + timedelta(days=2 + (offset % 29), hours=offset % 5)
        rows.append(
            appointment_row(
                state,
                org_id,
                profile,
                future_time,
                kind="future",
                event_name="Follow-up Call",
                outcome_role="APPOINTMENT_BOOKED",
                no_show=False,
                number=2,
            )
        )

    state.add_rows("appointments", rows)


def appointment_row(
    state: SeedState,
    org_id: str,
    profile: LeadProfile,
    schedule_time: datetime,
    *,
    kind: str,
    event_name: str,
    outcome_role: str,
    no_show: bool,
    number: int,
) -> dict[str, Any]:
    appointment_id = stable_uuid(
        org_id,
        "appointments",
        f"lead-{profile.index:03d}-{kind}-{number}",
    )
    event_type_id = state.appointment_event_type_ids_by_name[event_name]
    state.appointment_ids_by_lead_id.setdefault(profile.id, []).append(appointment_id)
    state.appointment_kind_by_id[appointment_id] = kind
    state.appointment_scenario_by_id[appointment_id] = profile.scenario
    if kind == "completed":
        state.completed_appointment_ids_by_lead_id.setdefault(profile.id, []).append(appointment_id)

    return {
        "id": appointment_id,
        "lead_id": profile.id,
        "clerk_org_id": org_id,
        "schedule_time": schedule_time,
        "snapshot_event_name": event_name,
        "snapshot_call_category": (
            "TRIAGE_CALL" if event_name == "Qualification Call" else "SALES_CALL"
        ),
        "appointment_event_type_id": event_type_id,
        "host_id": DEMO_CLOSER_ID,
        "setter_id": profile.setter_id,
        "meeting_url": None,
        "outcome_id": state.status_ids_by_role[outcome_role],
        "notes": appointment_note(kind),
        "recording_url": None,
        "no_show": no_show,
        "source": "CALENDLY" if profile.primary_source == "Calendly" else "MANUAL",
        "external_reference": f"demo-appointment-{profile.index:03d}-{kind}-{number}",
        "created_by": DEMO_CREATED_BY,
        "created_at": min(profile.created_at + timedelta(hours=3), schedule_time),
        "updated_at": max(schedule_time, profile.updated_at),
        "is_deleted": False,
        "deleted_at": None,
    }


def appointment_note(kind: str) -> str:
    notes = {
        "completed": "Demo attended call with follow-up captured in Fathom.",
        "no_show": "Demo no-show appointment; no call recording exists.",
        "canceled": "Demo appointment canceled before the scheduled call.",
        "rescheduled": "Demo appointment rescheduled; original call did not occur.",
        "future": "Demo future follow-up appointment; no Fathom record yet.",
    }
    return notes[kind]


def seed_fathom_call_records(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    for appointment in state.rows["appointments"]:
        appointment_id = appointment["id"]
        if state.appointment_kind_by_id.get(appointment_id) != "completed":
            continue
        profile = state.lead_profile_by_id[appointment["lead_id"]]
        template_key = fathom_template_for_profile(profile)
        story = fathom_story(template_key, profile)
        duration = 28 * 60 + (profile.index % 17) * 60
        call_started_at = appointment["schedule_time"] + timedelta(minutes=profile.index % 5)
        call_ended_at = call_started_at + timedelta(seconds=duration)
        fathom_id = stable_uuid(org_id, "fathom_call_records", str(appointment_id))
        outcome_role = profile.status_role if profile.status_role in state.status_ids_by_role else "FOLLOW_UP"
        row = {
            "id": fathom_id,
            "appointment_id": appointment_id,
            "clerk_org_id": org_id,
            "fathom_call_id": f"demo_fathom_{profile.index:03d}",
            "fathom_meeting_id": f"demo_meeting_{profile.index:03d}",
            "summary": story["summary"],
            "key_points": json.dumps(story["key_points"]),
            "action_items": json.dumps(story["action_items"]),
            "objections": json.dumps(story["objections"]),
            "transcript_url": None,
            "recording_url": None,
            "ai_suggested_outcome": state.status_ids_by_role[outcome_role],
            "ai_confidence_score": Decimal(story["confidence"]),
            "ai_rationale": story["rationale"],
            "ai_generated_title": story["title"],
            "outcome_applied": False,
            "outcome_applied_by": None,
            "match_strategy": "demo_seed_exact_appointment_match",
            "raw_payload": None,
            "call_duration_seconds": duration,
            "call_started_at": call_started_at,
            "call_ended_at": call_ended_at,
            "created_at": call_ended_at + timedelta(minutes=5),
            "updated_at": call_ended_at + timedelta(minutes=5),
        }
        rows.append(row)
        state.fathom_ids_by_appointment_id[appointment_id] = fathom_id
        state.fathom_template_by_appointment_id[appointment_id] = template_key
        state.fathom_summary_by_appointment_id[appointment_id] = story["summary"]
    state.add_rows("fathom_call_records", rows)


def fathom_template_for_profile(profile: LeadProfile) -> str:
    if profile.scenario == "paid_converted":
        return "converted_after_payment_plan" if profile.index % 4 == 0 else "converted_strong_intent"
    if profile.scenario == "signed_not_paid":
        return (
            "signed_not_paid_payment_link_issue"
            if profile.index % 2
            else "signed_not_paid_payment_timing"
        )
    if profile.scenario == "completed_not_signed":
        templates = (
            "completed_not_signed_partner_approval",
            "completed_not_signed_budget",
            "completed_not_signed_needs_more_time",
            "follow_up_needs_more_information",
        )
        return choose(templates, profile.index)
    if profile.scenario == "lost":
        return "lost_low_intent"
    if profile.scenario == "unqualified":
        return "unqualified_poor_fit"
    return "follow_up_needs_more_information"


def fathom_story(template_key: str, profile: LeadProfile) -> dict[str, Any]:
    stories = {
        "converted_strong_intent": {
            "title": "Strategy Call - Ready to Join",
            "summary": (
                "The lead joined with clear intent and asked practical questions about "
                "the program, expected results, and onboarding. They confirmed that the "
                "offer made sense and agreed to complete payment after the call."
            ),
            "key_points": [
                "Lead understood the value of the program",
                "Lead asked about onboarding and timeline",
                "Lead agreed to complete payment after the call",
            ],
            "objections": [],
            "action_items": [
                "Send onboarding instructions",
                "Confirm payment completion",
                "Add lead to customer onboarding flow",
            ],
            "confidence": "0.92",
            "rationale": "Strong verbal commitment and payment intent were captured in the call.",
        },
        "converted_after_payment_plan": {
            "title": "Strategy Call - Payment Plan Accepted",
            "summary": (
                "The lead was interested and wanted to understand the payment plan before "
                "joining. After reviewing the installment structure, they accepted the "
                "terms and agreed to move forward."
            ),
            "key_points": [
                "Lead had strong buying intent",
                "Payment plan resolved the main concern",
                "Contract and payment steps were accepted",
            ],
            "objections": ["Needed a payment plan"],
            "action_items": [
                "Send contract with payment plan terms",
                "Confirm first payment",
                "Schedule onboarding check-in",
            ],
            "confidence": "0.88",
            "rationale": "The budget concern was resolved during the call.",
        },
        "completed_not_signed_partner_approval": {
            "title": "Strategy Call - Partner Approval Needed",
            "summary": (
                "The lead was interested in the program but did not want to sign during "
                "the call. They said they needed to discuss the decision with their "
                "partner and asked for a short summary of the offer."
            ),
            "key_points": [
                "Lead understood the offer",
                "Partner approval is required",
                "Follow-up timing was agreed",
            ],
            "objections": ["Needs partner approval", "Needs more time"],
            "action_items": [
                "Follow up in 2 days",
                "Send a short offer summary",
                "Confirm whether partner approval is complete",
            ],
            "confidence": "0.84",
            "rationale": "The blocker was explicit partner approval rather than low interest.",
        },
        "completed_not_signed_budget": {
            "title": "Strategy Call - Budget Concern",
            "summary": (
                "The lead saw value in the program but was unsure whether the current "
                "budget could support the purchase. They wanted to review finances before "
                "making a commitment."
            ),
            "key_points": [
                "Lead showed interest but hesitated on price",
                "Budget availability was the main blocker",
                "A payment option may help",
            ],
            "objections": ["Budget concern", "Needs payment clarity"],
            "action_items": [
                "Send payment option overview",
                "Follow up after finance review",
                "Offer a short clarification call",
            ],
            "confidence": "0.81",
            "rationale": "Budget was mentioned as the reason for not signing.",
        },
        "completed_not_signed_needs_more_time": {
            "title": "Strategy Call - Needs More Time",
            "summary": (
                "The lead was engaged and asked several good questions, but they were not "
                "ready to make a decision during the call. They asked for time to review "
                "the details and compare timing with current priorities."
            ),
            "key_points": [
                "Lead was engaged throughout the call",
                "Timing is the main blocker",
                "Follow-up is required",
            ],
            "objections": ["Needs more time", "Timing issue"],
            "action_items": [
                "Follow up this week",
                "Send recap of next steps",
                "Ask for a clear decision date",
            ],
            "confidence": "0.80",
            "rationale": "The lead did not reject the offer but delayed the decision.",
        },
        "signed_not_paid_payment_link_issue": {
            "title": "Contract Signed - Payment Link Support Needed",
            "summary": (
                "The lead accepted the offer and contract terms, but payment was not "
                "completed during the call. They mentioned they may need help with the "
                "payment link and asked for the details to be sent again."
            ),
            "key_points": [
                "Contract step is complete",
                "Payment is still pending",
                "Lead asked for payment support",
            ],
            "objections": ["Payment link support needed"],
            "action_items": [
                "Resend payment instructions",
                "Follow up today to confirm payment",
                "Escalate if payment issue continues",
            ],
            "confidence": "0.87",
            "rationale": "Payment friction is operational rather than a sales rejection.",
        },
        "signed_not_paid_payment_timing": {
            "title": "Contract Signed - Payment Timing",
            "summary": (
                "The lead signed the contract and confirmed intent to pay, but asked to "
                "complete payment later in the week. The next step is a direct payment "
                "follow-up."
            ),
            "key_points": [
                "Contract is signed",
                "Payment timing is delayed",
                "Follow-up date was agreed",
            ],
            "objections": ["Payment not completed"],
            "action_items": [
                "Follow up on agreed payment date",
                "Confirm payment method",
                "Keep onboarding pending until payment clears",
            ],
            "confidence": "0.85",
            "rationale": "The lead intends to pay but payment has not been collected.",
        },
        "lost_low_intent": {
            "title": "Sales Call - Low Intent",
            "summary": (
                "The lead attended but did not show enough urgency to move forward. They "
                "were curious about the offer but did not have a clear need or timeline."
            ),
            "key_points": [
                "Low urgency",
                "No clear decision timeline",
                "Offer was not rejected on product fit alone",
            ],
            "objections": ["Not ready now"],
            "action_items": ["Move to nurture", "Check back next quarter"],
            "confidence": "0.76",
            "rationale": "The lead lacked urgency and did not commit to next steps.",
        },
        "unqualified_poor_fit": {
            "title": "Qualification Call - Poor Fit",
            "summary": (
                "The lead was not a good fit for the current program because their goals "
                "and starting point did not match the offer. The recommended path was to "
                "avoid sending a contract."
            ),
            "key_points": [
                "Goals do not match the program",
                "Lead is not ready for the offer",
                "No contract should be sent",
            ],
            "objections": ["Wrong customer fit"],
            "action_items": ["Close as unqualified", "Send free resources only"],
            "confidence": "0.91",
            "rationale": "The call showed a clear fit mismatch.",
        },
        "follow_up_needs_more_information": {
            "title": "Strategy Call - More Information Needed",
            "summary": (
                "The lead was interested but wanted a clearer explanation of outcomes, "
                "support, and implementation before committing. A focused follow-up should "
                "address the remaining questions."
            ),
            "key_points": [
                "Lead has open questions",
                "More proof and clarity are needed",
                "Follow-up can still recover the opportunity",
            ],
            "objections": ["Needs more information"],
            "action_items": [
                "Send proof points",
                "Answer remaining questions",
                "Book a short follow-up call",
            ],
            "confidence": "0.79",
            "rationale": "The lead needs more information before signing.",
        },
    }
    story = dict(stories[template_key])
    story["summary"] = f"{story['summary']} {fathom_context_sentence(profile)}"
    story["key_points"] = [
        *story["key_points"],
        f"Program discussed: {profile.program_name}",
        f"Stated goal: {profile.goal}",
    ]
    return story


def fathom_context_sentence(profile: LeadProfile) -> str:
    variants = (
        (
            f"The conversation centered on {profile.program_name}, with the lead's "
            f"main goal listed as {profile.goal} and their current challenge as "
            f"{profile.challenge}."
        ),
        (
            f"They came through {profile.last_source}, said their start timeline was "
            f"{profile.start_timeline}, and described the budget range as "
            f"{profile.budget_range}."
        ),
        (
            f"The lead's decision-maker answer was '{profile.decision_maker}', and "
            f"the follow-up should stay focused on {profile.goal.lower()}."
        ),
        (
            f"For this demo journey, the discussed program was {profile.program_name}; "
            f"the lead's source was {profile.last_source} and the main challenge was "
            f"{profile.challenge.lower()}."
        ),
    )
    return choose(variants, profile.index)


def seed_contracts(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    signed_scenarios = {"paid_converted", "signed_not_paid"}
    for profile in state.lead_profile_by_id.values():
        if profile.scenario in signed_scenarios:
            rows.append(contract_row(state, org_id, profile, status="SIGNED", number=1))

    completed_not_signed = [
        state.lead_profile_by_id[lead_id]
        for lead_id in state.lead_ids_by_scenario["completed_not_signed"][:35]
    ]
    for profile in completed_not_signed:
        status = "VIEWED" if profile.index % 2 else "SENT"
        rows.append(contract_row(state, org_id, profile, status=status, number=1))

    lost_profiles = [
        state.lead_profile_by_id[lead_id]
        for lead_id in state.lead_ids_by_scenario["lost"][:8]
    ]
    for profile in lost_profiles:
        rows.append(contract_row(state, org_id, profile, status="VOIDED", number=1))

    state.add_rows("contracts", rows)


def contract_row(
    state: SeedState,
    org_id: str,
    profile: LeadProfile,
    *,
    status: str,
    number: int,
) -> dict[str, Any]:
    contract_id = stable_uuid(org_id, "contracts", f"lead-{profile.index:03d}-{number}")
    program_id = state.program_ids_by_name[str(profile.program_name)]
    program_price = dict(PROGRAMS)[str(profile.program_name)]
    completed_at = latest_completed_appointment_time(state, profile.id)
    sent_at = (completed_at or profile.created_at) + timedelta(days=1 + (profile.index % 3))
    signed_at = None
    voided_at = None
    if status == "SIGNED":
        signed_at = sent_at + timedelta(days=profile.index % 5, hours=2)
    if status == "VOIDED":
        voided_at = sent_at + timedelta(days=2 + (profile.index % 4))

    row = {
        "id": contract_id,
        "clerk_org_id": org_id,
        "lead_id": profile.id,
        "program_id": program_id,
        "closer_id": DEMO_CLOSER_ID,
        "setter_id": profile.setter_id,
        "type": "PP" if profile.index % 3 == 0 else "PIF",
        "total_value": Decimal(program_price),
        "currency": "EUR",
        "status": status,
        "created_with_template": False,
        "notes": contract_note(status),
        "esign_template_id": None,
        "esign_contract_id": None,
        "voided_reason": "Lead decided not to proceed" if status == "VOIDED" else None,
        "voided_by": DEMO_CLOSER_ID if status == "VOIDED" else None,
        "voided_at": voided_at,
        "sent_at": sent_at,
        "signed_at": signed_at,
        "created_by": DEMO_CREATED_BY,
        "created_at": sent_at,
        "updated_at": signed_at or voided_at or sent_at + timedelta(hours=4),
        "is_deleted": False,
        "deleted_at": None,
    }
    state.contract_ids_by_lead_id.setdefault(profile.id, []).append(contract_id)
    return row


def latest_completed_appointment_time(state: SeedState, lead_id: uuid.UUID) -> datetime | None:
    completed_ids = set(state.completed_appointment_ids_by_lead_id.get(lead_id, []))
    completed_times = [
        row["schedule_time"]
        for row in state.rows.get("appointments", [])
        if row["id"] in completed_ids
    ]
    return max(completed_times) if completed_times else None


def contract_note(status: str) -> str:
    notes = {
        "SIGNED": "Demo contract signed after sales call.",
        "SENT": "Demo contract sent but not signed.",
        "VIEWED": "Demo contract viewed but not signed.",
        "VOIDED": "Demo contract voided after the opportunity was lost.",
    }
    return notes[status]


def seed_payments(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    paid_profiles = [
        state.lead_profile_by_id[lead_id]
        for lead_id in state.lead_ids_by_scenario["paid_converted"]
    ]
    split_payment_ids = {profile.id for profile in paid_profiles[:55]}
    for profile in paid_profiles:
        contract_id = state.contract_ids_by_lead_id[profile.id][0]
        contract = contract_by_id(state, contract_id)
        signed_at = contract["signed_at"]
        total_amount = Decimal(contract["total_value"])
        if profile.id in split_payment_ids:
            first_amount = (total_amount / Decimal(2)).quantize(Decimal("1"))
            second_amount = total_amount - first_amount
            rows.append(
                payment_row(
                    state,
                    org_id,
                    profile,
                    contract_id,
                    amount=first_amount,
                    status="PAID",
                    payment_type="DEPOSIT",
                    number=1,
                    due_at=signed_at,
                    paid_at=signed_at + timedelta(days=profile.index % 3, hours=1),
                )
            )
            rows.append(
                payment_row(
                    state,
                    org_id,
                    profile,
                    contract_id,
                    amount=second_amount,
                    status="PAID",
                    payment_type="INSTALMENT",
                    number=2,
                    due_at=signed_at + timedelta(days=14),
                    paid_at=signed_at + timedelta(days=14 + (profile.index % 5), hours=1),
                )
            )
        else:
            rows.append(
                payment_row(
                    state,
                    org_id,
                    profile,
                    contract_id,
                    amount=total_amount,
                    status="PAID",
                    payment_type="FIRST_PAYMENT",
                    number=1,
                    due_at=signed_at,
                    paid_at=signed_at + timedelta(days=profile.index % 6, hours=1),
                )
            )

    signed_not_paid_profiles = [
        state.lead_profile_by_id[lead_id]
        for lead_id in state.lead_ids_by_scenario["signed_not_paid"]
    ]
    for offset, profile in enumerate(signed_not_paid_profiles, start=1):
        contract_id = state.contract_ids_by_lead_id[profile.id][0]
        contract = contract_by_id(state, contract_id)
        signed_at = contract["signed_at"]
        status = "PENDING" if offset <= 15 else "FAILED"
        rows.append(
            payment_row(
                state,
                org_id,
                profile,
                contract_id,
                amount=Decimal(contract["total_value"]),
                status=status,
                payment_type="FIRST_PAYMENT",
                number=1,
                due_at=signed_at + timedelta(days=1 + (offset % 6)),
                paid_at=None,
            )
        )

    state.add_rows("payments", rows)


def contract_by_id(state: SeedState, contract_id: uuid.UUID) -> dict[str, Any]:
    for contract in state.rows["contracts"]:
        if contract["id"] == contract_id:
            return contract
    raise KeyError(f"Unknown contract id: {contract_id}")


def payment_row(
    state: SeedState,
    org_id: str,
    profile: LeadProfile,
    contract_id: uuid.UUID,
    *,
    amount: Decimal,
    status: str,
    payment_type: str,
    number: int,
    due_at: datetime | None,
    paid_at: datetime | None,
) -> dict[str, Any]:
    payment_id = stable_uuid(
        org_id,
        "payments",
        f"lead-{profile.index:03d}-{payment_type.lower()}-{number}",
    )
    provider = choose(("STRIPE", "MOLLIE", "MANUAL"), profile.index + number)
    created_at = due_at or profile.updated_at
    row = {
        "id": payment_id,
        "contract_id": contract_id,
        "subscription_id": None,
        "lead_id": profile.id,
        "clerk_org_id": org_id,
        "type": payment_type,
        "payment_provider": provider,
        "status": status,
        "amount": amount,
        "due_date": due_at,
        "paid_at": paid_at,
        "currency": "EUR",
        "note": payment_note(status),
        "failure_reason": "Payment attempt failed in demo scenario" if status == "FAILED" else None,
        "external_payment_id": f"demo_payment_{profile.index:03d}_{number}",
        "billing_cycle_number": None,
        "created_by": DEMO_CREATED_BY,
        "created_at": created_at,
        "updated_at": paid_at or created_at + timedelta(hours=3),
        "is_deleted": False,
        "deleted_at": None,
    }
    state.payment_ids_by_contract_id.setdefault(contract_id, []).append(payment_id)
    state.payment_ids_by_lead_id.setdefault(profile.id, []).append(payment_id)
    if status == "PAID":
        state.paid_payment_rows.append(row)
    return row


def payment_note(status: str) -> str:
    notes = {
        "PAID": "Demo payment collected successfully.",
        "PENDING": "Demo payment is pending follow-up.",
        "FAILED": "Demo payment failed and needs support.",
    }
    return notes[status]


def seed_refunds(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    refund_reasons = (
        "Customer changed decision after onboarding",
        "Duplicate payment correction",
        "Program no longer suitable",
    )
    for offset, payment in enumerate(state.paid_payment_rows[:12], start=1):
        refund_id = stable_uuid(org_id, "refunds", f"refund-{offset:02d}-{payment['id']}")
        amount = (Decimal(payment["amount"]) / Decimal(4)).quantize(Decimal("1"))
        refunded_at = payment["paid_at"] + timedelta(days=7 + offset * 2)
        rows.append(
            {
                "id": refund_id,
                "payment_id": payment["id"],
                "clerk_org_id": org_id,
                "amount": amount,
                "currency": "EUR",
                "status": "SUCCEEDED",
                "reason": choose(refund_reasons, offset),
                "external_refund_id": f"demo_refund_{offset:02d}",
                "payment_provider": payment["payment_provider"],
                "refunded_at": refunded_at,
                "failure_reason": None,
                "created_by": DEMO_CREATED_BY,
                "created_at": refunded_at,
                "updated_at": refunded_at + timedelta(minutes=10),
            }
        )
        state.refund_ids_by_payment_id[payment["id"]] = refund_id
    state.add_rows("refunds", rows)


def seed_diagnostic_text_insights(state: SeedState, org_id: str) -> None:
    rows: list[dict[str, Any]] = []
    for fathom in state.rows["fathom_call_records"]:
        appointment_id = fathom["appointment_id"]
        profile = profile_for_appointment(state, appointment_id)
        template_key = state.fathom_template_by_appointment_id[appointment_id]
        reason_category, reason_subcategory, is_blocker = STORY_REASON_MAP[template_key]
        insight_id = stable_uuid(org_id, "diagnostic_text_insights", f"fathom-{fathom['id']}")
        rows.append(
            diagnostic_insight_row(
                org_id,
                insight_id,
                profile,
                source_table="fathom_call_records",
                source_record_id=fathom["id"],
                source_text_type="fathom_summary",
                source_event_at=fathom["call_started_at"],
                source_text=str(fathom["summary"]),
                reason_category=reason_category,
                reason_subcategory=reason_subcategory,
                is_conversion_blocker=is_blocker,
            )
        )
        state.diagnostic_text_insight_ids_by_lead_id.setdefault(profile.id, []).append(insight_id)

    for appointment in state.rows["appointments"]:
        kind = state.appointment_kind_by_id[appointment["id"]]
        if kind in {"completed", "future"}:
            continue
        profile = state.lead_profile_by_id[appointment["lead_id"]]
        reason_category, reason_subcategory = appointment_reason(kind)
        text_source = f"{appointment['snapshot_event_name']} ended as {kind.replace('_', ' ')}."
        insight_id = stable_uuid(org_id, "diagnostic_text_insights", f"appointment-{appointment['id']}")
        rows.append(
            diagnostic_insight_row(
                org_id,
                insight_id,
                profile,
                source_table="appointments",
                source_record_id=appointment["id"],
                source_text_type="appointment_outcome",
                source_event_at=appointment["schedule_time"],
                source_text=text_source,
                reason_category=reason_category,
                reason_subcategory=reason_subcategory,
                is_conversion_blocker=True,
            )
        )
        state.diagnostic_text_insight_ids_by_lead_id.setdefault(profile.id, []).append(insight_id)

    state.add_rows("diagnostic_text_insights", rows)


def profile_for_appointment(state: SeedState, appointment_id: uuid.UUID) -> LeadProfile:
    for appointment in state.rows["appointments"]:
        if appointment["id"] == appointment_id:
            return state.lead_profile_by_id[appointment["lead_id"]]
    raise KeyError(f"Unknown appointment id: {appointment_id}")


def appointment_reason(kind: str) -> tuple[str, str]:
    if kind == "no_show":
        return "no_show", "missed_call"
    if kind == "canceled":
        return "no_show", "cancelled_call"
    if kind == "rescheduled":
        return "timing_issue", "needs_more_time"
    raise ValueError(f"Unsupported appointment insight kind: {kind}")


def diagnostic_insight_row(
    org_id: str,
    insight_id: uuid.UUID,
    profile: LeadProfile,
    *,
    source_table: str,
    source_record_id: uuid.UUID,
    source_text_type: str,
    source_event_at: datetime,
    source_text: str,
    reason_category: str,
    reason_subcategory: str,
    is_conversion_blocker: bool,
) -> dict[str, Any]:
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    buying_intent, lead_quality = intent_and_quality(profile.scenario)
    return {
        "id": insight_id,
        "clerk_org_id": org_id,
        "lead_id": profile.id,
        "source_table": source_table,
        "source_record_id": source_record_id,
        "source_text_type": source_text_type,
        "source_event_at": source_event_at,
        "source_text_hash": source_hash,
        "source_text_length": len(source_text),
        "reason_category": reason_category,
        "reason_subcategory": reason_subcategory,
        "is_conversion_blocker": is_conversion_blocker,
        "buying_intent_level": buying_intent,
        "lead_quality_level": lead_quality,
        "profession_category": PROFESSION_TO_ENUM.get(profile.profession, "unknown"),
        "employment_status": EMPLOYMENT_TO_ENUM.get(profile.employment_status, "unknown"),
        "extraction_status": "success",
        "extracted_at": DEMO_REFERENCE_DATE,
        "created_at": DEMO_REFERENCE_DATE,
    }


def intent_and_quality(scenario: str) -> tuple[str, str]:
    mapping = {
        "paid_converted": ("very_high", "high_quality"),
        "completed_not_signed": ("medium", "medium_quality"),
        "signed_not_paid": ("high", "medium_quality"),
        "booked_not_completed": ("medium", "medium_quality"),
        "lead_only": ("low", "unknown"),
        "lost": ("low", "low_quality"),
        "unqualified": ("very_low", "unqualified"),
    }
    return mapping[scenario]


def cleanup_dummy_org(conn: Connection, org_id: str) -> dict[str, int]:
    cleanup_sql = (
        (
            "diagnostic_lead_snapshot",
            "DELETE FROM diagnostic_lead_snapshot WHERE clerk_org_id = :org_id",
        ),
        (
            "diagnostic_text_insights",
            "DELETE FROM diagnostic_text_insights WHERE clerk_org_id = :org_id",
        ),
        ("refunds", "DELETE FROM refunds WHERE clerk_org_id = :org_id"),
        ("payments", "DELETE FROM payments WHERE clerk_org_id = :org_id"),
        ("contracts", "DELETE FROM contracts WHERE clerk_org_id = :org_id"),
        ("fathom_call_records", "DELETE FROM fathom_call_records WHERE clerk_org_id = :org_id"),
        ("appointments", "DELETE FROM appointments WHERE clerk_org_id = :org_id"),
        (
            "opt_in_question_answers",
            """
            DELETE FROM opt_in_question_answers q
            USING opt_ins o
            WHERE q.opt_in_id = o.id
              AND o.clerk_org_id = :org_id
            """,
        ),
        (
            "traffic_attributions",
            """
            DELETE FROM traffic_attributions ta
            USING opt_ins o
            WHERE ta.opt_in_id = o.id
              AND o.clerk_org_id = :org_id
            """,
        ),
        ("opt_ins", "DELETE FROM opt_ins WHERE clerk_org_id = :org_id"),
        ("leads", "DELETE FROM leads WHERE clerk_org_id = :org_id"),
        (
            "appointment_event_types",
            "DELETE FROM appointment_event_types WHERE clerk_org_id = :org_id",
        ),
        ("programs", "DELETE FROM programs WHERE clerk_org_id = :org_id"),
        ("marketing_sources", "DELETE FROM marketing_sources WHERE clerk_org_id = :org_id"),
        ("sales_statuses", "DELETE FROM sales_statuses WHERE clerk_org_id = :org_id"),
    )
    deleted_counts: dict[str, int] = {}
    for table_name, sql in cleanup_sql:
        if table_name == "diagnostic_lead_snapshot" and not public_table_exists(
            conn,
            table_name,
        ):
            deleted_counts[table_name] = 0
            continue
        result = conn.execute(text(sql), {"org_id": org_id})
        deleted_counts[table_name] = int(result.rowcount or 0)
    return deleted_counts


def public_table_exists(conn: Connection, table_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT EXISTS (
                  SELECT 1
                  FROM information_schema.tables
                  WHERE table_schema = 'public'
                    AND table_name = :table_name
                )
                """
            ),
            {"table_name": table_name},
        ).scalar_one()
    )


def ensure_no_existing_demo_rows(conn: Connection, org_id: str) -> None:
    rows = conn.execute(
        text(
            """
            SELECT table_name, row_count
            FROM (
              SELECT 'sales_statuses' AS table_name, COUNT(*)::int AS row_count
                FROM sales_statuses WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'marketing_sources', COUNT(*)::int
                FROM marketing_sources WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'programs', COUNT(*)::int
                FROM programs WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'appointment_event_types', COUNT(*)::int
                FROM appointment_event_types WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'leads', COUNT(*)::int
                FROM leads WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'opt_ins', COUNT(*)::int
                FROM opt_ins WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'appointments', COUNT(*)::int
                FROM appointments WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'fathom_call_records', COUNT(*)::int
                FROM fathom_call_records WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'contracts', COUNT(*)::int
                FROM contracts WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'payments', COUNT(*)::int
                FROM payments WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'refunds', COUNT(*)::int
                FROM refunds WHERE clerk_org_id = :org_id
              UNION ALL
              SELECT 'diagnostic_text_insights', COUNT(*)::int
                FROM diagnostic_text_insights WHERE clerk_org_id = :org_id
            ) counts
            WHERE row_count > 0
            ORDER BY table_name
            """
        ),
        {"org_id": org_id},
    ).mappings()
    existing = [f"{row['table_name']}={row['row_count']}" for row in rows]
    if existing:
        raise RuntimeError(
            "Dummy org rows already exist. Rerun with --force for a safe dummy-org rebuild. "
            f"Existing rows: {', '.join(existing)}"
        )


def warn_optional_dependency_rows(conn: Connection, org_id: str) -> None:
    optional_count = sum(fetch_optional_row_counts(conn, org_id).values())
    if optional_count:
        print(
            "Warning: optional/admin first-demo tables already contain rows connected to "
            f"the dummy org. This script will not create or delete those rows. Found optional "
            f"rows: {optional_count}."
        )


def insert_seed_rows(conn: Connection, state: SeedState) -> dict[str, int]:
    insert_order = (
        "sales_statuses",
        "marketing_sources",
        "programs",
        "appointment_event_types",
        "leads",
        "opt_ins",
        "traffic_attributions",
        "opt_in_question_answers",
        "appointments",
        "fathom_call_records",
        "contracts",
        "payments",
        "refunds",
        "diagnostic_text_insights",
    )
    counts: dict[str, int] = {}
    for table in insert_order:
        rows = state.rows.get(table, [])
        if not rows:
            counts[table] = 0
            continue
        execute_many(conn, table, rows)
        counts[table] = len(rows)
    return counts


def execute_many(conn: Connection, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns = list(rows[0].keys())
    placeholders = [placeholder_for(table, column) for column in columns]
    sql = text(
        f"""
        INSERT INTO {table} ({", ".join(columns)})
        VALUES ({", ".join(placeholders)})
        """
    )
    conn.execute(sql, rows)


def placeholder_for(table: str, column: str) -> str:
    if (table, column) in {
        ("appointment_event_types", "metadata"),
        ("fathom_call_records", "key_points"),
        ("fathom_call_records", "action_items"),
        ("fathom_call_records", "objections"),
        ("fathom_call_records", "raw_payload"),
        ("opt_ins", "raw_payload"),
    }:
        return f"CAST(:{column} AS jsonb)"
    return f":{column}"


def build_diagnostic_snapshot(engine: Engine, org_id: str) -> dict[str, Any]:
    # Diagnostic snapshot is derived after base records are seeded. The helper
    # owns its transaction, so base rows are committed before this runs.
    return build_diagnostic_lead_snapshot_once(org_id, force=True, engine=engine)


def run_validations(conn: Connection, org_id: str) -> list[ValidationResult]:
    validations = [
        validate_count(conn, org_id, "active_leads", lead_count_sql(), 500),
        validate_distribution(
            conn,
            org_id,
            "monthly_lead_distribution",
            monthly_distribution_sql(),
            MONTHLY_LEAD_DISTRIBUTION,
        ),
        validate_distribution(
            conn,
            org_id,
            "source_distribution",
            source_distribution_sql(),
            SOURCE_DISTRIBUTION,
        ),
        validate_scalar_zero(
            conn,
            org_id,
            "source_quality",
            """
            SELECT COUNT(*)::int
            FROM leads l
            LEFT JOIN marketing_sources first_ms
              ON first_ms.id = l.first_source_id
             AND first_ms.clerk_org_id = l.clerk_org_id
            LEFT JOIN marketing_sources last_ms
              ON last_ms.id = l.last_source_id
             AND last_ms.clerk_org_id = l.clerk_org_id
            WHERE l.clerk_org_id = :org_id
              AND (
                l.first_source_id IS NULL
                OR l.last_source_id IS NULL
                OR NULLIF(BTRIM(l.first_source_name), '') IS NULL
                OR NULLIF(BTRIM(l.last_source_name), '') IS NULL
                OR l.first_source_name ILIKE 'unknown'
                OR l.last_source_name ILIKE 'unknown'
                OR first_ms.id IS NULL
                OR last_ms.id IS NULL
              )
            """,
        ),
        validate_scalar_zero(
            conn,
            org_id,
            "appointment_fathom_mismatches",
            """
            WITH appointment_rows AS (
              SELECT
                a.id,
                a.schedule_time,
                a.no_show,
                ss.role::text AS outcome_role,
                COUNT(f.id)::int AS fathom_count
              FROM appointments a
              JOIN sales_statuses ss
                ON ss.id = a.outcome_id
               AND ss.clerk_org_id = a.clerk_org_id
              LEFT JOIN fathom_call_records f
                ON f.appointment_id = a.id
               AND f.clerk_org_id = a.clerk_org_id
              WHERE a.clerk_org_id = :org_id
                AND a.is_deleted = false
              GROUP BY a.id, a.schedule_time, a.no_show, ss.role
            )
            SELECT COUNT(*)::int
            FROM appointment_rows
            WHERE (
              schedule_time < NOW()
              AND no_show = false
              AND outcome_role NOT IN ('CANCELED', 'RESCHEDULED')
              AND fathom_count <> 1
            )
            OR (
              (
                no_show = true
                OR outcome_role IN ('CANCELED', 'RESCHEDULED')
                OR schedule_time >= NOW()
              )
              AND fathom_count <> 0
            )
            """,
        ),
        validate_scalar_zero(
            conn,
            org_id,
            "relationship_integrity",
            """
            WITH problems AS (
              SELECT a.id::text AS id
              FROM appointments a
              LEFT JOIN leads l ON l.id = a.lead_id AND l.clerk_org_id = a.clerk_org_id
              WHERE a.clerk_org_id = :org_id AND l.id IS NULL
              UNION ALL
              SELECT o.id::text
              FROM opt_ins o
              LEFT JOIN leads l ON l.id = o.lead_id AND l.clerk_org_id = o.clerk_org_id
              WHERE o.clerk_org_id = :org_id AND l.id IS NULL
              UNION ALL
              SELECT c.id::text
              FROM contracts c
              LEFT JOIN leads l ON l.id = c.lead_id AND l.clerk_org_id = c.clerk_org_id
              LEFT JOIN programs p ON p.id = c.program_id AND p.clerk_org_id = c.clerk_org_id
              WHERE c.clerk_org_id = :org_id AND (l.id IS NULL OR p.id IS NULL)
              UNION ALL
              SELECT p.id::text
              FROM payments p
              LEFT JOIN leads l ON l.id = p.lead_id AND l.clerk_org_id = p.clerk_org_id
              LEFT JOIN contracts c ON c.id = p.contract_id AND c.clerk_org_id = p.clerk_org_id
              WHERE p.clerk_org_id = :org_id AND (l.id IS NULL OR c.id IS NULL)
              UNION ALL
              SELECT r.id::text
              FROM refunds r
              LEFT JOIN payments p ON p.id = r.payment_id AND p.clerk_org_id = r.clerk_org_id
              WHERE r.clerk_org_id = :org_id AND p.id IS NULL
            )
            SELECT COUNT(*)::int FROM problems
            """,
        ),
        validate_scalar_zero(
            conn,
            org_id,
            "fathom_relationship_integrity",
            """
            WITH duplicate_appointments AS (
              SELECT appointment_id
              FROM fathom_call_records
              WHERE clerk_org_id = :org_id
                AND appointment_id IS NOT NULL
              GROUP BY appointment_id
              HAVING COUNT(*) > 1
            ),
            invalid_fathom AS (
              SELECT f.id::text
              FROM fathom_call_records f
              LEFT JOIN appointments a
                ON a.id = f.appointment_id
               AND a.clerk_org_id = f.clerk_org_id
               AND a.is_deleted = false
              LEFT JOIN sales_statuses ss
                ON ss.id = a.outcome_id
               AND ss.clerk_org_id = a.clerk_org_id
              WHERE f.clerk_org_id = :org_id
                AND (
                  a.id IS NULL
                  OR a.schedule_time >= NOW()
                  OR a.no_show = true
                  OR ss.role::text IN ('CANCELED', 'RESCHEDULED')
                )
              UNION ALL
              SELECT appointment_id::text
              FROM duplicate_appointments
            )
            SELECT COUNT(*)::int
            FROM invalid_fathom
            """,
        ),
        validate_scalar_zero(
            conn,
            org_id,
            "scenario_revenue_consistency",
            scenario_revenue_consistency_sql(),
        ),
        validate_scalar_zero(
            conn,
            org_id,
            "diagnostic_text_insight_relationships",
            diagnostic_text_insight_relationship_sql(),
        ),
        validate_scalar_zero(
            conn,
            org_id,
            "refund_amounts",
            """
            SELECT COUNT(*)::int
            FROM refunds r
            JOIN payments p
              ON p.id = r.payment_id
             AND p.clerk_org_id = r.clerk_org_id
            WHERE r.clerk_org_id = :org_id
              AND (
                p.status::text <> 'PAID'
                OR r.amount > p.amount
                OR r.refunded_at < p.paid_at
              )
            """,
        ),
        validate_optional_table_warning(conn, org_id),
        validate_count(conn, org_id, "diagnostic_snapshot_rows", snapshot_count_sql(), 500),
        validate_scalar_zero(
            conn,
            org_id,
            "diagnostic_snapshot_quality_flags",
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
                OR completed_calls_missing_fathom_count <> 0
                OR (
                  completed_call_count > 0
                  AND completed_call_fathom_coverage_rate <> 100.00
                )
              )
            """,
        ),
    ]
    return validations


def lead_count_sql() -> str:
    return """
    SELECT COUNT(*)::int
    FROM leads
    WHERE clerk_org_id = :org_id
      AND is_deleted = false
    """


def monthly_distribution_sql() -> str:
    return """
    SELECT to_char(date_trunc('month', created_at), 'YYYY-MM') AS bucket, COUNT(*)::int AS row_count
    FROM leads
    WHERE clerk_org_id = :org_id
      AND is_deleted = false
    GROUP BY 1
    ORDER BY 1
    """


def source_distribution_sql() -> str:
    return """
    SELECT first_source_name AS bucket, COUNT(*)::int AS row_count
    FROM leads
    WHERE clerk_org_id = :org_id
      AND is_deleted = false
    GROUP BY first_source_name
    ORDER BY first_source_name
    """


def optional_table_count_sql() -> str:
    return """
    SELECT (
      (SELECT COUNT(*) FROM invoices WHERE clerk_org_id = :org_id) +
      (SELECT COUNT(*) FROM payment_proofs WHERE clerk_org_id = :org_id) +
      (SELECT COUNT(*)
       FROM payment_links pl
       JOIN payments p ON p.id = pl.payment_id
       WHERE p.clerk_org_id = :org_id) +
      (SELECT COUNT(*)
       FROM contract_subscriptions cs
       JOIN contracts c ON c.id = cs.contract_id
       WHERE c.clerk_org_id = :org_id) +
      (SELECT COUNT(*)
       FROM subscription_checkout_links scl
       JOIN contract_subscriptions cs ON cs.id = scl.subscription_id
       JOIN contracts c ON c.id = cs.contract_id
       WHERE c.clerk_org_id = :org_id) +
      (SELECT COUNT(*) FROM unmatched_payments WHERE clerk_org_id = :org_id)
    )::int
    """


def validate_optional_table_warning(conn: Connection, org_id: str) -> ValidationResult:
    counts = fetch_optional_row_counts(conn, org_id)
    total = sum(counts.values())
    details = ", ".join(f"{table}={count}" for table, count in counts.items())
    if not details:
        details = "optional tables not present"
    return ValidationResult(
        check_name="optional_seeded_rows_warning",
        passed=True,
        details=f"warning {total}; {details}",
    )


def scenario_revenue_consistency_sql() -> str:
    return """
    WITH demo_leads AS (
      SELECT id, external_reference
      FROM leads
      WHERE clerk_org_id = :org_id
        AND is_deleted = false
    ),
    appointment_agg AS (
      SELECT lead_id, COUNT(*)::int AS appointment_count
      FROM appointments
      WHERE clerk_org_id = :org_id
        AND is_deleted = false
      GROUP BY lead_id
    ),
    contract_agg AS (
      SELECT
        lead_id,
        COUNT(*)::int AS contract_count,
        BOOL_OR(status::text = 'SIGNED') AS has_signed_contract
      FROM contracts
      WHERE clerk_org_id = :org_id
        AND is_deleted = false
      GROUP BY lead_id
    ),
    payment_agg AS (
      SELECT
        lead_id,
        COUNT(*)::int AS payment_count,
        BOOL_OR(status::text = 'PAID') AS has_paid_payment,
        BOOL_OR(status::text IN ('PENDING', 'FAILED')) AS has_pending_or_failed_payment
      FROM payments
      WHERE clerk_org_id = :org_id
        AND is_deleted = false
      GROUP BY lead_id
    )
    SELECT COUNT(*)::int
    FROM demo_leads l
    LEFT JOIN appointment_agg aa ON aa.lead_id = l.id
    LEFT JOIN contract_agg ca ON ca.lead_id = l.id
    LEFT JOIN payment_agg pa ON pa.lead_id = l.id
    WHERE (
      l.external_reference LIKE 'demo:paid_converted:%'
      AND (
        NOT COALESCE(ca.has_signed_contract, false)
        OR NOT COALESCE(pa.has_paid_payment, false)
      )
    )
    OR (
      l.external_reference LIKE 'demo:signed_not_paid:%'
      AND (
        NOT COALESCE(ca.has_signed_contract, false)
        OR NOT COALESCE(pa.has_pending_or_failed_payment, false)
      )
    )
    OR (
      l.external_reference LIKE 'demo:completed_not_signed:%'
      AND COALESCE(pa.has_paid_payment, false)
    )
    OR (
      l.external_reference LIKE 'demo:lead_only:%'
      AND (
        COALESCE(aa.appointment_count, 0) > 0
        OR COALESCE(ca.contract_count, 0) > 0
        OR COALESCE(pa.payment_count, 0) > 0
      )
    )
    OR (
      l.external_reference LIKE 'demo:booked_not_completed:%'
      AND (
        COALESCE(ca.contract_count, 0) > 0
        OR COALESCE(pa.payment_count, 0) > 0
      )
    )
    OR (
      l.external_reference LIKE 'demo:unqualified:%'
      AND COALESCE(pa.payment_count, 0) > 0
    )
    """


def diagnostic_text_insight_relationship_sql() -> str:
    return """
    WITH invalid AS (
      SELECT d.id::text
      FROM diagnostic_text_insights d
      LEFT JOIN leads l
        ON l.id = d.lead_id
       AND l.clerk_org_id = d.clerk_org_id
       AND l.is_deleted = false
      WHERE d.clerk_org_id = :org_id
        AND (
          l.id IS NULL
          OR NULLIF(BTRIM(d.source_text_hash), '') IS NULL
          OR COALESCE(d.source_text_length, 0) <= 0
          OR d.extraction_status <> 'success'
        )
      UNION ALL
      SELECT d.id::text
      FROM diagnostic_text_insights d
      LEFT JOIN fathom_call_records f
        ON f.id = d.source_record_id
       AND f.clerk_org_id = d.clerk_org_id
      WHERE d.clerk_org_id = :org_id
        AND d.source_text_type = 'fathom_summary'
        AND (
          d.source_table <> 'fathom_call_records'
          OR f.id IS NULL
          OR d.source_event_at IS DISTINCT FROM f.call_started_at
        )
      UNION ALL
      SELECT d.id::text
      FROM diagnostic_text_insights d
      WHERE d.clerk_org_id = :org_id
        AND d.source_table = 'fathom_call_records'
        AND d.source_text_type <> 'fathom_summary'
    )
    SELECT COUNT(*)::int
    FROM invalid
    """


def snapshot_count_sql() -> str:
    return """
    SELECT COUNT(*)::int
    FROM diagnostic_lead_snapshot
    WHERE clerk_org_id = :org_id
    """


def validate_count(
    conn: Connection,
    org_id: str,
    check_name: str,
    sql: str,
    expected_count: int,
) -> ValidationResult:
    actual = scalar_int(conn, sql, {"org_id": org_id})
    return ValidationResult(
        check_name=check_name,
        passed=actual == expected_count,
        details=f"expected {expected_count}, got {actual}",
    )


def validate_distribution(
    conn: Connection,
    org_id: str,
    check_name: str,
    sql: str,
    expected: dict[str, int],
) -> ValidationResult:
    rows = conn.execute(text(sql), {"org_id": org_id}).mappings().all()
    actual = {str(row["bucket"]): int(row["row_count"]) for row in rows}
    return ValidationResult(
        check_name=check_name,
        passed=actual == expected,
        details=f"expected {expected}, got {actual}",
    )


def validate_scalar_zero(
    conn: Connection,
    org_id: str,
    check_name: str,
    sql: str,
    *,
    warning_only: bool = False,
) -> ValidationResult:
    actual = scalar_int(conn, sql, {"org_id": org_id})
    passed = actual == 0 or warning_only
    prefix = "warning" if warning_only and actual else "count"
    return ValidationResult(check_name=check_name, passed=passed, details=f"{prefix} {actual}")


def scalar_int(conn: Connection, sql: str, params: dict[str, Any]) -> int:
    value = conn.execute(text(sql), params).scalar_one()
    return int(value or 0)


def fetch_row_counts(conn: Connection, org_id: str) -> dict[str, int]:
    table_sql = {
        "sales_statuses": "SELECT COUNT(*)::int FROM sales_statuses WHERE clerk_org_id = :org_id",
        "marketing_sources": "SELECT COUNT(*)::int FROM marketing_sources WHERE clerk_org_id = :org_id",
        "programs": "SELECT COUNT(*)::int FROM programs WHERE clerk_org_id = :org_id",
        "appointment_event_types": (
            "SELECT COUNT(*)::int FROM appointment_event_types WHERE clerk_org_id = :org_id"
        ),
        "leads": "SELECT COUNT(*)::int FROM leads WHERE clerk_org_id = :org_id",
        "opt_ins": "SELECT COUNT(*)::int FROM opt_ins WHERE clerk_org_id = :org_id",
        "traffic_attributions": (
            "SELECT COUNT(*)::int FROM traffic_attributions ta "
            "JOIN opt_ins o ON o.id = ta.opt_in_id WHERE o.clerk_org_id = :org_id"
        ),
        "opt_in_question_answers": (
            "SELECT COUNT(*)::int FROM opt_in_question_answers q "
            "JOIN opt_ins o ON o.id = q.opt_in_id WHERE o.clerk_org_id = :org_id"
        ),
        "appointments": "SELECT COUNT(*)::int FROM appointments WHERE clerk_org_id = :org_id",
        "fathom_call_records": (
            "SELECT COUNT(*)::int FROM fathom_call_records WHERE clerk_org_id = :org_id"
        ),
        "contracts": "SELECT COUNT(*)::int FROM contracts WHERE clerk_org_id = :org_id",
        "payments": "SELECT COUNT(*)::int FROM payments WHERE clerk_org_id = :org_id",
        "refunds": "SELECT COUNT(*)::int FROM refunds WHERE clerk_org_id = :org_id",
        "diagnostic_text_insights": (
            "SELECT COUNT(*)::int FROM diagnostic_text_insights WHERE clerk_org_id = :org_id"
        ),
        "diagnostic_lead_snapshot": (
            "SELECT COUNT(*)::int FROM diagnostic_lead_snapshot WHERE clerk_org_id = :org_id"
        ),
    }
    return {
        table: scalar_int(conn, sql, {"org_id": org_id})
        for table, sql in table_sql.items()
    }


def fetch_optional_row_counts(conn: Connection, org_id: str) -> dict[str, int]:
    table_sql: dict[str, tuple[tuple[str, ...], str]] = {
        "invoices": (
            ("invoices",),
            "SELECT COUNT(*)::int FROM invoices WHERE clerk_org_id = :org_id",
        ),
        "payment_links": (
            ("payment_links",),
            "SELECT COUNT(*)::int FROM payment_links pl "
            "JOIN payments p ON p.id = pl.payment_id WHERE p.clerk_org_id = :org_id",
        ),
        "payment_proofs": (
            ("payment_proofs",),
            "SELECT COUNT(*)::int FROM payment_proofs WHERE clerk_org_id = :org_id",
        ),
        "contract_subscriptions": (
            ("contract_subscriptions",),
            "SELECT COUNT(*)::int FROM contract_subscriptions cs "
            "JOIN contracts c ON c.id = cs.contract_id WHERE c.clerk_org_id = :org_id",
        ),
        "subscription_checkout_links": (
            ("subscription_checkout_links", "contract_subscriptions"),
            "SELECT COUNT(*)::int FROM subscription_checkout_links scl "
            "JOIN contract_subscriptions cs ON cs.id = scl.subscription_id "
            "JOIN contracts c ON c.id = cs.contract_id WHERE c.clerk_org_id = :org_id",
        ),
        "unmatched_payments": (
            ("unmatched_payments",),
            "SELECT COUNT(*)::int FROM unmatched_payments WHERE clerk_org_id = :org_id",
        ),
    }
    counts: dict[str, int] = {}
    for table, (required_tables, sql) in table_sql.items():
        if all(public_table_exists(conn, required_table) for required_table in required_tables):
            counts[table] = scalar_int(conn, sql, {"org_id": org_id})
        else:
            counts[table] = 0
    return counts


def planned_appointment_stats(state: SeedState) -> dict[str, int]:
    fathom_by_appointment = set(state.fathom_ids_by_appointment_id)
    appointment_rows = state.rows.get("appointments", [])
    stats = {
        "appointments": len(appointment_rows),
        "completed": 0,
        "no_show": 0,
        "canceled": 0,
        "rescheduled": 0,
        "future": 0,
        "completed_missing_fathom": 0,
        "no_show_with_fathom": 0,
        "canceled_with_fathom": 0,
        "rescheduled_with_fathom": 0,
        "future_with_fathom": 0,
    }
    for appointment in appointment_rows:
        appointment_id = appointment["id"]
        kind = state.appointment_kind_by_id[appointment_id]
        stats[kind] += 1
        has_fathom = appointment_id in fathom_by_appointment
        if kind == "completed" and not has_fathom:
            stats["completed_missing_fathom"] += 1
        if kind != "completed" and has_fathom:
            stats[f"{kind}_with_fathom"] += 1
    return stats


def print_dry_run_summary(
    state: SeedState,
    org_id: str,
    optional_counts: dict[str, int],
) -> None:
    appointment_stats = planned_appointment_stats(state)
    print("Demo seed dry run.")
    print("")
    print(f"Organization: {org_id}")
    print("Safety:")
    print("- org guard: passed")
    print("- dry-run: no deletes, inserts, or diagnostic snapshot build will run")
    if BLOCKED_ORG_PLACEHOLDER in BLOCKED_ORG_IDS:
        print("- live-org blocklist: placeholder present; --force will refuse until replaced")
    else:
        print("- live-org blocklist: configured")
    print("")
    print("Planned row counts:")
    for table in REQUIRED_TABLES:
        print(f"- {table}: {state.row_count(table)}")
    print("- diagnostic_lead_snapshot: derived after base seed, expected 500")
    print("")
    print("Planned appointment counts:")
    print(f"- appointments: {appointment_stats['appointments']}")
    print(f"- completed appointments: {appointment_stats['completed']}")
    print(f"- no-show appointments: {appointment_stats['no_show']}")
    print(f"- canceled appointments: {appointment_stats['canceled']}")
    print(f"- rescheduled appointments: {appointment_stats['rescheduled']}")
    print(f"- future appointments: {appointment_stats['future']}")
    print("")
    print("Planned Fathom coverage:")
    print(f"- completed appointments: {appointment_stats['completed']}")
    print(f"- fathom_call_records: {state.row_count('fathom_call_records')}")
    print(f"- completed appointments missing Fathom: {appointment_stats['completed_missing_fathom']}")
    print(f"- Fathom records for no-show appointments: {appointment_stats['no_show_with_fathom']}")
    print(f"- Fathom records for canceled appointments: {appointment_stats['canceled_with_fathom']}")
    print(
        f"- Fathom records for rescheduled appointments: "
        f"{appointment_stats['rescheduled_with_fathom']}"
    )
    print(f"- Fathom records for future appointments: {appointment_stats['future_with_fathom']}")
    print("")
    print("Planned monthly distribution:")
    for month, count in MONTHLY_LEAD_DISTRIBUTION.items():
        print(f"- {month}: {count}")
    print("")
    print("Planned scenario distribution:")
    for scenario, count in SCENARIO_DISTRIBUTION.items():
        print(f"- {scenario}: {count}")
    print("")
    print("Planned source distribution:")
    for source, count in SOURCE_DISTRIBUTION.items():
        print(f"- {source}: {count}")
    print("")
    print("Optional table check for dummy org:")
    for table, count in optional_counts.items():
        print(f"- {table}: {count}")
    optional_total = sum(optional_counts.values())
    if optional_total:
        print(
            f"Warning: optional/admin tables already contain {optional_total} row(s) "
            "connected to the dummy org. They are not seeded by default."
        )
    else:
        print("- warning: none")


def print_summary(
    org_id: str,
    row_counts: dict[str, int],
    validations: list[ValidationResult],
    snapshot_summary: dict[str, Any] | None,
) -> None:
    print("Demo seed completed successfully.")
    print("")
    print("Organization:")
    print(f"- {org_id}")
    print("")
    print("Seeded row counts:")
    for table, count in row_counts.items():
        print(f"- {table}: {count}")
    if snapshot_summary:
        print("")
        print("Diagnostic snapshot:")
        print(f"- rows_inserted: {snapshot_summary.get('rows_inserted')}")
        print(f"- validation_status: {snapshot_summary.get('validation_status')}")
    print("")
    print("Validation:")
    for result in validations:
        status = "passed" if result.passed else "failed"
        print(f"- {result.check_name}: {status} ({result.details})")


def print_validation_failure(validations: list[ValidationResult]) -> None:
    print("Demo seed failed validation.")
    print("")
    print("Failed checks:")
    for result in validations:
        if not result.passed:
            print(f"- {result.check_name}: {result.details}")
    print("")
    print_post_write_failure_notice()


def print_post_write_failure_notice() -> None:
    print("Validation failed after seed attempt.")
    print("Dummy org data may have been partially written.")
    print(
        "Run the script again with --force after fixing the issue, or allow automatic "
        f"cleanup for {DUMMY_ORG_ID} only."
    )


def cleanup_after_failed_seed(engine: Engine, org_id: str) -> None:
    if org_id != DUMMY_ORG_ID:
        raise RuntimeError("Automatic cleanup is only allowed for the fixed dummy org.")
    try:
        with engine.begin() as conn:
            cleanup_dummy_org(conn, org_id)
        print(f"Automatic cleanup completed for {org_id} only.", file=sys.stderr)
    except Exception as cleanup_exc:
        print(
            f"Automatic cleanup failed for {org_id}: {cleanup_exc}. "
            "Review the database state before retrying.",
            file=sys.stderr,
        )


def run_seed(args: argparse.Namespace) -> None:
    org_id = str(args.org_id).strip()
    validate_safety_args(args)
    state = build_seed_state(org_id)
    engine = get_engine()
    schema_smoke_check(engine)

    if args.dry_run:
        with engine.connect() as conn:
            optional_counts = fetch_optional_row_counts(conn, org_id)
        print_dry_run_summary(state, org_id, optional_counts)
        return

    started_at = time.monotonic()
    wrote_committed_rows = False
    validation_failure_reported = False
    snapshot_summary: dict[str, Any] | None = None
    try:
        with engine.begin() as conn:
            warn_optional_dependency_rows(conn, org_id)
            if args.force:
                cleanup_dummy_org(conn, org_id)
            else:
                ensure_no_existing_demo_rows(conn, org_id)
            insert_seed_rows(conn, state)
        wrote_committed_rows = True

        snapshot_summary = build_diagnostic_snapshot(engine, org_id)

        with engine.connect() as conn:
            validations = run_validations(conn, org_id)
            failed = [result for result in validations if not result.passed]
            if failed:
                print_validation_failure(validations)
                validation_failure_reported = True
                raise RuntimeError("Demo seed failed validation.")
            row_counts = fetch_row_counts(conn, org_id)
    except Exception:
        if wrote_committed_rows:
            if not validation_failure_reported:
                print_post_write_failure_notice()
            cleanup_after_failed_seed(engine, org_id)
        raise

    duration_seconds = round(time.monotonic() - started_at, 3)
    print_summary(org_id, row_counts, validations, snapshot_summary)
    print("")
    print(f"Duration seconds: {duration_seconds}")


def main() -> int:
    try:
        args = parse_args()
        run_seed(args)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
