"""Safe read-only Postgres helper for Hermon SQL analytics.

Use this module from notebooks, APIs, and future LangGraph tools:

    from app.db import get_db
    db = get_db()
    df = db.query_df("SELECT COUNT(*) FROM leads WHERE clerk_org_id = :org_id", {"org_id": org_id})

The helper validates SQL before execution and runs every query inside a
read-only transaction with a statement timeout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_database_settings


APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_DIR.parent
SCHEMA_DIR = APP_DIR / "schema"

DANGEROUS_SQL_RE = re.compile(
    r"\b("
    r"alter|analyze|call|copy|create|delete|do|drop|execute|grant|insert|"
    r"lock|merge|notify|refresh|reindex|revoke|truncate|update|vacuum"
    r")\b",
    re.IGNORECASE,
)
SELECT_STAR_RE = re.compile(
    r"(\bselect\s+\*\s+\bfrom\b|\b[a-zA-Z_][a-zA-Z0-9_]*\.\*)",
    re.IGNORECASE | re.DOTALL,
)
READONLY_QUERY_RE = re.compile(r"^(select|with)\b", re.IGNORECASE)
TABLE_REF_RE = re.compile(
    r"\b(?:from|join)\s+(?:(?:public|information_schema)\.)?\"?([a-zA-Z_][a-zA-Z0-9_]*)\"?",
    re.IGNORECASE,
)
COMMA_TABLE_REF_RE = re.compile(
    r",\s+(?:(?:public|information_schema)\.)?\"?([a-zA-Z_][a-zA-Z0-9_]*)\"?(?=\s|,|$)",
    re.IGNORECASE,
)
TENANT_FILTER_RE = re.compile(
    r"("
    r"(?:\b[a-zA-Z_][a-zA-Z0-9_]*\.)?clerk_org_id\s*(?:=|in)\s*(?::[a-zA-Z_][a-zA-Z0-9_]*|'[^']+'|\([^)]+\))"
    r"|"
    r"(?::[a-zA-Z_][a-zA-Z0-9_]*|'[^']+')\s*=\s*(?:\b[a-zA-Z_][a-zA-Z0-9_]*\.)?clerk_org_id"
    r")",
    re.IGNORECASE,
)

BUSINESS_TABLES = {
    "appointment_event_types",
    "appointments",
    "audit_logs",
    "calendar_availability_snapshots",
    "contract_subscriptions",
    "contracts",
    "diagnostic_lead_snapshot",
    "fathom_call_records",
    "fathom_org_settings",
    "invoices",
    "lead_notes",
    "leads",
    "marketing_sources",
    "notification_logs",
    "notification_masters",
    "opt_ins",
    "payments",
    "payment_proofs",
    "program_provider_products",
    "programs",
    "refunds",
    "sales_statuses",
}

CHILD_TABLES_REQUIRING_PARENT_SCOPE = {
    "opt_in_question_answers",
    "traffic_attributions",
    "payment_links",
    "subscription_checkout_links",
}


class QueryValidationError(ValueError):
    """Raised when SQL violates safety rules."""


@dataclass(frozen=True)
class ReadOnlyQueryConfig:
    """Configuration for safe read-only SQL execution."""

    database_url: str | None = None
    max_rows: int = 500
    statement_timeout_ms: int = 10000
    require_org_scope: bool = True


class ReadOnlyPostgres:
    """Read-only Postgres query runner with SQL safety checks."""

    def __init__(
        self,
        config: ReadOnlyQueryConfig | None = None,
        blocked_path: Path | None = None,
    ) -> None:
        settings = get_database_settings()
        self.config = config or ReadOnlyQueryConfig(
            database_url=settings.database_url,
            max_rows=settings.max_rows,
            statement_timeout_ms=settings.statement_timeout_ms,
            require_org_scope=settings.require_org_scope,
        )
        self.blocked_path = blocked_path or SCHEMA_DIR / "blocked_tables.yaml"
        self.blocked_config = self._load_yaml(self.blocked_path)
        self.blocked_tables = self._load_blocked_tables()
        self.blocked_columns = self.blocked_config.get("blocked_columns", {})
        self._engine: Engine | None = None

    def query_df(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        *,
        max_rows: int | None = None,
    ) -> pd.DataFrame:
        """Validate and execute SQL, returning a pandas DataFrame."""

        validated_sql = self.validate_sql(sql)
        limited_sql = self._wrap_with_limit(validated_sql, max_rows=max_rows)
        return self._execute_df(limited_sql, params=params or {})

    def query_records(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        *,
        max_rows: int | None = None,
    ) -> list[dict[str, Any]]:
        """Validate and execute SQL, returning records for API/agent use."""

        validated_sql = self.validate_sql(sql)
        limited_sql = self._wrap_with_limit(validated_sql, max_rows=max_rows)
        return self._execute_records(limited_sql, params=params or {})

    def validate_sql(self, sql: str) -> str:
        """Return cleaned SQL if safe, otherwise raise QueryValidationError."""

        cleaned = self._clean_sql(sql)
        masked = self._mask_string_literals(cleaned)

        if not READONLY_QUERY_RE.match(cleaned):
            raise QueryValidationError("Only SELECT or WITH queries are allowed.")

        if ";" in masked:
            raise QueryValidationError("Only one SQL statement is allowed.")

        if DANGEROUS_SQL_RE.search(masked):
            raise QueryValidationError("Write/admin SQL keywords are not allowed.")

        if SELECT_STAR_RE.search(masked):
            raise QueryValidationError("SELECT * is not allowed. Select explicit columns.")

        referenced_tables = self._referenced_tables(masked)

        blocked_tables = sorted(referenced_tables.intersection(self.blocked_tables))
        if blocked_tables:
            raise QueryValidationError(f"Blocked table(s) referenced: {', '.join(blocked_tables)}")

        blocked_columns = self._referenced_blocked_columns(masked, referenced_tables)
        if blocked_columns:
            raise QueryValidationError(
                f"Blocked column(s) referenced: {', '.join(sorted(blocked_columns))}"
            )

        if self.config.require_org_scope and self._needs_org_scope(referenced_tables):
            if not self._has_tenant_filter(cleaned):
                raise QueryValidationError(
                    "Business-table queries must filter clerk_org_id to a parameter or literal."
                )

        return cleaned

    def _execute_df(self, sql: str, params: dict[str, Any]) -> pd.DataFrame:
        engine = self._get_engine()
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                conn.exec_driver_sql("SET TRANSACTION READ ONLY")
                conn.exec_driver_sql(
                    f"SET LOCAL statement_timeout = {int(self.config.statement_timeout_ms)}"
                )
                df = pd.read_sql_query(text(sql), conn, params=params)
                transaction.commit()
                return df
            except Exception:
                transaction.rollback()
                raise

    def _execute_records(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        engine = self._get_engine()
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                conn.exec_driver_sql("SET TRANSACTION READ ONLY")
                conn.exec_driver_sql(
                    f"SET LOCAL statement_timeout = {int(self.config.statement_timeout_ms)}"
                )
                result = conn.execute(text(sql), params)
                rows = [dict(row) for row in result.mappings()]
                transaction.commit()
                return rows
            except Exception:
                transaction.rollback()
                raise

    def _get_engine(self) -> Engine:
        database_url = self.config.database_url
        if not database_url:
            raise RuntimeError("Missing HERMON_DATABASE_URL or DATABASE_URL in .env.")
        if self._engine is None:
            self._engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                future=True,
            )
        return self._engine

    def _wrap_with_limit(self, sql: str, *, max_rows: int | None = None) -> str:
        row_limit = self.config.max_rows if max_rows is None else max_rows
        if row_limit is None:
            return sql
        if row_limit <= 0:
            raise QueryValidationError("max_rows must be greater than zero.")
        # The validator blocks SELECT * in model-written SQL. This wrapper is
        # added only after validation so app-side row limiting stays centralized.
        return f"SELECT * FROM ({sql}) AS _safe_query LIMIT {int(row_limit)}"

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _load_blocked_tables(self) -> set[str]:
        blocked = self.blocked_config.get("blocked_tables", {})
        names: set[str] = set()
        for key in ("always_block", "block_for_business_chatbot"):
            names.update(blocked.get(key, []))
        return names

    def _clean_sql(self, sql: str) -> str:
        cleaned = sql.strip()
        cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"--.*?$", " ", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        if cleaned.endswith(";"):
            cleaned = cleaned[:-1].strip()
        return cleaned

    def _mask_string_literals(self, sql: str) -> str:
        return re.sub(r"'(?:''|[^'])*'", "''", sql)

    def _referenced_tables(self, sql: str) -> set[str]:
        referenced_tables = {match.group(1).lower() for match in TABLE_REF_RE.finditer(sql)}
        referenced_tables.update(match.group(1).lower() for match in COMMA_TABLE_REF_RE.finditer(sql))
        return referenced_tables

    def _referenced_blocked_columns(self, sql: str, referenced_tables: set[str]) -> set[str]:
        blocked_columns = set()
        for table in referenced_tables:
            for column in self.blocked_columns.get(table, []):
                if re.search(rf"\b{re.escape(column)}\b", sql, flags=re.IGNORECASE):
                    blocked_columns.add(f"{table}.{column}")
        return blocked_columns

    def _needs_org_scope(self, referenced_tables: set[str]) -> bool:
        scoped_tables = BUSINESS_TABLES.union(CHILD_TABLES_REQUIRING_PARENT_SCOPE)
        return bool(referenced_tables.intersection(scoped_tables))

    def _has_tenant_filter(self, sql: str) -> bool:
        return TENANT_FILTER_RE.search(sql) is not None


def get_db(config: ReadOnlyQueryConfig | None = None) -> ReadOnlyPostgres:
    """Create the safe read-only database helper."""

    return ReadOnlyPostgres(config=config)
