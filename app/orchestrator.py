"""Router-first orchestration for Hermon user questions."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any

from app.schema.router import RouterResponse, RouterRoute
from app.utils.prompt_loader import load_prompt


MAX_ROUTER_HISTORY = 5
UNSUPPORTED_MESSAGE = (
    "That request is not supported. I can help with read-only analytics or a safe "
    "single-lead Lead 360 view."
)
PROFILE_DIAGNOSTIC_TERM_RE = re.compile(
    r"\b("
    r"profession|professions|occupation|occupations|work|job|jobs|role|roles|"
    r"employment\s+status|working\s+status|job\s+status|work\s+status|"
    r"business\s+owner|self[-\s]?employed|employee|student|trader|investor|"
    r"sales\s+or\s+marketing|technology|healthcare|retired|unemployed|"
    r"full[-\s]?time|part[-\s]?time"
    r")\b",
    re.IGNORECASE,
)
PROFILE_SQL_INTENT_RE = re.compile(
    r"\b("
    r"most\s+leads|generated\s+the\s+most|generated.*leads|"
    r"most\s+common|submitted.*opt-?ins?|opt-?ins?.*by|"
    r"trend|trends|increasing|joined|recently|"
    r"breakdown|distribution|group\s+by|how\s+many|count"
    r")\b",
    re.IGNORECASE,
)
PROFILE_DIAGNOSTIC_INTENT_RE = re.compile(
    r"\b("
    r"converts?\s+best|highest\s+paid\s+conversion|paid\s+conversion|"
    r"should\s+we|should\s+sales|focus\s+on|prioriti[sz]e|"
    r"why|not\s+converting|converting\s+better|weak\s+conversion|"
    r"high\s+volume\s+but\s+weak"
    r")\b",
    re.IGNORECASE,
)
GENERIC_TREND_DIAGNOSTIC_RE = re.compile(
    r"\b("
    r"what\s+trends\s+are\s+you\s+noticing|"
    r"what\s+are\s+the\s+current\s+trends|"
    r"what\s+business\s+trends\s+do\s+you\s+see|"
    r"what\s+is\s+changing\s+in\s+the\s+business|"
    r"what\s+looks\s+different\s+recently|"
    r"what\s+should\s+i\s+pay\s+attention\s+to\s+from\s+recent\s+trends"
    r")\b",
    re.IGNORECASE,
)
DIRECT_METRIC_TREND_RE = re.compile(
    r"\b("
    r"lead\s+trend|leads\s+trend|revenue\s+trend|appointment\s+trend|"
    r"call\s+trend|source\s+trend|profession\s+trend|employment\s+status\s+trend|"
    r"trend\s+by\s+source|trend\s+by\s+profession|trend\s+by\s+employment\s+status|"
    r"monthly\s+leads|monthly\s+revenue|monthly\s+appointments|monthly\s+calls"
    r")\b",
    re.IGNORECASE,
)
ACQUISITION_STATUS_CONVERSION_TERM_RE = re.compile(
    r"\b("
    r"won\s+leads?|won[-\s]?lead\s+rate|leads?\s+won|"
    r"current\s+lead\s+status|lead\s+status\s+breakdown"
    r")\b",
    re.IGNORECASE,
)
ACQUISITION_ATTRIBUTION_TERM_RE = re.compile(
    r"\b("
    r"utm\s+campaign|utm\s+source|utm\s+medium|landing\s+page|"
    r"provider\s+form|opt-?in\s+source|acquisition\s+source"
    r")\b",
    re.IGNORECASE,
)
UNSUPPORTED_ACQUISITION_REVENUE_TERM_RE = re.compile(
    r"\b("
    r"revenue|payment|payments|paid\s+revenue|net\s+collected|"
    r"gross\s+paid|contract\s+value|signed\s+value|amount|"
    r"roas|cost|spend"
    r")\b",
    re.IGNORECASE,
)
SQL_METRIC_FOLLOW_UP_CAUSAL_RE = re.compile(
    r"\b("
    r"why|what\s+caused|what\s+drove|explain|reason\s+for|root\s+cause|"
    r"what\s+happened|caused|drove|driver|drivers|drop|dropped|decrease|"
    r"decreased|decline|declined|fall|fell|increase|increased|rise|rose|"
    r"changed|change|weaker|stronger"
    r")\b",
    re.IGNORECASE,
)
SQL_METRIC_FOLLOW_UP_REFERENCE_RE = re.compile(
    r"\b("
    r"it|this|that|these|those|above|previous|same|metric|trend|drop|dropped|"
    r"increase|increased|decrease|decreased|revenue|payment|payments|lead|"
    r"leads|appointment|appointments|contract|contracts|count|amount|value"
    r")\b",
    re.IGNORECASE,
)
EXPLICIT_DIAGNOSTIC_BASIS_SWITCH_RE = re.compile(
    r"\b("
    r"lead[-\s]?created|lead\s+cohort|cohort|cohort\s+performance|"
    r"diagnostic|business\s+diagnosis|business\s+health|business\s+performance|"
    r"broader\s+business|across\s+the\s+business|overall\s+business|funnel|"
    r"source\s+quality|conversion|converting|conversion[-\s]?quality|"
    r"moneti[sz]ed?\s+weaker|leads?\s+moneti[sz]ed"
    r")\b",
    re.IGNORECASE,
)
SQL_METRIC_CONTEXT_RE = re.compile(
    r"\b("
    r"gross\s+paid\s+revenue|net\s+collected\s+revenue|paid\s+payment|"
    r"payment\s+date|paid_at|revenue\s+trend|lead\s+trend|lead\s+count|"
    r"appointment\s+trend|appointment\s+count|contract\s+value|"
    r"signed\s+contract|revenue|payments?|leads?|appointments?|contracts?|trend"
    r")\b",
    re.IGNORECASE,
)
SQL_ANALYTICS_SKILLS = {
    "lead_analytics",
    "appointment_analytics",
    "acquisition_analytics",
    "lead_profile_analytics",
    "revenue_analytics",
}
SQL_METRIC_COMPARISON_RE = re.compile(
    r"from\s+(?P<previous_value>[^\d\s]*[\d,]+(?:\.\d+)?)\s+in\s+"
    r"(?P<previous_period>[A-Za-z]{3,9}\s+\d{4})\s+to\s+"
    r"(?P<current_value>[^\d\s]*[\d,]+(?:\.\d+)?)\s+in\s+"
    r"(?P<current_period>[A-Za-z]{3,9}\s+\d{4})",
    re.IGNORECASE,
)


def _model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        raw = model.model_dump()
    elif hasattr(model, "dict"):
        raw = model.dict()
    else:
        raw = dict(model)
    return json.loads(
        json.dumps(
            raw,
            default=lambda value: value.value if isinstance(value, Enum) else str(value),
        )
    )


def _coerce_router_response(raw_response: Any) -> RouterResponse:
    """Validate the router output with the shared RouterResponse schema."""

    if isinstance(raw_response, RouterResponse):
        return raw_response

    if isinstance(raw_response, str):
        raw_response = json.loads(raw_response)
    elif hasattr(raw_response, "content"):
        content = getattr(raw_response, "content")
        if isinstance(content, str):
            raw_response = json.loads(content)

    if hasattr(RouterResponse, "model_validate"):
        return RouterResponse.model_validate(raw_response)
    return RouterResponse.parse_obj(raw_response)


def _is_profile_question(question: str) -> bool:
    clean_question = str(question or "").strip()
    return bool(PROFILE_DIAGNOSTIC_TERM_RE.search(clean_question))


def _should_force_profile_sql_route(question: str) -> bool:
    clean_question = str(question or "").strip()
    return bool(
        _is_profile_question(clean_question)
        and PROFILE_SQL_INTENT_RE.search(clean_question)
        and not PROFILE_DIAGNOSTIC_INTENT_RE.search(clean_question)
    )


def _should_force_profile_diagnostic_route(question: str) -> bool:
    clean_question = str(question or "").strip()
    return bool(
        _is_profile_question(clean_question)
        and PROFILE_DIAGNOSTIC_INTENT_RE.search(clean_question)
    )


def _should_force_generic_trend_diagnostic_route(question: str) -> bool:
    clean_question = str(question or "").strip()
    return bool(
        GENERIC_TREND_DIAGNOSTIC_RE.search(clean_question)
        and not DIRECT_METRIC_TREND_RE.search(clean_question)
    )


def _should_force_acquisition_status_sql_route(question: str) -> bool:
    clean_question = str(question or "").strip()
    if not clean_question:
        return False
    if UNSUPPORTED_ACQUISITION_REVENUE_TERM_RE.search(clean_question):
        return False
    return bool(
        ACQUISITION_STATUS_CONVERSION_TERM_RE.search(clean_question)
        and ACQUISITION_ATTRIBUTION_TERM_RE.search(clean_question)
    )


def _compact_context_text(value: str, limit: int = 700) -> str:
    clean_value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(clean_value) <= limit:
        return clean_value
    return clean_value[: limit - 3].rstrip() + "..."


def _is_sql_metric_follow_up(question: str) -> bool:
    clean_question = str(question or "").strip()
    if not clean_question:
        return False
    if EXPLICIT_DIAGNOSTIC_BASIS_SWITCH_RE.search(clean_question):
        return False
    return bool(
        SQL_METRIC_FOLLOW_UP_CAUSAL_RE.search(clean_question)
        and SQL_METRIC_FOLLOW_UP_REFERENCE_RE.search(clean_question)
    )


def _latest_turn_has_sql_metric_context(turn: dict[str, str]) -> bool:
    route = str(turn.get("route") or "").strip()
    selected_skill = str(turn.get("selected_skill") or "").strip()
    context = "\n".join(
        str(turn.get(key) or "")
        for key in ("question", "standalone_question", "answer")
    )

    has_sql_route = route == RouterRoute.SQL_ANALYTICS.value
    has_sql_skill = selected_skill in SQL_ANALYTICS_SKILLS
    has_metric_context = bool(SQL_METRIC_CONTEXT_RE.search(context))
    inferred_direct_metric_question = bool(
        DIRECT_METRIC_TREND_RE.search(context)
        or re.search(
            r"\b(show|what\s+is|compare)\b.*\b(count|trend|revenue|payments?)\b",
            context,
            re.IGNORECASE,
        )
    )

    return (
        has_sql_route or has_sql_skill or inferred_direct_metric_question
    ) and has_metric_context


def _movement_word(question: str, context: str) -> str:
    text = f"{question}\n{context}".lower()
    if re.search(
        r"\b(drop|dropped|decrease|decreased|decline|declined|fall|fell)\b",
        text,
    ):
        return "dropped"
    if re.search(r"\b(increase|increased|rise|rose|grew|growth)\b", text):
        return "increased"
    return "changed"


def _metric_label(context: str) -> str:
    lower_context = context.lower()
    if "gross paid" in lower_context:
        return "gross paid revenue by payment date"
    if "net collected" in lower_context:
        return "net collected revenue by payment date"
    if "paid payment" in lower_context:
        return "paid payment count by payment date"
    if "signed contract" in lower_context or "contract value" in lower_context:
        return "signed contract value by contract signed date"
    if re.search(r"\bleads?\b|\blead count\b", lower_context):
        return "lead count"
    if re.search(r"\bappointments?\b|\bbooked calls?\b|\bcalls?\b", lower_context):
        return "appointment count"
    if "revenue" in lower_context or "payment" in lower_context:
        return "revenue by payment date"
    return "the previous SQL metric"


def _basis_phrase(context: str) -> str:
    lower_context = context.lower()
    if "revenue" in lower_context or "payment" in lower_context:
        return "same revenue basis as the previous revenue trend answer"
    if re.search(r"\bleads?\b|\blead count\b", lower_context):
        return "same lead-created date basis as the previous lead trend answer"
    if re.search(r"\bappointments?\b|\bbooked calls?\b|\bcalls?\b", lower_context):
        return "same appointment timing basis as the previous appointment trend answer"
    if "contract" in lower_context:
        return "same contract timing basis as the previous contract trend answer"
    return "same SQL metric basis as the previous answer"


def _build_sql_metric_follow_up_question(
    current_question: str,
    latest_turn: dict[str, str],
) -> str:
    context = "\n".join(
        str(latest_turn.get(key) or "")
        for key in ("question", "standalone_question", "answer")
    )
    comparison = SQL_METRIC_COMPARISON_RE.search(context)
    if comparison:
        return (
            f"Explain why {_metric_label(context)} {_movement_word(current_question, context)} "
            f"from {comparison.group('previous_value')} in {comparison.group('previous_period')} "
            f"to {comparison.group('current_value')} in {comparison.group('current_period')}, "
            f"using the {_basis_phrase(context)}."
        )

    previous_question = _compact_context_text(str(latest_turn.get("question") or ""))
    previous_answer = _compact_context_text(str(latest_turn.get("answer") or ""))
    parts = [
        "Explain this follow-up using the same SQL analytics metric basis and compared periods as the previous answer.",
    ]
    if previous_question:
        parts.append(f"Previous question: {previous_question}")
    if previous_answer:
        parts.append(f"Previous answer: {previous_answer}")
    parts.append(f"Current follow-up: {current_question}")
    return " ".join(parts)


def _should_preserve_latest_sql_metric_context(
    current_question: str,
    latest_history: list[dict[str, str]],
) -> bool:
    if not latest_history or not _is_sql_metric_follow_up(current_question):
        return False
    return _latest_turn_has_sql_metric_context(latest_history[-1])


def _apply_router_overrides(
    router_response: RouterResponse,
    *,
    current_question: str,
    latest_history: list[dict[str, str]],
) -> RouterResponse:
    standalone_question = router_response.standalone_question or current_question
    override_question = "\n".join(
        part for part in (current_question, standalone_question) if part
    )

    if _should_force_acquisition_status_sql_route(override_question):
        return RouterResponse(
            route=RouterRoute.SQL_ANALYTICS,
            history_count=router_response.history_count,
            standalone_question=standalone_question,
        )

    if router_response.route in {RouterRoute.LEAD_360, RouterRoute.UNSUPPORTED}:
        return router_response

    if _should_preserve_latest_sql_metric_context(current_question, latest_history):
        return RouterResponse(
            route=RouterRoute.SQL_ANALYTICS,
            history_count=max(1, router_response.history_count),
            standalone_question=_build_sql_metric_follow_up_question(
                current_question,
                latest_history[-1],
            ),
        )
    if _should_force_generic_trend_diagnostic_route(override_question):
        return RouterResponse(
            route=RouterRoute.DIAGNOSTIC_ANALYTICS,
            history_count=router_response.history_count,
            standalone_question=standalone_question,
        )
    if _should_force_profile_diagnostic_route(override_question):
        return RouterResponse(
            route=RouterRoute.DIAGNOSTIC_ANALYTICS,
            history_count=router_response.history_count,
            standalone_question=standalone_question,
        )
    if _should_force_profile_sql_route(override_question):
        return RouterResponse(
            route=RouterRoute.SQL_ANALYTICS,
            history_count=router_response.history_count,
            standalone_question=standalone_question,
        )
    return router_response


def _turn_question(turn: Any) -> str:
    if isinstance(turn, dict):
        return str(turn.get("question") or turn.get("user_question") or turn.get("user") or "")
    return str(getattr(turn, "question", ""))


def _turn_answer(turn: Any) -> str:
    if isinstance(turn, dict):
        return str(turn.get("answer") or turn.get("assistant") or "")
    return str(getattr(turn, "answer", ""))


def _turn_optional_value(turn: Any, key: str) -> str:
    if isinstance(turn, dict):
        return str(turn.get(key) or "")
    return str(getattr(turn, key, ""))


def latest_qa_turns(chat_history: Sequence[Any], limit: int = MAX_ROUTER_HISTORY) -> list[dict[str, str]]:
    """Return normalized latest completed Q&A turns."""

    normalized: list[dict[str, str]] = []
    for turn in chat_history[-limit:]:
        question = _turn_question(turn).strip()
        answer = _turn_answer(turn).strip()
        if not question and not answer:
            continue
        normalized_turn = {"question": question, "answer": answer}
        for key in ("route", "selected_skill", "standalone_question"):
            value = _turn_optional_value(turn, key).strip()
            if value:
                normalized_turn[key] = value
        normalized.append(normalized_turn)
    return normalized


def _format_router_user_input(current_question: str, history: list[dict[str, str]]) -> str:
    if history:
        history_lines = []
        for index, turn in enumerate(history, start=1):
            turn_lines = [f"Turn {index}"]
            if turn.get("route"):
                turn_lines.append(f"Route: {turn['route']}")
            if turn.get("selected_skill"):
                turn_lines.append(f"Selected skill: {turn['selected_skill']}")
            if turn.get("standalone_question"):
                turn_lines.append(f"Standalone question: {turn['standalone_question']}")
            turn_lines.extend(
                [
                    f"User: {turn['question']}",
                    f"Assistant: {turn['answer']}",
                ]
            )
            history_lines.append("\n".join(turn_lines))
        history_text = "\n\n".join(history_lines)
    else:
        history_text = "None"

    return "\n\n".join(
        [
            "Current user question:",
            current_question,
            "Latest previous Q&A turns:",
            history_text,
        ]
    )


def build_router_messages(current_question: str, history: list[dict[str, str]]) -> list[Any]:
    """Build messages for the routing model."""

    system_prompt = load_prompt("router").system
    user_input = _format_router_user_input(current_question, history)

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]
    except ModuleNotFoundError:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]


def _invoke_component(component: Any, payload: Any, *, config: dict[str, Any] | None = None) -> Any:
    if callable(component) and not hasattr(component, "invoke"):
        return component(payload)

    if config is None:
        return component.invoke(payload)

    try:
        return component.invoke(payload, config=config)
    except TypeError:
        return component.invoke(payload)


def _emit_progress(
    progress_callback: Callable[[dict[str, Any]], None] | None,
    *,
    stage: str,
    message: str,
    route: str | None = None,
) -> None:
    if progress_callback is None:
        return

    try:
        progress_callback(
            {
                "stage": stage,
                "message": message,
                "route": route,
            }
        )
    except Exception:
        return


def _router_model_kwargs() -> dict[str, Any]:
    from app.config import get_sql_agent_settings

    settings = get_sql_agent_settings()
    model_kwargs: dict[str, Any] = {}
    if settings.reasoning:
        model_kwargs["reasoning"] = settings.reasoning
    if settings.service_tier:
        model_kwargs["service_tier"] = settings.service_tier
    return model_kwargs


def create_default_router():
    """Create the structured-output router used before every downstream flow."""

    from app.config import ensure_openai_key, get_sql_agent_settings

    ensure_openai_key()
    from langchain.chat_models import init_chat_model

    settings = get_sql_agent_settings()
    model = init_chat_model(settings.model, **_router_model_kwargs())
    return model.with_structured_output(RouterResponse)


def create_default_sql_agent():
    """Create the SQL analytics flow without exposing it to callers directly."""

    from app.agents.sql_agent import create_sql_agent

    return create_sql_agent()


def create_default_lead_360_agent():
    """Create the Lead 360 flow without exposing it to callers directly."""

    from app.agents.lead_360 import create_lead_360_agent

    return create_lead_360_agent()


def create_default_diagnostic_agent():
    """Create the Diagnostic Analytics flow without exposing it to callers directly."""

    from app.agents.diagnostic_agent import create_diagnostic_agent

    return create_diagnostic_agent()


def route_question(
    current_question: str,
    chat_history: Sequence[Any],
    *,
    router: Any | None = None,
    config: dict[str, Any] | None = None,
) -> tuple[RouterResponse, list[dict[str, str]]]:
    """Route a question using the latest five Q&A turns."""

    history = latest_qa_turns(chat_history, MAX_ROUTER_HISTORY)
    router_messages = build_router_messages(current_question, history)
    effective_router = router or create_default_router()
    raw_response = _invoke_component(effective_router, router_messages, config=config)
    router_response = _coerce_router_response(raw_response)
    return _apply_router_overrides(
        router_response,
        current_question=current_question,
        latest_history=history,
    ), history


def selected_history_for_route(
    router_response: RouterResponse,
    latest_history: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Apply router.history_count to the latest router-visible history."""

    history_count = min(router_response.history_count, len(latest_history))
    if history_count <= 0:
        return []
    return latest_history[-history_count:]


def build_downstream_messages(
    standalone_question: str,
    selected_history: list[dict[str, str]],
    runtime_context: str | None = None,
) -> list[dict[str, str]]:
    """Build the exact message window allowed for the selected downstream flow."""

    messages: list[dict[str, str]] = []
    for turn in selected_history:
        messages.extend(
            [
                {"role": "user", "content": turn["question"]},
                {"role": "assistant", "content": turn["answer"]},
            ]
        )
    if runtime_context:
        messages.append({"role": "system", "content": runtime_context})
    messages.append({"role": "user", "content": standalone_question})
    return messages


def _message_role(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("role") or message.get("type") or "")
    return str(getattr(message, "type", message.__class__.__name__))


def _message_content(message: Any) -> str:
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")

    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def final_answer_from(messages: Sequence[Any]) -> str:
    """Return the last assistant/AI text from a downstream agent result."""

    for message in reversed(messages):
        role = _message_role(message).lower()
        if role not in {"ai", "assistant"}:
            continue
        content = _message_content(message).strip()
        if content:
            return content
    return "No final answer was returned."


def _invoke_downstream_agent(
    agent: Any,
    messages: list[dict[str, str]],
    *,
    config: dict[str, Any] | None = None,
) -> tuple[str, list[Any], list[Any]]:
    result = _invoke_component(agent, {"messages": messages}, config=config)
    all_messages = list(result.get("messages", [])) if isinstance(result, dict) else []
    context_message_count = max(0, len(messages) - 1)
    trace_messages = (
        all_messages[context_message_count:]
        if context_message_count < len(all_messages)
        else all_messages
    )
    answer = final_answer_from(trace_messages) or final_answer_from(all_messages)
    return answer, trace_messages, all_messages


def _static_turn(
    *,
    current_question: str,
    router_response: RouterResponse,
    latest_history: list[dict[str, str]],
    selected_history: list[dict[str, str]],
    answer: str,
) -> dict[str, Any]:
    return {
        "question": current_question,
        "standalone_question": router_response.standalone_question,
        "answer": answer,
        "route": router_response.route.value,
        "router_response": _model_dump(router_response),
        "latest_router_history": latest_history,
        "selected_history": selected_history,
        "trace_messages": [],
        "all_messages": [],
        "context_turn_count": len(selected_history),
    }


def answer_user_question(
    current_question: str,
    chat_history: Sequence[Any],
    *,
    router: Any | None = None,
    sql_agent: Any | None = None,
    lead_360_agent: Any | None = None,
    diagnostic_agent: Any | None = None,
    config: dict[str, Any] | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
    sql_agent_factory: Callable[[], Any] = create_default_sql_agent,
    lead_360_agent_factory: Callable[[], Any] = create_default_lead_360_agent,
    diagnostic_agent_factory: Callable[[], Any] = create_default_diagnostic_agent,
    runtime_context: str | None = None,
) -> dict[str, Any]:
    """Route first, then dispatch to exactly one allowed downstream flow."""

    _emit_progress(
        progress_callback,
        stage="routing",
        message="Checking whether this is SQL analytics, Lead 360, or diagnostic analytics...",
    )
    router_response, latest_history = route_question(
        current_question,
        chat_history,
        router=router,
        config=config,
    )
    selected_history = selected_history_for_route(router_response, latest_history)
    route_value = router_response.route.value

    _emit_progress(
        progress_callback,
        stage="route_selected",
        message=f"Route selected: {route_value.replace('_', ' ')}.",
        route=route_value,
    )

    if router_response.route == RouterRoute.UNSUPPORTED:
        _emit_progress(
            progress_callback,
            stage="unsupported",
            message="Preparing a safe response for an unsupported request...",
            route=route_value,
        )
        return _static_turn(
            current_question=current_question,
            router_response=router_response,
            latest_history=latest_history,
            selected_history=selected_history,
            answer=UNSUPPORTED_MESSAGE,
        )

    messages = build_downstream_messages(
        router_response.standalone_question,
        selected_history,
        runtime_context=runtime_context,
    )

    if router_response.route == RouterRoute.SQL_ANALYTICS:
        _emit_progress(
            progress_callback,
            stage="flow_start",
            message="Loading the SQL analytics flow...",
            route=route_value,
        )
        effective_agent = sql_agent or sql_agent_factory()
    elif router_response.route == RouterRoute.LEAD_360:
        _emit_progress(
            progress_callback,
            stage="flow_start",
            message="Loading the Lead 360 flow...",
            route=route_value,
        )
        effective_agent = lead_360_agent or lead_360_agent_factory()
    elif router_response.route == RouterRoute.DIAGNOSTIC_ANALYTICS:
        _emit_progress(
            progress_callback,
            stage="flow_start",
            message="Loading the diagnostic analytics flow...",
            route=route_value,
        )
        effective_agent = diagnostic_agent or diagnostic_agent_factory()
    else:
        _emit_progress(
            progress_callback,
            stage="unsupported",
            message="Preparing a safe response for an unsupported request...",
            route=route_value,
        )
        return _static_turn(
            current_question=current_question,
            router_response=router_response,
            latest_history=latest_history,
            selected_history=selected_history,
            answer=UNSUPPORTED_MESSAGE,
        )

    _emit_progress(
        progress_callback,
        stage="flow_running",
        message="Running the selected flow with the approved tools...",
        route=route_value,
    )
    answer, trace_messages, all_messages = _invoke_downstream_agent(
        effective_agent,
        messages,
        config=config,
    )
    _emit_progress(
        progress_callback,
        stage="answer_ready",
        message="Preparing the final answer...",
        route=route_value,
    )
    return {
        "question": current_question,
        "standalone_question": router_response.standalone_question,
        "answer": answer,
        "route": router_response.route.value,
        "router_response": _model_dump(router_response),
        "latest_router_history": latest_history,
        "selected_history": selected_history,
        "trace_messages": trace_messages,
        "all_messages": all_messages,
        "context_turn_count": len(selected_history),
    }
