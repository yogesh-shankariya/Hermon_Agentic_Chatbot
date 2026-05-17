# Codex Instructions: Add Generic Diagnostic Monthly Trend Overview Tool

## Goal

Implement a separate diagnostic tool for generic business trend questions such as:

```text
What trends are you noticing?
What are the current trends?
What is changing in the business?
What should I pay attention to?
What looks different recently?
```

These questions should not produce only a funnel-leakage answer. They should return a business trend review with multiple sections in this exact order:

1. Overall lead trend
2. Revenue trend
3. Appointment / call trend
4. Lead trend by source
5. Lead trend by profession
6. Short business summary bullets

The individual SQL skills already handle single-metric trend questions. This new tool is specifically for broad diagnostic questions where the user expects the AI to look across the business.

---

## Why a Separate Tool Is Needed

Create a separate diagnostic tool because generic diagnostic trend questions need multiple trend datasets at the same time.

Do not try to answer this by calling only one existing diagnostic snapshot:

- `get_diagnostic_business_change_snapshot` gives current-vs-previous period comparison, not month-by-month tables.
- `get_diagnostic_funnel_snapshot` is designed for funnel leakage and stuck-stage analysis.
- `get_diagnostic_source_snapshot` gives source performance for one period, not a monthly source trend.
- `get_diagnostic_profile_snapshot` gives profile performance for one period, not a monthly profile trend.

The new tool should return monthly rows for leads, revenue, appointments, source trend, and profession trend in one structured response so the diagnostic answer can format everything consistently.

---

## New Tool Name

Add this tool:

```python
def get_diagnostic_monthly_trend_overview_snapshot(
    org_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    source_basis: str = "first",
    profile_field: str = "latest_profession",
    source_limit: int = 10,
    profile_limit: int = 10,
) -> dict[str, Any]:
    ...
```

## Tool Purpose

This tool returns a multi-section monthly trend snapshot from `diagnostic_lead_snapshot` for business-level diagnostic trend answers.

It must not generate natural-language answers. It should return structured JSON only.

---

## Default Date Window

If `start_date` and `end_date` are not provided, use the previous 3 completed calendar months.

Example: if today is 2026-05-17, default period is:

```text
start_date = 2026-02-01
end_date = 2026-05-01
```

The final displayed trend period should be:

```text
Feb 2026 through Apr 2026 (default previous 3 completed months)
```

Rules:

- `end_date` is exclusive.
- Exclude the current partial month by default.
- If the user explicitly asks for this month or month-to-date, allow the application/router to pass a custom date range.
- Do not ask the user for dates when the default applies.

---

## Source Basis Rules

Default:

```text
source_basis = "first"
```

Use first-touch source by default because generic business trend questions should show where leads originally came from.

Allowed values:

```text
first
last
```

Map source basis as follows:

```python
if source_basis == "last":
    source_column = "last_source"
else:
    source_column = "first_source"
```

If the current `diagnostic_lead_snapshot` uses different source column names, reuse the existing `_source_column(source_basis)` helper already used by `get_diagnostic_source_snapshot`.

Do not use latest/last source unless the user explicitly asks for latest source, last source, or last-touch source.

---

## Profile Field Rules

Default:

```text
profile_field = "latest_profession"
```

Allowed values:

```text
latest_profession
latest_employment_status
```

Generic trend questions should usually include profession trend. Employment status can be used later if the user asks for employment-status trend specifically.

If the profile field does not exist in `diagnostic_lead_snapshot`, then Codex should either:

1. use the existing profile field already present in the snapshot, or
2. add the missing profile fields to the snapshot build script before implementing this tool.

The diagnostic response should never generate profession from LLM inference. It should use only stored/latest opt-in profile answer fields.

---

## Money Rule

Important:

`diagnostic_lead_snapshot` money fields are already stored as major-unit EUR values.

Do not divide these fields by `100` again:

```text
gross_paid_amount
refund_amount
net_collected_amount
outstanding_amount
```

Use EUR formatting in the final answer.

---

## Required JSON Response Shape

The tool should return this structure:

```json
{
  "status": "success",
  "tool": "get_diagnostic_monthly_trend_overview_snapshot",
  "scope_note": "...",
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-05-01",
    "display_start_month": "Feb 2026",
    "display_end_month": "Apr 2026",
    "display_label": "Feb 2026 through Apr 2026",
    "date_note": "default previous 3 completed months",
    "end_date_is_exclusive": true
  },
  "source_basis": "first",
  "profile_field": "latest_profession",
  "source_limit": 10,
  "profile_limit": 10,
  "overall_lead_trend": [],
  "revenue_trend": [],
  "appointment_trend": [],
  "source_lead_trend": [],
  "profile_lead_trend": [],
  "summary_metrics": {},
  "warnings": []
}
```

If something fails, return the same error pattern already used by existing diagnostic tools:

```json
{
  "status": "error",
  "tool": "get_diagnostic_monthly_trend_overview_snapshot",
  "message": "safe error message"
}
```

Do not expose raw SQL, traceback, database credentials, internal UUIDs, or private payloads in tool output.

---

## SQL Section 1: Overall Lead Trend

Use `diagnostic_lead_snapshot.lead_created_at` for the monthly lead trend.

Required output columns:

```text
month_start
month_label
lead_count
previous_month_lead_count
lead_count_change
percentage_change
total_matching_leads
```

SQL template:

```sql
WITH monthly AS (
  SELECT
    DATE_TRUNC('month', dls.lead_created_at)::date AS month_start,
    TO_CHAR(DATE_TRUNC('month', dls.lead_created_at)::date, 'Mon YYYY') AS month_label,
    COUNT(*)::int AS lead_count
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
  GROUP BY 1, 2
), enriched AS (
  SELECT
    month_start,
    month_label,
    lead_count,
    LAG(lead_count) OVER (ORDER BY month_start) AS previous_month_lead_count
  FROM monthly
)
SELECT
  month_start,
  month_label,
  lead_count,
  previous_month_lead_count,
  CASE
    WHEN previous_month_lead_count IS NULL THEN NULL
    ELSE lead_count - previous_month_lead_count
  END AS lead_count_change,
  ROUND(
    100.0 * (lead_count - previous_month_lead_count)
    / NULLIF(previous_month_lead_count, 0),
    2
  ) AS percentage_change,
  SUM(lead_count) OVER ()::int AS total_matching_leads
FROM enriched
ORDER BY month_start ASC;
```

---

## SQL Section 2: Revenue Trend

Revenue trend should be based on the lead cohort month in `diagnostic_lead_snapshot`.

Required output columns:

```text
month_start
month_label
paid_payment_count
net_collected_amount
previous_month_net_collected_amount
revenue_change
percentage_change
```

SQL template:

```sql
WITH monthly AS (
  SELECT
    DATE_TRUNC('month', dls.lead_created_at)::date AS month_start,
    TO_CHAR(DATE_TRUNC('month', dls.lead_created_at)::date, 'Mon YYYY') AS month_label,
    COALESCE(SUM(dls.paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(dls.net_collected_amount), 0)::numeric(12,2) AS net_collected_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
  GROUP BY 1, 2
), enriched AS (
  SELECT
    month_start,
    month_label,
    paid_payment_count,
    net_collected_amount,
    LAG(net_collected_amount) OVER (ORDER BY month_start) AS previous_month_net_collected_amount
  FROM monthly
)
SELECT
  month_start,
  month_label,
  paid_payment_count,
  net_collected_amount,
  previous_month_net_collected_amount,
  CASE
    WHEN previous_month_net_collected_amount IS NULL THEN NULL
    ELSE net_collected_amount - previous_month_net_collected_amount
  END AS revenue_change,
  ROUND(
    100.0 * (net_collected_amount - previous_month_net_collected_amount)
    / NULLIF(previous_month_net_collected_amount, 0),
    2
  ) AS percentage_change
FROM enriched
ORDER BY month_start ASC;
```

Revenue caveat for final answer:

```text
Revenue figures here are cohort-based: they show lifetime net collected revenue for leads created in the selected period, not true payment-period revenue.
```

Include this caveat after the revenue table or at the end of the answer when revenue is shown.

---

## SQL Section 3: Appointment / Call Trend

Use this section only from `diagnostic_lead_snapshot`.

Required output columns:

```text
month_start
month_label
booked_lead_count
appointment_count
completed_call_count
no_show_count
completed_call_rate
no_show_rate
```

SQL template:

```sql
SELECT
  DATE_TRUNC('month', dls.lead_created_at)::date AS month_start,
  TO_CHAR(DATE_TRUNC('month', dls.lead_created_at)::date, 'Mon YYYY') AS month_label,
  COUNT(*) FILTER (WHERE dls.appointment_count > 0)::int AS booked_lead_count,
  COALESCE(SUM(dls.appointment_count), 0)::int AS appointment_count,
  COALESCE(SUM(dls.completed_call_count), 0)::int AS completed_call_count,
  COALESCE(SUM(dls.no_show_count), 0)::int AS no_show_count,
  ROUND(
    100.0 * COALESCE(SUM(dls.completed_call_count), 0)
    / NULLIF(COALESCE(SUM(dls.appointment_count), 0), 0),
    2
  ) AS completed_call_rate,
  ROUND(
    100.0 * COALESCE(SUM(dls.no_show_count), 0)
    / NULLIF(COALESCE(SUM(dls.appointment_count), 0), 0),
    2
  ) AS no_show_rate
FROM diagnostic_lead_snapshot dls
WHERE dls.clerk_org_id = :org_id
  AND dls.lead_created_at >= CAST(:start_date AS date)
  AND dls.lead_created_at < CAST(:end_date AS date)
GROUP BY 1, 2
ORDER BY month_start ASC;
```

---

## SQL Section 4: Lead Trend by Source

This is a monthly source trend based on lead cohort month.

Required output columns:

```text
month_start
month_label
source_name
lead_count
previous_period_lead_count
percentage_change
total_matching_leads
```

The SQL should first identify the top sources across the selected period, then return monthly rows only for those sources.

SQL template:

```sql
WITH scoped AS (
  SELECT
    DATE_TRUNC('month', dls.lead_created_at)::date AS month_start,
    TO_CHAR(DATE_TRUNC('month', dls.lead_created_at)::date, 'Mon YYYY') AS month_label,
    COALESCE(NULLIF(BTRIM(dls.{source_column}), ''), 'Unknown') AS source_name,
    dls.lead_id AS lead_id
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
), top_sources AS (
  SELECT
    source_name,
    COUNT(DISTINCT lead_id)::int AS total_leads
  FROM scoped
  GROUP BY source_name
  ORDER BY total_leads DESC, source_name ASC
  LIMIT :source_limit
), monthly_counts AS (
  SELECT
    s.month_start,
    s.month_label,
    s.source_name,
    COUNT(DISTINCT s.lead_id)::int AS lead_count
  FROM scoped s
  JOIN top_sources ts
    ON ts.source_name = s.source_name
  GROUP BY s.month_start, s.month_label, s.source_name
), enriched AS (
  SELECT
    month_start,
    month_label,
    source_name,
    lead_count,
    LAG(lead_count) OVER (
      PARTITION BY source_name
      ORDER BY month_start
    ) AS previous_period_lead_count
  FROM monthly_counts
)
SELECT
  month_start,
  month_label,
  source_name,
  lead_count,
  previous_period_lead_count,
  ROUND(
    100.0 * (lead_count - previous_period_lead_count)
    / NULLIF(previous_period_lead_count, 0),
    2
  ) AS percentage_change,
  SUM(lead_count) OVER ()::int AS total_matching_leads
FROM enriched
ORDER BY
  month_start ASC,
  lead_count DESC,
  source_name ASC;
```

Replace `{source_column}` using the existing source helper or safe allowlist. Do not string-format user input directly into SQL except through an allowlisted column name.

---

## SQL Section 5: Lead Trend by Profession

This is a monthly profile trend based on lead cohort month.

Required output columns:

```text
month_start
month_label
profile_value
lead_count
previous_period_lead_count
percentage_change
total_matching_leads
```

SQL template:

```sql
WITH scoped AS (
  SELECT
    DATE_TRUNC('month', dls.lead_created_at)::date AS month_start,
    TO_CHAR(DATE_TRUNC('month', dls.lead_created_at)::date, 'Mon YYYY') AS month_label,
    COALESCE(NULLIF(BTRIM(dls.{profile_column}), ''), 'Not provided') AS profile_value,
    dls.lead_id AS lead_id
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
), top_profiles AS (
  SELECT
    profile_value,
    COUNT(DISTINCT lead_id)::int AS total_leads
  FROM scoped
  GROUP BY profile_value
  ORDER BY total_leads DESC, profile_value ASC
  LIMIT :profile_limit
), monthly_counts AS (
  SELECT
    s.month_start,
    s.month_label,
    s.profile_value,
    COUNT(DISTINCT s.lead_id)::int AS lead_count
  FROM scoped s
  JOIN top_profiles tp
    ON tp.profile_value = s.profile_value
  GROUP BY s.month_start, s.month_label, s.profile_value
), enriched AS (
  SELECT
    month_start,
    month_label,
    profile_value,
    lead_count,
    LAG(lead_count) OVER (
      PARTITION BY profile_value
      ORDER BY month_start
    ) AS previous_period_lead_count
  FROM monthly_counts
)
SELECT
  month_start,
  month_label,
  profile_value,
  lead_count,
  previous_period_lead_count,
  ROUND(
    100.0 * (lead_count - previous_period_lead_count)
    / NULLIF(previous_period_lead_count, 0),
    2
  ) AS percentage_change,
  SUM(lead_count) OVER ()::int AS total_matching_leads
FROM enriched
ORDER BY
  month_start ASC,
  lead_count DESC,
  profile_value ASC;
```

Replace `{profile_column}` only from this allowlist:

```python
PROFILE_COLUMN_MAP = {
    "latest_profession": "latest_profession",
    "latest_employment_status": "latest_employment_status",
}
```

Do not allow arbitrary profile column names.

---

## Suggested Python Implementation Pattern

Add constants near the existing diagnostic SQL constants:

```python
MONTHLY_LEAD_TREND_SQL = """..."""
MONTHLY_REVENUE_TREND_SQL = """..."""
MONTHLY_APPOINTMENT_TREND_SQL = """..."""
MONTHLY_SOURCE_LEAD_TREND_SQL_TEMPLATE = """... {source_column} ..."""
MONTHLY_PROFILE_LEAD_TREND_SQL_TEMPLATE = """... {profile_column} ..."""
```

Add helper:

```python
def _default_monthly_trend_periods(
    org_id: str,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, str]:
    ...
```

Behavior:

- If both `start_date` and `end_date` are provided, use them.
- If not provided, compute previous 3 completed calendar months.
- Use date strings in `YYYY-MM-DD` format.
- Include display metadata for final answer.

Add allowlist helper:

```python
def _profile_column(profile_field: str) -> str:
    normalized = str(profile_field or "latest_profession").strip().lower()
    if normalized == "latest_employment_status":
        return "latest_employment_status"
    return "latest_profession"
```

Then implement:

```python
def get_diagnostic_monthly_trend_overview_snapshot(
    org_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    source_basis: str = "first",
    profile_field: str = "latest_profession",
    source_limit: int = 10,
    profile_limit: int = 10,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_monthly_trend_periods(clean_org_id, start_date, end_date)
        safe_source_limit = _safe_limit(source_limit)
        safe_profile_limit = _safe_limit(profile_limit)
        source_column = _source_column(source_basis)
        profile_column = _profile_column(profile_field)

        params = {
            "org_id": clean_org_id,
            "start_date": periods["start_date"],
            "end_date": periods["end_date"],
        }

        overall_rows = _query_records(MONTHLY_LEAD_TREND_SQL, params)
        revenue_rows = _query_records(MONTHLY_REVENUE_TREND_SQL, params)
        appointment_rows = _query_records(MONTHLY_APPOINTMENT_TREND_SQL, params)

        source_sql = MONTHLY_SOURCE_LEAD_TREND_SQL_TEMPLATE.format(source_column=source_column)
        source_rows = _query_records(
            source_sql,
            {**params, "source_limit": safe_source_limit},
            max_rows=safe_source_limit * 12,
        )

        profile_sql = MONTHLY_PROFILE_LEAD_TREND_SQL_TEMPLATE.format(profile_column=profile_column)
        profile_rows = _query_records(
            profile_sql,
            {**params, "profile_limit": safe_profile_limit},
            max_rows=safe_profile_limit * 12,
        )

        return _json_ready({
            "status": "success",
            "tool": "get_diagnostic_monthly_trend_overview_snapshot",
            "scope_note": SCOPE_NOTE,
            "period": periods,
            "source_basis": str(source_basis or "first").strip().lower(),
            "profile_field": profile_column,
            "source_limit": safe_source_limit,
            "profile_limit": safe_profile_limit,
            "overall_lead_trend": overall_rows,
            "revenue_trend": revenue_rows,
            "appointment_trend": appointment_rows,
            "source_lead_trend": source_rows,
            "profile_lead_trend": profile_rows,
            "summary_metrics": _monthly_trend_summary(
                overall_rows,
                revenue_rows,
                appointment_rows,
                source_rows,
                profile_rows,
            ),
            "warnings": [],
        })
    except Exception as exc:
        return _error_payload("get_diagnostic_monthly_trend_overview_snapshot", exc)
```

`_monthly_trend_summary` is optional, but useful. It can calculate:

```text
latest_month_label
highest_lead_month_label
highest_lead_count
latest_lead_count
previous_lead_count
latest_lead_change
latest_lead_percentage_change
latest_revenue
previous_revenue
latest_revenue_change
latest_revenue_percentage_change
latest_top_source
latest_top_source_lead_count
latest_top_profile
latest_top_profile_lead_count
```

This summary must only use returned rows. Do not invent values.

---

## Diagnostic Agent Prompt Update

Update `diagnostic_analytics.md` with this behavior.

```md
## Generic Monthly Trend Overview

For broad trend questions such as:

```text
What trends are you noticing?
What are the current trends?
What is changing in the business?
What should I pay attention to?
What looks different recently?
```

Call:

```text
get_diagnostic_monthly_trend_overview_snapshot
```

Do not call only `get_diagnostic_funnel_snapshot` for these questions.
Do not answer these questions as only a funnel leakage analysis.
Do not show stuck-stage reason tables unless the user specifically asks where leads are dropping or why leads are not converting.

Required output order:

1. Overall lead trend
2. Revenue trend
3. Appointment / call trend
4. Lead trend by source
5. Lead trend by profession
6. What this points to
7. Recommended next action, optional and max 1-2 bullets

Use the exact table shapes below.
```

---

## Required Final Answer Format

For generic diagnostic trend questions, use this answer shape.

```text
Trend period: <Month YYYY> through <Month YYYY> (<default/date note>)
<Highest/latest lead insight>
<Latest month vs previous month lead insight>

| Month | Lead count | Previous month | % change |
|---|---:|---:|---:|
| Feb 2026 | 82 | — | — |
| Mar 2026 | 90 | 82 | 9.76% |
| Apr 2026 | 108 | 90 | 20.00% |

Revenue trend:

| Month | Paid payments | Revenue | Previous month | % change |
|---|---:|---:|---:|---:|
| Feb 2026 | 36 | €68,500 | — | — |
| Mar 2026 | 22 | €72,500 | €68,500 | 5.84% |
| Apr 2026 | 20 | €63,000 | €72,500 | -13.10% |

Appointment trend:

| Month | Booked leads | Appointments | Completed calls | No-shows | Completed-call rate |
|---|---:|---:|---:|---:|---:|
| Feb 2026 | 70 | 75 | 52 | 18 | 69.33% |
| Mar 2026 | 76 | 82 | 55 | 21 | 67.07% |
| Apr 2026 | 86 | 95 | 58 | 28 | 61.05% |

Lead trend by source:

| Source | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Facebook | 13 | 17 (+30.77%) | 22 (+29.41%) |
| Webinar | 7 | 11 (+57.14%) | 15 (+36.36%) |
| Instagram | 12 | 8 (-33.33%) | 15 (+87.50%) |

Lead trend by profession:

| Profession | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Student | 14 | 20 (+42.86%) | 33 (+65.00%) |
| Business Owner | 28 | 31 (+10.71%) | 35 (+12.90%) |
| Trader / Investor | 12 | 15 (+25.00%) | 18 (+20.00%) |

What this points to:
- Lead volume is improving, with Apr 2026 being the strongest month.
- Revenue weakened in Apr 2026 even though lead volume increased, so lead growth is not fully converting into cash.
- Bookings increased, but the completed-call rate weakened, which suggests more appointment leakage.
- Facebook and Webinar are driving source growth.
- Student and Business Owner leads are growing, so these profiles should be checked against signed and paid conversion before scaling further.

Recommended next action:
- Compare the fastest-growing sources and professions against completed-call, signed, and paid conversion rates.

Revenue figures here are cohort-based: they show lifetime net collected revenue for leads created in the selected period, not true payment-period revenue.
```

---

## Formatting Rules for Final Answer

### Overall lead trend table

Columns:

```text
Month | Lead count | Previous month | % change
```

Rules:

- First month uses `—` for previous month and `% change`.
- Later months show previous month count and percentage change.
- Add the lead summary lines before this table.

### Revenue trend table

Columns:

```text
Month | Paid payments | Revenue | Previous month | % change
```

Rules:

- Revenue = `net_collected_amount`.
- Format revenue as `€68,500` or `€68,500.25` depending on decimals.
- First month uses `—` for previous month and `% change`.
- Add the cohort-based revenue caveat when revenue is shown.

### Appointment trend table

Columns:

```text
Month | Booked leads | Appointments | Completed calls | No-shows | Completed-call rate
```

Rules:

- Keep this table compact.
- Do not add Fathom details in generic trend answers.
- Mention Fathom only when the trend question explicitly asks about call records or call summaries.

### Source trend table

Columns:

```text
Source | <Month 1> | <Month 2> | <Month 3>
```

Rules:

- Use top sources only, default top 10.
- For first month, show only count.
- For later months, show count and percentage change.
- Example: `22 (+29.41%)`, `10 (-33.33%)`, `6 (0.00%)`.
- Sort rows by latest-month lead count DESC, then total lead count DESC, then source name ASC.

### Profession trend table

Columns:

```text
Profession | <Month 1> | <Month 2> | <Month 3>
```

Rules:

- Use top professions only, default top 10.
- For first month, show only count.
- For later months, show count and percentage change.
- Sort rows by latest-month lead count DESC, then total lead count DESC, then profession ASC.
- Add `Based on latest lead-level profile answers.` only if there is any risk of confusion.

### Summary bullets

Use heading:

```text
What this points to:
```

Rules:

- Give one bullet for lead movement.
- Give one bullet for revenue movement.
- Give one bullet for appointment/call movement.
- Give one bullet for source movement.
- Give one bullet for profession movement.
- Do not add a long recommendation.
- Do not mention funnel leakage unless it is clearly supported by appointment/signed/paid trend movement.

---

## Router Update

Update `router.md` so these generic trend-discovery questions route to `diagnostic_analytics`:

```md
- "What trends are you noticing?" → `diagnostic_analytics`
- "What are the current trends?" → `diagnostic_analytics`
- "What business trends do you see?" → `diagnostic_analytics`
- "What is changing in the business?" → `diagnostic_analytics`
- "What looks different recently?" → `diagnostic_analytics`
- "What should I pay attention to from recent trends?" → `diagnostic_analytics`
```

Keep direct single-metric trend questions in `sql_analytics`:

```md
- "Show lead trend." → `sql_analytics`
- "Show revenue trend by month." → `sql_analytics`
- "Show appointment trend." → `sql_analytics`
- "Lead trend by source." → `sql_analytics`
- "Monthly leads trend by profession." → `sql_analytics`
```

Rule:

```md
Route broad trend-discovery questions to `diagnostic_analytics` when the user is asking what the AI notices across the business rather than asking for one explicit metric trend.
```

---

## Tool Registration

Register the new tool wherever existing diagnostic tools are exposed to the diagnostic agent.

The diagnostic agent must be able to call:

```text
get_diagnostic_monthly_trend_overview_snapshot
```

Add the tool description:

```text
Returns a monthly multi-business trend overview for broad diagnostic trend questions. Includes overall lead trend, revenue trend, appointment/call trend, lead trend by source, and lead trend by profession for the selected or default period.
```

---

## Tests to Add

Add or manually validate the following tests.

### Router tests

Input:

```text
What trends are you noticing?
```

Expected:

```json
{
  "route": "diagnostic_analytics",
  "history_count": 0,
  "standalone_question": "What trends are you noticing?"
}
```

Input:

```text
What are the current trends?
```

Expected route:

```text
diagnostic_analytics
```

Input:

```text
Show lead trend by source.
```

Expected route:

```text
sql_analytics
```

Input:

```text
Monthly leads trend by profession.
```

Expected route:

```text
sql_analytics
```

### Tool tests

Call:

```python
get_diagnostic_monthly_trend_overview_snapshot(org_id="<valid_org_id>")
```

Expected:

- `status = success`
- period covers previous 3 completed months
- `overall_lead_trend` has monthly rows
- `revenue_trend` has monthly rows
- `appointment_trend` has monthly rows
- `source_lead_trend` has rows grouped by month and source
- `profile_lead_trend` has rows grouped by month and profession
- no raw SQL is exposed
- no money values are divided by 100 again

### Final answer tests

Input:

```text
What trends are you noticing?
```

Expected answer contains these sections in order:

1. `Trend period:`
2. overall lead trend table
3. `Revenue trend:`
4. revenue table
5. `Appointment trend:`
6. appointment table
7. `Lead trend by source:`
8. source pivot table
9. `Lead trend by profession:`
10. profession pivot table
11. `What this points to:`
12. optional `Recommended next action:`

Expected answer must not start with funnel leakage.
Expected answer must not show the full funnel stage table.
Expected answer must not show stuck-group reason tables.

---

## Acceptance Criteria

Implementation is complete only when all of the following are true:

- Generic trend questions route to `diagnostic_analytics`.
- Direct metric trend questions still route to `sql_analytics`.
- Diagnostic agent calls the new monthly trend overview tool for generic trend questions.
- Output starts with overall lead trend, not funnel leakage.
- Revenue table appears after lead trend.
- Appointment/call trend appears before source and profession trend.
- Source trend table uses months as columns and sources as rows.
- Profession trend table uses months as columns and professions as rows.
- Summary bullets explain the trend from each section.
- Snapshot money is not divided by 100 again.
- The answer remains compact and business-friendly.
- The output does not expose SQL, raw tool payloads, internal IDs, raw payloads, or credentials.
