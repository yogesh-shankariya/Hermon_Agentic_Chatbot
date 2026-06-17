"""Factory for the generic SQL analytics agent."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from app.agents.sql_agent.middleware import SkillMiddleware
from app.config import ensure_openai_key, get_sql_agent_settings
from app.utils.prompt_loader import load_prompt


MAX_SQL_EXECUTION_STEPS = 8
SQL_EXECUTION_TOOL = "run_readonly_sql"


def _model_kwargs(
    *,
    service_tier: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    settings = get_sql_agent_settings()
    model_kwargs: dict[str, Any] = {}
    if settings.reasoning:
        model_kwargs["reasoning"] = settings.reasoning
    effective_service_tier = service_tier if service_tier is not None else settings.service_tier
    if effective_service_tier:
        model_kwargs["service_tier"] = effective_service_tier
    if timeout_seconds is not None:
        model_kwargs["timeout"] = timeout_seconds
    openai_request_kwargs = {}
    if settings.prompt_cache_key:
        openai_request_kwargs["prompt_cache_key"] = settings.prompt_cache_key
    if settings.prompt_cache_retention:
        openai_request_kwargs["prompt_cache_retention"] = settings.prompt_cache_retention
    if openai_request_kwargs:
        model_kwargs["model_kwargs"] = openai_request_kwargs
    return model_kwargs


def _invoke_component(
    component: Any,
    payload: Any,
    *,
    config: dict[str, Any] | None = None,
) -> Any:
    if config is None:
        return component.invoke(payload)
    try:
        return component.invoke(payload, config=config)
    except TypeError:
        return component.invoke(payload)


def _message_role(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("role") or message.get("type") or "")
    return str(getattr(message, "type", message.__class__.__name__))


def _message_name(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("name") or "")
    return str(getattr(message, "name", "") or "")


def _stringify_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if "text" in content:
            return str(content["text"])
        if "content" in content:
            return _stringify_content(content["content"])
        return ""
    if isinstance(content, list):
        parts = []
        for item in content:
            text = _stringify_content(item)
            if text:
                parts.append(text)
        return "\n".join(parts)
    return str(content)


def _message_content(message: Any) -> str:
    if isinstance(message, dict):
        return _stringify_content(message.get("content", ""))
    return _stringify_content(getattr(message, "content", ""))


def _message_tool_calls(message: Any) -> list[dict[str, Any]]:
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls is None and isinstance(message, dict):
        tool_calls = message.get("tool_calls")
    if not tool_calls:
        return []

    normalized = []
    for tool_call in tool_calls:
        try:
            safe_tool_call = json.loads(json.dumps(tool_call, default=str))
        except TypeError:
            continue
        if isinstance(safe_tool_call, dict):
            normalized.append(safe_tool_call)
    return normalized


def _parse_json_object(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _selected_skill_names(messages: Sequence[Any]) -> list[str]:
    skill_names: list[str] = []
    for message in messages:
        role = _message_role(message).lower()
        if role in {"ai", "assistant"}:
            for tool_call in _message_tool_calls(message):
                if tool_call.get("name") != "load_skill":
                    continue
                args = tool_call.get("args") or {}
                if not isinstance(args, dict):
                    continue
                skill_name = str(args.get("skill_name") or "").strip()
                if skill_name and skill_name not in skill_names:
                    skill_names.append(skill_name)
        if role != "tool":
            continue
        content = _message_content(message).strip()
        if not content.startswith("Loaded skill:"):
            continue
        first_line = content.splitlines()[0]
        skill_name = first_line.replace("Loaded skill:", "", 1).strip()
        if skill_name and skill_name not in skill_names:
            skill_names.append(skill_name)
    return skill_names


def _latest_sql_execution(messages: Sequence[Any]) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    for message in messages:
        if _message_role(message).lower() != "tool":
            continue
        parsed = _parse_json_object(_message_content(message).strip())
        is_sql_result = _message_name(message) == SQL_EXECUTION_TOOL or (
            isinstance(parsed, dict)
            and "effective_params" in parsed
            and ("rows" in parsed or "sql" in parsed)
        )
        if not is_sql_result:
            continue
        if parsed is None:
            latest = {"ok": False, "error": _message_content(message)}
            continue
        latest = parsed
    return latest


def _has_successful_sql_execution(messages: Sequence[Any]) -> bool:
    latest = _latest_sql_execution(messages)
    return bool(
        isinstance(latest, dict)
        and latest.get("ok") is True
        and isinstance(latest.get("rows"), list)
    )


def _ends_after_tool_call(messages: Sequence[Any]) -> bool:
    if not messages:
        return False
    return _message_role(messages[-1]).lower() == "tool"


def _last_user_content(messages: Sequence[Any]) -> str:
    for message in reversed(messages):
        if _message_role(message).lower() in {"user", "human"}:
            return _message_content(message).strip()
    return ""


def _compact_effective_params(params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        return {}
    return {
        str(key): value
        for key, value in params.items()
        if str(key) not in {"org_id"}
    }


def _parse_iso_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except Exception:
        return None


def _date_range_label(effective_params: dict[str, Any]) -> str | None:
    start_date = _parse_iso_date(effective_params.get("start_date"))
    end_date = _parse_iso_date(effective_params.get("end_date"))
    if start_date is None or end_date is None:
        return None
    display_end = end_date - timedelta(days=1)
    if display_end < start_date:
        return None
    if start_date == display_end:
        return start_date.isoformat()
    return f"{start_date.isoformat()} through {display_end.isoformat()}"


def _row_keys(rows: Any) -> list[str]:
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return []
    keys: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in row:
            key_text = str(key)
            if key_text not in keys:
                keys.append(key_text)
    return keys


def _has_numeric_scalar(rows: Any, visible_keys: Sequence[str]) -> bool:
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        return False
    return any(isinstance(rows[0].get(key), (int, float)) for key in visible_keys)


def _infer_metric_type(question: str, rows: Any) -> str:
    keys = _row_keys(rows)
    lower_keys = [key.lower() for key in keys]
    lower_question = str(question or "").lower()
    if any(
        re.search(
            r"(^|_)(period|month|week|date|day)($|_)|"
            r"(^|_)(previous|pct_change|percent_change)($|_)",
            key,
        )
        for key in lower_keys
    ):
        return "trend"
    if re.search(r"\b(which|list|show me|show the|overdue|missing)\b", lower_question):
        if len(keys) > 2:
            return "list"
    if isinstance(rows, list) and len(rows) == 1:
        visible_keys = [
            key
            for key in keys
            if not key.lower().startswith("total_matching_")
            and key.lower() not in {"total_records", "total_rows"}
        ]
        lower_visible_keys = [key.lower() for key in visible_keys]
        has_metric_key = any(
            re.search(r"(count|total|sum|amount|rate|avg|average)", key)
            for key in lower_visible_keys
        )
        if len(visible_keys) <= 2 and (
            has_metric_key or _has_numeric_scalar(rows, visible_keys)
        ):
            return "count"
    if isinstance(rows, list) and len(rows) > 1:
        return "breakdown"
    return "unknown"


def build_sql_answer_payload(
    messages: Sequence[Any],
    *,
    standalone_question: str | None = None,
) -> dict[str, Any]:
    """Build the compact context used by SQL final answer generation."""

    latest_execution = _latest_sql_execution(messages) or {}
    rows = latest_execution.get("rows")
    if not isinstance(rows, list):
        rows = []
    effective_params = _compact_effective_params(latest_execution.get("effective_params"))
    question = (standalone_question or _last_user_content(messages)).strip()
    skill_names = _selected_skill_names(messages)
    display_metadata: dict[str, Any] = {
        "route": "sql_analytics",
        "metric_type": _infer_metric_type(question, rows),
    }
    if skill_names:
        display_metadata["skill_name"] = skill_names[0]
    if len(skill_names) > 1:
        display_metadata["skill_names"] = skill_names
    if date_label := _date_range_label(effective_params):
        display_metadata["date_range_label"] = date_label

    return {
        "standalone_question": question,
        "rows": rows,
        "effective_params": effective_params,
        "display_metadata": display_metadata,
    }


def build_sql_answer_messages(
    answer_prompt: str,
    answer_payload: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": answer_prompt},
        {
            "role": "user",
            "content": json.dumps(answer_payload, indent=2, sort_keys=True, default=str),
        },
    ]


def _response_text(response: Any) -> str:
    if isinstance(response, str):
        return response.strip()
    if isinstance(response, dict):
        return _stringify_content(response.get("content", "")).strip()
    return _stringify_content(getattr(response, "content", "")).strip()


class CompactSqlAnswerAgent:
    """Run SQL with full skill context, then answer from compact result context."""

    def __init__(
        self,
        *,
        execution_agent: Any,
        answer_model: Any,
        answer_prompt: str,
        max_execution_steps: int = MAX_SQL_EXECUTION_STEPS,
    ) -> None:
        self.execution_agent = execution_agent
        self.answer_model = answer_model
        self.answer_prompt = answer_prompt
        self.max_execution_steps = max_execution_steps

    def invoke(
        self,
        payload: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = dict(payload)
        messages = list(state.get("messages", []))
        standalone_question = _last_user_content(messages)
        result: dict[str, Any] = {"messages": messages}

        for _ in range(self.max_execution_steps):
            previous_message_count = len(messages)
            raw_result = _invoke_component(self.execution_agent, state, config=config)
            result = dict(raw_result) if isinstance(raw_result, dict) else {"messages": []}
            messages = list(result.get("messages", []))

            if _has_successful_sql_execution(messages):
                answer_payload = build_sql_answer_payload(
                    messages,
                    standalone_question=standalone_question,
                )
                answer_messages = build_sql_answer_messages(self.answer_prompt, answer_payload)
                answer_response = _invoke_component(
                    self.answer_model,
                    answer_messages,
                    config=config,
                )
                answer_text = (
                    _response_text(answer_response)
                    or "No final answer was returned."
                )
                return {
                    **result,
                    "messages": [
                        *messages,
                        {"role": "assistant", "content": answer_text},
                    ],
                    "sql_answer_payload": answer_payload,
                }

            if not _ends_after_tool_call(messages):
                return result
            if len(messages) <= previous_message_count:
                return result

            state = {**result, "messages": messages}

        return result


def create_sql_agent(
    *,
    service_tier: str | None = None,
    timeout_seconds: float | None = None,
):
    """Create a LangChain SQL agent configured with enabled SQL skills."""

    ensure_openai_key()
    settings = get_sql_agent_settings()
    sql_prompt = load_prompt("sql_agent")
    answer_prompt = load_prompt("sql_answer")
    model_kwargs = _model_kwargs(
        service_tier=service_tier,
        timeout_seconds=timeout_seconds,
    )
    execution_model = init_chat_model(settings.model, **model_kwargs)
    answer_model = init_chat_model(settings.model, **model_kwargs)

    execution_agent = create_agent(
        execution_model,
        system_prompt=sql_prompt.system,
        middleware=[SkillMiddleware()],
        interrupt_after=["tools"],
    )
    return CompactSqlAnswerAgent(
        execution_agent=execution_agent,
        answer_model=answer_model,
        answer_prompt=answer_prompt.system,
    )
