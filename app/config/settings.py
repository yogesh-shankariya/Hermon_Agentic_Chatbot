"""YAML-backed runtime settings for Hermon agents and database access."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_DIR.parent
CONFIG_PATH = APP_DIR / "config" / "config.yaml"

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class SqlAgentSettings:
    """Runtime settings for the generic SQL agent."""

    model: str
    reasoning: dict[str, Any] | None
    prompt_cache_key: str | None
    prompt_cache_retention: str | None
    service_tier: str | None
    default_org_id: str | None
    max_tool_rows: int
    enabled_skills: tuple[str, ...]
    prompt_version: str


@dataclass(frozen=True)
class SilverTruthSettings:
    """Runtime settings for silver-truth batch generation."""

    service_tier: str | None


@dataclass(frozen=True)
class ContextExtractionSettings:
    """Runtime settings for diagnostic context extraction."""

    model: str
    reasoning: dict[str, Any] | None
    service_tier: str | None
    prompt_cache_key: str | None
    prompt_cache_retention: str | None
    max_retries: int
    prompt_version: str


@dataclass(frozen=True)
class DatabaseSettings:
    """Runtime settings for read-only database access."""

    database_url: str | None
    max_rows: int
    statement_timeout_ms: int
    require_org_scope: bool


@lru_cache(maxsize=1)
def load_app_config() -> dict[str, Any]:
    """Load application config from YAML."""

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        loaded = yaml.safe_load(config_file) or {}
    if not isinstance(loaded, dict):
        raise RuntimeError(f"Config file must contain a YAML object: {CONFIG_PATH}")
    return loaded


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _enabled_sql_skills(agent_config: dict[str, Any]) -> tuple[str, ...]:
    configured_skills = agent_config.get("enabled_skills")
    if configured_skills is None or configured_skills == "all":
        from app.utils.skill_loader import load_skill_metadata

        return tuple(skill.name for skill in load_skill_metadata())

    if not isinstance(configured_skills, list):
        raise RuntimeError("llm.sql_agent.enabled_skills must be 'all' or a YAML list.")

    return tuple(str(skill).strip() for skill in configured_skills if str(skill).strip())


def get_sql_agent_settings() -> SqlAgentSettings:
    """Return SQL agent settings from YAML with env overrides."""

    config = load_app_config()
    llm_config = config.get("llm", {})
    agent_config = llm_config.get("sql_agent", {})
    prompts_config = config.get("prompts", {})
    prompt_config = prompts_config.get("sql_agent", {})
    database_config = config.get("database", {})

    default_org_id_env = database_config.get("default_org_id_env", "HERMON_DEFAULT_CLERK_ORG_ID")
    model = os.getenv("OPENAI_MODEL") or agent_config.get("Model") or "gpt-5.4"
    reasoning = agent_config.get("reasoning")
    if reasoning is not None and not isinstance(reasoning, dict):
        raise RuntimeError("llm.sql_agent.reasoning must be a YAML object when provided.")
    prompt_cache_key = agent_config.get("prompt_cache_key")
    prompt_cache_retention = agent_config.get("prompt_cache_retention")
    service_tier = agent_config.get("service_tier")
    max_tool_rows = _int_env(
        "HERMON_AGENT_MAX_TOOL_ROWS",
        int(agent_config.get("max_tool_rows", 20)),
    )

    return SqlAgentSettings(
        model=model,
        reasoning=reasoning,
        prompt_cache_key=str(prompt_cache_key) if prompt_cache_key else None,
        prompt_cache_retention=str(prompt_cache_retention) if prompt_cache_retention else None,
        service_tier=str(service_tier) if service_tier else None,
        default_org_id=os.getenv(default_org_id_env),
        max_tool_rows=max_tool_rows,
        enabled_skills=_enabled_sql_skills(agent_config),
        prompt_version=str(prompt_config.get("version", "1_0_0")),
    )


def get_silver_truth_settings() -> SilverTruthSettings:
    """Return settings for silver-truth test generation."""

    config = load_app_config()
    testing_config = config.get("testing", {})
    silver_truth_config = testing_config.get("silver_truth", {})
    service_tier = silver_truth_config.get("service_tier")

    return SilverTruthSettings(
        service_tier=str(service_tier) if service_tier else None,
    )


def get_context_extraction_settings() -> ContextExtractionSettings:
    """Return settings for diagnostic context extraction."""

    config = load_app_config()
    llm_config = config.get("llm", {})
    extraction_config = llm_config.get("context_extraction", {})
    sql_agent_config = llm_config.get("sql_agent", {})
    prompts_config = config.get("prompts", {})
    prompt_config = prompts_config.get("extract_context", {})

    model = (
        os.getenv("OPENAI_MODEL")
        or extraction_config.get("Model")
        or sql_agent_config.get("Model")
        or "gpt-5.4"
    )
    reasoning = extraction_config.get("reasoning")
    if reasoning is not None and not isinstance(reasoning, dict):
        raise RuntimeError("llm.context_extraction.reasoning must be a YAML object when provided.")

    max_retries_default = int(extraction_config.get("max_retries", llm_config.get("max_retries", 2)))
    max_retries = _int_env("HERMON_CONTEXT_EXTRACTION_MAX_RETRIES", max_retries_default)

    return ContextExtractionSettings(
        model=str(model),
        reasoning=reasoning,
        service_tier=(
            str(extraction_config["service_tier"])
            if extraction_config.get("service_tier")
            else None
        ),
        prompt_cache_key=(
            str(extraction_config["prompt_cache_key"])
            if extraction_config.get("prompt_cache_key")
            else None
        ),
        prompt_cache_retention=(
            str(extraction_config["prompt_cache_retention"])
            if extraction_config.get("prompt_cache_retention")
            else None
        ),
        max_retries=max_retries,
        prompt_version=str(prompt_config.get("version", "1_0_0")),
    )


def get_database_settings() -> DatabaseSettings:
    """Return database settings from YAML with env overrides."""

    config = load_app_config()
    database_config = config.get("database", {})
    url_env = database_config.get("url_env", "HERMON_DATABASE_URL")
    fallback_url_env = database_config.get("fallback_url_env", "DATABASE_URL")
    max_rows_env = database_config.get("max_rows_env", "HERMON_SQL_MAX_ROWS")
    timeout_env = database_config.get("timeout_ms_env", "HERMON_SQL_TIMEOUT_MS")

    return DatabaseSettings(
        database_url=os.getenv(url_env) or os.getenv(fallback_url_env),
        max_rows=_int_env(max_rows_env, int(database_config.get("max_rows", 500))),
        statement_timeout_ms=_int_env(timeout_env, int(database_config.get("timeout_ms", 10000))),
        require_org_scope=bool(database_config.get("require_org_scope", True)),
    )


def ensure_openai_key() -> None:
    """Fail fast if the OpenAI key is not available to LangChain."""

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Missing OPENAI_API_KEY in environment or .env.")
