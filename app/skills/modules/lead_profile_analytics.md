# Skill: `lead_profile_analytics`

## Short Description

Use this skill for read-only SQL analytics about lead-level profile attributes derived from latest opt-in form answers, especially profession/work/occupation and employment status/job status.

This skill must generate SQL only. The application will execute the SQL through a safe read-only database helper.

## When To Use This Skill

Use `lead_profile_analytics` for direct count, ranking, distribution, and trend questions about profile fields collected in opt-in form answers.

Use this skill for:

- Lead count by profession, work, job, occupation, or role.
- Lead count by employment status, working status, job status, employment, or work status.
- Opt-in count by profession or employment status when the user explicitly says opt-ins, submissions, form submissions, registrations, or submitted forms.
- Monthly, weekly, or daily lead trends by profession or employment status.
- Recently joined or increasing profile groups.
- Profile distributions by month.

Do not use this skill for:

- Root-cause diagnosis, recommendations, or conversion-quality diagnostics. Use `diagnostic_analytics`.
- One specific lead/person profile questions. Use Lead 360.
- LLM inference of profession or employment status.

## Primary Skill Rule

This skill is the primary skill when the user asks about:

```text
profession
work
job
occupation
role
employment status
working status
job status
employment
work status
lead profile distribution
profile opt-in count
profile trend
```

When `lead_profile_analytics` is primary, it controls profile question mapping, latest profile answer selection, lead-level vs opt-in-level grain, profile trend grouping, and profile distribution logic.

## Grain Rules

Lead-level questions use one row per lead and the latest non-empty profile answer per lead.

Examples:

```text
Which profession generated the most leads?
Monthly leads trend by profession.
Which employment status is most common among leads?
How many leads are Business Owner?
Which professions joined recently?
```

Use:

```sql
COUNT(DISTINCT l.id)
```

For lead trend questions, use `leads.created_at` as the date field.

Opt-in-level questions use opt-in/form-submission grain only when the user explicitly says opt-ins, submissions, form submissions, registrations, or submitted forms.

Examples:

```text
Which profession submitted the most opt-ins?
Show opt-in count by profession.
Which employment status submitted the most forms?
```

Use:

```sql
COUNT(*)
```

from `opt_ins` joined to `opt_in_question_answers`.

## Profile Question Mapping

Profession aliases:

```text
profession
work
job
occupation
role
what do leads do
what do they do for work
```

Map to the actual form question:

```text
What do you do for work?
```

Employment status aliases:

```text
employment status
working status
job status
employment
work status
```

Map to the actual form question:

```text
What is your employment status?
```

Never generate SQL like:

```sql
WHERE q.question = 'profession'
```

Use the mapped form question:

```sql
LOWER(TRIM(q.question)) = LOWER('What do you do for work?')
```

The actual schema columns are `q.question` and `q.answer`.

## Latest Lead-Level CTEs

Latest profession:

```sql
latest_profession AS (
  SELECT DISTINCT ON (o.lead_id)
    o.lead_id,
    NULLIF(TRIM(q.answer), '') AS latest_profession
  FROM opt_ins o
  JOIN opt_in_question_answers q
    ON q.opt_in_id = o.id
  WHERE o.clerk_org_id = :org_id
    AND NULLIF(TRIM(q.answer), '') IS NOT NULL
    AND LOWER(TRIM(q.question)) = LOWER('What do you do for work?')
  ORDER BY
    o.lead_id,
    COALESCE(q.created_at, o.created_at) DESC,
    o.created_at DESC,
    o.id DESC
)
```

Latest employment status:

```sql
latest_employment_status AS (
  SELECT DISTINCT ON (o.lead_id)
    o.lead_id,
    NULLIF(TRIM(q.answer), '') AS latest_employment_status
  FROM opt_ins o
  JOIN opt_in_question_answers q
    ON q.opt_in_id = o.id
  WHERE o.clerk_org_id = :org_id
    AND NULLIF(TRIM(q.answer), '') IS NOT NULL
    AND LOWER(TRIM(q.question)) = LOWER('What is your employment status?')
  ORDER BY
    o.lead_id,
    COALESCE(q.created_at, o.created_at) DESC,
    o.created_at DESC,
    o.id DESC
)
```

## Lead Count By Profession

For `Which profession generated the most leads?`, use lead-level grain:

```sql
WITH latest_profession AS (
  SELECT DISTINCT ON (o.lead_id)
    o.lead_id,
    NULLIF(TRIM(q.answer), '') AS latest_profession
  FROM opt_ins o
  JOIN opt_in_question_answers q
    ON q.opt_in_id = o.id
  WHERE o.clerk_org_id = :org_id
    AND NULLIF(TRIM(q.answer), '') IS NOT NULL
    AND LOWER(TRIM(q.question)) = LOWER('What do you do for work?')
  ORDER BY
    o.lead_id,
    COALESCE(q.created_at, o.created_at) DESC,
    o.created_at DESC,
    o.id DESC
)
SELECT
  COALESCE(lp.latest_profession, 'Not provided') AS profession,
  COUNT(DISTINCT l.id)::int AS lead_count,
  ROUND(
    100.0 * COUNT(DISTINCT l.id) / NULLIF(SUM(COUNT(DISTINCT l.id)) OVER (), 0),
    2
  ) AS share_of_leads,
  SUM(COUNT(DISTINCT l.id)) OVER ()::int AS total_matching_leads
FROM leads l
LEFT JOIN latest_profession lp
  ON lp.lead_id = l.id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(lp.latest_profession, 'Not provided')
ORDER BY lead_count DESC, profession ASC
LIMIT :limit
```

## Opt-In Count By Profession

For `Which profession submitted the most opt-ins?`, use opt-in-level grain:

```sql
SELECT
  COALESCE(NULLIF(TRIM(q.answer), ''), 'Not provided') AS profession,
  COUNT(*)::int AS opt_in_count,
  COUNT(DISTINCT o.lead_id)::int AS unique_leads,
  ROUND(
    100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0),
    2
  ) AS share_of_opt_ins,
  SUM(COUNT(*)) OVER ()::int AS total_matching_opt_ins
FROM opt_ins o
JOIN opt_in_question_answers q
  ON q.opt_in_id = o.id
WHERE o.clerk_org_id = :org_id
  AND LOWER(TRIM(q.question)) = LOWER('What do you do for work?')
GROUP BY COALESCE(NULLIF(TRIM(q.answer), ''), 'Not provided')
ORDER BY opt_in_count DESC, profession ASC
LIMIT :limit
```

## Monthly Lead Trend By Profession

For `Monthly leads trend by profession`, use lead-level grain and row-based SQL output. Do not generate hardcoded SQL pivot columns.

```sql
WITH latest_profession AS (
  SELECT DISTINCT ON (o.lead_id)
    o.lead_id,
    NULLIF(TRIM(q.answer), '') AS latest_profession
  FROM opt_ins o
  JOIN opt_in_question_answers q
    ON q.opt_in_id = o.id
  WHERE o.clerk_org_id = :org_id
    AND NULLIF(TRIM(q.answer), '') IS NOT NULL
    AND LOWER(TRIM(q.question)) = LOWER('What do you do for work?')
  ORDER BY
    o.lead_id,
    COALESCE(q.created_at, o.created_at) DESC,
    o.created_at DESC,
    o.id DESC
),
base AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    TO_CHAR(DATE_TRUNC('month', l.created_at)::date, 'Mon YYYY') AS month_label,
    COALESCE(lp.latest_profession, 'Not provided') AS profession,
    l.id AS lead_id
  FROM leads l
  LEFT JOIN latest_profession lp
    ON lp.lead_id = l.id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= CAST(:start_date AS date)
    AND l.created_at < CAST(:end_date AS date)
),
monthly_counts AS (
  SELECT
    month_start,
    month_label,
    profession,
    COUNT(DISTINCT lead_id)::int AS lead_count
  FROM base
  GROUP BY month_start, month_label, profession
),
monthly_totals AS (
  SELECT
    month_start,
    COUNT(DISTINCT lead_id)::int AS total_month_leads
  FROM base
  GROUP BY month_start
)
SELECT
  mc.month_start,
  mc.month_label,
  mc.profession,
  mc.lead_count,
  LAG(mc.lead_count) OVER (
    PARTITION BY mc.profession
    ORDER BY mc.month_start
  ) AS previous_period_lead_count,
  ROUND(
    100.0 * (
      mc.lead_count
      - LAG(mc.lead_count) OVER (
          PARTITION BY mc.profession
          ORDER BY mc.month_start
        )
    )
    / NULLIF(
        LAG(mc.lead_count) OVER (
          PARTITION BY mc.profession
          ORDER BY mc.month_start
        ),
        0
      ),
    2
  ) AS percentage_change,
  mt.total_month_leads,
  ROUND(
    100.0 * mc.lead_count / NULLIF(mt.total_month_leads, 0),
    2
  ) AS share_of_month_leads,
  SUM(mc.lead_count) OVER ()::int AS total_matching_leads
FROM monthly_counts mc
JOIN monthly_totals mt
  ON mt.month_start = mc.month_start
ORDER BY
  mc.month_start ASC,
  mc.lead_count DESC,
  mc.profession ASC
```

## Employment Status Patterns

For employment-status questions, use the same logic but replace:

```text
profession
latest_profession
What do you do for work?
```

with:

```text
employment_status
latest_employment_status
What is your employment status?
```

## Trend Answer Formatting

For profile trend answers, keep SQL output row-based and format the final answer as a pivot-style table.

Before the table, include:

```text
Trend period: <first month> through <last month> (<default/date-range note>)
Total matching leads: <total>
In <latest month>, <top profile group> generated the most leads at <count>, <change text from previous month>
Based on latest lead-level profile answers.
```

If previous month value is zero or missing, do not invent percentage change.

For the first month, show only the count. For later months, show `<count> (<percentage_change>%)`, such as `20 (+25.00%)`, `15 (-6.25%)`, or `8 (0.00%)`.

Default final pivot table sort:

```text
latest month lead_count DESC
then total lead_count across displayed period DESC
then alphabetical
```

Do not say exact opt-in submission trend unless the SQL is opt-in-level.
