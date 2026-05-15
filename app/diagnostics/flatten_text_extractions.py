"""Flatten diagnostic text extraction JSONL into diagnostic_text_insights."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "artifacts" / "diagnostic_text_extractions.jsonl"

ALLOWED_EXTRACTION_STATUSES = {
    "success",
    "skipped_empty",
    "skipped_too_short",
    "skipped_duplicate",
    "skipped_no_signal",
    "validation_failed",
    "llm_failed",
}
ALLOWED_REASON_CATEGORIES = {
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
ALLOWED_REASON_SUBCATEGORIES = {
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
ALLOWED_BUYING_INTENT_LEVELS = {
    "very_high",
    "high",
    "medium",
    "low",
    "very_low",
    "unknown",
}
ALLOWED_LEAD_QUALITY_LEVELS = {
    "high_quality",
    "medium_quality",
    "low_quality",
    "unqualified",
    "unknown",
}
ALLOWED_PROFESSION_CATEGORIES = {
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
ALLOWED_EMPLOYMENT_STATUSES = {
    "full_time",
    "part_time",
    "self_employed",
    "student",
    "business_owner",
    "unemployed",
    "retired",
    "unknown",
}

REQUIRED_ENVELOPE_FIELDS = {
    "clerk_org_id",
    "lead_id",
    "source_table",
    "source_record_id",
    "source_text_type",
    "source_text_hash",
}

DEDUPLICATION_FIELDS = (
    "clerk_org_id",
    "lead_id",
    "source_table",
    "source_record_id",
    "source_text_type",
    "source_text_hash",
    "reason_category",
    "reason_subcategory",
    "is_conversion_blocker",
    "buying_intent_level",
    "lead_quality_level",
    "profession_category",
    "employment_status",
)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS diagnostic_text_insights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  clerk_org_id text NOT NULL,
  lead_id uuid NOT NULL,

  source_table text NOT NULL,
  source_record_id uuid NOT NULL,
  source_text_type text NOT NULL,
  source_event_at timestamptz,
  source_text_hash text NOT NULL,
  source_text_length integer,

  reason_category text NOT NULL DEFAULT 'unknown',
  reason_subcategory text NOT NULL DEFAULT 'unknown',
  is_conversion_blocker boolean NOT NULL DEFAULT false,
  buying_intent_level text NOT NULL DEFAULT 'unknown',
  lead_quality_level text NOT NULL DEFAULT 'unknown',
  profession_category text NOT NULL DEFAULT 'unknown',
  employment_status text NOT NULL DEFAULT 'unknown',

  extraction_status text NOT NULL DEFAULT 'success',
  extracted_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT chk_dti_extraction_status CHECK (
    extraction_status IN (
      'success',
      'skipped_empty',
      'skipped_too_short',
      'skipped_duplicate',
      'skipped_no_signal',
      'validation_failed',
      'llm_failed'
    )
  ),
  CONSTRAINT chk_dti_reason_category CHECK (
    reason_category IN (
      'price_or_budget',
      'timing_issue',
      'not_decision_maker',
      'needs_partner_approval',
      'trust_issue',
      'low_intent',
      'unclear_need',
      'poor_fit',
      'competition',
      'too_busy',
      'needs_more_information',
      'payment_friction',
      'contract_friction',
      'no_show',
      'ghosted',
      'follow_up_pending',
      'operational_delay',
      'technical_issue',
      'language_or_communication_issue',
      'location_or_timezone_issue',
      'already_solved',
      'unknown'
    )
  ),
  CONSTRAINT chk_dti_reason_subcategory CHECK (
    reason_subcategory IN (
      'price_too_high',
      'budget_not_available',
      'wants_discount',
      'needs_payment_plan',
      'not_ready_now',
      'needs_more_time',
      'waiting_for_partner',
      'waiting_for_team',
      'waiting_for_finance',
      'does_not_trust_offer',
      'needs_proof_or_case_study',
      'unclear_value',
      'comparing_competitor',
      'not_enough_need',
      'wrong_customer_fit',
      'not_qualified',
      'missed_call',
      'cancelled_call',
      'stopped_responding',
      'needs_more_information',
      'contract_not_signed',
      'payment_not_completed',
      'payment_failed',
      'refund_requested',
      'internal_team_delay',
      'system_or_link_issue',
      'language_barrier',
      'timezone_issue',
      'issue_already_solved',
      'other',
      'unknown'
    )
  ),
  CONSTRAINT chk_dti_buying_intent_level CHECK (
    buying_intent_level IN (
      'very_high',
      'high',
      'medium',
      'low',
      'very_low',
      'unknown'
    )
  ),
  CONSTRAINT chk_dti_lead_quality_level CHECK (
    lead_quality_level IN (
      'high_quality',
      'medium_quality',
      'low_quality',
      'unqualified',
      'unknown'
    )
  ),
  CONSTRAINT chk_dti_profession_category CHECK (
    profession_category IN (
      'student',
      'employee',
      'self_employed',
      'business_owner',
      'entrepreneur',
      'freelancer',
      'trader_or_investor',
      'finance_or_accounting',
      'sales_or_marketing',
      'healthcare',
      'education',
      'technology',
      'engineering',
      'construction_or_trades',
      'hospitality',
      'retail',
      'real_estate',
      'transport_or_logistics',
      'creative_or_media',
      'government_or_public_sector',
      'unemployed',
      'retired',
      'other',
      'unknown'
    )
  ),
  CONSTRAINT chk_dti_employment_status CHECK (
    employment_status IN (
      'full_time',
      'part_time',
      'self_employed',
      'student',
      'business_owner',
      'unemployed',
      'retired',
      'unknown'
    )
  )
)
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_dti_org ON diagnostic_text_insights (clerk_org_id)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_lead ON diagnostic_text_insights (clerk_org_id, lead_id)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_source ON diagnostic_text_insights (clerk_org_id, source_table, source_text_type)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_source_hash ON diagnostic_text_insights (clerk_org_id, source_text_hash)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_reason ON diagnostic_text_insights (clerk_org_id, reason_category)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_reason_subcategory ON diagnostic_text_insights (clerk_org_id, reason_category, reason_subcategory)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_blocker ON diagnostic_text_insights (clerk_org_id, is_conversion_blocker)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_intent ON diagnostic_text_insights (clerk_org_id, buying_intent_level)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_quality ON diagnostic_text_insights (clerk_org_id, lead_quality_level)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_profession ON diagnostic_text_insights (clerk_org_id, profession_category)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_employment ON diagnostic_text_insights (clerk_org_id, employment_status)",
    "CREATE INDEX IF NOT EXISTS idx_dti_org_event_at ON diagnostic_text_insights (clerk_org_id, source_event_at)",
]

CREATE_UNIQUE_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_dti_source_insight
ON diagnostic_text_insights (
  clerk_org_id,
  lead_id,
  source_table,
  source_record_id,
  source_text_type,
  source_text_hash,
  reason_category,
  reason_subcategory,
  is_conversion_blocker,
  buying_intent_level,
  lead_quality_level,
  profession_category,
  employment_status
)
"""

DELETE_ORG_SQL = """
DELETE FROM diagnostic_text_insights
WHERE clerk_org_id = :org_id
"""

INSERT_INSIGHT_SQL = """
INSERT INTO diagnostic_text_insights (
  clerk_org_id,
  lead_id,
  source_table,
  source_record_id,
  source_text_type,
  source_event_at,
  source_text_hash,
  source_text_length,
  reason_category,
  reason_subcategory,
  is_conversion_blocker,
  buying_intent_level,
  lead_quality_level,
  profession_category,
  employment_status,
  extraction_status,
  extracted_at
) VALUES (
  :clerk_org_id,
  CAST(:lead_id AS uuid),
  :source_table,
  CAST(:source_record_id AS uuid),
  :source_text_type,
  CAST(:source_event_at AS timestamptz),
  :source_text_hash,
  :source_text_length,
  :reason_category,
  :reason_subcategory,
  :is_conversion_blocker,
  :buying_intent_level,
  :lead_quality_level,
  :profession_category,
  :employment_status,
  :extraction_status,
  CAST(:extracted_at AS timestamptz)
)
ON CONFLICT (
  clerk_org_id,
  lead_id,
  source_table,
  source_record_id,
  source_text_type,
  source_text_hash,
  reason_category,
  reason_subcategory,
  is_conversion_blocker,
  buying_intent_level,
  lead_quality_level,
  profession_category,
  employment_status
) DO NOTHING
"""


@dataclass
class FlattenSummary:
    org_id: str
    jsonl_rows_read: int = 0
    jsonl_rows_for_org: int = 0
    success_jsonl_rows: int = 0
    non_success_jsonl_rows_skipped: int = 0
    insights_seen: int = 0
    insights_inserted: int = 0
    duplicates_skipped: int = 0
    validation_errors: int = 0
    force_used: bool = False
    dry_run: bool = False
    rows_deleted: int = 0
    duration_seconds: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "org_id": self.org_id,
            "jsonl_rows_read": self.jsonl_rows_read,
            "jsonl_rows_for_org": self.jsonl_rows_for_org,
            "success_jsonl_rows": self.success_jsonl_rows,
            "non_success_jsonl_rows_skipped": self.non_success_jsonl_rows_skipped,
            "insights_seen": self.insights_seen,
            "insights_inserted": self.insights_inserted,
            "duplicates_skipped": self.duplicates_skipped,
            "validation_errors": self.validation_errors,
            "force_used": self.force_used,
            "dry_run": self.dry_run,
            "rows_deleted": self.rows_deleted,
            "duration_seconds": self.duration_seconds,
        }


def _env_value(name: str) -> str | None:
    if os.getenv(name):
        return os.getenv(name)
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key == name:
            return value.strip().strip("'\"") or None
    return None


def _diagnostic_database_url() -> str | None:
    return (
        _env_value("HERMON_DIAGNOSTIC_DATABASE_URL")
        or _env_value("SUPABASE_DB_URL")
        or _env_value("HERMON_DATABASE_URL")
        or _env_value("DATABASE_URL")
    )


def _sqlalchemy_psycopg_url(database_url: str) -> str:
    clean_url = database_url.strip()
    if clean_url.startswith("postgresql://"):
        return clean_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if clean_url.startswith("postgres://"):
        return clean_url.replace("postgres://", "postgresql+psycopg://", 1)
    return clean_url


def _create_engine_from_env() -> Any:
    database_url = _diagnostic_database_url()
    if not database_url:
        raise RuntimeError(
            "Missing database URL. Set HERMON_DIAGNOSTIC_DATABASE_URL, SUPABASE_DB_URL, "
            "HERMON_DATABASE_URL, or DATABASE_URL in .env."
        )
    try:
        from sqlalchemy import create_engine
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing SQLAlchemy dependencies. Run `pip install -r requirements.txt`.") from exc
    return create_engine(_sqlalchemy_psycopg_url(database_url), pool_pre_ping=True, future=True)


def _sql_text(sql: str) -> Any:
    try:
        from sqlalchemy import text

        return text(sql)
    except ModuleNotFoundError:
        return sql


def _safe_json_loads(line: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(line)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _coerce_uuid(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        return None


def _coerce_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)


def _validate_timestamp(value: Any, *, required: bool = False) -> str | None:
    if value in (None, ""):
        return None if not required else ""
    text_value = str(value).strip()
    parse_value = text_value.replace("Z", "+00:00")
    try:
        dt.datetime.fromisoformat(parse_value)
    except ValueError:
        return ""
    return text_value


def _enum_value(value: Any, allowed: set[str], default: str = "unknown") -> str | None:
    text_value = _coerce_text(value) or default
    return text_value if text_value in allowed else None


def dedupe_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row[field] for field in DEDUPLICATION_FIELDS)


def build_insert_row(jsonl_row: dict[str, Any], insight: dict[str, Any]) -> dict[str, Any] | None:
    """Return a safe DB row for one insight, or None if validation fails."""

    if not isinstance(insight, dict):
        return None
    for field in REQUIRED_ENVELOPE_FIELDS:
        if not _coerce_text(jsonl_row.get(field)):
            return None

    lead_id = _coerce_uuid(jsonl_row.get("lead_id"))
    source_record_id = _coerce_uuid(jsonl_row.get("source_record_id"))
    if lead_id is None or source_record_id is None:
        return None

    extraction_status = _coerce_text(jsonl_row.get("extraction_status")) or "success"
    if extraction_status not in ALLOWED_EXTRACTION_STATUSES:
        return None

    source_event_at = _validate_timestamp(jsonl_row.get("source_event_at"))
    if source_event_at == "":
        return None
    extracted_at = _validate_timestamp(jsonl_row.get("extracted_at"), required=True)
    if not extracted_at:
        return None

    reason_category = _enum_value(
        insight.get("reason_category"),
        ALLOWED_REASON_CATEGORIES,
    )
    reason_subcategory = _enum_value(
        insight.get("reason_subcategory"),
        ALLOWED_REASON_SUBCATEGORIES,
    )
    buying_intent_level = _enum_value(
        insight.get("buying_intent_level"),
        ALLOWED_BUYING_INTENT_LEVELS,
    )
    lead_quality_level = _enum_value(
        insight.get("lead_quality_level"),
        ALLOWED_LEAD_QUALITY_LEVELS,
    )
    profession_category = _enum_value(
        insight.get("profession_category"),
        ALLOWED_PROFESSION_CATEGORIES,
    )
    employment_status = _enum_value(
        insight.get("employment_status"),
        ALLOWED_EMPLOYMENT_STATUSES,
    )
    if None in {
        reason_category,
        reason_subcategory,
        buying_intent_level,
        lead_quality_level,
        profession_category,
        employment_status,
    }:
        return None

    source_text_length = jsonl_row.get("source_text_length")
    if source_text_length is not None:
        try:
            source_text_length = int(source_text_length)
        except (TypeError, ValueError):
            return None

    return {
        "clerk_org_id": str(jsonl_row["clerk_org_id"]),
        "lead_id": lead_id,
        "source_table": str(jsonl_row["source_table"]),
        "source_record_id": source_record_id,
        "source_text_type": str(jsonl_row["source_text_type"]),
        "source_event_at": source_event_at,
        "source_text_hash": str(jsonl_row["source_text_hash"]),
        "source_text_length": source_text_length,
        "reason_category": reason_category,
        "reason_subcategory": reason_subcategory,
        "is_conversion_blocker": _coerce_bool(insight.get("is_conversion_blocker", False)),
        "buying_intent_level": buying_intent_level,
        "lead_quality_level": lead_quality_level,
        "profession_category": profession_category,
        "employment_status": employment_status,
        "extraction_status": extraction_status,
        "extracted_at": extracted_at,
    }


def collect_insert_rows(
    input_path: str | Path,
    *,
    org_id: str,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], FlattenSummary]:
    """Read JSONL and return validated, deduplicated DB rows with a safe summary."""

    summary = FlattenSummary(org_id=org_id)
    rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[Any, ...]] = set()
    path = Path(input_path)

    with path.open("r", encoding="utf-8") as input_file:
        for line in input_file:
            if limit is not None and summary.jsonl_rows_read >= limit:
                break
            summary.jsonl_rows_read += 1
            if not line.strip():
                summary.validation_errors += 1
                continue
            jsonl_row = _safe_json_loads(line)
            if jsonl_row is None:
                summary.validation_errors += 1
                continue
            if jsonl_row.get("clerk_org_id") != org_id:
                continue
            summary.jsonl_rows_for_org += 1

            if jsonl_row.get("extraction_status") != "success":
                summary.non_success_jsonl_rows_skipped += 1
                continue
            summary.success_jsonl_rows += 1

            llm_output_json = jsonl_row.get("llm_output_json", {})
            if not isinstance(llm_output_json, dict):
                summary.validation_errors += 1
                continue
            insights = llm_output_json.get("insights", [])
            if not isinstance(insights, list):
                summary.validation_errors += 1
                continue

            for insight in insights:
                summary.insights_seen += 1
                insert_row = build_insert_row(jsonl_row, insight)
                if insert_row is None:
                    summary.validation_errors += 1
                    continue
                key = dedupe_key(insert_row)
                if key in seen_keys:
                    summary.duplicates_skipped += 1
                    continue
                seen_keys.add(key)
                rows.append(insert_row)

    return rows, summary


def _ensure_schema(conn: Any) -> None:
    conn.execute(_sql_text(CREATE_TABLE_SQL))
    for statement in CREATE_INDEX_SQL:
        conn.execute(_sql_text(statement))
    conn.execute(_sql_text(CREATE_UNIQUE_INDEX_SQL))


def _execute_database_phase(
    rows: Iterable[dict[str, Any]],
    summary: FlattenSummary,
    *,
    engine: Any,
    create_table: bool,
    force: bool,
) -> None:
    with engine.begin() as conn:
        if create_table:
            _ensure_schema(conn)
        if force:
            delete_result = conn.execute(_sql_text(DELETE_ORG_SQL), {"org_id": summary.org_id})
            summary.rows_deleted = int(getattr(delete_result, "rowcount", 0) or 0)
        for row in rows:
            result = conn.execute(_sql_text(INSERT_INSIGHT_SQL), row)
            rowcount = int(getattr(result, "rowcount", 0) or 0)
            if rowcount:
                summary.insights_inserted += rowcount
            else:
                summary.duplicates_skipped += 1


def run_flatten(
    *,
    input_path: str | Path,
    org_id: str,
    limit: int | None = None,
    dry_run: bool = False,
    force: bool = False,
    create_table: bool = False,
    engine: Any | None = None,
) -> dict[str, Any]:
    """Flatten JSONL extraction rows and optionally insert into Postgres."""

    started_at = time.monotonic()
    clean_org_id = str(org_id or "").strip()
    if not clean_org_id:
        raise ValueError("org_id is required.")

    rows, summary = collect_insert_rows(input_path, org_id=clean_org_id, limit=limit)
    summary.force_used = bool(force)
    summary.dry_run = bool(dry_run)

    if dry_run:
        summary.insights_inserted = len(rows)
    else:
        effective_engine = engine or _create_engine_from_env()
        _execute_database_phase(
            rows,
            summary,
            engine=effective_engine,
            create_table=create_table,
            force=force,
        )

    summary.duration_seconds = round(time.monotonic() - started_at, 3)
    return summary.as_dict()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flatten diagnostic text extraction JSONL into diagnostic_text_insights.",
    )
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--org-id", default=_env_value("HERMON_DEFAULT_CLERK_ORG_ID"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--create-table", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.org_id:
        raise SystemExit("Missing --org-id or HERMON_DEFAULT_CLERK_ORG_ID.")
    summary = run_flatten(
        input_path=args.input_path,
        org_id=args.org_id,
        limit=args.limit,
        dry_run=args.dry_run,
        force=args.force,
        create_table=args.create_table,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
