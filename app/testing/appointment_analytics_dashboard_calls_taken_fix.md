# Codex Instruction: Align `appointment_analytics.md` Calls Taken With Dashboard Metrics Reference

## Goal

Update only:

```text
modules/appointment_analytics.md
```

Do not update `1_0_0.yaml`, `router.md`, `registry.yaml`, or other skills unless existing tests fail because of wording-only references.

The issue is not routing. The issue is the `appointment_analytics` business definition for “calls taken”, “completed calls”, “attended calls”, and “held calls”. It currently risks counting appointments using only `a.schedule_time < NOW()` and `a.no_show = false`, which can incorrectly include canceled or rescheduled appointments.

The chatbot must align dashboard-style appointment metrics with `dashboard_metrics_reference.md`.

---

## Dashboard reference rule to apply

Use this dashboard definition for dashboard-style appointment metrics:

```text
The dashboard KPI calculator deduplicates appointment-based metrics by lead.
For each lead, only the latest appointment in the selected input period is used.

Completed/taken outcome roles:
- WON
- PARTIAL_PAYMENT
- FOLLOW_UP
- LOST
- UNQUALIFIED

Excluded / scheduled-false outcome roles:
- CANCELED
- RESCHEDULED

No-show:
- outcome role is NO_SHOW
- OR appointments.no_show = true

Calls taken:
- unique leads whose latest past appointment in the selected period has a completed/taken outcome role.
```

Important: `a.no_show = false` alone is not enough for “calls taken”. A taken call must have `outcome.role` in the completed/taken group.

---

## Required skill wording changes

In `appointment_analytics.md`, update the business interpretation for completed / attended / taken calls.

Replace the current completed-call wording that says, or implies:

```sql
 a.schedule_time < NOW()
 AND a.no_show = false
```

with this instruction:

```text
For dashboard-style “calls taken”, “completed calls”, “attended calls”, or “held calls”, follow the dashboard KPI definition:

- Use appointment scheduled time as the period filter.
- Deduplicate to the latest appointment per lead inside the selected period.
- Keep only latest appointments whose scheduled time is in the past.
- Count only outcome roles in `WON`, `PARTIAL_PAYMENT`, `FOLLOW_UP`, `LOST`, or `UNQUALIFIED`.
- Do not count `CANCELED`, `RESCHEDULED`, or `NO_SHOW` as calls taken.
- Do not use `a.no_show = false` alone as the completed-call definition.
```

Keep the existing appointment date handling unchanged:

```sql
 a.schedule_time >= :start_date
 AND a.schedule_time < :end_date
```

Do not add timezone conversion logic in this patch.

---

## Required SQL pattern for `calls_taken`

Add or replace the common pattern for “Count Completed Attended Calls” / “Calls Taken” with this SQL:

```sql
WITH appointment_base AS (
  SELECT
    a.id AS appointment_id,
    a.lead_id,
    a.schedule_time,
    a.host_id,
    a.setter_id,
    a.snapshot_event_name,
    a.snapshot_call_category,
    a.source AS appointment_source,
    a.no_show,
    outcome.name AS outcome_name,
    CAST(outcome.role AS text) AS outcome_role
  FROM appointments a
  LEFT JOIN sales_statuses outcome
    ON outcome.id = a.outcome_id
   AND outcome.clerk_org_id = a.clerk_org_id
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.lead_id IS NOT NULL
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
), latest_appointment_per_lead AS (
  SELECT DISTINCT ON (lead_id)
    appointment_id,
    lead_id,
    schedule_time,
    host_id,
    setter_id,
    snapshot_event_name,
    snapshot_call_category,
    appointment_source,
    no_show,
    outcome_name,
    outcome_role
  FROM appointment_base
  ORDER BY lead_id, schedule_time DESC, appointment_id DESC
)
SELECT
  COUNT(*)::int AS calls_taken
FROM latest_appointment_per_lead
WHERE schedule_time < NOW()
  AND outcome_role IN ('WON', 'PARTIAL_PAYMENT', 'FOLLOW_UP', 'LOST', 'UNQUALIFIED');
```

This is the default SQL pattern for user questions like:

```text
How many calls were taken?
How many calls were taken on that day?
How many completed calls happened?
How many attended calls did we have?
How many held calls did we have?
```

---

## Required SQL pattern for calls taken by day / specific day

When the user asks “calls taken on 15 May 2026” or “calls taken on that day”, do not hardcode dates inside the skill. Generate the same parameterized SQL and rely on the application to pass:

```text
:start_date = selected day 00:00:00
:end_date = next day 00:00:00
```

Use the same `appointment_base` and `latest_appointment_per_lead` CTE logic above.

Important: deduplicate after filtering to the selected input period. Do not select the latest appointment across all time and then filter to the requested day.

---

## Optional grouped SQL pattern: calls taken by event type

If the user asks for calls taken by event type, use the same latest-per-lead and completed/taken outcome logic:

```sql
WITH appointment_base AS (
  SELECT
    a.id AS appointment_id,
    a.lead_id,
    a.schedule_time,
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    outcome.name AS outcome_name,
    CAST(outcome.role AS text) AS outcome_role
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  LEFT JOIN sales_statuses outcome
    ON outcome.id = a.outcome_id
   AND outcome.clerk_org_id = a.clerk_org_id
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.lead_id IS NOT NULL
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
), latest_appointment_per_lead AS (
  SELECT DISTINCT ON (lead_id)
    appointment_id,
    lead_id,
    schedule_time,
    event_name,
    outcome_name,
    outcome_role
  FROM appointment_base
  ORDER BY lead_id, schedule_time DESC, appointment_id DESC
), calls_taken AS (
  SELECT *
  FROM latest_appointment_per_lead
  WHERE schedule_time < NOW()
    AND outcome_role IN ('WON', 'PARTIAL_PAYMENT', 'FOLLOW_UP', 'LOST', 'UNQUALIFIED')
)
SELECT
  event_name,
  COUNT(*)::int AS calls_taken,
  SUM(COUNT(*)) OVER ()::int AS total_calls_taken,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0),
    2
  ) AS percentage_of_total
FROM calls_taken
GROUP BY event_name
ORDER BY calls_taken DESC, event_name ASC;
```

Apply the same pattern for breakdowns by `host_id`, `setter_id`, `snapshot_call_category`, or `appointment_source`.

---

## Related metric guidance to add briefly

Add a short “Dashboard-aligned appointment metrics” note in `appointment_analytics.md`:

```text
For dashboard-style KPI questions, appointment metrics should align with `dashboard_metrics_reference.md`.

- `calls_booked`: unique leads with at least one appointment in the selected period, using the latest appointment per lead.
- `calls_scheduled`: unique leads whose latest appointment in the selected period is not `CANCELED` or `RESCHEDULED`.
- `calls_taken`: unique leads whose latest past appointment in the selected period has outcome role `WON`, `PARTIAL_PAYMENT`, `FOLLOW_UP`, `LOST`, or `UNQUALIFIED`.
- `no_show`: unique leads whose latest past appointment in the selected period has outcome role `NO_SHOW` or `appointments.no_show = true`.
- `cancelled`: unique leads whose latest appointment in the selected period has outcome role `CANCELED`.
- `rescheduled`: unique leads whose latest past appointment in the selected period has outcome role `RESCHEDULED`.

For non-dashboard wording such as raw appointment row counts, keep existing appointment row-count logic. But for user-facing business KPI wording like booked calls, scheduled calls, calls taken, show rate, no-show, cancelled, and rescheduled, use the dashboard-aligned latest-appointment-per-lead logic.
```

---

## Show rate dependency

If `appointment_analytics.md` has show-rate SQL patterns, update them to reuse dashboard-aligned components:

```text
show_rate_percent = calls_taken / past scheduled calls * 100
adjusted_show_rate_percent = calls_taken / calls_booked * 100
```

Where:

```text
calls_taken = dashboard-aligned taken-call count
past scheduled calls = latest appointments per lead that are not CANCELED or RESCHEDULED and have schedule_time < NOW()
calls_booked = latest appointments per lead in the selected period, regardless of outcome
```

Do not use all appointment rows as the denominator for dashboard-style show rate.

---

## Acceptance criteria

After the patch:

1. A question like “How many calls were taken on that day?” must not count canceled appointments.
2. It must not count rescheduled appointments.
3. It must not count no-show appointments.
4. It must not use only `a.no_show = false` to define completed/taken calls.
5. It must count unique leads, not raw appointment rows, for dashboard-style `calls_taken`.
6. It must use the latest appointment per lead inside the selected period.
7. It must keep organization filtering with `:org_id`.
8. It must keep date filters parameterized with `:start_date` and `:end_date`.
9. It must not hardcode organization IDs or dates.
10. It must not change router or generic SQL agent prompts for this fix.

Strictly follow the dashboard metric reference for dashboard-style appointment KPI wording.
