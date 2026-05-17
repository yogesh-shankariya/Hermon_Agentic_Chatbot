# Codex Task — Add Latest Profession and Employment Status to Diagnostic Lead Snapshot

## Goal

Add two lead-level profile columns to:

```text
diagnostic_lead_snapshot
```

New columns:

```text
latest_profession
latest_employment_status
```

These fields should store one latest profile value per lead, derived from `opt_in_question_answers`.

Do not create a new opt-in snapshot table for now.

---

## Why This Is Needed

Currently, questions like these may fail or require exact form-question matching:

```text
Which profession submitted the most opt-ins?
Which employment status is most common?
```

For diagnostic analytics, it is better to support lead-level profile questions from `diagnostic_lead_snapshot`.

This keeps the diagnostic snapshot one row per lead and avoids duplicate counting from multiple opt-ins.

---

## Business Meaning

Use the latest non-empty opt-in answer per lead.

Mapping:

```text
latest_profession
→ latest non-empty answer to: "What do you do for work?"

latest_employment_status
→ latest non-empty answer to: "What is your employment status?"
```

---

## Important Grain Rule

`diagnostic_lead_snapshot` must remain:

```text
one row per lead
```

A lead can have multiple opt-ins, but the snapshot must store only one final selected value per lead.

Do not create multiple snapshot rows for the same lead.

Do not count opt-ins as leads in this snapshot.

---

## Selection Rule

For each lead:

```text
1. Find all opt-ins for that lead.
2. Find non-empty answers for the mapped question.
3. Choose the latest answer using answer created_at first.
4. If answer created_at is null, fallback to opt_in created_at.
5. If no valid answer exists, store null.
```

Use deterministic ordering.

Recommended ordering:

```text
COALESCE(opt_in_question_answers.created_at, opt_ins.created_at) DESC
opt_ins.created_at DESC
opt_ins.id DESC
```

---

## Schema Change

Add nullable text columns:

```sql
ALTER TABLE diagnostic_lead_snapshot
ADD COLUMN IF NOT EXISTS latest_profession TEXT;

ALTER TABLE diagnostic_lead_snapshot
ADD COLUMN IF NOT EXISTS latest_employment_status TEXT;
```

Do not make these columns required.

Do not add default values like `Unknown`.

Use `NULL` when the answer is missing.

---

## Snapshot Builder Update

Update the diagnostic snapshot builder query/script so these two fields are populated when rebuilding `diagnostic_lead_snapshot`.

Use CTEs similar to this pattern.

### Latest Profession CTE

```sql
latest_profession AS (
  SELECT DISTINCT ON (oi.lead_id)
    oi.lead_id,
    NULLIF(TRIM(oqa.answer_text), '') AS latest_profession
  FROM opt_ins oi
  JOIN opt_in_question_answers oqa
    ON oqa.opt_in_id = oi.id
   AND oqa.clerk_org_id = oi.clerk_org_id
  WHERE oi.clerk_org_id = :org_id
    AND oi.is_deleted = false
    AND oqa.is_deleted = false
    AND LOWER(TRIM(oqa.question_text)) = LOWER('What do you do for work?')
    AND NULLIF(TRIM(oqa.answer_text), '') IS NOT NULL
  ORDER BY
    oi.lead_id,
    COALESCE(oqa.created_at, oi.created_at) DESC,
    oi.created_at DESC,
    oi.id DESC
)
```

### Latest Employment Status CTE

```sql
latest_employment_status AS (
  SELECT DISTINCT ON (oi.lead_id)
    oi.lead_id,
    NULLIF(TRIM(oqa.answer_text), '') AS latest_employment_status
  FROM opt_ins oi
  JOIN opt_in_question_answers oqa
    ON oqa.opt_in_id = oi.id
   AND oqa.clerk_org_id = oi.clerk_org_id
  WHERE oi.clerk_org_id = :org_id
    AND oi.is_deleted = false
    AND oqa.is_deleted = false
    AND LOWER(TRIM(oqa.question_text)) = LOWER('What is your employment status?')
    AND NULLIF(TRIM(oqa.answer_text), '') IS NOT NULL
  ORDER BY
    oi.lead_id,
    COALESCE(oqa.created_at, oi.created_at) DESC,
    oi.created_at DESC,
    oi.id DESC
)
```

Then join both CTEs into the final snapshot select:

```sql
LEFT JOIN latest_profession lp
  ON lp.lead_id = l.id

LEFT JOIN latest_employment_status les
  ON les.lead_id = l.id
```

And include:

```sql
lp.latest_profession,
les.latest_employment_status
```

in the final insert/select for `diagnostic_lead_snapshot`.

---

## Column Naming

Use exactly:

```text
latest_profession
latest_employment_status
```

Do not use alternative names like:

```text
profession
employment
employment_type
job_title
```

Reason: the values are selected from latest opt-in profile answers, so the `latest_` prefix makes the meaning clear.

---

## Diagnostic Tool Update

Add support for profile breakdowns in diagnostic analytics.

Minimum required support:

```text
group by latest_profession
group by latest_employment_status
```

Supported questions should include:

```text
Which profession generated the most leads?
Which profession converts best?
Which employment status is most common?
Which employment status has the highest paid conversion?
```

If the user asks:

```text
Which profession submitted the most opt-ins?
```

Since `diagnostic_lead_snapshot` is lead-level, answer with careful wording:

```text
Based on the latest lead-level opt-in profile answer, <profession> is the most common profession among leads.
```

Do not claim this is exact opt-in-level count unless the query uses `opt_in_question_answers`.

---

## Recommended Diagnostic Profile Tool

If cleanest, add a new controlled diagnostic tool:

```text
get_diagnostic_profile_snapshot
```

Inputs:

```text
org_id
current_start_date
current_end_date
profile_field
limit
```

Allowed `profile_field` values:

```text
latest_profession
latest_employment_status
```

Reject any other field.

This tool should read only from:

```text
diagnostic_lead_snapshot
```

### Metrics to Return

For each profile value:

```text
profile_value
lead_count
booked_lead_count
completed_call_lead_count
signed_lead_count
paid_lead_count
net_collected_amount
lead_to_booked_call_rate
completed_lead_to_signed_lead_rate
signed_lead_to_paid_lead_rate
paid_lead_rate
net_collected_per_lead
```

Use distinct lead-level metrics.

Do not use payment-record count as paid leads.

### Sorting

Default sort:

```text
lead_count DESC
profile_value ASC
```

For “converts best” questions, sort by:

```text
paid_lead_rate DESC
lead_count DESC
```

Apply a sensible minimum sample caveat if needed.

---

## SQL Pattern for Profile Snapshot Tool

Example for profession:

```sql
WITH scoped AS (
  SELECT
    COALESCE(NULLIF(TRIM(latest_profession), ''), 'Not provided') AS profile_value,
    appointment_count,
    completed_call_count,
    signed_contract_count,
    paid_payment_count,
    net_collected_amount
  FROM diagnostic_lead_snapshot
  WHERE clerk_org_id = :org_id
    AND lead_created_at >= CAST(:start_date AS date)
    AND lead_created_at < CAST(:end_date AS date)
)
SELECT
  profile_value,
  COUNT(*)::int AS lead_count,
  COUNT(*) FILTER (WHERE appointment_count > 0)::int AS booked_lead_count,
  COUNT(*) FILTER (WHERE completed_call_count > 0)::int AS completed_call_lead_count,
  COUNT(*) FILTER (WHERE signed_contract_count > 0)::int AS signed_lead_count,
  COUNT(*) FILTER (WHERE paid_payment_count > 0)::int AS paid_lead_count,
  COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE appointment_count > 0)
    / NULLIF(COUNT(*), 0),
    2
  ) AS lead_to_booked_call_rate,
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
  ) AS paid_lead_rate,
  ROUND(
    COALESCE(SUM(net_collected_amount), 0) / NULLIF(COUNT(*), 0),
    2
  ) AS net_collected_per_lead
FROM scoped
GROUP BY profile_value
ORDER BY lead_count DESC, profile_value ASC
LIMIT :limit;
```

For employment status, replace:

```text
latest_profession
```

with:

```text
latest_employment_status
```

---

## Diagnostic Analytics Prompt Update

Update `diagnostic_analytics.md` to mention profile questions.

Add under supported question types:

```text
which profession generated the most leads
which profession converts best
which employment status is most common
which employment status converts best
```

Add tool guidance:

```text
For profile breakdown questions, use get_diagnostic_profile_snapshot if available.
Use latest_profession for profession/work/occupation questions.
Use latest_employment_status for employment status/job status questions.
```

Add wording rule:

```text
These are latest lead-level opt-in profile answers, not exact opt-in submission counts.
```

---

## Validation Checks

Update the validation script to check:

```text
diagnostic_lead_snapshot still has exactly one row per lead.
latest_profession does not create duplicate lead rows.
latest_employment_status does not create duplicate lead rows.
latest_profession has no blank strings.
latest_employment_status has no blank strings.
latest_profession is populated for expected demo leads.
latest_employment_status is populated for expected demo leads.
```

For current demo data, since every opt-in has both questions, most or all leads should have:

```text
latest_profession IS NOT NULL
latest_employment_status IS NOT NULL
```

If there are missing values, report count and sample reason, but do not invent values.

---

## Seed Script / Dummy Data Update

After adding columns to the snapshot builder, rerun the demo seed or snapshot rebuild for:

```text
org_dummy_client_demo_001
```

Then rerun validation.

Expected:

```text
diagnostic_lead_snapshot rows = 500
latest_profession populated
latest_employment_status populated
no duplicate lead rows
```

---

## Answer Examples

### Question

```text
Which profession generated the most leads?
```

Expected answer:

```markdown
Based on the latest lead-level opt-in profile answer, the most common profession is <profession>, with <lead_count> leads.

| Profession | Leads | Paid leads | Paid lead rate | Lifetime net collected |
|---|---:|---:|---:|---:|
| ... | ... | ... | ... | ... |
```

### Question

```text
Which employment status is most common?
```

Expected answer:

```markdown
Based on the latest lead-level opt-in profile answer, the most common employment status is <status>, with <lead_count> leads.

| Employment status | Leads | Paid leads | Paid lead rate | Lifetime net collected |
|---|---:|---:|---:|---:|
| ... | ... | ... | ... | ... |
```

---

## Important Wording Rule

Because this is lead-level:

Say:

```text
Based on the latest lead-level opt-in profile answer...
```

Do not say:

```text
exact opt-in submissions by profession
exact opt-in submissions by employment status
```

unless the answer uses opt-in-level tables.

---

## Do Not Do

Do not:

```text
Do not create multiple diagnostic_lead_snapshot rows per lead.
Do not create a new opt-in snapshot table for this task.
Do not store raw form payloads.
Do not expose raw opt-in answers beyond the grouped profile values.
Do not use diagnostic_text_insights for opt-in profile distribution.
Do not call LLM to infer profession or employment status.
Do not use exact user wording like "profession" as a raw form question filter.
Do not replace missing values with fake values.
Do not break existing diagnostic funnel/source/revenue behavior.
```

---

## Definition of Done

This task is complete when:

```text
diagnostic_lead_snapshot has latest_profession and latest_employment_status columns.
Snapshot builder populates both fields from latest non-empty opt-in answers.
Snapshot remains one row per lead.
Diagnostic analytics can answer profession and employment-status profile breakdown questions.
Answers clearly say these are latest lead-level opt-in profile answers.
Validation passes.
Existing diagnostic answers continue to work.
```
