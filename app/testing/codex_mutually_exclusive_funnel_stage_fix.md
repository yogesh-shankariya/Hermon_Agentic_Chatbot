# Codex Addendum: Fix Mutually Exclusive Diagnostic Funnel Stage Counts

## Goal

Fix the remaining funnel leakage issue in the diagnostic analytics output.

The current text-reason section is now internally consistent, but the funnel stage table can still over-count because the stage rows are not always mutually exclusive.

The funnel stage table must represent final lead positions in the funnel. Each lead must appear in exactly one stage row.

---

## Problem To Fix

Bad output example:

```text
Total leads = 515

Never booked a call = 108
Booked but did not complete call = 126
Completed call but did not sign = 159
Signed but not paid = 2
Paid / converted = 135
```

These stage rows sum to:

```text
108 + 126 + 159 + 2 + 135 = 530
```

But total leads is only:

```text
515
```

This is invalid because the stage rows over-count by 15 leads.

---

## Required Rule

For the funnel stage table, use mutually exclusive final-position cohorts.

This validation must always pass:

```text
total_leads
=
never_booked_leads
+ booked_not_completed_leads
+ completed_not_signed_leads
+ signed_not_paid_leads
+ paid_converted_leads
```

If this validation fails, do not present the funnel stage table as final.

---

## Correct Funnel Stage Definitions

Use the following mutually exclusive final-position definitions.

### 1. Total Leads

```sql
all leads in the selected lead_created_at period
```

### 2. Never Booked A Call

```sql
appointment_count = 0
```

Meaning:

```text
The lead entered the CRM/funnel but never reached the appointment stage.
```

### 3. Booked But Did Not Complete Call

```sql
appointment_count > 0
AND completed_call_count = 0
AND paid_payment_count = 0
```

Meaning:

```text
The lead booked at least one appointment but did not complete a call and did not become paid.
```

Important:

If a lead became paid, do not count them as booked-but-not-completed, even if their completed_call_count is 0 due to missing call data.

### 4. Completed Call But Did Not Sign

```sql
completed_call_count > 0
AND signed_contract_count = 0
AND paid_payment_count = 0
```

Meaning:

```text
The lead completed a call but did not sign a contract and did not become paid.
```

Important:

If a lead became paid without a clean signed contract record, do not count them as completed-but-not-signed. Paid / converted should win.

### 5. Signed But Not Paid

```sql
signed_contract_count > 0
AND paid_payment_count = 0
```

Meaning:

```text
The lead signed a contract but payment was not completed.
```

### 6. Paid / Converted

```sql
paid_payment_count > 0
```

Meaning:

```text
The lead reached paid conversion.
```

Paid / converted must be the highest-priority terminal stage.

---

## Stage Priority Rule

Assign each lead to exactly one final stage using this priority order:

```text
1. Paid / converted
2. Signed but not paid
3. Completed call but did not sign
4. Booked but did not complete call
5. Never booked a call
```

This means:

```sql
CASE
  WHEN paid_payment_count > 0 THEN 'paid_converted'
  WHEN signed_contract_count > 0 THEN 'signed_not_paid'
  WHEN completed_call_count > 0 THEN 'completed_not_signed'
  WHEN appointment_count > 0 THEN 'booked_not_completed'
  ELSE 'never_booked'
END
```

This priority prevents a paid lead from also appearing in an earlier stuck stage.

---

## Recommended SQL Pattern

Use one lead-level CTE first, then assign a final funnel stage.

Example pattern:

```sql
WITH lead_cohort AS (
  SELECT
    dls.lead_id,
    dls.appointment_count,
    dls.completed_call_count,
    dls.signed_contract_count,
    dls.paid_payment_count,
    CASE
      WHEN dls.paid_payment_count > 0 THEN 'paid_converted'
      WHEN dls.signed_contract_count > 0 THEN 'signed_not_paid'
      WHEN dls.completed_call_count > 0 THEN 'completed_not_signed'
      WHEN dls.appointment_count > 0 THEN 'booked_not_completed'
      ELSE 'never_booked'
    END AS final_funnel_stage
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :start_date
    AND dls.lead_created_at < :end_date
),
stage_counts AS (
  SELECT
    final_funnel_stage,
    COUNT(DISTINCT lead_id)::int AS lead_count
  FROM lead_cohort
  GROUP BY final_funnel_stage
),
total_check AS (
  SELECT COUNT(DISTINCT lead_id)::int AS total_leads
  FROM lead_cohort
)
SELECT
  sc.final_funnel_stage,
  sc.lead_count,
  tc.total_leads
FROM stage_counts sc
CROSS JOIN total_check tc
ORDER BY
  CASE sc.final_funnel_stage
    WHEN 'never_booked' THEN 1
    WHEN 'booked_not_completed' THEN 2
    WHEN 'completed_not_signed' THEN 3
    WHEN 'signed_not_paid' THEN 4
    WHEN 'paid_converted' THEN 5
    ELSE 99
  END;
```

---

## Required Validation

After computing stage counts, validate:

```python
stage_total = (
    never_booked_leads
    + booked_not_completed_leads
    + completed_not_signed_leads
    + signed_not_paid_leads
    + paid_converted_leads
)

assert stage_total == total_leads
```

If validation fails, the tool must return:

```json
{
  "status": "validation_failed",
  "safe_message": "Funnel stage counts could not be reconciled because final stage rows do not sum to total leads."
}
```

The final diagnostic answer must not show the invalid stage table.

---

## Text Reason Cohort Consistency

When the answer selects the biggest stuck group, the text reason tool must use the exact same final-stage cohort.

Example:

If the biggest stuck group is:

```text
completed_not_signed = 159
```

Then the text reason tool must filter using:

```sql
CASE
  WHEN paid_payment_count > 0 THEN 'paid_converted'
  WHEN signed_contract_count > 0 THEN 'signed_not_paid'
  WHEN completed_call_count > 0 THEN 'completed_not_signed'
  WHEN appointment_count > 0 THEN 'booked_not_completed'
  ELSE 'never_booked'
END = 'completed_not_signed'
```

The text reason output must satisfy:

```text
reason_combination_distribution total = 159
coverage total = 159
selected funnel stage count = 159
```

Do not use a separate looser condition like:

```sql
completed_call_count > 0
AND signed_contract_count = 0
```

unless it is exactly equivalent to the final-stage assignment.

---

## Corrected Answer Format

Use this format after the fix.

```text
The biggest leak is after the call: leads are completing calls but not signing.

For leads created between <display_start_date> and <display_end_date>, <total_leads> leads entered the funnel.

| Funnel stage | Leads | What this means |
|---|---:|---|
| Never booked a call | <never_booked> | Leads did not reach the appointment stage |
| Booked but did not complete call | <booked_not_completed> | Leads booked a call but did not attend/complete it |
| Completed call but did not sign | <completed_not_signed> | Leads attended the call but did not move to signed contract |
| Signed but not paid | <signed_not_paid> | Leads signed but payment was not completed |
| Paid / converted | <paid_converted> | Leads completed the paid conversion path |
| Total | <total_leads> | Must equal the sum of all rows above |
```

The `Total` row must equal the sum of the five mutually exclusive stage rows.

---

## Do Not Use This Invalid Format

Do not calculate the funnel table by subtracting independent reached counts like this:

```text
Total leads
Booked a call
Completed a call
Signed contract
Paid / converted
```

and then use those differences as final stuck groups.

Independent reached counts are useful for high-level conversion rates, but they are not safe for final-position leakage tables when records are not perfectly nested.

For diagnostic leakage answers, prefer mutually exclusive final-position cohorts.

---

## Optional: Reached Counts Can Be Shown Separately

If useful, reached-count metrics may be shown separately as supporting context, but do not mix them with final-position stage counts.

Allowed supporting section:

```text
Reached milestones:
- Booked a call: 407 leads
- Completed a call: 281 leads
- Signed contract: 136 leads
- Paid / converted: 135 leads
```

But the main leakage table must remain mutually exclusive and must sum to total leads.

---

## User-Friendly Labels

Do not show raw stage enum values in the final answer.

Use these labels:

```text
never_booked -> Never booked a call
booked_not_completed -> Booked but did not complete call
completed_not_signed -> Completed call but did not sign
signed_not_paid -> Signed but not paid
paid_converted -> Paid / converted
```

---

## Tests To Add

Add tests for the diagnostic funnel tool and final answer formatting.

### Test 1: Stage Sum Validation

Given the tool output:

```json
{
  "total_leads": 515,
  "never_booked_leads": 108,
  "booked_not_completed_leads": 126,
  "completed_not_signed_leads": 159,
  "signed_not_paid_leads": 2,
  "paid_converted_leads": 135
}
```

The validation must fail because:

```text
108 + 126 + 159 + 2 + 135 = 530
530 != 515
```

### Test 2: Valid Final Stage Output

Given mutually exclusive counts that sum to total:

```json
{
  "total_leads": 515,
  "never_booked_leads": 97,
  "booked_not_completed_leads": 122,
  "completed_not_signed_leads": 158,
  "signed_not_paid_leads": 3,
  "paid_converted_leads": 135
}
```

The validation must pass because:

```text
97 + 122 + 158 + 3 + 135 = 515
```

### Test 3: Text Reason Cohort Match

If `completed_not_signed_leads = 158`, then:

```text
text_reason_snapshot.total_dropped_leads must equal 158
reason_combination_distribution total must equal 158
coverage total must equal 158
```

If any value differs, the final answer must not present the reason table.

### Test 4: Paid Lead Priority

A lead with:

```json
{
  "appointment_count": 0,
  "completed_call_count": 0,
  "signed_contract_count": 0,
  "paid_payment_count": 1
}
```

must be assigned to:

```text
paid_converted
```

not `never_booked`.

### Test 5: Signed Lead Priority

A lead with:

```json
{
  "appointment_count": 1,
  "completed_call_count": 0,
  "signed_contract_count": 1,
  "paid_payment_count": 0
}
```

must be assigned to:

```text
signed_not_paid
```

not `booked_not_completed`.

---

## Completion Criteria

This task is complete only when:

- Funnel stage rows are mutually exclusive.
- Each lead appears in exactly one final funnel stage.
- Stage rows always sum to total leads.
- The biggest stuck group count equals the text-reason cohort count.
- Reason combination table total equals selected stuck group count.
- Coverage totals equal selected stuck group count.
- Raw enum labels are not shown in the final answer.
- If validation fails, the agent does not present the invalid funnel or reason table.
