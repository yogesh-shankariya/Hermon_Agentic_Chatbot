# Codex Task: Add Diagnostic Text Insight Reasons To Diagnostic Analytics

## Goal

Add the new `diagnostic_text_insights` table into the existing Diagnostic Analytics flow so that broad diagnostic questions can explain not only **where** leads are dropping in the funnel, but also **why** they appear to be dropping based on safe extracted text insight enums.

The main target question is:

```text
Where are we losing people in the funnel?
```

After this implementation, the answer should still start with the numeric funnel movement from `diagnostic_lead_snapshot`, then add a concise text-reason explanation for the biggest dropped/stuck cohort, for example completed-call leads who did not sign or pay.

---

## Current Design Constraints

The current diagnostic agent is intentionally separate from normal SQL analytics and Lead 360.

Keep these rules unchanged:

```text
Do not generate SQL in the diagnostic agent.
Do not call run_readonly_sql.
Do not call load_skill.
Do not call Lead 360 tools.
Do not expose raw text, raw notes, raw call summaries, raw form answers, links, emails, phones, IDs, payloads, credentials, or provider references.
Use only controlled diagnostic tools.
```

The new text-reason capability must be added as a controlled diagnostic tool, not as free-form SQL generation.

---

## Existing Tables

### 1. Existing numeric diagnostic table

```text
diagnostic_lead_snapshot
```

Grain:

```text
one row per lead
```

Use this for numeric funnel, source, revenue, payment, contract, and data-quality signals.

Important fields used by this task:

```text
clerk_org_id
lead_id
lead_created_at
appointment_count
completed_call_count
signed_contract_count
paid_payment_count
contract_count
payment_count
funnel_stage
conversion_outcome
net_collected_amount
outstanding_amount
source_confidence
first_source
last_source
```

Money fields in this table are already major-unit EUR values. Do not divide by 100.

The diagnostic snapshot uses `lead_created_at` cohort logic. Revenue/payment values are lifetime outcomes for leads created in the selected period, not true payment-period revenue.

### 2. New text insight table

```text
diagnostic_text_insights
```

Grain:

```text
one row per extracted insight
```

Important consequence:

```text
One lead can have multiple text insight rows.
Therefore, never count raw insight rows as leads.
Always aggregate to DISTINCT lead_id first.
```

Important fields:

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

Do not use or expose raw text. The flattened table must not contain raw text or `llm_output_json`.

---

## What To Build

Build one new read-only diagnostic tool:

```text
get_diagnostic_text_reason_snapshot
```

This tool must join:

```text
diagnostic_lead_snapshot dls
LEFT JOIN diagnostic_text_insights dti
```

The join must be tenant-safe:

```sql
dti.clerk_org_id = dls.clerk_org_id
AND dti.lead_id = dls.lead_id
```

The tool must return lead-level text reason evidence for a selected dropped/stuck cohort.

---

## Files To Update

Update these files:

```text
app/tools/diagnostic_tools.py
app/tools/__init__.py
app/skills/modules/diagnostic_analytics.md
app/prompts/router.md
```

Add or update tests, using the closest existing test files in the repo:

```text
tests/test_diagnostic_text_reason_tool.py
tests/test_diagnostic_agent_prompt.py
tests/test_orchestrator.py
tests/test_router.py
```

If the repo uses different existing test names, update the closest matching files instead.

---

## Do Not Modify

Do not modify these unless tests prove a direct compatibility issue:

```text
app/agents/sql_agent/*
app/agents/lead_360/*
app/tools/lead_360*
normal SQL analytics skills
revenue_analytics.md
lead_analytics.md
appointment_analytics.md
acquisition_analytics.md
```

Do not rebuild or refresh `diagnostic_lead_snapshot` from this task.

Do not call the LLM in this task.

Do not regenerate diagnostic text extraction JSONL.

Do not change the flattened text extraction script unless the table itself is missing or invalid.

---

## New Tool: `get_diagnostic_text_reason_snapshot`

### Purpose

Use this tool to answer broad questions like:

```text
After completed calls, why are leads not signing?
After completed calls, why are leads not paying?
Where are we losing people in the funnel, and why?
What are the main post-call blockers?
Why are attended leads not converting?
Why do signed leads not pay?
What reasons are stopping completed-call leads from becoming signed or paid?
```

### Not For

Do not use this tool for:

```text
one specific lead
single customer journey
raw transcript review
raw call-summary search
raw note search
ad attribution
ROAS
cost per lead
cost per sale
Facebook Ads performance
YouTube attribution
revenue by UTM campaign
revenue by landing page
revenue by referrer
```

---

## Tool Function Signature

Add a plain Python function and a LangChain tool wrapper following the same pattern as the existing diagnostic tools.

Suggested plain function:

```python
def get_diagnostic_text_reason_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    cohort_name: str = "completed_not_paid",
    reason_limit: int = 10,
    combination_limit: int = 10,
    subcategory_limit: int = 10,
    blockers_only: bool = False,
) -> dict[str, Any]:
    ...
```

Suggested tool wrapper:

```python
def _get_diagnostic_text_reason_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    cohort_name: str = "completed_not_paid",
    reason_limit: int = 10,
    combination_limit: int = 10,
    subcategory_limit: int = 10,
    blockers_only: bool = False,
) -> str:
    ...
```

Expose as:

```python
get_diagnostic_text_reason_snapshot_tool = tool("get_diagnostic_text_reason_snapshot")(
    _get_diagnostic_text_reason_snapshot_tool
)
```

Add it to:

```python
DIAGNOSTIC_TOOLS = [
    get_diagnostic_funnel_snapshot_tool,
    get_diagnostic_source_snapshot_tool,
    get_diagnostic_source_quality_snapshot_tool,
    get_diagnostic_business_change_snapshot_tool,
    get_diagnostic_text_reason_snapshot_tool,
]
```

---

## Tool Input Rules

### `org_id`

Use the same `_default_org_id()` behavior already used by diagnostic tools.

### `current_start_date` and `current_end_date`

Use the same date handling as existing diagnostic tools.

The date filter must apply to:

```text
dls.lead_created_at
```

Do not filter primarily by `dti.source_event_at`, because the diagnostic snapshot is a lead-created cohort view and the text insights explain the lifetime outcome of those selected leads.

The SQL must use:

```sql
dls.lead_created_at >= :start_date
AND dls.lead_created_at < :end_date
```

### `cohort_name`

Allowed values:

```text
lead_not_booked
booked_not_completed
completed_not_signed
signed_not_paid
completed_not_paid
not_converted_paid
all_active_not_paid
```

If an invalid value is passed, return a safe error response.

Use these definitions:

```text
lead_not_booked:
  appointment_count = 0
  paid_payment_count = 0

booked_not_completed:
  appointment_count > 0
  completed_call_count = 0
  paid_payment_count = 0

completed_not_signed:
  completed_call_count > 0
  signed_contract_count = 0
  paid_payment_count = 0

signed_not_paid:
  signed_contract_count > 0
  paid_payment_count = 0

completed_not_paid:
  completed_call_count > 0
  paid_payment_count = 0

not_converted_paid:
  paid_payment_count = 0

all_active_not_paid:
  paid_payment_count = 0
  AND conversion_outcome NOT IN ('lost', 'unqualified', 'refunded')
```

Default should be:

```text
completed_not_paid
```

Reason: when a user asks “after call completion, why are people not converting?”, the safest broad interpretation is completed calls that have not reached paid conversion.

### Limits

Use default top 10.

```text
reason_limit default = 10
combination_limit default = 10
subcategory_limit default = 10
```

Clamp safely:

```text
minimum = 1
maximum = 20
```

Only return top 20 if the user explicitly asks for more detail.

### `blockers_only`

When `blockers_only = true`, only include insights where:

```sql
dti.is_conversion_blocker = true
```

Default:

```text
false
```

Use `blockers_only = true` only when the user explicitly asks for blockers.

---

## User-Friendly Labels

Do not show raw enum values like `timing_issue` or `price_or_budget` in final business answers.

Implement a Python mapping inside `app/tools/diagnostic_tools.py`, or return both raw and display labels and instruct the prompt to use display labels.

Preferred: return display labels directly in the tool output, while optionally keeping raw enum keys for debugging/internal tests.

### Reason Category Labels

```python
REASON_CATEGORY_LABELS = {
    "price_or_budget": "Price or budget concern",
    "timing_issue": "Not ready yet / needs more time",
    "not_decision_maker": "Not the decision-maker",
    "needs_partner_approval": "Waiting for partner or decision-maker approval",
    "trust_issue": "Needs more trust or proof",
    "low_intent": "Low buying intent",
    "unclear_need": "Need or goal is unclear",
    "poor_fit": "Not a strong fit",
    "competition": "Comparing with another option",
    "too_busy": "Too busy right now",
    "needs_more_information": "Needs clearer information",
    "payment_friction": "Payment issue or payment not completed",
    "contract_friction": "Contract signing issue",
    "no_show": "Missed or cancelled call",
    "ghosted": "Stopped responding",
    "follow_up_pending": "Follow-up still pending",
    "operational_delay": "Internal or operational delay",
    "technical_issue": "Link or technical issue",
    "language_or_communication_issue": "Communication issue",
    "location_or_timezone_issue": "Location or timezone issue",
    "already_solved": "Problem already solved",
    "unknown": "Reason not clear",
}
```

### Reason Subcategory Labels

```python
REASON_SUBCATEGORY_LABELS = {
    "price_too_high": "Price felt too high",
    "budget_not_available": "Budget not available right now",
    "wants_discount": "Asked for discount",
    "needs_payment_plan": "Needs a payment plan",
    "not_ready_now": "Not ready right now",
    "needs_more_time": "Needs more time before deciding",
    "waiting_for_partner": "Waiting for partner approval",
    "waiting_for_team": "Waiting for team input",
    "waiting_for_finance": "Waiting for finance approval",
    "does_not_trust_offer": "Does not fully trust the offer yet",
    "needs_proof_or_case_study": "Needs proof or case studies",
    "unclear_value": "Value is not clear enough",
    "comparing_competitor": "Comparing with another option",
    "not_enough_need": "Need is not strong enough",
    "wrong_customer_fit": "Not the right customer fit",
    "not_qualified": "Not qualified",
    "missed_call": "Missed the call",
    "cancelled_call": "Cancelled the call",
    "stopped_responding": "Stopped responding",
    "needs_more_information": "Needs more information",
    "contract_not_signed": "Contract not signed",
    "payment_not_completed": "Payment not completed",
    "payment_failed": "Payment failed",
    "refund_requested": "Refund requested",
    "internal_team_delay": "Internal team delay",
    "system_or_link_issue": "System or link issue",
    "language_barrier": "Language barrier",
    "timezone_issue": "Timezone issue",
    "issue_already_solved": "Issue already solved",
    "other": "Other reason",
    "unknown": "Reason not clear",
}
```

### Buying Intent Labels

```python
BUYING_INTENT_LABELS = {
    "very_high": "Very high intent",
    "high": "High intent",
    "medium": "Medium intent",
    "low": "Low intent",
    "very_low": "Very low intent",
    "unknown": "Intent not clear",
}
```

---

## Output Shape

The tool must return JSON with this shape:

```json
{
  "status": "success",
  "tool": "get_diagnostic_text_reason_snapshot",
  "scope_note": "...",
  "period": {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "display_start_date": "YYYY-MM-DD",
    "display_end_date": "YYYY-MM-DD",
    "date_range_display": "YYYY-MM-DD to YYYY-MM-DD",
    "anchor_date": "YYYY-MM-DD",
    "date_field": "lead_created_at"
  },
  "cohort": {
    "cohort_name": "completed_not_paid",
    "cohort_label": "Completed call but not paid",
    "cohort_definition": "completed_call_count > 0 AND paid_payment_count = 0",
    "total_leads": 80
  },
  "text_insight_coverage": {
    "leads_with_text_insights": 72,
    "leads_without_text_insights": 8,
    "text_insight_coverage_rate": 90.0,
    "known_reason_leads": 62,
    "unknown_only_reason_leads": 10,
    "known_reason_coverage_rate": 77.5,
    "unknown_or_missing_reason_leads": 18,
    "unknown_or_missing_reason_rate": 22.5
  },
  "reason_combination_distribution": [
    {
      "issue_combination": "Not ready yet / needs more time + Waiting for partner or decision-maker approval",
      "issue_combination_raw": "timing_issue + needs_partner_approval",
      "lead_count": 18,
      "share_of_cohort_leads": 22.5
    }
  ],
  "individual_issue_distribution": [
    {
      "reason_category": "Not ready yet / needs more time",
      "reason_category_raw": "timing_issue",
      "leads_with_issue": 28,
      "share_of_cohort_leads": 35.0,
      "share_of_all_known_issue_mentions": 30.43
    }
  ],
  "top_reason_subcategories": [
    {
      "reason_subcategory": "Needs more time before deciding",
      "reason_subcategory_raw": "needs_more_time",
      "leads_with_subcategory": 20,
      "share_of_cohort_leads": 25.0
    }
  ],
  "buying_intent_breakdown": [
    {
      "buying_intent_level": "Medium intent",
      "buying_intent_level_raw": "medium",
      "lead_count": 40,
      "share_of_cohort_leads": 50.0
    }
  ],
  "source_text_type_breakdown": [
    {
      "source_text_type": "call_summary",
      "lead_count": 50
    }
  ],
  "display_limits": {
    "reason_limit": 10,
    "combination_limit": 10,
    "subcategory_limit": 10
  },
  "limitations": [
    "Text reasons are extracted from available structured text insight enums, not raw transcripts.",
    "One lead may have multiple issues, so individual issue counts do not sum to the cohort total.",
    "The combination distribution assigns each lead to exactly one combination row and must sum to the cohort total."
  ]
}
```

---

## SQL Logic Requirements

The SQL must use fixed templates and named parameters.

Do not use `SELECT *`.

Do not select raw text.

Do not select:

```text
email
phone
meeting_url
recording_url
transcript_url
payment links
checkout links
raw_payload
raw notes
raw summaries
source_record_id in final returned output
```

Selecting `source_record_id` inside a CTE only for deduplication is allowed, but do not return it.

### Base scoped cohort

Use this pattern conceptually:

```sql
WITH scoped_leads AS (
  SELECT
    dls.clerk_org_id,
    dls.lead_id
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= :start_date
    AND dls.lead_created_at < :end_date
    AND <cohort condition from allowlist>
)
```

The cohort condition must be selected from a Python allowlist, not generated dynamically by the model.

### Text rows

Use only successful text insight rows:

```sql
text_rows AS (
  SELECT
    sl.lead_id,
    dti.reason_category,
    dti.reason_subcategory,
    dti.is_conversion_blocker,
    dti.buying_intent_level,
    dti.lead_quality_level,
    dti.profession_category,
    dti.employment_status,
    dti.source_text_type
  FROM scoped_leads sl
  JOIN diagnostic_text_insights dti
    ON dti.clerk_org_id = sl.clerk_org_id
   AND dti.lead_id = sl.lead_id
  WHERE dti.extraction_status = 'success'
    AND (:blockers_only = false OR dti.is_conversion_blocker = true)
)
```

### Lead-level coverage

Calculate these lead-level metrics:

```text
total_cohort_leads
leads_with_text_insights
leads_without_text_insights
known_reason_leads
unknown_only_reason_leads
known_reason_coverage_rate
unknown_or_missing_reason_leads
unknown_or_missing_reason_rate
```

A known reason is:

```sql
reason_category IS NOT NULL
AND reason_category <> 'unknown'
```

### Reason combination distribution

This distribution answers:

```text
Out of the dropped leads, what combination of issues did each lead have?
```

Rules:

```text
Each lead must appear in exactly one combination row.
The table must sum to total_cohort_leads.
Known reason categories should be sorted alphabetically inside the combination.
Exclude unknown from known issue combinations.
If a lead has text insights but no known reason, bucket as unknown_reason.
If a lead has no text insights, bucket as no_text_insight_available.
Limit to top 10 by default.
Aggregate lower-volume known combinations into Other lower-volume combinations.
Keep unknown_reason and no_text_insight_available as separate rows.
```

Pseudo SQL approach:

```sql
known_reasons_per_lead AS (
  SELECT DISTINCT
    lead_id,
    reason_category
  FROM text_rows
  WHERE reason_category IS NOT NULL
    AND reason_category <> 'unknown'
),
text_coverage_per_lead AS (
  SELECT
    sl.lead_id,
    COUNT(tr.lead_id) AS text_insight_count,
    COUNT(kr.reason_category) AS known_reason_count
  FROM scoped_leads sl
  LEFT JOIN text_rows tr
    ON tr.lead_id = sl.lead_id
  LEFT JOIN known_reasons_per_lead kr
    ON kr.lead_id = sl.lead_id
  GROUP BY sl.lead_id
),
lead_reason_combinations AS (
  SELECT
    sl.lead_id,
    CASE
      WHEN COUNT(kr.reason_category) > 0
      THEN STRING_AGG(kr.reason_category, ' + ' ORDER BY kr.reason_category)
      WHEN MAX(tc.text_insight_count) > 0
      THEN 'unknown_reason'
      ELSE 'no_text_insight_available'
    END AS issue_combination_raw
  FROM scoped_leads sl
  LEFT JOIN known_reasons_per_lead kr
    ON kr.lead_id = sl.lead_id
  LEFT JOIN text_coverage_per_lead tc
    ON tc.lead_id = sl.lead_id
  GROUP BY sl.lead_id
),
combination_rollup AS (
  SELECT
    issue_combination_raw,
    COUNT(*)::int AS lead_count
  FROM lead_reason_combinations
  GROUP BY issue_combination_raw
)
```

Apply top-N limiting in Python after retrieving the rollup, or in SQL using `ROW_NUMBER()`. Python is simpler and less error-prone because you also need to preserve `unknown_reason` and `no_text_insight_available` as separate rows.

After limiting, verify in Python:

```python
sum(row["lead_count"] for row in reason_combination_distribution) == total_cohort_leads
```

If the sum does not match, raise/return a safe tool error.

### Individual issue distribution

This distribution answers:

```text
Across the same dropped leads, how many leads had each issue?
```

Rules:

```text
Count DISTINCT lead_id per reason_category.
Exclude unknown from the main ranking.
One lead can appear under multiple issues.
This table does not need to sum to total_cohort_leads.
Limit to top 10 by default.
```

Pseudo SQL:

```sql
SELECT
  reason_category,
  COUNT(DISTINCT lead_id)::int AS leads_with_issue
FROM text_rows
WHERE reason_category IS NOT NULL
  AND reason_category <> 'unknown'
GROUP BY reason_category
ORDER BY leads_with_issue DESC, reason_category ASC
LIMIT :reason_limit
```

Calculate:

```text
share_of_cohort_leads = leads_with_issue / total_cohort_leads
share_of_all_known_issue_mentions = leads_with_issue / SUM(leads_with_issue over known reason categories)
```

Important: `SUM(leads_with_issue)` can be greater than total cohort leads because one lead can have multiple known issues.

### Reason subcategory distribution

Use this as supporting detail only.

Rules:

```text
Count DISTINCT lead_id per reason_subcategory.
Exclude unknown from main ranking.
Limit to top 10 by default.
Use user-friendly labels.
```

### Buying intent breakdown

Return all buying intent values because there are only a few values.

Use display labels:

```text
Very high intent
High intent
Medium intent
Low intent
Very low intent
Intent not clear
```

### Lead quality, profession, employment

Do not show by default in final answers.

Reason: these fields can have high unknown coverage.

The tool may return coverage stats for these fields, but the prompt should not display them unless the user explicitly asks and coverage is acceptable.

---

## Python Post-Processing Requirements

Implement helper functions in `app/tools/diagnostic_tools.py`:

```python
def _safe_top_limit(limit: int | None, *, default: int = 10, maximum: int = 20) -> int:
    ...


def _reason_category_label(value: str | None) -> str:
    ...


def _reason_subcategory_label(value: str | None) -> str:
    ...


def _buying_intent_label(value: str | None) -> str:
    ...


def _display_issue_combination(raw_combination: str) -> str:
    ...
```

`_display_issue_combination()` must handle:

```text
unknown_reason -> Reason not clear
no_text_insight_available -> No usable text insight available
other_lower_volume_combinations -> Other lower-volume combinations
```

For normal combinations:

```text
timing_issue + needs_partner_approval
```

return:

```text
Not ready yet / needs more time + Waiting for partner or decision-maker approval
```

---

## Recommended Change To Existing Funnel Tool

Update `get_diagnostic_funnel_snapshot` response to include optional recommended text cohorts.

Add a derived field:

```json
"recommended_text_cohorts": [
  {
    "cohort_name": "completed_not_signed",
    "cohort_label": "Completed call but did not sign",
    "lead_count": 80,
    "reason": "Largest stuck group after completed calls"
  },
  {
    "cohort_name": "signed_not_paid",
    "cohort_label": "Signed but not paid",
    "lead_count": 26,
    "reason": "Payment-stage leakage"
  }
]
```

Keep this backward-compatible. Do not remove existing fields.

Recommended cohort ranking for general funnel leakage:

```text
1. completed_not_signed
2. signed_not_paid
3. booked_not_completed
4. lead_not_booked
```

Only include cohorts where lead_count > 0.

Limit to top 2 by default.

This helps the diagnostic agent know which cohort to pass into `get_diagnostic_text_reason_snapshot` after calling `get_diagnostic_funnel_snapshot`.

---

## Update `app/tools/__init__.py`

Add imports:

```python
from app.tools.diagnostic_tools import (
    get_diagnostic_text_reason_snapshot,
    get_diagnostic_text_reason_snapshot_tool,
)
```

Add to `__all__`:

```python
"get_diagnostic_text_reason_snapshot",
"get_diagnostic_text_reason_snapshot_tool",
```

Make sure `DIAGNOSTIC_TOOLS` exported from `diagnostic_tools.py` now includes the new tool.

---

## Update `diagnostic_analytics.md`

Add the new tool to the available diagnostic tools section:

```text
get_diagnostic_funnel_snapshot
get_diagnostic_source_snapshot
get_diagnostic_source_quality_snapshot
get_diagnostic_business_change_snapshot
get_diagnostic_text_reason_snapshot
```

Update the table-read scope from:

```text
diagnostic_lead_snapshot
```

to:

```text
diagnostic_lead_snapshot
diagnostic_text_insights
```

But make clear:

```text
The diagnostic agent can use diagnostic_text_insights only through get_diagnostic_text_reason_snapshot.
```

Add the following sections to `diagnostic_analytics.md`.

```markdown
---

## Diagnostic Text Insight Layer

The diagnostic agent may use text insight evidence only through this controlled tool:

```text
get_diagnostic_text_reason_snapshot
```

This tool reads only:

```text
diagnostic_lead_snapshot
diagnostic_text_insights
```

Use this tool for broad post-call and funnel-drop reason questions, such as:

```text
After completed calls, why are leads not signing?
After completed calls, why are leads not paying?
Why are attended leads not converting?
What are the main post-call blockers?
Where are we losing people in the funnel, and why?
```

Do not use this tool for one specific lead. Single-lead questions must go to Lead 360.

Do not generate SQL.
Do not call normal SQL analytics tools.
Do not expose raw text, raw notes, raw call summaries, raw objections, transcript links, recording links, lead IDs, emails, phones, source record IDs, or provider IDs.

### Text Reason Tool Selection

For general funnel leakage questions such as:

```text
Where are we losing people in the funnel?
Why are leads not converting?
Which funnel stage is the biggest bottleneck?
```

Call:

```text
get_diagnostic_funnel_snapshot
```

Then, if the funnel output shows meaningful dropped or stuck cohorts, call:

```text
get_diagnostic_text_reason_snapshot
```

Use the text reason tool only for the top 1-2 largest dropped/stuck cohorts, not for all leads by default.

For post-call questions, prioritize:

```text
completed_not_signed
signed_not_paid
completed_not_paid
```

For pre-call attendance issues, use:

```text
booked_not_completed
```

### Text Reason Aggregation Rules

The text insight table has one row per extracted insight, and one lead may have multiple insight rows.

Therefore:

```text
Never count raw insight rows as leads.
Always use distinct lead counts from tool output.
```

Use `reason_category` as the primary issue field.
Use `reason_subcategory` only for deeper explanation after the main reason category result.
Use `buying_intent_level` only as supporting context.
Do not show `lead_quality_level`, `profession_category`, or `employment_status` by default because these fields may have high unknown coverage.

### Reason Combination Distribution

For each dropped/stuck cohort, use the reason combination distribution to answer:

```text
Out of the dropped leads, what combination of issues did each lead have?
```

Rules:

- Each dropped/stuck lead appears in exactly one combination row.
- The combination table must sum to the total dropped/stuck lead count.
- Known reason categories are combined into one readable issue combination.
- Leads with text but no known reason are shown as `Reason not clear`.
- Leads without usable text insight are shown as `No usable text insight available`.

Use this table format:

| Issue combination | Leads | % of dropped leads |
|---|---:|---:|

### Individual Issue Distribution

Use the individual issue distribution to answer:

```text
Across the same dropped leads, how many leads had each issue?
```

Rules:

- Count distinct leads per issue.
- One lead can appear under multiple issues.
- This table does not need to sum to the dropped/stuck lead count.
- Use readable issue labels, not raw enum values.

Use this table format:

| Issue | Leads with this issue | % of dropped leads | % of all issue mentions |
|---|---:|---:|---:|

### Display Limits For Text Reason Tables

Keep diagnostic text-reason answers concise and business-friendly.

Default limits:

```text
reason_combination_distribution: top 10
individual_issue_distribution: top 10
top_reason_subcategories: top 10
buying_intent_breakdown: all values
```

Only show top 20 when the user explicitly asks for more detail, such as:

```text
show more
show top 20
give me detailed breakdown
show all major reasons
```

Do not show all enum values by default.

For the written diagnosis, mention only the top 3-5 known reasons.

If there are more reasons beyond the displayed limit, add a short note:

```text
Showing the top 10 known reasons. Smaller reason groups are grouped under other lower-volume reasons.
```

### Unknown Handling

Do not hide unknowns.

Show these separately when available:

```text
unknown_only_reason_leads
leads_without_text_insights
text_insight_coverage_rate
known_reason_coverage_rate
```

Do not make unknown the main business conclusion unless unknown/no-text coverage is the main finding.

Use cautious wording when coverage is incomplete:

```text
Among leads where a reason was detected...
The known text reasons point to...
This is directional because some dropped leads have unknown or missing text reasons.
```

### User-Friendly Text Reason Labels

Never show raw diagnostic text enum values directly to the business user.

The tool may return stable enum values such as:

```text
timing_issue
price_or_budget
needs_partner_approval
trust_issue
payment_friction
contract_friction
ghosted
unknown
```

But the final answer must display readable business labels.

Examples:

```text
timing_issue -> Not ready yet / needs more time
price_or_budget -> Price or budget concern
needs_partner_approval -> Waiting for partner or decision-maker approval
trust_issue -> Needs more trust or proof
needs_more_information -> Needs clearer information
payment_friction -> Payment issue or payment not completed
contract_friction -> Contract signing issue
ghosted -> Stopped responding
unknown -> Reason not clear
```

For issue-combination tables, combine user-friendly labels.

Do not show snake_case enum values unless the user explicitly asks for raw technical fields.

### Funnel Answer Format With Text Reasons

For funnel leakage questions, use this structure:

```text
<One-line diagnosis>

For leads created between <display_start_date> and <display_end_date>, <total_leads> leads entered the funnel.

Funnel movement:
<funnel movement table from get_diagnostic_funnel_snapshot>

Biggest stuck/drop area:
<short explanation of the largest drop or stuck cohort>

Known reasons for this stuck group:
<reason combination distribution table>

Individual issue view:
<individual issue distribution table>

What this points to:
<short business interpretation connecting numeric drop + text reasons>

Coverage note:
<text insight coverage, unknown reason count, no-text count if available>

Recommended next action:
<1-2 actions tied to the top known reasons>
```

### Recommendation Mapping

Tie recommendations to the known reasons:

```text
Price or budget concern -> Review pricing objection handling and payment-plan explanation.
Needs more trust or proof -> Add proof, testimonials, case studies, or expectation-setting material.
Waiting for partner or decision-maker approval -> Send partner/decision-maker follow-up material.
Not ready yet / needs more time -> Create a structured follow-up sequence for not-ready-now leads.
Needs clearer information -> Improve post-call recap, FAQ, and next-step clarity.
Payment issue or payment not completed -> Check payment links, failed payment cases, and payment-plan process.
Contract signing issue -> Review contract signing reminders and signing flow.
Stopped responding -> Improve follow-up speed and response discipline.
Missed or cancelled call -> Review appointment reminders and rescheduling process.
Link or technical issue -> Check links, system access, and payment/contract technical flow.
```

Do not recommend ad-spend changes from text reasons alone.
```

---

## Update Tool Selection Section In `diagnostic_analytics.md`

Change the current rule for:

```text
Where are we losing people in the funnel?
```

From:

```text
Use get_diagnostic_funnel_snapshot
```

To:

```text
Use get_diagnostic_funnel_snapshot first.
Then, if the funnel output identifies a meaningful stuck/dropped cohort, use get_diagnostic_text_reason_snapshot for the top stuck cohort.
```

Add examples:

```text
Question: Where are we losing people in the funnel?
Tools:
1. get_diagnostic_funnel_snapshot
2. get_diagnostic_text_reason_snapshot for the biggest stuck cohort

Question: Why are completed calls not converting to signed leads?
Tool:
1. get_diagnostic_text_reason_snapshot with cohort_name = completed_not_signed

Question: Why are signed leads not paying?
Tool:
1. get_diagnostic_text_reason_snapshot with cohort_name = signed_not_paid

Question: Why are attended leads not becoming paid customers?
Tool:
1. get_diagnostic_text_reason_snapshot with cohort_name = completed_not_paid
```

---

## Update Router Prompt

In `app/prompts/router.md`, add these examples under `diagnostic_analytics`:

```text
Why are completed calls not converting to signed leads? -> diagnostic_analytics
After calls, why are people not paying? -> diagnostic_analytics
What are the main reasons attended leads do not buy? -> diagnostic_analytics
Why do completed-call leads get stuck before payment? -> diagnostic_analytics
What are the top post-call blockers? -> diagnostic_analytics
Where are we losing people in the funnel and why? -> diagnostic_analytics
Where are we loosing people on funnel? -> diagnostic_analytics
```

Keep one-specific-lead examples routed to Lead 360:

```text
Why did Vedran not pay? -> lead_360
Why did this lead not sign? -> lead_360 when single-lead context exists
```

---

## Example Final Answer After Implementation

This is a sample with dummy numbers. The real answer must use tool output only.

```text
The biggest funnel leak is after completed calls: many leads are attending the call, but not moving to signed contracts. The known text reasons suggest people are often not ready yet, waiting for partner approval, needing more proof, or raising price/budget concerns.

For leads created between 2026-01-01 and 2026-05-10, 281 leads entered the funnel.

Funnel movement:

| Funnel step | Leads reached | Dropped from previous step | Drop % | Conversion % |
|---|---:|---:|---:|---:|
| Total leads | 281 | - | - | 100.00% |
| Booked a call | 218 | 63 | 22.42% | 77.58% |
| Completed a call | 150 | 68 | 31.19% | 53.38% |
| Signed contract | 70 | 80 | 53.33% | 24.91% |
| Paid / converted | 44 | 26 | 37.14% | 15.66% |

Biggest stuck/drop area:

80 leads completed a call but did not sign. This is the largest visible drop after engagement.

Known reasons for this stuck group:

| Issue combination | Leads | % of dropped leads |
|---|---:|---:|
| Not ready yet / needs more time + Waiting for partner or decision-maker approval | 18 | 22.50% |
| Needs more trust or proof + Needs clearer information | 14 | 17.50% |
| Price or budget concern | 12 | 15.00% |
| Not ready yet / needs more time | 10 | 12.50% |
| Payment issue or payment not completed + Contract signing issue | 8 | 10.00% |
| Reason not clear | 10 | 12.50% |
| No usable text insight available | 8 | 10.00% |
| Total | 80 | 100.00% |

Individual issue view:

| Issue | Leads with this issue | % of dropped leads | % of all issue mentions |
|---|---:|---:|---:|
| Not ready yet / needs more time | 28 | 35.00% | 30.43% |
| Waiting for partner or decision-maker approval | 18 | 22.50% | 19.57% |
| Needs more trust or proof | 14 | 17.50% | 15.22% |
| Needs clearer information | 14 | 17.50% | 15.22% |
| Price or budget concern | 12 | 15.00% | 13.04% |
| Payment issue or payment not completed | 4 | 5.00% | 4.35% |
| Contract signing issue | 2 | 2.50% | 2.17% |

What this points to:

The main problem is not only lead volume or call booking. The biggest leakage appears after the sales call. The known reasons suggest that many leads are still undecided, need approval, need more proof, or need clearer post-call information before signing.

Coverage note:

This reason analysis is directional. Out of 80 completed-call leads who did not sign, 62 had known text reasons, 10 had unclear reasons, and 8 had no usable text insight.

Recommended next action:

Focus first on post-call follow-up. Create a structured follow-up sequence for leads who need more time, partner approval, proof/case studies, and pricing clarification.
```

---

## Safety Rules For Final Answers

The final diagnostic answer must never expose:

```text
lead_id
source_record_id
email
phone
meeting link
recording link
transcript link
payment link
checkout link
raw notes
raw call summaries
raw objections
raw form answers
raw payloads
webhook payloads
credentials
API keys
provider IDs
```

The answer may say:

```text
The text-insight layer found known reasons for 62 leads.
```

But must not show the underlying raw text.

---

## Confidence And Coverage Rules

When text coverage is incomplete, mention it naturally.

Use this logic:

```text
High confidence:
  total cohort size is reasonable
  text insight coverage is high
  known reason coverage is high
  one or two reasons dominate clearly

Medium confidence:
  direction is clear
  text insight coverage is decent
  unknown/missing reason rate is noticeable but not overwhelming

Low confidence:
  sample size is small
  many leads have no text insight
  many leads have unknown reasons
  reason categories are too fragmented
```

Do not overclaim causal certainty.

Use cautious wording:

```text
suggests
points to
appears
directionally
among leads where a reason was detected
```

Avoid:

```text
proves
caused by
definitely because of
all leads failed because
```

---

## Minimum Tests

### Test 1: New Tool Is Registered

Assert `DIAGNOSTIC_TOOLS` includes:

```text
get_diagnostic_text_reason_snapshot
```

Assert diagnostic tools still do not include:

```text
load_skill
run_readonly_sql
get_lead_360
```

### Test 2: Tool Rejects Invalid Cohort

Call:

```python
get_diagnostic_text_reason_snapshot(cohort_name="bad_cohort")
```

Expected:

```text
status = error
safe error message
no SQL trace exposed
```

### Test 3: Tool Limit Clamping

Call with:

```python
reason_limit=999
combination_limit=999
subcategory_limit=999
```

Expected limits in output:

```text
20
20
20
```

Call with:

```python
reason_limit=0
```

Expected:

```text
1
```

or default to 10, as long as behavior is deterministic and safe.

### Test 4: Tenant Scope

Inspect or mock SQL execution and assert SQL includes:

```sql
dls.clerk_org_id = :org_id
```

and join includes:

```sql
dti.clerk_org_id = dls.clerk_org_id
AND dti.lead_id = dls.lead_id
```

### Test 5: No Raw/Sensitive Fields Returned

Assert output does not contain:

```text
email
phone
raw_payload
meeting_url
recording_url
transcript_url
source_record_id
raw_text
summary_clean
objection_text
```

### Test 6: Combination Distribution Sums To Cohort Total

For a mocked result or real test org:

```python
sum(row["lead_count"] for row in output["reason_combination_distribution"]) == output["cohort"]["total_leads"]
```

This must always pass.

### Test 7: Individual Issue Distribution Does Not Need To Sum

Assert the code does not force:

```python
sum(leads_with_issue) == total_leads
```

Reason: one lead can have multiple issues.

### Test 8: User-Friendly Labels

Assert final display fields do not contain snake_case labels for reason category display.

Examples:

```text
timing_issue -> Not ready yet / needs more time
price_or_budget -> Price or budget concern
needs_partner_approval -> Waiting for partner or decision-maker approval
```

### Test 9: Prompt Includes New Tool Rules

Assert `diagnostic_analytics.md` contains:

```text
get_diagnostic_text_reason_snapshot
Reason Combination Distribution
Individual Issue Distribution
Never show raw diagnostic text enum values
Default limits
```

### Test 10: Router Examples

Assert router prompt routes these to diagnostic analytics:

```text
Why are completed calls not converting to signed leads?
After calls, why are people not paying?
Where are we losing people in the funnel and why?
```

---

## Manual Smoke Tests

After implementation, run these questions in the app:

```text
Where are we losing people in the funnel?
Where are we loosing people on funnel?
Why are completed calls not converting to signed leads?
After calls, why are people not paying?
What are the main post-call blockers?
Why are attended leads not becoming paid customers?
```

Expected behavior:

```text
The answer uses diagnostic_analytics route.
The answer calls diagnostic tools only.
The answer starts with numeric funnel or cohort size.
The answer shows user-friendly issue labels.
The answer limits issue tables to top 10 by default.
The answer includes unknown/no-text coverage.
The answer does not expose raw text or private fields.
The answer gives practical sales recommendations tied to top known reasons.
```

---

## Completion Criteria

This task is complete only when:

```text
get_diagnostic_text_reason_snapshot exists.
The new tool is included in DIAGNOSTIC_TOOLS.
The diagnostic agent has exactly diagnostic tools and no SQL/Lead360 tools.
The tool reads only diagnostic_lead_snapshot and diagnostic_text_insights.
All queries are tenant-scoped with :org_id.
No raw text or sensitive fields are returned.
Reason counts use DISTINCT lead_id.
Reason combination distribution assigns each lead to exactly one row.
Reason combination distribution sums to the total cohort lead count.
Individual issue distribution allows one lead to appear in multiple issue rows.
Default top-N display is 10.
Maximum top-N display is 20.
Unknown and no-text insight coverage are shown separately.
Raw enum values are converted to user-friendly labels in final answers.
diagnostic_analytics.md instructs the agent to use text reasons after numeric funnel results.
Router examples cover post-call reason and funnel-plus-reason questions.
Tests or smoke tests pass.
```

---

## Final Implementation Reminder

Keep the diagnostic design deterministic, safe, tenant-scoped, and business-reviewable.

The final answer should feel like a business diagnosis:

```text
The biggest leak is after completed calls, and the known reasons suggest people need more time, partner approval, proof, and clearer post-call information.
```

It should not feel like a database dump:

```text
timing_issue + needs_partner_approval + trust_issue
```
