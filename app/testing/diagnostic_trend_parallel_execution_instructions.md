# Parallel Execution Instructions for Diagnostic Monthly Trend Overview Tool

## Purpose

Apply this only to the new diagnostic generic trend tool:

```text
get_diagnostic_monthly_trend_overview_snapshot
```

This instruction is only for improving execution speed by running independent SQL sections in parallel.

Do not change existing individual trend behavior in:

```text
lead_analytics
revenue_analytics
appointment_analytics
lead_profile_analytics
acquisition_analytics
1_0_0.yaml
```

Individual trend questions must continue to work exactly as they currently do.

## Why Parallel Execution Is Needed

The generic diagnostic trend tool needs multiple independent trend sections:

```text
overall_lead_trend
revenue_trend
appointment_trend
source_trend
profession_trend
```

These sections do not depend on each other.

Running them one by one can make the generic diagnostic answer slow. Run them in parallel using `ThreadPoolExecutor` so the total response time is closer to the slowest query instead of the sum of all query times.

## Required Parallel Sections

Run these sections concurrently:

```text
overall_lead_trend
revenue_trend
appointment_trend
source_trend
profession_trend
```

Preserve this same order in the final response object:

```text
1. overall_lead_trend
2. revenue_trend
3. appointment_trend
4. source_trend
5. profession_trend
```

## Worker Count

Use bounded concurrency.

Recommended MVP/demo setting:

```python
max_workers = 4
```

Alternative dynamic setting:

```python
max_workers = min(5, len(tasks))
```

Do not use unlimited workers.

Do not create one thread per SQL query if more sections are added later. Keep a hard maximum.

## Shared Input Preparation

Before starting parallel execution, calculate these once:

```text
org_id
start_date
end_date
period_label
default_used
reporting_cutoff
```

Pass the same values to every section query.

Do not calculate different date windows inside each thread.

## Database Safety Rules

Every query must remain read-only.

Every query must include:

```sql
:org_id
```

Every query must use the same:

```sql
:start_date
:end_date
```

Do not hardcode organization ID or dates inside SQL.

Do not share the same database cursor across threads.

Do not share a non-thread-safe database session across threads.

Each thread should execute through the existing safe read-only SQL helper independently.

Safe options:

```text
- Use a database connection pool where each thread checks out its own connection.
- Or let the existing run_readonly_sql helper create/use an independent connection per call.
- If using SQLAlchemy, create a session/connection inside the thread, not outside.
- If using Supabase/Postgres helper, confirm each parallel call is independent and thread-safe.
```

## Error Handling

Each section should fail independently.

If one optional section fails, do not fail the whole diagnostic tool.

Return:

```text
status = "partial_success"
```

when at least one section succeeds and at least one section fails.

Return:

```text
status = "error"
```

only when all required sections fail or the tool cannot calculate the reporting window.

Do not expose raw stack traces to the user-facing answer.

Put safe technical details only inside `_diagnostics`.

## Timeout Handling

Set a timeout per section.

Recommended default:

```python
section_timeout_seconds = 30
```

If a section times out:

```text
- return an empty list for that section
- record the timeout in `_diagnostics.section_errors`
- continue with the remaining sections
```

## Suggested Implementation Pattern

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_diagnostic_monthly_trend_overview_snapshot(
    org_id: str,
    start_date=None,
    end_date=None,
    limit: int = 10,
):
    period = resolve_monthly_trend_period(
        start_date=start_date,
        end_date=end_date,
        default_months=3,
    )

    shared_params = {
        "org_id": org_id,
        "start_date": period["start_date"],
        "end_date": period["end_date"],
        "limit": limit,
    }

    tasks = {
        "overall_lead_trend": run_overall_lead_trend,
        "revenue_trend": run_revenue_trend,
        "appointment_trend": run_appointment_trend,
        "source_trend": run_source_trend,
        "profession_trend": run_profession_trend,
    }

    results = {}
    errors = {}

    max_workers = min(5, len(tasks))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(fn, **shared_params): section_name
            for section_name, fn in tasks.items()
        }

        for future in as_completed(future_map):
            section_name = future_map[future]

            try:
                results[section_name] = future.result(timeout=30)
            except Exception as exc:
                results[section_name] = []
                errors[section_name] = str(exc)

    ordered_sections = {
        "overall_lead_trend": results.get("overall_lead_trend", []),
        "revenue_trend": results.get("revenue_trend", []),
        "appointment_trend": results.get("appointment_trend", []),
        "source_trend": results.get("source_trend", []),
        "profession_trend": results.get("profession_trend", []),
    }

    successful_sections = [
        name for name, rows in ordered_sections.items()
        if rows
    ]

    if errors and successful_sections:
        status = "partial_success"
    elif errors and not successful_sections:
        status = "error"
    else:
        status = "success"

    return {
        "status": status,
        "period": {
            "start_date": period["start_date"],
            "end_date": period["end_date"],
            "label": period["label"],
            "default_used": period["default_used"],
        },
        **ordered_sections,
        "_diagnostics": {
            "parallel_execution": True,
            "max_workers": max_workers,
            "successful_sections": successful_sections,
            "section_errors": errors,
        },
    }
```

## Important Correction for Timeout Usage

`future.result(timeout=30)` inside `as_completed()` will usually not enforce the full per-task timeout because `as_completed()` yields futures after completion.

If strict per-section timeout is required, use one of these safer approaches:

```text
Option 1:
Set statement timeout at the database/query level.

Option 2:
Use the existing SQL helper timeout if it supports timeout_seconds.

Option 3:
Wrap each query function so the read-only SQL call has its own timeout handling.
```

Recommended approach:

```python
run_readonly_sql(sql, params=params, timeout_seconds=30)
```

Use database-level or SQL-helper-level timeout as the real timeout mechanism.

## Recommended Section Wrapper

```python
def run_section(section_name: str, sql: str, params: dict):
    try:
        rows = run_readonly_sql(
            sql=sql,
            params=params,
            timeout_seconds=30,
        )
        return {
            "section_name": section_name,
            "rows": rows,
            "error": None,
        }
    except Exception as exc:
        return {
            "section_name": section_name,
            "rows": [],
            "error": str(exc),
        }
```

Then submit wrappers instead of raw query functions.

## Output Contract

The tool must return this structure:

```json
{
  "status": "success",
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-05-01",
    "label": "Feb 2026 through Apr 2026",
    "default_used": true
  },
  "overall_lead_trend": [],
  "revenue_trend": [],
  "appointment_trend": [],
  "source_trend": [],
  "profession_trend": [],
  "_diagnostics": {
    "parallel_execution": true,
    "max_workers": 4,
    "successful_sections": [],
    "section_errors": {}
  }
}
```

## User-Facing Answer Rules

The user-facing answer should not mention:

```text
ThreadPoolExecutor
parallel execution
workers
SQL helper
section errors
stack traces
```

The user-facing answer should only use available successful sections.

If one optional section fails, the assistant can naturally say:

```text
Profession trend was not available in this run.
```

Do not show the raw technical error.

## Consistency Rules

For static MVP/demo data, parallel execution is safe.

For live production data, parallel queries may read slightly different database moments if records change during execution.

To reduce mismatch:

```text
- calculate date window once
- pass same start_date and end_date to all sections
- avoid using NOW() separately inside every SQL query
- use one application-level reporting_cutoff timestamp where needed
```

## Acceptance Criteria

Codex implementation is acceptable only if:

```text
- The diagnostic generic trend tool runs independent SQL sections in parallel.
- Existing individual trend questions remain unchanged.
- Each query uses org_id, start_date, and end_date safely.
- No shared cursor/session is reused across threads.
- Output order is stable.
- One section failure does not fail the entire tool.
- User-facing answer does not expose technical errors.
- _diagnostics contains parallel_execution = true.
```
