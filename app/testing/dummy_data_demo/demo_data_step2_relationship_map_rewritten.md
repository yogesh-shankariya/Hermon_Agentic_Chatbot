# Step 2 — Dummy Data Relationship Map and Insert Order

## Purpose

This document defines how the dummy/demo data should connect across tables before writing the seed script.

Step 1 defined the business blueprint. Step 2 defines the relationship map, insert order, scenario mapping, ID reuse, cleanup safety, and validation expectations.

This document is intentionally focused on the first client demo. The first demo should be clean, understandable, and business-friendly. It should avoid operational/admin noise that can distract the client.

Do not write the seed script until this Step 2 relationship map is reviewed and approved.

---

## 1. Fixed Demo Organization

All dummy/demo records must use one fixed organization ID:

```text
org_dummy_client_demo_001
```

### Rules

```text
Do not insert dummy data into the live client organization.
Do not delete or update live client organization data.
Every dummy row with clerk_org_id must use org_dummy_client_demo_001.
Seed cleanup must only delete rows for org_dummy_client_demo_001.
The seed script must refuse to run if org_id is empty.
The seed script must refuse to run if org_id is the known live client org ID.
```

---

## 2. First Demo Scope

The first demo should focus on the main business journey:

```text
Lead created
↓
Opt-in / form submission
↓
Appointment booked
↓
Completed call or no-show/canceled/rescheduled
↓
Fathom call record for completed calls
↓
Contract sent/signed
↓
Payment paid/pending/failed/refunded
↓
Diagnostic snapshot and insights
```

### Required Tables for First Demo

Seed these tables:

```text
sales_statuses
marketing_sources
programs
appointment_event_types
leads
opt_ins
traffic_attributions
opt_in_question_answers
appointments
fathom_call_records
contracts
payments
refunds
diagnostic_text_insights
diagnostic_lead_snapshot
```

### Optional Tables Not Seeded by Default

Do not seed these tables for the first demo unless explicitly required later:

```text
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
```

Reason:

```text
The first demo should avoid operational/admin noise such as missing invoices, invalid payment links, missing payment proofs, subscription edge cases, or unmatched payment reconciliation.
```

---

## 3. Required Insert Order

Use this insert order for the first demo.

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
14. diagnostic_text_insights
15. diagnostic_lead_snapshot
```

Important:

```text
diagnostic_lead_snapshot should be built after base tables are seeded.
Do not manually fake diagnostic_lead_snapshot first.
```

---

## 4. Optional Tables for Later Demo Versions

The following tables are supported by the wider schema, but should be skipped for the first client demo.

### `invoices`

Skip initially.

Add later only if the client specifically needs invoice questions.

### `payment_links`

Skip initially.

Do not create fake real-looking payment URLs.

Do not expose payment URLs in the demo.

### `payment_proofs`

Skip initially.

Add later only if manual-payment proof questions are required.

Do not create real file keys or upload references.

### `contract_subscriptions`

Skip initially.

Add later only if subscription or MRR demo questions are required.

### `subscription_checkout_links`

Skip initially.

Add later only if subscription checkout demo questions are required.

Do not create fake real-looking checkout URLs.

### `unmatched_payments`

Skip initially.

Reason:

```text
Unmatched payments are more of an operational reconciliation workflow and are not required for the first client-facing funnel and revenue demo.
```

---

## 5. ID Maps to Maintain in the Seed Script

The seed script should create stable IDs and keep dictionaries/maps so child rows can connect correctly.

The script should be deterministic.

Recommended fixed random seed:

```text
random_seed = 42
```

Recommended ID maps:

```text
status_ids_by_role
status_ids_by_name
marketing_source_ids_by_name
program_ids_by_name
appointment_event_type_ids_by_name
lead_ids_by_scenario
lead_profile_by_id
opt_in_ids_by_lead_id
traffic_attribution_ids_by_opt_in_id
question_answer_ids_by_opt_in_id
appointment_ids_by_lead_id
completed_appointment_ids_by_lead_id
fathom_ids_by_appointment_id
contract_ids_by_lead_id
payment_ids_by_contract_id
payment_ids_by_lead_id
refund_ids_by_payment_id
diagnostic_text_insight_ids_by_lead_id
```

### Why These Maps Matter

```text
Leads need valid status and source IDs.
Opt-ins need valid lead IDs.
Traffic attribution rows need valid opt-in IDs.
Form-answer rows need valid opt-in IDs.
Appointments need valid lead IDs and event type IDs.
Fathom rows need valid completed appointment IDs.
Contracts need valid lead and program IDs.
Payments need valid contracts and leads.
Refunds need valid paid payments.
Diagnostic text insights need valid leads and source records.
```

---

## 6. Reference Table: `sales_statuses`

Create one status per major pipeline role.

| Role | Suggested name | Purpose |
|---|---|---|
| NEW_LEAD | New Lead | Lead created, no major progress yet |
| APPOINTMENT_BOOKED | Appointment Booked | Lead has booked a call |
| NO_SHOW | No Show | Lead missed appointment |
| RESCHEDULED | Rescheduled | Appointment was rescheduled |
| CANCELED | Canceled | Appointment or lead canceled |
| PARTIAL_PAYMENT | Partial Payment | Signed or payment-started but not fully paid |
| WON | Won | Converted/paid customer |
| UNQUALIFIED | Unqualified | Poor fit |
| FOLLOW_UP | No Sale - Follow Up | Needs sales follow-up |
| LOST | Lost | Closed lost |

### Rules

```text
Use org_dummy_client_demo_001 for every status.
Make names business-friendly.
Use these statuses for both lead current status and appointment outcome where relevant.
Do not create confusing or internal-only status names.
```

---

## 7. Reference Table: `marketing_sources`

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

### Rules

```text
No Unknown source.
No blank source.
No missing source.
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

## 8. Reference Table: `programs`

Create 3 to 5 simple programs.

| Program | Price minor | Display value |
|---|---:|---:|
| Starter Program | 150000 | €1,500 |
| Growth Program | 300000 | €3,000 |
| Premium Coaching Program | 500000 | €5,000 |
| Freedom Academy | 250000 | €2,500 |
| Trading Accelerator | 400000 | €4,000 |

### Rules

```text
Use EUR only.
Source tables store money in minor units when schema expects minor units.
Programs should not be soft-deleted.
Program names should be simple and client-friendly.
```

---

## 9. Reference Table: `appointment_event_types`

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

### Rules

```text
Most demo appointments should be SALES_CALL.
Event names should be client-friendly.
Do not create confusing/internal event names.
Do not mark active demo event types as deleted.
```

---

## 10. Lead Scenario Mapping

Each lead must belong to one scenario.

| Scenario | Lead count | Lead status | Appointment | Fathom | Contract | Payment |
|---|---:|---|---|---|---|---|
| Paid / converted | 110 | WON | Completed | Yes | Signed | Paid |
| Completed call but not signed | 150 | FOLLOW_UP or LOST | Completed | Yes | Sent/viewed optional or none | None |
| Booked but not completed | 90 | NO_SHOW / CANCELED / RESCHEDULED | No-show/canceled/rescheduled | No | None | None |
| Lead created but never booked | 75 | NEW_LEAD or FOLLOW_UP | None | No | None | None |
| Signed but not paid | 25 | PARTIAL_PAYMENT or FOLLOW_UP | Completed | Yes | Signed | Pending/failed |
| Lost | 30 | LOST | Optional completed/no-show | If completed, yes | Optional voided | None |
| Unqualified | 20 | UNQUALIFIED | Optional triage call | If completed, yes | None | None |

Total leads:

```text
500
```

### Rules

```text
Each lead should have a clear business journey.
The lead status should match the scenario.
Do not create a paid lead with LOST or UNQUALIFIED status.
Do not create an unqualified lead with paid payment.
Do not create a signed-but-not-paid lead without a signed contract.
Do not create a completed/attended appointment without a Fathom record.
```

---

## 11. Monthly Lead Distribution

Lead creation dates must follow the Step 1 trend story.

| Month | Lead count | Intended story |
|---|---:|---|
| Nov 2025 | 55 | Starting baseline |
| Dec 2025 | 70 | Growth begins |
| Jan 2026 | 95 | Strong campaign growth |
| Feb 2026 | 82 | Slight decrease after campaign peak |
| Mar 2026 | 90 | Stabilized and recovering |
| Apr 2026 | 108 | Growth returns |

Total:

```text
500
```

### Rules

```text
Do not create flat random monthly distribution.
Distribute scenarios across months in a realistic way.
Keep April strong.
Keep February slightly down.
Keep March recovering.
```

---

## 12. Source Distribution

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

### Rules

```text
Referral and Google Search should have better conversion rates.
Facebook and Instagram should have higher volume but weaker conversion.
YouTube should have many completed calls but more completed-not-signed leads.
Webinar should have strong attendance but mixed payment outcomes.
Do not create Unknown source.
```

---

## 13. Lead Table Relationship Rules

Every lead should include at minimum:

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

### Rules

```text
Use fake names only.
Use example.com or another safe test email domain.
Use fake phone numbers only.
Do not use real client names, real emails, or real phone numbers.
Do not use deleted leads for the main demo dataset.
Every lead must have a valid sales_statuses reference.
Every lead must have valid marketing source references.
```

---

## 14. Acquisition Relationship Rules

Acquisition relationship:

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

### Rules

```text
Do not confuse geographic location with marketing source.
Do not use precise addresses.
Do not use real personal location data.
Do not use form answers to claim revenue attribution unless approved later.
Every form answer must join through a valid opt_in.
```

---

## 15. Opt-In Enrichment Rules

The demo should include rich but safe form answers so the client can ask natural questions.

Use these questions:

```text
What do you do for work?
What is your employment status?
Which country are you from?
Which city or region are you based in?
What is your main goal?
What is your biggest challenge right now?
How soon do you want to get started?
What is your current experience level?
What budget range are you comfortable with?
Are you the final decision maker?
```

### Controlled Profession / Industry Answers

```text
Business Owner
Employee
Self-employed
Student
Trader / Investor
Sales or Marketing
Technology
Healthcare
Retired
Unemployed
```

### Controlled Employment Status Answers

```text
Full-time
Part-time
Self-employed
Student
Business Owner
Unemployed
Retired
```

### Controlled Country / Region Answers

```text
Netherlands
Belgium
Germany
United Kingdom
Spain
France
Dubai
Amsterdam
Rotterdam
Brussels
Berlin
London
Barcelona
```

### Controlled Goal Answers

```text
Grow income
Start online business
Improve trading skills
Change career
Build side income
Get financial confidence
```

### Controlled Challenge Answers

```text
No clear plan
Lack of time
Budget concern
Needs partner approval
Not confident yet
Needs more information
```

### Controlled Start Timeline Answers

```text
Immediately
This month
In 1-3 months
Later this year
Not sure yet
```

### Controlled Budget Range Answers

```text
Below €1,000
€1,000-€2,500
€2,500-€5,000
Above €5,000
Not sure yet
```

### Controlled Decision-Maker Answers

```text
Yes, I decide myself
I need partner approval
I need team approval
I need finance approval
Not sure yet
```

### Expected Supported Questions

```text
Which profession submitted the most opt-ins?
Which country generated the most submissions?
Which city or region generated the most submissions?
What are the most common challenges?
How many leads are ready to start immediately?
How many leads need partner approval?
Which budget range is most common?
Show opt-ins by current lead status.
Show form answer distribution for budget range.
Show form answer distribution for profession.
```

### Important Limitation

Allowed:

```text
Opt-ins by profession
Opt-ins by country
Opt-ins by budget range
Opt-ins by decision-maker status
Current lead status by form answer
```

Avoid unless later explicitly supported:

```text
Revenue by profession
Revenue by country
Revenue by budget range
Revenue by form answer
Revenue by UTM campaign
Revenue by landing page
```

---

## 16. Appointment Relationship Rules

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

### Rules

```text
Appointment date must be after lead.created_at.
Most appointments should happen 1 to 14 days after lead creation.
Future appointments should not have Fathom records.
No-show appointments should have no_show = true.
Canceled appointments should use CANCELED outcome status.
Rescheduled appointments should use RESCHEDULED outcome status.
Completed appointments should have no_show = false and non-canceled/non-rescheduled outcome.
```

---

## 17. Fathom Relationship Rules

Fathom relationship:

```text
completed appointment -> exactly one fathom_call_record
```

This is a fixed demo rule for this project.

| Appointment scenario | Fathom record? | Reason |
|---|---:|---|
| Completed / attended sales call | Yes | Looks complete and useful |
| No-show | No | No call happened |
| Canceled | No | Call did not happen |
| Rescheduled | No | Original call did not complete |
| Future appointment | No | Call has not happened yet |
| Attended but missing Fathom | Avoid | Looks like integration issue |

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

### Rules

```text
Do not create Fathom records for no-show appointments.
Do not create Fathom records for canceled appointments.
Do not create Fathom records for rescheduled appointments.
Do not create Fathom records for future appointments.
Do not create Fathom records without a valid appointment.
Do not create more than one Fathom record per completed appointment for this demo.
Do not create a completed appointment without a Fathom record.
```

---

## 18. Fathom Story Mapping

Assign Fathom story templates based on lead scenario.

| Lead scenario | Fathom story type |
|---|---|
| Paid / converted | converted_strong_intent or converted_after_payment_plan |
| Completed call but not signed | completed_not_signed_partner_approval, completed_not_signed_budget, or completed_not_signed_needs_more_time |
| Signed but not paid | signed_not_paid_payment_link_issue or signed_not_paid_payment_timing |
| Lost | lost_low_intent |
| Unqualified | unqualified_poor_fit |
| Follow-up pending | follow_up_needs_more_information |

### Rules

```text
Fathom summaries should sound like real business call notes.
Do not use placeholder text.
Do not expose private data.
Objections should align with the lead scenario.
Action items should be practical and easy to understand.
The summary should help the chatbot explain why a lead converted, did not sign, did not pay, or needs follow-up.
```

---

## 19. Contract Relationship Rules

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

### Rules

```text
Signed contracts must have signed_at.
Sent/viewed contracts should have sent_at and optionally viewed_at.
Voided contracts should have voided_at.
Do not create paid payments for unsigned contracts.
Do not create contracts for unqualified leads unless intentionally testing edge cases; avoid for client demo.
Contract total_value should use the schema's expected money unit.
If source table expects minor units, use minor units.
```

---

## 20. Payment Relationship Rules

Payment relationship:

```text
contract -> payment
lead -> payment
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
| Lead only / never booked | No payment |
| Booked but not completed | No payment |

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

### Rules

```text
Use EUR only.
Source payment amount should use the schema's expected unit.
If amount is stored as minor units, use values like 250000 for €2,500.
Paid payments should have paid_at.
Pending payments should have due_date.
Failed payments can have due_date and failed-like status.
Do not create payment before contract signed.
Do not create payment for unqualified leads.
Do not create payment for lead-only/no-booked-call leads.
Do not create payment for no-show/canceled/rescheduled-only leads.
```

---

## 21. Refund Relationship Rules

Refund relationship:

```text
paid payment -> refund
```

Target:

```text
10 to 15 refund cases
```

### Rules

```text
Refunds must connect to valid paid payments.
Refund date must be after payment paid_at.
Refund amount must not exceed original payment amount.
Use status SUCCEEDED for normal demo refunds.
Use FAILED or INITIATED only if needed for refund status demo later.
Do not create refunds for pending or failed payments.
Do not create refunds for leads that never paid.
```

---

## 22. Invoice, Payment Link, and Payment Proof Rules

For the first client demo, these tables are optional and should not be seeded by default.

Do not seed:

```text
invoices
payment_links
payment_proofs
```

### Reason

```text
The first demo should avoid operational/admin noise such as missing invoices, invalid payment links, or payment proof issues.
```

### Optional Later Behavior

If required in a later demo version:

```text
Invoices:
- Add only if invoice-specific demo questions are required.
- Connect invoices to valid payments.

Payment links:
- Add only if payment-link demo questions are required.
- Do not create fake real-looking URLs.
- Do not expose payment URLs in the demo.

Payment proofs:
- Add only if manual-payment proof questions are required.
- Do not create real file keys or upload references.
```

---

## 23. Subscription Rules

Skip subscription data for the first client demo.

Do not seed:

```text
contract_subscriptions
subscription_checkout_links
```

### Reason

```text
The first demo is focused on lead funnel, appointments, Fathom calls, contracts, payments, refunds, and diagnostics.
Subscription/MRR questions can be added in a later demo version if required.
```

---

## 24. Unmatched Payment Rules

Skip unmatched payments for the first client demo.

Do not seed:

```text
unmatched_payments
```

### Reason

```text
Unmatched payments are more of an operational reconciliation workflow.
They are not required for the first client-facing funnel and revenue demo.
```

---

## 25. Diagnostic Text Insights Relationship Rules

If `diagnostic_text_insights` is seeded directly, generate insights from the lead scenario and Fathom/payment/contract/opt-in story.

Relationship:

```text
lead -> diagnostic_text_insights
source record can be fathom_call_records, payments, contracts, or opt_in_question_answers
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

Avoid overusing:

```text
unknown
```

### Scenario Mapping

| Scenario | Reason category | Reason subcategory |
|---|---|---|
| Completed call but not signed | timing_issue | needs_more_time |
| Completed call but not signed | needs_partner_approval | waiting_for_partner |
| Completed call but not signed | price_or_budget | budget_not_available |
| Signed but not paid | payment_friction | payment_not_completed |
| Signed but not paid | payment_friction | system_or_link_issue |
| Booked but not completed | no_show | missed_call |
| Booked but not completed | no_show | cancelled_call |
| Lost | low_intent | not_ready_now |
| Unqualified | poor_fit | wrong_customer_fit |
| Follow-up pending | follow_up_pending | needs_more_information |

### Rules

```text
Do not call LLM during seed unless intentionally running an extraction job.
If seeded deterministically, align reason_category with lead scenario.
Do not store sensitive text.
Do not create raw transcripts.
```

---

## 26. Diagnostic Lead Snapshot Rules

Do not insert `diagnostic_lead_snapshot` manually as the main approach.

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

### Important Money Rule

```text
Source contract/payment/refund tables may store money in minor units.
diagnostic_lead_snapshot money fields should be major-unit EUR after snapshot build.
Do not divide diagnostic money fields by 100 again.
```

---

## 27. Date Sequencing Rules

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
canceled appointment with Fathom
rescheduled appointment with Fathom
completed appointment without Fathom
```

### Suggested Date Offsets

```text
opt_in.created_at = lead.created_at or within 0 to 2 days
appointment.schedule_time = lead.created_at + 1 to 14 days
fathom.call_started_at = appointment.schedule_time + 0 to 5 minutes
fathom.call_ended_at = call_started_at + call_duration_seconds
contract.sent_at = completed call time + 0 to 3 days
contract.viewed_at = sent_at + 0 to 2 days
contract.signed_at = viewed_at + 0 to 5 days
payment.due_date = signed_at or signed_at + 1 to 7 days
payment.paid_at = signed_at + 0 to 7 days for paid customers
refund.created_at = payment.paid_at + 7 to 45 days
```

---

## 28. Cleanup Strategy for Dummy Org

The seed script should support a safe force rebuild for only the dummy org.

### Required Behavior

```text
Require explicit org_id argument.
Require org_id = org_dummy_client_demo_001 unless explicitly overridden in local-only mode.
Refuse to run if org_id is empty.
Refuse to run if org_id matches known live org ID.
Delete only rows for org_dummy_client_demo_001.
Delete child rows before parent rows.
Never truncate full tables.
Never delete rows without org filtering.
```

### Cleanup Order

For the first demo scope, cleanup should happen in reverse dependency order.

Suggested cleanup order:

```text
1. diagnostic_lead_snapshot where clerk_org_id = org_dummy_client_demo_001
2. diagnostic_text_insights where clerk_org_id = org_dummy_client_demo_001
3. refunds where clerk_org_id = org_dummy_client_demo_001
4. payments where clerk_org_id = org_dummy_client_demo_001
5. contracts where clerk_org_id = org_dummy_client_demo_001
6. fathom_call_records where clerk_org_id = org_dummy_client_demo_001
7. appointments where clerk_org_id = org_dummy_client_demo_001
8. opt_in_question_answers by joining to opt_ins for org_dummy_client_demo_001
9. traffic_attributions by joining to opt_ins for org_dummy_client_demo_001
10. opt_ins where clerk_org_id = org_dummy_client_demo_001
11. leads where clerk_org_id = org_dummy_client_demo_001
12. appointment_event_types where clerk_org_id = org_dummy_client_demo_001
13. programs where clerk_org_id = org_dummy_client_demo_001
14. marketing_sources where clerk_org_id = org_dummy_client_demo_001
15. sales_statuses where clerk_org_id = org_dummy_client_demo_001
```

Important:

```text
Some child tables may not have clerk_org_id directly.
For child tables without clerk_org_id, delete through parent joins only.
```

---

## 29. Validation Requirements

After seeding, run validation checks.

### 29.1 Organization Safety

```text
All inserted rows use org_dummy_client_demo_001.
No rows are inserted into live client org.
No cleanup affects live client org.
```

### 29.2 Source Validation

```text
No lead has missing first_source_id.
No lead has missing last_source_id.
No lead has blank first_source_name or last_source_name.
No source name is Unknown.
All first_source_id and last_source_id join to marketing_sources.
No revenue exists without a valid source.
```

### 29.3 Lead Validation

```text
Total active dummy leads = 500.
Monthly lead distribution matches the blueprint.
Lead source distribution matches the blueprint.
Every lead has a valid status_id.
Every lead has fake email and fake phone only.
No deleted leads are included in main demo counts.
```

### 29.4 Acquisition Validation

```text
Every opt-in joins to a valid lead.
Most leads have at least one opt-in.
Total opt-ins are around 650.
Traffic attribution rows join to valid opt-ins.
Form answer rows join to valid opt-ins.
Profession answers exist for most opt-ins.
Employment-status answers exist for most opt-ins.
Country or region answers exist for most opt-ins.
Goal answers exist for most opt-ins.
Challenge answers exist for most opt-ins.
Budget range answers exist for most opt-ins.
Decision-maker answers exist for most opt-ins.
No precise addresses are generated.
No real personal location data is used.
No revenue attribution is claimed from form answers unless explicitly supported later.
```

### 29.5 Appointment and Fathom Validation

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

### 29.6 Revenue Validation

```text
Every contract joins to a valid lead and program.
Every paid payment joins to a valid lead and signed contract.
Every refund joins to a valid paid payment.
Refund amount does not exceed original paid amount.
Paid leads have paid payments.
Signed-not-paid leads have pending or failed payments.
Unqualified leads do not have payments.
Lead-only / never-booked leads do not have payments.
Booked-but-not-completed leads do not have payments.
```

### 29.7 Optional Table Validation

For first demo, these tables should have no seeded rows unless explicitly enabled:

```text
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
```

### 29.8 Business Story Validation

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

### 29.9 Diagnostic Validation

```text
diagnostic_lead_snapshot row count = active dummy lead count.
No unknown source quality flags.
No missing source quality flags.
completed_calls_missing_fathom_count = 0.
completed_call_fathom_coverage_rate = 100.00.
Diagnostic money values are in major-unit EUR.
```

---

## 30. Expected Demo Questions Supported

The final seeded data should support questions like:

```text
How many leads do we have?
Show monthly lead trend.
Which source generated the most leads?
Which source generated the most revenue?
Show revenue by source.
Show signed contract value by source.
Show appointment count by source.
Show no-show rate by source.
Show Fathom coverage.
Show recent Fathom call summaries.
Which calls had objections?
What are the common call objections?
Where are we losing leads in the funnel?
Why are leads not converting?
Which source has high volume but weak conversion?
What should sales focus on?
Which profession submitted the most opt-ins?
Which country generated the most submissions?
What are the most common form challenges?
How many leads need partner approval?
```

Avoid promising these unless later explicitly supported:

```text
Revenue by UTM campaign
Revenue by landing page
Revenue by profession
Revenue by country
Revenue by form answer
Ad spend
ROAS
Cost per lead
Cost per sale
```

---

## 31. Step 2 Completion Criteria

Step 2 is complete when this document is reviewed and approved.

Checklist:

```text
First-demo required table scope is finalized.
Optional revenue/admin tables are clearly skipped.
Insert order is finalized.
Reference table values are finalized.
ID map strategy is finalized.
Lead scenario mapping is finalized.
Source distribution relationship is finalized.
Acquisition relationship rules are finalized.
Opt-in enrichment rules are finalized.
Appointment/Fathom relationship rules are finalized.
Revenue relationship rules are finalized.
Diagnostic text and snapshot rules are finalized.
Date sequencing rules are finalized.
Cleanup strategy is defined.
Validation checks are defined.
```

---

## 32. Next Step Hint

Step 3 should be the Codex implementation instruction.

Step 3 should ask Codex to create a deterministic Python seed script that:

```text
connects to Postgres
accepts org_dummy_client_demo_001
optionally force-cleans only dummy org data
seeds required parent and child tables in the correct order
skips invoices, payment links, payment proofs, subscriptions, and unmatched payments for the first demo
creates realistic scenario-based records
generates 100% Fathom coverage for completed calls
runs validation checks
builds diagnostic_lead_snapshot after base data
prints a final row-count and validation report
```

Do not start Step 3 until this Step 2 relationship map is approved.
