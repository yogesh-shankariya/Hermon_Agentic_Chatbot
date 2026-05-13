# Codex Task: Build `diagnostic_lead_snapshot` for MVP Diagnostic Analytics

## Goal

Build a deterministic lead-level snapshot table for diagnostic analytics.

This table will help answer broad diagnostic questions such as:

- Why are leads increasing but revenue is not?
- Where are we losing people in the funnel?
- Which source looks good but may be misleading?
- Can we trust source performance?
- Which source has high lead volume but weak conversion?
- Which source has booked calls but low paid revenue?
- Which source has signed contracts but low collected cash?
- Which source creates leads but not booked calls?
- Which source creates booked calls but not sales?

This task is only for the numeric/source/funnel diagnostic layer.

Do not build the final diagnostic agent yet.
Do not add LLM calls.
Do not extract raw text insights in this task.
Do not include raw notes, raw call summaries, raw objections, raw form answers, emails, phone numbers, links, raw payloads, webhook payloads, external provider IDs, credentials, or API keys.

---

## Required Deliverables

Create:

1. A new table/model named `diagnostic_lead_snapshot`.
2. A refresh/backfill function or script for one organization.
3. A deterministic SQL aggregation pipeline.
4. Indexes for diagnostic query performance.
5. Basic validation checks after refresh.

Use existing project style and database patterns.

---

## Monetary Unit Rule

The revenue source tables store money in minor units:

```text
contracts.total_value
payments.amount
refunds.amount
```

All money columns stored in `diagnostic_lead_snapshot` must be business-facing major-unit EUR values.

Divide source monetary sums by `100.0` before writing them into the snapshot. After the values are in `diagnostic_lead_snapshot`, do not divide them by `100` again.

---

## Table Grain

One row per:

```text
clerk_org_id + lead_id
````

Use either:

```text
DELETE existing snapshot rows for org_id, then INSERT fresh rows
```

or:

```text
UPSERT using unique constraint on (clerk_org_id, lead_id)
```

For MVP, delete-and-reinsert for the selected organization is acceptable and simpler.

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

Do not use admin, credential, webhook, raw payload, or integration-secret tables.

---

## Organization Scope

For MVP, refresh only one organization.

All source queries must filter by:

```sql
clerk_org_id = :org_id
```

For child tables without `clerk_org_id`, always join through the parent table that has org scope.

Examples:

```sql
opt_in_question_answers -> opt_ins
traffic_attributions -> opt_ins
```

---

## Soft Delete Rules

Exclude soft-deleted rows by default:

```sql
leads.is_deleted = false
appointments.is_deleted = false
contracts.is_deleted = false
payments.is_deleted = false
programs.is_deleted = false
```

Do not add soft-delete filters to tables that do not have `is_deleted`.

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
raw lead notes
raw appointment notes
raw call summaries
raw objections
raw action items
raw form answers
```

This table must stay numeric, source, funnel, and status focused.

---

## Required Columns

### Identity

```text
id
clerk_org_id
lead_id
lead_created_at
lead_updated_at
snapshot_refreshed_at
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

Use these as guidance:

```text
id                              uuid primary key default gen_random_uuid()
clerk_org_id                    text not null
lead_id                         uuid not null

lead_created_at                 timestamptz
lead_updated_at                 timestamptz
snapshot_refreshed_at           timestamptz not null default now()

current_status_id               uuid nullable
current_status_name             text nullable
current_status_role             text nullable
assigned_to                     text nullable
setter_id                       text nullable
next_touch_point_at             timestamptz nullable
next_touch_point_type           text nullable

source ids                      uuid nullable
source/name/status fields        text nullable
counts                          integer not null default 0
booleans                        boolean not null default false
amounts                         numeric(12,2) not null default 0
duration seconds                numeric nullable
day gaps                        integer nullable

source_quality_flags             jsonb not null default '[]'::jsonb
data_quality_flags               jsonb not null default '[]'::jsonb
```

Add unique constraint:

```text
unique (clerk_org_id, lead_id)
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
(clerk_org_id, first_source)
(clerk_org_id, last_source)
(clerk_org_id, net_collected_amount)
(clerk_org_id, signed_contract_value)
(clerk_org_id, snapshot_refreshed_at)
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
- next_touch_point_at is null
- current_status_role is not WON, LOST, UNQUALIFIED, CANCELED

is_overdue_followup = true only when:
- next_touch_point_at < now()
- current_status_role is not WON, LOST, UNQUALIFIED, CANCELED
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
first_source = COALESCE(first_ms.name, NULLIF(TRIM(l.first_source_name), ''), 'Unknown')

last_source_id = l.last_source_id
last_source = COALESCE(last_ms.name, NULLIF(TRIM(l.last_source_name), ''), 'Unknown')
```

Source flags:

```text
source_changed = first_source <> last_source

has_missing_first_source =
  l.first_source_id is null
  and l.first_source_name is null or blank

has_missing_last_source =
  l.last_source_id is null
  and l.last_source_name is null or blank

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

`source_confidence` logic:

```text
high:
- first_source is not Unknown
- last_source is not Unknown
- no orphaned first/last source IDs

medium:
- first_source or last_source is Unknown
- or first_source <> last_source

low:
- both first_source and last_source are Unknown
- or source IDs are orphaned
```

`source_quality_flags` should be a JSON array.

Possible values:

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

Populate:

```text
opt_in_count = count(opt_ins)
first_opt_in_at = min(o.created_at)
latest_opt_in_at = max(o.created_at)
first_opt_in_source = source from earliest opt-in
latest_opt_in_source = source from latest opt-in
first_provider_form_name = provider_form_name from earliest opt-in
latest_provider_form_name = provider_form_name from latest opt-in
has_multiple_opt_ins = opt_in_count > 1
```

For first/latest opt-in, use window functions:

```sql
ROW_NUMBER() OVER (PARTITION BY o.lead_id ORDER BY o.created_at ASC, o.id ASC) = 1
ROW_NUMBER() OVER (PARTITION BY o.lead_id ORDER BY o.created_at DESC, o.id DESC) = 1
```

---

## 4. Traffic Attribution Logic

Join traffic attribution through opt-ins:

```sql
LEFT JOIN traffic_attributions ta
  ON ta.opt_in_id = o.id
```

Do not query `traffic_attributions` without joining to `opt_ins`.

Populate first attribution fields from the earliest opt-in/attribution available:

```text
first_utm_source
first_utm_medium
first_utm_campaign
first_landing_page
first_referrer
```

Populate latest attribution fields from the latest opt-in/attribution available:

```text
latest_utm_source
latest_utm_medium
latest_utm_campaign
latest_landing_page
latest_referrer
```

Coverage flags:

```text
has_traffic_attribution = at least one traffic_attributions row exists for the lead

missing_utm_source = no non-blank utm_source across lead opt-ins
missing_utm_campaign = no non-blank utm_campaign across lead opt-ins
missing_landing_page = no non-blank landing_page across lead opt-ins
missing_referrer = no non-blank referrer across lead opt-ins
```

Do not use UTM fields for revenue attribution in this table.
Only store them as diagnostic context.

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

Do not store raw questions or answers in `diagnostic_lead_snapshot`.

Raw question/answer text belongs to a future table called `diagnostic_text_insights`.

---

## 6. Appointment Logic

Aggregate `appointments` by lead.

Filter:

```sql
a.clerk_org_id = :org_id
AND a.is_deleted = false
```

Populate:

```text
appointment_count = count(distinct a.id)
past_appointment_count = count where a.schedule_time < now()
upcoming_appointment_count = count where a.schedule_time >= now()
no_show_count = count where a.no_show = true
first_appointment_at = min(a.schedule_time)
latest_appointment_at = max(a.schedule_time)
latest_host_id = host_id from latest appointment
latest_event_type_name = snapshot_event_name from latest appointment
latest_call_category = snapshot_call_category::text from latest appointment
```

Completed call logic for MVP:

```text
completed_call_count =
count of past appointments where:
- schedule_time < now()
- no_show = false
```

This is an approximation because there is no single completed flag. If Fathom record exists, it also supports that the call likely happened.

Populate:

```text
latest_completed_call_at = max(schedule_time) where schedule_time < now() and no_show = false
```

Cancelled appointment logic:

```text
cancelled_appointment_count =
count where appointment outcome role is CANCELED
```

Join appointment outcome:

```sql
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
```

Populate latest appointment outcome from latest appointment:

```text
latest_appointment_outcome_name = outcome.name
latest_appointment_outcome_role = outcome.role::text
```

---

## 7. Fathom Coverage Logic

Join Fathom call records only for counts and duration.

Do not store raw summary, key points, objections, action items, AI rationale, transcript, or recording URLs.

Use appointment-linked Fathom records.

Populate:

```text
has_fathom_record = count(fathom records) > 0
fathom_record_count = count(distinct fathom_call_records.id)
avg_call_duration_seconds = average duration if duration column exists
total_call_duration_seconds = sum duration if duration column exists
```

If the exact duration column name differs, inspect schema and use the correct existing column.
If no duration column exists, keep these fields nullable.

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
signed_contract_count = count where c.status = 'SIGNED'
sent_contract_count = count where c.status = 'SENT'
viewed_contract_count = count where c.status = 'VIEWED'
voided_contract_count = count where c.status = 'VOIDED'
signed_contract_value = sum(c.total_value) / 100.0 where c.status = 'SIGNED'
```

Latest contract fields should come from the latest contract by:

```text
COALESCE(c.signed_at, c.sent_at, c.created_at)
```

Populate from latest contract:

```text
latest_contract_status
latest_contract_sent_at
latest_contract_signed_at
latest_contract_voided_at
contract_currency
closer_id
contract_setter_id
```

Join program:

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
has_contract_without_payment =
contract_count > 0 and payment_count = 0
```

---

## 9. Payment Logic

Aggregate `payments` by lead.

Primary join:

```text
payments.lead_id = leads.id
```

Also handle payments linked to contracts if needed:

```text
payments.contract_id -> contracts.id -> contracts.lead_id
```

Avoid double counting. Use a payment CTE that resolves one `resolved_lead_id` per payment:

```text
resolved_lead_id = COALESCE(p.lead_id, c.lead_id)
```

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
latest_payment_status = status from latest payment
latest_paid_at = max(p.paid_at)
latest_payment_due_date = due_date from latest payment
payment_currency = currency from latest payment
```

Do not include LOST payment amount in `outstanding_amount` or `overdue_amount`.

Latest payment should be selected by:

```text
COALESCE(p.paid_at, p.due_date, p.created_at)
```

Payment quality flag:

```text
has_payment_without_contract =
payment_count > 0 and contract_count = 0
```

---

## 10. Refund Logic

Aggregate `refunds` by payment/lead.

Use only succeeded refunds for refund amount:

```text
refund_amount = sum(refund amount) / 100.0 where refund.status = 'SUCCEEDED'
```

Join refunds to payments, then to resolved lead.

Do not add soft-delete filter to refunds if refunds table has no `is_deleted`.

Calculate:

```text
net_collected_amount = gross_paid_amount - refund_amount
```

Both `gross_paid_amount` and `refund_amount` must already be major-unit EUR values before this subtraction.

Revenue/source quality flag:

```text
has_revenue_without_source =
net_collected_amount > 0 and has_unknown_source = true
```

---

## 11. Funnel Stage Logic

Calculate `funnel_stage` using the farthest meaningful stage reached.

Base logic:

```text
If net_collected_amount > 0:
  paid

Else if signed_contract_count > 0:
  signed_not_paid

Else if completed_call_count > 0:
  completed_not_signed

Else if appointment_count > 0:
  booked_not_completed

Else:
  lead_only
```

Override logic:

```text
If refund_amount > 0 and net_collected_amount <= 0:
  refunded

If current_status_role = 'LOST':
  lost

If current_status_role = 'UNQUALIFIED':
  unqualified
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

---

## 12. Conversion Outcome Logic

Calculate `conversion_outcome`.

Recommended values:

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

---

## 13. Stage Delay Logic

Calculate day gaps:

```text
lead_to_booked_days =
date difference between first_appointment_at and lead_created_at

booked_to_completed_days =
date difference between latest_completed_call_at and first_appointment_at

completed_to_signed_days =
date difference between latest_contract_signed_at and latest_completed_call_at

signed_to_paid_days =
date difference between latest_paid_at and latest_contract_signed_at
```

Return null if either side is missing.

Use integer days.

---

## 14. Multiple Source Logic

Calculate:

```text
has_multiple_sources =
first_source <> last_source
OR first_utm_source <> latest_utm_source
OR first_utm_campaign <> latest_utm_campaign
```

Use null-safe comparison.

---

## 15. Data Quality Flags

Store `data_quality_flags` as JSON array.

Possible values:

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

Set corresponding boolean columns as well.

---

## 16. Snapshot Refresh Function

Create a function/script like:

```text
refresh_diagnostic_lead_snapshot(org_id: str) -> dict
```

It should:

1. Accept one `org_id`.
2. Delete existing snapshot rows for that organization.
3. Insert fresh snapshot rows from deterministic SQL.
4. Return refresh summary.

Return summary fields:

```text
organization_id
rows_deleted
rows_inserted
snapshot_refreshed_at
duration_seconds
```

If project style prefers upsert, use upsert instead of delete-insert.

---

## 17. Validation Checks After Refresh

After refresh, run basic checks:

```text
1. Snapshot row count should equal active non-deleted lead count for the org.
2. No duplicate (clerk_org_id, lead_id).
3. No null clerk_org_id.
4. No null lead_id.
5. Counts should not be negative.
6. Amounts should not be negative except net_collected_amount may be zero but should not be negative unless refunds exceed paid amount.
7. funnel_stage should only contain allowed values.
8. conversion_outcome should only contain allowed values.
9. Money columns should be major-unit EUR values and not raw minor-unit source values.
```

If validation fails, raise a clear error.

---

## 18. Important Design Constraints

Do not make this table too complex.
Do not add raw text.
Do not add LLM extraction.
Do not use raw payloads.
Do not use unsupported external ad-spend or ROAS data.
Do not calculate Facebook Ads ROAS, blended ROAS, cost per lead, cost per registration, cost per appointment, cost per sale, YouTube video attribution, scientific attribution, assisted attribution, or multi-touch attribution.

This snapshot only supports CRM-side diagnostic analysis from existing tables.

---

## 19. Expected Diagnostic Usage

The table should allow simple SQL queries like:

```text
lead count by period
funnel stage by period
funnel stage by source
revenue by source
signed value by source
paid amount by source
drop-off by source
unknown source percentage
source confidence distribution
source with high lead volume but low paid revenue
source with many appointments but low completed calls
source with signed contracts but low collected cash
```

Example question support:

```text
Why are leads increasing but revenue is not?
```

The diagnostic agent can compare:

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

The diagnostic agent can group by:

```text
funnel_stage
conversion_outcome
```

Example question support:

```text
Which source looks good but may be misleading?
```

The diagnostic agent can compare by source:

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

The diagnostic agent can check:

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

## 20. Out of Scope for This Task

Do not build these yet:

```text
diagnostic agent
diagnostic planner
diagnostic answer prompt
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
```

Only build `diagnostic_lead_snapshot` and its refresh logic.

```
```
