# Skill: `appointment_analytics`

## Short Description

Use this skill for read-only SQL questions about appointments, booked calls, call outcomes, no-shows, event types, hosts, setters, call categories, and Fathom call records connected to appointments.

This skill must generate SQL only. The application will execute the SQL through a safe read-only database helper.

## When To Use This Skill

Use `appointment_analytics` when the user asks questions like:

- How many appointments do we have?
- How many calls were booked today, this week, this month, or during a date range?
- How many upcoming appointments are scheduled?
- How many completed or past appointments do we have?
- What is the appointment no-show rate?
- Which event type has the highest no-show rate?
- Which host has the most appointments?
- Which setter booked the most appointments?
- What is the appointment breakdown by outcome?
- What is the appointment breakdown by call category?
- What is the appointment breakdown by source, such as Calendly or manual?
- Which appointments were no-shows?
- Which appointments have no Fathom call record?
- Which appointments have Fathom summaries?
- What are common objections captured in Fathom call records?
- Which calls had action items?
- What is the average call duration?
- How many calls have AI-suggested outcomes?

## When Not To Use This Skill

Do not use this skill for:

- Lead-only counts, lead source breakdowns, stale leads, missing owners, missing setters, or lead creation trends. Use `lead_analytics`.
- Revenue, contracts, payments, invoices, refunds, subscriptions, or payment links. Use `revenue_analytics`.
- Form-answer, UTM, landing-page, traffic attribution, or opt-in question analysis. Use `acquisition_analytics`.
- Full single-lead summaries with notes, calls, contracts, payments, and complete timeline. Use `lead_360`.
- Provider integration health, webhook troubleshooting, credential validation, API keys, webhook payloads, or connection status. Use an integration/admin skill.
- Deep semantic search over long call text, notes, or objections. Use a future semantic retrieval or pgvector skill when the user asks for qualitative theme discovery across many records.

If the user question requires tables outside `appointments`, `appointment_event_types`, `sales_statuses`, `leads`, or `fathom_call_records`, do not use this skill unless the required logic is explicitly listed in this file.

## SQL Generation Rules

Generate exactly one read-only PostgreSQL SQL statement.

Allowed statements:

- `SELECT`
- `WITH ... SELECT`

Never generate:

- `INSERT`
- `UPDATE`
- `DELETE`
- `UPSERT`
- `MERGE`
- `DROP`
- `ALTER`
- `CREATE`
- `TRUNCATE`
- `GRANT`
- `REVOKE`
- `COPY`
- `CALL`
- `DO`
- `VACUUM`
- `ANALYZE`
- `EXPLAIN ANALYZE`

Do not generate multiple SQL statements.

Do not use `SELECT *`.

Do not expose secrets, webhook payloads, API keys, encrypted credentials, raw payloads, provider credentials, or private integration data.

Never select `fathom_call_records.raw_payload`.

Every business query must include an organization filter. For appointment-first queries, use:

```sql
WHERE a.clerk_org_id = :org_id
```

For `appointments`, always exclude soft-deleted rows unless the user explicitly asks about deleted appointments:

```sql
AND a.is_deleted = false
```

For `appointment_event_types`, exclude soft-deleted rows by default:

```sql
AND aet.is_deleted = false
```

For `leads`, exclude soft-deleted rows by default when joining to lead identity:

```sql
AND l.is_deleted = false
```

Always use parameterized SQL for organization scope and dynamic values.

Use named parameters such as:

- `:org_id`
- `:start_date`
- `:end_date`
- `:host_id`
- `:setter_id`
- `:event_type_id`
- `:call_category`
- `:appointment_source`
- `:limit`

Do not hardcode the organization ID in generated agent SQL except in local manual debugging.

For aggregate analytics questions, return aggregate columns only.

For list-style questions such as "which appointments", select only the fields needed to answer the question, add a deterministic `ORDER BY`, and cap the result with a reasonable `LIMIT` unless the user asks for a specific limit.

Default list limit: `50`.

Do not include lead email or phone fields in list outputs unless the user explicitly asks for contact details.

`host_id` and `setter_id` are user IDs. Do not invent host or setter names unless a future user/profile table is available in another skill.

When joining `fathom_call_records`, use `COUNT(DISTINCT a.id)` for appointment counts to avoid double-counting appointments that have multiple call records.

## Primary Tables

## `appointments`

One row is one booked appointment/call connected to a lead.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Appointment primary key. | Join key and appointment identity. |
| `lead_id` | Lead ID connected to the appointment. | Join to `leads.id`. |
| `clerk_org_id` | Tenant/organization ID. | Required filter. |
| `schedule_time` | Scheduled appointment datetime. | Date filtering, upcoming calls, no-show rate period, trends. |
| `host_id` | Host/closer user ID. | Host performance and missing host checks. |
| `setter_id` | Setter user ID. | Setter appointment booking analysis. |
| `meeting_url` | Meeting link. | Display only when explicitly useful. |
| `snapshot_event_name` | Event name saved on appointment. | Historical event type display. |
| `snapshot_call_category` | Call category saved on appointment. | Historical call category reporting. |
| `appointment_event_type_id` | Event type ID. | Join to `appointment_event_types.id`. |
| `outcome_id` | Appointment outcome status ID. | Join to `sales_statuses.id`. |
| `notes` | Appointment notes. | Light appointment context. |
| `recording_url` | Recording URL. | Display only when explicitly asked. |
| `no_show` | Whether the appointment was a no-show. | No-show counts and rates. |
| `source` | Appointment source enum. | Calendly/manual breakdown. |
| `external_reference` | External provider reference. | Provider/debug context only when explicitly requested. |
| `created_by` | User/system that created appointment. | Admin context only when needed. |
| `created_at` | Appointment record creation datetime. | Booking-created trend only when user asks when appointments were created. |
| `updated_at` | Last appointment record update datetime. | Recency/debug context only. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |
| `deleted_at` | Deletion datetime. | Deleted-appointment analysis only. |

Required default filter:

```sql
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
```

## `appointment_event_types`

One row is a Calendly/manual event type catalog entry.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Event type primary key. | Join from `appointments.appointment_event_type_id`. |
| `clerk_org_id` | Tenant/organization ID. | Required join safety. |
| `external_event_type_id` | Provider event type ID. | Provider/debug context only when explicitly requested. |
| `event_type_name` | Current event type name. | Event type breakdown and labels. |
| `call_category` | Current call category. | Event catalog category analysis. |
| `provider` | Provider enum. | Calendly/manual/provider breakdown. |
| `is_favourite` | Favorite flag. | Setup/admin context. |
| `is_ignored` | Ignored event type flag. | Setup/admin context and excluding ignored event types when requested. |
| `owner_name` | Provider owner display name. | Event owner context when available. |
| `owner_ref` | Provider owner reference. | Provider/debug context only. |
| `kind` | Provider kind/type. | Provider context only. |
| `source` | Event type source enum. | Provider/manual event type source. |
| `metadata` | Provider metadata. | Avoid unless explicitly asked; do not expose raw provider internals. |
| `created_by` | User/system that created event type. | Admin context only. |
| `created_at` | Event type creation datetime. | Setup/admin context. |
| `updated_at` | Last update datetime. | Setup/admin context. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Join from appointments:

```sql
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
```

Use `a.snapshot_event_name` for historical appointment reporting because it reflects the event name at appointment time.

Use `aet.event_type_name` when the user asks about the current event type catalog.

Do not join `appointment_event_types` without matching `clerk_org_id`.

## `sales_statuses`

One row is a readable pipeline status or appointment outcome for an organization.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Status primary key. | Join from `appointments.outcome_id`. |
| `clerk_org_id` | Tenant/organization ID. | Required join safety. |
| `name` | Human-readable outcome/status name. | Display exact appointment outcome. |
| `description` | Status description. | Explain outcome if available. |
| `role` | Normalized status role enum. | Group appointment outcomes into business categories. |
| `is_default` | Whether default status. | Setup/admin context. |
| `is_system` | Whether system-created status. | Setup/admin context. |

Join from appointments:

```sql
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
```

Use `a.no_show` for true appointment no-show rate.

Use `outcome.role` or `outcome.name` when the user asks for appointment outcome breakdowns.

Do not join `sales_statuses` without matching `clerk_org_id`.

## `leads`

Use this table only when appointment answers need lead display context.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Lead primary key. | Join from `appointments.lead_id`. |
| `clerk_org_id` | Tenant/organization ID. | Required join safety. |
| `first_name` | First name. | Display and search. |
| `last_name` | Last name. | Display and search. |
| `full_name` | Generated/display full name. | Display and search. |
| `email` | Lead email. | Search and identity only when explicitly requested. |
| `phone_e164` | Phone number in E.164 format. | Contact detail only when explicitly requested. |
| `source` | Lead source enum. | Lead-source context only. |
| `assigned_to` | Owner/assignee user ID. | Lead owner context only. |
| `setter_id` | Lead setter user ID. | Lead setter context only. |
| `status_id` | Current lead status ID. | Lead status context only. |
| `created_at` | Lead creation datetime. | Lead-age context only. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Join from appointments:

```sql
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
```

Do not use this skill for lead-only analytics. Use `lead_analytics` for lead-only questions.

## `fathom_call_records`

One row is a Fathom AI call record, usually connected to an appointment.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Fathom record primary key. | Fathom record identity. |
| `appointment_id` | Appointment ID connected to the Fathom record. | Join to `appointments.id`. |
| `clerk_org_id` | Tenant/organization ID. | Required filter and join safety. |
| `fathom_call_id` | Fathom call ID. | Provider/debug context only. |
| `fathom_meeting_id` | Fathom meeting ID. | Provider/debug context only. |
| `summary` | Fathom call summary. | Call summary and qualitative context. |
| `key_points` | Fathom key points JSON. | Call themes and important details. |
| `action_items` | Fathom action items JSON. | Follow-up/action item analysis. |
| `objections` | Fathom objections JSON. | Objection analysis. |
| `transcript_url` | Transcript URL. | Display only when explicitly asked. |
| `recording_url` | Recording URL. | Display only when explicitly asked. |
| `ai_suggested_outcome` | AI-suggested outcome status ID. | Join to `sales_statuses.id` if needed. |
| `ai_confidence_score` | AI confidence score. | AI outcome confidence analysis. |
| `ai_rationale` | AI rationale text. | AI outcome explanation. |
| `outcome_applied` | Whether AI outcome was applied. | Automation/application analysis. |
| `call_duration_seconds` | Call duration in seconds. | Average duration and duration distribution. |
| `call_started_at` | Actual call start datetime. | Actual call timing when available. |
| `call_ended_at` | Actual call end datetime. | Actual call timing when available. |
| `created_at` | Fathom record creation datetime. | Fathom ingestion timing. |
| `updated_at` | Last update datetime. | Debug context only. |
| `match_strategy` | How Fathom matched to appointment. | Matching quality/debug context. |
| `outcome_applied_by` | User/system applying outcome. | Admin context only. |
| `ai_generated_title` | AI-generated call title. | Display/context. |

Never select:

```text
raw_payload
```

Join from appointments:

```sql
LEFT JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
```

Join AI-suggested outcome:

```sql
LEFT JOIN sales_statuses ai_outcome
  ON ai_outcome.id = f.ai_suggested_outcome
 AND ai_outcome.clerk_org_id = f.clerk_org_id
```

Fathom records can be missing for appointments.

Fathom records can have `appointment_id` as `NULL`; for appointment analytics, only count appointment-linked records unless the user explicitly asks for unmatched Fathom records.

## Enums

## `AppointmentSource`

Business-defined values:

```text
CALENDLY
MANUAL
```

Meaning:

| Value | Meaning |
|---|---|
| `CALENDLY` | Appointment came from Calendly/provider booking flow. |
| `MANUAL` | Appointment was manually created. |

Use `a.source` for appointment source reporting.

## `CallCategory`

Business-defined values:

```text
SALES_CALL
COACHING_CALL
TRIAGE_CALL
```

Meaning:

| Value | Meaning |
|---|---|
| `SALES_CALL` | Sales/discovery/closing call. |
| `COACHING_CALL` | Coaching/client call. |
| `TRIAGE_CALL` | Qualification or triage call. |

Use `a.snapshot_call_category` for historical appointment reporting.

Use `aet.call_category` for current event type catalog reporting.

## `AppointmentEventTypeSource`

Business-defined values:

```text
PROVIDER
MANUAL
```

Use `aet.source` when the user asks whether event types came from provider sync or manual setup.

## `ProviderType`

Relevant values for appointment analytics:

```text
CALENDLY
FATHOM
```

Other provider enum values may exist, but appointment event type reporting usually uses `CALENDLY`.

## `SalesStatusRole`

Business-defined values:

```text
NEW_LEAD
APPOINTMENT_BOOKED
NO_SHOW
RESCHEDULED
CANCELED
PARTIAL_PAYMENT
WON
UNQUALIFIED
FOLLOW_UP
LOST
```

Use `outcome.role` for normalized appointment outcome analysis.

## Business Interpretation Rules

## Appointment Counts

When the user asks how many appointments, count rows in `appointments`:

```sql
COUNT(*) AS appointment_count
```

Use `a.schedule_time` for appointment timing questions.

Use `a.created_at` only when the user asks when appointments were created or booked in the system.

## Upcoming Appointments

When the user asks for upcoming appointments, use:

```sql
a.schedule_time >= NOW()
```

Do not require a Fathom call record for upcoming appointments.

## Past or Completed Appointments

When the user asks for past appointments, completed appointments, call history, or previous calls, use:

```sql
a.schedule_time < NOW()
```

If the user specifically asks for attended/completed calls, exclude no-shows:

```sql
a.schedule_time < NOW()
AND a.no_show = false
```

## No-Show Rate

For appointment no-show rate, prefer the explicit appointment field:

```sql
a.no_show = true
```

Default no-show denominator:

- non-deleted appointments
- scoped by `a.clerk_org_id = :org_id`
- filtered by `a.schedule_time` if the user provides a date range

Use this rate formula:

```sql
ROUND(
  100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
  2
) AS no_show_rate_percent
```

If the user asks for no-show lead status, use `lead_analytics`.

If the user asks for appointment no-show rate, use this skill.

## Appointment Outcomes

Use `appointments.outcome_id` joined to `sales_statuses.id`.

Use `outcome.name` for exact outcome labels.

Use `outcome.role` for normalized outcome categories.

For no-show reporting, `a.no_show` is more direct than `outcome.role = 'NO_SHOW'`.

## Event Type Names

Use `a.snapshot_event_name` for historical appointment reports.

Use `aet.event_type_name` for current event type catalog reports.

If a query is grouped by event type for historical performance, prefer:

```sql
COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
```

## Host and Setter

`a.host_id` is the appointment host user ID.

`a.setter_id` is the appointment setter user ID.

Treat both `NULL` and blank strings as missing:

```sql
NULLIF(TRIM(a.host_id), '') IS NULL
```

and:

```sql
NULLIF(TRIM(a.setter_id), '') IS NULL
```

For grouping, use:

```sql
COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id
```

and:

```sql
COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id
```

Do not invent host or setter names from IDs.

## Fathom Coverage

When the user asks whether calls have Fathom records, join `fathom_call_records`.

Use `COUNT(DISTINCT a.id)` for appointment totals.

Use `COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL)` for appointments with Fathom records.

Use `COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NULL)` for appointments missing Fathom records.

## Fathom Text Fields

Use Fathom text fields for direct SQL retrieval and light summaries:

- `f.summary`
- `f.key_points`
- `f.action_items`
- `f.objections`
- `f.ai_rationale`
- `f.ai_generated_title`

Do not use `f.raw_payload`.

For broad qualitative questions like "why are calls not converting" or "what objections are common across all calls", SQL can retrieve candidate rows or JSON fields, but a future semantic retrieval or pgvector skill should handle deeper theme clustering.

## Timeframe Rules

For appointments scheduled during a date range, use:

```sql
a.schedule_time >= :start_date
AND a.schedule_time < :end_date
```

For Fathom calls that actually started during a date range, use:

```sql
f.call_started_at >= :start_date
AND f.call_started_at < :end_date
```

If the user says "calls booked this month", prefer `a.schedule_time` unless they clearly mean records created in the system.

If the user says "appointments created this month" or "calls booked into the system this month", use `a.created_at`.

## Default List Output Rules

For list-style appointment queries, default output fields are:

- `a.id`
- `a.schedule_time`
- `display_name`
- `event_name`
- `call_category`
- `outcome_name`
- `outcome_role`
- `a.no_show`
- `a.source`
- `a.host_id`
- `a.setter_id`
- `has_fathom_record`

Use this display name expression:

```sql
COALESCE(
  NULLIF(TRIM(l.full_name), ''),
  NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
  l.first_name,
  'Unknown Lead'
) AS display_name
```

Use this event name expression:

```sql
COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name
```

Do not include `l.email`, `l.phone_e164`, `a.meeting_url`, `a.recording_url`, `f.transcript_url`, or `f.recording_url` unless the user explicitly asks for contact details, meeting links, transcript links, or recording links.

Use `LIMIT :limit` when the application passes a limit.

If the application does not pass a limit and the user does not request one, use:

```sql
LIMIT 50
```

Always use deterministic ordering, such as:

```sql
ORDER BY a.schedule_time DESC, a.id ASC
```

or, for upcoming appointments:

```sql
ORDER BY a.schedule_time ASC, a.id ASC
```

## Common Query Patterns

## Count Appointments

```sql
SELECT COUNT(*) AS appointment_count
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false;
```

## Count Appointments Scheduled in a Date Range

```sql
SELECT COUNT(*) AS appointments_scheduled_in_period
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date;
```

## Count Upcoming Appointments

```sql
SELECT COUNT(*) AS upcoming_appointments
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= NOW();
```

## Appointment No-Show Rate

```sql
SELECT
  COUNT(*) AS total_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false;
```

## Appointment No-Show Rate in a Date Range

```sql
SELECT
  COUNT(*) AS total_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date;
```

## Appointments by Outcome Name

```sql
SELECT
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  COUNT(*) AS appointment_count
FROM appointments a
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY
  COALESCE(outcome.name, 'No Outcome'),
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME')
ORDER BY appointment_count DESC, outcome_name ASC;
```

## Appointments by Call Category

```sql
SELECT
  CAST(a.snapshot_call_category AS text) AS call_category,
  COUNT(*) AS appointment_count
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY CAST(a.snapshot_call_category AS text)
ORDER BY appointment_count DESC, call_category ASC;
```

## Appointments by Source

```sql
SELECT
  CAST(a.source AS text) AS appointment_source,
  COUNT(*) AS appointment_count
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY CAST(a.source AS text)
ORDER BY appointment_count DESC, appointment_source ASC;
```

## Appointments by Event Type

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) AS appointment_count
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY appointment_count DESC, event_name ASC;
```

## No-Show Rate by Event Type

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) AS total_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY no_show_rate_percent DESC NULLS LAST, total_appointments DESC, event_name ASC;
```

## Appointments by Host

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COUNT(*) AS appointment_count
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host')
ORDER BY appointment_count DESC, host_id ASC;
```

## Appointments by Setter

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS appointment_count
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter')
ORDER BY appointment_count DESC, setter_id ASC;
```

## List Upcoming Appointments

```sql
SELECT
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= NOW()
ORDER BY a.schedule_time ASC, a.id ASC
LIMIT 50;
```

## List No-Show Appointments

```sql
SELECT
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.no_show = true
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 50;
```

## Fathom Coverage for Appointments

```sql
SELECT
  COUNT(DISTINCT a.id) AS total_appointments,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) AS appointments_with_fathom,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NULL) AS appointments_without_fathom,
  ROUND(
    100.0 * COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) / NULLIF(COUNT(DISTINCT a.id), 0),
    2
  ) AS fathom_coverage_percent
FROM appointments a
LEFT JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false;
```

## List Appointments Missing Fathom Records

```sql
SELECT
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
LEFT JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND f.id IS NULL
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 50;
```

## List Fathom Call Summaries

```sql
SELECT
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  f.summary,
  f.key_points,
  f.action_items,
  f.objections,
  f.call_duration_seconds,
  f.call_started_at,
  f.call_ended_at
FROM fathom_call_records f
LEFT JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.appointment_id IS NOT NULL
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 50;
```

## Average Call Duration

```sql
SELECT
  COUNT(*) FILTER (WHERE f.call_duration_seconds IS NOT NULL) AS calls_with_duration,
  ROUND(AVG(f.call_duration_seconds) FILTER (WHERE f.call_duration_seconds IS NOT NULL) / 60.0, 2) AS avg_call_duration_minutes
FROM fathom_call_records f
WHERE f.clerk_org_id = :org_id
  AND f.appointment_id IS NOT NULL;
```

## Average Call Duration by Event Type

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) FILTER (WHERE f.call_duration_seconds IS NOT NULL) AS calls_with_duration,
  ROUND(AVG(f.call_duration_seconds) FILTER (WHERE f.call_duration_seconds IS NOT NULL) / 60.0, 2) AS avg_call_duration_minutes
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
WHERE f.clerk_org_id = :org_id
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY avg_call_duration_minutes DESC NULLS LAST, calls_with_duration DESC, event_name ASC;
```

## AI-Suggested Outcomes from Fathom

```sql
SELECT
  COALESCE(ai_outcome.name, 'No AI Suggested Outcome') AS ai_suggested_outcome_name,
  COALESCE(CAST(ai_outcome.role AS text), 'NO_AI_OUTCOME') AS ai_suggested_outcome_role,
  COUNT(*) AS fathom_record_count,
  ROUND(AVG(f.ai_confidence_score), 2) AS avg_ai_confidence_score,
  COUNT(*) FILTER (WHERE f.outcome_applied = true) AS applied_count
FROM fathom_call_records f
LEFT JOIN sales_statuses ai_outcome
  ON ai_outcome.id = f.ai_suggested_outcome
 AND ai_outcome.clerk_org_id = f.clerk_org_id
WHERE f.clerk_org_id = :org_id
  AND f.appointment_id IS NOT NULL
GROUP BY
  COALESCE(ai_outcome.name, 'No AI Suggested Outcome'),
  COALESCE(CAST(ai_outcome.role AS text), 'NO_AI_OUTCOME')
ORDER BY fathom_record_count DESC, ai_suggested_outcome_name ASC;
```

## Appointment Trend by Day

```sql
SELECT
  DATE_TRUNC('day', a.schedule_time)::date AS appointment_date,
  COUNT(*) AS appointment_count
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY DATE_TRUNC('day', a.schedule_time)::date
ORDER BY appointment_date ASC;
```

## No-Show Trend by Day

```sql
SELECT
  DATE_TRUNC('day', a.schedule_time)::date AS appointment_date,
  COUNT(*) AS total_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY DATE_TRUNC('day', a.schedule_time)::date
ORDER BY appointment_date ASC;
```

## Mistakes To Avoid

- Do not count deleted appointments unless explicitly requested.
- Do not join `appointments` to `sales_statuses`, `appointment_event_types`, `leads`, or `fathom_call_records` without matching `clerk_org_id`.
- Do not use `fathom_call_records.raw_payload`.
- Do not use webhook payloads, provider credentials, API keys, or unrelated integration tables in this skill.
- Do not use `a.created_at` when the user asks when calls happened. Use `a.schedule_time`.
- Do not use `f.call_started_at` for appointment booking counts unless the user asks for actual Fathom call start time.
- Do not treat `outcome.role = 'NO_SHOW'` as the primary appointment no-show metric. Prefer `a.no_show`.
- Do not double-count appointments when joining to Fathom records. Use `COUNT(DISTINCT a.id)` for appointment counts after a Fathom join.
- Do not invent host or setter names from `host_id` or `setter_id`.
- Do not include lead email, lead phone, meeting URL, recording URL, or transcript URL unless explicitly requested.
- Do not use `SELECT *`.
- Do not generate SQL without a tenant filter.
- Do not generate non-read SQL.
- Do not answer revenue, acquisition, integration, or full lead timeline questions from this skill.

## Related Skills

- `lead_analytics`: lead counts, lead statuses, lead sources, owners, setters, stale leads, follow-up.
- `acquisition_analytics`: opt-ins, form answers, UTM, traffic attribution, landing pages.
- `revenue_analytics`: programs, contracts, payments, payment links, proofs, refunds, invoices, subscriptions.
- `lead_360`: single-lead complete view across notes, calls, contracts, payments, and timeline.
- `semantic_context`: pgvector or hybrid semantic search over notes, call summaries, objections, and form answers.
