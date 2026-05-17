# Codex Task — Final Corrections for Broad Diagnostic Overview Answer

## Context

The current broad diagnostic answer for questions like:

```text
What's going on?
What is happening overall?
Give me a business overview.
What should I pay attention to?
How is the business doing?
```

is mostly good, but a few improvements are required before client demo.

This task applies only to broad diagnostic overview answers.

Do not change the existing format for funnel-loss questions like:

```text
Where are we losing people in the funnel?
Where are we losing leads?
Where is the funnel leaking?
Which funnel stage has the biggest drop?
```

Those funnel-loss answers are already working well and should remain unchanged unless there is a specific bug.

---

## Required Corrections

Apply these corrections:

```text
1. Add Drop rate from previous to the Step conversion view table.
2. Make source table heading future-safe: use top 10/all returned first sources, not unconditional "all sources".
3. Clarify source table record-count columns.
4. Prefer adding distinct source-level lead counts in diagnostic_tools.py.
5. Avoid unsupported source interpretation text unless the metric is shown.
6. Keep the 81.0% lead-to-booked-call correction.
7. Keep the cohort revenue caveat when diagnostic money values are shown.
```

---

## 1. Add Drop Rate to Step Conversion View

### Current Table

The current broad overview step table is:

```text
| Step | Leads reached | Dropped from previous | Conversion from previous |
|---|---:|---:|---:|
```

### Required New Table

Change it to:

```text
| Step | Leads reached | Dropped from previous | Drop rate from previous | Conversion from previous |
|---|---:|---:|---:|---:|
```

### Use Existing Tool Fields

Use values already returned by `get_diagnostic_funnel_snapshot.funnel_flow`:

```text
leads_reached
dropped_from_previous
drop_rate_from_previous
conversion_rate_from_previous
```

Do not invent or recalculate these values if the tool already returns them.

### Expected Example for Current Demo Data

```text
| Step | Leads reached | Dropped from previous | Drop rate from previous | Conversion from previous |
|---|---:|---:|---:|---:|
| Total leads | 500 | — | — | — |
| Booked a call | 405 | 95 | 19.0% | 81.0% |
| Completed a call | 285 | 120 | 29.63% | 70.37% |
| Signed contract | 135 | 150 | 52.63% | 47.37% |
| Paid / converted | 110 | 25 | 18.52% | 81.48% |
```

### Important Rules

```text
Drop rate from previous + Conversion from previous should be approximately 100%.
Do not show drop rate for Total leads; use —.
This table is based on funnel_flow.
Do not confuse this with the mutually exclusive final-stage funnel table.
```

---

## 2. Keep Funnel View as Mutually Exclusive Final-Stage Table

For broad overview answers, keep the first funnel table as the final-stage view from:

```text
get_diagnostic_funnel_snapshot.stuck_group_funnel
```

Table format:

```text
| Funnel stage | Leads | What this means |
|---|---:|---|
```

Current demo values should remain:

```text
Never booked a call = 95
Booked but did not complete call = 120
Completed call but did not sign = 150
Signed but not paid = 25
Paid / converted = 110
Total = 500
```

The total must equal:

```text
95 + 120 + 150 + 25 + 110 = 500
```

Do not mix activity record counts into this table.

---

## 3. Keep Correct Lead-to-Booked-Call Rate

Do not reintroduce the earlier 89.0% mistake.

Correct metric:

```text
Lead-to-booked-call rate = distinct leads with at least one appointment / total leads
```

For current demo data:

```text
405 booked leads / 500 total leads = 81.0%
```

Do not say:

```text
Lead-to-appointment rate = 89.0%
```

because:

```text
445 appointment records / 500 leads = 0.89 appointment records per lead
```

That is not a conversion rate.

Allowed wording:

```text
405 of 500 leads booked at least one call, so the lead-to-booked-call rate is 81.0%.
```

If mentioning appointment records separately, say:

```text
There were 445 appointment records across 500 leads, equal to 0.89 appointment records per lead.
```

---

## 4. Source View Heading Must Be Future-Safe

Current broad answer used:

```text
Source view: all first sources, sorted by lifetime net collected
```

This is okay only when the tool returns all sources. But the diagnostic source tool has a limit, so future live data may have more than 10 sources.

### Required Heading

Use:

```text
Source view: top 10 first sources, sorted by lifetime net collected
```

If the tool metadata confirms that all returned sources are all available sources, then it is acceptable to say:

```text
Source view: all first sources, sorted by lifetime net collected
```

### Current Demo Rule

For the current demo dataset, there are 10 first sources. Since the source tool limit is 10, the top 10 means all demo sources.

Do not say “all sources” unless either:

```text
total_distinct_sources <= returned_source_count
```

or the tool explicitly confirms `is_truncated = false`.

---

## 5. Add Source Snapshot Metadata in diagnostic_tools.py

Update `get_diagnostic_source_snapshot` to include metadata so the assistant does not have to guess whether rows are truncated.

Add these fields to the tool response:

```text
requested_limit
returned_source_count
source_sort
source_selection_note
```

Recommended values:

```python
"requested_limit": safe_limit
"returned_source_count": len(rows)
"source_sort": "net_collected_amount DESC, signed_contract_count DESC, completed_call_count DESC, lead_count DESC, source_name ASC"
"source_selection_note": "Rows are limited by the requested limit and sorted by lifetime net collected."
```

If possible, also add:

```text
total_distinct_sources
is_truncated
```

Recommended logic:

```text
total_distinct_sources = count distinct source_name for the selected org/date/source_basis
is_truncated = total_distinct_sources > returned_source_count
```

Then the model can safely choose heading:

```text
if is_truncated:
    Source view: top 10 first sources, sorted by lifetime net collected
else:
    Source view: all first sources, sorted by lifetime net collected
```

---

## 6. Clarify Source Table Record Counts

Current source table columns:

```text
Completed calls
Signed contracts
Paid payment records
```

The source snapshot currently sums these fields from `diagnostic_lead_snapshot`:

```text
completed_call_count
signed_contract_count
paid_payment_count
```

These can behave like activity/record counts, especially `paid_payment_count`.

To avoid client confusion, use clearer labels:

```text
Completed-call records
Signed-contract records
Paid payment records
```

Do not call `paid_payment_count`:

```text
Paid leads
```

unless the tool returns distinct leads with at least one paid payment.

---

## 7. Preferred Tool Improvement — Add Distinct Source-Level Lead Counts

This is strongly recommended.

Add distinct lead-level source metrics to `SOURCE_SNAPSHOT_SQL_TEMPLATE`.

### Add Fields

For each source, calculate:

```text
booked_lead_count = COUNT(*) FILTER (WHERE appointment_count > 0)
completed_call_lead_count = COUNT(*) FILTER (WHERE completed_call_count > 0)
signed_lead_count = COUNT(*) FILTER (WHERE signed_contract_count > 0)
paid_lead_count = COUNT(*) FILTER (WHERE paid_payment_count > 0)
```

`booked_lead_count` already exists in the SQL, but add and expose the others.

### Add Lead-Based Conversion Rates

Add:

```text
lead_to_completed_call_rate = completed_call_lead_count / lead_count
completed_lead_to_signed_lead_rate = signed_lead_count / completed_call_lead_count
signed_lead_to_paid_lead_rate = paid_lead_count / signed_lead_count
paid_lead_rate = paid_lead_count / lead_count
```

Use safe division with `NULLIF`.

Example SQL expressions:

```sql
COUNT(*) FILTER (WHERE completed_call_count > 0)::int AS completed_call_lead_count,
COUNT(*) FILTER (WHERE signed_contract_count > 0)::int AS signed_lead_count,
COUNT(*) FILTER (WHERE paid_payment_count > 0)::int AS paid_lead_count,

ROUND(
  100.0 * COUNT(*) FILTER (WHERE completed_call_count > 0)
  / NULLIF(COUNT(*), 0),
  2
) AS lead_to_completed_call_rate,

ROUND(
  100.0 * COUNT(*) FILTER (WHERE signed_contract_count > 0)
  / NULLIF(COUNT(*) FILTER (WHERE completed_call_count > 0), 0),
  2
) AS completed_lead_to_signed_lead_rate,

ROUND(
  100.0 * COUNT(*) FILTER (WHERE paid_payment_count > 0)
  / NULLIF(COUNT(*) FILTER (WHERE signed_contract_count > 0), 0),
  2
) AS signed_lead_to_paid_lead_rate,

ROUND(
  100.0 * COUNT(*) FILTER (WHERE paid_payment_count > 0)
  / NULLIF(COUNT(*), 0),
  2
) AS paid_lead_rate
```

### Preferred Business Table Columns After Tool Update

Once these distinct metrics are available, prefer this source table for broad overview:

```text
Source
Leads
Booked leads
Completed-call leads
Signed-contract leads
Paid leads
Lifetime net collected
What it suggests
```

This is cleaner for business users than record-count columns.

### If Tool Is Not Updated Yet

If distinct lead metrics are not available yet, use the safer record-count labels:

```text
Source
Leads
Completed-call records
Signed-contract records
Paid payment records
Lifetime net collected
What it suggests
```

---

## 8. Do Not Make Unsupported Source Claims

Do not include interpretations that rely on metrics not shown or not returned.

Avoid statements like:

```text
Weak attendance/completion
Weak booking
Sizable outstanding amount
```

unless the table/tool output includes the relevant evidence.

For example:

```text
Calendly: Weak attendance/completion
```

requires evidence such as:

```text
booked_lead_count
appointment_count
completed_call_count
appointment_to_completed_rate
```

If those fields are not shown, use safer wording:

```text
Lower completed-call and signed-contract volume
```

Similarly:

```text
Instagram: sizable outstanding amount
```

requires `outstanding_amount` shown or explicitly returned and referenced.

If outstanding amount is not displayed, use:

```text
Moderate volume but lower collected revenue than stronger sources
```

### Safer Source Interpretation Examples

Use evidence-based interpretation:

```text
Google Search -> Strong CRM-side revenue yield
Referral -> Strong conversion quality
Webinar -> Mid-pack revenue contribution
YouTube -> Good completed-call volume, weaker signing
Facebook -> High volume, weaker monetization per lead
Instagram -> Moderate volume and lower collected revenue than stronger sources
Email Campaign -> Smaller volume with decent revenue contribution
Calendly -> Lower completed-call and signed-contract volume
Organic Search -> Low volume and weak downstream conversion
Landing Page -> Weak downstream conversion in this snapshot
```

Do not call a source “bad” or “low quality” unless the metrics clearly support it.

Prefer:

```text
weaker downstream conversion
needs review
lower collected revenue
lower signed-contract outcome
```

over:

```text
bad source
low-quality source
poor channel
```

---

## 9. Source Quality Wording

Do not say:

```text
194 of 500 leads have a primary source-quality issue.
```

Do not call multiple-source leads a source-quality issue.

Multiple-source leads mean first source and last source differ for some leads. This is a CRM-side reporting caveat, not automatically a data-quality failure.

Only mention source quality caveats when:

```text
the user asks about source trust
source quality tool shows actual low confidence/unknown/orphaned source issues
source quality materially affects the answer
```

If needed, say:

```text
Some leads have different first and last sources, so this should be treated as CRM-side first-source reporting, not ad attribution or multi-touch attribution.
```

Do not say source quality is not clean when diagnostic source-quality failures are zero.

---

## 10. Broad Overview Answer Structure

For broad overview questions, use this structure:

```text
1. One-line summary
2. Funnel view table
3. Step conversion view table with drop rate
4. Source view table
5. What this points to
6. Recommended next action
7. Revenue cohort caveat if money is mentioned
```

### Broad Overview Target Shape

```markdown
Overall, the business is generating leads and booked calls, but the biggest leak is after completed calls: too many leads attend and then do not sign.

### Funnel view

| Funnel stage | Leads | What this means |
|---|---:|---|
| Never booked a call | 95 | Leads did not reach the appointment stage |
| Booked but did not complete call | 120 | Leads booked a call but did not attend/complete it |
| Completed call but did not sign | 150 | Leads attended the call but did not move to signed contract |
| Signed but not paid | 25 | Leads signed but payment was not completed |
| Paid / converted | 110 | Leads completed the paid conversion path |
| Total | 500 | Must equal the sum of all rows above |

### Step conversion view

| Step | Leads reached | Dropped from previous | Drop rate from previous | Conversion from previous |
|---|---:|---:|---:|---:|
| Total leads | 500 | — | — | — |
| Booked a call | 405 | 95 | 19.0% | 81.0% |
| Completed a call | 285 | 120 | 29.63% | 70.37% |
| Signed contract | 135 | 150 | 52.63% | 47.37% |
| Paid / converted | 110 | 25 | 18.52% | 81.48% |

### Source view: top 10 first sources, sorted by lifetime net collected

| Source | Leads | Completed-call records | Signed-contract records | Paid payment records | Lifetime net collected | What it suggests |
|---|---:|---:|---:|---:|---:|---|
| <source> | <value> | <value> | <value> | <value> | <value> | <evidence-based interpretation> |

### What this points to

<Short interpretation based on the funnel and source evidence.>

### Recommended next action

<1-2 practical actions.>

Revenue figures here are cohort-based: they show lifetime net collected revenue for leads created in the selected period, not true payment-period revenue.
```

If distinct source-level lead metrics are added, replace the source table with:

```text
Source
Leads
Booked leads
Completed-call leads
Signed-contract leads
Paid leads
Lifetime net collected
What it suggests
```

---

## 11. Revenue Caveat

Whenever diagnostic answers mention revenue, payment, refund, outstanding, or net collected values, include this exact caveat:

```text
Revenue figures here are cohort-based: they show lifetime net collected revenue for leads created in the selected period, not true payment-period revenue.
```

Do not say:

```text
revenue collected during the month
payments received during the month
true monthly revenue
```

unless the answer comes from SQL revenue analytics using `payments.paid_at`.

---

## 12. What Not To Do

Do not:

```text
Do not change existing funnel-loss answers that are already working well.
Do not show lead-to-appointment as 89.0% when using appointment records.
Do not call appointment records per lead a conversion rate.
Do not say all sources if the source tool returns a limited top 10 and there may be more.
Do not show only top 5 sources for broad overview.
Do not call paid payment records paid leads.
Do not make source interpretation claims from metrics that are not shown or returned.
Do not say multiple-source leads are source-quality failures.
Do not claim diagnostic cohort revenue is true payment-period revenue.
Do not invent source values.
Do not hardcode source order.
```

---

## 13. Definition of Done

This task is complete when:

```text
Broad overview answers include drop rate in the Step conversion view.
Lead-to-booked-call rate remains 81.0% for 405/500.
Source table heading is future-safe: top 10/all returned first sources as appropriate.
Source table labels record counts accurately unless distinct lead metrics are added.
Source snapshot tool includes metadata about limit/sort/truncation.
Preferably, source snapshot tool includes distinct lead-level source counts and lead-based conversion rates.
Source interpretation text only uses evidence returned/shown.
Source-quality issue wording does not incorrectly count multiple-source leads as data-quality failures.
Revenue cohort caveat appears when diagnostic money is mentioned.
Existing funnel-loss answer format remains unchanged.
```
