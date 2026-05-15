# Codex Addendum: Fix Funnel + Text Reason Cohort Consistency

## Goal

Update the diagnostic analytics implementation so that funnel leakage answers and diagnostic text reason answers use the same lead cohort.

This addendum fixes the issue where one answer can show different counts for the same business group, such as:

```text
Completed call → Signed contract drop = 145
Completed-call leads who did not sign = 158
Main visible stuck group = 87
```

That must never happen.

For any funnel leakage answer, the numeric funnel stage, selected stuck/drop cohort, text reason table, coverage note, and recommendation must all refer to the same lead population.

---

## Why This Change Is Required

The current funnel answer can calculate drop-off by subtracting independent reached counts, for example:

```text
completed_call_leads - signed_contract_leads
```

This can be misleading if the data is not perfectly nested. For example, a lead may have a signed contract but no completed-call flag, or a paid payment without a clean signed-contract path.

The text reason tool may then use a separate cohort condition such as:

```text
completed_call_count > 0 AND signed_contract_count = 0
```

This causes mismatch between the funnel number and the text reason number.

Fix this by using explicit lead-level stuck/drop cohorts and passing the exact same cohort definition to the text reason tool.

---

## Critical Rule

For funnel leakage answers:

```text
The selected dropped/stuck cohort count must equal the text reason cohort count.
```

Example:

```text
Completed call but did not sign = 158
Reason combination table total = 158
Coverage note total = 158
```

Do not show multiple counts for the same group.

Bad:

```text
Completed call → Signed contract drop = 145
87 leads completed a call but did not sign
Text reason cohort = 158 completed-call leads who did not sign
```

Good:

```text
Completed call but did not sign = 158
Reason combination table total = 158
Coverage note total = 158
```

---

## Required Implementation Change

### 1. Stop Using Independent Subtraction For Business Stuck Groups

Do not derive text-reason cohorts from only this type of subtraction:

```text
completed_call_leads - signed_contract_leads
```

Instead, calculate explicit lead-level stuck/drop cohorts from `diagnostic_lead_snapshot`.

### 2. Use Explicit Stuck/Drop Cohort Definitions

Use these definitions consistently in both funnel and text reason logic.

```text
total_leads:
  all active diagnostic snapshot leads in the selected lead_created_at period

never_booked:
  appointment_count = 0

booked_not_completed:
  appointment_count > 0
  AND completed_call_count = 0

completed_not_signed:
  completed_call_count > 0
  AND signed_contract_count = 0

signed_not_paid:
  signed_contract_count > 0
  AND paid_payment_count = 0

paid_converted:
  paid_payment_count > 0
```

If the team wants a stricter fully sequential paid path, optionally also support:

```text
paid_after_signed:
  signed_contract_count > 0
  AND paid_payment_count > 0
```

But do not mix `paid_converted` and `paid_after_signed` in the same answer without labeling clearly.

---

## Recommended Funnel Answer Shape

For broad questions like:

```text
Where are we losing people in the funnel?
Where are we losing people on funnel?
Why are leads not converting?
Which stage is the biggest bottleneck?
```

Use this structure:

```text
<One-line diagnosis>

For leads created between <display_start_date> and <display_end_date>, <total_leads> leads entered the funnel.

| Funnel stage | Leads | What this means |
|---|---:|---|
| Total leads | <total_leads> | All leads in the selected period |
| Never booked a call | <never_booked> | Leads did not reach the appointment stage |
| Booked but did not complete call | <booked_not_completed> | Leads booked a call but did not attend/complete it |
| Completed call but did not sign | <completed_not_signed> | Leads attended the call but did not move to signed contract |
| Signed but not paid | <signed_not_paid> | Leads signed but payment was not completed |
| Paid / converted | <paid_converted> | Leads completed the paid conversion path |

What this means:
<short interpretation>

Known reasons for the biggest stuck group: <selected_cohort_label>
<reason combination distribution>

Individual issue view:
<individual issue distribution>

Coverage note:
<coverage numbers>

Recommended next action:
<actions>
```

Important:

- This is a stuck-group view, not a strict conversion-rate table.
- Do not show confusing `Dropped from previous step` values unless they are calculated from the exact same explicit cohort logic.
- Prefer a clear stuck-group table for business users.

---

## Selecting The Biggest Stuck Group

For the broad funnel question, identify the largest meaningful stuck/drop group among:

```text
never_booked
booked_not_completed
completed_not_signed
signed_not_paid
```

Then run text reason analysis for that selected cohort.

Priority rule:

1. If `completed_not_signed` is large, prefer it because it is post-call and usually has richer text insights.
2. If `booked_not_completed` is larger, report it as the biggest numeric leak, but mention that text reasons may be less rich if no call happened.
3. If `signed_not_paid` is meaningful, mention it separately as payment-stage leakage.
4. Do not run text reasons for every cohort by default. Use top 1 cohort, or top 2 if needed.

---

## Text Reason Tool Requirement

The `get_diagnostic_text_reason_snapshot` tool must accept a `cohort_name` or equivalent parameter.

Supported cohort names:

```text
never_booked
booked_not_completed
completed_not_signed
signed_not_paid
completed_not_paid
```

Recommended default for broad funnel leakage:

```text
selected largest stuck/drop cohort
```

Recommended default for post-call conversion questions:

```text
completed_not_signed
```

Recommended default for payment questions:

```text
signed_not_paid
```

The text reason tool must apply the exact same lead-level cohort condition as the funnel/stuck group answer.

---

## SQL Logic Guidance

Use CTEs that first define the period lead population, then create explicit cohorts.

Example pattern:

```sql
WITH period_leads AS (
  SELECT
    dls.lead_id,
    dls.clerk_org_id,
    dls.appointment_count,
    dls.completed_call_count,
    dls.signed_contract_count,
    dls.paid_payment_count
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :start_date
    AND dls.lead_created_at < :end_date
),
cohort_leads AS (
  SELECT
    lead_id,
    clerk_org_id,
    CASE
      WHEN :cohort_name = 'never_booked'
        AND appointment_count = 0 THEN true
      WHEN :cohort_name = 'booked_not_completed'
        AND appointment_count > 0
        AND completed_call_count = 0 THEN true
      WHEN :cohort_name = 'completed_not_signed'
        AND completed_call_count > 0
        AND signed_contract_count = 0 THEN true
      WHEN :cohort_name = 'signed_not_paid'
        AND signed_contract_count > 0
        AND paid_payment_count = 0 THEN true
      WHEN :cohort_name = 'completed_not_paid'
        AND completed_call_count > 0
        AND paid_payment_count = 0 THEN true
      ELSE false
    END AS in_selected_cohort
  FROM period_leads
)
SELECT COUNT(*) AS selected_cohort_leads
FROM cohort_leads
WHERE in_selected_cohort = true;
```

The same `cohort_leads` CTE should be used when joining to `diagnostic_text_insights`.

---

## Reason Combination Distribution

This table answers:

```text
Out of the selected dropped/stuck leads, what combination of issues did each lead have?
```

Rules:

- Each selected cohort lead appears in exactly one combination row.
- The table must sum to `total_dropped_leads` / `selected_cohort_leads`.
- Build one sorted distinct known reason-category list per lead.
- Exclude `unknown` from known issue combinations.
- If a lead has text insights but all reasons are `unknown`, bucket as `Reason not clear`.
- If a lead has no usable text insight, bucket as `No usable text insight available`.
- Combine lower-volume known combinations into `Other lower-volume combinations`.
- Keep `Reason not clear` and `No usable text insight available` separate.
- Show `Other lower-volume combinations` at the bottom, not at the top, even if it is the largest row.

Default display limit:

```text
top 10 rows total, including special rows and Other lower-volume combinations
```

If the `Other lower-volume combinations` row is more than 40% of the cohort, add this note:

```text
Reason combinations are fragmented, so the individual issue view is more useful than the combination view.
```

---

## Individual Issue Distribution

This table answers:

```text
Across the same selected dropped/stuck leads, how many leads had each issue?
```

Rules:

- Count distinct leads per issue.
- One lead may appear in multiple issue rows.
- This table does not need to sum to the cohort total.
- Do not count raw insight rows as leads.
- Exclude `unknown` from the main issue ranking.
- Show unknown and no-text insight counts in the coverage note.

Default display limit:

```text
top 10 known issues
```

Allow top 20 only if the user explicitly asks:

```text
show more
show top 20
show detailed breakdown
show all major reasons
```

Formula:

```text
% of dropped leads = leads_with_issue / selected_cohort_leads
% of all issue mentions = leads_with_issue / total_known_lead_issue_mentions
```

Where:

```text
total_known_lead_issue_mentions = sum of distinct lead counts across all known reason categories
```

---

## User-Friendly Labels

Do not show raw enum values in the final answer.

Use readable labels.

### reason_category Mapping

```text
price_or_budget -> Price or budget concern
timing_issue -> Not ready yet / needs more time
not_decision_maker -> Not the decision-maker
needs_partner_approval -> Waiting for partner or decision-maker approval
trust_issue -> Needs more trust or proof
low_intent -> Low buying intent
unclear_need -> Need or goal is unclear
poor_fit -> Not a strong fit
competition -> Comparing with another option
too_busy -> Too busy right now
needs_more_information -> Needs clearer information
payment_friction -> Payment issue or payment not completed
contract_friction -> Contract signing issue
no_show -> Missed or cancelled call
ghosted -> Stopped responding
follow_up_pending -> Follow-up still pending
operational_delay -> Internal or operational delay
technical_issue -> Link or technical issue
language_or_communication_issue -> Communication issue
location_or_timezone_issue -> Location or timezone issue
already_solved -> Problem already solved
unknown -> Reason not clear
```

For combination labels, join the user-friendly labels with ` + `.

Example:

```text
timing_issue + needs_partner_approval
```

Display as:

```text
Not ready yet / needs more time + Waiting for partner or decision-maker approval
```

---

## Coverage Note Rules

Every text-reason funnel answer must include a coverage note.

Coverage values must reconcile:

```text
selected_cohort_leads = leads_with_usable_text_insight + leads_without_usable_text_insight

leads_with_usable_text_insight = known_reason_leads + unknown_reason_leads
```

Use this wording style:

```text
The text reason analysis is directional. Out of <selected_cohort_leads> <cohort label>, <leads_with_usable_text_insight> had usable text insight coverage. <known_reason_leads> had a known reason, <leads_without_usable_text_insight> had no usable text insight, and <unknown_reason_leads> had text but the reason was still unclear.
```

If the numbers do not reconcile, do not show the reason tables. Return a safe limitation:

```text
The text reason breakdown could not be safely reconciled with the selected funnel cohort, so I am not showing the reason tables for this answer.
```

---

## Final Answer Validation Checklist

Before returning the final answer, validate all of the following:

```text
1. The selected stuck/drop cohort appears with one count only.
2. The reason combination table total equals selected_cohort_leads.
3. The coverage note total equals selected_cohort_leads.
4. The text reason tool cohort_name matches the selected stuck/drop cohort.
5. Raw enum values are not shown to the user.
6. Raw lead IDs, emails, phones, source record IDs, transcript links, recording links, and raw text are not shown.
7. Other lower-volume combinations is at the bottom.
8. Unknown/no-text counts are shown as coverage limitations, not as main business reasons.
```

---

## Corrected Sample Answer Style

Use this as the expected style for:

```text
Where are we losing people on funnel?
```

Sample with dummy/demo numbers:

```text
The biggest leak is after completed calls: people are getting to the call, but many are not moving to signed contracts.

For leads created between 2025-10-25 and 2026-04-24, 515 leads entered the funnel.

| Funnel stage | Leads | What this means |
|---|---:|---|
| Total leads | 515 | All leads in the selected period |
| Never booked a call | 97 | Leads did not reach the appointment stage |
| Booked but did not complete call | 122 | Leads booked a call but did not attend/complete it |
| Completed call but did not sign | 158 | Leads attended the call but did not move to signed contract |
| Signed but not paid | 3 | Leads signed but payment was not completed |
| Paid / converted | 135 | Leads completed the paid conversion path |

What this means:

The biggest visible stuck group is Completed call but did not sign, with 158 leads.
There is also a meaningful earlier leak at Booked but did not complete call, with 122 leads.
Once leads sign, payment leakage looks small, with only 3 signed leads not paid.

So the main issue is not only lead generation or call booking. The biggest business problem is post-call conversion into signed contracts.

Known reasons for the biggest stuck group: Completed call but did not sign

Out of 158 completed-call leads who did not sign, 131 leads had usable text insight coverage.
125 leads had a known reason, 27 leads had no usable text insight, and 6 leads had text but the reason was still unclear.

| Issue combination | Leads | % of dropped leads |
|---|---:|---:|
| No usable text insight available | 27 | 17.09% |
| Not ready yet / needs more time | 12 | 7.59% |
| Needs clearer information | 7 | 4.43% |
| Waiting for partner or decision-maker approval | 7 | 4.43% |
| Reason not clear | 6 | 3.80% |
| Payment issue or payment not completed | 5 | 3.16% |
| Price or budget concern | 5 | 3.16% |
| Needs more trust or proof | 5 | 3.16% |
| Need or goal is unclear | 4 | 2.53% |
| Other lower-volume combinations | 80 | 50.63% |
| Total | 158 | 100.00% |

Reason combinations are fragmented, so the individual issue view is more useful than the combination view.

Individual issue view:

One lead can have multiple issues, so this table does not sum to 158.

| Issue | Leads with this issue | % of dropped leads | % of all issue mentions |
|---|---:|---:|---:|
| Not ready yet / needs more time | 50 | 31.65% | 19.31% |
| Waiting for partner or decision-maker approval | 35 | 22.15% | 13.51% |
| Follow-up still pending | 32 | 20.25% | 12.36% |
| Needs clearer information | 28 | 17.72% | 10.81% |
| Needs more trust or proof | 22 | 13.92% | 8.49% |
| Price or budget concern | 19 | 12.03% | 7.34% |
| Payment issue or payment not completed | 15 | 9.49% | 5.79% |
| Link or technical issue | 10 | 6.33% | 3.86% |
| Missed or cancelled call | 9 | 5.70% | 3.47% |
| Not a strong fit | 9 | 5.70% | 3.47% |

What this points to:

The largest funnel leak is happening after the sales call. The known text reasons suggest that many leads are not immediately rejecting the offer, but are getting stuck because they need more time, need approval from a partner or decision-maker, need clearer information, or need more trust/proof before signing.

This means the business should focus first on post-call follow-up and signing conversion, not only on generating more leads.

Coverage note:

The text reason analysis is directional. Out of 158 completed-call leads who did not sign, 131 had usable text insight coverage, which is 82.91%.
125 leads had a known reason, 27 had no usable text insight, and 6 had text but the reason was still unclear.

Recommended next action:

First, focus on post-call conversion. Tighten follow-up speed, improve the post-call recap, and create specific follow-up material for:

1. Leads who need more time.
2. Leads waiting for partner or decision-maker approval.
3. Leads who need more proof or trust.
4. Leads with price or budget concerns.

Second, review the 122 booked-but-not-completed leads, because attendance leakage is still the second major bottleneck before the sales call can even happen.
```

---

## Files To Update

Update whichever files currently implement the diagnostic flow in the repo. Based on the current project structure, this likely includes:

```text
app/tools/diagnostic_tools.py
app/skills/modules/diagnostic_analytics.md
app/agents/diagnostic_agent/builder.py only if tool registration changes are needed
app/prompts/router.md only if new examples are missing
```

Do not modify:

```text
diagnostic_lead_snapshot builder logic unless required for missing columns
diagnostic_text_insights flattening logic
normal SQL analytics agent
Lead 360 agent
read-only SQL safety validator unless the new table must be added as an allowed business table
```

If `diagnostic_text_insights` is queried through the shared read-only SQL helper, add it to the allowed business tables list if required by validation.

---

## Tests To Add

### Test 1: Cohort Consistency

Input:

```text
Where are we losing people on funnel?
```

Expected:

```text
The selected stuck/drop cohort count equals the reason combination table total.
The selected stuck/drop cohort count equals the coverage note total.
No conflicting count appears for the same cohort.
```

### Test 2: Other Row Placement

Expected:

```text
Other lower-volume combinations appears near the bottom of the combination table, before Total if Total is shown.
```

### Test 3: User-Friendly Labels

Expected:

```text
The final answer does not show raw enum values such as timing_issue, price_or_budget, or needs_partner_approval.
```

### Test 4: Distinct Lead Counting

Expected:

```text
Individual issue distribution counts distinct leads, not raw insight rows.
```

### Test 5: Missing Text Coverage

Expected:

```text
Leads with no usable text insight are shown in the coverage note and combination table.
```

### Test 6: Unsafe Data Not Exposed

Expected:

```text
No lead_id, email, phone, source_record_id, raw text, transcript link, or recording link appears in the answer.
```

---

## Completion Criteria

This task is complete only when:

```text
1. Funnel leakage answers use explicit stuck/drop cohorts.
2. Text reason tool uses the exact same selected cohort.
3. The final answer no longer displays different counts for the same group.
4. Reason combination distribution sums exactly to the selected cohort count.
5. Coverage note reconciles exactly to the selected cohort count.
6. User-friendly labels are used in all final answer tables.
7. Top 10 default limits are applied.
8. Unknown and no-text coverage are shown clearly.
9. The corrected sample style can be reproduced for “Where are we losing people on funnel?”
```
