# Codex Instruction: Fix “New Leads” Prompt Interpretation

## Goal

Fix the chatbot prompt so that normal business questions like:

```text
How many new leads were created on 15 May 2026?
New leads on 15th May?
How many leads came in this month?
```

count **leads created in the selected period** using `leads.created_at`.

They must **not** count only leads currently in the `NEW_LEAD` pipeline status.

This is a prompt/skill fix only. Do not build the long-term dashboard metrics table in this change.

---

## Problem

The current `lead_analytics.md` prompt has conflicting/wrong guidance.

It currently says:

```text
new lead, fresh lead -> NEW_LEAD
```

and also says:

```text
When the user asks for "new leads today", "new leads this week", or "new leads this month", combine:
ss.role = 'NEW_LEAD'
with the l.created_at timeframe filter.
```

This is wrong for dashboard-style reporting.

For business users, “new leads on 15 May” means:

```text
leads created on 15 May
```

not:

```text
leads created on 15 May that are still currently in New Lead status
```

A lead created on that day may already have moved to booked, won, lost, follow-up, no-show, etc. It should still be counted as a new lead created on that day.

---

## Scope

Update this file only:

```text
modules/lead_analytics.md
```

Do not change any other prompt, YAML, registry, router, schema, database table, metric table, diagnostic snapshot, revenue skill, appointment skill, acquisition skill, or Lead 360 logic for this fix.

Router changes are not required because this is still a direct metric/report question and should remain `sql_analytics`.

---

## Required Change 1: Update `lead_analytics.md` “When To Use” section

Find this bullet or equivalent:

```text
- New lead counts based on normalized lead status role.
```

Replace it with:

```text
- Lead creation counts and trends by today, week, month, specific date, or custom date range.
- Current New Lead status counts only when the user explicitly asks for leads currently/still in the New Lead status or New Lead pipeline stage.
```

Keep the existing bullet for lead creation counts/trends if already present, but avoid duplicate/conflicting wording.

---

## Required Change 2: Update status synonym mapping

In `lead_analytics.md`, find the status synonym mapping row:

```text
| new lead, fresh lead | `NEW_LEAD` |
```

Replace it with stricter wording:

```text
| currently in New Lead status, still in New Lead status, New Lead pipeline stage, leads with current status New Lead, status is New Lead | `NEW_LEAD` |
```

Add this note immediately under the status mapping table:

```text
Important New Lead wording rule:
- Generic phrases like "new leads", "fresh leads", "new leads today", "new leads this week", "new leads this month", "new leads on <date>", "leads came in", "leads created", or "leads generated" mean lead records created during the selected period.
- Do not map those generic phrases to `ss.role = 'NEW_LEAD'`.
- Use `ss.role = 'NEW_LEAD'` only when the user explicitly asks for current status, current stage, pipeline status, or leads still/currently in New Lead status.
```

---

## Required Change 3: Replace the full `## New Leads` section

In `lead_analytics.md`, replace the current `## New Leads` section with this:

```text
## New Leads / Leads Created

For normal business reporting, "new leads" means leads created during the selected period.

When the user asks:
- new leads today
- new leads yesterday
- new leads this week
- new leads this month
- new leads on a specific date
- how many new leads were created
- how many leads were created
- how many leads came in
- how many leads came through
- leads generated during a period
- fresh leads during a period

Use only `leads.created_at`.

Do not join `sales_statuses`.
Do not filter `ss.role = 'NEW_LEAD'`.
Do not interpret "new leads" as current New Lead pipeline status unless the user explicitly asks for:
- currently in New Lead status
- still in New Lead status
- New Lead pipeline stage
- leads with status New Lead
- leads whose current status is New Lead
- current New Lead status count

For date-based created-lead questions, use the application-provided date parameters:

```sql
l.created_at >= :start_date
AND l.created_at < :end_date
```

Correct default query pattern:

```sql
SELECT COUNT(*) AS new_leads_created
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

Only use current status logic when the user explicitly asks for current New Lead status.
```

---

## Required Change 4: Fix common query patterns

In `lead_analytics.md`, find this section:

```text
## Count New Leads
```

Rename it to:

```text
## Count Current New Lead Status
```

Keep the status-based SQL only under this renamed section, and add this warning above the SQL:

```text
Use this only when the user explicitly asks for leads currently/still in New Lead status or the New Lead pipeline stage.
Do not use this for "new leads created", "new leads today", "new leads this month", or "leads came in" questions.
```

Then find this section:

```text
## Count New Leads Created in a Date Range
```

Replace its SQL with this SQL only:

```sql
SELECT COUNT(*) AS new_leads_created_in_period
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

Important: this query must not join `sales_statuses` and must not filter `ss.role = 'NEW_LEAD'`.

---

## What To Remove or Avoid

Remove or replace these misleading instructions:

```text
When the user says "new leads" without a date range, interpret it as the normalized status role:
ss.role = 'NEW_LEAD'
```

Remove or replace this instruction:

```text
When the user asks for "new leads today", "new leads this week", or "new leads this month", combine:
ss.role = 'NEW_LEAD'
with the l.created_at timeframe filter.
```

Do not keep any common query pattern where:

```text
Count New Leads Created in a Date Range
```

uses:

```sql
LEFT JOIN sales_statuses ss ...
AND ss.role = 'NEW_LEAD'
```

That is the exact bug.

Do not remove the `NEW_LEAD` enum itself.
Do not remove status-based current New Lead reporting entirely.
Just make it explicit-status-only.

---

## Expected SQL Behavior

### Case 1: Created leads on a specific date

User:

```text
How many new leads were created on 15 May 2026?
```

Expected SQL shape:

```sql
SELECT COUNT(*) AS new_leads_created
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

Must not include:

```sql
sales_statuses
ss.role = 'NEW_LEAD'
```

---

### Case 2: Created leads this month

User:

```text
How many new leads came in this month?
```

Expected behavior:

- Use `l.created_at`.
- Use the application-provided `:start_date` and `:end_date`.
- Do not join `sales_statuses`.
- Do not filter current status.

---

### Case 3: Current New Lead status

User:

```text
How many leads are currently in New Lead status?
```

Expected behavior:

- Join `sales_statuses`.
- Filter `ss.role = 'NEW_LEAD'`.
- Do not require a created date range unless the user also asks for one.

Expected SQL shape:

```sql
SELECT COUNT(*) AS current_new_lead_status_count
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NEW_LEAD';
```

---

## Tests To Add or Manually Verify

Add or run prompt/agent tests for these questions.

### Should use `l.created_at` only

```text
How many new leads were created on 15 May 2026?
New leads on 15th May?
How many new leads came in this month?
How many fresh leads came through last week?
How many leads were generated yesterday?
Show lead creation count for April.
```

Expected:

- Route: `sql_analytics`
- Skill: `lead_analytics`
- SQL must use `l.created_at`
- SQL must not join `sales_statuses`
- SQL must not use `ss.role = 'NEW_LEAD'`

### Should use current status

```text
How many leads are currently in New Lead status?
Show leads still in the New Lead pipeline stage.
Which leads have current status New Lead?
Count leads whose status is New Lead.
```

Expected:

- Route: `sql_analytics`
- Skill: `lead_analytics`
- SQL should join `sales_statuses`
- SQL should filter `ss.role = 'NEW_LEAD'` or exact status name if the user asks for exact label

---

## Acceptance Criteria

The change is successful when:

1. Date-based “new leads” questions count all non-deleted leads created in the selected period.
2. Date-based “new leads” SQL does not join `sales_statuses`.
3. Date-based “new leads” SQL does not filter `ss.role = 'NEW_LEAD'`.
4. Explicit current-status questions still support `ss.role = 'NEW_LEAD'`.
5. Existing lead trend behavior continues to use `l.created_at`.
6. No database schema or table changes are made for this prompt-only fix.

Strictly follow the above instructions.
