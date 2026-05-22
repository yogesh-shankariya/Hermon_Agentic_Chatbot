# Codex Instruction: Fix “Call Taken / Completed Call” Logic in `appointment_analytics.md`

## Goal

Update only `appointment_analytics.md` so that questions like:

```text
How many calls were taken on 15 May 2026?
How many calls happened that day?
How many completed calls were there?
How many attended calls were there?
```

count only real attended/completed calls.

A cancelled or rescheduled appointment must not be counted as a call taken, even if `a.no_show = false`.

## Scope

Modify only:

```text
modules/appointment_analytics.md
```

Do not change:

```text
1_0_0.yaml
registry.yaml
router.md
other skill files
application routing logic
answer formatting prompt
```

This is a metric-definition fix inside the appointment analytics skill only.

## Problem

The current completed/attended call rule is too loose:

```sql
a.schedule_time < NOW()
AND a.no_show = false
```

This can incorrectly count cancelled or rescheduled appointments as completed/taken calls when those appointments are not marked as no-show.

## Required Business Definition

For appointment analytics, treat these phrases as the same metric:

```text
call taken
call happened
completed call
attended call
completed attended call
non-no-show completed call
```

The metric must mean:

```text
Non-deleted appointment
+ scheduled in the past
+ no_show = false
+ appointment outcome is not CANCELED
+ appointment outcome is not RESCHEDULED
+ appointment outcome is not NO_SHOW
```

Use `appointments.schedule_time` as the timing field for when the call was supposed to happen.

## Required SQL Pattern

Wherever `appointment_analytics.md` defines completed, attended, or call-taken appointments, use this pattern:

```sql
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id

WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND a.no_show = false
  AND COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED', 'NO_SHOW')
```

Important:

- Use `LEFT JOIN`, not `INNER JOIN`, because older valid appointments may not have an outcome row.
- Keep null/no-outcome appointments eligible if they satisfy the other completed-call conditions.
- Do not rely only on `a.no_show = false`.
- Do not use `outcome.role = 'NO_SHOW'` as the primary no-show flag. Keep `a.no_show` as the primary no-show flag, and use `outcome.role` only to exclude cancelled/rescheduled/no-show outcomes from completed/taken calls.

## Replace This Section

Find the section:

```text
## Past and Completed Appointments
```

Replace the completed/attended part with this wording:

```markdown
## Past and Completed Appointments

When the user asks for past appointments, previous appointments, call history, or previous calls, use:

```sql
a.schedule_time < NOW()
```

If the user specifically asks for attended, completed, completed non-no-show, call taken, or call happened, count only appointments that were actually eligible as completed calls:

```sql
a.schedule_time < NOW()
AND a.no_show = false
AND COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED', 'NO_SHOW')
```

For completed/attended/call-taken queries, join appointment outcomes like this:

```sql
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
```

Do not count cancelled or rescheduled appointments as completed/taken calls.
```

## Replace The Common Query Pattern

Find the section:

```text
## Count Completed Attended Calls
```

Replace the SQL with:

```sql
SELECT COUNT(*) AS completed_attended_calls
FROM appointments a
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND a.no_show = false
  AND COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED', 'NO_SHOW');
```

## Add A Date-Range Example For “Calls Taken On A Day”

Add this new common query pattern near the completed attended calls section:

```markdown
## Count Calls Taken In A Date Range

Use this when the user asks how many calls were taken, completed, attended, or happened on a specific day or within a specific date range.

```sql
SELECT COUNT(*) AS calls_taken_in_period
FROM appointments a
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
  AND a.no_show = false
  AND COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED', 'NO_SHOW');
```
```

## Update Mistakes To Avoid

Add these bullets under `## Mistakes To Avoid`:

```markdown
- Do not count cancelled appointments as completed, attended, happened, or taken calls.
- Do not count rescheduled appointments as completed, attended, happened, or taken calls.
- Do not treat `a.no_show = false` alone as proof that a call was taken; also exclude outcome roles `CANCELED`, `RESCHEDULED`, and `NO_SHOW`.
```

## Do Not Change No-Show Rate Logic

No-show rate should still use `a.no_show = true` as the primary no-show definition.

Do not change this logic:

```sql
a.no_show = true
```

The outcome-role exclusion is only for completed/attended/call-taken metrics.

## Acceptance Criteria

After the change, generated SQL for:

```text
How many calls were taken on 15 May 2026?
```

must include:

```sql
FROM appointments a
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
  AND a.no_show = false
  AND COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED', 'NO_SHOW')
```

It must not generate SQL that counts only this:

```sql
a.schedule_time < NOW()
AND a.no_show = false
```

## Final Reminder

Keep the change minimal and strictly limited to `appointment_analytics.md`.
