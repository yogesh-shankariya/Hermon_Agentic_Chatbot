# Codex Task: Build `diagnostic_lead_snapshot` for MVP Diagnostic Analytics

## Goal

Build a deterministic lead-level snapshot table for MVP diagnostic analytics.

This table is a read-optimized diagnostic layer that combines lead, source, acquisition, appointment, contract, payment, refund, funnel, and data-quality signals into one safe row per lead.

The table should help the future diagnostic agent answer broad business questions such as:

- Why are leads increasing but revenue is not?
- Where are we losing people in the funnel?
- Which source looks good but may be misleading?
- Can we trust source performance?
- Which source has high lead volume but weak conversion?
- Which source has booked calls but low paid revenue?
- Which source has signed contracts but low collected cash?
- Which source creates leads but not booked calls?
- Which source creates booked calls but not sales?

This task is only for the deterministic numeric/source/funnel diagnostic layer.

Do not build the final diagnostic agent in this task.
Do not add LLM calls.
Do not add semantic extraction.
Do not extract or store raw text insights.
Do not use raw payloads, webhook payloads, credentials, API keys, or integration-secret tables.

---

## Important MVP Decision

Use one main snapshot table for MVP:

```text
diagnostic_lead_snapshot
```

The future diagnostic agent should read this table through controlled diagnostic tools.

For this task, only create the table and one-time static snapshot build logic.

For MVP, the source data is static.

Do not build a recurring refresh/update pipeline.
Do not build a scheduled refresh.
Do not build a cron job.
Do not build trigger-based refresh.
Do not build incremental upsert logic.
Do not build a user-facing refresh button.
Do not build a chatbot tool that updates this table.

---

## Currency Assumption

For this MVP, assume all monetary reporting is in EUR.

Rules:

- Treat all contract, payment, refund, revenue, outstanding, and overdue amounts as EUR.
- Do not add FX conversion logic.
- Do not create multi-currency aggregation logic.
- Do not add mixed-currency flags for MVP.
- Keep `contract_currency` and `payment_currency` as text fields for transparency, but populate them as `EUR` by default.
- Treat the demo dataset as EUR even if legacy/static source rows still contain default currency labels.
- Do not block the one-time build only because existing static rows contain non-EUR currency labels.

Money unit rule:

```text
contracts.total_value, payments.amount, and refunds.amount are stored in minor units.
All snapshot money columns must be stored as business-facing major-unit EUR values.
Divide source monetary sums by 100.0, matching revenue_analytics.
```

This keeps diagnostic monetary totals consistent with the existing revenue analytics skill.

---

## Required Deliverables

Create:

1. A new database table/model named `diagnostic_lead_snapshot`.
2. A one-time admin backfill script for one selected organization.
3. Deterministic aggregation SQL used by that script.
4. Indexes for diagnostic query performance.
5. Basic validation checks after the one-time build.

Use existing project style and database patterns where possible.

Important:

- This one-time build script is a write operation.
- Do not run it through the existing read-only SQL agent helper.
- Use an admin script with write database access.
- The future diagnostic agent should only read from `diagnostic_lead_snapshot`.
- Do not expose this script as a chatbot tool.
- Do not schedule this script.
- Do not create cron jobs, triggers, incremental refresh, or upsert logic.

---

## Table Grain

One row per:

```text
clerk_org_id + lead_id
```

For MVP, use this one-time build strategy:

```text
Without force:
- fail if diagnostic_lead_snapshot rows already exist for the selected organization
- insert snapshot rows once from deterministic SQL

With explicit force for local/demo reruns only:
- delete existing snapshot rows for the selected organization
- insert rebuilt snapshot rows transactionally
```

This avoids accidental overwrites while still allowing intentional local/demo rebuilds.

Add a unique constraint on:

```text
(clerk_org_id, lead_id)
```

---

## Table Name

```text
diagnostic_lead_snapshot
```

---

## Source Tables Allowed

Use only these source tables:

```text
leads
sales_statuses
marketing_sources
opt_ins
traffic_attributions
opt_in_question_answers
appointments
appointment_event_types
fathom_call_records
contracts
programs
payments
refunds
```

Do not use:

```text
admin tables
credential tables
provider credential tables
webhook tables
raw payload tables
integration-secret tables
notification payload tables
API key tables
lead_notes
payment_links
subscription_checkout_links
payment_proofs
invoices
unmatched_payments
contract_subscriptions
```

These are intentionally out of scope for this MVP snapshot.

---

## Organization Scope

For MVP, build the static snapshot for only one organization at a time.

Every source query must be scoped to:

```sql
clerk_org_id = :org_id
```

For child tables without `clerk_org_id`, always join through the parent table that has organization scope.

Examples:

```text
opt_in_question_answers -> opt_ins
traffic_attributions -> opt_ins
```

Never query `opt_in_question_answers` or `traffic_attributions` without joining to `opt_ins` and filtering `opt_ins.clerk_org_id = :org_id`.

---

## Soft Delete Rules

Exclude soft-deleted rows by default for tables that have `is_deleted`:

```sql
leads.is_deleted = false
appointments.is_deleted = false
contracts.is_deleted = false
payments.is_deleted = false
programs.is_deleted = false
```

Do not add soft-delete filters to tables that do not have `is_deleted`.

Do not add `is_deleted` filters to:

```text
sales_statuses
marketing_sources
opt_ins
traffic_attributions
opt_in_question_answers
fathom_call_records
refunds
```

For `appointment_event_types`, use the table only as optional fallback display context. Put any `is_deleted = false` condition inside the `LEFT JOIN`, not in the `WHERE` clause, so historical appointments are not dropped.

---

## Do Not Select or Store

Never select or store these in `diagnostic_lead_snapshot`:

```text
email
phone_e164
raw_payload
meeting_url
recording_url
transcript_url
payment link URL
checkout URL
external provider IDs
webhook payloads
credentials
API keys
encrypted keys
raw lead notes
raw appointment notes
raw call summaries
raw objections
raw action items
raw form questions
raw form answers
payment failure reason
refund failure reason
contract notes
voided reason
```

This snapshot must stay numeric, source, funnel, status, and data-quality focused.

---

## Required Columns

### Identity

```text
id
clerk_org_id
lead_id
lead_created_at
lead_updated_at
snapshot_built_at
```

### Current Lead State

```text
current_status_id
current_status_name
current_status_role
assigned_to
setter_id
next_touch_point_at
next_touch_point_type
is_overdue_followup
is_missing_next_touchpoint
```

### Lead Source

```text
lead_source_enum
first_source_id
first_source
last_source_id
last_source
source_changed
source_confidence
source_quality_flags
```

### Acquisition / Opt-in / UTM

```text
opt_in_count
first_opt_in_at
latest_opt_in_at
first_opt_in_source
latest_opt_in_source
first_provider_form_name
latest_provider_form_name
first_utm_source
first_utm_medium
first_utm_campaign
first_landing_page
first_referrer
latest_utm_source
latest_utm_medium
latest_utm_campaign
latest_landing_page
latest_referrer
has_traffic_attribution
missing_utm_source
missing_utm_campaign
missing_landing_page
missing_referrer
has_form_answers
opt_in_answer_count
```

### Appointments / Calls

```text
appointment_count
past_appointment_count
upcoming_appointment_count
past_non_no_show_appointment_count
completed_call_count
no_show_count
cancelled_appointment_count
first_appointment_at
latest_appointment_at
latest_completed_call_at
latest_event_type_name
latest_call_category
latest_host_id
latest_appointment_outcome_name
latest_appointment_outcome_role
has_fathom_record
fathom_record_count
completed_calls_missing_fathom_count
completed_call_fathom_coverage_rate
avg_call_duration_seconds
total_call_duration_seconds
```

### Contracts

```text
contract_count
signed_contract_count
sent_contract_count
viewed_contract_count
voided_contract_count
contract_sent_lifecycle_count
latest_contract_status
latest_contract_sent_at
latest_contract_signed_at
latest_contract_voided_at
signed_contract_value
contract_currency
latest_program_name
closer_id
contract_setter_id
```

### Payments / Revenue

```text
payment_count
paid_payment_count
pending_payment_count
failed_payment_count
lost_payment_count
refunded_payment_count
gross_paid_amount
refund_amount
net_collected_amount
outstanding_amount
overdue_amount
latest_payment_status
latest_paid_at
latest_payment_due_date
payment_currency
```

### Funnel

```text
funnel_stage
conversion_outcome
lead_to_booked_days
booked_to_completed_days
completed_to_signed_days
signed_to_paid_days
```

### Data Quality

```text
has_missing_first_source
has_missing_last_source
has_orphaned_first_source_id
has_orphaned_last_source_id
has_unknown_source
has_multiple_opt_ins
has_multiple_sources
has_revenue_without_source
has_payment_without_contract
has_contract_without_payment
data_quality_flags
```

---

## Suggested Data Types

Use these as guidance.

```text
id                               uuid primary key default gen_random_uuid()
clerk_org_id                     text not null
lead_id                          uuid not null

lead_created_at                  timestamptz
lead_updated_at                  timestamptz
snapshot_built_at                timestamptz not null default now()

current_status_id                uuid null
current_status_name              text null
current_status_role              text null
assigned_to                      text null
setter_id                        text null
next_touch_point_at              timestamptz null
next_touch_point_type            text null

lead_source_enum                 text null
first_source_id                  uuid null
first_source                     text null
last_source_id                   uuid null
last_source                      text null
source_changed                   boolean not null default false
source_confidence                text not null default 'low'
source_quality_flags             jsonb not null default '[]'::jsonb

counts                           integer not null default 0
booleans                         boolean not null default false
amounts                          numeric(12,2) not null default 0
duration seconds                 numeric null
day gaps                         integer null
rates                            numeric(5,2) null
currency fields                  text not null default 'EUR'

data_quality_flags               jsonb not null default '[]'::jsonb
```

Required constraint:

```text
unique (clerk_org_id, lead_id)
```

Required check constraints:

```text
source_confidence IN ('high', 'medium', 'low')
funnel_stage IN (
  'lead_only',
  'booked_not_completed',
  'completed_not_signed',
  'signed_not_paid',
  'paid',
  'refunded',
  'lost',
  'unqualified'
)
conversion_outcome IN (
  'converted_paid',
  'signed_pending_payment',
  'attended_not_signed',
  'booked_not_attended',
  'lead_not_booked',
  'lost',
  'unqualified',
  'refunded',
  'unknown'
)
contract_currency = 'EUR'
payment_currency = 'EUR'
```

---

## Required Indexes

Create indexes:

```text
(clerk_org_id)
(clerk_org_id, lead_id)
(clerk_org_id, lead_created_at)
(clerk_org_id, current_status_role)
(clerk_org_id, funnel_stage)
(clerk_org_id, conversion_outcome)
(clerk_org_id, first_source)
(clerk_org_id, last_source)
(clerk_org_id, source_confidence)
(clerk_org_id, net_collected_amount)
(clerk_org_id, signed_contract_value)
(clerk_org_id, snapshot_built_at)
```

For Postgres, use clear names such as:

```text
idx_dls_org
idx_dls_org_lead
idx_dls_org_lead_created_at
idx_dls_org_status_role
idx_dls_org_funnel_stage
idx_dls_org_conversion_outcome
idx_dls_org_first_source
idx_dls_org_last_source
idx_dls_org_source_confidence
idx_dls_org_net_collected_amount
idx_dls_org_signed_contract_value
idx_dls_org_built_at
```

---

## Extraction Logic

## 1. Base Lead Data

Base table must be `leads`.

Filter:

```sql
l.clerk_org_id = :org_id
AND l.is_deleted = false
```

Join current lead status:

```sql
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
```

Populate:

```text
lead_id = l.id
clerk_org_id = l.clerk_org_id
lead_created_at = l.created_at
lead_updated_at = l.updated_at
current_status_id = l.status_id
current_status_name = ss.name
current_status_role = ss.role::text
assigned_to = l.assigned_to
setter_id = l.setter_id
next_touch_point_at = l.next_touch_point_at
next_touch_point_type = l.next_touch_point_type::text
lead_source_enum = l.source::text
```

Follow-up flags:

```text
is_missing_next_touchpoint = true only when:
- l.next_touch_point_at is null
- current_status_role is not WON, LOST, UNQUALIFIED, CANCELED

is_overdue_followup = true only when:
- l.next_touch_point_at is not null
- l.next_touch_point_at < now()
- current_status_role is not WON, LOST, UNQUALIFIED, CANCELED
```

Use this role expression for null-safe logic:

```sql
COALESCE(CAST(ss.role AS text), 'NO_STATUS')
```

---

## 2. Lead Source Logic

Join marketing sources twice:

```sql
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id

LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
```

Populate:

```text
first_source_id = l.first_source_id
first_source = COALESCE(first_ms.name, NULLIF(BTRIM(l.first_source_name), ''), 'Unknown')

last_source_id = l.last_source_id
last_source = COALESCE(last_ms.name, NULLIF(BTRIM(l.last_source_name), ''), 'Unknown')
```

Source flags:

```text
source_changed = first_source IS DISTINCT FROM last_source

has_missing_first_source =
  l.first_source_id is null
  and NULLIF(BTRIM(l.first_source_name), '') is null

has_missing_last_source =
  l.last_source_id is null
  and NULLIF(BTRIM(l.last_source_name), '') is null

has_orphaned_first_source_id =
  l.first_source_id is not null
  and first_ms.id is null

has_orphaned_last_source_id =
  l.last_source_id is not null
  and last_ms.id is null

has_unknown_source =
  first_source = 'Unknown'
  or last_source = 'Unknown'
```

Source confidence must use deterministic precedence.

Use this order:

```text
low:
- both first_source and last_source are Unknown
- or has_orphaned_first_source_id = true
- or has_orphaned_last_source_id = true

medium:
- first_source is Unknown
- or last_source is Unknown
- or first_source IS DISTINCT FROM last_source

high:
- first_source is not Unknown
- last_source is not Unknown
- no orphaned first/last source IDs
- first_source is not different from last_source
```

Implement as a `CASE` statement in the order `low`, then `medium`, then `high`.

`source_quality_flags` should be a JSON array.

Allowed values:

```text
missing_first_source
missing_last_source
orphaned_first_source_id
orphaned_last_source_id
unknown_source
source_changed
multiple_sources
```

---

## 3. Opt-in / Acquisition Logic

Aggregate `opt_ins` by `lead_id`.

Filter:

```sql
o.clerk_org_id = :org_id
```

Do not add an `is_deleted` filter to `opt_ins` because the current table does not have `is_deleted`.

Populate:

```text
opt_in_count = count(distinct o.id)
first_opt_in_at = min(o.created_at)
latest_opt_in_at = max(o.created_at)
first_opt_in_source = o.source::text from earliest opt-in
latest_opt_in_source = o.source::text from latest opt-in
first_provider_form_name = provider_form_name from earliest opt-in
latest_provider_form_name = provider_form_name from latest opt-in
has_multiple_opt_ins = opt_in_count > 1
```

For first/latest opt-in, use window functions:

```sql
ROW_NUMBER() OVER (PARTITION BY o.lead_id ORDER BY o.created_at ASC, o.id ASC) = 1
ROW_NUMBER() OVER (PARTITION BY o.lead_id ORDER BY o.created_at DESC, o.id DESC) = 1
```

Do not select or store:

```text
o.raw_payload
o.external_reference
o.provider_form_id
o.ip_address
o.user_agent
```

---

## 4. Traffic Attribution Logic

Join traffic attribution through opt-ins:

```sql
LEFT JOIN traffic_attributions ta
  ON ta.opt_in_id = o.id
```

Do not query `traffic_attributions` without joining to `opt_ins`.

Use `opt_ins.clerk_org_id = :org_id` for organization scope.

Populate first attribution fields from the earliest attribution available for the lead:

```text
first_utm_source
first_utm_medium
first_utm_campaign
first_landing_page
first_referrer
```

Populate latest attribution fields from the latest attribution available for the lead:

```text
latest_utm_source
latest_utm_medium
latest_utm_campaign
latest_landing_page
latest_referrer
```

Recommended ordering:

```text
First attribution: order by o.created_at asc, ta.created_at asc, o.id asc
Latest attribution: order by o.created_at desc, ta.created_at desc, o.id desc
```

Coverage flags:

```text
has_traffic_attribution = at least one traffic_attributions row exists for the lead

missing_utm_source = opt_in_count > 0 and no non-blank utm_source across lead opt-ins
missing_utm_campaign = opt_in_count > 0 and no non-blank utm_campaign across lead opt-ins
missing_landing_page = opt_in_count > 0 and no non-blank landing_page across lead opt-ins
missing_referrer = opt_in_count > 0 and no non-blank referrer across lead opt-ins
```

Do not use UTM fields for revenue attribution in this table.

Only store UTM, landing page, and referrer as diagnostic context.

For leads with no opt-ins, leave these missing UTM/landing/referrer flags false.
Those leads may have no acquisition context, but should not automatically be marked as bad UTM data.

Revenue by UTM campaign, landing page, referrer, provider form, form answer, or opt-in source remains unsupported unless a future approved attribution model is created.

---

## 5. Opt-in Question Answer Coverage

Use `opt_in_question_answers` only for coverage counts.

Join through `opt_ins`:

```sql
JOIN opt_ins o
  ON o.id = q.opt_in_id
WHERE o.clerk_org_id = :org_id
```

Populate:

```text
has_form_answers = count(q.id) > 0
opt_in_answer_count = count(q.id)
```

Do not store raw questions or raw answers in `diagnostic_lead_snapshot`.

Raw question/answer text belongs to a future text-insight layer, not this snapshot.

---

## 6. Appointment Logic

Aggregate `appointments` by lead.

Filter:

```sql
a.clerk_org_id = :org_id
AND a.is_deleted = false
```

Join appointment outcome:

```sql
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
```

Optional event type fallback:

```sql
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
```

Use `appointments.snapshot_event_name` and `appointments.snapshot_call_category` as the primary historical appointment labels.

Populate:

```text
appointment_count = count(distinct a.id)
past_appointment_count = count where a.schedule_time < now()
upcoming_appointment_count = count where a.schedule_time >= now()
past_non_no_show_appointment_count = count where a.schedule_time < now() and a.no_show = false
no_show_count = count where a.no_show = true
cancelled_appointment_count = count where outcome.role::text = 'CANCELED'
first_appointment_at = min(a.schedule_time)
latest_appointment_at = max(a.schedule_time)
latest_host_id = a.host_id from latest appointment
latest_event_type_name = COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') from latest appointment
latest_call_category = a.snapshot_call_category::text from latest appointment
latest_appointment_outcome_name = outcome.name from latest appointment
latest_appointment_outcome_role = outcome.role::text from latest appointment
```

Latest appointment ordering:

```sql
ORDER BY a.schedule_time DESC, a.created_at DESC, a.id DESC
```

Completed call logic for MVP:

Store two appointment completion signals to avoid confusion with existing appointment analytics.

Compatibility metric:

```text
past_non_no_show_appointment_count =
count of appointments where:
- a.schedule_time < now()
- a.no_show = false
```

This matches the current simple appointment analytics completed/attended logic.

Diagnostic funnel metric:

```text
completed_call_count = count of appointments where:
- a.schedule_time < now()
- a.no_show = false
- appointment outcome role is not CANCELED
- appointment outcome role is not RESCHEDULED
```

Recommended SQL condition:

```sql
a.schedule_time < NOW()
AND a.no_show = false
AND COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED')
```

Use `completed_call_count` for diagnostic funnel analysis.
Use `past_non_no_show_appointment_count` only for compatibility checks against existing appointment analytics.

If these counts differ, the difference likely represents past appointments that were not no-shows but were canceled or rescheduled.

Populate:

```text
latest_completed_call_at = max(a.schedule_time) using the stricter completed_call_count condition
```

---

## 7. Fathom Coverage Logic

Join Fathom call records only for counts and duration.

Do not store raw Fathom text or links.

Never select or store:

```text
f.summary
f.key_points
f.action_items
f.objections
f.transcript_url
f.recording_url
f.ai_rationale
f.raw_payload
f.fathom_call_id
f.fathom_meeting_id
```

Use appointment-linked Fathom records and valid non-deleted appointments.

Recommended join:

```sql
LEFT JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
```

Populate:

```text
has_fathom_record = count(distinct f.id) > 0
fathom_record_count = count(distinct f.id)
completed_calls_missing_fathom_count = count of completed_call_count appointments with no linked Fathom record
completed_call_fathom_coverage_rate = percentage of completed_call_count appointments that have at least one linked Fathom record
avg_call_duration_seconds = avg(f.call_duration_seconds) where f.call_duration_seconds is not null
total_call_duration_seconds = sum(f.call_duration_seconds) where f.call_duration_seconds is not null
```

Use the stricter `completed_call_count` condition as the Fathom coverage denominator.

Recommended missing-count logic:

```sql
COUNT(DISTINCT a.id) FILTER (
  WHERE a.schedule_time < NOW()
    AND a.no_show = false
    AND COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') NOT IN ('CANCELED', 'RESCHEDULED')
    AND f.id IS NULL
) AS completed_calls_missing_fathom_count
```

Recommended coverage-rate logic:

```sql
CASE
  WHEN completed_call_count > 0
  THEN ROUND(
    100.0 * (completed_call_count - completed_calls_missing_fathom_count)
      / completed_call_count,
    2
  )
  ELSE NULL
END AS completed_call_fathom_coverage_rate
```

Compute this rate in an outer CTE or final projection after `completed_call_count` and `completed_calls_missing_fathom_count` are available.

Missing Fathom flag rule:

```text
no_fathom_record = completed_calls_missing_fathom_count > 0
```

Do not flag upcoming-only appointments as missing Fathom records.
Do not use raw `appointment_count` for missing Fathom data quality flags.

The current duration column is:

```text
fathom_call_records.call_duration_seconds
```

---

## 8. Contract Logic

Aggregate `contracts` by lead.

Filter:

```sql
c.clerk_org_id = :org_id
AND c.is_deleted = false
```

Populate:

```text
contract_count = count(distinct c.id)
signed_contract_count = count where current c.status = 'SIGNED'
sent_contract_count = count where current c.status = 'SENT'
viewed_contract_count = count where current c.status = 'VIEWED'
voided_contract_count = count where c.status = 'VOIDED'
contract_sent_lifecycle_count = count where c.sent_at is not null
signed_contract_value = sum(c.total_value) / 100.0 where c.status = 'SIGNED'
contract_currency = 'EUR'
```

Use `COALESCE(c.total_value, 0)` inside sums, then divide the aggregate result by `100.0`.

Do not add `contract_viewed_lifecycle_count` for MVP because the current `contracts` schema does not have a `viewed_at` column.

Current-status contract counts and lifecycle counts are intentionally different:

```text
sent_contract_count = contracts currently in SENT status
contract_sent_lifecycle_count = contracts that have ever been sent, based on sent_at
```

Latest contract ordering:

```sql
ORDER BY
  GREATEST(
    COALESCE(c.signed_at, '-infinity'::timestamptz),
    COALESCE(c.voided_at, '-infinity'::timestamptz),
    COALESCE(c.sent_at, '-infinity'::timestamptz),
    c.created_at
  ) DESC,
  c.created_at DESC,
  c.id DESC
```

Populate from the latest contract:

```text
latest_contract_status = c.status::text
latest_contract_sent_at = c.sent_at
latest_contract_signed_at = c.signed_at
latest_contract_voided_at = c.voided_at
closer_id = c.closer_id
contract_setter_id = c.setter_id
```

Join program for latest contract display context:

```sql
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
```

Populate:

```text
latest_program_name = pr.name from latest contract
```

Contract quality flag:

```text
has_contract_without_payment = contract_count > 0 and payment_count = 0
```

Do not store:

```text
c.notes
c.esign_template_id
c.esign_contract_id
c.voided_reason
```

---

## 9. Payment Logic

Aggregate `payments` by lead.

Primary join:

```text
payments.lead_id = leads.id
```

The current schema has `payments.lead_id` as required, so use it as the primary resolved lead.

If defensive fallback is needed, you may join `contracts` and use:

```text
resolved_lead_id = COALESCE(p.lead_id, c.lead_id)
```

Avoid double counting. Use one payment CTE with one row per payment ID.

Filter:

```sql
p.clerk_org_id = :org_id
AND p.is_deleted = false
```

Populate:

```text
payment_count = count(distinct p.id)
paid_payment_count = count where p.status = 'PAID'
pending_payment_count = count where p.status = 'PENDING'
failed_payment_count = count where p.status = 'FAILED'
lost_payment_count = count where p.status = 'LOST'
refunded_payment_count = count where p.status = 'REFUNDED'
gross_paid_amount = sum(p.amount) / 100.0 where p.status = 'PAID'
outstanding_amount = sum(p.amount) / 100.0 where p.status in ('PENDING', 'FAILED')
overdue_amount = sum(p.amount) / 100.0 where p.status in ('PENDING', 'FAILED') and p.due_date < now()
latest_payment_status = p.status::text from latest payment
latest_paid_at = max(p.paid_at)
latest_payment_due_date = p.due_date from latest payment
payment_currency = 'EUR'
```

Use `COALESCE(p.amount, 0)` inside sums, then divide the aggregate result by `100.0`.

Important correction:

```text
Do not include LOST payments in outstanding_amount or overdue_amount.
```

Reason:

```text
LOST is a separate diagnostic signal, not collectable outstanding revenue.
```

Latest payment ordering:

```sql
ORDER BY
  GREATEST(
    COALESCE(p.paid_at, '-infinity'::timestamptz),
    COALESCE(p.due_date, '-infinity'::timestamptz),
    p.created_at
  ) DESC,
  p.created_at DESC,
  p.id DESC
```

Payment quality flag:

```text
has_payment_without_contract = payment_count > 0 and contract_count = 0
```

Do not store:

```text
p.note
p.failure_reason
p.external_payment_id
```

---

## 10. Refund Logic

Aggregate `refunds` by payment and lead.

Use only succeeded refunds for money calculations:

```text
refund_amount = sum(r.amount) / 100.0 where r.status = 'SUCCEEDED'
```

Join refunds through non-deleted payments:

```sql
JOIN payments p
  ON p.id = r.payment_id
 AND p.clerk_org_id = r.clerk_org_id
 AND p.is_deleted = false
WHERE r.clerk_org_id = :org_id
```

Resolve lead through the payment:

```text
resolved_lead_id = p.lead_id
```

Do not add an `is_deleted` filter to `refunds` because the current refunds table does not have `is_deleted`.

Calculate:

```text
net_collected_amount = gross_paid_amount - refund_amount
```

Both `gross_paid_amount` and `refund_amount` must already be major-unit EUR values before this subtraction.

Revenue/source quality flag:

```text
has_revenue_without_source = net_collected_amount > 0 and has_unknown_source = true
```

Do not store:

```text
r.reason
r.external_refund_id
r.failure_reason
```

---

## 11. Funnel Stage Logic

Calculate `funnel_stage` using the farthest meaningful stage reached.

Use this precedence:

```text
If net_collected_amount > 0:
  paid

Else if refund_amount > 0 and net_collected_amount <= 0:
  refunded

Else if current_status_role = 'LOST':
  lost

Else if current_status_role = 'UNQUALIFIED':
  unqualified

Else if signed_contract_count > 0:
  signed_not_paid

Else if completed_call_count > 0:
  completed_not_signed

Else if appointment_count > 0:
  booked_not_completed

Else:
  lead_only
```

Allowed `funnel_stage` values:

```text
lead_only
booked_not_completed
completed_not_signed
signed_not_paid
paid
refunded
lost
unqualified
```

Notes:

- Paid revenue should not be hidden just because current lead status is later changed to LOST.
- LOST and UNQUALIFIED should override only when no positive net collected revenue exists.

---

## 12. Conversion Outcome Logic

Calculate `conversion_outcome` from `funnel_stage`.

Allowed values:

```text
converted_paid
signed_pending_payment
attended_not_signed
booked_not_attended
lead_not_booked
lost
unqualified
refunded
unknown
```

Rules:

```text
If funnel_stage = paid:
  converted_paid

If funnel_stage = signed_not_paid:
  signed_pending_payment

If funnel_stage = completed_not_signed:
  attended_not_signed

If funnel_stage = booked_not_completed:
  booked_not_attended

If funnel_stage = lead_only:
  lead_not_booked

If funnel_stage = lost:
  lost

If funnel_stage = unqualified:
  unqualified

If funnel_stage = refunded:
  refunded
```

Use `unknown` only as a defensive fallback if none of the above rules can be applied.

---

## 13. Stage Delay Logic

Calculate integer day gaps.

```text
lead_to_booked_days = date difference between first_appointment_at and lead_created_at
booked_to_completed_days = date difference between latest_completed_call_at and first_appointment_at
completed_to_signed_days = date difference between latest_contract_signed_at and latest_completed_call_at
signed_to_paid_days = date difference between latest_paid_at and latest_contract_signed_at
```

Return null if either side is missing.

Return null if the calculated value is negative.

Use integer days.

Recommended Postgres expression style:

```sql
CASE
  WHEN later_ts IS NOT NULL AND earlier_ts IS NOT NULL AND later_ts >= earlier_ts
  THEN FLOOR(EXTRACT(EPOCH FROM (later_ts - earlier_ts)) / 86400)::int
  ELSE NULL
END
```

---

## 14. Multiple Source Logic

Calculate:

```text
has_multiple_sources =
  first_source IS DISTINCT FROM last_source
  OR first_utm_source IS DISTINCT FROM latest_utm_source
  OR first_utm_campaign IS DISTINCT FROM latest_utm_campaign
```

Use null-safe comparison.

For source-related flags, use `IS DISTINCT FROM`, not `<>`, because null handling matters.

---

## 15. Data Quality Flags

Store `data_quality_flags` as a JSON array.

Allowed values:

```text
missing_first_source
missing_last_source
orphaned_first_source_id
orphaned_last_source_id
unknown_source
source_changed
multiple_opt_ins
multiple_sources
revenue_without_source
payment_without_contract
contract_without_payment
missing_utm_source
missing_utm_campaign
missing_landing_page
missing_referrer
no_fathom_record
```

Set corresponding boolean columns where available.

Rules:

```text
has_missing_first_source -> add missing_first_source
has_missing_last_source -> add missing_last_source
has_orphaned_first_source_id -> add orphaned_first_source_id
has_orphaned_last_source_id -> add orphaned_last_source_id
has_unknown_source -> add unknown_source
source_changed -> add source_changed
has_multiple_opt_ins -> add multiple_opt_ins
has_multiple_sources -> add multiple_sources
has_revenue_without_source -> add revenue_without_source
has_payment_without_contract -> add payment_without_contract
has_contract_without_payment -> add contract_without_payment
missing_utm_source -> add missing_utm_source only when opt_in_count > 0
missing_utm_campaign -> add missing_utm_campaign only when opt_in_count > 0
missing_landing_page -> add missing_landing_page only when opt_in_count > 0
missing_referrer -> add missing_referrer only when opt_in_count > 0
completed_calls_missing_fathom_count > 0 -> add no_fathom_record
```

Build JSON flag arrays with null-safe logic, or build arrays in application code after SQL aggregation.
Do not rely on a JSON object null-strip helper if it would leave null elements inside an array.

The final stored value must be a JSON array, not a comma-separated string.
Do not leave null values inside `source_quality_flags` or `data_quality_flags`.

Allowed:

```json
["missing_first_source"]
```

Not allowed:

```json
[null, "missing_first_source", null]
```

---

## 16. Deterministic Aggregation Requirements

The one-time build SQL must avoid double counting.

Use separate CTEs by grain:

```text
base_leads: one row per lead
lead_sources: one row per lead
opt_in_agg: one row per lead
traffic_agg: one row per lead
question_answer_agg: one row per lead
appointment_agg: one row per lead
fathom_agg: one row per lead
contract_agg: one row per lead
payment_agg: one row per lead
refund_agg: one row per lead
final_snapshot: one row per lead
```

Do not join raw one-to-many tables directly into the final SELECT without pre-aggregating them.

Use `COUNT(DISTINCT ...)` where needed.

Use deterministic latest-record ordering with a tie-breaker ID.

---

## 17. One-Time Snapshot Build Script

Create a function/script like:

```text
build_diagnostic_lead_snapshot_once(org_id: str, force: bool = False) -> dict
```

It should:

1. Accept exactly one `org_id`.
2. Validate that `org_id` is provided and not blank.
3. Accept an explicit `force` flag that defaults to `False`.
4. Treat static demo monetary rows as EUR and do not run FX conversion.
5. Start a database transaction.
6. If `force = false`, fail before inserting when snapshot rows already exist for that organization.
7. If `force = true`, delete existing snapshot rows for that organization before rebuilding.
8. Insert snapshot rows from deterministic SQL.
9. Run validation checks.
10. Commit if validation passes.
11. Roll back and raise a clear error if validation fails.
12. Return a build summary.

Return summary fields:

```text
organization_id
force
rows_deleted
rows_inserted
snapshot_built_at
duration_seconds
validation_status
```

For MVP, build once and stop.
For local/demo reruns only, use explicit `force = true` to delete and rebuild transactionally.
Without `force`, the script must fail if snapshot rows already exist for the organization to avoid accidental overwrites.

Do not expose this as a user-facing chatbot tool.
Do not schedule it.
Do not create cron jobs.
Do not create triggers.
Do not implement incremental refresh or upsert logic.

---

## 18. Validation Checks After One-Time Build

After the one-time build, run these checks:

```text
1. Snapshot row count equals active non-deleted lead count for the org.
2. No duplicate (clerk_org_id, lead_id).
3. No null clerk_org_id.
4. No null lead_id.
5. Counts are not negative.
6. Amounts are not negative, except net_collected_amount may be negative only if succeeded refunds exceed paid amount.
7. funnel_stage contains only allowed values.
8. conversion_outcome contains only allowed values.
9. source_confidence contains only high, medium, or low.
10. contract_currency = 'EUR' for every row.
11. payment_currency = 'EUR' for every row.
12. Money columns are major-unit EUR values and are not raw minor-unit source values.
13. source_quality_flags is a JSON array.
14. data_quality_flags is a JSON array.
15. source_quality_flags and data_quality_flags contain no null array elements.
16. Every snapshot row belongs to the selected org_id.
17. For every active non-deleted lead in the selected org, exactly one diagnostic snapshot row exists.
```

If validation fails, raise a clear error and roll back the build.

---

## 19. Important Design Constraints

Do not make this table too complex.
Do not add raw text.
Do not add LLM extraction.
Do not use raw payloads.
Do not use unsupported external ad-spend or ROAS data.
Do not calculate Facebook Ads ROAS, blended ROAS, cost per lead, cost per registration, cost per appointment, cost per sale, YouTube video attribution, scientific attribution, assisted attribution, or multi-touch attribution.

This snapshot only supports CRM-side diagnostic analysis from existing tables.

---

## 20. Supported Diagnostic Usage

This table should support simple diagnostic queries like:

```text
lead count by period
funnel stage by period
funnel stage by source
lifetime net collected revenue by source
signed value by source
paid amount by source
drop-off by source
unknown source percentage
source confidence distribution
sources with high lead volume but low paid revenue
sources with many appointments but low completed calls
sources with signed contracts but low collected cash
sources with poor source data quality
```

Example question support:

```text
Why are leads increasing but revenue is not?
```

The diagnostic layer can compare:

```text
lead_count
appointment_count
completed_call_count
signed_contract_count
paid_payment_count
net_collected_amount
```

Example question support:

```text
Where are we losing people in the funnel?
```

The diagnostic layer can group by:

```text
funnel_stage
conversion_outcome
```

Example question support:

```text
Which source looks good but may be misleading?
```

The diagnostic layer can compare by source:

```text
lead_count
appointment_count
completed_call_count
signed_contract_count
net_collected_amount
refund_amount
source_confidence
data_quality_flags
```

Example question support:

```text
Can we trust source performance?
```

The diagnostic layer can check:

```text
has_unknown_source
has_missing_first_source
has_missing_last_source
has_orphaned_first_source_id
has_orphaned_last_source_id
has_multiple_sources
source_confidence
data_quality_flags
```

---

## 21. Snapshot Scope Warning

This is a cumulative lead-level snapshot.

It supports:

```text
lead-cohort diagnostics
source/funnel drop-off diagnostics
source confidence checks
lifetime revenue/contract/payment status per lead
CRM-side source performance checks
```

It does not fully support:

```text
true payment-period revenue trends
exact revenue collected last month by payment date
exact refund-period trends
multi-touch attribution
revenue by UTM campaign
revenue by landing page
revenue by referrer
revenue by provider form
revenue by form answer
ad spend
ROAS
cost per lead
cost per booked call
cost per sale
```

For true payment-period revenue analysis, use the existing revenue analytics flow with `payments.paid_at` and `refunds.refunded_at`, or build a future diagnostic payment fact table.

Revenue by source in this snapshot means revenue by lead-level first/last marketing source only.

It must not mean revenue by UTM campaign, landing page, referrer, provider form, or form answer.

---

## 22. Out of Scope for This Task

Do not build these yet:

```text
diagnostic agent
diagnostic planner
diagnostic answer prompt
diagnostic tools
diagnostic_text_insights
LLM-based objection extraction
semantic search
vector search
raw text summarization
ad-spend integration
ROAS integration
Facebook Ads integration
YouTube analytics integration
multi-touch attribution model
payment-period diagnostic fact table
```

Only build `diagnostic_lead_snapshot` and its one-time static snapshot build script.

---

## 23. Final Implementation Reminder

The final implementation must be deterministic, safe, tenant-scoped, and business-reviewable.

Before considering the task complete, confirm:

```text
The table exists.
The unique constraint exists.
All required indexes exist.
The one-time build script works for one org_id.
Without force, the build fails if snapshot rows already exist for the organization.
With explicit force, delete-and-rebuild works transactionally for local/demo reruns.
Validation checks pass.
No raw text or sensitive fields are selected or stored.
All monetary outputs assume EUR and are stored as major-unit values after dividing source minor-unit sums by 100.0.
No LOST payment amount is included in outstanding_amount.
Completed-call logic excludes no-show, canceled, and rescheduled appointments.
past_non_no_show_appointment_count exists for compatibility with current appointment analytics.
Each aggregate CTE returns one row per lead before joining into the final snapshot.
```
