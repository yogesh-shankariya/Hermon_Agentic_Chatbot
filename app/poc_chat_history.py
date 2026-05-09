"""Local SQLite chat history for POC/demo Streamlit runs."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_HISTORY_ROWS_PER_ORG = 5
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / ".hermon_poc_chat_history.sqlite3"
DB_PATH_ENV = "HERMON_POC_CHAT_HISTORY_DB"


def poc_chat_history_db_path() -> Path:
    configured_path = os.getenv(DB_PATH_ENV)
    if configured_path:
        return Path(configured_path).expanduser()
    return DEFAULT_DB_PATH


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or poc_chat_history_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def _json_dumps(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str)


def _json_loads(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _ensure_column(
    connection: sqlite3.Connection,
    *,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    columns = {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )


def ensure_poc_chat_history_table(db_path: Path | None = None) -> None:
    with _connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS poc_chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id TEXT NOT NULL,
                route TEXT NOT NULL,
                selected_skill TEXT NULL,
                user_question TEXT NOT NULL,
                standalone_question TEXT NULL,
                generated_sql TEXT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                elapsed_seconds REAL NULL,
                execution_details_json TEXT NULL,
                timing_json TEXT NULL,
                lead_360_diagnostics_json TEXT NULL
            )
            """
        )
        _ensure_column(
            connection,
            table_name="poc_chat_history",
            column_name="elapsed_seconds",
            column_type="REAL NULL",
        )
        _ensure_column(
            connection,
            table_name="poc_chat_history",
            column_name="execution_details_json",
            column_type="TEXT NULL",
        )
        _ensure_column(
            connection,
            table_name="poc_chat_history",
            column_name="timing_json",
            column_type="TEXT NULL",
        )
        _ensure_column(
            connection,
            table_name="poc_chat_history",
            column_name="lead_360_diagnostics_json",
            column_type="TEXT NULL",
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_poc_chat_history_org_created
            ON poc_chat_history (organization_id, created_at DESC, id DESC)
            """
        )


def fetch_latest_poc_chat_history(
    organization_id: str,
    *,
    db_path: Path | None = None,
    limit: int = MAX_HISTORY_ROWS_PER_ORG,
) -> list[dict[str, Any]]:
    """Fetch latest rows ordered newest first for one organization."""

    ensure_poc_chat_history_table(db_path)
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                organization_id,
                route,
                selected_skill,
                user_question,
                standalone_question,
                generated_sql,
                answer,
                created_at,
                elapsed_seconds,
                execution_details_json,
                timing_json,
                lead_360_diagnostics_json
            FROM poc_chat_history
            WHERE organization_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (organization_id, limit),
        ).fetchall()
    parsed_rows: list[dict[str, Any]] = []
    for row in rows:
        row_dict = dict(row)
        row_dict["execution_details"] = _json_loads(
            row_dict.pop("execution_details_json", None)
        )
        row_dict["timing"] = _json_loads(row_dict.pop("timing_json", None))
        row_dict["lead_360_diagnostics"] = _json_loads(
            row_dict.pop("lead_360_diagnostics_json", None)
        )
        parsed_rows.append(row_dict)
    return parsed_rows


def fetch_router_poc_chat_history(
    organization_id: str,
    *,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Fetch the latest five rows and return them oldest-to-newest for prompts."""

    return list(reversed(fetch_latest_poc_chat_history(organization_id, db_path=db_path)))


def prune_poc_chat_history(organization_id: str, *, db_path: Path | None = None) -> None:
    """Keep only the latest five rows for one organization."""

    ensure_poc_chat_history_table(db_path)
    with _connect(db_path) as connection:
        connection.execute(
            """
            DELETE FROM poc_chat_history
            WHERE organization_id = ?
              AND id NOT IN (
                  SELECT id
                  FROM poc_chat_history
                  WHERE organization_id = ?
                  ORDER BY created_at DESC, id DESC
                  LIMIT ?
              )
            """,
            (organization_id, organization_id, MAX_HISTORY_ROWS_PER_ORG),
        )


def clear_poc_chat_history(organization_id: str, *, db_path: Path | None = None) -> None:
    ensure_poc_chat_history_table(db_path)
    with _connect(db_path) as connection:
        connection.execute(
            "DELETE FROM poc_chat_history WHERE organization_id = ?",
            (organization_id,),
        )


def insert_poc_chat_history(
    *,
    organization_id: str,
    route: str,
    user_question: str,
    answer: str,
    selected_skill: str | None = None,
    standalone_question: str | None = None,
    generated_sql: str | None = None,
    elapsed_seconds: float | None = None,
    execution_details: dict[str, Any] | None = None,
    timing: dict[str, Any] | None = None,
    lead_360_diagnostics: dict[str, Any] | None = None,
    created_at: str | None = None,
    db_path: Path | None = None,
) -> int:
    """Insert one POC history row, then prune older rows for the organization."""

    ensure_poc_chat_history_table(db_path)
    stored_sql = generated_sql if route == "sql_analytics" else None
    stored_skill = selected_skill if route == "sql_analytics" else None
    timestamp = created_at or datetime.now(timezone.utc).isoformat()

    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO poc_chat_history (
                organization_id,
                route,
                selected_skill,
                user_question,
                standalone_question,
                generated_sql,
                answer,
                created_at,
                elapsed_seconds,
                execution_details_json,
                timing_json,
                lead_360_diagnostics_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                organization_id,
                route,
                stored_skill,
                user_question,
                standalone_question,
                stored_sql,
                answer,
                timestamp,
                elapsed_seconds,
                _json_dumps(execution_details),
                _json_dumps(timing),
                _json_dumps(lead_360_diagnostics),
            ),
        )
        row_id = int(cursor.lastrowid)
        connection.execute(
            """
            DELETE FROM poc_chat_history
            WHERE organization_id = ?
              AND id NOT IN (
                  SELECT id
                  FROM poc_chat_history
                  WHERE organization_id = ?
                  ORDER BY created_at DESC, id DESC
                  LIMIT ?
              )
            """,
            (organization_id, organization_id, MAX_HISTORY_ROWS_PER_ORG),
        )
    return row_id
