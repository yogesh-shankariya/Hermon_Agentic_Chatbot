"""Build silver-truth outputs for SQL analytics test questions.

Run from the project root:

    python -m app.testing.build_silver_truth

Appointment analytics:

    python -m app.testing.build_silver_truth --skill appointment_analytics

Appointment analytics actual output:

    python -m app.testing.build_silver_truth --skill appointment_analytics --run-type actual_output

The measured execution time wraps only the agent invocation for each question.
CSV and Markdown writes happen after timing is captured.
Outputs are appended after every question so reruns resume from the next
unrecorded row.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.sql_agent import create_sql_agent  # noqa: E402
from app.config import get_silver_truth_settings, get_sql_agent_settings  # noqa: E402


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "app" / "testing" / "output"
DEFAULT_QUESTION_COLUMN = "question"
RUN_TYPE_TITLES = {
    "silver_truth": "Silver Truth",
    "actual_output": "Actual Output",
}
SKILL_PRESETS = {
    "lead_analytics": {
        "input_path": PROJECT_ROOT
        / "app"
        / "testing"
        / "input"
        / "lead_analytics_test_questions_with_guardrails.csv",
    },
    "appointment_analytics": {
        "input_path": PROJECT_ROOT
        / "app"
        / "testing"
        / "input"
        / "appointment_analytics_test_questions_with_guardrails.csv",
    },
}

OUTPUT_COLUMNS = [
    "generated_sql",
    "generated_params_json",
    "generated_final_answer",
    "source_row_count",
    "source_columns_json",
    "source_rows_json",
    "execution_seconds",
    "execution_ms",
    "run_status",
    "error_message",
    "model",
    "reasoning_effort",
    "service_tier",
]


class AgentRunError(RuntimeError):
    """Agent execution failed after a measured duration."""

    def __init__(self, message: str, elapsed_seconds: float) -> None:
        super().__init__(message)
        self.elapsed_seconds = elapsed_seconds


def stringify_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "reasoning":
                    continue
                if "text" in item:
                    parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def message_role(message: object) -> str:
    return str(getattr(message, "type", message.__class__.__name__))


def message_content(message: object) -> str:
    return stringify_content(getattr(message, "content", ""))


def safe_json(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def maybe_json(value: str) -> Any | None:
    try:
        return json.loads(value)
    except Exception:
        return None


def csv_json(value: Any) -> str:
    return json.dumps(value, default=str, ensure_ascii=False)


def readable_skill_name(skill_name: str) -> str:
    return skill_name.replace("_", " ").title()


def default_run_name(skill_name: str, run_type: str) -> str:
    return f"{skill_name}_{run_type}"


def default_title(skill_name: str, run_type: str) -> str:
    return f"{readable_skill_name(skill_name)} {RUN_TYPE_TITLES[run_type]}"


def final_answer_from(messages: list[object]) -> str:
    for message in reversed(messages):
        if message_role(message) == "ai":
            content = message_content(message).strip()
            if content:
                return content
    return ""


def extract_execution_details(messages: list[object]) -> dict[str, Any]:
    details: dict[str, Any] = {
        "sql": "",
        "params": "",
        "row_count": "",
        "rows": [],
        "tool_error": "",
    }

    for message in messages:
        if message_role(message) == "ai":
            for tool_call in getattr(message, "tool_calls", None) or []:
                tool_call = safe_json(tool_call)
                tool_name = tool_call.get("name")
                args = tool_call.get("args") or {}
                if not isinstance(args, dict):
                    continue

                if tool_name in {"run_readonly_sql", "validate_sql"} and args.get("query"):
                    details["sql"] = str(args["query"]).strip()
                    if args.get("params_json"):
                        details["params"] = str(args["params_json"]).strip()

        if message_role(message) == "tool":
            parsed = maybe_json(message_content(message).strip())
            if not isinstance(parsed, dict):
                continue

            if parsed.get("sql"):
                details["sql"] = str(parsed["sql"]).strip()
            if parsed.get("error"):
                details["tool_error"] = str(parsed["error"])
            if "row_count" in parsed:
                details["row_count"] = parsed.get("row_count", "")
            if isinstance(parsed.get("rows"), list):
                details["rows"] = parsed["rows"]
                details["row_count"] = parsed.get("row_count", len(parsed["rows"]))

    return details


def read_input_rows(input_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames:
            raise RuntimeError(f"CSV has no header row: {input_path}")
        return list(reader.fieldnames), list(reader)


def run_one_question(agent: Any, question: str) -> tuple[list[object], float]:
    request_messages = [{"role": "user", "content": question}]

    started_at = time.perf_counter()
    try:
        result = agent.invoke({"messages": request_messages})
    except Exception as exc:
        elapsed_seconds = time.perf_counter() - started_at
        raise AgentRunError(f"{type(exc).__name__}: {exc}", elapsed_seconds) from exc

    elapsed_seconds = time.perf_counter() - started_at
    return list(result.get("messages", [])), elapsed_seconds


def build_output_row(
    input_row: dict[str, str],
    *,
    messages: list[object],
    elapsed_seconds: float,
    model: str,
    reasoning_effort: str,
    service_tier: str,
    error_message: str = "",
) -> dict[str, str]:
    details = extract_execution_details(messages)
    final_answer = final_answer_from(messages)
    status = "error" if error_message or details.get("tool_error") else "ok"
    source_rows = details.get("rows")
    if not isinstance(source_rows, list):
        source_rows = []
    source_columns = list(source_rows[0].keys()) if source_rows and isinstance(source_rows[0], dict) else []

    return {
        **input_row,
        "generated_sql": str(details.get("sql") or ""),
        "generated_params_json": str(details.get("params") or ""),
        "generated_final_answer": final_answer,
        "source_row_count": str(details.get("row_count") or ""),
        "source_columns_json": csv_json(source_columns),
        "source_rows_json": csv_json(source_rows),
        "execution_seconds": f"{elapsed_seconds:.3f}",
        "execution_ms": str(round(elapsed_seconds * 1000)),
        "run_status": status,
        "error_message": error_message or str(details.get("tool_error") or ""),
        "model": model,
        "reasoning_effort": reasoning_effort,
        "service_tier": service_tier,
    }


def row_key(row: dict[str, str], question_column: str) -> str:
    return (row.get("question_id") or row.get(question_column) or "").strip()


def read_existing_output(output_path: Path) -> list[dict[str, str]]:
    if not output_path.exists() or output_path.stat().st_size == 0:
        return []

    with output_path.open("r", encoding="utf-8", newline="") as output_file:
        return list(csv.DictReader(output_file))


def completed_keys(
    rows: list[dict[str, str]],
    *,
    question_column: str,
    retry_errors: bool,
) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        if retry_errors and row.get("run_status") == "error":
            continue
        key = row_key(row, question_column)
        if key:
            keys.add(key)
    return keys


def read_csv_header(output_path: Path) -> list[str]:
    if not output_path.exists() or output_path.stat().st_size == 0:
        return []

    with output_path.open("r", encoding="utf-8", newline="") as output_file:
        reader = csv.reader(output_file)
        return next(reader, [])


def initialize_csv(
    output_path: Path,
    fieldnames: list[str],
    *,
    existing_rows: list[dict[str, str]],
    fresh: bool,
) -> None:
    if fresh or not output_path.exists() or output_path.stat().st_size == 0:
        with output_path.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
        return

    if read_csv_header(output_path) != fieldnames:
        with output_path.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)


def append_csv_row(output_path: Path, fieldnames: list[str], row: dict[str, str]) -> None:
    with output_path.open("a", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writerow(row)


def markdown_block(row: dict[str, str], *, index: int, question_column: str) -> str:
    question_id = row.get("question_id") or f"Question {index}"
    question = row.get(question_column, "")
    sql = row.get("generated_sql") or "No SQL captured."
    answer = row.get("generated_final_answer") or "No final answer captured."

    lines = [
        f"## {index}. {question_id}",
        "",
        "**Question**",
        "",
        question,
        "",
        "**Generated SQL**",
        "",
        "```sql",
        sql,
        "```",
        "",
        "**Generated final answer**",
        "",
        answer,
        "",
        f"**Execution time:** {row.get('execution_seconds', '')} sec",
        f"**Status:** {row.get('run_status', '')}",
    ]
    if row.get("error_message"):
        lines.extend(["", f"**Error:** {row['error_message']}"])
    lines.append("")
    return "\n".join(lines)


def initialize_markdown(
    output_path: Path,
    *,
    existing_rows: list[dict[str, str]],
    question_column: str,
    fresh: bool,
    title: str,
) -> None:
    if existing_rows and not fresh and output_path.exists() and output_path.stat().st_size > 0:
        return

    lines = [f"# {title}", ""]
    for index, row in enumerate(existing_rows, start=1):
        lines.append(markdown_block(row, index=index, question_column=question_column))

    output_path.write_text("\n".join(lines), encoding="utf-8")


def append_markdown_row(
    output_path: Path,
    row: dict[str, str],
    *,
    index: int,
    question_column: str,
) -> None:
    with output_path.open("a", encoding="utf-8") as output_file:
        output_file.write("\n")
        output_file.write(markdown_block(row, index=index, question_column=question_column))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build agent-run CSV and Markdown outputs.")
    parser.add_argument(
        "--skill",
        choices=sorted(SKILL_PRESETS),
        default="lead_analytics",
        help="Use default input/output naming for a supported test matrix.",
    )
    parser.add_argument(
        "--run-type",
        choices=sorted(RUN_TYPE_TITLES),
        default="silver_truth",
        help="Controls default output file names and Markdown title.",
    )
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--question-column", default=DEFAULT_QUESTION_COLUMN)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--service-tier",
        choices=["auto", "default", "flex", "priority"],
        default=None,
        help="Override configured testing service_tier for this run.",
    )
    parser.add_argument("--fresh", action="store_true", help="Overwrite existing output and start from row 1.")
    parser.add_argument("--retry-errors", action="store_true", help="Rerun rows previously saved with run_status=error.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preset = SKILL_PRESETS[args.skill]
    input_path = (args.input or preset["input_path"]).resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_name = args.run_name or default_run_name(args.skill, args.run_type)
    csv_output_path = output_dir / f"{run_name}.csv"
    md_output_path = output_dir / f"{run_name}.md"

    input_fieldnames, input_rows = read_input_rows(input_path)
    if args.question_column not in input_fieldnames:
        raise RuntimeError(f"Question column '{args.question_column}' not found in {input_path}")
    if args.limit is not None:
        input_rows = input_rows[: args.limit]
    output_fieldnames = input_fieldnames + [
        column for column in OUTPUT_COLUMNS if column not in input_fieldnames
    ]

    existing_rows = [] if args.fresh else read_existing_output(csv_output_path)
    skip_keys = completed_keys(
        existing_rows,
        question_column=args.question_column,
        retry_errors=args.retry_errors,
    )
    initialize_csv(
        csv_output_path,
        output_fieldnames,
        existing_rows=existing_rows,
        fresh=args.fresh,
    )
    initialize_markdown(
        md_output_path,
        existing_rows=existing_rows,
        question_column=args.question_column,
        fresh=args.fresh,
        title=args.title or default_title(args.skill, args.run_type),
    )

    settings = get_sql_agent_settings()
    reasoning_effort = ""
    if settings.reasoning:
        reasoning_effort = str(settings.reasoning.get("effort", ""))
    silver_truth_settings = get_silver_truth_settings()
    service_tier = args.service_tier
    if service_tier is None:
        service_tier = silver_truth_settings.service_tier or ""

    agent = create_sql_agent(service_tier=service_tier or None)
    output_index = len(existing_rows)

    for index, input_row in enumerate(input_rows, start=1):
        key = row_key(input_row, args.question_column)
        if key in skip_keys:
            print(f"[{index}/{len(input_rows)}] Skipping already recorded: {key}")
            continue

        question = input_row.get(args.question_column, "").strip()
        print(f"[{index}/{len(input_rows)}] {question}")
        try:
            messages, elapsed_seconds = run_one_question(agent, question)
            output_row = build_output_row(
                input_row,
                messages=messages,
                elapsed_seconds=elapsed_seconds,
                model=settings.model,
                reasoning_effort=reasoning_effort,
                service_tier=service_tier,
            )
        except AgentRunError as exc:
            output_row = build_output_row(
                input_row,
                messages=[],
                elapsed_seconds=exc.elapsed_seconds,
                model=settings.model,
                reasoning_effort=reasoning_effort,
                service_tier=service_tier,
                error_message=str(exc),
            )

        append_csv_row(csv_output_path, output_fieldnames, output_row)
        output_index += 1
        append_markdown_row(
            md_output_path,
            output_row,
            index=output_index,
            question_column=args.question_column,
        )
        if key:
            skip_keys.add(key)

    print(f"CSV output: {csv_output_path}")
    print(f"Markdown output: {md_output_path}")


if __name__ == "__main__":
    main()
