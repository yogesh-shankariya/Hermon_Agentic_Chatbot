# UI Question Answerability Audit

Audit date: 2026-05-17

Scope: Streamlit UI question-bank sections only, excluding `Lead 360` and `Diagnostic Analytics` as requested.

UI source: `app/ui/streamlit_app.py` loads the question picker from these CSV files:

- `app/testing/input/multi_skills_analytics_clean_test_questions.csv`
- `app/testing/input/lead_analytics_clean_test_questions.csv`
- `app/testing/input/appointment_analytics_clean_test_questions.csv`
- `app/testing/input/acquisition_analytics_clean_test_questions.csv`
- `app/testing/input/revenue_analytics_clean_test_questions.csv`

Excluded from this audit:

- `app/testing/input/lead_360_clean_test_questions.csv`
- `app/testing/input/diagnostic_analytics_clean_test_questions.csv`

## Executive Summary

| UI section | Questions audited | Legit / answerable | Not demo-safe | Notes |
|---|---:|---:|---:|---|
| Multi Skills Analytics | 35 | 30 | 5 | Lead profile rows are not reliable because the live form question text does not match the skill mapping. |
| Lead Analytics | 147 | 147 | 0 | Supported by live `leads`, `sales_statuses`, and `marketing_sources`. |
| Appointment Analytics | 118 | 118 | 0 | Supported by live appointment and Fathom tables. |
| Acquisition Analytics | 110 | 110 | 0 | Supported by live opt-in, form-answer, and traffic attribution tables. |
| Revenue Analytics | 114 | 113 | 1 | `unmatched_payments` is documented but missing in the live DB. |
| Total | 524 | 518 | 6 | 98.85% of in-scope UI questions are answerable. |

## Do Not Demo Yet

These questions are present in the UI source files, but should not be shown to the client until the noted issue is fixed.

| Question ID | UI section | Question | Expected skill | Why not demo-safe | Fix |
|---|---|---|---|---|---|
| `MSAQ-031` | Multi Skills Analytics | Which profession generated the most leads? | `lead_profile_analytics` | The skill maps profession to exact question `What do you do for work?`, but the live data has 0 answers for that exact text. Current live question text is closer to `What do you currently do for a living?`. | Update `lead_profile_analytics.md` mappings to include the live wording and variants. |
| `MSAQ-032` | Multi Skills Analytics | Which profession submitted the most opt-ins? | `lead_profile_analytics` | Same profession mapping issue. It will likely return empty or `Not provided` despite the raw form data containing similar answers. | Update profession mapping to the live question text. |
| `MSAQ-033` | Multi Skills Analytics | Which employment status is most common? | `lead_profile_analytics` | The skill maps employment status to exact question `What is your employment status?`, but the live data has 0 answers for that exact text. The live form has combined/larger living/work-status questions instead. | Add a supported employment-status extraction/mapping rule or remove this preset. |
| `MSAQ-034` | Multi Skills Analytics | Monthly leads trend by profession. | `lead_profile_analytics` | Same profession mapping issue, compounded over monthly trend output. | Update profession mapping before demo. |
| `MSAQ-035` | Multi Skills Analytics | Monthly leads trend by employment status. | `lead_profile_analytics` | Same employment-status mapping issue. | Add supported mapping/extraction before demo. |
| `RAQ-115` | Revenue Analytics | How many unmatched payments were manually attached? | `revenue_analytics` | The skill references `unmatched_payments`, but the connected live DB does not currently have this table. Silver-truth output also shows `relation "unmatched_payments" does not exist`. | Add/migrate the table and seed data, or remove this preset from the UI. |

Also avoid any older unmatched-payment questions if they are re-added to the UI, such as pending unmatched payment counts, unmatched payment breakdowns, or attached unmatched payment lists. They all depend on the same missing `unmatched_payments` table.

## Legit Answerable UI Question Sets

These groups are supported by both skill descriptions and live table/column availability.

### Lead Analytics

Status: Legit. All `147` UI questions are answerable.

Answerable question IDs: `LAQ-001` through `LAQ-147`.

Supported families:

- Lead counts and date-range lead counts.
- New lead, won, lost, follow-up, appointment-booked, no-show, rescheduled, canceled, unqualified, and partial-payment lead status questions.
- Pipeline role counts, breakdowns, lists, and trends.
- Exact pipeline status ranking and distribution.
- First-touch and last-touch source breakdowns.
- High-level lead source enum questions.
- Source and status cross-breakdowns.
- Owner and setter assignment analysis.
- Missing owner, missing setter, missing status, and missing next-touch-point checks.
- Operational follow-up, overdue follow-up, stale lead, and activity freshness questions.
- Lead creation trends by day, week, month, source, owner, setter, and pipeline role.

Primary live tables:

- `leads`
- `sales_statuses`
- `marketing_sources`

Live data check:

- `leads`: 515 rows
- `sales_statuses`: 10 rows
- `marketing_sources`: 11 rows

### Appointment Analytics

Status: Legit. All `118` UI questions are answerable.

Answerable question IDs: `AAQ-001` through `AAQ-118`.

Supported families:

- Appointment totals, booked calls, upcoming appointments, past appointments, completed/attended calls.
- Appointment lists by schedule window and status.
- Appointment no-show counts and no-show rates.
- No-show breakdowns by event type, host, setter, call category, source, and date range.
- Appointment breakdowns by source, call category, event type, and outcome.
- Host, setter, and event-type performance.
- Fathom coverage for past appointments.
- Appointments missing Fathom records.
- Fathom summaries, action items, objections, key points, and AI rationale.
- Call duration and average call duration analytics.
- AI-suggested Fathom outcomes and applied outcome analysis.
- Fathom matching questions, including unmatched Fathom records.
- Appointment daily, weekly, and monthly trends.

Primary live tables:

- `appointments`
- `appointment_event_types`
- `sales_statuses`
- `leads`
- `fathom_call_records`

Live data check:

- `appointments`: 451 rows
- `appointment_event_types`: 14 rows
- `fathom_call_records`: 93 rows

Demo caveat:

- Fathom questions are answerable, but only 93 Fathom records are present for 451 appointments. Coverage/missing-record answers may show a lot of missing Fathom data, which is valid but should not surprise the presenter.

### Acquisition Analytics

Status: Legit. All `110` UI questions are answerable.

Answerable question IDs: `AQ-001` through `AQ-110`.

Supported families:

- Opt-in and form-submission counts.
- Unique leads from opt-ins.
- Opt-in trends by day, week, and month.
- Opt-in source breakdowns.
- Provider form performance.
- Setter attribution on opt-ins.
- UTM source, medium, campaign, content, and term analysis.
- UTM source plus campaign cross-breakdowns.
- Landing page and referrer performance.
- Traffic attribution coverage.
- Missing UTM, landing page, and referrer checks.
- Form question inventory.
- Form answer distributions.
- Opt-in list questions by UTM, landing page, referrer, provider form, or opt-in source.
- Current lead-status conversion by acquisition attributes.
- First-touch and last-touch opt-in attribution model questions.
- Trend-by-campaign, trend-by-landing-page, trend-by-source, and trend-by-form questions.

Primary live tables:

- `opt_ins`
- `opt_in_question_answers`
- `traffic_attributions`
- `leads`
- `sales_statuses`

Live data check:

- `opt_ins`: 750 rows
- `opt_in_question_answers`: 2,855 rows
- `traffic_attributions`: 180 rows

Demo caveat:

- Attribution coverage questions are answerable, but the live data has traffic attribution for only 180 of 750 opt-ins. Missing-attribution answers may look high because that is what the current data says.

### Revenue Analytics

Status: Mostly legit. `113` of `114` current UI questions are answerable.

Answerable question IDs:

- `RAQ-001` through `RAQ-108`
- `RAQ-117` through `RAQ-121`

The current UI CSV skips `RAQ-109` through `RAQ-114` and `RAQ-116`.

Not answerable:

- `RAQ-115`

Supported families:

- Net collected revenue and gross paid revenue totals.
- Revenue date ranges and revenue trends.
- Payment status, payment type, provider, currency, failed, lost, due-soon, overdue, outstanding, and paid-payment questions.
- Contract status, contract type, signed value, signed rate, sent-to-signed rate, closer performance, setter performance, and program performance.
- Refund totals, refund rates, failed/initiated/succeeded refunds.
- Invoice counts, invoice status breakdowns, invoice amount breakdowns, payments with invoices, and payments missing invoices.
- Payment link counts, status breakdowns, active/used/invalid links, and missing links.
- Payment proof coverage and lists.
- Subscription counts, MRR, past-due/cancellation scheduled subscriptions, next billing dates, and subscription checkout link status.
- Source-attributed net revenue, gross paid revenue, signed contract value, and high-level lead source category revenue.

Primary live tables:

- `programs`
- `contracts`
- `contract_subscriptions`
- `subscription_checkout_links`
- `payments`
- `payment_links`
- `payment_proofs`
- `refunds`
- `invoices`
- `leads`
- `marketing_sources`

Live data check:

- `programs`: 5 rows
- `contracts`: 181 rows
- `payments`: 261 rows
- `payment_links`: 199 rows
- `payment_proofs`: 22 rows
- `refunds`: 1 row
- `invoices`: 0 rows
- `contract_subscriptions`: 0 rows
- `subscription_checkout_links`: 0 rows
- `unmatched_payments`: missing table

Demo caveats:

- Invoice questions are answerable, but the current data has 0 invoices. Expect zero/empty invoice answers.
- Subscription and subscription checkout questions are answerable, but the current data has 0 subscriptions and 0 subscription checkout links. Expect zero/empty subscription answers.
- Refund questions are answerable, but the current data has only 1 refund. Refund rate and refund breakdowns may be very small.
- Unmatched-payment questions are not answerable because the table is missing.

### Multi Skills Analytics

Status: Mostly legit. `30` of `35` current UI questions are answerable.

Answerable question IDs:

- `MSAQ-001` through `MSAQ-030`

Not answerable:

- `MSAQ-031`
- `MSAQ-032`
- `MSAQ-033`
- `MSAQ-034`
- `MSAQ-035`

Supported families:

- Source-attributed revenue.
- Source-attributed signed contract value.
- Source-attributed refunds.
- Appointment count by lead source.
- No-show rate by lead source.
- Fathom coverage by lead source.
- Won leads by UTM campaign.
- Won lead rate by landing page.
- Opt-ins by current lead status.
- Lead source ranking and distribution.
- Pipeline status and role counts.
- Operational follow-up.
- Lead owner and setter breakdowns.
- Lead trends.
- Appointment counts and appointment breakdowns.
- No-show analytics.
- Host analytics.
- Payment breakdowns.
- Payment provider revenue.
- Program revenue.
- Contract status.
- UTM campaign performance.

Do not demo yet:

- Lead profile questions about profession or employment status, until the form-question mapping is fixed.

## Client-Safe Demo Shortlist

These are high-confidence examples from the current UI question bank.

| Question ID | Question |
|---|---|
| `LAQ-001` | How many active leads do we have? |
| `LAQ-011` | How many won leads do we have? |
| `LAQ-034` | Which pipeline role has the most leads? |
| `LAQ-063` | Show leads by owner. |
| `LAQ-090` | Which leads have overdue next touch points? |
| `LAQ-127` | Show monthly lead growth from 2025-05-01 to 2026-05-01. |
| `AAQ-001` | How many appointments do we have in total? |
| `AAQ-015` | What is the appointment no-show rate? |
| `AAQ-055` | What is the Fathom coverage for past appointments? |
| `AAQ-116` | Which calls mention objections in the Fathom record? |
| `AQ-001` | How many opt-ins do we have in total? |
| `AQ-021` | Which provider form has the most submissions? |
| `AQ-036` | Which UTM campaign generated the most opt-ins? |
| `AQ-073` | What questions are being asked across opt-in forms? |
| `AQ-088` | Show won leads by UTM campaign. |
| `RAQ-001` | How much net collected revenue have we collected so far? |
| `RAQ-009` | Show the monthly net revenue trend from 2025-05-01 to 2026-05-01. |
| `RAQ-026` | Which payment provider collected the most revenue? |
| `RAQ-056` | Which closer has the highest signed contract value? |
| `RAQ-117` | Which source generated the most net collected revenue? |
| `MSAQ-001` | Show revenue by source. |
| `MSAQ-005` | Show appointment count by lead source. |
| `MSAQ-008` | Show won leads by UTM campaign. |
| `MSAQ-016` | How many leads need follow-up? |
| `MSAQ-025` | Show revenue by payment provider. |

## Out Of Scope For Current Skills

These are not necessarily in the current UI picker, but they are likely client follow-ups that should be treated as unsupported unless new skills/tables are added.

- Cost per lead, cost per appointment, cost per sale, ROAS, ad spend, Facebook Ads, YouTube analytics, Hyros, Airtable, Zoom, webinar platform data.
- Revenue by UTM campaign, landing page, referrer, provider form, or form-answer source. Revenue by normalized lead source is supported, but revenue by raw acquisition attribution is not.
- Raw webhook payloads, API keys, provider credentials, raw provider payloads, or connection debugging.
- Write/admin actions such as updating payments, deleting leads, changing statuses, or editing records.
- Broad semantic theme discovery across long call transcripts or long form answers using only SQL. The appointment skill can count/list existing Fathom fields, but deeper semantic analysis needs a semantic context/retrieval flow.

## Recommended Fixes Before Client Demo

1. Remove or hide `RAQ-115` from the Revenue Analytics UI picker until `unmatched_payments` exists in the connected DB.
2. Update `lead_profile_analytics.md` to map live profession/work wording, especially `What do you currently do for a living?` and the longer variant that includes working status.
3. Decide whether employment-status questions should be supported by parsing the current combined question text, adding a clean form field, or removing those presets.
4. Add a small UI note or internal demo script caveat for invoice/subscription questions, because those are valid but currently return zero/empty answers.
5. If old unmatched-payment presets `RAQ-109` through `RAQ-116` are reintroduced, keep them hidden until the missing table issue is fixed.
