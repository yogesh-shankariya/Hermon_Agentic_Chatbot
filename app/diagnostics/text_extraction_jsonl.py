"""Generate validated diagnostic text extraction JSONL.

This module collects approved text candidates for one organization, cleans the
text, calls the configured LLM with the extraction prompt/schema, validates the
response, and writes one safe JSONL envelope per source text item.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "app" / "prompts" / "extract_context" / "1_0_0.yaml"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "app" / "schema" / "context_extraction.py"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "artifacts" / "diagnostic_text_extractions.jsonl"
DEFAULT_PREVIEW_MD_PATH = PROJECT_ROOT / "artifacts" / "diagnostic_text_extractions_preview.md"
ALLOWED_STATUSES = {
    "success",
    "skipped_empty",
    "skipped_too_short",
    "skipped_duplicate",
    "skipped_no_signal",
    "validation_failed",
    "llm_failed",
}
DEFAULT_MIN_SIGNAL_CHARS = 12
DEFAULT_MAX_RETRIES = 2

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((?:https?://|mailto:)[^)]+\)", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(?!\w)"
)
PROVIDER_ID_RE = re.compile(
    r"\b(?:"
    r"[A-Za-z][A-Za-z0-9_-]*(?:[_-]?(?:id|reference|ref))"
    r"|(?:id|reference|ref)[_-]?"
    r")\s*[:=#-]?\s*[A-Za-z0-9_-]{8,}\b",
    re.IGNORECASE,
)
LONG_TOKEN_RE = re.compile(r"\b[A-Za-z0-9_-]{32,}\b")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class TextCandidate:
    """One approved source text item before/after cleaning."""

    clerk_org_id: str
    lead_id: str
    source_table: str
    source_record_id: str
    source_text_type: str
    source_event_at: str | None
    source_text: str | None


@dataclass(frozen=True)
class SourceSpec:
    """SQL source specification for one candidate text field."""

    source_table: str
    source_text_type: str
    required_columns: dict[str, set[str]]
    sql: str


@dataclass(frozen=True)
class ExtractionResult:
    """Processed row plus cleaned input retained only for preview markdown."""

    candidate: TextCandidate
    cleaned_text: str
    row: dict[str, Any]


class ExtractionValidationError(ValueError):
    """Raised when a model response cannot be parsed or validated."""


def _iso_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


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


def _database_url_from_env() -> str | None:
    database_url = _env_value("HERMON_DATABASE_URL") or _env_value("DATABASE_URL")
    if database_url and database_url.startswith("postgresql+psycopg:"):
        return database_url.replace("postgresql+psycopg:", "postgresql:", 1)
    return database_url


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    return value


def _as_nonempty_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    else:
        text = str(value)
    text = text.strip()
    if text in {"", "null", "[]", "{}"}:
        return None
    return text


def clean_text(text: str | None) -> str:
    """Remove identifiers/contact links and normalize whitespace."""

    if not text:
        return ""
    cleaned = MARKDOWN_LINK_RE.sub(r"\1", str(text))
    cleaned = URL_RE.sub(" ", cleaned)
    cleaned = EMAIL_RE.sub(" ", cleaned)
    cleaned = PHONE_RE.sub(" ", cleaned)
    cleaned = PROVIDER_ID_RE.sub(" ", cleaned)
    cleaned = LONG_TOKEN_RE.sub(" ", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    return cleaned.strip()


def hash_text(cleaned_text: str) -> str:
    """Return a stable SHA-256 hash for cleaned source text."""

    return hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()


def dedupe_key_for_row(row: dict[str, Any]) -> str:
    """Build the dedupe key required by the extraction instructions."""

    parts = [
        row.get("clerk_org_id"),
        row.get("lead_id"),
        row.get("source_table"),
        row.get("source_record_id"),
        row.get("source_text_type"),
        row.get("source_text_hash"),
    ]
    return "|".join("" if part is None else str(part) for part in parts)


def load_existing_hashes(output_path: str | Path) -> set[str]:
    """Load existing JSONL dedupe keys from a prior output file."""

    path = Path(output_path)
    if not path.exists():
        return set()

    hashes: set[str] = set()
    with path.open("r", encoding="utf-8") as output_file:
        for line in output_file:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            hashes.add(dedupe_key_for_row(row))
    return hashes


def _build_base_row(
    candidate: TextCandidate,
    *,
    cleaned_text: str,
    prompt_path: str | Path,
    schema_path: str | Path,
    extraction_model: str,
    extracted_at: str,
) -> dict[str, Any]:
    return {
        "clerk_org_id": candidate.clerk_org_id,
        "lead_id": candidate.lead_id,
        "source_table": candidate.source_table,
        "source_record_id": candidate.source_record_id,
        "source_text_type": candidate.source_text_type,
        "source_event_at": candidate.source_event_at,
        "source_text_hash": hash_text(cleaned_text),
        "source_text_length": len(cleaned_text),
        "extraction_status": "success",
        "llm_output_json": {"insights": []},
        "extraction_error": None,
        "extraction_model": extraction_model,
        "prompt_path": str(prompt_path),
        "schema_path": str(schema_path),
        "extracted_at": extracted_at,
    }


def _finish_row(
    row: dict[str, Any],
    *,
    status: str,
    llm_output_json: dict[str, Any] | None = None,
    extraction_error: str | None = None,
) -> dict[str, Any]:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Unsupported extraction_status: {status}")
    row["extraction_status"] = status
    row["llm_output_json"] = llm_output_json or {"insights": []}
    row["extraction_error"] = _safe_error(extraction_error)
    return row


def _safe_error(error: str | None) -> str | None:
    if not error:
        return None
    return clean_text(error)[:300]


def write_jsonl_row(output_path: str | Path, row: dict[str, Any], *, append: bool = True) -> None:
    """Append or write one JSONL envelope row."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as output_file:
        output_file.write(json.dumps(_json_safe(row), ensure_ascii=True, sort_keys=True))
        output_file.write("\n")


def _load_prompt_system(prompt_path: str | Path) -> str:
    path = Path(prompt_path)
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        system = str(loaded.get("System", "")).strip()
        if system:
            return system
    except ModuleNotFoundError:
        pass

    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("System:"):
            body: list[str] = []
            for body_line in lines[index + 1 :]:
                if body_line and not body_line.startswith(" "):
                    break
                body.append(body_line[2:] if body_line.startswith("  ") else body_line)
            system = "\n".join(body).strip()
            if system:
                return system
    raise ValueError(f"Prompt file is missing a non-empty System block: {path}")


def _render_prompt(prompt_path: str | Path, candidate: TextCandidate, cleaned_text: str) -> str:
    prompt = _load_prompt_system(prompt_path)
    replacements = {
        "{{source_table}}": candidate.source_table,
        "{{source_text_type}}": candidate.source_text_type,
        "{{cleaned_text}}": cleaned_text,
    }
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)
    return prompt


def load_schema_class(schema_path: str | Path):
    """Import the configured Pydantic response schema class."""

    path = Path(schema_path)
    spec = importlib.util.spec_from_file_location("context_extraction_schema_runtime", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import schema module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.DiagnosticTextInsightResponse
    except AttributeError as exc:
        raise ImportError(f"Schema is missing DiagnosticTextInsightResponse: {path}") from exc


def _extract_message_content(message: Any) -> Any:
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        return message.get("content", message)
    return getattr(message, "content", message)


def _parse_json_response(raw_output: Any) -> Any:
    content = _extract_message_content(raw_output)
    if isinstance(content, (dict, list)):
        return content
    if hasattr(content, "model_dump") or hasattr(content, "dict"):
        return content
    text = str(content).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ExtractionValidationError("LLM returned invalid JSON.") from exc


def validate_llm_output(raw_output: Any, schema_class: Any) -> dict[str, Any]:
    """Parse and validate raw LLM output using the configured schema."""

    parsed = _parse_json_response(raw_output)
    try:
        if hasattr(schema_class, "model_validate"):
            validated = schema_class.model_validate(parsed)
        elif hasattr(schema_class, "parse_obj"):
            validated = schema_class.parse_obj(parsed)
        else:
            validated = schema_class(**parsed)
    except Exception as exc:  # noqa: BLE001 - schema libraries raise varied errors.
        raise ExtractionValidationError("LLM output failed schema validation.") from exc

    if hasattr(validated, "model_dump"):
        return validated.model_dump(mode="json")
    if hasattr(validated, "dict"):
        return validated.dict()
    if isinstance(validated, dict):
        return validated
    raise ExtractionValidationError("Validated LLM output is not JSON serializable.")


def _context_extraction_settings() -> Any | None:
    try:
        from app.config import get_context_extraction_settings

        return get_context_extraction_settings()
    except Exception:
        return None


def _configured_model_name() -> str:
    if _env_value("OPENAI_MODEL"):
        return str(_env_value("OPENAI_MODEL"))
    settings = _context_extraction_settings()
    if settings is not None:
        return str(settings.model)
    return "gpt-5.4"


def _llm_model_kwargs(timeout_seconds: float | None) -> dict[str, Any]:
    settings = _context_extraction_settings()
    kwargs: dict[str, Any] = {}
    if settings is not None:
        if settings.reasoning:
            kwargs["reasoning"] = settings.reasoning
        if settings.service_tier:
            kwargs["service_tier"] = settings.service_tier
        openai_request_kwargs: dict[str, Any] = {}
        if settings.prompt_cache_key:
            openai_request_kwargs["prompt_cache_key"] = settings.prompt_cache_key
        if settings.prompt_cache_retention:
            openai_request_kwargs["prompt_cache_retention"] = settings.prompt_cache_retention
        if openai_request_kwargs:
            kwargs["model_kwargs"] = openai_request_kwargs
    if timeout_seconds is not None:
        kwargs["timeout"] = timeout_seconds
    return kwargs


def _configured_max_retries() -> int:
    settings = _context_extraction_settings()
    if settings is not None:
        return int(settings.max_retries)
    return DEFAULT_MAX_RETRIES


def call_llm_for_candidate(
    candidate: TextCandidate,
    *,
    cleaned_text: str,
    prompt_path: str | Path,
    schema_class: Any,
    model_name: str | None = None,
    timeout_seconds: float | None = 60,
) -> Any:
    """Call the configured OpenAI model for one cleaned candidate."""

    openai_key = _env_value("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment or .env.")
    os.environ.setdefault("OPENAI_API_KEY", openai_key)

    try:
        from langchain.chat_models import init_chat_model
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing LangChain dependencies. Run `pip install -r requirements.txt`.") from exc

    prompt = _render_prompt(prompt_path, candidate, cleaned_text)
    kwargs = _llm_model_kwargs(timeout_seconds)
    model = init_chat_model(model_name or _configured_model_name(), **kwargs)
    if hasattr(model, "with_structured_output"):
        return model.with_structured_output(schema_class).invoke(prompt)
    return model.invoke([{"role": "system", "content": prompt}])


def _source_specs() -> list[SourceSpec]:
    return [
        SourceSpec(
            "fathom_call_records",
            "fathom_summary",
            {
                "fathom_call_records": {"id", "appointment_id", "clerk_org_id", "summary"},
                "appointments": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT f.clerk_org_id, a.lead_id, f.id AS source_record_id,
                   f.call_started_at AS source_event_at, f.summary AS source_text
            FROM fathom_call_records f
            JOIN appointments a
              ON a.id = f.appointment_id
             AND a.clerk_org_id = f.clerk_org_id
            WHERE f.clerk_org_id = :org_id
              AND NULLIF(BTRIM(f.summary), '') IS NOT NULL
            ORDER BY COALESCE(f.call_started_at, f.created_at) DESC, f.id DESC
            """,
        ),
        SourceSpec(
            "fathom_call_records",
            "fathom_key_points",
            {
                "fathom_call_records": {"id", "appointment_id", "clerk_org_id", "key_points"},
                "appointments": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT f.clerk_org_id, a.lead_id, f.id AS source_record_id,
                   f.call_started_at AS source_event_at, f.key_points AS source_text
            FROM fathom_call_records f
            JOIN appointments a
              ON a.id = f.appointment_id
             AND a.clerk_org_id = f.clerk_org_id
            WHERE f.clerk_org_id = :org_id
              AND f.key_points IS NOT NULL
            ORDER BY COALESCE(f.call_started_at, f.created_at) DESC, f.id DESC
            """,
        ),
        SourceSpec(
            "fathom_call_records",
            "fathom_action_items",
            {
                "fathom_call_records": {"id", "appointment_id", "clerk_org_id", "action_items"},
                "appointments": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT f.clerk_org_id, a.lead_id, f.id AS source_record_id,
                   f.call_started_at AS source_event_at, f.action_items AS source_text
            FROM fathom_call_records f
            JOIN appointments a
              ON a.id = f.appointment_id
             AND a.clerk_org_id = f.clerk_org_id
            WHERE f.clerk_org_id = :org_id
              AND f.action_items IS NOT NULL
            ORDER BY COALESCE(f.call_started_at, f.created_at) DESC, f.id DESC
            """,
        ),
        SourceSpec(
            "fathom_call_records",
            "fathom_objections",
            {
                "fathom_call_records": {"id", "appointment_id", "clerk_org_id", "objections"},
                "appointments": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT f.clerk_org_id, a.lead_id, f.id AS source_record_id,
                   f.call_started_at AS source_event_at, f.objections AS source_text
            FROM fathom_call_records f
            JOIN appointments a
              ON a.id = f.appointment_id
             AND a.clerk_org_id = f.clerk_org_id
            WHERE f.clerk_org_id = :org_id
              AND f.objections IS NOT NULL
            ORDER BY COALESCE(f.call_started_at, f.created_at) DESC, f.id DESC
            """,
        ),
        SourceSpec(
            "fathom_call_records",
            "fathom_ai_rationale",
            {
                "fathom_call_records": {"id", "appointment_id", "clerk_org_id", "ai_rationale"},
                "appointments": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT f.clerk_org_id, a.lead_id, f.id AS source_record_id,
                   f.call_started_at AS source_event_at, f.ai_rationale AS source_text
            FROM fathom_call_records f
            JOIN appointments a
              ON a.id = f.appointment_id
             AND a.clerk_org_id = f.clerk_org_id
            WHERE f.clerk_org_id = :org_id
              AND NULLIF(BTRIM(f.ai_rationale), '') IS NOT NULL
            ORDER BY COALESCE(f.call_started_at, f.created_at) DESC, f.id DESC
            """,
        ),
        SourceSpec(
            "lead_notes",
            "lead_note",
            {"lead_notes": {"id", "lead_id", "clerk_org_id", "note", "created_at"}},
            """
            SELECT n.clerk_org_id, n.lead_id, n.id AS source_record_id,
                   n.created_at AS source_event_at, n.note AS source_text
            FROM lead_notes n
            WHERE n.clerk_org_id = :org_id
              AND COALESCE(n.is_deleted, false) = false
              AND NULLIF(BTRIM(n.note), '') IS NOT NULL
            ORDER BY n.created_at DESC, n.id DESC
            """,
        ),
        SourceSpec(
            "appointments",
            "appointment_note",
            {"appointments": {"id", "lead_id", "clerk_org_id", "notes", "created_at"}},
            """
            SELECT a.clerk_org_id, a.lead_id, a.id AS source_record_id,
                   COALESCE(a.schedule_time, a.created_at) AS source_event_at,
                   a.notes AS source_text
            FROM appointments a
            WHERE a.clerk_org_id = :org_id
              AND COALESCE(a.is_deleted, false) = false
              AND NULLIF(BTRIM(a.notes), '') IS NOT NULL
            ORDER BY COALESCE(a.schedule_time, a.created_at) DESC, a.id DESC
            """,
        ),
        SourceSpec(
            "contracts",
            "contract_note",
            {"contracts": {"id", "lead_id", "clerk_org_id", "notes", "created_at"}},
            """
            SELECT c.clerk_org_id, c.lead_id, c.id AS source_record_id,
                   c.created_at AS source_event_at, c.notes AS source_text
            FROM contracts c
            WHERE c.clerk_org_id = :org_id
              AND COALESCE(c.is_deleted, false) = false
              AND NULLIF(BTRIM(c.notes), '') IS NOT NULL
            ORDER BY c.created_at DESC, c.id DESC
            """,
        ),
        SourceSpec(
            "contracts",
            "contract_voided_reason",
            {"contracts": {"id", "lead_id", "clerk_org_id", "voided_reason", "created_at"}},
            """
            SELECT c.clerk_org_id, c.lead_id, c.id AS source_record_id,
                   COALESCE(c.voided_at, c.updated_at, c.created_at) AS source_event_at,
                   c.voided_reason AS source_text
            FROM contracts c
            WHERE c.clerk_org_id = :org_id
              AND COALESCE(c.is_deleted, false) = false
              AND NULLIF(BTRIM(c.voided_reason), '') IS NOT NULL
            ORDER BY COALESCE(c.voided_at, c.updated_at, c.created_at) DESC, c.id DESC
            """,
        ),
        SourceSpec(
            "payments",
            "payment_note",
            {"payments": {"id", "lead_id", "clerk_org_id", "note", "created_at"}},
            """
            SELECT p.clerk_org_id, p.lead_id, p.id AS source_record_id,
                   COALESCE(p.paid_at, p.due_date, p.created_at) AS source_event_at,
                   p.note AS source_text
            FROM payments p
            WHERE p.clerk_org_id = :org_id
              AND COALESCE(p.is_deleted, false) = false
              AND NULLIF(BTRIM(p.note), '') IS NOT NULL
            ORDER BY COALESCE(p.paid_at, p.due_date, p.created_at) DESC, p.id DESC
            """,
        ),
        SourceSpec(
            "payments",
            "payment_failure_reason",
            {"payments": {"id", "lead_id", "clerk_org_id", "failure_reason", "created_at"}},
            """
            SELECT p.clerk_org_id, p.lead_id, p.id AS source_record_id,
                   COALESCE(p.updated_at, p.created_at) AS source_event_at,
                   p.failure_reason AS source_text
            FROM payments p
            WHERE p.clerk_org_id = :org_id
              AND COALESCE(p.is_deleted, false) = false
              AND NULLIF(BTRIM(p.failure_reason), '') IS NOT NULL
            ORDER BY COALESCE(p.updated_at, p.created_at) DESC, p.id DESC
            """,
        ),
        SourceSpec(
            "refunds",
            "refund_reason",
            {
                "refunds": {"id", "payment_id", "clerk_org_id", "reason", "created_at"},
                "payments": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT r.clerk_org_id, p.lead_id, r.id AS source_record_id,
                   COALESCE(r.refunded_at, r.created_at) AS source_event_at,
                   r.reason AS source_text
            FROM refunds r
            JOIN payments p
              ON p.id = r.payment_id
             AND p.clerk_org_id = r.clerk_org_id
            WHERE r.clerk_org_id = :org_id
              AND COALESCE(p.is_deleted, false) = false
              AND NULLIF(BTRIM(r.reason), '') IS NOT NULL
            ORDER BY COALESCE(r.refunded_at, r.created_at) DESC, r.id DESC
            """,
        ),
        SourceSpec(
            "refunds",
            "refund_failure_reason",
            {
                "refunds": {"id", "payment_id", "clerk_org_id", "failure_reason", "created_at"},
                "payments": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT r.clerk_org_id, p.lead_id, r.id AS source_record_id,
                   COALESCE(r.updated_at, r.created_at) AS source_event_at,
                   r.failure_reason AS source_text
            FROM refunds r
            JOIN payments p
              ON p.id = r.payment_id
             AND p.clerk_org_id = r.clerk_org_id
            WHERE r.clerk_org_id = :org_id
              AND COALESCE(p.is_deleted, false) = false
              AND NULLIF(BTRIM(r.failure_reason), '') IS NOT NULL
            ORDER BY COALESCE(r.updated_at, r.created_at) DESC, r.id DESC
            """,
        ),
        SourceSpec(
            "contract_subscriptions",
            "subscription_cancellation_reason",
            {
                "contract_subscriptions": {
                    "id",
                    "contract_id",
                    "cancellation_reason",
                    "created_at",
                },
                "contracts": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT c.clerk_org_id, c.lead_id, s.id AS source_record_id,
                   COALESCE(s.cancelled_at, s.updated_at, s.created_at) AS source_event_at,
                   s.cancellation_reason AS source_text
            FROM contract_subscriptions s
            JOIN contracts c
              ON c.id = s.contract_id
            WHERE c.clerk_org_id = :org_id
              AND COALESCE(c.is_deleted, false) = false
              AND COALESCE(s.is_deleted, false) = false
              AND NULLIF(BTRIM(s.cancellation_reason), '') IS NOT NULL
            ORDER BY COALESCE(s.cancelled_at, s.updated_at, s.created_at) DESC, s.id DESC
            """,
        ),
        SourceSpec(
            "opt_in_question_answers",
            "opt_in_question_answer",
            {
                "opt_in_question_answers": {"id", "opt_in_id", "question", "answer", "created_at"},
                "opt_ins": {"id", "lead_id", "clerk_org_id"},
            },
            """
            SELECT o.clerk_org_id, o.lead_id, q.id AS source_record_id,
                   COALESCE(q.created_at, o.created_at) AS source_event_at,
                   CONCAT('Question: ', q.question, E'\\nAnswer: ', q.answer) AS source_text
            FROM opt_in_question_answers q
            JOIN opt_ins o
              ON o.id = q.opt_in_id
            WHERE o.clerk_org_id = :org_id
              AND (
                NULLIF(BTRIM(q.question), '') IS NOT NULL
                OR NULLIF(BTRIM(q.answer), '') IS NOT NULL
              )
            ORDER BY COALESCE(q.created_at, o.created_at) DESC, q.id DESC
            """,
        ),
    ]


def _existing_columns(connection: Any, table_names: Iterable[str]) -> dict[str, set[str]]:
    from sqlalchemy import text

    result = connection.execute(
        text(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = ANY(:table_names)
            """
        ),
        {"table_names": list(sorted(set(table_names)))},
    )
    columns: dict[str, set[str]] = {}
    for row in result.mappings():
        columns.setdefault(str(row["table_name"]), set()).add(str(row["column_name"]))
    return columns


def _spec_is_available(spec: SourceSpec, columns: dict[str, set[str]]) -> bool:
    for table_name, required in spec.required_columns.items():
        if not required.issubset(columns.get(table_name, set())):
            return False
    return True


def _rows_to_candidates(
    rows: Iterable[dict[str, Any]],
    *,
    source_table: str,
    source_text_type: str,
) -> list[TextCandidate]:
    candidates: list[TextCandidate] = []
    for row in rows:
        source_text = _as_nonempty_text(row.get("source_text"))
        candidates.append(
            TextCandidate(
                clerk_org_id=str(row["clerk_org_id"]),
                lead_id=str(row["lead_id"]),
                source_table=source_table,
                source_record_id=str(row["source_record_id"]),
                source_text_type=source_text_type,
                source_event_at=(
                    _json_safe(row.get("source_event_at")) if row.get("source_event_at") else None
                ),
                source_text=source_text,
            )
        )
    return candidates


def collect_text_candidates(
    org_id: str,
    *,
    limit: int | None = None,
    source_table: str | None = None,
) -> list[TextCandidate]:
    """Collect tenant-scoped candidates from approved source columns."""

    if not org_id:
        raise ValueError("org_id is required.")

    try:
        from sqlalchemy import create_engine, text
    except ModuleNotFoundError as exc:
        return _collect_text_candidates_with_psql(org_id, limit=limit, source_table=source_table)

    try:
        from app.config import get_database_settings
    except ModuleNotFoundError:
        return _collect_text_candidates_with_psql(org_id, limit=limit, source_table=source_table)

    settings = get_database_settings()
    if not settings.database_url:
        raise RuntimeError("Missing HERMON_DATABASE_URL or DATABASE_URL in environment or .env.")

    specs = [
        spec
        for spec in _source_specs()
        if source_table is None or spec.source_table == source_table
    ]
    if source_table and not specs:
        valid = ", ".join(sorted({spec.source_table for spec in _source_specs()}))
        raise ValueError(f"Unsupported source_table {source_table!r}. Expected one of: {valid}")

    all_tables = {table for spec in specs for table in spec.required_columns}
    engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    collected: list[TextCandidate] = []
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            connection.exec_driver_sql(
                f"SET LOCAL statement_timeout = {int(settings.statement_timeout_ms)}"
            )
            columns = _existing_columns(connection, all_tables)
            for spec in specs:
                if limit is not None and len(collected) >= limit:
                    break
                if not _spec_is_available(spec, columns):
                    continue
                remaining = None if limit is None else max(limit - len(collected), 0)
                query_limit = settings.max_rows if remaining is None else max(remaining, 0)
                rows = connection.execute(
                    text(f"SELECT * FROM ({spec.sql}) source_rows LIMIT :limit"),
                    {"org_id": org_id, "limit": query_limit},
                )
                collected.extend(
                    _rows_to_candidates(
                        rows.mappings(),
                        source_table=spec.source_table,
                        source_text_type=spec.source_text_type,
                    )
                )
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
    return collected[:limit] if limit is not None else collected


def _collect_text_candidates_with_psql(
    org_id: str,
    *,
    limit: int | None = None,
    source_table: str | None = None,
) -> list[TextCandidate]:
    """Collect candidates via the psql CLI when Python DB dependencies are absent."""

    database_url = _database_url_from_env()
    if not database_url:
        raise RuntimeError("Missing HERMON_DATABASE_URL or DATABASE_URL in environment or .env.")
    if shutil.which("psql") is None:
        raise RuntimeError("Missing SQLAlchemy dependencies and `psql` is not available.")

    specs = [
        spec
        for spec in _source_specs()
        if source_table is None or spec.source_table == source_table
    ]
    if source_table and not specs:
        valid = ", ".join(sorted({spec.source_table for spec in _source_specs()}))
        raise ValueError(f"Unsupported source_table {source_table!r}. Expected one of: {valid}")

    collected: list[TextCandidate] = []
    for spec in specs:
        if limit is not None and len(collected) >= limit:
            break
        remaining = 500 if limit is None else max(limit - len(collected), 0)
        rows = _run_psql_source_query(
            database_url,
            spec.sql,
            org_id=org_id,
            limit=remaining,
        )
        collected.extend(
            _rows_to_candidates(
                rows,
                source_table=spec.source_table,
                source_text_type=spec.source_text_type,
            )
        )
    return collected[:limit] if limit is not None else collected


def _run_psql_source_query(
    database_url: str,
    sql: str,
    *,
    org_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    psql_sql = sql.strip().rstrip(";").replace(":org_id", ":'org_id'")
    wrapped_sql = f"""
    SELECT COALESCE(json_agg(row_to_json(limited_rows)), '[]'::json)
    FROM (
      SELECT *
      FROM ({psql_sql}) source_rows
      LIMIT :limit
    ) limited_rows
    """
    command = [
        "psql",
        database_url,
        "-X",
        "-q",
        "-t",
        "-A",
        "-v",
        "ON_ERROR_STOP=1",
        "-v",
        f"org_id={org_id}",
        "-v",
        f"limit={int(limit)}",
        "-c",
        wrapped_sql,
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(_safe_error(result.stderr) or "psql source query failed.")
    output = result.stdout.strip()
    if not output:
        return []
    loaded = json.loads(output)
    if not isinstance(loaded, list):
        raise RuntimeError("psql source query did not return a JSON array.")
    return loaded


def _process_candidate(
    candidate: TextCandidate,
    *,
    prompt_path: str | Path,
    schema_path: str | Path,
    schema_class: Any,
    existing_hashes: set[str],
    min_signal_chars: int,
    max_retries: int,
    extraction_model: str,
    llm_callable: Callable[[TextCandidate, str], Any] | None,
    dry_run: bool,
) -> ExtractionResult:
    cleaned = clean_text(candidate.source_text)
    row = _build_base_row(
        candidate,
        cleaned_text=cleaned,
        prompt_path=prompt_path,
        schema_path=schema_path,
        extraction_model=extraction_model,
        extracted_at=_iso_now(),
    )

    if not cleaned:
        return ExtractionResult(
            candidate=candidate,
            cleaned_text=cleaned,
            row=_finish_row(row, status="skipped_empty"),
        )

    if len(cleaned) < min_signal_chars:
        return ExtractionResult(
            candidate=candidate,
            cleaned_text=cleaned,
            row=_finish_row(row, status="skipped_too_short"),
        )

    dedupe_key = dedupe_key_for_row(row)
    if dedupe_key in existing_hashes:
        return ExtractionResult(
            candidate=candidate,
            cleaned_text=cleaned,
            row=_finish_row(row, status="skipped_duplicate"),
        )
    existing_hashes.add(dedupe_key)

    if dry_run:
        return ExtractionResult(candidate=candidate, cleaned_text=cleaned, row=row)

    last_validation_error: str | None = None
    last_llm_error: str | None = None
    for attempt in range(max_retries + 1):
        try:
            raw_output = (
                llm_callable(candidate, cleaned)
                if llm_callable is not None
                else call_llm_for_candidate(
                    candidate,
                    cleaned_text=cleaned,
                    prompt_path=prompt_path,
                    schema_class=schema_class,
                    model_name=extraction_model,
                )
            )
            llm_output_json = validate_llm_output(raw_output, schema_class)
            status = "success" if llm_output_json.get("insights") else "skipped_no_signal"
            return ExtractionResult(
                candidate=candidate,
                cleaned_text=cleaned,
                row=_finish_row(row, status=status, llm_output_json=llm_output_json),
            )
        except ExtractionValidationError as exc:
            last_validation_error = str(exc)
            if attempt >= max_retries:
                return ExtractionResult(
                    candidate=candidate,
                    cleaned_text=cleaned,
                    row=_finish_row(
                        row,
                        status="validation_failed",
                        extraction_error=last_validation_error,
                    ),
                )
        except Exception as exc:  # noqa: BLE001 - API clients raise varied exceptions.
            last_llm_error = str(exc)
            if attempt >= max_retries:
                return ExtractionResult(
                    candidate=candidate,
                    cleaned_text=cleaned,
                    row=_finish_row(row, status="llm_failed", extraction_error=last_llm_error),
                )

    return ExtractionResult(
        candidate=candidate,
        cleaned_text=cleaned,
        row=_finish_row(
            row,
            status="llm_failed",
            extraction_error=last_llm_error or last_validation_error,
        ),
    )


def write_preview_markdown(
    preview_path: str | Path,
    results: list[ExtractionResult],
    *,
    dry_run: bool = False,
) -> None:
    """Write a manual review markdown file with cleaned input and output."""

    path = Path(preview_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Diagnostic Text Extraction Preview",
        "",
        f"Generated at: {_iso_now()}",
        f"Rows: {len(results)}",
        "",
        "This preview contains cleaned model input, not raw source text.",
        "",
    ]
    for index, result in enumerate(results, start=1):
        row = result.row
        lines.extend(
            [
                f"## Run {index}",
                "",
                f"- Status: `{row['extraction_status']}`",
                f"- Source: `{row['source_table']}.{row['source_text_type']}`",
                f"- Lead ID: `{row['lead_id']}`",
                f"- Source record ID: `{row['source_record_id']}`",
                f"- Source event at: `{row['source_event_at']}`",
                f"- Cleaned text length: `{row['source_text_length']}`",
                f"- Cleaned text hash: `{row['source_text_hash']}`",
                "",
                "### Input",
                "",
                "```text",
                result.cleaned_text,
                "```",
                "",
                "### Output",
                "",
                "```json",
            ]
        )
        output = (
            {"dry_run": True, "message": "LLM was not called."}
            if dry_run and row["extraction_status"] == "success"
            else row["llm_output_json"]
        )
        lines.extend(
            [
                json.dumps(_json_safe(output), ensure_ascii=True, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
        if row.get("extraction_error"):
            lines.extend(["### Error", "", f"`{row['extraction_error']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run_extraction(
    *,
    org_id: str,
    prompt_path: str | Path,
    schema_path: str | Path,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
    preview_md_path: str | Path | None = None,
    limit: int | None = None,
    source_table: str | None = None,
    dry_run: bool = False,
    preview_only: bool = False,
    overwrite: bool = False,
    append: bool = True,
    skip_duplicates: bool = True,
    min_signal_chars: int = DEFAULT_MIN_SIGNAL_CHARS,
    max_retries: int | None = None,
    llm_callable: Callable[[TextCandidate, str], Any] | None = None,
) -> dict[str, Any]:
    """Run collection, optional LLM extraction, JSONL writing, and preview output."""

    if overwrite and not dry_run and not preview_only and Path(output_path).exists():
        Path(output_path).unlink()

    candidates = collect_text_candidates(org_id, limit=limit, source_table=source_table)
    schema_class = None if dry_run else load_schema_class(schema_path)
    existing_hashes = load_existing_hashes(output_path) if skip_duplicates else set()
    extraction_model = _configured_model_name()
    effective_max_retries = _configured_max_retries() if max_retries is None else max_retries
    results: list[ExtractionResult] = []

    for candidate in candidates:
        result = _process_candidate(
            candidate,
            prompt_path=prompt_path,
            schema_path=schema_path,
            schema_class=schema_class,
            existing_hashes=existing_hashes,
            min_signal_chars=min_signal_chars,
            max_retries=effective_max_retries,
            extraction_model=extraction_model,
            llm_callable=llm_callable,
            dry_run=dry_run,
        )
        results.append(result)
        if not dry_run and not preview_only:
            write_jsonl_row(output_path, result.row, append=append)
            append = True

    if preview_md_path is not None:
        write_preview_markdown(preview_md_path, results, dry_run=dry_run)

    statuses: dict[str, int] = {}
    for result in results:
        status = str(result.row["extraction_status"])
        statuses[status] = statuses.get(status, 0) + 1

    return {
        "org_id": org_id,
        "candidate_count": len(candidates),
        "written_jsonl": 0 if dry_run or preview_only else len(results),
        "output_path": None if dry_run or preview_only else str(output_path),
        "preview_md_path": str(preview_md_path) if preview_md_path else None,
        "statuses": statuses,
        "dry_run": dry_run,
        "preview_only": preview_only,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate diagnostic text extraction JSONL.")
    parser.add_argument("--org-id", default=_env_value("HERMON_DEFAULT_CLERK_ORG_ID"))
    parser.add_argument("--prompt-path", required=False, default=str(DEFAULT_PROMPT_PATH))
    parser.add_argument("--schema-path", required=False, default=str(DEFAULT_SCHEMA_PATH))
    parser.add_argument("--output-path", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--preview-md-output", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--source-table", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--no-skip-duplicates", action="store_true")
    parser.add_argument("--min-signal-chars", type=int, default=DEFAULT_MIN_SIGNAL_CHARS)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.org_id:
        raise SystemExit("Missing --org-id or HERMON_DEFAULT_CLERK_ORG_ID.")
    summary = run_extraction(
        org_id=args.org_id,
        prompt_path=args.prompt_path,
        schema_path=args.schema_path,
        output_path=args.output_path,
        preview_md_path=args.preview_md_output,
        limit=args.limit,
        source_table=args.source_table,
        dry_run=args.dry_run,
        preview_only=args.preview_only,
        overwrite=args.overwrite,
        append=args.append or not args.overwrite,
        skip_duplicates=not args.no_skip_duplicates,
        min_signal_chars=args.min_signal_chars,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
