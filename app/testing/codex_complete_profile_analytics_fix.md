# Codex Task — Complete Profile Analytics Fix

## Goal

Fix profile analytics properly and avoid creating a new diagnostic tool for every profile question.

This file includes all required corrections:

```text
1. Do not distribute profession evenly in dummy data.
2. Fix employment-status distribution so it is not evenly distributed.
3. Route generic profile count/trend/distribution questions to SQL analytics.
4. Keep profile conversion/recommendation/root-cause questions in diagnostic analytics.
5. Create or update a generic SQL skill for lead profile analytics.
6. Support natural language aliases like profession, occupation, work, employment status.
7. Format monthly profile trend answers like existing source trend answers.
8. Keep diagnostic conversion answers working.
```

---

# 1. Current Problems

## Problem 1 — Profession distribution looks fake

Current answer:

```text
Based on the latest lead-level opt-in profile answer, there is a tie: all 10 returned profession groups generated 50 leads each.
```

This is bad for demo because it looks artificial.

Do not distribute professions evenly.

---

## Problem 2 — Monthly profile trend questions are not supported

Question:

```text
monthly leads trends by profession
```

Current answer says it is unsupported.

This should be supported through SQL analytics, not diagnostic analytics.

---

## Problem 3 — Too many diagnostic tools

Do not create a new diagnostic tool for every profile trend/count question.

Generic profile count/trend/distribution questions should be handled by SQL analytics.

Diagnostic analytics should remain focused on business diagnosis, conversion quality, root cause, and recommendation.

---

# 2. Final Routing Decision

Use this split:

```text
Generic count / trend / distribution / ranking
→ sql_analytics

Conversion quality / recommendation / why / root cause
→ diagnostic_analytics
```

---

## Route to SQL Analytics

Route these questions to:

```text
sql_analytics
```

Examples:

```text
Which profession submitted the most opt-ins?
Which profession generated the most leads?
Which employment status is most common?
Monthly leads trend by profession.
Show monthly lead trend by profession.
Show profession distribution by month.
Which professions joined mostly recently?
Which professions are increasing recently?
Monthly leads trend by employment status.
Which employment status is increasing recently?
How many leads are business owners?
Show lead count by employment status.
Show opt-in count by profession.
```

These are direct count/trend/distribution questions.

---

## Route to Diagnostic Analytics

Route these questions to:

```text
diagnostic_analytics
```

Examples:

```text
Which profession converts best?
Which employment status has the highest paid conversion?
Which profession should we focus on?
Which profession has high volume but weak conversion?
Why are Business Owner leads not converting?
Why are self-employed leads converting better?
Which employment status should sales prioritize?
```

These require conversion quality, recommendation, or diagnosis.

---

# 3. Router Changes

Update `router.md`.

## Remove from diagnostic generic examples

Remove or stop routing these to diagnostic:

```text
Which profession generated the most leads?
Which profession submitted the most opt-ins?
Which employment status is most common?
Monthly leads trend by profession.
Monthly leads trend by employment status.
Which professions joined mostly recently?
Which professions are increasing recently?
```

## Add SQL examples

Add:

```text
"Which profession submitted the most opt-ins?" -> sql_analytics
"Which profession generated the most leads?" -> sql_analytics
"Which employment status is most common?" -> sql_analytics
"Monthly leads trend by profession." -> sql_analytics
"Show profession distribution by month." -> sql_analytics
"Which professions joined mostly recently?" -> sql_analytics
"Which professions are increasing recently?" -> sql_analytics
"Monthly leads trend by employment status." -> sql_analytics
```

## Keep diagnostic examples

Keep:

```text
"Which profession converts best?" -> diagnostic_analytics
"Which employment status has the highest paid conversion?" -> diagnostic_analytics
"Which profession should we focus on?" -> diagnostic_analytics
"Why are Business Owner leads not converting?" -> diagnostic_analytics
"Which profession has high volume but weak conversion?" -> diagnostic_analytics
```

---

# 4. Create New SQL Skill

Create a new skill:

```text
modules/lead_profile_analytics.md
```

This skill should handle read-only SQL analytics about lead-level profile attributes derived from latest opt-in answers.

---

## Add to Registry

Update `registry.yaml`:

```yaml
- name: lead_profile_analytics
  description: "Use for read-only SQL analytics about lead-level profile attributes derived from latest opt-in form answers, especially latest profession/work/occupation and latest employment status/job status. Supports lead counts, opt-in counts, distributions, monthly trends, recently joined groups, and profile trend analysis. Do not use for root-cause diagnosis, recommendations, or conversion-quality diagnostics; use diagnostic_analytics for those."
  path: modules/lead_profile_analytics.md
  primary_tables:
    - leads
    - opt_ins
    - opt_in_question_answers
    - sales_statuses
```

Ensure the skill is added to the enabled SQL skill list if there is a separate config.

---

# 5. SQL Agent Skill Selection Update

Update SQL agent instructions so the new skill is selected.

Add primary skill rule:

```text
Profession, work, occupation, employment status, job status, lead profile distribution, profile opt-in count, and profile trends
→ primary skill is lead_profile_analytics
```

Examples:

```text
Which profession generated the most leads? -> lead_profile_analytics
Monthly leads trend by profession. -> lead_profile_analytics
Which employment status is most common? -> lead_profile_analytics
Which profession submitted the most opt-ins? -> lead_profile_analytics
```

If `lead_profile_analytics` is primary, it controls:

```text
profile question mapping
latest profile answer selection
lead-level vs opt-in-level grain
profile trend grouping
profile distribution logic
```

---

# 6. Lead-Level vs Opt-In-Level Meaning

This is critical.

## Lead-Level Questions

Use one row per lead and latest non-empty answer.

Examples:

```text
Which profession generated the most leads?
Monthly leads trend by profession.
Which employment status is most common among leads?
How many leads are business owners?
Which professions joined recently?
```

Use:

```text
COUNT(DISTINCT l.id)
```

Date field for lead trend:

```text
leads.created_at
```

---

## Opt-In-Level Questions

Use opt-in/form-submission grain only when the user explicitly says:

```text
opt-ins
submissions
form submissions
registrations
submitted forms
```

Examples:

```text
Which profession submitted the most opt-ins?
Show opt-in count by profession.
Which employment status submitted the most forms?
```

Use:

```text
COUNT(*) from opt_ins joined to opt_in_question_answers
```

A single lead can have multiple opt-ins, so opt-in count can be higher than lead count.

---

# 7. Natural Language Alias Mapping

The skill must map natural language to actual form questions.

## Profession

User may say:

```text
profession
work
job
occupation
role
what do leads do
what do they do for work
```

Actual form question:

```text
What do you do for work?
```

## Employment Status

User may say:

```text
employment status
working status
job status
employment
work status
```

Actual form question:

```text
What is your employment status?
```

Do not generate SQL like:

```sql
WHERE q.question = 'profession'
```

Use the mapped form question:

```sql
WHERE LOWER(TRIM(q.question)) = LOWER('What do you do for work?')
```

---

# 8. Latest Lead-Level Profile CTEs

Use these patterns for lead-level profile analytics.

## Latest Profession

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

## Latest Employment Status

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

Important:

```text
Use q.question and q.answer if these are the actual schema columns.
Do not use q.question_text or q.answer_text unless that is the actual schema.
```

---

# 9. SQL Pattern — Lead Count by Profession

For:

```text
Which profession generated the most leads?
```

Use lead-level grain.

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
LIMIT :limit;
```

---

# 10. SQL Pattern — Opt-In Count by Profession

For:

```text
Which profession submitted the most opt-ins?
```

Use opt-in-level grain.

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
LIMIT :limit;
```

---

# 11. SQL Pattern — Monthly Lead Trend by Profession

For:

```text
Monthly leads trend by profession.
```

Use lead-level grain and row-based SQL output.

Do not generate hardcoded SQL pivot columns.

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
  mc.profession ASC;
```

---

# 12. Employment Status Patterns

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

---

# 13. Trend Answer Formatting

For profile trend questions, final answer should look like the existing source trend answer.

## Desired Shape

```text
Trend period: Feb 2026 through Apr 2026 (default previous 3 completed months)
Total matching leads: 280
In Apr 2026, Business Owner generated the most leads at 28, up 40.00% from Mar 2026
```

Then pivot-style table:

```markdown
| Profession | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Business Owner | 16 | 20 (+25.00%) | 28 (+40.00%) |
| Employee | 14 | 15 (+7.14%) | 16 (+6.67%) |
| Self-employed | 11 | 13 (+18.18%) | 16 (+23.08%) |
```

Important:

```text
The SQL output must stay row-based.
The final answer can pivot rows for readability.
Do not generate hardcoded SQL pivot columns.
```

---

## Trend Summary Rules

Before the table, include:

```text
Trend period: <first month> through <last month> (<default/date-range note>)
Total matching leads: <total>
In <latest month>, <top profile group> generated the most leads at <count>, <change text from previous month>
```

If previous month value is zero or missing, say:

```text
In Apr 2026, Business Owner generated the most leads at 28.
```

Do not invent percentage change if denominator is zero or unavailable.

---

## Trend Table Rules

For the first month, show only the count:

```text
16
```

For later months, show:

```text
<count> (<percentage_change>%)
```

Examples:

```text
20 (+25.00%)
15 (-6.25%)
8 (0.00%)
```

If percentage cannot be safely calculated, show only the count.

Default sort for final pivot table:

```text
latest month lead_count DESC
then total lead_count across displayed period DESC
then alphabetical
```

---

## Lead-Level Wording Rule

For lead-level profile trends, include:

```text
Based on latest lead-level profile answers.
```

or:

```text
This is based on the latest lead-level opt-in profile answer.
```

Do not say:

```text
exact opt-in submission trend
```

unless it is opt-in-level.

---

# 14. Dummy Data Distribution Fix

Fix `scripts/seed_demo_data.py`.

The current profession values are too evenly distributed.

## Required Profession Distribution

Use this weighted distribution for 500 demo leads:

| Profession | Leads |
|---|---:|
| Business Owner | 101 |
| Employee | 85 |
| Self-employed | 65 |
| Sales or Marketing | 55 |
| Technology | 51 |
| Trader / Investor | 44 |
| Healthcare | 37 |
| Student | 33 |
| Retired | 19 |
| Unemployed | 10 |
| Total | 500 |

## Required Monthly Profession Distribution

Monthly lead totals must remain unchanged:

```text
Nov 2025 = 55
Dec 2025 = 70
Jan 2026 = 95
Feb 2026 = 82
Mar 2026 = 90
Apr 2026 = 108
Total = 500
```

Use:

| Month | Business Owner | Employee | Self-employed | Sales or Marketing | Technology | Trader / Investor | Healthcare | Student | Retired | Unemployed | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nov 2025 | 8 | 10 | 6 | 6 | 5 | 4 | 5 | 6 | 3 | 2 | 55 |
| Dec 2025 | 11 | 13 | 7 | 8 | 7 | 5 | 6 | 7 | 4 | 2 | 70 |
| Jan 2026 | 18 | 17 | 12 | 10 | 10 | 8 | 7 | 7 | 4 | 2 | 95 |
| Feb 2026 | 16 | 14 | 11 | 9 | 9 | 7 | 6 | 5 | 3 | 2 | 82 |
| Mar 2026 | 20 | 15 | 13 | 10 | 9 | 9 | 6 | 4 | 3 | 1 | 90 |
| Apr 2026 | 28 | 16 | 16 | 12 | 11 | 11 | 7 | 4 | 2 | 1 | 108 |

This creates a realistic trend:

```text
Business Owner increases strongly in recent months.
Self-employed increases gradually.
Trader / Investor increases gradually.
Employee stays important but flatter.
Student, Retired, and Unemployed remain smaller.
```

---

## Implementation Rule

Assign profession at lead level, not opt-in row level.

Suggested approach:

```python
profession_by_lead_id[lead_id] = assigned_profession
```

Then when generating form answers:

```python
if question == "What do you do for work?":
    answer = profession_by_lead_id[lead_id]
```

If one lead has multiple opt-ins, the latest opt-in should still contain the same assigned profession.

Do not rotate profession by opt-in row.

---

# 15. Employment Status Distribution Fix

Do not distribute employment status evenly.

Use a weighted distribution across 500 leads.

Example:

| Employment status | Leads |
|---|---:|
| Full-time employed | 160 |
| Business owner | 105 |
| Self-employed | 95 |
| Part-time employed | 50 |
| Student | 35 |
| Unemployed | 25 |
| Retired | 20 |
| Career break / homemaker | 10 |
| Total | 500 |

If the current seed script has different labels, keep the existing labels but apply a non-even weighted distribution.

Do not use:

```text
Unknown
```

Do not assign every employment status the same count.

---

# 16. Diagnostic Analytics Changes

Update `diagnostic_analytics.md`.

## Remove Generic Profile Count/Trend Support

Remove or stop listing these as diagnostic-supported questions:

```text
Which profession generated the most leads?
Which profession submitted the most opt-ins?
Which employment status is most common?
Monthly leads trend by profession.
Monthly leads trend by employment status.
Which professions joined mostly recently?
Which professions are increasing recently?
```

These now belong to SQL analytics.

## Keep Diagnostic Profile Conversion Support

Keep:

```text
Which profession converts best?
Which employment status has the highest paid conversion?
Which profession should we focus on?
Which profession has high volume but weak conversion?
Why are Business Owner leads not converting?
```

Diagnostic can keep using existing profile conversion logic if it is already working.

Do not add a new diagnostic profile trend tool.

---

# 17. Do Not Add Diagnostic Profile Trend Tool

Do not add:

```text
get_diagnostic_profile_trend_snapshot
```

If this was partially added, remove it unless it is already required elsewhere.

Reason:

```text
Generic profile trends should be solved by SQL analytics using the new lead_profile_analytics skill.
```

---

# 18. Validation and Tests

## Router Tests

Add tests:

```text
Which profession submitted the most opt-ins? -> sql_analytics
Which profession generated the most leads? -> sql_analytics
Which employment status is most common? -> sql_analytics
Monthly leads trend by profession. -> sql_analytics
Which professions joined mostly recently? -> sql_analytics
Which professions are increasing recently? -> sql_analytics
Monthly leads trend by employment status. -> sql_analytics

Which profession converts best? -> diagnostic_analytics
Which employment status has the highest paid conversion? -> diagnostic_analytics
Which profession should we focus on? -> diagnostic_analytics
Why are Business Owner leads not converting? -> diagnostic_analytics
```

## SQL Skill Tests

Add tests:

```text
profession alias maps to "What do you do for work?"
employment status alias maps to "What is your employment status?"
lead-level profession count uses COUNT(DISTINCT l.id)
opt-in-level profession count uses COUNT(*) from opt_ins/question answers
monthly trend groups by DATE_TRUNC('month', l.created_at)
query uses :org_id
query excludes l.is_deleted = false for lead-level queries
```

## Seed Validation

Add checks:

```text
latest_profession counts are not evenly distributed
Business Owner = 101
Employee = 85
Self-employed = 65
profession total = 500
monthly profession totals reconcile to monthly lead totals
latest_employment_status counts are not evenly distributed
no latest_profession value is Unknown
no latest_employment_status value is Unknown
```

---

# 19. Expected Answers

## Question

```text
Which profession generated the most leads?
```

Expected answer:

```markdown
Business Owner generated the most leads based on the latest lead-level opt-in profile answer.

| Profession | Leads | Share of leads |
|---|---:|---:|
| Business Owner | 101 | 20.20% |
| Employee | 85 | 17.00% |
| Self-employed | 65 | 13.00% |
```

---

## Question

```text
Which profession submitted the most opt-ins?
```

Expected answer:

```markdown
Business Owner had the most opt-in submissions by profession.

| Profession | Opt-ins | Unique leads | Share of opt-ins |
|---|---:|---:|---:|
| Business Owner | ... | ... | ... |
```

---

## Question

```text
Monthly leads trend by profession.
```

Expected answer style:

```markdown
Trend period: Feb 2026 through Apr 2026 (default previous 3 completed months)
Total matching leads: 280
In Apr 2026, Business Owner generated the most leads at 28, up 40.00% from Mar 2026

Based on latest lead-level profile answers.

| Profession | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Business Owner | 16 | 20 (+25.00%) | 28 (+40.00%) |
| Employee | 14 | 15 (+7.14%) | 16 (+6.67%) |
| Self-employed | 11 | 13 (+18.18%) | 16 (+23.08%) |
| Sales or Marketing | 9 | 10 (+11.11%) | 12 (+20.00%) |
| Trader / Investor | 7 | 9 (+28.57%) | 11 (+22.22%) |
| Technology | 9 | 9 (0.00%) | 11 (+22.22%) |
| Healthcare | 6 | 6 (0.00%) | 7 (+16.67%) |
| Student | 5 | 4 (-20.00%) | 4 (0.00%) |
| Retired | 3 | 3 (0.00%) | 2 (-33.33%) |
| Unemployed | 2 | 1 (-50.00%) | 1 (0.00%) |
```

---

# 20. Do Not Do

Do not:

```text
Do not distribute professions evenly.
Do not leave all professions at 50 leads each.
Do not distribute employment statuses evenly.
Do not route generic profile counts/trends to diagnostic_analytics.
Do not create get_diagnostic_profile_trend_snapshot.
Do not create a new diagnostic tool for every profile trend.
Do not use diagnostic_text_insights for profession or employment-status distribution.
Do not infer profession using an LLM.
Do not require exact user wording like "What do you do for work?"
Do not search q.question = 'profession'.
Do not count opt-ins when the user asks for lead count.
Do not count leads when the user explicitly asks for opt-ins/submissions.
Do not break existing diagnostic conversion answers like "Which profession converts best?"
```

---

# 21. Definition of Done

This task is complete when:

```text
Dummy profession distribution is realistic and no longer equal 50 per group.
Dummy employment status distribution is realistic and not evenly distributed.
A generic lead_profile_analytics SQL skill exists.
Router sends profile count/trend/distribution questions to sql_analytics.
Router keeps profile conversion/recommendation/why questions in diagnostic_analytics.
SQL analytics can answer profession and employment-status count/trend questions.
"Which profession submitted the most opt-ins?" works.
"Which profession generated the most leads?" works.
"Monthly leads trend by profession" works and is formatted like source trend.
"Which employment status is most common?" works.
"Which profession converts best?" still works through diagnostic analytics.
Validation passes.
Existing demo questions continue to work.
```
