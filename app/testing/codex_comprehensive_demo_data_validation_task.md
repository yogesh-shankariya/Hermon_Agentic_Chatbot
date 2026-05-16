# Codex Task — Create Comprehensive Demo Data Validation Script

## Goal

Create a separate read-only validation script to verify the seeded dummy/demo dataset end-to-end before sharing the Streamlit link.

This validation must be independent from the seed script.

The seed script has already inserted the dummy data successfully, but this task is to create a stronger post-seed validation layer that checks:

```text
data safety
row counts
relationships
date sequence
money/revenue consistency
appointment/Fathom consistency
diagnostic snapshot consistency
diagnostic text insight consistency
supported chatbot question consistency
optional table leakage
client-facing data quality
```

Failing to validate this properly can cause serious client-demo embarrassment, so this script must be strict.

---

## Script to Create

Create:

```text
scripts/validate_demo_data.py
```

This script must be read-only.

It must not insert, update, delete, truncate, create, alter, or clean anything.

---

## Required Command

The script should run like this:

```bash
python scripts/validate_demo_data.py --org-id org_dummy_client_demo_001
```

Optional flags:

```bash
python scripts/validate_demo_data.py --org-id org_dummy_client_demo_001 --verbose
python scripts/validate_demo_data.py --org-id org_dummy_client_demo_001 --export-json artifacts/demo_data_validation_report.json
```

---

## Safety Rules

The validation script must:

```text
Require --org-id.
Allow only org_dummy_client_demo_001 by default.
Refuse empty org ID.
Refuse known live client org IDs.
Use read-only SELECT queries only.
Never modify data.
Never print database URL.
Never print secrets.
Never print raw payloads.
Never print access codes.
Never expose meeting/payment/Fathom links.
```

Add constants:

```python
DUMMY_ORG_ID = "org_dummy_client_demo_001"
BLOCKED_ORG_IDS = {
    "<actual live client org id>"
}
```

If the live org ID is not configured, print a warning, but since this is read-only validation it can still run for the dummy org only.

---

## Validation Result Format

Create a common result structure:

```python
@dataclass
class ValidationCheck:
    name: str
    severity: str  # "critical", "high", "medium", "info"
    passed: bool
    expected: str
    actual: str
    details: str | None = None
```

At the end, print a readable summary:

```text
Demo data validation completed.

Overall status: PASSED / FAILED

Summary:
- critical: 0 failed / X checked
- high: 0 failed / X checked
- medium: 0 failed / X checked
- info: X checked

Failed checks:
- <check name>: <details>
```

Exit codes:

```text
0 = all critical and high checks passed
1 = any critical or high check failed
```

Medium/info failures can be printed but should not fail the process unless explicitly configured.

---

## 1. Organization and Scope Validation

Validate:

```text
All required tables have rows only for org_dummy_client_demo_001 when checking demo dataset.
No seeded dummy records exist under any other org.
No required table has zero rows.
No optional/admin tables were seeded for the dummy org.
```

Required first-demo tables:

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

Optional tables that should be zero for dummy org:

```text
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
```

Admin/raw tables should not be seeded for dummy org:

```text
provider_integrations
provider_credentials
webhook_events
integration_health_checks
audit_logs
notification_logs
```

If a table does not exist in the current schema, skip with info-level message only if it is optional/admin. Required tables must exist.

---

## 2. Expected Row Count Validation

Validate exact or expected row counts.

Expected exact counts:

```text
sales_statuses = 10
marketing_sources = 10
programs = 5
appointment_event_types = 5
leads = 500
opt_ins = 650
traffic_attributions = 650
opt_in_question_answers = 6500
appointments = 445
fathom_call_records = 285
contracts = 178
payments = 190
refunds = 12
diagnostic_text_insights = 405
diagnostic_lead_snapshot = 500
```

These are critical checks for the current first demo.

If the dataset is intentionally regenerated with different counts later, update the expected constants in one place.

---

## 3. Monthly Trend Validation

Validate lead creation distribution:

```text
2025-11 = 55
2025-12 = 70
2026-01 = 95
2026-02 = 82
2026-03 = 90
2026-04 = 108
```

Also validate:

```text
No lead.created_at before 2025-11-01.
No lead.created_at after 2026-04-30 23:59:59.
Monthly trend is not flat.
Jan 2026 > Dec 2025.
Feb 2026 < Jan 2026.
Mar 2026 >= Feb 2026.
Apr 2026 > Mar 2026.
```

---

## 4. Source Distribution and Source Quality Validation

Validate source distribution:

```text
Facebook = 90
Instagram = 60
YouTube = 65
Google Search = 70
Webinar = 60
Referral = 40
Email Campaign = 35
Calendly = 30
Landing Page = 30
Organic Search = 20
```

Validate:

```text
No first_source_name is null/blank.
No last_source_name is null/blank.
No source name is Unknown.
No source name is Not Set, N/A, Blank, No Source, Other Unknown.
Every first_source_id joins to marketing_sources.
Every last_source_id joins to marketing_sources.
No orphaned first_source_id.
No orphaned last_source_id.
No revenue exists without valid source.
```

Also validate `diagnostic_lead_snapshot` source quality:

```text
has_missing_first_source = false for all rows
has_missing_last_source = false for all rows
has_orphaned_first_source_id = false for all rows
has_orphaned_last_source_id = false for all rows
has_unknown_source = false for all rows
has_revenue_without_source = false for all rows
source_confidence should be high or medium only
```

Medium source confidence is acceptable only when first source and last source differ.

---

## 5. Lead Scenario and Funnel Validation

Validate scenario counts using current status + activity behavior.

Expected scenario counts:

```text
paid_converted = 110
completed_not_signed = 150
booked_not_completed = 90
lead_only = 75
signed_not_paid = 25
lost = 30
unqualified = 20
```

Validate funnel snapshot counts:

```text
diagnostic_lead_snapshot.funnel_stage counts should match intended business story.
There must be leads in each expected funnel stage.
Paid/converted leads should have net_collected_amount > 0.
Completed-not-signed leads should have completed_call_count > 0 and signed_contract_count = 0.
Signed-not-paid leads should have signed_contract_count > 0 and paid_payment_count = 0.
Booked-not-completed leads should have appointment_count > 0 and completed_call_count = 0.
Lead-only leads should have appointment_count = 0.
Lost leads should have current_status_role = LOST or funnel_stage = lost.
Unqualified leads should have current_status_role = UNQUALIFIED or funnel_stage = unqualified.
```

---

## 6. Relationship Integrity Validation

Validate all joins.

Required checks:

```text
Every lead.status_id joins to sales_statuses.
Every lead.first_source_id joins to marketing_sources.
Every lead.last_source_id joins to marketing_sources.
Every opt_in.lead_id joins to leads.
Every traffic_attribution.opt_in_id joins to opt_ins.
Every opt_in_question_answer.opt_in_id joins to opt_ins.
Every appointment.lead_id joins to leads.
Every appointment.appointment_event_type_id joins to appointment_event_types.
Every appointment.outcome_id joins to sales_statuses when outcome_id is not null.
Every fathom_call_record.appointment_id joins to appointments.
Every contract.lead_id joins to leads.
Every contract.program_id joins to programs.
Every payment.lead_id joins to leads.
Every payment.contract_id joins to contracts when contract_id is not null.
Every refund.payment_id joins to payments.
Every diagnostic_text_insight.lead_id joins to leads.
Every diagnostic_lead_snapshot.lead_id joins to leads.
```

Also validate cross-org safety:

```text
Child row org must match parent row org wherever both sides have clerk_org_id.
```

Examples:

```text
appointments.clerk_org_id = leads.clerk_org_id
fathom_call_records.clerk_org_id = appointments.clerk_org_id
contracts.clerk_org_id = leads.clerk_org_id
payments.clerk_org_id = leads.clerk_org_id
payments.clerk_org_id = contracts.clerk_org_id
refunds.clerk_org_id = payments.clerk_org_id
```

---

## 7. Date Sequence Validation

This is critical.

Validate the journey timeline order.

### Lead and Opt-In

```text
opt_ins.created_at >= leads.created_at
traffic_attributions.created_at >= opt_ins.created_at
opt_in_question_answers.created_at >= opt_ins.created_at
```

### Appointment

```text
appointments.schedule_time >= leads.created_at
appointments.created_at >= leads.created_at
future appointments have schedule_time > now()
past appointments have schedule_time < now()
```

### Fathom

For Fathom-linked appointments:

```text
fathom_call_records.call_started_at >= appointments.schedule_time
fathom_call_records.call_ended_at > fathom_call_records.call_started_at
fathom_call_records.created_at >= fathom_call_records.call_started_at
call_duration_seconds > 0
call_duration_seconds = approximately call_ended_at - call_started_at
```

Allow a small tolerance of 60 seconds for duration calculation.

### Contract

For signed/sent/viewed/voided contracts:

```text
contracts.created_at >= leads.created_at
contracts.sent_at >= latest completed Fathom call time when lead has completed call
contracts.signed_at >= contracts.sent_at when signed_at is not null
contracts.voided_at >= contracts.sent_at when voided_at is not null
signed contracts must have signed_at
sent/viewed contracts must have sent_at
voided contracts must have voided_at
```

### Payment

```text
payments.created_at >= contracts.created_at
payments.due_date >= contracts.signed_at for signed contracts
payments.paid_at >= contracts.signed_at for paid payments
paid payments must have paid_at
pending payments must have due_date
failed payments must have due_date or failure_reason
```

### Refund

```text
refunds.created_at >= payments.paid_at
refunds.refunded_at >= payments.paid_at when refunded_at is not null
refunds.amount <= payments.amount
refunds only connect to PAID or REFUNDED payments
```

### No Impossible Timelines

Fail if any of these exist:

```text
appointment before lead
Fathom before appointment
Fathom ended before started
contract before completed call for completed-call scenarios
signed contract before sent contract
payment before contract signed
refund before payment
future appointment with Fathom
no-show appointment with Fathom
canceled appointment with Fathom
rescheduled appointment with Fathom
completed appointment without Fathom
```

---

## 8. Appointment and Fathom Validation

Validate strict Fathom rule:

```text
Every completed/attended past appointment has exactly one Fathom record.
No completed appointment has zero Fathom records.
No completed appointment has more than one Fathom record.
No no-show appointment has Fathom record.
No canceled appointment has Fathom record.
No rescheduled appointment has Fathom record.
No future appointment has Fathom record.
No deleted appointment has Fathom record.
```

Validate expected counts:

```text
completed appointments = 285
fathom_call_records = 285
completed appointments missing Fathom = 0
Fathom records for no-show/canceled/rescheduled/future appointments = 0
```

Validate Fathom content:

```text
summary is not null/blank
key_points is valid JSON array and not empty
action_items is valid JSON array and not empty
objections is valid JSON array
ai_generated_title is not null/blank
ai_confidence_score between 0 and 1
call_duration_seconds within reasonable range
raw_payload is null
recording_url is null
transcript_url is null
```

Recommended duration range:

```text
10 minutes <= call_duration_seconds <= 75 minutes
```

---

## 9. Contract Validation

Validate:

```text
Every contract has valid lead_id and program_id.
Every contract currency = EUR.
Every contract total_value > 0.
Every signed contract has signed_at.
Every sent/viewed contract has sent_at.
Every voided contract has voided_at.
No unqualified lead has contract.
No lead-only lead has contract.
No booked-not-completed lead has contract.
Paid leads have signed contracts.
Signed-not-paid leads have signed contracts.
Completed-not-signed leads may have sent/viewed contracts but no signed contract.
```

Validate contract totals:

```text
Signed contract value from contracts should equal expected sum by signed contracts.
Signed contract value by program should sum to total signed contract value.
Signed contract value by source should sum to total signed contract value.
Monthly signed contract value should sum to total signed contract value for same signed_at date range.
```

Important:

```text
Use contracts.signed_at for contract signed-date revenue/value checks.
Use total_value in minor units.
Convert to EUR major units only for reporting.
```

---

## 10. Payment and Revenue Validation

Use payments as the source of collected revenue.

Use:

```text
paid revenue = SUM(payments.amount) WHERE status = 'PAID'
pending amount = SUM(payments.amount) WHERE status = 'PENDING'
failed amount = SUM(payments.amount) WHERE status = 'FAILED'
gross paid revenue = paid revenue
net collected revenue = paid revenue - succeeded refunds
```

Validate:

```text
Every payment has valid lead_id.
Every payment has valid contract_id where contract_id is required.
Every payment currency = EUR.
Every payment amount > 0.
Paid payments have paid_at.
Pending payments have due_date.
Failed payments have due_date or failure_reason.
Paid / converted leads have at least one PAID payment.
Signed-but-not-paid leads have PENDING or FAILED payment.
Completed-not-signed leads have no PAID payment.
Lead-only leads have no payment.
Booked-not-completed leads have no payment.
Unqualified leads have no payment.
```

### Revenue Reconciliation Checks

Run all of these and compare.

For the full dataset:

```text
total_gross_paid_revenue = SUM(PAID payments.amount)
total_succeeded_refunds = SUM(SUCCEEDED refunds.amount)
total_net_collected_revenue = total_gross_paid_revenue - total_succeeded_refunds
```

Then validate:

```text
SUM(daily gross paid revenue by paid_at) = total_gross_paid_revenue
SUM(weekly gross paid revenue by paid_at) = total_gross_paid_revenue
SUM(monthly gross paid revenue by paid_at) = total_gross_paid_revenue

SUM(daily succeeded refunds by refunded_at) = total_succeeded_refunds
SUM(weekly succeeded refunds by refunded_at) = total_succeeded_refunds
SUM(monthly succeeded refunds by refunded_at) = total_succeeded_refunds

SUM(daily net revenue) = total_net_collected_revenue
SUM(weekly net revenue) = total_net_collected_revenue
SUM(monthly net revenue) = total_net_collected_revenue
```

Important:

```text
Daily/weekly/monthly totals must use the exact same date window and date field.
Use paid_at for paid payments.
Use refunded_at for refunds, fallback to created_at only if refunded_at is null.
Use half-open intervals: start_date inclusive, end_date exclusive.
```

### Revenue Breakdown Reconciliation

Validate:

```text
SUM(revenue by source) = total_gross_paid_revenue
SUM(net revenue by source) = total_net_collected_revenue
SUM(revenue by program) = total_gross_paid_revenue
SUM(revenue by payment_provider) = total_gross_paid_revenue
SUM(revenue by payment_type) = total_gross_paid_revenue
SUM(payment status amounts by status) = total payment amount across all statuses
```

Allow small tolerance:

```text
tolerance_minor_units = 1
```

because of rounding only if any calculation converts units.

Prefer comparing in minor units to avoid rounding.

---

## 11. Refund Validation

Validate:

```text
Refunds connect to valid payments.
Refunds connect only to paid/refunded payments.
Refund amount > 0.
Refund amount <= original payment amount.
Refund currency = payment currency.
Refund payment_provider = payment payment_provider.
SUCCEEDED refunds have refunded_at.
Refund date is after payment paid_at.
Total succeeded refund amount equals sum of refunds by source/program/month.
```

---

## 12. Diagnostic Snapshot Validation

Validate snapshot row count:

```text
diagnostic_lead_snapshot rows = active leads = 500
```

Validate snapshot field consistency against base tables:

```text
snapshot.opt_in_count = count(opt_ins) per lead
snapshot.appointment_count = count(appointments) per lead
snapshot.completed_call_count = completed appointment count per lead
snapshot.fathom_record_count = count(fathom_call_records) per lead
snapshot.contract_count = count(contracts) per lead
snapshot.payment_count = count(payments) per lead
snapshot.gross_paid_amount = paid payments amount / 100 per lead
snapshot.refund_amount = succeeded refunds amount / 100 per lead
snapshot.net_collected_amount = gross_paid_amount - refund_amount
snapshot.signed_contract_value = signed contracts total_value / 100
```

Validate diagnostic quality:

```text
completed_calls_missing_fathom_count = 0
completed_call_fathom_coverage_rate = 100.00 for leads with completed calls
has_unknown_source = false
has_missing_first_source = false
has_missing_last_source = false
has_orphaned_first_source_id = false
has_orphaned_last_source_id = false
has_revenue_without_source = false
has_payment_without_contract = false
```

Important:

```text
diagnostic_lead_snapshot money fields are already major-unit EUR.
Do not divide diagnostic money fields by 100 again.
```

---

## 13. Diagnostic Text Insight Validation

Validate:

```text
diagnostic_text_insights count = 405
Every row joins to a valid lead.
Every row has valid clerk_org_id.
Every Fathom-derived row joins to a valid Fathom record.
Every Fathom-derived row has source_event_at = fathom_call_records.call_started_at.
source_text_hash is not null/blank.
source_text_length > 0.
extraction_status = success.
reason_category is allowed enum value.
reason_subcategory is allowed enum value.
buying_intent_level is allowed enum value.
lead_quality_level is allowed enum value.
profession_category is allowed enum value.
employment_status is allowed enum value.
```

Validate scenario consistency:

```text
completed_not_signed insights should mostly be timing_issue, needs_partner_approval, price_or_budget, or needs_more_information.
signed_not_paid insights should be payment_friction.
booked_not_completed insights should be no_show.
lost insights should be low_intent or ghosted.
unqualified insights should be poor_fit.
```

Do not require zero `unknown`, but fail if unknown is unexpectedly high for demo data.

Suggested threshold:

```text
reason_category = unknown should be less than 5% for demo data
```

---

## 14. Acquisition and Form Answer Validation

Validate:

```text
Every lead has at least one opt-in unless intentionally allowed.
Every opt-in has traffic attribution.
Every opt-in has exactly 10 form answers.
No form question is blank.
No form answer is blank.
Every expected question exists across the dataset.
Profession answers exist for most opt-ins.
Employment-status answers exist for most opt-ins.
Country or region answers exist for most opt-ins.
Goal answers exist for most opt-ins.
Challenge answers exist for most opt-ins.
Budget range answers exist for most opt-ins.
Decision-maker answers exist for most opt-ins.
No precise address-like values.
No postal codes.
No real-looking street addresses.
```

Expected questions:

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

---

## 15. Safe Data / Privacy Validation

Validate no unsafe data is present.

Fail if any of these are non-null/non-empty where not expected:

```text
opt_ins.raw_payload
opt_ins.ip_address
opt_ins.user_agent
appointments.meeting_url
appointments.recording_url
fathom_call_records.raw_payload
fathom_call_records.recording_url
fathom_call_records.transcript_url
payments.external_payment_id
refunds.external_refund_id
```

Validate synthetic identity:

```text
lead emails end with @example.com
lead phone numbers follow the synthetic pattern
no lead email uses real domains
no obvious real names from live client are present if a denylist is provided
```

Optional input:

```bash
--denylist-file artifacts/live_client_denylist.txt
```

If provided, check that none of the denylist strings appear in dummy lead names, emails, notes, Fathom summaries, contract notes, payment notes, or diagnostic text insights.

---

## 16. Supported Chatbot Metric Reconciliation

Validate that common chatbot metrics reconcile to base data.

### Lead Analytics Checks

```text
Total leads = 500.
Lead count by source sums to 500.
Lead count by status sums to 500.
Monthly lead trend sums to 500.
```

### Appointment Analytics Checks

```text
Appointment count by source sums to total appointments.
Appointment count by event type sums to total appointments.
No-show count by source sums to total no-shows.
Completed call count equals Fathom record count.
Average call duration uses only Fathom records.
```

### Acquisition Analytics Checks

```text
Opt-ins by provider form sums to total opt-ins.
Opt-ins by UTM campaign sums to total traffic attribution rows.
Form answer distribution for each expected question sums to total answers for that question.
Opt-ins by current lead status joins through leads correctly.
```

### Revenue Analytics Checks

```text
Revenue by source sums to total paid revenue.
Net revenue by source sums to total net revenue.
Signed contract value by source sums to total signed contract value.
Payment count by status sums to total payments.
Refund amount by source sums to total refund amount.
```

### Diagnostic Analytics Checks

```text
Diagnostic snapshot lead count = active leads.
Diagnostic funnel buckets sum to snapshot rows.
Diagnostic source snapshot lead counts sum to snapshot rows.
Diagnostic source quality issue count is zero or expected.
```

---

## 17. Unsupported Metric Guardrail Validation

Validate that the dataset does not accidentally imply unsupported claims.

The validation script should print warnings, not failures, for these:

```text
Revenue by UTM campaign is not supported unless explicit attribution rule is added.
Revenue by landing page is not supported unless explicit attribution rule is added.
Revenue by form answer is not supported unless explicit attribution rule is added.
ROAS/ad spend/cost per lead are not available.
```

This is a reminder for demo testing, not a database failure.

---

## 18. Output Artifacts

If `--export-json` is passed, write:

```text
artifacts/demo_data_validation_report.json
```

JSON should include:

```text
org_id
started_at
finished_at
duration_seconds
overall_status
checks
failed_checks
row_counts
money_totals_minor
money_totals_eur
```

Do not include secrets or raw data samples.

---

## 19. Manual Acceptance Criteria

The validation script is accepted only when:

```text
All critical checks pass.
All high checks pass.
Revenue reconciliation passes.
Daily/weekly/monthly revenue totals reconcile.
Date sequence checks pass.
Relationship integrity checks pass.
Fathom coverage checks pass.
Diagnostic snapshot matches base tables.
Diagnostic text insights match Fathom/source records.
Optional/admin tables remain empty.
No unsafe raw payloads or URLs are present.
```

---

## 20. Recommended Demo Validation Run Order

After creating the script, run:

```bash
python scripts/validate_demo_data.py --org-id org_dummy_client_demo_001 --verbose --export-json artifacts/demo_data_validation_report.json
```

If it passes, then test the Streamlit chatbot with supported questions.

Do not share the Streamlit link until this validation passes.

---

## 21. Important Notes

The diagnostic snapshot uses lead-created-at cohort logic. It is not true payment-period revenue.

So validate two separate things:

```text
1. Source table revenue by payments.paid_at and refunds.refunded_at.
2. Diagnostic snapshot money fields as lead-cohort lifetime outcome values.
```

Do not compare payment-period monthly revenue directly against diagnostic cohort revenue unless the date logic is intentionally aligned.

For strict revenue reconciliation, use source tables:

```text
payments
refunds
contracts
```

For diagnostic chatbot validation, use:

```text
diagnostic_lead_snapshot
```
