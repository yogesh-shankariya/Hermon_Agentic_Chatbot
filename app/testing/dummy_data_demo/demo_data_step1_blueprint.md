# Step 1 — Dummy Data Blueprint for Client Demo

## Purpose

This document defines the dummy/demo data plan before writing any seed script.

The goal is not only to create valid rows. The goal is to create a realistic, client-friendly demo dataset so the chatbot can answer business questions clearly, consistently, and safely without exposing live client data.

This is Step 1 only. Do not start coding until this blueprint is reviewed and approved.

---

## 1. Fixed Demo Organization

Use one fixed dummy organization ID for all demo rows:

```text
org_dummy_client_demo_001
```

Every dummy row that has `clerk_org_id` must use this value only.

Do not mix dummy rows into the live client organization.

### Rules

- All dummy data must belong to `org_dummy_client_demo_001`.
- Do not insert dummy rows using the live client org ID.
- Do not use real client names, real emails, real phone numbers, real meeting links, real payment links, real Fathom links, real webhook data, or real payloads.
- Use EUR only for all money-related records.
- Use synthetic names and safe test email domains such as `example.com`.

---

## 2. Dataset Period and Trend Story

Use a 6-month dataset period:

```text
2025-11-01 to 2026-04-30
```

The data must not look flat or randomly distributed. It should show a clear trend so the client can ask questions such as:

```text
Show monthly lead trend.
Why did leads drop in February?
How did April perform compared to March?
Show appointment trend by month.
Show revenue trend by month.
```

### Monthly Lead Distribution

| Month | Leads | Intended story |
|---|---:|---|
| Nov 2025 | 55 | Starting baseline |
| Dec 2025 | 70 | Growth begins |
| Jan 2026 | 95 | Strong campaign growth |
| Feb 2026 | 82 | Slight decrease after campaign peak |
| Mar 2026 | 90 | Stabilized and recovering |
| Apr 2026 | 108 | Growth returns |

Total leads:

```text
500
```

### Trend Behavior

The trend should look like:

```text
Increasing → increasing → slight drop → stable/recovering → increasing
```

Related records must follow the same time story:

| Domain | Date field behavior |
|---|---|
| Leads | `leads.created_at` follows monthly distribution |
| Opt-ins | `opt_ins.created_at` occurs near lead creation |
| Appointments | `appointments.schedule_time` happens after lead creation |
| Fathom records | `call_started_at` and `call_ended_at` align with completed appointment time |
| Contracts | `sent_at`, `viewed_at`, and `signed_at` happen after completed calls |
| Payments | `paid_at` or `due_date` happens after signed contracts |
| Refunds | Small number of refunded cases, spread lightly across months |

Do not create completely random dates.

---

## 3. Demo Dataset Size

Target a medium-sized dataset that is large enough for trends, breakdowns, and diagnostic answers.

| Data area | Target volume |
|---|---:|
| Leads | 500 |
| Opt-ins | Around 650 |
| Appointments | Around 420 |
| Completed / attended calls | Around 260 |
| Fathom records | Exactly equal to completed / attended calls |
| Contracts | Around 170 |
| Payments | Around 190 |
| Refunds | Around 10 to 15 |
| Diagnostic lead snapshot | One row per active dummy lead |
| Diagnostic text insights | Generated from dummy call/notes/payment/contract context if used |

The exact number can vary slightly, but it must remain internally consistent.

---

## 4. Supported Tables to Prioritize

The seed script should focus only on tables that support the chatbot demo.

### Core Tables

```text
sales_statuses
marketing_sources
leads
appointment_event_types
appointments
fathom_call_records
opt_ins
opt_in_question_answers
traffic_attributions
programs
contracts
payments
refunds
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
diagnostic_lead_snapshot
diagnostic_text_insights
```

### Tables to Avoid or Keep Minimal

Avoid generating realistic data for admin/security/raw integration tables unless the UI strictly requires them.

```text
provider_integrations
provider_credentials
webhook_events
integration_health_checks
audit_logs
notification_logs
raw payload tables
credential tables
secret/token/API key tables
```

Never generate fake secrets that look real.

---

## 5. Lead Funnel Story

The dummy data should tell a clear business story.

Primary story:

```text
The biggest leak is after completed calls: many leads attend calls but do not sign.
The second leak is booked calls that do not complete due to no-shows, cancellations, or reschedules.
Some sources generate high lead volume but weaker conversion.
Referral and Google Search generate better quality and stronger revenue.
```

### Funnel Distribution

| Lead outcome | Lead count | Demo purpose |
|---|---:|---|
| Paid / converted | 110 | Shows successful revenue path |
| Completed call but not signed | 150 | Main funnel leak |
| Booked but not completed | 90 | No-show/canceled/rescheduled story |
| Lead created but never booked | 75 | Top-of-funnel drop |
| Signed but not paid | 25 | Payment follow-up story |
| Lost | 30 | Closed lost scenario |
| Unqualified | 20 | Poor-fit scenario |

Total:

```text
500
```

### Business Interpretation

The chatbot should be able to answer:

```text
Where are we losing leads?
Why are leads not converting?
Why are many calls not turning into signed contracts?
What should sales focus on?
Which sources bring better quality leads?
```

---

## 6. Source Rules

For client demo, avoid unknown/missing source scenarios.

Do not use:

```text
Unknown
Other Unknown
Not Set
Blank
N/A
No Source
```

### Lead Source Enum Values

For `leads.source`, use only controlled enum-style values:

```text
CALENDLY
MANUAL
TYPEFORM
WEBINAR
NEWSLETTER
LANDING_PAGE
OTHER
```

### Marketing Source Names

Create clean business-facing `marketing_sources` rows:

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

Every dummy lead must have:

```text
first_source_id
first_source_name
last_source_id
last_source_name
```

Both source IDs must point to valid `marketing_sources` rows.

For most leads:

```text
first_source = last_source
```

For a small number of leads, around 10% to 15%, source can change:

```text
first_source = Facebook
last_source = Webinar
```

But do not create missing, orphaned, or unknown source data for client demo.

### Source Distribution

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

### Diagnostic Source Quality Rule

Avoid source-quality problems in demo data.

Expected:

```text
source_confidence mostly high
missing_first_source = false
missing_last_source = false
has_unknown_source = false
orphaned_first_source_id = false
orphaned_last_source_id = false
has_revenue_without_source = false
```

A few rows can have medium confidence only because first source and last source changed, not because source is missing.

---

## 7. Appointment Design

Appointments should support questions about booked calls, no-shows, completed calls, upcoming calls, event types, and appointment trends.

### Appointment Event Types

Create simple, understandable event types:

```text
Qualification Call
Strategy Call
Discovery Call
Follow-up Call
Payment Support Call
```

Suggested categories:

```text
SALES_CALL
TRIAGE_CALL
COACHING_CALL
```

For demo, most appointments should be sales calls.

### Appointment Scenarios

| Scenario | Approx count | Notes |
|---|---:|---|
| Completed / attended past sales call | Around 260 | Must have Fathom record |
| No-show | Around 55 | No Fathom record |
| Canceled | Around 35 | No Fathom record |
| Rescheduled | Around 30 | No Fathom record for original appointment |
| Future scheduled | Around 40 | No Fathom record yet |

Total appointments:

```text
Around 420
```

### Date Rules

- Appointment date should be after lead creation.
- Most appointments should happen 1 to 14 days after lead creation.
- Future appointments should be after the current demo reference date.
- No deleted appointments should be included in normal demo analytics unless specifically testing deleted-data behavior.

---

## 8. Fathom Record Rule

This is a fixed rule for this project.

For client demo data, every completed/attended past appointment must have exactly one linked Fathom record.

### Appointment-to-Fathom Rules

| Appointment scenario | Fathom record? | Client perception |
|---|---:|---|
| Completed / attended sales call | Yes | Looks complete and useful |
| No-show | No | Makes sense |
| Canceled | No | Makes sense |
| Rescheduled | No | Makes sense |
| Future appointment | No | Makes sense |
| Attended but missing Fathom | Avoid | Looks like integration issue |

### Expected Diagnostic Outcome

```text
completed_call_count = fathom_record_count
completed_calls_missing_fathom_count = 0
completed_call_fathom_coverage_rate = 100.00
```

### Required Linking

Every Fathom record must be linked by:

```text
fathom_call_records.appointment_id = appointments.id
fathom_call_records.clerk_org_id = appointments.clerk_org_id
```

### Demo Safety

Keep these fields null or empty:

```text
raw_payload
recording_url
transcript_url
```

Do not create fake recording or transcript links unless the demo specifically requires it later.

---

## 9. Fathom Story Templates

Fathom summaries must sound like useful business call notes, not dummy placeholders.

Create 8 to 10 reusable story templates and assign them based on the lead outcome.

### Required Template Types

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

Each Fathom record should contain:

```text
summary
key_points
objections
action_items
ai_generated_title
ai_suggested_outcome
ai_confidence_score
ai_rationale
call_duration_seconds
call_started_at
call_ended_at
```

### Example: Converted Strong Intent

```text
Title:
Strategy Call - Ready to Join

Summary:
The lead joined the call with clear interest and asked practical questions about the program, expected results, and onboarding. They confirmed the offer made sense and agreed to move forward with the recommended plan.

Key points:
- Lead understood the value of the program
- Lead asked about onboarding and timeline
- Lead agreed to complete payment after the call

Objections:
[]

Action items:
- Send onboarding instructions
- Confirm payment completion
- Add lead to the customer onboarding flow
```

### Example: Completed But Not Signed

```text
Title:
Strategy Call - Needs More Time

Summary:
The lead was interested in the program but was not ready to sign during the call. They wanted to discuss the decision with their partner and review the offer once more before committing.

Key points:
- Lead showed interest but did not commit immediately
- Partner approval is needed before signing
- Follow-up timing was agreed

Objections:
- Needs partner approval
- Needs more time

Action items:
- Follow up in 2 days
- Send a short summary of the offer
- Confirm whether partner approval is completed
```

### Example: Signed But Not Paid

```text
Title:
Contract Signed - Payment Pending

Summary:
The lead agreed with the offer and contract terms, but payment was not completed during the call. They mentioned they may need help with the payment link and asked for the details to be sent again.

Key points:
- Lead accepted the offer
- Contract step is complete
- Payment is still pending

Objections:
- Payment not completed
- Payment link support needed

Action items:
- Resend payment link
- Follow up today to confirm payment
- Escalate if payment link does not work
```

---

## 10. Contract, Payment, and Revenue Design

Revenue data should support client questions about revenue, signed contract value, pending payments, refunds, payment provider, and program performance.

### Programs

Create 3 to 5 simple programs:

```text
Starter Program
Growth Program
Premium Coaching Program
Freedom Academy
Trading Accelerator
```

Use EUR pricing.

Example prices in minor units:

```text
Starter Program: 150000
Growth Program: 300000
Premium Coaching Program: 500000
Freedom Academy: 250000
Trading Accelerator: 400000
```

These represent EUR 1,500, EUR 3,000, EUR 5,000, EUR 2,500, and EUR 4,000.

### Contract Scenarios

| Scenario | Approx count | Notes |
|---|---:|---|
| Signed contracts with paid payments | Around 110 | Converted leads |
| Signed contracts with pending/failed payment | Around 25 | Signed but not paid |
| Sent/viewed but not signed | Around 35 | Completed call but not signed |
| Voided/lost contracts | Small count | For realistic operational data |

### Payment Scenarios

| Payment status | Purpose |
|---|---|
| PAID | Collected revenue |
| PENDING | Outstanding amount |
| FAILED | Payment issue |
| LOST | Lost payment |
| REFUNDED | Refunded customer |

Use providers:

```text
STRIPE
MOLLIE
MANUAL
```

Avoid WHOP unless the existing demo UI or schema needs it.

### Refund Scenarios

Create 10 to 15 refund cases only.

Refunds should be tied to paid payments.

Refund reasons can be simple and business-friendly:

```text
Customer changed decision after onboarding
Duplicate payment correction
Program no longer suitable
```

---

## 11. Acquisition and Form Data

Acquisition data should support questions about opt-ins, forms, UTM campaigns, landing pages, referrers, and form-answer distributions.

### Opt-ins

Target:

```text
Around 650 opt-ins for 500 leads
```

This means some leads can have multiple opt-ins.

### Provider Form Names

Use clean form names:

```text
Qualification Form
Strategy Call Form
Webinar Registration Form
Newsletter Signup Form
Landing Page Lead Form
```

### UTM Campaigns

Use readable campaign names:

```text
jan_growth_campaign
webinar_q1_promo
youtube_strategy_series
facebook_leadgen_q1
google_search_brand
email_followup_sequence
```

### Landing Pages

Use simple paths, not real URLs:

```text
/freedom-academy
/trading-accelerator
/strategy-call
/webinar-registration
/free-training
```

### Referrers

Use generic safe values:

```text
google.com
facebook.com
instagram.com
youtube.com
email
referral
```

Do not use real client domains unless they are fake/demo domains.

### Form Question Examples

Use realistic but safe business questions:

```text
What is your main goal?
What is your biggest challenge right now?
How soon do you want to get started?
What is your current experience level?
What budget range are you comfortable with?
Are you the final decision maker?
```

Answers should be simple and useful for analytics.

## Opt-In Enrichment Fields

Add additional dummy form-answer data to make the client demo more useful, realistic, and easy to understand.

These fields should be stored in:

```text
opt_in_question_answers
```

Do not store these directly on the lead table unless the actual schema already supports it.

Use these additional form questions:

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

Use broad safe demo locations only.

Do not generate:

```text
street addresses
house numbers
postal codes
precise home locations
real personal location data
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

### Expected Demo Questions Supported

These fields should support client-facing questions like:

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

Do not use these fields to claim revenue attribution unless an approved revenue-to-form-answer attribution rule is added later.

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
```

---

## 12. Diagnostic Snapshot Design

Do not manually fake `diagnostic_lead_snapshot` first.

Correct sequence:

```text
Seed base tables
Run diagnostic snapshot builder for org_dummy_client_demo_001
Validate diagnostic snapshot
```

The diagnostic snapshot should be derived from the dummy base data so diagnostic answers match normal SQL analytics answers.

### Expected Diagnostic Behavior

The chatbot should be able to answer:

```text
Where are we losing people in the funnel?
Why are leads not converting?
Which source looks good but may be misleading?
Which source has high lead volume but weak conversion?
What should sales focus on?
What should marketing investigate?
Why did leads increase but revenue not increase at the same rate?
```

### Diagnostic Story

Expected high-level story:

```text
The largest leak is after completed calls because many attended leads did not sign.
Facebook and Instagram bring higher volume but lower conversion.
Referral and Google Search bring fewer leads but stronger conversion and revenue.
Webinar has strong attendance but mixed payment completion.
YouTube has good booked-call volume but many completed-not-signed leads.
```

---

## 13. Diagnostic Text Insights

If using `diagnostic_text_insights`, generate it from dummy text sources such as:

```text
Fathom summaries
lead notes
payment context
contract context
opt-in answers
```

Do not call LLM during normal seed unless intentionally running an extraction job.

For demo, the insights can be generated deterministically from scenario templates.

### Useful Reason Categories

Use clear categories that support client-facing explanations:

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

Unknown can exist in real data, but for this client demo keep the data understandable and confidence-building.

---

## 14. Data Quality Rules

For this client demo, avoid creating issues that make the product look broken.

Avoid:

```text
Unknown source
Missing source
Orphaned source ID
Revenue without source
Completed call without Fathom
Payment without lead
Contract without lead
Appointment without lead
Opt-in without lead
Raw payload exposure
Fake but real-looking secrets
Broken payment links
Broken meeting links
```

Allowed realistic business issues:

```text
No-show appointments
Canceled appointments
Rescheduled appointments
Pending payments
Failed payments
Unsigned contracts
Lost leads
Unqualified leads
Follow-up pending
Partner approval needed
Budget concern
Timing issue
```

These issues are business problems, not product problems.

---

## 15. Insert Order Preview

This is only a preview. The exact insert order will be finalized in Step 2.

Likely order:

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

---

## 16. Validation Requirements

After data generation, the seed script must run validation checks.

### Organization Safety

```text
All inserted rows use org_dummy_client_demo_001.
No rows are inserted into live client org.
No seed cleanup deletes live client rows.
```

### Source Validation

```text
No lead has missing first_source_id.
No lead has missing last_source_id.
No lead has unknown source name.
All source IDs join to marketing_sources.
```

### Appointment and Fathom Validation

```text
Every completed/attended past appointment has exactly one Fathom record.
No no-show appointment has Fathom record.
No canceled appointment has Fathom record.
No rescheduled appointment has Fathom record.
No future appointment has Fathom record.
completed_calls_missing_fathom_count = 0.
Fathom coverage for completed calls = 100%.
```

### Relationship Validation

```text
Every appointment joins to a valid lead.
Every opt-in joins to a valid lead.
Every contract joins to a valid lead and program.
Every payment joins to a valid lead and contract where applicable.
Every refund joins to a valid payment.
Every Fathom record joins to a valid completed appointment.
```

### Business Validation

```text
There are leads in each funnel stage.
There are paid payments.
There are pending payments.
There are failed payments.
There are signed contracts.
There are sent/viewed unsigned contracts.
There are no-shows.
There are canceled/rescheduled appointments.
There are meaningful Fathom summaries.
Monthly trend is not flat.
Source performance varies by source.
```

## Opt-In Enrichment Validation

```text
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

### Diagnostic Validation

```text
diagnostic_lead_snapshot row count = active dummy lead count.
No unknown source quality flags.
completed_calls_missing_fathom_count = 0.
completed_call_fathom_coverage_rate = 100.00.
Money fields are in major-unit EUR in diagnostic snapshot.
```

---

## 17. Step 1 Completion Criteria

Step 1 is complete only when this blueprint is reviewed and approved.

Checklist:

```text
Demo org ID is fixed.
Dataset period is fixed.
Monthly trend is fixed.
Lead count and funnel distribution are fixed.
Source list and source distribution are fixed.
Unknown/missing source is avoided.
Appointment/Fathom rule is fixed.
Fathom story templates are agreed.
Revenue/payment/refund scenarios are defined.
Acquisition/form/UTM plan is defined.
Diagnostic snapshot will be built from base data.
Validation requirements are defined.
```

---

## 18. Next Step Hint

Step 2 should define the exact table relationship map and insert order in detail.

Step 2 should answer:

```text
Which table should be seeded first?
Which columns are required for each table?
Which IDs should be generated and reused?
How do lead outcomes map to statuses, appointments, contracts, payments, and Fathom records?
What cleanup strategy should be used for the dummy org?
What validation SQL should run after seeding?
```

Do not write the seed script until Step 2 is finalized.
