# Step 2 — Dummy Data Relationship Map and Insert Order

## Purpose

This document defines how the dummy/demo data should connect across tables before writing the seed script.

Step 1 defined the business blueprint. Step 2 defines the relationship map, insert order, scenario mapping, ID reuse, and validation expectations.

Do not write the seed script until this Step 2 relationship map is reviewed and approved.

---

## 1. Fixed Demo Organization

All dummy/demo records must use:

```text
org_dummy_client_demo_001
```

Rules:

```text
Do not insert dummy data into the live client org.
Do not delete or update live client org data.
Every dummy row with clerk_org_id must use org_dummy_client_demo_001.
Seed cleanup must only delete rows for org_dummy_client_demo_001.
```

---

## 2. Insert Order

Use this insert order so parent/reference records exist before child records.

```text
1. sales_statuses
2. marketing_sources
3. programs
4. appointment_event_types
5. leads
6. opt_ins
7. traffic_attributions
8. opt_in_question_answers
9. appointments
10. fathom_call_records
11. contracts
12. payments
13. refunds
14. invoices
15. payment_links
16. payment_proofs
17. contract_subscriptions
18. subscription_checkout_links
19. unmatched_payments
20. diagnostic_text_insights
21. diagnostic_lead_snapshot
```

Important:

```text
diagnostic_lead_snapshot should be built after base tables are seeded.
Do not manually fake diagnostic_lead_snapshot first.
```

---

## 3. ID Maps to Maintain in the Seed Script

The seed script should create stable IDs and keep dictionaries/maps so child rows can connect correctly.

Recommended maps:

```text
status_ids_by_role
status_ids_by_name
marketing_source_ids_by_name
program_ids_by_name
appointment_event_type_ids_by_name
lead_ids_by_scenario
lead_profile_by_id
opt_in_ids_by_lead_id
appointment_ids_by_lead_id
completed_appointment_ids_by_lead_id
fathom_ids_by_appointment_id
contract_ids_by_lead_id
payment_ids_by_contract_id
payment_ids_by_lead_id
refund_ids_by_payment_id
```

The script should be deterministic. Use a fixed random seed.

Example:

```text
random_seed = 42
```

---

## 4. Reference Table: `sales_statuses`

Create one status per major pipeline role.

| Role | Suggested name | Purpose |
|---|---|---|
| NEW_LEAD | New Lead | Lead created, no major progress yet |
| APPOINTMENT_BOOKED | Appointment Booked | Lead has booked a call |
| NO_SHOW | No Show | Lead missed appointment |
| RESCHEDULED | Rescheduled | Appointment was rescheduled |
| CANCELED | Canceled | Appointment/lead canceled |
| PARTIAL_PAYMENT | Partial Payment | Signed or payment-started but not fully paid |
| WON | Won | Converted/paid customer |
| UNQUALIFIED | Unqualified | Poor fit |
| FOLLOW_UP | No Sale - Follow Up | Needs sales follow-up |
| LOST | Lost | Closed lost |

Rules:

```text
Use the same clerk_org_id for every status.
Make names business-friendly.
Use these statuses for both lead current status and appointment outcome where relevant.
```

---

## 5. Reference Table: `marketing_sources`

Create these exact marketing sources:

```text
Facebook
Instagram
YouTube
Google Search
Webinar
Referral
Email Campaign
Organic Search
Calendly
Landing Page
```

Rules:

```text
No Unknown source.
No blank source.
No orphaned source IDs.
Every lead must have first_source_id and last_source_id.
Every lead must have first_source_name and last_source_name.
first_source_id and last_source_id must point to valid marketing_sources rows.
```

For most leads:

```text
first_source = last_source
```

For around 10% to 15% of leads:

```text
first_source may differ from last_source
```

This is allowed only to show realistic source change, not missing/unknown source issues.

---

## 6. Reference Table: `programs`

Create 3 to 5 simple programs.

| Program | Price minor | Display value |
|---|---:|---:|
| Starter Program | 150000 | €1,500 |
| Growth Program | 300000 | €3,000 |
| Premium Coaching Program | 500000 | €5,000 |
| Freedom Academy | 250000 | €2,500 |
| Trading Accelerator | 400000 | €4,000 |

Rules:

```text
Use EUR only.
Source tables store money in minor units.
Do not store major-unit money in source revenue tables unless the schema column expects major units.
Programs should not be soft-deleted.
```

---

## 7. Reference Table: `appointment_event_types`

Create simple event types:

```text
Qualification Call
Strategy Call
Discovery Call
Follow-up Call
Payment Support Call
```

Suggested call categories:

```text
SALES_CALL
TRIAGE_CALL
COACHING_CALL
```

Rules:

```text
Most demo appointments should be SALES_CALL.
Event names should be client-friendly.
Do not create confusing/internal event names.
Do not mark active demo event types as deleted.
```

---

## 8. Lead Scenario Mapping

Each lead must belong to one scenario.

| Scenario | Lead count | Lead status | Appointment | Fathom | Contract | Payment |
|---|---:|---|---|---|---|---|
| Paid / converted | 110 | WON | Completed | Yes | Signed | Paid |
| Completed call but not signed | 150 | FOLLOW_UP or LOST | Completed | Yes | Sent/viewed or none | None |
| Booked but not completed | 90 | NO_SHOW / CANCELED / RESCHEDULED | No-show/canceled/rescheduled | No | None | None |
| Lead created but never booked | 75 | NEW_LEAD or FOLLOW_UP | None | No | None | None |
| Signed but not paid | 25 | PARTIAL_PAYMENT or FOLLOW_UP | Completed | Yes | Signed | Pending/failed |
| Lost | 30 | LOST | Optional completed/no-show | If completed, yes | Optional voided | None |
| Unqualified | 20 | UNQUALIFIED | Optional triage call | If completed, yes | None | None |

Total leads:

```text
500
```

Rules:

```text
Each lead should have a clear business journey.
The lead status should match the scenario.
Do not create a paid lead with LOST or UNQUALIFIED status.
Do not create an unqualified lead with paid payment.
Do not create a signed-but-not-paid lead without a signed contract.
```

---

## 9. Monthly Lead Distribution

Lead creation dates must follow the Step 1 trend story.

| Month | Lead count |
|---|---:|
| Nov 2025 | 55 |
| Dec 2025 | 70 |
| Jan 2026 | 95 |
| Feb 2026 | 82 |
| Mar 2026 | 90 |
| Apr 2026 | 108 |

Total:

```text
500
```

Rules:

```text
Do not create flat random monthly distribution.
Distribute scenarios across months in a realistic way.
Keep April strong, February slightly down, March recovering.
```

---

## 10. Source Distribution

Use this lead distribution by marketing source.

| Source | Lead count | Demo story |
|---|---:|---|
| Facebook | 90 | High volume, lower conversion |
| Instagram | 60 | Medium volume, lower payment completion |
| YouTube | 65 | Good booked-call volume, many completed-not-signed leads |
| Google Search | 70 | Good lead quality, steady conversion |
| Webinar | 60 | Medium volume, strong call attendance, mixed payment outcome |
| Referral | 40 | Lower volume, high conversion and high revenue |
| Email Campaign | 35 | Lower volume, good follow-up performance |
| Calendly | 30 | Direct booked-call source |
| Landing Page | 30 | Good opt-in volume, mixed call completion |
| Organic Search | 20 | Stable source with average conversion |

Total:

```text
500
```

Rules:

```text
Referral and Google Search should have better conversion rates.
Facebook and Instagram should have higher volume but weaker conversion.
YouTube should have many completed calls but more completed-not-signed leads.
Webinar should have strong attendance but mixed payment outcomes.
```

---

## 11. Lead Table Relationship Rules

Every lead should include:

```text
id
clerk_org_id
first_name
last_name
full_name
email
phone_e164
source
status_id
first_source_id
first_source_name
last_source_id
last_source_name
created_at
updated_at
is_deleted = false
```

Rules:

```text
Use fake names only.
Use example.com or another safe test email domain.
Use fake phone numbers only.
Do not use real client names, real emails, or real phone numbers.
Do not use deleted leads for the main demo dataset.
```

---

## 12. Acquisition Relationship Rules

For every lead:

```text
lead -> one or more opt_ins
opt_in -> zero or one traffic_attributions
opt_in -> many opt_in_question_answers
```

Target:

```text
500 leads
around 650 opt_ins
multiple opt-ins for some leads
```

### `opt_ins`

Each opt-in should connect to:

```text
lead_id
clerk_org_id
source
provider_form_name
created_at
```

Use provider form names:

```text
Qualification Form
Strategy Call Form
Webinar Registration Form
Newsletter Signup Form
Landing Page Lead Form
```

### `traffic_attributions`

Use for marketing attribution fields:

```text
utm_source
utm_medium
utm_campaign
utm_content
utm_term
landing_page
referrer
```

Example campaigns:

```text
jan_growth_campaign
webinar_q1_promo
youtube_strategy_series
facebook_leadgen_q1
google_search_brand
email_followup_sequence
```

Landing pages:

```text
/freedom-academy
/trading-accelerator
/strategy-call
/webinar-registration
/free-training
```

Referrers:

```text
google.com
facebook.com
instagram.com
youtube.com
email
referral
```

### `opt_in_question_answers`

Use for enrichment questions:

```text
profession
employment status
country / region
goal
challenge
budget range
decision-maker status
start timeline
experience level
```

Rules:

```text
Do not confuse geographic location with marketing source.
Do not use precise addresses.
Do not use real personal location data.
Do not use form answers to claim revenue attribution unless approved later.
```

---

## 13. Appointment Relationship Rules

Appointment relationship:

```text
lead -> appointments
```

Target:

```text
around 420 appointments
around 260 completed / attended past calls
around 55 no-shows
around 35 canceled
around 30 rescheduled
around 40 future scheduled
```

Every appointment should include:

```text
id
lead_id
clerk_org_id
schedule_time
host_id
setter_id
snapshot_event_name
snapshot_call_category
appointment_event_type_id
outcome_id
no_show
source
created_at
updated_at
is_deleted = false
```

Rules:

```text
Appointment date must be after lead.created_at.
Most appointments should happen 1 to 14 days after lead creation.
Future appointments should not have Fathom records.
No-show appointments should have no_show = true.
Canceled/rescheduled appointments should use matching outcome status.
Completed appointments should have no_show = false and non-canceled/non-rescheduled outcome.
```

---

## 14. Fathom Relationship Rules

Fathom relationship:

```text
completed appointment -> exactly one fathom_call_record
```

Fixed demo rule:

| Appointment scenario | Fathom record? |
|---|---:|
| Completed / attended sales call | Yes |
| No-show | No |
| Canceled | No |
| Rescheduled | No |
| Future appointment | No |
| Attended but missing Fathom | Avoid |

Expected outcome:

```text
completed_call_count = fathom_record_count
completed_calls_missing_fathom_count = 0
completed_call_fathom_coverage_rate = 100.00
```

Every Fathom record should include:

```text
id
appointment_id
clerk_org_id
summary
key_points
action_items
objections
ai_generated_title
ai_suggested_outcome
ai_confidence_score
ai_rationale
outcome_applied
match_strategy
call_duration_seconds
call_started_at
call_ended_at
created_at
updated_at
```

Keep these null:

```text
raw_payload
recording_url
transcript_url
```

Rules:

```text
Do not create Fathom records for no-show appointments.
Do not create Fathom records for canceled appointments.
Do not create Fathom records for rescheduled appointments.
Do not create Fathom records for future appointments.
Do not create Fathom records without a valid appointment.
Do not create more than one Fathom record per completed appointment for this demo.
```

---

## 15. Fathom Story Mapping

Assign Fathom story templates based on lead scenario.

| Lead scenario | Fathom story type |
|---|---|
| Paid / converted | converted_strong_intent or converted_after_payment_plan |
| Completed call but not signed | completed_not_signed_partner_approval, completed_not_signed_budget, or completed_not_signed_needs_more_time |
| Signed but not paid | signed_not_paid_payment_link_issue or signed_not_paid_payment_timing |
| Lost | lost_low_intent |
| Unqualified | unqualified_poor_fit |
| Follow-up pending | follow_up_needs_more_information |

Rules:

```text
Fathom summaries should sound like real business call notes.
Do not use placeholder text.
Do not expose private data.
Objections should align with the lead scenario.
Action items should be practical and easy to understand.
```

---

## 16. Contract Relationship Rules

Contract relationship:

```text
lead -> contract -> optional payment
```

Contract scenarios:

| Lead scenario | Contract behavior |
|---|---|
| Paid / converted | Signed contract |
| Signed but not paid | Signed contract |
| Completed call but not signed | Sent/viewed contract optional |
| Lost | Optional voided contract |
| Unqualified | No contract |
| Lead only / never booked | No contract |
| Booked but not completed | No contract |

Every contract should include:

```text
id
clerk_org_id
lead_id
program_id
closer_id
setter_id
type
total_value
currency = EUR
status
sent_at
viewed_at
signed_at
voided_at
created_at
updated_at
is_deleted = false
```

Rules:

```text
Signed contracts must have signed_at.
Sent/viewed contracts should have sent_at and optionally viewed_at.
Voided contracts should have voided_at.
Do not create paid payments for unsigned contracts.
Do not create contracts for unqualified leads unless intentionally testing edge cases; avoid for client demo.
```

---

## 17. Payment Relationship Rules

Payment relationship:

```text
contract -> payment
lead -> payment
payment -> optional invoice
payment -> optional payment_proof
payment -> optional refund
```

Payment behavior by scenario:

| Lead scenario | Payment behavior |
|---|---|
| Paid / converted | One or more PAID payments |
| Signed but not paid | PENDING or FAILED payment |
| Completed call but not signed | No payment |
| Lost | No paid payment |
| Unqualified | No payment |

Payment statuses to use:

```text
PAID
PENDING
FAILED
LOST
REFUNDED
```

Payment providers:

```text
STRIPE
MOLLIE
MANUAL
```

Rules:

```text
Use EUR only.
Source payment amount should use the schema's expected unit.
If amount is stored as minor units, use values like 250000 for €2,500.
Paid payments should have paid_at.
Pending payments should have due_date.
Failed payments can have due_date and failed-like status.
Do not create payment before contract signed.
Do not create payment for unqualified leads.
```

---

## 18. Refund Relationship Rules

Refund relationship:

```text
paid payment -> refund
```

Target:

```text
10 to 15 refund cases
```

Rules:

```text
Refunds must connect to valid paid payments.
Refund date must be after payment paid_at.
Refund amount must not exceed original payment amount.
Use status SUCCEEDED for normal demo refunds.
Use FAILED or INITIATED only if needed for refund status demo.
```

---

## 19. Invoice, Payment Link, and Payment Proof Rules

These are optional support tables for richer revenue demo.

### Invoices

```text
Create invoices for some paid payments.
Invoice status should match the payment/refund story.
```

### Payment Links

```text
Create payment links only if needed for demo.
Do not use real URLs.
Prefer keeping URL null or using safe placeholder values only if schema requires it.
```

### Payment Proofs

```text
Create payment proofs for some MANUAL payments.
Do not create real file keys or real uploads.
Use safe placeholder/demo values only if schema requires it.
```

Do not expose:

```text
real payment links
provider payment IDs
provider secrets
file keys
raw provider payloads
```

---

## 20. Subscription Rules

Only generate subscription data if needed for demo.

If generated:

```text
Use active subscriptions only for a small number of paid leads.
Use pending or past-due subscriptions for a small number of signed-not-paid leads.
Keep subscription checkout links safe and non-real.
```

Avoid complex subscription edge cases in the first demo dataset.

---

## 21. Unmatched Payment Rules

Unmatched payments are optional.

If generated:

```text
Create only a small number.
Use generic customer names/emails.
Do not use real external payment IDs.
Use safe placeholder IDs only if schema requires them.
```

For client demo, this table is lower priority than leads, appointments, Fathom, contracts, and payments.

---

## 22. Diagnostic Text Insights Relationship Rules

If `diagnostic_text_insights` is seeded directly, generate insights from the lead scenario and Fathom/notes story.

Relationship:

```text
lead -> diagnostic_text_insights
source record can be fathom_call_records, payments, contracts, opt_in_question_answers, or lead notes if available
```

Use useful reason categories:

```text
timing_issue
needs_partner_approval
price_or_budget
payment_friction
contract_friction
needs_more_information
low_intent
poor_fit
follow_up_pending
no_show
ghosted
trust_issue
```

Rules:

```text
Avoid overusing unknown.
Do not call LLM during seed unless intentionally running an extraction job.
If seeded deterministically, align reason_category with lead scenario.
```

Examples:

| Scenario | Reason category | Reason subcategory |
|---|---|---|
| Completed call but not signed | timing_issue | needs_more_time |
| Completed call but not signed | needs_partner_approval | waiting_for_partner |
| Signed but not paid | payment_friction | payment_not_completed |
| Booked but not completed | no_show | missed_call |
| Lost | low_intent | not_ready_now |
| Unqualified | poor_fit | wrong_customer_fit |

---

## 23. Diagnostic Lead Snapshot Rules

Do not insert `diagnostic_lead_snapshot` manually as the primary source.

Correct flow:

```text
Seed base tables
Run diagnostic snapshot builder for org_dummy_client_demo_001
Validate diagnostic snapshot
```

Expected:

```text
diagnostic_lead_snapshot row count = active dummy lead count
completed_calls_missing_fathom_count = 0
completed_call_fathom_coverage_rate = 100.00
no unknown source quality flags
money fields in diagnostic snapshot are major-unit EUR
```

---

## 24. Date Sequencing Rules

Every journey should follow this order:

```text
lead.created_at
↓
opt_ins.created_at
↓
appointments.schedule_time
↓
fathom_call_records.call_started_at / call_ended_at
↓
contracts.sent_at / viewed_at / signed_at
↓
payments.due_date / paid_at
↓
refunds.created_at if applicable
```

Never create impossible timelines:

```text
appointment before lead creation
Fathom before appointment
contract signed before completed call
payment before contract signed
refund before payment
future appointment with Fathom
no-show appointment with Fathom
```

---

## 25. Cleanup Strategy for Dummy Org

The seed script should support a safe force rebuild for only the dummy org.

Rules:

```text
Require explicit org_id argument.
Require org_id = org_dummy_client_demo_001 unless explicitly overridden in local-only mode.
Refuse to run if org_id is empty.
Refuse to run if org_id matches known live org ID.
Delete only rows for org_dummy_client_demo_001.
Delete child rows before parent rows.
Never truncate full tables.
Never delete rows without clerk_org_id filtering, except child tables that require join through parent table.
```

Child-table cleanup must be careful for tables that do not directly have `clerk_org_id`.

For child tables without direct `clerk_org_id`, delete through parent joins only.

---

## 26. Validation Requirements

After seeding, run validation checks.

### Organization Safety

```text
All inserted rows use org_dummy_client_demo_001.
No rows are inserted into live client org.
No cleanup affects live client org.
```

### Source Validation

```text
No lead has missing first_source_id.
No lead has missing last_source_id.
No lead has blank first_source_name or last_source_name.
No source name is Unknown.
All first_source_id and last_source_id join to marketing_sources.
No revenue exists without a valid source.
```

### Lead Validation

```text
Total active dummy leads = 500.
Monthly lead distribution matches the blueprint.
Lead source distribution matches the blueprint.
Every lead has a valid status_id.
Every lead has fake email and fake phone only.
No deleted leads are included in main demo counts.
```

### Acquisition Validation

```text
Every opt-in joins to a valid lead.
Most leads have at least one opt-in.
Total opt-ins are around 650.
Traffic attribution rows join to valid opt-ins.
Form answer rows join to valid opt-ins.
Profession answers exist for most opt-ins.
Country or region answers exist for most opt-ins.
Budget range answers exist for most opt-ins.
Decision-maker answers exist for most opt-ins.
No precise addresses are generated.
```

### Appointment and Fathom Validation

```text
Every appointment joins to a valid lead.
Completed/attended past appointments have exactly one Fathom record.
No no-show appointment has Fathom record.
No canceled appointment has Fathom record.
No rescheduled appointment has Fathom record.
No future appointment has Fathom record.
No Fathom record exists without valid appointment.
completed_calls_missing_fathom_count = 0.
completed_call_fathom_coverage_rate = 100.00.
```

### Revenue Validation

```text
Every contract joins to a valid lead and program.
Every paid payment joins to a valid lead and signed contract.
Every refund joins to a valid paid payment.
Refund amount does not exceed original paid amount.
Paid leads have paid payments.
Signed-not-paid leads have pending or failed payments.
Unqualified leads do not have payments.
```

### Business Story Validation

```text
There are leads in every planned funnel scenario.
There is a visible monthly trend.
Source performance varies by source.
Facebook has higher volume and weaker conversion.
Referral and Google Search have stronger conversion.
YouTube has many completed-not-signed leads.
Webinar has strong attendance with mixed payment outcome.
There are meaningful Fathom summaries, objections, and action items.
```

### Diagnostic Validation

```text
diagnostic_lead_snapshot row count = active dummy lead count.
No unknown source quality flags.
No missing source quality flags.
completed_calls_missing_fathom_count = 0.
completed_call_fathom_coverage_rate = 100.00.
Diagnostic money values are in major-unit EUR.
```

---

## 27. Step 2 Completion Criteria

Step 2 is complete when this document is reviewed and approved.

Checklist:

```text
Insert order is finalized.
Reference table values are finalized.
ID map strategy is finalized.
Lead scenario mapping is finalized.
Source distribution relationship is finalized.
Acquisition relationship rules are finalized.
Appointment/Fathom relationship rules are finalized.
Revenue relationship rules are finalized.
Date sequencing rules are finalized.
Cleanup strategy is defined.
Validation checks are defined.
```

---

## 28. Next Step Hint

Step 3 should be the Codex implementation instruction.

Step 3 should ask Codex to create a deterministic Python seed script that:

```text
connects to Postgres
accepts org_dummy_client_demo_001
optionally force-cleans only dummy org data
seeds all parent and child tables in the correct order
creates realistic scenario-based records
generates 100% Fathom coverage for completed calls
runs validation checks
builds diagnostic_lead_snapshot after base data
prints a final row-count and validation report
```

Do not start Step 3 until this Step 2 relationship map is approved.
