# Step 3 — Codex Instruction to Create Dummy Demo Seed Script

## Purpose

This document is the implementation instruction for Codex.

Codex must create a deterministic Python seed script for the dummy/client-demo dataset.

Codex must read and follow:

```text
demo_data_step1_blueprint.md
demo_data_step2_relationship_map_rewritten.md
```

These two documents are the source of truth for:

```text
business story
dummy org ID
table scope
insert order
source distribution
monthly trend
lead scenario mapping
appointment/Fathom rules
contract/payment/refund rules
diagnostic snapshot rules
validation rules
```

This Step 3 document tells Codex how to implement the seed script safely.

---

## 1. Main Goal

Create a Python script that seeds realistic dummy data for the first client demo.

Script path:

```text
scripts/seed_demo_data.py
```

The script must generate data for this dummy organization only:

```text
org_dummy_client_demo_001
```

The script must not insert, update, delete, or modify any live client organization data.

The script must not run automatically after creation.

Codex should only create the script and supporting code. Do not execute the seed script against the database until the script is reviewed in Step 4.

---

## 2. Required Behavior Summary

The script must:

```text
1. Connect to Postgres/Supabase using the existing project database configuration.
2. Accept org ID from CLI argument.
3. Allow only org_dummy_client_demo_001 by default.
4. Refuse to run if org ID is empty.
5. Refuse to run if org ID matches a known live client org ID.
6. Support --dry-run.
7. Support --force for safe rebuild of only dummy org data.
8. Clean only dummy org data when --force is passed.
9. Seed required tables in the correct Step 2 insert order.
10. Skip optional/admin tables for the first demo.
11. Generate 500 leads with the approved monthly trend.
12. Generate clean sources with no Unknown source.
13. Generate opt-ins, traffic attribution, and form answers.
14. Generate appointments with realistic outcomes.
15. Generate exactly one Fathom record for every completed/attended past call.
16. Generate no Fathom records for no-show, canceled, rescheduled, future, or deleted appointments.
17. Generate contracts, payments, and refunds according to the scenario rules.
18. Generate deterministic diagnostic_text_insights.
19. Build diagnostic_lead_snapshot after base data is seeded.
20. Run validation checks.
21. Print final row counts and validation summary.
```

---

## 3. Absolute Safety Requirements

Codex must implement these safety rules before any write operation.

### Required CLI Guardrails

The script must require:

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001
```

The script must support:

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --dry-run
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --force
```

### Refuse to Run When

The script must stop with a clear error if:

```text
--org-id is missing
--org-id is empty
--org-id is not org_dummy_client_demo_001, unless an explicit local-only override flag is added
--org-id equals any known live client org ID
database URL is missing
schema/table validation fails
```

### Known Live Org Protection

Add a constant near the top of the script:

```python
DUMMY_ORG_ID = "org_dummy_client_demo_001"
BLOCKED_ORG_IDS = {
    "REPLACE_WITH_LIVE_CLIENT_ORG_ID_BEFORE_RUNNING"
}
```

If `BLOCKED_ORG_IDS` still contains the placeholder, print a warning and require the user to replace it before running with `--force`.

Do not silently proceed with force mode if the blocked live org ID is not configured.

### No Automatic Execution

Codex must not execute:

```bash
python scripts/seed_demo_data.py ...
```

Codex must only create the script.

---

## 4. Required First-Demo Table Scope

Seed these required tables only:

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

Do not seed these optional/admin tables for the first demo:

```text
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
provider_integrations
provider_credentials
webhook_events
integration_health_checks
audit_logs
notification_logs
raw payload tables
secret/token/API key tables
```

If the script sees existing rows in optional tables for the dummy org, do not delete them unless explicitly required by the cleanup dependency for seeded data. For first demo, the script should not create new rows in those tables.

---

## 5. Required Insert Order

Use this insert order:

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
diagnostic_lead_snapshot must be built after base tables are seeded.
Do not manually fake diagnostic_lead_snapshot first.
```

---

## 6. Required Cleanup Strategy for --force

When `--force` is passed, delete only rows belonging to:

```text
org_dummy_client_demo_001
```

Never truncate full tables.

Never delete rows without org filtering.

For child tables without direct `clerk_org_id`, delete through parent joins only.

### Cleanup Order

Use reverse dependency order:

```text
1. diagnostic_lead_snapshot where clerk_org_id = :org_id
2. diagnostic_text_insights where clerk_org_id = :org_id
3. refunds where clerk_org_id = :org_id
4. payments where clerk_org_id = :org_id
5. contracts where clerk_org_id = :org_id
6. fathom_call_records where clerk_org_id = :org_id
7. appointments where clerk_org_id = :org_id
8. opt_in_question_answers by joining through opt_ins for :org_id
9. traffic_attributions by joining through opt_ins for :org_id
10. opt_ins where clerk_org_id = :org_id
11. leads where clerk_org_id = :org_id
12. appointment_event_types where clerk_org_id = :org_id
13. programs where clerk_org_id = :org_id
14. marketing_sources where clerk_org_id = :org_id
15. sales_statuses where clerk_org_id = :org_id
```

Use transactions.

If any cleanup or insert fails, rollback the transaction.

---

## 7. Required Schema Inspection

Before coding inserts, Codex must inspect the actual schema files in the repository.

Use the current schema as the source of truth for:

```text
column names
enum values
nullable columns
required columns
foreign keys
money units
timestamp column names
soft delete columns
JSON/JSONB column names
```

Important:

```text
Do not invent columns.
Do not assume optional columns exist.
Do not insert into columns that are not present in the actual schema.
If a column exists in documentation but not in schema, follow the actual schema.
If a required column exists in schema but is not mentioned in the blueprint, generate safe demo value.
```

Recommended files to inspect:

```text
schema.txt
app/diagnostics/lead_snapshot.py
app/skills/modules/*.md
prisma schema files if available
```

If the project has existing DB helper utilities, use them where appropriate.

---

## 8. Database Connection Requirements

Use the existing project database settings.

Preferred approach:

```text
Use app.config.get_database_settings() or existing project settings if available.
Fallback to HERMON_DATABASE_URL or DATABASE_URL.
Use SQLAlchemy with psycopg if that is how the project already connects.
```

Do not hardcode database URL.

Do not print database URL.

Do not print credentials.

---

## 9. Deterministic Data Generation

Use deterministic generation.

Required:

```python
random.seed(42)
```

Use stable UUID generation where useful.

Recommended helper:

```python
uuid.uuid5(uuid.NAMESPACE_URL, f"{org_id}:{table}:{logical_key}")
```

This makes reruns stable and easier to debug.

If using random UUIDs, still keep generated relationships in ID maps.

Do not use Faker unless it is already installed in the project. Prefer built-in Python lists of synthetic names.

---

## 10. Required ID Maps

Maintain these maps during seeding:

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

These maps are required so child records join correctly.

---

## 11. Lead Counts and Monthly Trend

Generate exactly 500 active dummy leads.

Use this monthly lead distribution:

| Month | Lead count |
|---|---:|
| Nov 2025 | 55 |
| Dec 2025 | 70 |
| Jan 2026 | 95 |
| Feb 2026 | 82 |
| Mar 2026 | 90 |
| Apr 2026 | 108 |

Dataset period:

```text
2025-11-01 to 2026-04-30
```

Trend story:

```text
Increasing → increasing → slight drop → stable/recovering → increasing
```

Rules:

```text
Do not create flat random monthly distribution.
Spread lead.created_at values within each month.
Keep timestamps realistic.
Set updated_at after created_at.
Set is_deleted = false for main demo leads.
```

---

## 12. Lead Scenario Counts

Assign every lead to exactly one scenario.

| Scenario | Lead count |
|---|---:|
| Paid / converted | 110 |
| Completed call but not signed | 150 |
| Booked but not completed | 90 |
| Lead created but never booked | 75 |
| Signed but not paid | 25 |
| Lost | 30 |
| Unqualified | 20 |

Total:

```text
500
```

Rules:

```text
Lead status must match scenario.
Paid / converted leads should have WON status.
Signed but not paid leads should have PARTIAL_PAYMENT or FOLLOW_UP status.
Completed call but not signed leads should be FOLLOW_UP or LOST.
Booked but not completed leads should be NO_SHOW, CANCELED, or RESCHEDULED.
Lead created but never booked should be NEW_LEAD or FOLLOW_UP.
Lost leads should be LOST.
Unqualified leads should be UNQUALIFIED.
```

---

## 13. Source Distribution

Create exactly these marketing sources:

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

Distribute 500 leads like this:

| Source | Lead count |
|---|---:|
| Facebook | 90 |
| Instagram | 60 |
| YouTube | 65 |
| Google Search | 70 |
| Webinar | 60 |
| Referral | 40 |
| Email Campaign | 35 |
| Calendly | 30 |
| Landing Page | 30 |
| Organic Search | 20 |

Rules:

```text
No Unknown source.
No blank source.
No missing first_source_id.
No missing last_source_id.
No orphaned source IDs.
Every lead must have first_source_id, first_source_name, last_source_id, last_source_name.
For most leads first_source = last_source.
For around 10% to 15% of leads, first_source may differ from last_source to show realistic source change.
```

Business story:

```text
Referral and Google Search should have better conversion rates.
Facebook and Instagram should have higher lead volume but weaker conversion.
YouTube should have many completed calls but more completed-not-signed leads.
Webinar should have strong attendance but mixed payment outcomes.
```

---

## 14. Sales Status Seeding

Create one status per role:

| Role | Name |
|---|---|
| NEW_LEAD | New Lead |
| APPOINTMENT_BOOKED | Appointment Booked |
| NO_SHOW | No Show |
| RESCHEDULED | Rescheduled |
| CANCELED | Canceled |
| PARTIAL_PAYMENT | Partial Payment |
| WON | Won |
| UNQUALIFIED | Unqualified |
| FOLLOW_UP | No Sale - Follow Up |
| LOST | Lost |

Rules:

```text
Use org_dummy_client_demo_001.
Use valid enum values from schema.
Set display colors if required by schema.
Set is_default and is_system safely.
Do not create duplicate status names for the same org.
```

---

## 15. Program Seeding

Create these programs:

| Program | Price minor | Display value |
|---|---:|---:|
| Starter Program | 150000 | €1,500 |
| Growth Program | 300000 | €3,000 |
| Premium Coaching Program | 500000 | €5,000 |
| Freedom Academy | 250000 | €2,500 |
| Trading Accelerator | 400000 | €4,000 |

Rules:

```text
Use EUR where currency is required.
Use payment_type values supported by schema.
Do not soft-delete demo programs.
```

---

## 16. Appointment Event Type Seeding

Create these event types:

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
Most appointments should use SALES_CALL.
Do not create confusing internal names.
Do not soft-delete event types.
```

---

## 17. Lead Field Generation

Every lead should include safe synthetic identity data.

Required style:

```text
Use fake first and last names.
Use example.com emails.
Use fake phone numbers.
Do not use real client names.
Do not use real emails.
Do not use real phone numbers.
```

Example email pattern:

```text
lead001@example.com
lead002@example.com
```

Example phone pattern:

```text
+319700000001
+319700000002
```

Use schema-valid values for:

```text
source
status_id
assigned_to
setter_id
next_touch_point_at
next_touch_point_type
created_at
updated_at
is_deleted
```

For owner/setter IDs, use safe synthetic user IDs like:

```text
demo_closer_001
demo_setter_001
demo_owner_001
```

Do not invent real user names unless the schema has a user/profile table and the demo needs it.

---

## 18. Opt-In Seeding

Generate around 650 opt-ins for 500 leads.

Rules:

```text
Every lead should have at least one opt-in unless intentionally creating a small natural exception.
Some leads can have multiple opt-ins.
opt_ins.created_at should be equal to or shortly after lead.created_at.
Use provider_form_name values from Step 2.
Use valid opt_in source enum values from schema.
Do not store raw_payload.
Do not store real IP addresses or user agents.
```

Provider form names:

```text
Qualification Form
Strategy Call Form
Webinar Registration Form
Newsletter Signup Form
Landing Page Lead Form
```

---

## 19. Traffic Attribution Seeding

Generate traffic attribution rows for most opt-ins.

Use:

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

Rules:

```text
Use safe generic referrers only.
Do not use real client domains.
Keep attribution consistent with marketing source where possible.
Do not create Unknown UTM source for the first demo.
```

---

## 20. Opt-In Question Answer Seeding

For most opt-ins, create form answers for these questions:

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

Controlled answer lists must follow Step 2.

Rules:

```text
Use broad safe locations only.
Do not generate street addresses.
Do not generate postal codes.
Do not generate real personal location data.
Do not use form answers to claim revenue attribution unless supported later.
```

---

## 21. Appointment Seeding

Generate around 420 appointments.

Target distribution:

```text
around 260 completed / attended past calls
around 55 no-shows
around 35 canceled
around 30 rescheduled
around 40 future scheduled
```

Rules:

```text
Appointment date must be after lead.created_at.
Most appointments should happen 1 to 14 days after lead creation.
Future appointments must be after the demo reference date.
No-show appointments must have no_show = true.
Canceled appointments must use CANCELED outcome status.
Rescheduled appointments must use RESCHEDULED outcome status.
Completed appointments must have no_show = false and non-canceled/non-rescheduled outcome.
Use valid appointment source enum values.
Set is_deleted = false.
```

Important:

```text
No-show/canceled/rescheduled/future appointments must not get Fathom records.
```

---

## 22. Fathom Record Seeding

This is one of the most critical rules.

For every completed/attended past appointment, create exactly one linked Fathom record.

For all other appointment scenarios, create no Fathom record.

### Required Mapping

| Appointment scenario | Fathom record? |
|---|---:|
| Completed / attended sales call | Yes |
| No-show | No |
| Canceled | No |
| Rescheduled | No |
| Future appointment | No |
| Attended but missing Fathom | Avoid entirely |

### Required Expected Outcome

```text
completed_call_count = fathom_record_count
completed_calls_missing_fathom_count = 0
completed_call_fathom_coverage_rate = 100.00
```

### Fathom Fields

Populate where schema supports:

```text
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

### Story Templates

Use scenario-based summaries:

```text
converted_strong_intent
converted_after_payment_plan
completed_not_signed_partner_approval
completed_not_signed_budget
completed_not_signed_needs_more_time
signed_not_paid_payment_link_issue
signed_not_paid_payment_timing
lost_low_intent
unqualified_poor_fit
follow_up_needs_more_information
```

Rules:

```text
Summaries must sound like real sales-call notes.
Do not use placeholders.
Do not expose private data.
Objections must align with the lead scenario.
Action items must be practical.
```

---

## 23. Contract Seeding

Create contracts based on scenario.

| Lead scenario | Contract behavior |
|---|---|
| Paid / converted | Signed contract |
| Signed but not paid | Signed contract |
| Completed call but not signed | Sent/viewed contract optional |
| Lost | Optional voided contract |
| Unqualified | No contract |
| Lead only / never booked | No contract |
| Booked but not completed | No contract |

Rules:

```text
Signed contracts must have signed_at.
Sent/viewed contracts should have sent_at and optionally viewed_at.
Voided contracts should have voided_at.
Do not create paid payments for unsigned contracts.
Do not create contracts for unqualified leads in first demo.
Use EUR.
Use source table money unit correctly.
```

---

## 24. Payment Seeding

Create payments based on scenario.

| Lead scenario | Payment behavior |
|---|---|
| Paid / converted | One or more PAID payments |
| Signed but not paid | PENDING or FAILED payment |
| Completed call but not signed | No payment |
| Lost | No paid payment |
| Unqualified | No payment |
| Lead only / never booked | No payment |
| Booked but not completed | No payment |

Payment statuses:

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
Use minor units if schema expects minor units.
Paid payments should have paid_at.
Pending payments should have due_date.
Do not create payment before contract signed.
Do not create payment for unqualified leads.
Do not create payment for lead-only/no-booked-call leads.
Do not create payment for no-show/canceled/rescheduled-only leads.
```

---

## 25. Refund Seeding

Generate 10 to 15 refunds.

Rules:

```text
Refunds must connect to valid paid payments.
Refund date must be after payment paid_at.
Refund amount must not exceed original payment amount.
Use status SUCCEEDED for normal demo refunds.
Do not create refunds for pending or failed payments.
Do not create refunds for leads that never paid.
```

---

## 26. Diagnostic Text Insights Seeding

Seed `diagnostic_text_insights` deterministically from lead scenario and source context.

Do not call LLM during the seed.

## Primary Source for Demo Diagnostic Text Insights

For demo data, do not call the LLM to create `diagnostic_text_insights`.

Since dummy Fathom call records are already generated from known lead scenarios and story templates, use the generated `fathom_call_records` as the primary source for diagnostic text insights.

This means:

```text
lead scenario
+ Fathom story template
+ Fathom summary
+ Fathom objections
+ Fathom action items
↓
deterministic diagnostic_text_insights rows
```

Do not run a separate extraction job.

Do not call OpenAI or any LLM for this demo seeding task.

---

## Call-Derived Insight Source Fields

For insights created from Fathom records, use:

```text
source_table = fathom_call_records
source_record_id = fathom_call_records.id
source_text_type = fathom_summary
```

Each diagnostic insight must still include:

```text
clerk_org_id
lead_id
source_table
source_record_id
source_text_type
source_event_at
source_text_hash
source_text_length
reason_category
reason_subcategory
is_conversion_blocker
buying_intent_level
lead_quality_level
profession_category
employment_status
extraction_status
extracted_at
```

Use safe defaults for fields that are not naturally available from the Fathom story.

Do not store `is_human_reason_supported`.

Do not store raw transcripts.

---

## Deterministic Mapping From Fathom Story Template

The reason fields should be assigned deterministically from the same Fathom story template used to create the call summary.

Use this mapping:

| Fathom story template | reason_category | reason_subcategory | is_conversion_blocker |
|---|---|---|---:|
| `converted_strong_intent` | `unknown` | `unknown` | false |
| `converted_after_payment_plan` | `price_or_budget` | `needs_payment_plan` | false |
| `completed_not_signed_partner_approval` | `needs_partner_approval` | `waiting_for_partner` | true |
| `completed_not_signed_budget` | `price_or_budget` | `budget_not_available` | true |
| `completed_not_signed_needs_more_time` | `timing_issue` | `needs_more_time` | true |
| `signed_not_paid_payment_link_issue` | `payment_friction` | `system_or_link_issue` | true |
| `signed_not_paid_payment_timing` | `payment_friction` | `payment_not_completed` | true |
| `lost_low_intent` | `low_intent` | `not_ready_now` | true |
| `unqualified_poor_fit` | `poor_fit` | `wrong_customer_fit` | true |
| `follow_up_needs_more_information` | `needs_more_information` | `needs_more_information` | true |

---

## Suggested Intent and Quality Mapping

Use this mapping unless the scenario provides a better value:

| Lead scenario | buying_intent_level | lead_quality_level |
|---|---|---|
| Paid / converted | `high` or `very_high` | `high_quality` |
| Completed call but not signed | `medium` or `high` | `medium_quality` |
| Signed but not paid | `high` | `medium_quality` |
| Booked but not completed | `low` or `medium` | `medium_quality` |
| Lost | `low` | `low_quality` |
| Unqualified | `very_low` | `unqualified` |
| Lead created but never booked | `unknown` or `low` | `unknown` |

---

## Profession and Employment Mapping

If profession and employment status were already generated in `opt_in_question_answers`, reuse those values where possible.

Map them to the allowed `diagnostic_text_insights` enum values.

Example mappings:

```text
Business Owner → profession_category = business_owner
Employee → profession_category = employee
Self-employed → profession_category = self_employed
Student → profession_category = student
Trader / Investor → profession_category = trader_or_investor
Sales or Marketing → profession_category = sales_or_marketing
Technology → profession_category = technology
Healthcare → profession_category = healthcare
Retired → profession_category = retired
Unemployed → profession_category = unemployed
```

Employment-status mappings:

```text
Full-time → employment_status = full_time
Part-time → employment_status = part_time
Self-employed → employment_status = self_employed
Student → employment_status = student
Business Owner → employment_status = business_owner
Unemployed → employment_status = unemployed
Retired → employment_status = retired
```

If no safe mapping exists, use:

```text
profession_category = unknown
employment_status = unknown
```

---

## Source Text Hash and Length

For each Fathom-derived insight:

```text
source_text_hash = hash of the generated Fathom summary text
source_text_length = character length of the generated Fathom summary text
source_event_at = fathom_call_records.call_started_at
extraction_status = success
```

Use a deterministic hash such as SHA-256.

Do not use random hashes.

---

## Why This Rule Exists

This keeps demo data:

```text
deterministic
fast
cheap
consistent with generated Fathom summaries
free from LLM extraction variability
easy to validate
```

The production workflow can still use LLM extraction on real Fathom summaries later, but the demo seed script should not call an LLM.

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

Scenario mapping:

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

Rules:

```text
Every diagnostic_text_insights row must have valid clerk_org_id.
Every row must reference a valid lead_id.
source_table and source_record_id should reference a seeded source record where possible.
Do not store is_human_reason_supported.
Do not store raw transcript text.
```

---

## 27. Diagnostic Lead Snapshot Build

After base data and diagnostic text insights are seeded, build `diagnostic_lead_snapshot`.

Preferred approach:

```python
from app.diagnostics.lead_snapshot import build_diagnostic_lead_snapshot_once

build_diagnostic_lead_snapshot_once(org_id, force=True)
```

If this helper cannot be used directly, Codex should use the existing project diagnostic snapshot builder logic, not create an unrelated snapshot implementation.

Rules:

```text
Do not manually fake diagnostic_lead_snapshot first.
Snapshot must be derived from base tables.
Snapshot row count must equal active dummy lead count.
Diagnostic money fields must be major-unit EUR.
```

---

## 28. Validation Checks

The script must run validation checks after seeding.

If any validation fails, print the failed checks clearly and exit with non-zero status.

### 28.1 Organization Safety

Validate:

```text
All seeded rows use org_dummy_client_demo_001.
No seeded rows use live client org ID.
No cleanup affects live client org.
```

### 28.2 Lead Count and Distribution

Validate:

```text
Total active dummy leads = 500.
Monthly lead distribution:
- Nov 2025: 55
- Dec 2025: 70
- Jan 2026: 95
- Feb 2026: 82
- Mar 2026: 90
- Apr 2026: 108
```

### 28.3 Source Validation

Validate:

```text
No lead has missing first_source_id.
No lead has missing last_source_id.
No blank first_source_name.
No blank last_source_name.
No source name = Unknown.
All first_source_id and last_source_id join to marketing_sources.
Source distribution matches the blueprint.
```

### 28.4 Acquisition Validation

Validate:

```text
Every opt-in joins to a valid lead.
Traffic attribution rows join to valid opt-ins.
Question-answer rows join to valid opt-ins.
Profession answers exist for most opt-ins.
Employment-status answers exist for most opt-ins.
Country or region answers exist for most opt-ins.
Budget range answers exist for most opt-ins.
Decision-maker answers exist for most opt-ins.
No precise addresses are generated.
```

### 28.5 Appointment and Fathom Validation

Validate:

```text
Every appointment joins to a valid lead.
Every completed/attended past appointment has exactly one Fathom record.
No no-show appointment has Fathom record.
No canceled appointment has Fathom record.
No rescheduled appointment has Fathom record.
No future appointment has Fathom record.
No Fathom record exists without valid appointment.
completed_calls_missing_fathom_count = 0.
completed_call_fathom_coverage_rate = 100.00.
```

### 28.6 Revenue Validation

Validate:

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

### 28.7 Optional Table Validation

For the first demo, validate that the script did not seed these tables by default:

```text
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
```

If existing rows are present from earlier manual tests, print a warning instead of deleting them unless `--force-clean-optional` is explicitly implemented.

### 28.8 Diagnostic Validation

Validate:

```text
diagnostic_lead_snapshot row count = active dummy lead count.
No unknown source quality flags.
No missing source quality flags.
completed_calls_missing_fathom_count = 0.
completed_call_fathom_coverage_rate = 100.00.
Diagnostic money values are in major-unit EUR.
```

### 28.9 Business Story Validation

Print summary checks showing:

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

---

## 29. Expected Terminal Output

At the end, print a readable summary.

Example:

```text
Demo seed completed successfully.

Organization:
- org_dummy_client_demo_001

Seeded row counts:
- sales_statuses: 10
- marketing_sources: 10
- programs: 5
- appointment_event_types: 5
- leads: 500
- opt_ins: 650
- traffic_attributions: <count>
- opt_in_question_answers: <count>
- appointments: ~420
- fathom_call_records: <completed_call_count>
- contracts: <count>
- payments: <count>
- refunds: 10-15
- diagnostic_text_insights: <count>
- diagnostic_lead_snapshot: 500

Validation:
- organization safety: passed
- monthly trend: passed
- source validation: passed
- acquisition validation: passed
- appointment/Fathom validation: passed
- revenue validation: passed
- diagnostic validation: passed
```

If any validation fails:

```text
Demo seed failed validation.

Failed checks:
- <check_name>: <details>

Transaction rolled back.
```

---

## 30. Dry Run Behavior

When `--dry-run` is used:

```text
Do not insert rows.
Do not delete rows.
Do not build diagnostic snapshot.
Print planned counts.
Print planned scenario distribution.
Print planned source distribution.
Print planned monthly distribution.
Print safety checks.
```

Dry run should be safe to execute anytime.

---

## 31. Transaction Behavior

Use transactions for DB writes.

Preferred behavior:

```text
Start transaction.
Clean dummy org data if --force is passed.
Seed all required data.
Build diagnostic snapshot if it can run inside same transaction; otherwise run after commit only if base seed passed.
Run validations.
Commit only if everything passes.
Rollback if any error occurs.
```

If diagnostic snapshot builder manages its own transaction, clearly handle this and document it in comments.

---

## 32. Coding Style Requirements

Codex should produce clean, maintainable Python.

Required style:

```text
Use clear functions.
Avoid one giant script body.
Add docstrings for main functions.
Use type hints where practical.
Use constants for distributions.
Use helper functions for IDs, timestamps, inserts, and validation.
Do not add unnecessary dependencies.
Do not include placeholder comments like "handle other tables similarly".
Do not leave TODOs for required first-demo behavior.
```

Recommended function structure:

```text
parse_args()
get_engine()
validate_safety_args()
schema_smoke_check()
cleanup_dummy_org()
seed_sales_statuses()
seed_marketing_sources()
seed_programs()
seed_appointment_event_types()
generate_lead_plan()
seed_leads()
seed_opt_ins()
seed_traffic_attributions()
seed_opt_in_question_answers()
seed_appointments()
seed_fathom_call_records()
seed_contracts()
seed_payments()
seed_refunds()
seed_diagnostic_text_insights()
build_diagnostic_snapshot()
run_validations()
print_summary()
main()
```

---

## 33. Required Comments in Script

Add comments only where useful.

Useful comments:

```text
# Safety guard: never allow live org seeding.
# Child tables without clerk_org_id are cleaned through parent opt_ins.
# Fathom is generated only for completed attended calls.
# Diagnostic snapshot is derived after base records are seeded.
```

Avoid comments like:

```text
# This is what the user asked for.
# Add more tables similarly.
# TODO implement later.
```

---

## 34. Definition of Done

Codex is done with Step 3 implementation only when:

```text
scripts/seed_demo_data.py is created.
The script follows Step 1 and Step 2.
The script has CLI args for --org-id, --dry-run, and --force.
The script includes safety guardrails.
The script seeds only required first-demo tables.
The script skips optional/admin tables.
The script generates deterministic 500-lead demo data.
The script generates the approved monthly trend.
The script generates clean non-Unknown sources.
The script generates opt-ins and enriched form answers.
The script generates appointments.
The script generates exactly one Fathom record per completed call.
The script generates no Fathom records for no-shows/canceled/rescheduled/future appointments.
The script generates contracts, payments, and refunds.
The script generates diagnostic_text_insights.
The script builds diagnostic_lead_snapshot after base data.
The script runs validations.
The script prints row-count and validation summary.
Codex does not execute the script against the database.
```

---

## 35. What Not To Do

Do not:

```text
Do not execute the seed script.
Do not run database writes automatically.
Do not use live client org ID.
Do not insert dummy rows into live org.
Do not truncate full tables.
Do not delete rows without org filtering.
Do not create Unknown source.
Do not create completed appointments without Fathom.
Do not create Fathom for no-show/canceled/rescheduled/future appointments.
Do not seed invoices, payment links, payment proofs, subscriptions, or unmatched payments for first demo.
Do not create fake real-looking payment URLs.
Do not create fake real-looking recording/transcript URLs.
Do not generate secrets, tokens, API keys, provider credentials, or webhook payloads.
Do not call LLM during seeding.
Do not expose raw payloads.
Do not use real names, emails, phone numbers, or locations.
```

---

## 36. Next Step After Codex Generates Script

After Codex creates the script, do not run it immediately.

Step 4 should be:

```text
Review scripts/seed_demo_data.py carefully.
Check safety guardrails.
Check cleanup SQL.
Check insert order.
Check schema column usage.
Check validation queries.
Check Fathom logic.
Check optional tables are skipped.
Only then run dry-run.
```
