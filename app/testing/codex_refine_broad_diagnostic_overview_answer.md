# Codex Task — Refine Broad Diagnostic Overview Answer Formatting

## Goal

Update diagnostic answer formatting for broad overview questions like:

```text
What's going on?
What should I pay attention to?
Give me a business overview.
What is happening overall?
How is the business doing?
```

The goal is to make these answers clearer and more client-friendly, without breaking existing good answers for funnel-loss questions.

---

## Important Scope

Apply this formatting improvement only to broad overview questions.

Do not globally change every diagnostic answer.

Do not change the existing format for funnel-loss questions that are already working well.

---

## Do Not Change Existing Funnel-Loss Format

Keep the current answer format for questions like:

```text
Where are we losing people in the funnel?
Where are we losing leads?
Where is the funnel leaking?
Where are people dropping off?
Which funnel stage has the biggest drop?
```

Reason:

```text
The current funnel-loss answer format is already working well and should not be changed unless there is a specific bug.
```

---

## Broad Overview Answer Structure

For broad overview questions, use this structure:

```text
1. One-line summary
2. Funnel view table
3. Step conversion view table
4. Source view table with all first sources
5. Short interpretation
6. Recommended next action
7. Revenue/cohort caveat if revenue is mentioned
```

Use tables because broad overview answers compare many metrics.

Do not use tables unnecessarily for simple answers.

---

## Required Correction 1 — Lead-to-Booked-Call Rate

Do not mix distinct lead counts with appointment record counts.

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
445 appointment records / 500 leads = 0.89 appointments per lead
```

That is not the same as lead-to-booked-call conversion rate.

Allowed wording:

```text
405 of 500 leads booked at least one call, so the lead-to-booked-call rate is 81.0%.
```

If mentioning appointment records separately, use:

```text
There were 445 appointment records across 500 leads, equal to 0.89 appointment records per lead.
```

Do not call this 89.0% lead-to-appointment conversion.

---

## Required Correction 2 — Source Quality Wording

Do not say:

```text
194 of 500 leads have a primary source-quality issue.
```

Do not call multiple-source leads a source-quality issue.

The validation passed source-quality checks with zero source-quality failures, so this wording is misleading.

If needed, use softer and more accurate wording:

```text
Some leads have different first and last sources, so source performance should be treated as CRM-side first-source reporting, not ad attribution or multi-touch attribution.
```

Or simply omit this point unless the user asks about source reliability.

Do not say source quality is not clean if the diagnostic source-quality flags are zero.

---

## Required Correction 3 — Show All Sources in Broad Overview

For the current demo dataset, there are only 10 first sources.

For broad overview questions, show all 10 sources instead of only top 5.

Use this heading:

```text
Source view: all first sources, sorted by lifetime net collected
```

Do not use unclear headings like:

```text
Source view: first source
```

Do not show an unexplained subset of sources.

If all sources are shown, do not use wording like:

```text
top sources
selected sources
top group
```

---

## Source View Sorting

Default sorting for broad overview:

```text
Sort all first sources by lifetime net collected descending.
```

If the user specifically asks about volume:

```text
Sort by leads descending.
```

If the user specifically asks about weak conversion:

```text
Sort by completed-to-signed rate ascending or paid conversion rate ascending.
```

For generic:

```text
What's going on?
```

use:

```text
lifetime net collected descending
```

---

## Source View Columns

Use these columns for the broad overview source table:

```text
Source
Leads
Completed calls
Signed contracts
Paid payment records
Lifetime net collected
What it suggests
```

Important wording:

```text
Paid payment records
```

Do not call this:

```text
Paid leads
```

unless the metric is distinct leads with at least one paid payment.

One lead can have more than one payment record, so "paid payment records" is safer.

---

## Source View: All 10 Sources

The output should include all 10 first sources in the current demo dataset:

```text
Google Search
Referral
Webinar
YouTube
Facebook
Instagram
Email Campaign
Calendly
Landing Page
Organic Search
```

The exact order should be determined by lifetime net collected descending from the tool result.

Do not hardcode the order if tool values change.

Do not invent missing metric values.

If any metric is not returned by the diagnostic tool, use:

```text
—
```

---

## Example Corrected Broad Overview Format

Use this as the target style.

```markdown
Overall, the business is generating leads and bookings, but the main leak is after completed calls: too many attended leads are not becoming signed deals.

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

| Step | Leads reached | Dropped from previous | Conversion from previous |
|---|---:|---:|---:|
| Total leads | 500 | — | — |
| Booked a call | 405 | 95 | 81.0% |
| Completed a call | 285 | 120 | 70.37% |
| Signed contract | 135 | 150 | 47.37% |
| Paid / converted | 110 | 25 | 81.48% |

### Source view: all first sources, sorted by lifetime net collected

| Source | Leads | Completed calls | Signed contracts | Paid payment records | Lifetime net collected | What it suggests |
|---|---:|---:|---:|---:|---:|---|
| Google Search | 70 | 45 | 29 | 37 | €83,000.00 | Strong CRM-side revenue yield |
| Referral | 40 | 31 | 24 | 30 | €68,000.00 | Strong conversion quality |
| Webinar | 60 | 39 | 21 | 23 | €50,875.00 | Mid-pack; some cash still outstanding |
| YouTube | 65 | 46 | 16 | 19 | €37,500.00 | Good call volume, weaker signing |
| Facebook | 90 | 43 | 15 | 18 | €36,125.00 | High volume, weaker monetization per lead |
| Instagram | <value> | <value> | <value> | <value> | <value> | Add evidence-based interpretation |
| Email Campaign | <value> | <value> | <value> | <value> | <value> | Add evidence-based interpretation |
| Calendly | <value> | <value> | <value> | <value> | <value> | Add evidence-based interpretation |
| Landing Page | <value> | <value> | <value> | <value> | <value> | Add evidence-based interpretation |
| Organic Search | <value> | <value> | <value> | <value> | <value> | Add evidence-based interpretation |

### What this points to

The biggest bottleneck is post-call sales conversion. 150 leads completed a call but did not sign, which is the largest stuck group and a bigger issue than payment collection.

Attendance is the second major leak. 120 leads booked but did not complete, so the business is also losing a meaningful group before the sales conversation fully happens.

Top-of-funnel volume is not the main problem. 405 of 500 leads booked at least one call, so the lead-to-booked-call rate is 81.0%.

CRM-side first-source performance looks strongest from sources with higher net collected revenue and stronger signed-contract outcomes, while high-volume sources with weaker downstream conversion need review.

### Recommended next action

Focus first on the completed-call to signed-contract stage: review call handling, follow-up, objections, and offer/close process for attended leads who did not sign.

In parallel, tighten booked-call attendance for the booked-not-completed leads with reminder, confirmation, and rescheduling improvements.

Revenue caveat: these revenue and payment values use lead-created cohorts. They show lifetime net collected revenue for leads created in the selected period, not true payment-period revenue.
```

---

## Important Note About Example Values

Do not hardcode the placeholder values in the sample table.

Use actual tool output values.

The sample table shows the desired shape, not fixed source values.

---

## Revenue Caveat Requirement

Whenever diagnostic answers mention revenue, payment, refund, outstanding amount, or net collected values, include this caveat:

```text
Revenue figures here are cohort-based: they show lifetime net collected revenue for leads created in the selected period, not true payment-period revenue.
```

Do not claim:

```text
revenue collected during the period
payments received during the period
true monthly revenue
```

unless the answer is from SQL revenue analytics using `payments.paid_at`.

---

## What Not To Do

Do not:

```text
Do not change the existing funnel-loss question format.
Do not say lead-to-appointment is 89.0% when using 445 appointment records.
Do not call 445 appointment records / 500 leads a conversion rate.
Do not say 194 leads have source-quality issues if source-quality flags are zero.
Do not show only top 5 sources without explaining why.
Do not omit sources when there are only 10 sources.
Do not call paid payment records "paid leads".
Do not invent source metrics.
Do not hardcode source values.
Do not use diagnostic cohort revenue as payment-period revenue.
```

---

## Definition of Done

This task is complete when:

```text
Broad overview answers like "What's going on?" use the improved table-led format.
The lead-to-booked-call rate is correctly shown as 81.0% for 405/500.
Appointment record count is not confused with distinct booked leads.
The source table shows all 10 first sources for the current demo dataset.
The source table heading explains sorting clearly.
Misleading source-quality issue wording is removed.
Existing funnel-loss answers remain unchanged.
Revenue cohort caveat appears when diagnostic money values are mentioned.
```
