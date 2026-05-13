# Codex Task: Improve Diagnostic Funnel Output for User-Friendly Answers

## Goal

Improve the diagnostic funnel answer so business users can clearly understand:

```text
How many leads entered the funnel
How many reached each step
How many dropped at each step
Where the biggest leak is
What action should be taken next
```

Current issue:

The diagnostic answer is showing final funnel-stage buckets such as:

```text
Lead Only
Booked Not Completed
Completed Not Signed
Signed Not Paid
Converted Paid
```

This is useful, but it does not show a clear step-by-step funnel journey.

Business users expect a flow like:

```text
Total leads
  -> Booked a call
  -> Completed a call
  -> Signed contract
  -> Paid / converted
```

Therefore, update the diagnostic funnel tool output and diagnostic answer instructions.

---

## Files To Update

Update:

```text
app/tools/diagnostic_tools.py
app/skills/modules/diagnostic_analytics.md
tests/test_diagnostic_tools.py
tests/test_orchestrator.py or nearest diagnostic test file if needed
```

Do not update:

```text
diagnostic_lead_snapshot builder
SQL analytics agent
Lead 360 agent
router logic unless existing tests require it
database schema
```

---

## Important Scope

This change is only for diagnostic funnel readability.

Do not add:

```text
free-form SQL generation
new database tables
diagnostic_text_insights
LLM text extraction
vector search
admin rebuild tools
snapshot refresh tools
```

---

## Core Design Change

For `get_diagnostic_funnel_snapshot`, return three separate sections:

```text
funnel_flow
final_position_breakdown
activity_counts
```

### 1. `funnel_flow`

This is the main business-facing funnel movement.

It must use unique lead counts, not activity record counts.

Steps:

```text
Total leads
Booked a call
Completed a call
Signed contract
Paid / converted
```

### 2. `final_position_breakdown`

This is the current existing stage/bucket view.

Examples:

```text
Lead Only
Booked Not Completed
Completed Not Signed
Signed Not Paid
Paid
Lost
Unqualified
Refunded
```

This explains where leads finally ended up.

### 3. `activity_counts`

This is supporting context only.

Examples:

```text
appointment records
completed call records
no-show records
signed contract records
paid payment records
```

Important: These are not unique-lead funnel steps. They must not be mixed into the main funnel flow.

---

## Why This Matters

Do not mix different grains in the main funnel table.

Bad:

```text
515 leads
451 appointments
294 completed calls
136 signed contracts
158 paid payments
```

Reason this is bad:

```text
515 leads = unique leads
451 appointments = appointment records
158 paid payments = payment records
```

This can confuse the user.

Good:

```text
515 leads
418 leads booked a call
294 leads completed a call
136 leads signed
135 leads paid / converted
```

This is a consistent unique-lead funnel.

---

## Funnel Flow Logic

Use these unique-lead definitions from `diagnostic_lead_snapshot`:

```text
total_leads = COUNT(*)

booked_leads =
COUNT(*) WHERE appointment_count > 0

completed_call_leads =
COUNT(*) WHERE completed_call_count > 0

signed_leads =
COUNT(*) WHERE signed_contract_count > 0

paid_leads =
COUNT(*) WHERE net_collected_amount > 0
OR paid_payment_count > 0
```

Use this order:

```text
Total leads
Booked a call
Completed a call
Signed contract
Paid / converted
```

For each step after the first, calculate:

```text
dropped_from_previous = previous_step_leads - current_step_leads
drop_rate_from_previous = dropped_from_previous / previous_step_leads * 100
conversion_rate_from_previous = current_step_leads / previous_step_leads * 100
```

If previous step count is zero:

```text
drop_rate_from_previous = null
conversion_rate_from_previous = null
```

---

## SQL Guidance For `funnel_flow`

Update `FUNNEL_SQL` or add a new CTE section to produce cumulative funnel flow.

Use explicit columns only.

Do not use:

```sql
SELECT *
dls.*
```

Example SQL pattern:

```sql
WITH scoped AS (
  SELECT
    dls.lead_id,
    dls.appointment_count,
    dls.completed_call_count,
    dls.signed_contract_count,
    dls.paid_payment_count,
    dls.net_collected_amount,
    dls.no_show_count,
    dls.funnel_stage,
    dls.conversion_outcome
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
funnel_counts AS (
  SELECT
    COUNT(*)::int AS total_leads,
    COUNT(*) FILTER (WHERE appointment_count > 0)::int AS booked_leads,
    COUNT(*) FILTER (WHERE completed_call_count > 0)::int AS completed_call_leads,
    COUNT(*) FILTER (WHERE signed_contract_count > 0)::int AS signed_leads,
    COUNT(*) FILTER (
      WHERE net_collected_amount > 0
         OR paid_payment_count > 0
    )::int AS paid_leads
  FROM scoped
),
funnel_steps AS (
  SELECT
    1 AS step_order,
    'total_leads' AS step_key,
    'Total leads' AS step_label,
    total_leads AS leads_reached,
    NULL::int AS previous_step_leads
  FROM funnel_counts

  UNION ALL
  SELECT
    2,
    'booked_call',
    'Booked a call',
    booked_leads,
    total_leads
  FROM funnel_counts

  UNION ALL
  SELECT
    3,
    'completed_call',
    'Completed a call',
    completed_call_leads,
    booked_leads
  FROM funnel_counts

  UNION ALL
  SELECT
    4,
    'signed_contract',
    'Signed contract',
    signed_leads,
    completed_call_leads
  FROM funnel_counts

  UNION ALL
  SELECT
    5,
    'paid_converted',
    'Paid / converted',
    paid_leads,
    signed_leads
  FROM funnel_counts
)
SELECT
  step_order,
  step_key,
  step_label,
  leads_reached,
  CASE
    WHEN previous_step_leads IS NULL THEN NULL
    ELSE GREATEST(previous_step_leads - leads_reached, 0)
  END AS dropped_from_previous,
  CASE
    WHEN previous_step_leads IS NULL OR previous_step_leads = 0 THEN NULL
    ELSE ROUND(
      100.0 * GREATEST(previous_step_leads - leads_reached, 0) / previous_step_leads,
      2
    )
  END AS drop_rate_from_previous,
  CASE
    WHEN previous_step_leads IS NULL OR previous_step_leads = 0 THEN NULL
    ELSE ROUND(100.0 * leads_reached / previous_step_leads, 2)
  END AS conversion_rate_from_previous
FROM funnel_steps
ORDER BY step_order
```

---

## Final Position Breakdown Logic

Keep the existing final-stage breakdown, but rename labels to user-friendly language.

Raw values may be:

```text
lead_only
booked_not_completed
completed_not_signed
signed_not_paid
paid
lost
unqualified
refunded
```

Business-facing labels must be:

```text
lead_only -> Never booked a call
booked_not_completed -> Booked but did not complete call
completed_not_signed -> Completed call but did not sign
signed_not_paid -> Signed but not paid
paid -> Paid / converted
lost -> Lost
unqualified -> Unqualified
refunded -> Refunded
```

The tool can return raw `funnel_stage`, but the prompt should tell the agent to display readable labels.

Recommended output fields:

```text
funnel_stage
display_label
lead_count
pct_of_total_leads
net_collected_amount
interpretation_hint
```

---

## Activity Counts Logic

Return supporting activity counts separately.

Use these fields:

```text
appointment_count
completed_call_count
no_show_count
signed_contract_count
paid_payment_count
```

Recommended response section:

```json
"activity_counts": {
  "appointment_records": 451,
  "completed_call_records": 294,
  "no_show_records": 54,
  "signed_contract_records": 136,
  "paid_payment_records": 158
}
```

These are useful for context, but must not be used as the primary step-by-step funnel unless clearly labelled as records.

---

## Recommended Tool Response Shape

Update `get_diagnostic_funnel_snapshot` to return this shape:

```json
{
  "status": "success",
  "tool": "get_diagnostic_funnel_snapshot",
  "scope_note": "This diagnostic snapshot uses lead_created_at cohort logic. Revenue and payment fields are lifetime outcomes for leads created in the selected period, not true payment-period revenue.",
  "period": {
    "start_date": "2025-10-25",
    "end_date": "2026-04-25",
    "display_start_date": "2025-10-25",
    "display_end_date": "2026-04-24",
    "date_field": "lead_created_at",
    "date_range_display": "25 Oct 2025 to 24 Apr 2026"
  },
  "funnel_flow": [
    {
      "step_order": 1,
      "step_key": "total_leads",
      "step_label": "Total leads",
      "leads_reached": 515,
      "dropped_from_previous": null,
      "drop_rate_from_previous": null,
      "conversion_rate_from_previous": null
    },
    {
      "step_order": 2,
      "step_key": "booked_call",
      "step_label": "Booked a call",
      "leads_reached": 418,
      "dropped_from_previous": 97,
      "drop_rate_from_previous": 18.83,
      "conversion_rate_from_previous": 81.17
    },
    {
      "step_order": 3,
      "step_key": "completed_call",
      "step_label": "Completed a call",
      "leads_reached": 294,
      "dropped_from_previous": 124,
      "drop_rate_from_previous": 29.67,
      "conversion_rate_from_previous": 70.33
    },
    {
      "step_order": 4,
      "step_key": "signed_contract",
      "step_label": "Signed contract",
      "leads_reached": 136,
      "dropped_from_previous": 158,
      "drop_rate_from_previous": 53.74,
      "conversion_rate_from_previous": 46.26
    },
    {
      "step_order": 5,
      "step_key": "paid_converted",
      "step_label": "Paid / converted",
      "leads_reached": 135,
      "dropped_from_previous": 1,
      "drop_rate_from_previous": 0.74,
      "conversion_rate_from_previous": 99.26
    }
  ],
  "final_position_breakdown": [
    {
      "funnel_stage": "booked_not_completed",
      "display_label": "Booked but did not complete call",
      "lead_count": 122,
      "pct_of_total_leads": 23.69,
      "interpretation_hint": "Largest visible stuck group"
    }
  ],
  "activity_counts": {
    "appointment_records": 451,
    "completed_call_records": 294,
    "no_show_records": 54,
    "signed_contract_records": 136,
    "paid_payment_records": 158
  },
  "row_count": 515
}
```

Keep backwards compatibility if possible by also returning `rows`, but the diagnostic prompt should prefer:

```text
funnel_flow
final_position_breakdown
activity_counts
```

---

## Business-Friendly Date Display

Diagnostic tools use exclusive `end_date` internally:

```text
lead_created_at >= start_date
lead_created_at < end_date
```

This is correct and should stay.

But do not show users:

```text
up to but not including 2026-04-25
```

That sounds too technical.

Instead, display the period as inclusive by subtracting one day from `end_date`.

Example:

```text
Tool period:
start_date = 2025-10-25
end_date = 2026-04-25

Business-facing display:
For leads created between 25 Oct 2025 and 24 Apr 2026...
```

Add these fields to the period metadata:

```text
display_start_date = start_date
display_end_date = end_date - 1 day
date_range_display = formatted display_start_date to display_end_date
```

Use this wording in final answers:

```text
For leads created between 25 Oct 2025 and 24 Apr 2026...
```

Do not use:

```text
up to but not including
exclusive end date
end boundary
```

in business-facing answers.

---

## Diagnostic Prompt Update

Update `app/skills/modules/diagnostic_analytics.md`.

Add or replace the funnel answer section with the following:

```markdown
## Funnel Answer Format

For funnel leakage questions, always show the step-by-step funnel movement first.

Use `funnel_flow` from `get_diagnostic_funnel_snapshot` when available.

The main funnel movement must use unique lead counts, not record counts.

Use this order:

1. Total leads
2. Booked a call
3. Completed a call
4. Signed contract
5. Paid / converted

Show this table first:

| Funnel step | Leads reached | Dropped from previous step | Drop % | Conversion % |
|---|---:|---:|---:|---:|

After that, optionally show the final-position breakdown:

| Final funnel position | Leads | % of total leads | What it means |
|---|---:|---:|---|

Use user-friendly labels:
- `lead_only` -> Never booked a call
- `booked_not_completed` -> Booked but did not complete call
- `completed_not_signed` -> Completed call but did not sign
- `signed_not_paid` -> Signed but not paid
- `paid` -> Paid / converted
- `lost` -> Lost
- `unqualified` -> Unqualified
- `refunded` -> Refunded

Do not mix activity record counts into the main funnel flow.

Activity counts such as appointment records, completed call records, no-show records, signed contract records, and paid payment records may be mentioned only as supporting context.

Use business-friendly dates.

Diagnostic tools use exclusive `end_date` internally, but final answers must display the period as inclusive by using one day before the exclusive `end_date`.

Do not say:
"up to but not including <end_date>"

Say:
"For leads created between <display_start_date> and <display_end_date>..."
```

---

## User-Friendly Example Answer

Use this as the target answer style.

```text
The biggest funnel leak is around call attendance. Many leads book a call, but a large group does not complete it.

For leads created between 25 Oct 2025 and 24 Apr 2026, 515 leads entered the funnel.

| Funnel step | Leads reached | Dropped from previous step | Drop % | Conversion % |
|---|---:|---:|---:|---:|
| Total leads | 515 | - | - | - |
| Booked a call | 418 | 97 | 18.83% | 81.17% |
| Completed a call | 294 | 124 | 29.67% | 70.33% |
| Signed contract | 136 | 158 | 53.74% | 46.26% |
| Paid / converted | 135 | 1 | 0.74% | 99.26% |

What this means:
The largest step drop is from completed calls to signed contracts, where 158 leads dropped. The next major leak is from booked calls to completed calls, where 124 leads dropped.

Final funnel position:

| Final funnel position | Leads | % of total leads | What it means |
|---|---:|---:|---|
| Booked but did not complete call | 122 | 23.69% | Largest visible stuck group |
| Never booked a call | 97 | 18.83% | Leads did not reach the call stage |
| Completed call but did not sign | 87 | 16.89% | Post-call conversion needs review |
| Signed but not paid | 2 | 0.39% | Payment collection after signing is not the main issue |
| Paid / converted | 135 | 26.21% | Converted group |

Confidence:
High — the funnel pattern is clear across 515 leads.

Data quality note:
This is based on leads created in the selected period. Revenue and payment values, if shown, are lifetime outcomes for those leads, not revenue collected during that period.

Recommended next action:
Review the completed-call-but-not-signed group first to understand what is blocking signing after calls. Also review the booked-but-not-completed group to improve reminders, confirmation messages, show-up process, and follow-up speed.
```

---

## Interpretation Rules

When identifying the biggest leak, prefer the highest `dropped_from_previous` in `funnel_flow`.

Example:

```text
If completed_call -> signed_contract has the highest dropped_from_previous,
say the biggest step drop is post-call signing.
```

But also mention the largest final-position bucket if different.

Example:

```text
The biggest step drop is from completed call to signed contract, but the largest visible stuck group is booked but did not complete call.
```

This is more accurate than saying only one of them.

---

## Wording Rules

Use business-friendly wording.

Prefer:

```text
Never booked a call
Booked but did not complete call
Completed call but did not sign
Signed but not paid
Paid / converted
```

Avoid:

```text
lead_only
booked_not_completed
completed_not_signed
signed_not_paid
converted_paid
exclusive end date
up to but not including
```

Prefer:

```text
What this means
Recommended next action
Final funnel position
```

Avoid overly technical headings:

```text
What changed / what the evidence shows
Tool output
Raw rows
SQL result
Cohort boundary
```

For a simple funnel question, use:

```text
What the evidence shows
```

not:

```text
What changed
```

because “what changed” implies period comparison.

---

## Required Final Answer Structure For Funnel Questions

Use this structure:

```text
<One-line diagnosis>

For leads created between <display_start_date> and <display_end_date>, <total_leads> leads entered the funnel.

<Step-by-step funnel movement table>

What this means:
<Short interpretation based on biggest drop_from_previous and key stage buckets>

<Optional final-position breakdown table>

Confidence:
High / Medium / Low — <reason>

Data quality note:
<scope note in simple language>

Recommended next action:
<1-2 practical actions>
```

---

## Data Quality Note

Use this wording:

```text
This is based on leads created in the selected period. Revenue and payment values, if shown, are lifetime outcomes for those leads, not revenue collected during that period.
```

Do not say:

```text
lead_created_at cohort logic
exclusive end date
true payment-period revenue
```

unless the user asks for technical details.

---

## Tests To Add

Add or update tests for `get_diagnostic_funnel_snapshot`.

### Test 1: Funnel response has separate sections

Assert response includes:

```text
funnel_flow
final_position_breakdown
activity_counts
period.display_start_date
period.display_end_date
period.date_range_display
```

### Test 2: Funnel flow uses unique lead counts

Assert `funnel_flow` contains step keys:

```text
total_leads
booked_call
completed_call
signed_contract
paid_converted
```

### Test 3: Funnel flow has drop metrics

Assert each step after total has:

```text
dropped_from_previous
drop_rate_from_previous
conversion_rate_from_previous
```

### Test 4: No business-unfriendly date wording

If tests cover generated text, assert the final answer does not contain:

```text
up to but not including
exclusive end date
```

### Test 5: Prompt instruction exists

Assert `diagnostic_analytics.md` contains:

```text
For funnel leakage questions, always show the step-by-step funnel movement first.
Do not mix activity record counts into the main funnel flow.
Do not say "up to but not including".
```

---

## Completion Criteria

This task is complete when:

```text
1. get_diagnostic_funnel_snapshot returns funnel_flow.
2. get_diagnostic_funnel_snapshot returns final_position_breakdown.
3. get_diagnostic_funnel_snapshot returns activity_counts.
4. Period metadata includes display_start_date, display_end_date, and date_range_display.
5. diagnostic_analytics.md tells the agent to show funnel_flow first.
6. Final answers use business-friendly date wording.
7. Final answers do not show "up to but not including".
8. Final answers do not mix record counts into the main funnel flow.
9. Tests pass.
```
