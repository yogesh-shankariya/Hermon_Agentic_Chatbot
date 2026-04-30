"""LangChain tools used by the SQL assistant."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain.tools import tool

from app.config import get_sql_agent_settings
from app.db import QueryValidationError, get_db
from app.utils.skill_loader import SkillRegistryError
from app.utils.skill_loader import load_skill as load_file_skill


SQL_FENCE_RE = re.compile(r"^\s*```(?:sql)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)


def _clean_sql_input(query: str) -> str:
    """Accept raw SQL or a fenced SQL block from the model."""

    match = SQL_FENCE_RE.match(query)
    if match:
        return match.group(1).strip()
    return query.strip()


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
    HERMON_DEFAULT_CLERK_ORG_ID as `org_id` when it is not provided in
    params_json. Use params_json for other named parameters, for example:
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
    try:
        params = _load_params(params_json)
        # The agent must write tenant-scoped SQL, but this tool owns injecting
        # the actual tenant value so the model never sees or hardcodes it.
        params.setdefault("org_id", settings.default_org_id)
        params.setdefault("limit", settings.max_tool_rows)
        rows = get_db().query_records(sql, params=params, max_rows=settings.max_tool_rows)
    except (QueryValidationError, ValueError) as exc:
        return _json_response({"ok": False, "error": str(exc)})
    except Exception as exc:  # noqa: BLE001 - return DB/runtime errors to the agent for repair.
        return _json_response({"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    return _json_response(
        {
            "ok": True,
            "row_count": len(rows),
            "rows": rows,
        }
    )


SQL_AGENT_TOOLS = [load_skill, validate_sql, run_readonly_sql]
