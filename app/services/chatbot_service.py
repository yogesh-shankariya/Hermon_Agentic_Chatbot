"""Streamlit-free chatbot execution service."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import get_sql_agent_settings, load_app_config
from app.orchestrator import (
    answer_user_question,
    create_default_diagnostic_agent,
    create_default_lead_360_agent,
    create_default_router,
    create_default_sql_agent,
    final_answer_from,
)
from app.org_context import active_org_context
from app.poc_chat_history import (
    fetch_router_poc_chat_history,
    insert_poc_chat_history,
)
from app.schema.chat import ChatRequest, ChatResponse
from langchain_core.callbacks import BaseCallbackHandler

try:
    from langsmith import trace as langsmith_trace
except Exception:  # pragma: no cover - LangSmith is optional outside API runtime.
    langsmith_trace = None


LOGGER = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = APP_DIR / "config" / "config.yaml"
SQL_AGENT_PROMPT_PATH = APP_DIR / "prompts" / "sql_agent" / "1_0_0.yaml"
ROUTER_PROMPT_PATH = APP_DIR / "prompts" / "router.md"
LEAD_360_PROMPT_PATH = APP_DIR / "skills" / "modules" / "lead_360.md"
DIAGNOSTIC_PROMPT_PATH = APP_DIR / "skills" / "modules" / "diagnostic_analytics.md"
AGENT_CACHE_VERSION = "router-first-v1"

SAFE_TOOL_PROGRESS_MESSAGES = {
    "load_skill": "Loading the relevant analytics context...",
    "validate_sql": "Checking the query against the safety rules...",
    "run_readonly_sql": "Running the approved read-only query...",
    "get_lead_360": "Fetching the Lead 360 context...",
    "get_diagnostic_funnel_snapshot": "Running diagnostic funnel checks...",
    "get_diagnostic_source_snapshot": "Reviewing source performance signals...",
    "get_diagnostic_profile_snapshot": "Reviewing profile breakdown signals...",
    "get_diagnostic_source_quality_snapshot": "Checking source quality signals...",
    "get_diagnostic_business_change_snapshot": "Comparing business performance changes...",
    "get_diagnostic_text_reason_snapshot": "Reconciling text reasons with the selected funnel cohort...",
}


ProgressCallback = Callable[[str | dict[str, Any]], None]


def safe_json(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


INFRA_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|password|passwd|pwd|token|service[_-]?role|"
    r"openai[_-]?api[_-]?key|langsmith[_-]?api[_-]?key|database[_-]?url)",
    re.IGNORECASE,
)
INLINE_SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|passwd|pwd|service[_-]?role[_-]?key|"
    r"openai[_-]?api[_-]?key|langsmith[_-]?api[_-]?key)\b\s*[:=]\s*([^\s,;]+)"
)
OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
POSTGRES_PASSWORD_RE = re.compile(r"(postgres(?:ql)?://[^:\s/@]+:)([^@\s]+)(@)")


def redact_infrastructure_secrets(value: Any) -> Any:
    """Redact infrastructure secrets before sending rich payloads to LangSmith."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if INFRA_SECRET_KEY_RE.search(key_text):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_infrastructure_secrets(item)
        return redacted
    if isinstance(value, list):
        return [redact_infrastructure_secrets(item) for item in value]
    if isinstance(value, tuple):
        return [redact_infrastructure_secrets(item) for item in value]
    if isinstance(value, str):
        clean_value = INLINE_SECRET_RE.sub(r"\1=[REDACTED]", value)
        clean_value = OPENAI_KEY_RE.sub("sk-[REDACTED]", clean_value)
        clean_value = POSTGRES_PASSWORD_RE.sub(r"\1[REDACTED]\3", clean_value)
        return clean_value
    return value


def trace_safe_json(value: Any) -> Any:
    return redact_infrastructure_secrets(safe_json(value))


def maybe_json(value: str) -> Any | None:
    try:
        return json.loads(value)
    except Exception:
        return None


def stringify_content_block(item: Any) -> str:
    if isinstance(item, dict):
        block_type = str(item.get("type", "")).lower()
        if block_type in {"reasoning", "function_call", "tool_call"}:
            return ""
        if "text" in item:
            return str(item["text"])
        if "content" in item:
            return stringify_content(item["content"])
        return ""
    return stringify_content(item)


def stringify_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return stringify_content_block(content)
    if isinstance(content, list):
        parts = [part for item in content if (part := stringify_content_block(item))]
        return "\n".join(parts)
    return str(content)


def message_role(message: object) -> str:
    if isinstance(message, dict):
        return str(message.get("role") or message.get("type") or "")
    return str(getattr(message, "type", message.__class__.__name__))


def message_content(message: object) -> str:
    if isinstance(message, dict):
        return stringify_content(message.get("content", ""))
    return stringify_content(getattr(message, "content", ""))


def serialized_run_name(serialized: dict[str, Any] | None, fallback: str) -> str:
    if not isinstance(serialized, dict):
        return fallback

    name = serialized.get("name") or serialized.get("repr")
    if name:
        return str(name)

    identifier = serialized.get("id")
    if isinstance(identifier, list) and identifier:
        return str(identifier[-1])
    if identifier:
        return str(identifier)

    return fallback


class AgentTimingCallback(BaseCallbackHandler):
    """Collect per-model and per-tool timings for one chatbot turn."""

    raise_error = False

    def __init__(self) -> None:
        super().__init__()
        self._running: dict[str, dict[str, Any]] = {}
        self.events: list[dict[str, Any]] = []

    def _start(self, run_id: Any, *, kind: str, name: str) -> None:
        self._running[str(run_id)] = {
            "kind": kind,
            "name": name,
            "started_at": time.perf_counter(),
        }

    def _finish(
        self,
        run_id: Any,
        *,
        status: str,
        error: BaseException | None = None,
    ) -> None:
        event = self._running.pop(str(run_id), None)
        if event is None:
            return

        finished_at = time.perf_counter()
        started_at = float(event.pop("started_at"))
        event["duration_seconds"] = max(0.0, finished_at - started_at)
        event["status"] = status
        if error is not None:
            event["error"] = f"{type(error).__name__}: {error}"
        self.events.append(event)

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._start(
            run_id,
            kind="model",
            name=serialized_run_name(serialized, "chat_model"),
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        if str(run_id) in self._running:
            return
        self._start(
            run_id,
            kind="model",
            name=serialized_run_name(serialized, "llm"),
        )

    def on_llm_end(self, response: Any, *, run_id: Any, **kwargs: Any) -> None:
        self._finish(run_id, status="ok")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._finish(run_id, status="error", error=error)

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._start(
            run_id,
            kind="tool",
            name=serialized_run_name(serialized, "tool"),
        )

    def on_tool_end(self, output: Any, *, run_id: Any, **kwargs: Any) -> None:
        self._finish(run_id, status="ok")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._finish(run_id, status="error", error=error)


def safe_tool_progress_message(tool_name: str) -> str:
    normalized_name = tool_name.strip()
    if normalized_name in SAFE_TOOL_PROGRESS_MESSAGES:
        return SAFE_TOOL_PROGRESS_MESSAGES[normalized_name]
    if normalized_name.startswith("get_diagnostic_"):
        return "Running diagnostic checks..."
    return "Running an approved tool..."


class AgentProgressCallback(BaseCallbackHandler):
    """Emit safe user-facing progress updates from LangChain callbacks."""

    raise_error = False

    def __init__(self, emit: Callable[[str], None]) -> None:
        super().__init__()
        self.emit = emit
        self._seen_model_runs: set[str] = set()
        self._last_tool_name: str | None = None

    def _emit(self, message: str) -> None:
        try:
            self.emit(message)
        except Exception:
            return

    def _tool_names_from_generation(self, generation: Any) -> list[str]:
        message = getattr(generation, "message", None)
        if message is None and isinstance(generation, dict):
            message = generation.get("message")
        if message is None:
            return []

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls is None and isinstance(message, dict):
            tool_calls = message.get("tool_calls")
        if not tool_calls:
            return []

        names = []
        for tool_call in tool_calls:
            safe_tool_call = safe_json(tool_call)
            if not isinstance(safe_tool_call, dict):
                continue
            name = safe_tool_call.get("name")
            if name:
                names.append(str(name))
        return names

    def _tool_names_from_response(self, response: Any) -> list[str]:
        names = []
        generations = getattr(response, "generations", None)
        if generations is None and isinstance(response, dict):
            generations = response.get("generations")
        if not generations:
            return names

        for generation_group in generations:
            generation_items = generation_group if isinstance(generation_group, list) else [generation_group]
            for generation in generation_items:
                names.extend(self._tool_names_from_generation(generation))
        return names

    def _message_for_model_start(self) -> str:
        if not self._seen_model_runs:
            return "Calling the router model..."

        if self._last_tool_name == "load_skill":
            return "Drafting a safe read-only SQL query..."
        if self._last_tool_name == "run_readonly_sql":
            return "Generating the final answer from query results..."
        if self._last_tool_name == "get_lead_360":
            return "Generating the Lead 360 answer..."
        if self._last_tool_name and self._last_tool_name.startswith("get_diagnostic_"):
            return "Generating the diagnostic answer..."
        if len(self._seen_model_runs) == 1:
            return "Selecting the right skill and planning the next step..."
        return "Generating the final answer..."

    def _start_model(self, run_id: Any) -> None:
        run_key = str(run_id)
        if run_key in self._seen_model_runs:
            return
        self._emit(self._message_for_model_start())
        self._seen_model_runs.add(run_key)

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._start_model(run_id)

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._start_model(run_id)

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized_run_name(serialized, "tool")
        self._last_tool_name = tool_name
        self._emit(safe_tool_progress_message(tool_name))

    def on_tool_end(self, output: Any, *, run_id: Any, **kwargs: Any) -> None:
        self._emit("Reviewing the tool result...")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        self._emit("The tool returned an error, preparing a readable response...")

    def on_llm_end(self, response: Any, *, run_id: Any, **kwargs: Any) -> None:
        tool_names = self._tool_names_from_response(response)
        if not tool_names:
            return

        for tool_name in tool_names:
            self._last_tool_name = tool_name
            self._emit(safe_tool_progress_message(tool_name))


def build_timing_breakdown(
    events: list[dict[str, Any]],
    *,
    total_seconds: float,
) -> dict[str, Any]:
    clean_events: list[dict[str, Any]] = []
    for event in events:
        duration = event.get("duration_seconds")
        if not isinstance(duration, (int, float)):
            continue
        clean_events.append(
            {
                "kind": str(event.get("kind") or "unknown"),
                "name": str(event.get("name") or "unknown"),
                "duration_seconds": float(duration),
                "status": str(event.get("status") or "unknown"),
                "error": event.get("error"),
            }
        )

    model_positions = [
        index for index, event in enumerate(clean_events) if event["kind"] == "model"
    ]
    for model_number, position in enumerate(model_positions, start=1):
        event = clean_events[position]
        if len(model_positions) == 1:
            event["stage"] = "AI response"
        elif model_number == 1:
            event["stage"] = "Classification / skill selection"
        elif model_number == len(model_positions):
            event["stage"] = "Final answer generation"
        else:
            event["stage"] = f"AI tool planning {model_number - 1}"

    for event in clean_events:
        if event["kind"] == "tool":
            event["stage"] = f"Tool response: {event['name']}"

    model_seconds = sum(
        event["duration_seconds"] for event in clean_events if event["kind"] == "model"
    )
    tool_seconds = sum(
        event["duration_seconds"] for event in clean_events if event["kind"] == "tool"
    )
    event_seconds = sum(event["duration_seconds"] for event in clean_events)

    classification_seconds = (
        clean_events[model_positions[0]]["duration_seconds"] if model_positions else None
    )
    final_answer_seconds = (
        clean_events[model_positions[-1]]["duration_seconds"]
        if len(model_positions) > 1
        else None
    )

    return {
        "total_seconds": total_seconds,
        "classification_seconds": classification_seconds,
        "model_seconds": model_seconds,
        "tool_seconds": tool_seconds,
        "final_answer_seconds": final_answer_seconds,
        "overhead_seconds": max(0.0, total_seconds - event_seconds),
        "events": clean_events,
    }


def effective_runtime_params(params_json: str | None, *, org_id: str) -> dict[str, Any] | None:
    parsed_params = maybe_json(params_json or "{}")
    if not isinstance(parsed_params, dict):
        return None

    params = dict(parsed_params)
    params["org_id"] = org_id
    settings = get_sql_agent_settings()
    params.setdefault("limit", settings.max_tool_rows)
    return params


def extract_execution_details(messages: list[object], *, org_id: str) -> dict[str, Any]:
    """Pull user-facing SQL and result rows out of the agent trace."""

    details: dict[str, Any] = {
        "sql": None,
        "selected_skill": None,
        "params": None,
        "effective_params": None,
        "rows": None,
        "row_count": None,
        "tool_error": None,
    }

    for message in messages:
        if message_role(message) == "ai":
            for tool_call in getattr(message, "tool_calls", None) or []:
                tool_call = safe_json(tool_call)
                tool_name = tool_call.get("name")
                args = tool_call.get("args") or {}
                if not isinstance(args, dict):
                    continue

                if tool_name == "load_skill" and args.get("skill_name"):
                    details["selected_skill"] = str(args["skill_name"]).strip()

                if tool_name in {"run_readonly_sql", "validate_sql"} and args.get("query"):
                    details["sql"] = str(args["query"]).strip()
                    if tool_name == "run_readonly_sql":
                        details["params"] = str(args.get("params_json", "{}"))
                        details["effective_params"] = effective_runtime_params(
                            details["params"],
                            org_id=org_id,
                        )
                    elif args.get("params_json"):
                        details["params"] = args["params_json"]

        if message_role(message) == "tool":
            content = message_content(message).strip()
            if content.startswith("Loaded skill:"):
                first_line = content.splitlines()[0]
                details["selected_skill"] = first_line.replace("Loaded skill:", "", 1).strip()

            parsed = maybe_json(content)
            if not isinstance(parsed, dict):
                continue

            if parsed.get("sql"):
                details["sql"] = str(parsed["sql"]).strip()
            if parsed.get("error"):
                details["tool_error"] = str(parsed["error"])
            if isinstance(parsed.get("effective_params"), dict):
                details["effective_params"] = parsed["effective_params"]
            if isinstance(parsed.get("rows"), list):
                details["tool_error"] = None
                details["rows"] = parsed["rows"]
                details["row_count"] = parsed.get("row_count", len(parsed["rows"]))

    return details


def extract_lead_360_diagnostics(messages: list[object]) -> dict[str, Any] | None:
    for message in messages:
        if message_role(message) != "tool":
            continue
        parsed = maybe_json(message_content(message).strip())
        if not isinstance(parsed, dict):
            continue
        diagnostics = parsed.get("_diagnostics")
        if isinstance(diagnostics, dict):
            return diagnostics
    return None


def _path_mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


@lru_cache(maxsize=32)
def get_flow_components(
    cache_version: str = AGENT_CACHE_VERSION,
    organization_id: str = "",
    config_mtime_ns: int = 0,
    prompt_mtime_ns: int = 0,
    router_prompt_mtime_ns: int = 0,
    lead_360_prompt_mtime_ns: int = 0,
    diagnostic_prompt_mtime_ns: int = 0,
) -> dict[str, Any]:
    _ = cache_version
    _ = organization_id
    _ = config_mtime_ns
    _ = prompt_mtime_ns
    _ = router_prompt_mtime_ns
    _ = lead_360_prompt_mtime_ns
    _ = diagnostic_prompt_mtime_ns
    load_app_config.cache_clear()
    return {
        "router": create_default_router(),
        "sql_agent": create_default_sql_agent(),
        "lead_360_agent": create_default_lead_360_agent(),
        "diagnostic_agent": create_default_diagnostic_agent(),
    }


def _emit_progress(
    progress_callback: ProgressCallback | None,
    message_or_event: str | dict[str, Any],
) -> None:
    if progress_callback is None:
        return
    try:
        progress_callback(message_or_event)
    except Exception:
        return


def _make_text_progress_emitter(progress_callback: ProgressCallback | None) -> Callable[[str | dict[str, Any]], None]:
    def emit(message_or_event: str | dict[str, Any]) -> None:
        _emit_progress(progress_callback, message_or_event)

    return emit


def _validate_timezone(timezone_name: str | None) -> str:
    clean_timezone = str(timezone_name or "").strip()
    if not clean_timezone:
        raise ValueError("Timezone is required.")
    try:
        ZoneInfo(clean_timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid IANA timezone: {clean_timezone}") from exc
    return clean_timezone


def _resolve_org_id(request: ChatRequest) -> str:
    requested_org_id = str(request.org_id or "").strip()
    if requested_org_id:
        return requested_org_id

    raise ValueError("Organization ID is required.")


def _request_chat_history_was_supplied(request: ChatRequest) -> bool:
    fields_set = getattr(request, "model_fields_set", None)
    if fields_set is None:
        fields_set = getattr(request, "__fields_set__", set())
    return "chat_history" in fields_set


def _history_item_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "dict"):
        return item.dict()
    return {
        "role": getattr(item, "role", None),
        "content": getattr(item, "content", None),
        "question": getattr(item, "question", None),
        "answer": getattr(item, "answer", None),
        "route": getattr(item, "route", None),
        "selected_skill": getattr(item, "selected_skill", None),
        "standalone_question": getattr(item, "standalone_question", None),
    }


def _normalize_chat_history(chat_history: Sequence[Any]) -> list[dict[str, Any]]:
    """Convert role/content messages or stored POC turns into router Q&A turns."""

    turns: list[dict[str, Any]] = []
    pending_user: str | None = None

    for raw_item in chat_history:
        item = _history_item_dict(raw_item)
        question = str(
            item.get("question")
            or item.get("user_question")
            or item.get("user")
            or ""
        ).strip()
        answer = str(item.get("answer") or item.get("assistant") or "").strip()
        if question or answer:
            turn = {"question": question, "answer": answer}
            for key in ("route", "selected_skill", "standalone_question"):
                value = str(item.get(key) or "").strip()
                if value:
                    turn[key] = value
            turns.append(turn)
            pending_user = None
            continue

        role = str(item.get("role") or item.get("type") or "").strip().lower()
        content = stringify_content(item.get("content", "")).strip()
        if not role or not content:
            continue
        if role in {"user", "human"}:
            pending_user = content
            continue
        if role in {"assistant", "ai"} and pending_user is not None:
            turns.append({"question": pending_user, "answer": content})
            pending_user = None

    return turns


def _chat_history_for_request(
    request: ChatRequest,
    *,
    org_id: str,
    persist_history: bool,
) -> list[dict[str, Any]]:
    if _request_chat_history_was_supplied(request):
        return _normalize_chat_history(request.chat_history)
    if persist_history:
        return fetch_router_poc_chat_history(org_id)
    return []


def _persist_poc_turn(turn: dict[str, Any], *, org_id: str, question: str) -> None:
    """Save local POC chat history without letting persistence break the answer."""

    try:
        insert_poc_chat_history(
            organization_id=org_id,
            route=str(turn.get("route") or ""),
            selected_skill=turn.get("selected_skill"),
            user_question=question,
            standalone_question=str(turn.get("standalone_question") or "") or None,
            generated_sql=turn.get("generated_sql"),
            answer=str(turn.get("answer") or ""),
            elapsed_seconds=turn.get("elapsed_seconds"),
            execution_details=safe_json(turn.get("execution_details")),
            timing=safe_json(turn.get("timing")),
            lead_360_diagnostics=safe_json(turn.get("lead_360_diagnostics")),
        )
    except Exception:
        LOGGER.exception("Failed to persist local POC chat history")


def run_chatbot_turn(
    request: ChatRequest,
    *,
    progress_callback: ProgressCallback | None = None,
    persist_history: bool = False,
) -> dict[str, Any]:
    """Run one chatbot turn and return rich internal turn data."""

    question = str(request.question or "").strip()
    if not question:
        raise ValueError("Question is required.")

    requested_timezone = _validate_timezone(request.timezone)
    org_id = _resolve_org_id(request)
    emit_progress = _make_text_progress_emitter(progress_callback)
    request_chat_history_count = len(request.chat_history or [])

    _emit_progress(progress_callback, "Understanding your question...")
    started_at = time.perf_counter()

    with active_org_context(org_id):
        _emit_progress(progress_callback, "Loading recent conversation context...")
        chat_history = _chat_history_for_request(
            request,
            org_id=org_id,
            persist_history=persist_history,
        )
        _emit_progress(progress_callback, "Loading the configured agents...")
        components = get_flow_components(
            organization_id=org_id,
            config_mtime_ns=_path_mtime_ns(CONFIG_PATH),
            prompt_mtime_ns=_path_mtime_ns(SQL_AGENT_PROMPT_PATH),
            router_prompt_mtime_ns=_path_mtime_ns(ROUTER_PROMPT_PATH),
            lead_360_prompt_mtime_ns=_path_mtime_ns(LEAD_360_PROMPT_PATH),
            diagnostic_prompt_mtime_ns=_path_mtime_ns(DIAGNOSTIC_PROMPT_PATH),
        )
        timing_callback = AgentTimingCallback()
        callbacks: list[BaseCallbackHandler] = [timing_callback]
        if progress_callback is not None:
            callbacks.append(AgentProgressCallback(emit_progress))
        turn = answer_user_question(
            question,
            chat_history,
            router=components["router"],
            sql_agent=components["sql_agent"],
            lead_360_agent=components["lead_360_agent"],
            diagnostic_agent=components["diagnostic_agent"],
            config={"callbacks": callbacks},
            progress_callback=emit_progress,
        )

    elapsed_seconds = time.perf_counter() - started_at
    trace_messages = list(turn.get("trace_messages", []))
    all_messages = list(turn.get("all_messages", []))
    answer = str(turn.get("answer") or final_answer_from(trace_messages) or final_answer_from(all_messages))
    execution_details = extract_execution_details(trace_messages, org_id=org_id)
    lead_360_diagnostics = extract_lead_360_diagnostics(trace_messages)
    route = str(turn.get("route") or "")
    selected_skill = (
        str(execution_details.get("selected_skill") or "").strip()
        if route == "sql_analytics"
        else ""
    )
    selected_skill = selected_skill or None
    generated_sql = (
        str(execution_details.get("sql") or "").strip()
        if route == "sql_analytics"
        else ""
    )
    generated_sql = generated_sql or None
    timing = build_timing_breakdown(
        timing_callback.events,
        total_seconds=elapsed_seconds,
    )

    full_turn = {
        "question": question,
        "answer": answer,
        "standalone_question": turn.get("standalone_question", question),
        "route": route,
        "router_response": turn.get("router_response"),
        "organization_id": org_id,
        "user_id": request.user_id,
        "timezone": requested_timezone,
        "chat_history_count": request_chat_history_count,
        "selected_skill": selected_skill,
        "generated_sql": generated_sql,
        "latest_router_history": turn.get("latest_router_history", []),
        "selected_history": turn.get("selected_history", []),
        "trace_messages": trace_messages,
        "all_messages": all_messages,
        "context_turn_count": int(turn.get("context_turn_count", 0)),
        "elapsed_seconds": elapsed_seconds,
        "timing": timing,
        "lead_360_diagnostics": lead_360_diagnostics,
        "execution_details": execution_details,
    }

    if persist_history:
        _persist_poc_turn(full_turn, org_id=org_id, question=question)

    return full_turn


def _public_metadata(turn: dict[str, Any]) -> dict[str, Any]:
    timing = turn.get("timing") if isinstance(turn.get("timing"), dict) else {}
    timing_summary = {
        key: timing.get(key)
        for key in (
            "total_seconds",
            "classification_seconds",
            "model_seconds",
            "tool_seconds",
            "final_answer_seconds",
            "overhead_seconds",
        )
    }
    return {
        "standalone_question": turn.get("standalone_question"),
        "selected_skill": turn.get("selected_skill"),
        "context_turn_count": turn.get("context_turn_count"),
        "elapsed_seconds": turn.get("elapsed_seconds"),
        "timezone": turn.get("timezone"),
        "timing": timing_summary,
    }


def _safe_error_message(exc: BaseException) -> str:
    if isinstance(exc, ValueError):
        message = str(exc).strip()
        return message or "Invalid request."
    return "Unable to complete this request."


def _error_status_code(exc: BaseException) -> int:
    return 400 if isinstance(exc, ValueError) else 500


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


def response_to_dict(response: ChatResponse) -> dict[str, Any]:
    return _model_dump(response)


def _trace_request_inputs(request: ChatRequest) -> dict[str, Any]:
    return {
        "question": str(request.question or ""),
        "user_id": str(request.user_id or ""),
        "org_id": str(request.org_id or ""),
        "timezone": str(request.timezone or ""),
        "chat_history_count": len(request.chat_history or []),
    }


def _validate_required_request_fields(request: ChatRequest) -> None:
    if not str(request.question or "").strip():
        raise ValueError("Question is required.")
    if not str(request.user_id or "").strip():
        raise ValueError("User ID is required.")
    if not str(request.org_id or "").strip():
        raise ValueError("Organization ID is required.")
    if not str(request.timezone or "").strip():
        raise ValueError("Timezone is required.")


def _open_langsmith_trace(
    name: str,
    *,
    inputs: dict[str, Any],
    metadata: dict[str, Any],
) -> Any:
    if langsmith_trace is None:
        return nullcontext(None)
    return langsmith_trace(
        name,
        run_type="chain",
        inputs=trace_safe_json(inputs),
        metadata=trace_safe_json(metadata),
    )


def _trace_id_for_run(run: Any) -> str | None:
    run_id = getattr(run, "id", None)
    return str(run_id) if run_id else None


def _set_run_metadata(run: Any, metadata: dict[str, Any]) -> None:
    if run is None:
        return
    try:
        run.metadata.update(trace_safe_json(metadata))
    except Exception:
        return


def _end_trace_run(
    run: Any,
    *,
    outputs: dict[str, Any],
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if run is None:
        return
    if metadata:
        _set_run_metadata(run, metadata)
    clean_error = (
        str(redact_infrastructure_secrets(error))
        if error is not None
        else None
    )
    run.end(outputs=trace_safe_json(outputs), error=clean_error)


def _capture_trace_child(
    parent_run: Any,
    name: str,
    *,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    run_type: str = "chain",
    metadata: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    if parent_run is None or langsmith_trace is None:
        return
    try:
        with langsmith_trace(
            name,
            run_type=run_type,
            parent=parent_run,
            inputs=trace_safe_json(inputs or {}),
            metadata=trace_safe_json(metadata or {}),
        ) as child_run:
            _end_trace_run(
                child_run,
                outputs=outputs or {},
                error=error,
            )
    except Exception:
        LOGGER.exception("Failed to capture LangSmith child run: %s", name)


def _message_tool_calls(message: object) -> list[dict[str, Any]]:
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls is None and isinstance(message, dict):
        tool_calls = message.get("tool_calls")
    if not tool_calls:
        return []

    normalized: list[dict[str, Any]] = []
    for tool_call in tool_calls:
        safe_tool_call = safe_json(tool_call)
        if isinstance(safe_tool_call, dict):
            normalized.append(safe_tool_call)
    return normalized


def _message_attr(message: object, name: str) -> Any:
    if isinstance(message, dict):
        return message.get(name)
    return getattr(message, name, None)


def _parse_tool_output(output: str) -> Any:
    parsed = maybe_json(output.strip())
    return parsed if parsed is not None else output


def extract_tool_call_records(messages: list[object]) -> list[dict[str, Any]]:
    """Return complete LangChain tool inputs and outputs from trace messages."""

    records: list[dict[str, Any]] = []
    by_tool_call_id: dict[str, dict[str, Any]] = {}

    for message in messages:
        if message_role(message).lower() in {"ai", "assistant"}:
            for tool_call in _message_tool_calls(message):
                tool_call_id = str(
                    tool_call.get("id")
                    or tool_call.get("tool_call_id")
                    or ""
                ).strip()
                record = {
                    "tool_call_id": tool_call_id or None,
                    "tool_name": tool_call.get("name"),
                    "complete_tool_input": tool_call.get("args"),
                    "complete_tool_output": None,
                    "complete_tool_output_json": None,
                    "success_or_failure": None,
                    "error_details": None,
                }
                records.append(record)
                if tool_call_id:
                    by_tool_call_id[tool_call_id] = record
            continue

        if message_role(message).lower() != "tool":
            continue

        tool_call_id = str(_message_attr(message, "tool_call_id") or "").strip()
        output_text = message_content(message)
        parsed_output = _parse_tool_output(output_text)
        record = by_tool_call_id.get(tool_call_id)
        if record is None:
            record = {
                "tool_call_id": tool_call_id or None,
                "tool_name": _message_attr(message, "name"),
                "complete_tool_input": None,
                "complete_tool_output": None,
                "complete_tool_output_json": None,
                "success_or_failure": None,
                "error_details": None,
            }
            records.append(record)
        if not record.get("tool_name"):
            record["tool_name"] = _message_attr(message, "name")
        record["complete_tool_output"] = output_text
        if parsed_output is not output_text:
            record["complete_tool_output_json"] = parsed_output
            if isinstance(parsed_output, dict):
                error_details = parsed_output.get("error")
                record["success_or_failure"] = (
                    "failure"
                    if parsed_output.get("ok") is False or error_details
                    else "success"
                )
                record["error_details"] = error_details
        if record.get("success_or_failure") is None:
            record["success_or_failure"] = "success" if output_text else "unknown"

    return records


def _tool_names(tool_calls: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for tool_call in tool_calls:
        name = str(tool_call.get("tool_name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def _column_names(rows: Any) -> list[str]:
    if not isinstance(rows, list) or not rows:
        return []
    first_row = rows[0]
    if not isinstance(first_row, dict):
        return []
    return [str(key) for key in first_row.keys()]


def _sql_debug_payload(turn: dict[str, Any]) -> dict[str, Any]:
    execution_details = (
        turn.get("execution_details")
        if isinstance(turn.get("execution_details"), dict)
        else {}
    )
    rows = execution_details.get("rows")
    if not isinstance(rows, list):
        rows = []
    tool_error = execution_details.get("tool_error")
    return {
        "selected_skill": turn.get("selected_skill"),
        "complete_generated_sql": turn.get("generated_sql") or execution_details.get("sql"),
        "sql_params": execution_details.get("effective_params") or execution_details.get("params"),
        "sql_execution_status": "failure" if tool_error else "success",
        "row_count": execution_details.get("row_count", len(rows)),
        "column_names": _column_names(rows),
        "complete_sql_result": rows,
        "full_final_answer": turn.get("answer"),
        "error_details": tool_error,
    }


def _lead_sections_used(tool_output: Any) -> list[str]:
    if not isinstance(tool_output, dict):
        return []
    lead_360 = tool_output.get("lead_360")
    if not isinstance(lead_360, dict):
        return []
    return [
        str(key)
        for key, value in lead_360.items()
        if value not in (None, "", [], {})
    ]


def _trace_success_outputs(
    request: ChatRequest,
    turn: dict[str, Any],
    response: ChatResponse,
    *,
    tool_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_tools = _tool_names(tool_calls)
    outputs = {
        "question": turn.get("question") or request.question,
        "standalone_question": turn.get("standalone_question"),
        "user_id": request.user_id,
        "org_id": turn.get("organization_id") or request.org_id,
        "timezone": turn.get("timezone") or request.timezone,
        "chat_history_count": turn.get("chat_history_count", len(request.chat_history or [])),
        "route": turn.get("route"),
        "selected_skill": turn.get("selected_skill"),
        "selected_tool": selected_tools[0] if selected_tools else None,
        "selected_tools": selected_tools,
        "full_final_answer": turn.get("answer"),
        "latency": turn.get("elapsed_seconds"),
        "status_code": response.status_code,
        "error_details": None,
        "tool_calls": tool_calls,
        "timing": turn.get("timing"),
    }
    if turn.get("route") == "sql_analytics":
        outputs.update(_sql_debug_payload(turn))
    return outputs


def _trace_error_outputs(
    request: ChatRequest,
    response: ChatResponse,
    *,
    started_at: float,
    error_details: str,
) -> dict[str, Any]:
    return {
        "question": str(request.question or ""),
        "standalone_question": response.standalone_question,
        "user_id": str(request.user_id or ""),
        "org_id": str(request.org_id or ""),
        "timezone": str(request.timezone or ""),
        "chat_history_count": len(request.chat_history or []),
        "route": response.route,
        "selected_skill": None,
        "selected_tool": None,
        "full_final_answer": None,
        "latency": max(0.0, time.perf_counter() - started_at),
        "status_code": response.status_code,
        "error_details": error_details,
    }


def _capture_success_children(
    parent_run: Any,
    request: ChatRequest,
    turn: dict[str, Any],
    response: ChatResponse,
    *,
    tool_calls: list[dict[str, Any]],
) -> None:
    route = str(turn.get("route") or "")
    _capture_trace_child(
        parent_run,
        "route_decision",
        inputs={
            "question": request.question,
            "chat_history_count": turn.get("chat_history_count"),
        },
        outputs={
            "route": route,
            "standalone_question": turn.get("standalone_question"),
            "router_response": turn.get("router_response"),
        },
    )

    if turn.get("selected_skill"):
        load_skill_output = next(
            (
                tool_call.get("complete_tool_output")
                for tool_call in tool_calls
                if tool_call.get("tool_name") == "load_skill"
            ),
            None,
        )
        _capture_trace_child(
            parent_run,
            "skill_selection",
            inputs={"route": route},
            outputs={
                "selected_skill": turn.get("selected_skill"),
                "complete_tool_output": load_skill_output,
            },
        )

    selected_tools = _tool_names(tool_calls)
    if selected_tools:
        _capture_trace_child(
            parent_run,
            "tool_selection",
            inputs={"route": route},
            outputs={"selected_tool": selected_tools[0], "selected_tools": selected_tools},
        )

    if route == "sql_analytics":
        sql_payload = _sql_debug_payload(turn)
        _capture_trace_child(
            parent_run,
            "sql_generation",
            inputs={
                "standalone_question": turn.get("standalone_question"),
                "selected_skill": turn.get("selected_skill"),
            },
            outputs={
                "complete_generated_sql": sql_payload.get("complete_generated_sql"),
                "sql_params": sql_payload.get("sql_params"),
            },
        )
        _capture_trace_child(
            parent_run,
            "sql_execution",
            run_type="tool",
            inputs={
                "complete_generated_sql": sql_payload.get("complete_generated_sql"),
                "sql_params": sql_payload.get("sql_params"),
            },
            outputs=sql_payload,
            error=sql_payload.get("error_details"),
        )

    captured_tool_call_ids: set[str] = set()
    for tool_call in tool_calls:
        tool_name = str(tool_call.get("tool_name") or "")
        tool_call_id = str(tool_call.get("tool_call_id") or "")
        parsed_output = tool_call.get("complete_tool_output_json")
        if route == "diagnostic_analytics" and tool_name.startswith("get_diagnostic_"):
            captured_tool_call_ids.add(tool_call_id)
            _capture_trace_child(
                parent_run,
                "diagnostic_tool_call",
                run_type="tool",
                inputs={
                    "tool_name": tool_name,
                    "complete_tool_input": tool_call.get("complete_tool_input"),
                },
                outputs={
                    "tool_name": tool_name,
                    "complete_tool_input": tool_call.get("complete_tool_input"),
                    "complete_tool_output": tool_call.get("complete_tool_output"),
                    "complete_tool_output_json": parsed_output,
                    "full_final_answer": turn.get("answer"),
                    "success_or_failure": tool_call.get("success_or_failure"),
                    "error_details": tool_call.get("error_details"),
                },
                error=tool_call.get("error_details"),
            )
        elif route == "lead_360" and tool_name == "get_lead_360":
            captured_tool_call_ids.add(tool_call_id)
            lead_match_status = (
                parsed_output.get("status")
                if isinstance(parsed_output, dict)
                else None
            )
            _capture_trace_child(
                parent_run,
                "lead_360_tool_call",
                run_type="tool",
                inputs={
                    "tool_name": tool_name,
                    "complete_tool_input": tool_call.get("complete_tool_input"),
                },
                outputs={
                    "tool_name": tool_name,
                    "complete_tool_input": tool_call.get("complete_tool_input"),
                    "complete_tool_output": tool_call.get("complete_tool_output"),
                    "complete_tool_output_json": parsed_output,
                    "sections_used": _lead_sections_used(parsed_output),
                    "lead_match_status": lead_match_status,
                    "full_final_answer": turn.get("answer"),
                    "success_or_failure": tool_call.get("success_or_failure"),
                    "error_details": tool_call.get("error_details"),
                },
                error=tool_call.get("error_details"),
            )

    for tool_call in tool_calls:
        tool_call_id = str(tool_call.get("tool_call_id") or "")
        tool_name = str(tool_call.get("tool_name") or "")
        if tool_call_id in captured_tool_call_ids:
            continue
        if route == "sql_analytics" and tool_name in {"load_skill", "run_readonly_sql"}:
            continue
        _capture_trace_child(
            parent_run,
            "tool_call",
            run_type="tool",
            inputs={
                "name": tool_name,
                "input": tool_call.get("complete_tool_input"),
            },
            outputs={
                "name": tool_name,
                "input": tool_call.get("complete_tool_input"),
                "complete_output": tool_call.get("complete_tool_output"),
                "complete_output_json": tool_call.get("complete_tool_output_json"),
                "latency": None,
                "success_or_failure": tool_call.get("success_or_failure"),
                "error_details": tool_call.get("error_details"),
            },
            error=tool_call.get("error_details"),
        )

    _capture_trace_child(
        parent_run,
        "final_answer_generation",
        inputs={
            "route": route,
            "standalone_question": turn.get("standalone_question"),
        },
        outputs={
            "full_final_answer": turn.get("answer"),
            "status_code": response.status_code,
            "message": response.message,
        },
    )


def run_chatbot(
    request: ChatRequest,
    *,
    progress_callback: ProgressCallback | None = None,
) -> ChatResponse:
    """Run the chatbot and return the minimal API response contract."""

    trace_inputs = _trace_request_inputs(request)
    started_at = time.perf_counter()

    with _open_langsmith_trace(
        "/chat request",
        inputs=trace_inputs,
        metadata={"endpoint": "/chat", "chat_history_count": trace_inputs["chat_history_count"]},
    ) as root_run:
        trace_id = _trace_id_for_run(root_run)
        try:
            _validate_required_request_fields(request)
            turn = run_chatbot_turn(request, progress_callback=progress_callback)
        except Exception as exc:  # noqa: BLE001 - API responses must stay controlled.
            if isinstance(exc, ValueError):
                LOGGER.debug("Chatbot request validation failed: %s", exc)
            else:
                LOGGER.exception("Chatbot execution failed")
            status_code = _error_status_code(exc)
            response = ChatResponse(
                status_code=status_code,
                message=_safe_error_message(exc),
                answer=None,
                route=None,
                standalone_question=None,
                trace_id=trace_id,
            )
            error_details = f"{type(exc).__name__}: {exc}"
            outputs = _trace_error_outputs(
                request,
                response,
                started_at=started_at,
                error_details=error_details,
            )
            _capture_trace_child(
                root_run,
                "request_error",
                inputs=trace_inputs,
                outputs=outputs,
                error=error_details,
            )
            _end_trace_run(
                root_run,
                outputs=outputs,
                error=error_details,
                metadata={
                    "status_code": status_code,
                    "route": None,
                    "error_details": error_details,
                },
            )
            return response

        response = ChatResponse(
            status_code=200,
            message="success",
            answer=str(turn.get("answer") or ""),
            route=str(turn.get("route") or "") or None,
            standalone_question=str(turn.get("standalone_question") or "") or None,
            trace_id=trace_id,
        )
        tool_calls = extract_tool_call_records(list(turn.get("trace_messages", [])))
        outputs = _trace_success_outputs(
            request,
            turn,
            response,
            tool_calls=tool_calls,
        )
        _capture_success_children(
            root_run,
            request,
            turn,
            response,
            tool_calls=tool_calls,
        )
        _end_trace_run(
            root_run,
            outputs=outputs,
            metadata={
                "status_code": response.status_code,
                "route": response.route,
                "standalone_question": response.standalone_question,
                "latency": turn.get("elapsed_seconds"),
            },
        )
        return response
