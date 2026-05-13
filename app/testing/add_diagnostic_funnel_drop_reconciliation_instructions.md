# Codex Task: Add Exact Drop Reconciliation to Diagnostic Funnel Output

## Goal

Improve `get_diagnostic_funnel_snapshot` and `diagnostic_analytics.md` so funnel answers do not confuse users when the step-by-step funnel drop numbers do not exactly match the final funnel-position buckets.

Current issue:

The funnel movement table may show:

```text
Booked a call = 407
Completed a call = 281
Dropped from booked to completed = 126
```

But the final-position table may show:

```text
Booked but did not complete call = 122
Lost = 61
Unqualified = 10
Refunded = 1
```

Business users may ask:

```text
If 126 dropped after booking, why does the final table show only 122 booked-but-not-completed?
Where did the remaining 4 leads go?
```

The answer should not say vague wording like:

```text
Some leads were later marked as Lost or Unqualified.
```

Instead, the tool must return exact counts, and the final answer must say exactly where those dropped leads are now.

---

## Files To Update

Update:

```text
app/tools/diagnostic_tools.py
app/skills/modules/diagnostic_analytics.md
tests/test_diagnostic_tools.py
```

If the repo uses another diagnostic test file, update the nearest matching file.

Do not update:

```text
diagnostic_lead_snapshot builder
database schema
router
SQL agent
Lead 360 agent
normal SQL skills
```

---

## Existing Design Context

The diagnostic route is separate from SQL analytics and uses only diagnostic tools over `diagnostic_lead_snapshot`.

Do not add SQL agent usage.

Do not call:

```text
load_skill
run_readonly_sql
get_lead_360
```

The diagnostic prompt already states that diagnostic answers must use only diagnostic tool evidence and must not generate SQL.

---

## Required Tool Change

Update `get_diagnostic_funnel_snapshot` to return an additional section:

```text
drop_reconciliation
```

The response should now include:

```text
funnel_flow
drop_reconciliation
final_position_breakdown
activity_counts
```

Meaning:

| Section | Purpose |
|---|---|
| `funnel_flow` | Step-by-step movement through the funnel using unique lead counts |
| `drop_reconciliation` | Exact final-position split of leads that dropped between each step |
| `final_position_breakdown` | Where all leads finally sit now, one bucket per lead |
| `activity_counts` | Supporting record counts only, such as appointment records and payment records |

---

## Why `drop_reconciliation` Is Needed

`funnel_flow` is cumulative.

Example:

A paid lead is counted in every step it reached:

```text
Total leads
Booked a call
Completed a call
Signed contract
Paid / converted
```

`final_position_breakdown` is exclusive.

Each lead appears only once:

```text
Paid / converted
```

Because of this, movement drop counts and final-position buckets may not match one-to-one.

`drop_reconciliation` explains the exact difference.

---

## Drop Reconciliation Logic

For each drop point, filter the dropped lead set and group it by final `funnel_stage` and `conversion_outcome`.

Use only `diagnostic_lead_snapshot`.

Always filter:

```sql
dls.clerk_org_id = :org_id
dls.lead_created_at >= CAST(:start_date AS date)
dls.lead_created_at < CAST(:end_date AS date)
```

Use explicit columns only.

Do not use:

```sql
SELECT *
dls.*
```

---

## Drop Point Definitions

### 1. Did not book a call

These are leads that entered the funnel but did not reach booking.

```sql
appointment_count = 0
```

Drop point metadata:

```text
drop_point_key = lead_to_booked
drop_point_label = Did not book a call
from_step_label = Total leads
to_step_label = Booked a call
```

---

### 2. Booked but did not complete call

These are leads that booked but did not reach completed call.

```sql
appointment_count > 0
AND completed_call_count = 0
```

Drop point metadata:

```text
drop_point_key = booked_to_completed
drop_point_label = Booked but did not complete call
from_step_label = Booked a call
to_step_label = Completed a call
```

---

### 3. Completed call but did not sign

These are leads that completed a call but did not reach signed contract.

```sql
completed_call_count > 0
AND signed_contract_count = 0
```

Drop point metadata:

```text
drop_point_key = completed_to_signed
drop_point_label = Completed call but did not sign
from_step_label = Completed a call
to_step_label = Signed contract
```

---

### 4. Signed but did not pay

These are leads that signed but did not reach paid/converted.

```sql
signed_contract_count > 0
AND COALESCE(net_collected_amount, 0) <= 0
AND paid_payment_count = 0
```

Drop point metadata:

```text
drop_point_key = signed_to_paid
drop_point_label = Signed but did not pay
from_step_label = Signed contract
to_step_label = Paid / converted
```

---

## Business-Friendly Stage Labels

Use these labels in tool output and final answer.

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

If an unexpected stage appears, use:

```text
Unknown
```

---

## Recommended SQL Pattern

Add a CTE/query similar to this inside the funnel tool.

```sql
WITH scoped AS (
  SELECT
    dls.lead_id,
    dls.appointment_count,
    dls.completed_call_count,
    dls.signed_contract_count,
    dls.paid_payment_count,
    dls.net_collected_amount,
    dls.funnel_stage,
    dls.conversion_outcome
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
drop_sets AS (
  SELECT
    'lead_to_booked' AS drop_point_key,
    'Did not book a call' AS drop_point_label,
    'Total leads' AS from_step_label,
    'Booked a call' AS to_step_label,
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE appointment_count = 0

  UNION ALL

  SELECT
    'booked_to_completed',
    'Booked but did not complete call',
    'Booked a call',
    'Completed a call',
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE appointment_count > 0
    AND completed_call_count = 0

  UNION ALL

  SELECT
    'completed_to_signed',
    'Completed call but did not sign',
    'Completed a call',
    'Signed contract',
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE completed_call_count > 0
    AND signed_contract_count = 0

  UNION ALL

  SELECT
    'signed_to_paid',
    'Signed but did not pay',
    'Signed contract',
    'Paid / converted',
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE signed_contract_count > 0
    AND COALESCE(net_collected_amount, 0) <= 0
    AND paid_payment_count = 0
),
reconciled AS (
  SELECT
    drop_point_key,
    drop_point_label,
    from_step_label,
    to_step_label,
    funnel_stage,
    conversion_outcome,
    CASE funnel_stage
      WHEN 'lead_only' THEN 'Never booked a call'
      WHEN 'booked_not_completed' THEN 'Booked but did not complete call'
      WHEN 'completed_not_signed' THEN 'Completed call but did not sign'
      WHEN 'signed_not_paid' THEN 'Signed but not paid'
      WHEN 'paid' THEN 'Paid / converted'
      WHEN 'lost' THEN 'Lost'
      WHEN 'unqualified' THEN 'Unqualified'
      WHEN 'refunded' THEN 'Refunded'
      ELSE 'Unknown'
    END AS final_position_label,
    COUNT(*)::int AS lead_count
  FROM drop_sets
  GROUP BY
    drop_point_key,
    drop_point_label,
    from_step_label,
    to_step_label,
    funnel_stage,
    conversion_outcome
),
totals AS (
  SELECT
    drop_point_key,
    SUM(lead_count)::int AS dropped_leads
  FROM reconciled
  GROUP BY drop_point_key
)
SELECT
  r.drop_point_key,
  r.drop_point_label,
  r.from_step_label,
  r.to_step_label,
  t.dropped_leads,
  r.funnel_stage,
  r.conversion_outcome,
  r.final_position_label,
  r.lead_count,
  CASE
    WHEN t.dropped_leads = 0 THEN NULL
    ELSE ROUND(100.0 * r.lead_count / t.dropped_leads, 2)
  END AS pct_of_dropped_leads
FROM reconciled r
JOIN totals t
  ON t.drop_point_key = r.drop_point_key
ORDER BY
  CASE r.drop_point_key
    WHEN 'lead_to_booked' THEN 1
    WHEN 'booked_to_completed' THEN 2
    WHEN 'completed_to_signed' THEN 3
    WHEN 'signed_to_paid' THEN 4
    ELSE 99
  END,
  r.lead_count DESC,
  r.final_position_label ASC
```

---

## Required Tool Response Shape

Add `drop_reconciliation` as a list.

Example:

```json
{
  "status": "success",
  "tool": "get_diagnostic_funnel_snapshot",
  "period": {
    "start_date": "2025-10-25",
    "end_date": "2026-04-25",
    "display_start_date": "2025-10-25",
    "display_end_date": "2026-04-24",
    "date_range_display": "25 Oct 2025 to 24 Apr 2026",
    "date_field": "lead_created_at"
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
      "leads_reached": 407,
      "dropped_from_previous": 108,
      "drop_rate_from_previous": 20.97,
      "conversion_rate_from_previous": 79.03
    },
    {
      "step_order": 3,
      "step_key": "completed_call",
      "step_label": "Completed a call",
      "leads_reached": 281,
      "dropped_from_previous": 126,
      "drop_rate_from_previous": 30.96,
      "conversion_rate_from_previous": 69.04
    }
  ],
  "drop_reconciliation": [
    {
      "drop_point_key": "lead_to_booked",
      "drop_point_label": "Did not book a call",
      "from_step_label": "Total leads",
      "to_step_label": "Booked a call",
      "dropped_leads": 108,
      "funnel_stage": "lead_only",
      "conversion_outcome": "lead_not_booked",
      "final_position_label": "Never booked a call",
      "lead_count": 97,
      "pct_of_dropped_leads": 89.81
    },
    {
      "drop_point_key": "lead_to_booked",
      "drop_point_label": "Did not book a call",
      "from_step_label": "Total leads",
      "to_step_label": "Booked a call",
      "dropped_leads": 108,
      "funnel_stage": "lost",
      "conversion_outcome": "lost",
      "final_position_label": "Lost",
      "lead_count": 8,
      "pct_of_dropped_leads": 7.41
    },
    {
      "drop_point_key": "lead_to_booked",
      "drop_point_label": "Did not book a call",
      "from_step_label": "Total leads",
      "to_step_label": "Booked a call",
      "dropped_leads": 108,
      "funnel_stage": "unqualified",
      "conversion_outcome": "unqualified",
      "final_position_label": "Unqualified",
      "lead_count": 3,
      "pct_of_dropped_leads": 2.78
    }
  ],
  "final_position_breakdown": [],
  "activity_counts": {},
  "row_count": 515
}
```

The exact numbers must come from SQL. Do not hardcode demo values.

---

## Validation Rule

For each `drop_point_key`, this must be true:

```text
SUM(drop_reconciliation.lead_count for that drop_point_key)
=
drop_reconciliation.dropped_leads
```

Also, the `dropped_leads` value for each drop point must match the corresponding `dropped_from_previous` value from `funnel_flow`.

Mapping:

```text
lead_to_booked -> Booked a call.dropped_from_previous
booked_to_completed -> Completed a call.dropped_from_previous
completed_to_signed -> Signed contract.dropped_from_previous
signed_to_paid -> Paid / converted.dropped_from_previous
```

If these do not match, tests should fail.

---

## Prompt Update: `diagnostic_analytics.md`

Add this section under Funnel Answer Format.

```markdown
## Drop Reconciliation Format

For funnel leakage questions, if the tool returns `drop_reconciliation`, use it to explain exactly where dropped leads are now.

Do not say vague phrases such as:
- "some leads were later marked lost"
- "some leads moved to other statuses"
- "some leads are in other buckets"

Instead, give exact counts from `drop_reconciliation`.

Use this table after the funnel movement table:

| Drop point | Dropped leads | Final position now | Leads | % of dropped leads |
|---|---:|---|---:|---:|

Example wording:
"The movement table shows how many leads dropped between steps. The reconciliation table below shows exactly where those dropped leads are now."

For each drop point, group rows together logically:
- Did not book a call
- Booked but did not complete call
- Completed call but did not sign
- Signed but did not pay

If a drop point has multiple final positions, list each final position with exact counts.

Do not invent counts.
Do not calculate new counts unless the tool returned the required fields.
```

---

## Final Answer Format For Funnel Questions

Use this structure:

```text
<One-line diagnosis>

For leads created between <display_start_date> and <display_end_date>, <total_leads> leads entered the funnel.

Funnel movement:
<step-by-step movement table>

Where dropped leads are now:
<drop reconciliation table>

Final lead position:
<final-position table>

What this means:
<short explanation>

Confidence:
<High/Medium/Low + reason>

Data quality note:
<simple scope note>

Recommended next action:
<1-2 practical actions>
```

---

## User-Friendly Example Answer

Use this as the target answer style.

```text
The biggest funnel leak is after the completed call: many leads attend the call but do not sign.

For leads created between 25 Oct 2025 and 24 Apr 2026, 515 leads entered the funnel.

Funnel movement:

| Funnel step | Leads reached | Dropped from previous step | Drop % | Conversion % |
|---|---:|---:|---:|---:|
| Total leads | 515 | - | - | - |
| Booked a call | 407 | 108 | 20.97% | 79.03% |
| Completed a call | 281 | 126 | 30.96% | 69.04% |
| Signed contract | 136 | 145 | 51.60% | 48.40% |
| Paid / converted | 135 | 1 | 0.74% | 99.26% |

Where dropped leads are now:

| Drop point | Dropped leads | Final position now | Leads | % of dropped leads |
|---|---:|---|---:|---:|
| Did not book a call | 108 | Never booked a call | 97 | 89.81% |
| Did not book a call | 108 | Lost | 8 | 7.41% |
| Did not book a call | 108 | Unqualified | 3 | 2.78% |
| Booked but did not complete call | 126 | Booked but did not complete call | 122 | 96.83% |
| Booked but did not complete call | 126 | Lost | 3 | 2.38% |
| Booked but did not complete call | 126 | Unqualified | 1 | 0.79% |
| Completed call but did not sign | 145 | Completed call but did not sign | 87 | 60.00% |
| Completed call but did not sign | 145 | Lost | 50 | 34.48% |
| Completed call but did not sign | 145 | Unqualified | 7 | 4.83% |
| Completed call but did not sign | 145 | Refunded | 1 | 0.69% |
| Signed but did not pay | 1 | Signed but not paid | 1 | 100.00% |

Final lead position:

| Final lead position | Leads | % of total leads |
|---|---:|---:|
| Paid / converted | 135 | 26.21% |
| Booked but did not complete call | 122 | 23.69% |
| Never booked a call | 97 | 18.83% |
| Completed call but did not sign | 87 | 16.89% |
| Lost | 61 | 11.84% |
| Unqualified | 10 | 1.94% |
| Signed but not paid | 2 | 0.39% |
| Refunded | 1 | 0.19% |

What this means:
The largest step drop is from completed call to signed contract. The reconciliation table shows that those 145 dropped leads are mainly split between 87 still sitting as completed-but-not-signed and 50 marked lost.

Confidence:
High — the funnel movement and reconciliation both point to the same main bottleneck after the completed call.

Data quality note:
This is based on leads created in the selected period. Revenue and payment values, if shown, are lifetime outcomes for those leads, not revenue collected during that period.

Recommended next action:
Review completed-but-not-signed and lost leads from the post-call stage first. This is the biggest conversion leak and should be prioritized before payment collection.
```

Do not hardcode these example values. They are only an example format.

---

## Important Wording Rules

Do not use vague reconciliation language.

Avoid:

```text
some leads were marked lost
some leads are in other statuses
remaining leads are elsewhere
```

Use exact counts:

```text
Out of 126 leads that dropped between booked and completed call, 122 are still booked-but-not-completed, 3 are lost, and 1 is unqualified.
```

Use business-friendly labels.

Avoid raw enum values:

```text
lead_only
booked_not_completed
completed_not_signed
signed_not_paid
```

Use:

```text
Never booked a call
Booked but did not complete call
Completed call but did not sign
Signed but not paid
```

---

## Test Plan

### Test 1: Tool returns drop reconciliation

Assert `get_diagnostic_funnel_snapshot` response contains:

```text
drop_reconciliation
```

and that it is a list.

---

### Test 2: Required drop reconciliation fields

Every row in `drop_reconciliation` must include:

```text
drop_point_key
drop_point_label
from_step_label
to_step_label
dropped_leads
funnel_stage
conversion_outcome
final_position_label
lead_count
pct_of_dropped_leads
```

---

### Test 3: Drop point keys are valid

Allowed values:

```text
lead_to_booked
booked_to_completed
completed_to_signed
signed_to_paid
```

---

### Test 4: Reconciliation counts match

For each `drop_point_key`:

```text
sum(lead_count) = dropped_leads
```

---

### Test 5: Reconciliation matches funnel flow

Map reconciliation to funnel flow:

```text
lead_to_booked -> Booked a call.dropped_from_previous
booked_to_completed -> Completed a call.dropped_from_previous
completed_to_signed -> Signed contract.dropped_from_previous
signed_to_paid -> Paid / converted.dropped_from_previous
```

Assert:

```text
drop_reconciliation dropped_leads = corresponding funnel_flow dropped_from_previous
```

---

### Test 6: No raw SQL or unsafe output

The tool must not expose:

```text
raw SQL
raw IDs in business answer
email
phone
payment links
meeting links
recording links
transcript links
provider IDs
payloads
```

---

### Test 7: Prompt updated

Assert `diagnostic_analytics.md` contains:

```text
Drop Reconciliation Format
Do not say vague phrases
use exact counts from drop_reconciliation
```

---

## Completion Criteria

This task is complete when:

```text
1. get_diagnostic_funnel_snapshot returns drop_reconciliation.
2. drop_reconciliation shows exact final-position counts for each dropped lead group.
3. Sum of each drop group reconciliation equals dropped_leads.
4. dropped_leads matches the corresponding funnel_flow drop count.
5. diagnostic_analytics.md instructs the agent to show exact counts, not vague wording.
6. Final funnel answers explain where dropped leads are now with exact counts.
7. Existing diagnostic agent routing remains unchanged.
8. Existing SQL agent and Lead 360 agent remain unchanged.
9. Tests pass.
```
