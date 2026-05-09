"""Streamlit UI for the Hermon SQL analytics agent.

Run from the project root:

    streamlit run app/ui/streamlit_app.py
"""

from __future__ import annotations

import base64
import csv
import html
import inspect
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_sql_agent_settings, load_app_config  # noqa: E402
from app.orchestrator import (  # noqa: E402
    answer_user_question,
    create_default_lead_360_agent,
    create_default_router,
    create_default_sql_agent,
)
from app.poc_chat_history import (  # noqa: E402
    clear_poc_chat_history,
    fetch_latest_poc_chat_history,
    fetch_router_poc_chat_history,
    insert_poc_chat_history,
)
from app.utils.skill_loader import list_skill_metadata  # noqa: E402
from langchain_core.callbacks import BaseCallbackHandler  # noqa: E402


TESTING_DIR = PROJECT_ROOT / "app" / "testing"
CONFIG_PATH = PROJECT_ROOT / "app" / "config" / "config.yaml"
SQL_AGENT_PROMPT_PATH = PROJECT_ROOT / "app" / "prompts" / "sql_agent" / "1_0_0.yaml"
ROUTER_PROMPT_PATH = PROJECT_ROOT / "app" / "prompts" / "router.md"
LEAD_360_PROMPT_PATH = PROJECT_ROOT / "app" / "skills" / "modules" / "lead_360.md"
TESTING_INPUT_DIR = TESTING_DIR / "input"
ACQUISITION_INPUT_QUESTIONS_PATH = (
    TESTING_INPUT_DIR / "acquisition_analytics_clean_test_questions.csv"
)
APPOINTMENT_INPUT_QUESTIONS_PATH = (
    TESTING_INPUT_DIR / "appointment_analytics_clean_test_questions.csv"
)
LEAD_INPUT_QUESTIONS_PATH = TESTING_INPUT_DIR / "lead_analytics_clean_test_questions.csv"
LEAD_360_INPUT_QUESTIONS_PATH = TESTING_INPUT_DIR / "lead_360_clean_test_questions.csv"
REVENUE_INPUT_QUESTIONS_PATH = TESTING_INPUT_DIR / "revenue_analytics_clean_test_questions.csv"
BOT_LOGO_PATH = PROJECT_ROOT / "app" / "ui" / "assets" / "hermon_bot.svg"
PAGE_TITLE = "Hermon Q&A Agent"
PAGE_ICON = str(BOT_LOGO_PATH)
LAYOUT = "wide"
AGENT_CACHE_VERSION = "router-first-v1"
COMPACT_TABLE_MAX_COLUMNS = 8
COMPACT_TABLE_MAX_ROWS = 30
MAX_CONTEXT_TURNS = 5
POC_FALLBACK_ORG_ID = "local_demo"

SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*.*?```", re.IGNORECASE | re.DOTALL)
STRINGIFIED_REASONING_BLOCK_RE = re.compile(
    r"^\s*\{[^{}]*['\"]type['\"]:\s*['\"]reasoning['\"][^{}]*\}\s*",
    re.IGNORECASE,
)
IGNORED_CONTENT_BLOCK_TYPES = {"reasoning", "function_call", "tool_call"}
SECTION_LABELS_TO_STRIP = {
    "query",
    "query used",
    "raw rows",
    "raw tool json",
    "source data",
    "sql",
    "sql query",
    "sql used",
    "the sql query used",
    "tool output",
}
QUESTION_PICKER_CONFIGS: tuple[dict[str, Any], ...] = (
    {
        "key": "lead_analytics",
        "title": "Lead Analytics",
        "selectbox_label": "Lead Analytics coverage",
        "placeholder": "Choose a supported Lead Analytics question",
        "path": LEAD_INPUT_QUESTIONS_PATH,
    },
    {
        "key": "lead_360",
        "title": "Lead 360",
        "selectbox_label": "Lead 360 coverage",
        "placeholder": "Choose a supported Lead 360 question",
        "path": LEAD_360_INPUT_QUESTIONS_PATH,
    },
    {
        "key": "appointment_analytics",
        "title": "Appointment Analytics",
        "selectbox_label": "Appointment Analytics coverage",
        "placeholder": "Choose a supported Appointment Analytics question",
        "path": APPOINTMENT_INPUT_QUESTIONS_PATH,
    },
    {
        "key": "acquisition_analytics",
        "title": "Acquisition Analytics",
        "selectbox_label": "Acquisition Analytics coverage",
        "placeholder": "Choose a supported Acquisition Analytics question",
        "path": ACQUISITION_INPUT_QUESTIONS_PATH,
    },
    {
        "key": "revenue_analytics",
        "title": "Revenue Analytics",
        "selectbox_label": "Revenue Analytics coverage",
        "placeholder": "Choose a supported Revenue Analytics question",
        "path": REVENUE_INPUT_QUESTIONS_PATH,
    },
)


def init_state() -> None:
    organization_id = current_organization_id()
    if st.session_state.get("history_organization_id") != organization_id:
        st.session_state.history_organization_id = organization_id
        st.session_state.turns = load_poc_display_turns(organization_id)
        return
    if "turns" not in st.session_state:
        st.session_state.turns = load_poc_display_turns(organization_id)
        return
    prune_turn_history()


def prune_turn_history() -> None:
    st.session_state.turns = [
        turn
        for turn in st.session_state.turns
        if not is_persistence_error_turn(turn)
    ][-MAX_CONTEXT_TURNS:]


def is_persistence_error_turn(turn: dict[str, Any]) -> bool:
    answer = str(turn.get("answer") or "")
    return (
        "insert_poc_chat_history()" in answer
        and "unexpected keyword argument 'elapsed_seconds'" in answer
    )


def current_organization_id() -> str:
    settings = get_sql_agent_settings()
    return settings.default_org_id or POC_FALLBACK_ORG_ID


def turn_from_poc_row(row: dict[str, Any]) -> dict[str, Any]:
    generated_sql = row.get("generated_sql")
    execution_details = row.get("execution_details")
    if not isinstance(execution_details, dict):
        execution_details = {
            "sql": generated_sql,
            "selected_skill": row.get("selected_skill"),
            "params": None,
            "effective_params": None,
            "rows": None,
            "row_count": None,
            "tool_error": None,
        }

    timing = row.get("timing")
    if not isinstance(timing, dict):
        timing = None

    lead_360_diagnostics = row.get("lead_360_diagnostics")
    if not isinstance(lead_360_diagnostics, dict):
        lead_360_diagnostics = None

    return {
        "question": str(row.get("user_question") or ""),
        "answer": str(row.get("answer") or ""),
        "standalone_question": row.get("standalone_question"),
        "route": row.get("route"),
        "selected_skill": row.get("selected_skill"),
        "generated_sql": generated_sql,
        "organization_id": row.get("organization_id"),
        "created_at": row.get("created_at"),
        "elapsed_seconds": row.get("elapsed_seconds"),
        "timing": timing,
        "lead_360_diagnostics": lead_360_diagnostics,
        "trace_messages": [],
        "all_messages": [],
        "context_turn_count": 0,
        "execution_details": execution_details,
    }


def load_poc_display_turns(organization_id: str) -> list[dict[str, Any]]:
    rows = fetch_latest_poc_chat_history(organization_id)
    return [turn_from_poc_row(row) for row in reversed(rows)]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .hero-wrap {
            display: flex;
            align-items: center;
            gap: 1.15rem;
            margin: 0.45rem 0 1.55rem 0;
            padding: 1rem 0 0.2rem 0;
        }

        .hero-logo {
            width: 5.25rem;
            height: 5.25rem;
            flex: 0 0 auto;
            border: 1px solid rgba(96, 165, 250, 0.28);
            border-radius: 8px;
            background: rgba(30, 64, 175, 0.22);
            box-shadow:
                0 20px 48px rgba(37, 99, 235, 0.18),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
            display: grid;
            place-items: center;
        }

        .hero-logo img {
            width: 4.35rem;
            height: 4.35rem;
            display: block;
        }

        .hero-title {
            margin: 0;
            color: inherit;
            font-size: 3.35rem;
            font-weight: 850;
            letter-spacing: 0;
            line-height: 1.02;
        }

        .hero-copy {
            max-width: 48rem;
            margin-top: 0.5rem;
            color: inherit;
            font-size: 0.98rem;
            line-height: 1.48;
            opacity: 0.68;
        }

        .sidebar-module-card {
            margin: 0.5rem 0;
            padding: 0.82rem;
            border: 1px solid var(--module-border);
            border-radius: 8px;
            background:
                linear-gradient(135deg, var(--module-glow), rgba(255, 255, 255, 0.025)),
                rgba(15, 23, 42, 0.16);
            display: flex;
            align-items: flex-start;
            gap: 0.72rem;
        }

        .sidebar-module-card.skill {
            --module-border: rgba(251, 191, 36, 0.36);
            --module-glow: rgba(251, 191, 36, 0.14);
            --icon-bg: rgba(251, 191, 36, 0.16);
            --icon-border: rgba(251, 191, 36, 0.42);
            --accent: #fbbf24;
        }

        .sidebar-module-card.llm {
            --module-border: rgba(129, 140, 248, 0.36);
            --module-glow: rgba(129, 140, 248, 0.14);
            --icon-bg: rgba(129, 140, 248, 0.16);
            --icon-border: rgba(129, 140, 248, 0.42);
            --accent: #818cf8;
        }

        .sidebar-module-card.memory {
            --module-border: rgba(45, 212, 191, 0.34);
            --module-glow: rgba(45, 212, 191, 0.13);
            --icon-bg: rgba(45, 212, 191, 0.15);
            --icon-border: rgba(45, 212, 191, 0.4);
            --accent: #2dd4bf;
        }

        .sidebar-module-icon {
            width: 2.55rem;
            height: 2.55rem;
            flex: 0 0 auto;
            border: 1px solid var(--icon-border);
            border-radius: 8px;
            background: var(--icon-bg);
            display: grid;
            place-items: center;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }

        .sidebar-module-icon svg {
            width: 2rem;
            height: 2rem;
        }

        .sidebar-module-label {
            color: inherit;
            opacity: 0.58;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0;
            line-height: 1.2;
            margin-bottom: 0.16rem;
            text-transform: uppercase;
        }

        .sidebar-module-title {
            color: inherit;
            opacity: 0.96;
            font-size: 1rem;
            font-weight: 790;
            line-height: 1.2;
            margin-bottom: 0.28rem;
        }

        .sidebar-module-copy {
            color: inherit;
            opacity: 0.64;
            font-size: 0.84rem;
            line-height: 1.38;
        }

        .compact-table-wrap {
            margin: 0.35rem 0 1rem 0;
            overflow-x: auto;
            max-width: 100%;
            padding-bottom: 0.05rem;
        }

        table.compact-result-table {
            border-collapse: separate;
            border-spacing: 0;
            width: auto;
            max-width: 100%;
            display: inline-table;
            border: 1px solid color-mix(in srgb, currentColor 18%, transparent);
            border-radius: 8px;
            overflow: hidden;
            background: color-mix(in srgb, currentColor 2%, transparent);
            font-size: 0.92rem;
        }

        table.compact-result-table th,
        table.compact-result-table td {
            padding: 0.5rem 0.8rem;
            border-bottom: 1px solid color-mix(in srgb, currentColor 12%, transparent);
            color: inherit;
            white-space: nowrap;
            vertical-align: top;
        }

        table.compact-result-table th {
            color: inherit;
            opacity: 0.72;
            background: color-mix(in srgb, currentColor 5%, transparent);
            font-weight: 600;
            text-align: left;
        }

        table.compact-result-table tr:last-child td {
            border-bottom: none;
        }

        table.compact-result-table td.numeric-cell {
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        .reference-intro {
            margin: 0.85rem 0 0.45rem 0;
            padding: 0.65rem 0.8rem;
            border-left: 3px solid rgba(148, 163, 184, 0.75);
            border-radius: 8px;
            background: rgba(148, 163, 184, 0.08);
        }

        .reference-title {
            color: inherit;
            opacity: 0.92;
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0;
            margin-bottom: 0.12rem;
        }

        .reference-copy {
            color: inherit;
            opacity: 0.62;
            font-size: 0.84rem;
            line-height: 1.35;
        }

        div[data-testid="stChatInput"] {
            min-height: 3rem !important;
        }

        div[data-testid="stChatInput"] > div,
        div[data-testid="stChatInput"] [data-baseweb="textarea"] {
            min-height: 2.75rem !important;
            height: 2.75rem !important;
        }

        div[data-testid="stChatInput"] textarea {
            min-height: 2.75rem !important;
            height: 2.75rem !important;
            max-height: 2.75rem !important;
            padding-top: 0.72rem !important;
            padding-bottom: 0.72rem !important;
            resize: none !important;
            overflow-y: hidden !important;
        }

        @media (max-width: 720px) {
            .hero-wrap {
                align-items: flex-start;
                gap: 0.9rem;
            }

            .hero-logo {
                width: 4.25rem;
                height: 4.25rem;
            }

            .hero-logo img {
                width: 3.45rem;
                height: 3.45rem;
            }

            .hero-title {
                font-size: 2.35rem;
            }

            .hero-copy {
                font-size: 0.93rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_flow_components(
    cache_version: str = AGENT_CACHE_VERSION,
    config_mtime_ns: int = 0,
    prompt_mtime_ns: int = 0,
    router_prompt_mtime_ns: int = 0,
    lead_360_prompt_mtime_ns: int = 0,
):
    _ = cache_version
    _ = config_mtime_ns
    _ = prompt_mtime_ns
    _ = router_prompt_mtime_ns
    _ = lead_360_prompt_mtime_ns
    load_app_config.cache_clear()
    return {
        "router": create_default_router(),
        "sql_agent": create_default_sql_agent(),
        "lead_360_agent": create_default_lead_360_agent(),
    }


@st.cache_data(show_spinner=False)
def load_question_matrix() -> dict[str, Any]:
    """Load tested analytics questions from evaluation CSV inputs."""

    return {
        config["key"]: load_questions_from_paths(
            [config["path"]],
            default_category=config["title"],
        )
        for config in QUESTION_PICKER_CONFIGS
    }


def load_questions_from_paths(
    candidate_paths: list[Path],
    *,
    default_category: str,
) -> dict[str, Any]:
    for path in candidate_paths:
        if not path.exists():
            continue

        questions: list[dict[str, str]] = []
        with path.open("r", encoding="utf-8", newline="") as question_file:
            reader = csv.DictReader(question_file)
            for index, row in enumerate(reader, start=1):
                question = (row.get("question") or "").strip()
                if not question:
                    continue

                questions.append(
                    {
                        "id": (row.get("question_id") or f"Q{index:03d}").strip(),
                        "category": (row.get("category") or default_category).strip(),
                        "question": question,
                    }
                )

        return {
            "questions": questions,
            "source_file": path.name,
        }

    return {"questions": [], "source_file": ""}


def stringify_content_block(item: Any) -> str:
    if isinstance(item, dict):
        block_type = str(item.get("type", "")).lower()
        if block_type in IGNORED_CONTENT_BLOCK_TYPES:
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
    return str(getattr(message, "type", message.__class__.__name__))


def message_name(message: object) -> str | None:
    name = getattr(message, "name", None)
    return str(name) if name else None


def message_content(message: object) -> str:
    return stringify_content(getattr(message, "content", ""))


def safe_json(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def maybe_json(value: str) -> Any | None:
    try:
        return json.loads(value)
    except Exception:
        return None


def effective_runtime_params(params_json: str | None) -> dict[str, Any] | None:
    parsed_params = maybe_json(params_json or "{}")
    if not isinstance(parsed_params, dict):
        return None

    settings = get_sql_agent_settings()
    params = dict(parsed_params)
    if settings.default_org_id:
        params.setdefault("org_id", settings.default_org_id)
    params.setdefault("limit", settings.max_tool_rows)
    return params


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.2f} sec"
    minutes, remainder = divmod(seconds, 60)
    return f"{int(minutes)} min {remainder:.1f} sec"


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
    """Collect per-model and per-tool timings for one Streamlit turn."""

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

    def _finish(self, run_id: Any, *, status: str, error: BaseException | None = None) -> None:
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

    def on_llm_error(self, error: BaseException, *, run_id: Any, **kwargs: Any) -> None:
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

    def on_tool_error(self, error: BaseException, *, run_id: Any, **kwargs: Any) -> None:
        self._finish(run_id, status="error", error=error)


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


def readable_skill_name(skill_name: str) -> str:
    return skill_name.replace("_", " ").title()


def enabled_skill_summary(enabled_skills: tuple[str, ...]) -> str:
    enabled = set(enabled_skills)
    names = [
        readable_skill_name(skill.name)
        for skill in list_skill_metadata(allowed_skill_names=enabled)
    ]
    names.append("Lead 360")
    return ", ".join(names) if names else "No enabled skills"


def count_tool_calls(messages: list[object]) -> int:
    total = 0
    for message in messages:
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            total += len(tool_calls)
    return total


def extract_execution_details(messages: list[object]) -> dict[str, Any]:
    """Pull the user-facing SQL and result rows out of the agent trace."""

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
                        details["effective_params"] = effective_runtime_params(details["params"])
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


def normalize_heading_line(line: str) -> str:
    normalized = line.strip()
    normalized = re.sub(r"^\s{0,3}#{1,6}\s*", "", normalized)
    normalized = normalized.strip("*_`#:- \t")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def is_noise_section_heading(line: str) -> bool:
    return normalize_heading_line(line) in SECTION_LABELS_TO_STRIP


def clean_answer_for_display(answer: str) -> str:
    """Remove technical SQL/tool sections while preserving the business answer."""

    while True:
        cleaned_answer = STRINGIFIED_REASONING_BLOCK_RE.sub("", answer, count=1)
        if cleaned_answer == answer:
            break
        answer = cleaned_answer

    cleaned = SQL_FENCE_RE.sub("", answer)

    lines = []
    for line in cleaned.splitlines():
        if is_noise_section_heading(line):
            break
        lines.append(line.rstrip())

    cleaned = "\n".join(lines)

    lines = [line.rstrip() for line in cleaned.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines).strip() or "Here is the result."


def render_sql_dropdown(details: dict[str, Any]) -> None:
    sql = details.get("sql")
    params = details.get("params")
    effective_params = details.get("effective_params")
    tool_error = details.get("tool_error")

    with st.expander("SQL used", expanded=False):
        if sql:
            st.code(sql, language="sql")
        elif not tool_error:
            st.info("SQL was not captured for this turn.")
        if isinstance(effective_params, dict):
            st.caption("Parameters")
            st.json(effective_params, expanded=False)
        elif params:
            parsed_params = maybe_json(str(params))
            st.caption("Parameters")
            if parsed_params is not None:
                st.json(parsed_params, expanded=False)
            else:
                st.code(str(params), language="json")
        if tool_error:
            st.error(tool_error)


def render_source_data_dropdown(details: dict[str, Any]) -> None:
    rows = details.get("rows")
    if not isinstance(rows, list):
        with st.expander("Source data - unavailable", expanded=False):
            st.info(
                "Source rows were not captured for this turn. New SQL turns will keep "
                "the source rows available until they are pruned from the latest chat history."
            )
        return

    row_count = details.get("row_count")
    if not isinstance(row_count, int):
        row_count = len(rows)
    row_label = "row" if row_count == 1 else "rows"

    with st.expander(f"Source data - {row_count} {row_label}", expanded=False):
        st.markdown(
            "These are the exact database rows returned by the read-only SQL query. "
            "The chatbot summarizes these rows into the answer above; use this table "
            "to verify the numbers and labels."
        )
        render_result_table(rows)


def render_answer_block(clean_answer: str) -> None:
    with st.container(border=True):
        st.markdown(clean_answer)


def render_reference_intro(turn: dict[str, Any]) -> None:
    elapsed = format_duration(turn.get("elapsed_seconds"))
    st.markdown(
        f"""
        <div class="reference-intro">
            <div class="reference-title">Reference only</div>
            <div class="reference-copy">
                Source rows, SQL, and process trace are shown here for verification
                and debugging. They are separate from the business answer above.
                Completed in {html.escape(elapsed)}.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_timing_breakdown(turn: dict[str, Any]) -> None:
    timing = turn.get("timing")
    if not isinstance(timing, dict):
        with st.expander("Timing breakdown", expanded=False):
            st.info("Timing was not captured for this turn.")
        return

    events = timing.get("events")
    if not isinstance(events, list):
        with st.expander("Timing breakdown", expanded=False):
            st.info("Timing was not captured for this turn.")
        return

    with st.expander("Timing breakdown", expanded=False):
        columns = st.columns(4)
        columns[0].metric(
            "Classification",
            format_duration(timing.get("classification_seconds")),
        )
        columns[1].metric(
            "Tool response",
            format_duration(timing.get("tool_seconds")),
        )
        columns[2].metric(
            "Final answer",
            format_duration(timing.get("final_answer_seconds")),
        )
        columns[3].metric(
            "Other overhead",
            format_duration(timing.get("overhead_seconds")),
        )

        if not events:
            st.info("No model/tool timing events were captured for this turn.")
            render_lead_360_tool_timing(turn.get("lead_360_diagnostics"))
            return

        rows = []
        for index, event in enumerate(events, start=1):
            rows.append(
                {
                    "step": index,
                    "stage": event.get("stage") or event.get("name") or "unknown",
                    "kind": event.get("kind") or "unknown",
                    "duration": format_duration(event.get("duration_seconds")),
                    "status": event.get("status") or "unknown",
                }
            )
        render_compact_table(rows)
        render_lead_360_tool_timing(turn.get("lead_360_diagnostics"))


def readable_timing_label(value: Any) -> str:
    return str(value or "unknown").replace("_", " ").title()


def format_timing_details(details: Any) -> str:
    if not isinstance(details, dict) or not details:
        return "-"
    parts = []
    for key, value in details.items():
        parts.append(f"{str(key).replace('_', ' ')}: {value}")
    return ", ".join(parts)


def render_lead_360_tool_timing(diagnostics: Any) -> None:
    if not isinstance(diagnostics, dict):
        return

    timings = diagnostics.get("timings")
    if not isinstance(timings, dict):
        return

    events = timings.get("events")
    if not isinstance(events, list) or not events:
        return

    st.markdown("**Lead 360 tool sections**")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Tool internal total", format_duration(timings.get("total_seconds")))
    query_wall_time = next(
        (
            event.get("duration_seconds")
            for event in events
            if event.get("section") == "section_queries"
            and event.get("subsection") == "parallel_wall_time"
        ),
        None,
    )
    metric_columns[1].metric("Section query wall time", format_duration(query_wall_time))
    slowest_query = timings.get("slowest_query")
    slowest_label = "-"
    slowest_duration = None
    if isinstance(slowest_query, dict):
        slowest_label = readable_timing_label(slowest_query.get("subsection"))
        slowest_duration = slowest_query.get("duration_seconds")
    metric_columns[2].metric("Slowest section", slowest_label)
    metric_columns[3].metric("Slowest time", format_duration(slowest_duration))

    section_order = [
        "lead_resolution",
        "lead_context",
        "section_queries",
        "context_assembly",
        "lead_360_tool",
    ]
    ordered_sections = [
        section for section in section_order if any(event.get("section") == section for event in events)
    ]
    ordered_sections.extend(
        section
        for section in sorted({str(event.get("section")) for event in events})
        if section not in ordered_sections
    )

    for section in ordered_sections:
        rows = []
        for event in events:
            if event.get("section") != section:
                continue
            rows.append(
                {
                    "section": readable_timing_label(section),
                    "subsection": readable_timing_label(event.get("subsection")),
                    "duration": format_duration(event.get("duration_seconds")),
                    "status": event.get("status") or "unknown",
                    "details": format_timing_details(event.get("details")),
                }
            )
        if rows:
            st.caption(readable_timing_label(section))
            render_compact_table(rows)


def is_numeric_value(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def format_table_value(value: Any) -> str:
    if value is None:
        return "—"
    return str(value)


def render_compact_table(rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0].keys())
    numeric_columns = {
        column
        for column in columns
        if any(row.get(column) is not None for row in rows)
        and all(
            row.get(column) is None or is_numeric_value(row.get(column))
            for row in rows
        )
    }

    header_cells = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body_rows = []
    for row in rows:
        cells = []
        for column in columns:
            cell_class = ' class="numeric-cell"' if column in numeric_columns else ""
            value = html.escape(format_table_value(row.get(column)))
            cells.append(f"<td{cell_class}>{value}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_html = (
        '<div class="compact-table-wrap">'
        '<table class="compact-result-table">'
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_result_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        st.info("The SQL returned zero rows.")
        return

    column_count = len(rows[0])
    if len(rows) <= COMPACT_TABLE_MAX_ROWS and column_count <= COMPACT_TABLE_MAX_COLUMNS:
        render_compact_table(rows)
        return

    st.dataframe(rows, width="stretch", hide_index=True)


def message_to_dict(message: object) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        return safe_json(message.model_dump())
    if hasattr(message, "dict"):
        return safe_json(message.dict())
    return {
        "type": message_role(message),
        "name": message_name(message),
        "content": message_content(message),
        "tool_calls": safe_json(getattr(message, "tool_calls", None)),
    }


def final_answer_from(messages: list[object]) -> str:
    for message in reversed(messages):
        if message_role(message) == "ai":
            content = message_content(message).strip()
            if content:
                return content
    return "No final answer was returned."


def persist_poc_turn(**kwargs: Any) -> None:
    """Save chat history without letting persistence break the visible answer."""

    try:
        supported_kwargs = inspect.signature(insert_poc_chat_history).parameters
        insert_poc_chat_history(
            **{
                key: value
                for key, value in kwargs.items()
                if key in supported_kwargs
            }
        )
    except Exception:
        return


def run_question(question: str) -> dict[str, Any]:
    organization_id = current_organization_id()
    poc_history = fetch_router_poc_chat_history(organization_id)
    components = get_flow_components(
        config_mtime_ns=CONFIG_PATH.stat().st_mtime_ns,
        prompt_mtime_ns=SQL_AGENT_PROMPT_PATH.stat().st_mtime_ns,
        router_prompt_mtime_ns=ROUTER_PROMPT_PATH.stat().st_mtime_ns,
        lead_360_prompt_mtime_ns=LEAD_360_PROMPT_PATH.stat().st_mtime_ns,
    )
    timing_callback = AgentTimingCallback()
    started_at = time.perf_counter()
    turn = answer_user_question(
        question,
        poc_history,
        router=components["router"],
        sql_agent=components["sql_agent"],
        lead_360_agent=components["lead_360_agent"],
        config={"callbacks": [timing_callback]},
    )
    elapsed_seconds = time.perf_counter() - started_at

    trace_messages = list(turn.get("trace_messages", []))
    all_messages = list(turn.get("all_messages", []))
    answer = str(turn.get("answer") or final_answer_from(trace_messages) or final_answer_from(all_messages))
    execution_details = extract_execution_details(trace_messages)
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

    persist_poc_turn(
        organization_id=organization_id,
        route=route,
        selected_skill=selected_skill,
        user_question=question,
        standalone_question=str(turn.get("standalone_question") or "") or None,
        generated_sql=generated_sql,
        answer=answer,
        elapsed_seconds=elapsed_seconds,
        execution_details=safe_json(execution_details),
        timing=safe_json(timing),
        lead_360_diagnostics=safe_json(lead_360_diagnostics),
    )

    return {
        "question": question,
        "answer": answer,
        "standalone_question": turn.get("standalone_question", question),
        "route": route,
        "router_response": turn.get("router_response"),
        "organization_id": organization_id,
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


def render_tool_call(tool_call: dict[str, Any], index: int) -> None:
    name = tool_call.get("name", "unknown_tool")
    args = tool_call.get("args") or {}

    with st.container(border=True):
        st.markdown(f"**{index}. AI requested tool:** `{name}`")

        if not isinstance(args, dict):
            st.json(safe_json(args), expanded=False)
            return

        query = args.get("query")
        params_json = args.get("params_json")
        skill_name = args.get("skill_name")

        if skill_name:
            st.markdown(f"Skill requested: `{skill_name}`")

        if query:
            st.caption("SQL sent to tool")
            st.code(str(query).strip(), language="sql")

        if params_json:
            st.caption("Tool parameters")
            parsed_params = maybe_json(str(params_json))
            if parsed_params is not None:
                st.json(parsed_params, expanded=False)
            else:
                st.code(str(params_json), language="json")

        remaining_args = {
            key: value
            for key, value in args.items()
            if key not in {"query", "params_json", "skill_name"}
        }
        if remaining_args:
            st.caption("Other tool arguments")
            st.json(safe_json(remaining_args), expanded=False)


def render_loaded_skill(content: str) -> None:
    first_line, _, markdown_body = content.partition("\n\n")
    st.success(first_line.strip() or "Skill loaded")
    if markdown_body.strip():
        st.caption("Rendered skill instructions")
        st.markdown(markdown_body)


def render_sql_result(parsed: dict[str, Any]) -> None:
    ok = parsed.get("ok")
    if ok:
        st.success("SQL tool completed successfully.")
    else:
        st.error("SQL tool returned an error.")

    if "error" in parsed:
        st.code(str(parsed["error"]), language="text")

    if "sql" in parsed:
        st.caption("Validated SQL")
        st.code(str(parsed["sql"]).strip(), language="sql")

    if "row_count" in parsed:
        st.caption(f"Rows returned: {parsed['row_count']}")

    rows = parsed.get("rows")
    if isinstance(rows, list) and rows:
        render_result_table(rows)
    elif isinstance(rows, list):
        st.info("The SQL returned zero rows.")


def render_lead_360_result(parsed: dict[str, Any]) -> None:
    status = str(parsed.get("status", "unknown"))
    message = str(parsed.get("message") or "Lead 360 tool completed.")

    if status == "success":
        st.success(message)
    elif status == "multiple_matches":
        st.warning(message)
    elif status == "not_found":
        st.info(message)
    else:
        st.error(message)

    matches = parsed.get("matches")
    if isinstance(matches, list) and matches:
        render_result_table(matches)


def render_tool_message(message: object, content: str) -> None:
    name = message_name(message) or "tool"
    st.markdown(f"**Tool result:** `{name}`")

    if name == "load_skill" or content.startswith("Loaded skill:"):
        render_loaded_skill(content)
        return

    parsed = maybe_json(content)
    if isinstance(parsed, dict):
        if name == "get_lead_360" or "lead_360" in parsed:
            render_lead_360_result(parsed)
        else:
            render_sql_result(parsed)
        with st.popover("Raw tool JSON"):
            st.json(parsed, expanded=True)
        return

    st.markdown(content)


def render_ai_message(message: object, content: str) -> None:
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        for tool_index, tool_call in enumerate(tool_calls, start=1):
            render_tool_call(safe_json(tool_call), tool_index)
    if content:
        st.caption("AI message")
        st.markdown(content)


def render_message_trace(message: object, index: int) -> None:
    role = message_role(message)
    name = message_name(message)
    title = f"{index}. {role.upper()}"
    if name:
        title = f"{title} - {name}"

    with st.container(border=True):
        st.markdown(f"### {title}")

        content = message_content(message).strip()

        if role == "human":
            st.caption("User input")
            st.markdown(content)
        elif role == "ai":
            render_ai_message(message, content)
        elif role == "tool":
            render_tool_message(message, content)
        else:
            st.markdown(content or "_Empty message content_")


def render_raw_messages(messages: list[object]) -> None:
    for index, message in enumerate(messages, start=1):
        st.markdown(f"**Raw message {index}: `{message_role(message)}`**")
        st.json(message_to_dict(message), expanded=False)


def compact_trace_text(value: Any, max_chars: int = 260) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3].rstrip()}..."


def render_router_history_table(title: str, rows: Any) -> None:
    if not isinstance(rows, list) or not rows:
        st.caption(f"{title}: none")
        return

    table_rows = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        table_rows.append(
            {
                "#": index,
                "User question": compact_trace_text(
                    row.get("question") or row.get("user_question")
                ),
                "Assistant answer": compact_trace_text(row.get("answer")),
            }
        )

    if not table_rows:
        st.caption(f"{title}: none")
        return

    st.caption(title)
    render_compact_table(table_rows)


def render_router_trace(turn: dict[str, Any]) -> None:
    router_response = turn.get("router_response")
    if not isinstance(router_response, dict):
        st.info("No router trace was captured for this historical turn.")
        return

    route = str(router_response.get("route") or turn.get("route") or "unknown")
    history_count = router_response.get("history_count")
    standalone_question = str(
        router_response.get("standalone_question")
        or turn.get("standalone_question")
        or ""
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Router route", route)
    metric_columns[1].metric("Router history", history_count if history_count is not None else "-")
    metric_columns[2].metric("Fetched history", len(turn.get("latest_router_history") or []))
    metric_columns[3].metric("Selected context", len(turn.get("selected_history") or []))

    st.markdown("**Router input**")
    st.markdown(turn["question"])
    render_router_history_table(
        "Latest 5 POC history rows sent to router",
        turn.get("latest_router_history"),
    )

    st.markdown("**Router output**")
    st.json(router_response, expanded=False)
    if standalone_question:
        st.caption("Standalone question used by selected downstream flow")
        st.markdown(standalone_question)

    render_router_history_table(
        "Downstream context selected by router.history_count",
        turn.get("selected_history"),
    )


def render_process_trace(turn: dict[str, Any]) -> None:
    elapsed = format_duration(turn.get("elapsed_seconds"))
    with st.expander(f"Process trace - completed in {elapsed}", expanded=False):
        columns = st.columns(3)
        columns[0].metric("Total time", elapsed)
        columns[1].metric("Messages", len(turn["trace_messages"]))
        columns[2].metric("Tool calls", count_tool_calls(turn["trace_messages"]))

        st.markdown("**Input**")
        st.markdown(turn["question"])
        route = turn.get("route")
        if route:
            st.caption(f"Route: {route}")
        st.caption(f"Context sent to selected flow: latest {turn.get('context_turn_count', 0)} prior Q&A turns.")

        router_tab, timeline_tab, raw_tab = st.tabs(["Router", "Readable timeline", "Raw messages"])
        with router_tab:
            render_router_trace(turn)
        with timeline_tab:
            for index, message in enumerate(turn["trace_messages"], start=1):
                render_message_trace(message, index)
        with raw_tab:
            if isinstance(turn.get("router_response"), dict):
                st.markdown("**Router response**")
                st.json(turn["router_response"], expanded=False)
            if isinstance(turn.get("latest_router_history"), list):
                st.markdown("**Latest router history**")
                st.json(turn["latest_router_history"], expanded=False)
            if isinstance(turn.get("selected_history"), list):
                st.markdown("**Selected downstream history**")
                st.json(turn["selected_history"], expanded=False)
            render_raw_messages(turn["trace_messages"])


def render_answer(turn: dict[str, Any]) -> None:
    details = turn.get("execution_details") or extract_execution_details(turn["trace_messages"])
    clean_answer = clean_answer_for_display(turn["answer"])

    render_answer_block(clean_answer)
    render_reference_intro(turn)
    render_timing_breakdown(turn)
    render_source_data_dropdown(details)
    render_sql_dropdown(details)
    render_process_trace(turn)


def render_turn(turn: dict[str, Any]) -> None:
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant", avatar=str(BOT_LOGO_PATH)):
        render_answer(turn)


def render_question_picker(
    *,
    title: str,
    selectbox_label: str,
    placeholder: str,
    questions: list[dict[str, str]],
    source_file: str,
    key_prefix: str,
) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if source_file:
            st.caption(f"Loaded {len(questions)} questions from `{source_file}`.")
        else:
            st.caption("No question CSV found.")

        question_labels = [
            f"{item['id']}: {item['question']}"
            for item in questions
        ]
        dropdown_options = [placeholder, *question_labels]
        selected_question = st.selectbox(
            selectbox_label,
            options=dropdown_options,
            index=0,
            key=f"{key_prefix}_question_select",
        )
        selected_index = dropdown_options.index(selected_question) - 1
        has_selection = selected_index >= 0
        if st.button(
            "Ask selected question",
            use_container_width=True,
            disabled=not has_selection,
            key=f"{key_prefix}_ask_question",
        ):
            st.session_state.pending_question = questions[selected_index]["question"]
            st.rerun()


def render_sidebar() -> None:
    settings = get_sql_agent_settings()
    organization_id = current_organization_id()
    model_label = html.escape(str(settings.model).upper())
    skill_label = html.escape(enabled_skill_summary(settings.enabled_skills))
    memory_label = html.escape(f"Latest {MAX_CONTEXT_TURNS} Q&A turns")
    question_matrix = load_question_matrix()

    with st.sidebar:
        st.header("Hermon Q&A Agent")
        st.markdown(
            f"""
            <div class="sidebar-module-card skill">
                <div class="sidebar-module-icon" aria-hidden="true">
                    <svg viewBox="0 0 64 64" role="img">
                        <path d="M32 6C20 6 11 15 11 26c0 7 4 13 10 17 3 2 4 5 4 9v1h14v-1c0-4 2-7 5-9 6-4 10-10 10-17C54 15 44 6 32 6Z" fill="#fff7d6"/>
                        <path d="M24 53h16" stroke="#f59e0b" stroke-width="5" stroke-linecap="round"/>
                        <path d="M26 60h12" stroke="#fbbf24" stroke-width="5" stroke-linecap="round"/>
                        <path d="M25 27c5 5 9 5 14 0" fill="none" stroke="#f59e0b" stroke-width="4" stroke-linecap="round"/>
                        <path d="M32 11v7M16 21l6 3M48 21l-6 3" stroke="#fbbf24" stroke-width="4" stroke-linecap="round"/>
                        <circle cx="32" cy="26" r="3.5" fill="#111827"/>
                    </svg>
                </div>
                <div>
                    <div class="sidebar-module-label">Enabled skills</div>
                    <div class="sidebar-module-title">{skill_label}</div>
                    <div class="sidebar-module-copy">Routes supported analytics questions to the SQL skills and single-lead questions to the Lead 360 flow.</div>
                </div>
            </div>
            <div class="sidebar-module-card llm">
                <div class="sidebar-module-icon" aria-hidden="true">
                    <svg viewBox="0 0 64 64" role="img">
                        <rect x="14" y="14" width="36" height="36" rx="8" fill="#ecebff"/>
                        <rect x="22" y="22" width="20" height="20" rx="5" fill="#4f46e5"/>
                        <path d="M8 23h6M8 32h6M8 41h6M50 23h6M50 32h6M50 41h6M23 8v6M32 8v6M41 8v6M23 50v6M32 50v6M41 50v6" stroke="#818cf8" stroke-width="4" stroke-linecap="round"/>
                        <circle cx="29" cy="29" r="2.6" fill="#a5b4fc"/>
                        <circle cx="37" cy="35" r="2.6" fill="#22d3ee"/>
                        <path d="M29 29l8 6" stroke="#c4b5fd" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                </div>
                <div>
                    <div class="sidebar-module-label">Current model</div>
                    <div class="sidebar-module-title">{model_label}</div>
                    <div class="sidebar-module-copy">Translates supported analytics questions into safe read-only SQL and returns the business answer first.</div>
                </div>
            </div>
            <div class="sidebar-module-card memory">
                <div class="sidebar-module-icon" aria-hidden="true">
                    <svg viewBox="0 0 64 64" role="img">
                        <ellipse cx="32" cy="15" rx="20" ry="8" fill="#ccfbf1"/>
                        <path d="M12 15v31c0 5 9 9 20 9s20-4 20-9V15" fill="#99f6e4"/>
                        <path d="M12 25c0 5 9 9 20 9s20-4 20-9M12 36c0 5 9 9 20 9s20-4 20-9" fill="none" stroke="#0f766e" stroke-width="4"/>
                        <ellipse cx="32" cy="15" rx="20" ry="8" fill="none" stroke="#0f766e" stroke-width="4"/>
                        <path d="M32 19c8 0 14-2 14-4s-6-4-14-4-14 2-14 4 6 4 14 4Z" fill="#f0fdfa"/>
                    </svg>
                </div>
                <div>
                    <div class="sidebar-module-label">Memory window</div>
                    <div class="sidebar-module-title">{memory_label}</div>
                    <div class="sidebar-module-copy">Keeps the most recent conversation context for follow-up questions.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Clear chat", use_container_width=True):
            clear_poc_chat_history(organization_id)
            st.session_state.turns = []
            st.session_state.history_organization_id = organization_id
            st.cache_resource.clear()
            st.rerun()

        st.divider()
        st.markdown("**Tested questions**")
        for config in QUESTION_PICKER_CONFIGS:
            question_set = question_matrix.get(config["key"], {})
            render_question_picker(
                title=config["title"],
                selectbox_label=config["selectbox_label"],
                placeholder=config["placeholder"],
                questions=question_set.get("questions", []),
                source_file=str(question_set.get("source_file") or ""),
                key_prefix=config["key"],
            )
            st.markdown("")


def render_hero() -> None:
    logo_bytes = BOT_LOGO_PATH.read_bytes()
    logo_src = f"data:image/svg+xml;base64,{base64.b64encode(logo_bytes).decode('ascii')}"
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-logo" aria-hidden="true">
                <img src="{logo_src}" alt="" />
            </div>
            <div>
                <h1 class="hero-title">Hermon Q&amp;A Agent</h1>
                <div class="hero-copy">
                    Ask analytics questions in plain English. The agent translates them into safe read-only SQL,
                    returns the business answer first, and keeps source rows and SQL tucked away for review.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    load_app_config.cache_clear()
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT,
    )
    inject_styles()
    init_state()
    render_sidebar()

    render_hero()

    for turn in st.session_state.turns:
        render_turn(turn)

    pending_question = st.session_state.pop("pending_question", None)
    typed_question = st.chat_input(
        "Ask about leads, appointments, acquisition, revenue, statuses, sources, owners, setters, or follow-ups"
    )
    question = pending_question or typed_question

    if question:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant", avatar=str(BOT_LOGO_PATH)):
            with st.spinner("Routing the question, then running the selected flow..."):
                started_at = time.perf_counter()
                try:
                    turn = run_question(question)
                except Exception as exc:  # noqa: BLE001 - Streamlit should show readable errors.
                    elapsed_seconds = time.perf_counter() - started_at
                    turn = {
                        "question": question,
                        "answer": f"Something failed while running the agent: `{type(exc).__name__}: {exc}`",
                        "trace_messages": [],
                        "all_messages": [],
                        "elapsed_seconds": elapsed_seconds,
                        "timing": {
                            "total_seconds": elapsed_seconds,
                            "events": [],
                        },
                        "lead_360_diagnostics": None,
                        "execution_details": {},
                    }

            render_answer(turn)

        st.session_state.turns.append(turn)
        prune_turn_history()


if __name__ == "__main__":
    main()
