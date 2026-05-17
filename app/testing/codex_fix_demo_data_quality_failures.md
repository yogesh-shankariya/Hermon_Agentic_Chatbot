# Codex Task — Fix Demo Data Quality Validation Failures

## Context

The demo dataset was seeded successfully, but the independent validation script failed on three data-quality checks.

Do not weaken validation rules to make the report pass.

Fix the seed data generation properly in:

```text
scripts/seed_demo_data.py
```

Then rerun the seed script and validation script.

---

## Current Validation Status

Validation result:

```text
Overall status: FAILED
critical: 1 failed
high: 2 failed
```

Failed checks:

```text
answers_after_opt_in: 1250 question-answer rows have created_at before their parent opt-in.

diagnostic_text_unknown_reason_threshold: unknown reason rate is 19.753%; threshold is < 5%.
Detail: paid_converted=80.

unsafe_payloads_urls_and_provider_ids: 202 unsafe non-empty provider IDs.
Detail: payments_external_id=190, refunds_external_id=12.
```

Important checks already passed:

```text
All expected row counts passed.
Relationship integrity passed.
Fathom coverage passed.
Diagnostic snapshot consistency passed.
Revenue reconciliation passed daily, weekly, monthly.
Optional/admin table leakage checks passed.
```

So the issue is not core data structure. It is seed-quality cleanup.

---

## Required Fix 1 — Fix Opt-In Question Answer Timestamps

### Problem

Some `opt_in_question_answers.created_at` values are earlier than their parent `opt_ins.created_at`.

This is logically incorrect.

A form answer should happen at the same time as the opt-in or after it, never before it.

### Required Rule

For every question-answer row:

```text
opt_in_question_answers.created_at >= parent opt_ins.created_at
```

### Required Code Change

In `scripts/seed_demo_data.py`, when generating `opt_in_question_answers`, do not use `lead.created_at` or any earlier timestamp as the base.

Use the parent opt-in timestamp.

Recommended deterministic logic:

```python
answer_created_at = opt_in_created_at + timedelta(seconds=position)
```

Alternative deterministic logic:

```python
answer_created_at = opt_in_created_at + timedelta(seconds=(position * 3))
```

Where:

```text
position = question position/order
```

### Important

Do not use random offsets that can become negative.

Do not use timestamps earlier than the opt-in.

Do not modify the expected row count:

```text
opt_in_question_answers = 6500
```

### Expected Validation Result

After fix:

```text
answers_after_opt_in: passed
offending rows = 0
```

---

## Required Fix 2 — Reduce Unknown Diagnostic Text Reasons

### Problem

The validation failed because the unknown reason rate is too high:

```text
unknown reason rate = 19.753%
threshold = < 5%
```

The report shows the issue is mainly:

```text
paid_converted = 80
```

This means many converted/paid leads are getting diagnostic text insights with:

```text
reason_category = unknown
reason_subcategory = unknown
```

For the demo dataset, this looks weak and can reduce confidence.

### Required Rule

Do not generate `unknown` diagnostic reasons for normal paid/converted success stories.

Since these are deterministic demo insights, map successful converted call stories to meaningful non-blocker reason categories.

Do not call an LLM.

Do not run any extraction job.

Keep deterministic mapping.

---

## Diagnostic Text Mapping Changes

Update the Fathom-story-to-diagnostic-insight mapping in `scripts/seed_demo_data.py`.

### For `converted_strong_intent`

Use:

```text
reason_category = already_solved
reason_subcategory = issue_already_solved
is_conversion_blocker = false
buying_intent_level = very_high
lead_quality_level = high_quality
```

### For `converted_after_payment_plan`

Use:

```text
reason_category = price_or_budget
reason_subcategory = needs_payment_plan
is_conversion_blocker = false
buying_intent_level = high
lead_quality_level = high_quality
```

### For Other Converted/Successful Cases

If any other success/converted story type exists, use a safe non-blocker mapping such as:

```text
reason_category = already_solved
reason_subcategory = issue_already_solved
is_conversion_blocker = false
buying_intent_level = high
lead_quality_level = high_quality
```

---

## Do Not Break Existing Blocker Mappings

Keep blocker mappings for non-converted leads.

Examples:

```text
completed_not_signed_partner_approval
→ reason_category = needs_partner_approval
→ reason_subcategory = waiting_for_partner
→ is_conversion_blocker = true

completed_not_signed_budget
→ reason_category = price_or_budget
→ reason_subcategory = budget_not_available
→ is_conversion_blocker = true

completed_not_signed_needs_more_time
→ reason_category = timing_issue
→ reason_subcategory = needs_more_time
→ is_conversion_blocker = true

signed_not_paid_payment_link_issue
→ reason_category = payment_friction
→ reason_subcategory = system_or_link_issue
→ is_conversion_blocker = true

signed_not_paid_payment_timing
→ reason_category = payment_friction
→ reason_subcategory = payment_not_completed
→ is_conversion_blocker = true

lost_low_intent
→ reason_category = low_intent
→ reason_subcategory = not_ready_now
→ is_conversion_blocker = true

unqualified_poor_fit
→ reason_category = poor_fit
→ reason_subcategory = wrong_customer_fit
→ is_conversion_blocker = true

follow_up_needs_more_information
→ reason_category = needs_more_information
→ reason_subcategory = needs_more_information
→ is_conversion_blocker = true
```

### Expected Validation Result

After fix:

```text
diagnostic_text_unknown_reason_threshold: passed
unknown reason rate < 5%
```

Preferably unknown reason rate should be near zero for demo data.

---

## Required Fix 3 — Remove Unsafe Provider / External IDs

### Problem

The validation failed because the seed script generated non-empty provider/external IDs:

```text
payments_external_id = 190
refunds_external_id = 12
```

Even if these are fake, they look like provider identifiers and create avoidable demo/security risk.

### Required Rule

Do not seed fake provider-looking external IDs for the first demo.

Set these fields to null:

```text
payments.external_payment_id = null
refunds.external_refund_id = null
```

### Required Code Change

In payment generation, remove any generated values such as:

```text
external_payment_id
stripe-like IDs
mollie-like IDs
provider transaction IDs
```

Set:

```python
external_payment_id = None
```

In refund generation, remove any generated values such as:

```text
external_refund_id
provider refund IDs
stripe-like refund IDs
mollie-like refund IDs
```

Set:

```python
external_refund_id = None
```

### Also Keep These Safe

Confirm these remain null or empty:

```text
opt_ins.raw_payload
opt_ins.ip_address
opt_ins.user_agent
appointments.meeting_url
appointments.recording_url
fathom_call_records.raw_payload
fathom_call_records.recording_url
fathom_call_records.transcript_url
```

Do not generate:

```text
real payment links
fake real-looking payment links
real meeting links
fake real-looking meeting links
real recording links
fake real-looking recording links
provider IDs
webhook payloads
API keys
tokens
credentials
```

### Expected Validation Result

After fix:

```text
unsafe_payloads_urls_and_provider_ids: passed
offending rows = 0
```

---

## Required Run Order After Fixes

After updating `scripts/seed_demo_data.py`, rerun the seed script for the dummy org only.

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --force
```

Then rerun the validation script:

```bash
python scripts/validate_demo_data.py --org-id org_dummy_client_demo_001 --verbose --export-json artifacts/demo_data_validation_report.json
```

Do not share the Streamlit link until validation passes.

---

## Expected Final Validation Result

The final validation should show:

```text
Overall status: PASSED

critical failures: 0
high failures: 0

answers_after_opt_in: passed
diagnostic_text_unknown_reason_threshold: passed
unsafe_payloads_urls_and_provider_ids: passed
```

Existing passing checks must remain passed:

```text
row counts
relationship integrity
Fathom coverage
diagnostic snapshot consistency
revenue reconciliation daily/weekly/monthly
optional/admin table leakage
source quality
scenario behavior consistency
```

---

## Definition of Done

This task is complete only when:

```text
scripts/seed_demo_data.py is updated.
No form answer timestamp is before its parent opt-in.
Diagnostic unknown reason rate is below 5%.
No payment external provider IDs are seeded.
No refund external provider IDs are seeded.
Seed script reruns successfully with --force.
Validation script reruns successfully.
Validation overall status is PASSED.
No critical or high validation failures remain.
```

---

## Do Not Do

Do not:

```text
Do not change validation thresholds to hide the issue.
Do not mark failed checks as medium/info to bypass failure.
Do not manually patch the database only.
Do not call LLM for diagnostic text insights.
Do not create provider-looking IDs.
Do not seed optional/admin tables.
Do not change expected row counts unless explicitly requested.
Do not touch live client organization data.
```
