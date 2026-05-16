"""LangChain tools used by the SQL assistant."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any, Callable

from langchain.tools import tool

from app.config import get_sql_agent_settings
from app.db import QueryValidationError, get_db
from app.utils.skill_loader import SkillRegistryError
from app.utils.skill_loader import load_skill as load_file_skill


SQL_FENCE_RE = re.compile(r"^\s*```(?:sql)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)
DATE_TRUNC_GRANULARITY_RE = re.compile(
    r"\bdate_trunc\(\s*['\"](day|week|month)['\"]",
    re.IGNORECASE,
)
DATE_PARAM_CAST_RE = re.compile(r":(start_date|end_date)::(date|timestamp)\b", re.IGNORECASE)
EMPTY_COUNT_RE = re.compile(r"\bcount\s*\(\s*\)", re.IGNORECASE)
TREND_QUERY_MAX_ROWS = 200


def _rewrite_sql_outside_strings(sql: str, rewrite: Callable[[str], str]) -> str:
    parts: list[str] = []
    start = 0
    index = 0
    in_string = False

    while index < len(sql):
        if sql[index] != "'":
            index += 1
            continue

        if in_string and index + 1 < len(sql) and sql[index + 1] == "'":
            index += 2
            continue

        if in_string:
            parts.append(sql[start : index + 1])
            start = index + 1
        else:
            parts.append(rewrite(sql[start:index]))
            start = index

        in_string = not in_string
        index += 1

    tail = sql[start:]
    parts.append(tail if in_string else rewrite(tail))
    return "".join(parts)


def _normalize_sql_syntax(sql: str) -> str:
    sql = sql.replace("≥", ">=").replace("≤", "<=")
    sql = DATE_PARAM_CAST_RE.sub(
        lambda match: f"CAST(:{match.group(1)} AS {match.group(2).lower()})",
        sql,
    )
    return EMPTY_COUNT_RE.sub("COUNT(*)", sql)


def _clean_sql_input(query: str) -> str:
    """Accept raw SQL or a fenced SQL block from the model."""

    match = SQL_FENCE_RE.match(query)
    if match:
        query = match.group(1)

    return _rewrite_sql_outside_strings(query.strip(), _normalize_sql_syntax)


def _load_params(params_json: str | None) -> dict[str, Any]:
    if not params_json:
        return {}

    try:
        params = json.loads(params_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"params_json must be valid JSON: {exc}") from exc

    if not isinstance(params, dict):
        raise ValueError("params_json must decode to a JSON object.")

    return params


def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def _month_start_months_ago(month_start: date, months: int) -> date:
    month_index = month_start.year * 12 + month_start.month - 1 - months
    return date(month_index // 12, month_index % 12 + 1, 1)


def default_trend_dates(granularity: str, today: date) -> tuple[date | None, date | None]:
    granularity = {
        "day": "daily",
        "week": "weekly",
        "month": "monthly",
    }.get(granularity, granularity)

    if granularity == "daily":
        return today - timedelta(days=9), today + timedelta(days=1)

    if granularity == "weekly":
        week_start = today - timedelta(days=today.weekday())
        return week_start - timedelta(weeks=11), week_start + timedelta(weeks=1)

    if granularity == "monthly":
        current_month_start = today.replace(day=1)
        return _month_start_months_ago(current_month_start, 3), current_month_start

    return None, None


def default_previous_month_dates(today: date) -> tuple[date, date]:
    current_month_start = today.replace(day=1)
    return _month_start_months_ago(current_month_start, 1), current_month_start


def _infer_trend_granularity(sql: str) -> str | None:
    match = DATE_TRUNC_GRANULARITY_RE.search(sql)
    if not match:
        return None

    return match.group(1).lower()


def _max_rows_for_sql(sql: str, default_max_rows: int) -> int:
    if _infer_trend_granularity(sql):
        return max(default_max_rows, TREND_QUERY_MAX_ROWS)

    return default_max_rows


def _apply_default_trend_dates(sql: str, params: dict[str, Any]) -> None:
    if "start_date" in params or "end_date" in params:
        return

    if ":start_date" not in sql or ":end_date" not in sql:
        return

    start_date, end_date = default_trend_dates(_infer_trend_granularity(sql) or "", date.today())
    if start_date is None or end_date is None:
        return

    params["start_date"] = start_date.isoformat()
    params["end_date"] = end_date.isoformat()


def _apply_default_date_window(sql: str, params: dict[str, Any]) -> None:
    if "start_date" in params or "end_date" in params:
        return

    if ":start_date" not in sql or ":end_date" not in sql:
        return

    trend_granularity = _infer_trend_granularity(sql)
    if trend_granularity:
        start_date, end_date = default_trend_dates(trend_granularity, date.today())
    else:
        start_date, end_date = default_previous_month_dates(date.today())

    if start_date is None or end_date is None:
        return

    params["start_date"] = start_date.isoformat()
    params["end_date"] = end_date.isoformat()


@tool
def load_skill(skill_name: str) -> str:
    """Load detailed instructions for an enabled SQL skill.

    Use this before writing SQL so domain-specific rules stay in skill files
    instead of the generic SQL agent prompt.
    """

    settings = get_sql_agent_settings()
    try:
        skill = load_file_skill(
            skill_name,
            allowed_skill_names=set(settings.enabled_skills),
        )
    except SkillRegistryError as exc:
        return f"Could not load skill: {exc}"

    return f"Loaded skill: {skill.name}\n\n{skill.content}"


@tool
def validate_sql(query: str) -> str:
    """Validate read-only SQL against Hermon's safety rules without executing it."""

    sql = _clean_sql_input(query)
    try:
        validated_sql = get_db().validate_sql(sql)
    except QueryValidationError as exc:
        return _json_response({"ok": False, "error": str(exc)})

    return _json_response({"ok": True, "sql": validated_sql})


@tool
def run_readonly_sql(query: str, params_json: str = "{}") -> str:
    """Execute safe read-only SQL against Postgres and return JSON rows.

    The SQL must use `:org_id` for tenant scope. This tool injects
    HERMON_DEFAULT_CLERK_ORG_ID as `org_id` and ignores any model-supplied
    org_id in params_json. Daily, weekly, or monthly trend queries that omit
    start_date/end_date receive application defaults when granularity can be
    inferred from DATE_TRUNC. Non-trend queries that use both :start_date and
    :end_date but omit params receive the previous completed calendar month as
    a safe fallback. Use params_json for other named parameters, for example:
    {"start_date": "2026-04-01", "end_date": "2026-05-01"}.
    """

    settings = get_sql_agent_settings()
    if not settings.default_org_id:
        return _json_response(
            {
                "ok": False,
                "error": "Missing HERMON_DEFAULT_CLERK_ORG_ID in environment or .env.",
            }
        )

    sql = _clean_sql_input(query)
    params: dict[str, Any] = {}
    try:
        max_rows = _max_rows_for_sql(sql, settings.max_tool_rows)
        params = _load_params(params_json)
        # The agent must write tenant-scoped SQL, but this tool owns injecting
        # the actual tenant value so the model never sees or hardcodes it.
        params["org_id"] = settings.default_org_id
        params.setdefault("limit", max_rows)
        _apply_default_date_window(sql, params)
        rows = get_db().query_records(sql, params=params, max_rows=max_rows)
    except (QueryValidationError, ValueError) as exc:
        return _json_response(
            {"ok": False, "error": str(exc), "effective_params": params, "sql": sql}
        )
    except Exception as exc:  # noqa: BLE001 - return DB/runtime errors to the agent for repair.
        return _json_response(
            {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "effective_params": params,
                "sql": sql,
            }
        )

    return _json_response(
        {
            "ok": True,
            "effective_params": params,
            "row_count": len(rows),
            "rows": rows,
            "sql": sql,
        }
    )


# run_readonly_sql validates before executing, so the agent does not need a
# separate validate_sql round trip during normal Q&A.
SQL_AGENT_TOOLS = [load_skill, run_readonly_sql]
