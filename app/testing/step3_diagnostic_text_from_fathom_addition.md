# Step 3 Addition — Diagnostic Text Insights From Fathom Records

Add the following content inside **Step 3 — Section 26: Diagnostic Text Insights Seeding**.

Place it after the current instruction that says diagnostic text insights should be seeded deterministically and LLM should not be called.

---

## Primary Source for Demo Diagnostic Text Insights

For demo data, do not call the LLM to create `diagnostic_text_insights`.

Since dummy Fathom call records are already generated from known lead scenarios and story templates, use the generated `fathom_call_records` as the primary source for diagnostic text insights.

This means:

```text
lead scenario
+ Fathom story template
+ Fathom summary
+ Fathom objections
+ Fathom action items
↓
deterministic diagnostic_text_insights rows
```

Do not run a separate extraction job.

Do not call OpenAI or any LLM for this demo seeding task.

---

## Call-Derived Insight Source Fields

For insights created from Fathom records, use:

```text
source_table = fathom_call_records
source_record_id = fathom_call_records.id
source_text_type = fathom_summary
```

Each diagnostic insight must still include:

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

Use safe defaults for fields that are not naturally available from the Fathom story.

Do not store `is_human_reason_supported`.

Do not store raw transcripts.

---

## Deterministic Mapping From Fathom Story Template

The reason fields should be assigned deterministically from the same Fathom story template used to create the call summary.

Use this mapping:

| Fathom story template | reason_category | reason_subcategory | is_conversion_blocker |
|---|---|---|---:|
| `converted_strong_intent` | `unknown` | `unknown` | false |
| `converted_after_payment_plan` | `price_or_budget` | `needs_payment_plan` | false |
| `completed_not_signed_partner_approval` | `needs_partner_approval` | `waiting_for_partner` | true |
| `completed_not_signed_budget` | `price_or_budget` | `budget_not_available` | true |
| `completed_not_signed_needs_more_time` | `timing_issue` | `needs_more_time` | true |
| `signed_not_paid_payment_link_issue` | `payment_friction` | `system_or_link_issue` | true |
| `signed_not_paid_payment_timing` | `payment_friction` | `payment_not_completed` | true |
| `lost_low_intent` | `low_intent` | `not_ready_now` | true |
| `unqualified_poor_fit` | `poor_fit` | `wrong_customer_fit` | true |
| `follow_up_needs_more_information` | `needs_more_information` | `needs_more_information` | true |

---

## Suggested Intent and Quality Mapping

Use this mapping unless the scenario provides a better value:

| Lead scenario | buying_intent_level | lead_quality_level |
|---|---|---|
| Paid / converted | `high` or `very_high` | `high_quality` |
| Completed call but not signed | `medium` or `high` | `medium_quality` |
| Signed but not paid | `high` | `medium_quality` |
| Booked but not completed | `low` or `medium` | `medium_quality` |
| Lost | `low` | `low_quality` |
| Unqualified | `very_low` | `unqualified` |
| Lead created but never booked | `unknown` or `low` | `unknown` |

---

## Profession and Employment Mapping

If profession and employment status were already generated in `opt_in_question_answers`, reuse those values where possible.

Map them to the allowed `diagnostic_text_insights` enum values.

Example mappings:

```text
Business Owner → profession_category = business_owner
Employee → profession_category = employee
Self-employed → profession_category = self_employed
Student → profession_category = student
Trader / Investor → profession_category = trader_or_investor
Sales or Marketing → profession_category = sales_or_marketing
Technology → profession_category = technology
Healthcare → profession_category = healthcare
Retired → profession_category = retired
Unemployed → profession_category = unemployed
```

Employment-status mappings:

```text
Full-time → employment_status = full_time
Part-time → employment_status = part_time
Self-employed → employment_status = self_employed
Student → employment_status = student
Business Owner → employment_status = business_owner
Unemployed → employment_status = unemployed
Retired → employment_status = retired
```

If no safe mapping exists, use:

```text
profession_category = unknown
employment_status = unknown
```

---

## Source Text Hash and Length

For each Fathom-derived insight:

```text
source_text_hash = hash of the generated Fathom summary text
source_text_length = character length of the generated Fathom summary text
source_event_at = fathom_call_records.call_started_at
extraction_status = success
```

Use a deterministic hash such as SHA-256.

Do not use random hashes.

---

## Why This Rule Exists

This keeps demo data:

```text
deterministic
fast
cheap
consistent with generated Fathom summaries
free from LLM extraction variability
easy to validate
```

The production workflow can still use LLM extraction on real Fathom summaries later, but the demo seed script should not call an LLM.
