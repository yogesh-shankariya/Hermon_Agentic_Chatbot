# Codex Task: Flatten Diagnostic Text Extraction JSONL Into `diagnostic_text_insights`

## Goal

Create a script that reads validated diagnostic text extraction JSONL and inserts one row per extracted insight into a new table:

```text
diagnostic_text_insights
```

This task is only for flattening existing JSONL into a database table.

Do not call the LLM in this task.
Do not regenerate JSONL.
Do not modify `diagnostic_lead_snapshot`.
Do not modify router logic.
Do not modify SQL agent or Lead 360 agent.
Do not build diagnostic answer tools yet.

---

## Important Decision

The JSONL may contain this field inside each insight:

```text
is_human_reason_supported
```

Ignore it.

Do not store `is_human_reason_supported` in the final table.

Whatever reason output is present in the JSONL should be inserted as-is, after enum/value validation and safe defaults.

Do not apply this rule:

```text
If is_human_reason_supported = false:
  reason_category = unknown
  reason_subcategory = unknown
  is_conversion_blocker = false
```

That rule must not be used in this task.

---

## Input

Use existing JSONL file:

```text
artifacts/diagnostic_text_extractions.jsonl
```

Each JSONL row may contain:

```text
clerk_org_id
lead_id
source_table
source_record_id
source_text_type
source_event_at
source_text_hash
source_text_length
extraction_status
llm_output_json.insights
extracted_at
```

Each insight may contain:

```text
reason_category
reason_subcategory
is_conversion_blocker
is_human_reason_supported
buying_intent_level
lead_quality_level
profession_category
employment_status
```

The final table must ignore `is_human_reason_supported`.

---

## Table Grain

The table grain must be:

```text
one row per extracted insight
```

That means:

- One JSONL source text item can create zero rows.
- One JSONL source text item can create one row.
- One JSONL source text item can create multiple rows.
- One lead can have many rows across calls, notes, payments, contracts, refunds, and opt-in answers.

---

## Table To Create

Create table if not exists:

```sql
CREATE TABLE IF NOT EXISTS diagnostic_text_insights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  clerk_org_id text NOT NULL,
  lead_id uuid NOT NULL,

  source_table text NOT NULL,
  source_record_id uuid NOT NULL,
  source_text_type text NOT NULL,
  source_event_at timestamptz,
  source_text_hash text NOT NULL,
  source_text_length integer,

  reason_category text NOT NULL DEFAULT 'unknown',
  reason_subcategory text NOT NULL DEFAULT 'unknown',
  is_conversion_blocker boolean NOT NULL DEFAULT false,
  buying_intent_level text NOT NULL DEFAULT 'unknown',
  lead_quality_level text NOT NULL DEFAULT 'unknown',
  profession_category text NOT NULL DEFAULT 'unknown',
  employment_status text NOT NULL DEFAULT 'unknown',

  extraction_status text NOT NULL DEFAULT 'success',
  extracted_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT chk_dti_extraction_status CHECK (
    extraction_status IN (
      'success',
      'skipped_empty',
      'skipped_too_short',
      'skipped_duplicate',
      'skipped_no_signal',
      'validation_failed',
      'llm_failed'
    )
  ),

  CONSTRAINT chk_dti_reason_category CHECK (
    reason_category IN (
      'price_or_budget',
      'timing_issue',
      'not_decision_maker',
      'needs_partner_approval',
      'trust_issue',
      'low_intent',
      'unclear_need',
      'poor_fit',
      'competition',
      'too_busy',
      'needs_more_information',
      'payment_friction',
      'contract_friction',
      'no_show',
      'ghosted',
      'follow_up_pending',
      'operational_delay',
      'technical_issue',
      'language_or_communication_issue',
      'location_or_timezone_issue',
      'already_solved',
      'unknown'
    )
  ),

  CONSTRAINT chk_dti_reason_subcategory CHECK (
    reason_subcategory IN (
      'price_too_high',
      'budget_not_available',
      'wants_discount',
      'needs_payment_plan',
      'not_ready_now',
      'needs_more_time',
      'waiting_for_partner',
      'waiting_for_team',
      'waiting_for_finance',
      'does_not_trust_offer',
      'needs_proof_or_case_study',
      'unclear_value',
      'comparing_competitor',
      'not_enough_need',
      'wrong_customer_fit',
      'not_qualified',
      'missed_call',
      'cancelled_call',
      'stopped_responding',
      'needs_more_information',
      'contract_not_signed',
      'payment_not_completed',
      'payment_failed',
      'refund_requested',
      'internal_team_delay',
      'system_or_link_issue',
      'language_barrier',
      'timezone_issue',
      'issue_already_solved',
      'other',
      'unknown'
    )
  ),

  CONSTRAINT chk_dti_buying_intent_level CHECK (
    buying_intent_level IN (
      'very_high',
      'high',
      'medium',
      'low',
      'very_low',
      'unknown'
    )
  ),

  CONSTRAINT chk_dti_lead_quality_level CHECK (
    lead_quality_level IN (
      'high_quality',
      'medium_quality',
      'low_quality',
      'unqualified',
      'unknown'
    )
  ),

  CONSTRAINT chk_dti_profession_category CHECK (
    profession_category IN (
      'student',
      'employee',
      'self_employed',
      'business_owner',
      'entrepreneur',
      'freelancer',
      'trader_or_investor',
      'finance_or_accounting',
      'sales_or_marketing',
      'healthcare',
      'education',
      'technology',
      'engineering',
      'construction_or_trades',
      'hospitality',
      'retail',
      'real_estate',
      'transport_or_logistics',
      'creative_or_media',
      'government_or_public_sector',
      'unemployed',
      'retired',
      'other',
      'unknown'
    )
  ),

  CONSTRAINT chk_dti_employment_status CHECK (
    employment_status IN (
      'full_time',
      'part_time',
      'self_employed',
      'student',
      'business_owner',
      'unemployed',
      'retired',
      'unknown'
    )
  )
);
```

---

## Required Indexes

Create these indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_dti_org
ON diagnostic_text_insights (clerk_org_id);

CREATE INDEX IF NOT EXISTS idx_dti_org_lead
ON diagnostic_text_insights (clerk_org_id, lead_id);

CREATE INDEX IF NOT EXISTS idx_dti_org_source
ON diagnostic_text_insights (clerk_org_id, source_table, source_text_type);

CREATE INDEX IF NOT EXISTS idx_dti_org_source_hash
ON diagnostic_text_insights (clerk_org_id, source_text_hash);

CREATE INDEX IF NOT EXISTS idx_dti_org_reason
ON diagnostic_text_insights (clerk_org_id, reason_category);

CREATE INDEX IF NOT EXISTS idx_dti_org_reason_subcategory
ON diagnostic_text_insights (clerk_org_id, reason_category, reason_subcategory);

CREATE INDEX IF NOT EXISTS idx_dti_org_blocker
ON diagnostic_text_insights (clerk_org_id, is_conversion_blocker);

CREATE INDEX IF NOT EXISTS idx_dti_org_intent
ON diagnostic_text_insights (clerk_org_id, buying_intent_level);

CREATE INDEX IF NOT EXISTS idx_dti_org_quality
ON diagnostic_text_insights (clerk_org_id, lead_quality_level);

CREATE INDEX IF NOT EXISTS idx_dti_org_profession
ON diagnostic_text_insights (clerk_org_id, profession_category);

CREATE INDEX IF NOT EXISTS idx_dti_org_employment
ON diagnostic_text_insights (clerk_org_id, employment_status);

CREATE INDEX IF NOT EXISTS idx_dti_org_event_at
ON diagnostic_text_insights (clerk_org_id, source_event_at);
```

---

## Optional Unique Index For Deduplication

Create this unique index if it does not cause issues with existing duplicate data:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_dti_source_insight
ON diagnostic_text_insights (
  clerk_org_id,
  lead_id,
  source_table,
  source_record_id,
  source_text_type,
  source_text_hash,
  reason_category,
  reason_subcategory,
  is_conversion_blocker,
  buying_intent_level,
  lead_quality_level,
  profession_category,
  employment_status
);
```

If a unique index is too strict, deduplicate in Python using the same field set.

---

## Insert Logic

For each JSONL row:

1. Read JSON safely.
2. Skip invalid JSON lines with a safe validation counter.
3. Only insert rows where:

```text
extraction_status = success
```

4. Read:

```text
llm_output_json.insights
```

5. If `insights` is empty, insert zero table rows.
6. For each insight object, insert one table row.
7. Ignore `is_human_reason_supported` completely.
8. Do not store raw text.
9. Do not store `llm_output_json`.
10. Do not store `extraction_error`.
11. Do not store `prompt_path` or `schema_path`.
12. Do not store absolute local file paths.

---

## Field Mapping

Use this mapping:

```text
JSONL clerk_org_id -> diagnostic_text_insights.clerk_org_id
JSONL lead_id -> diagnostic_text_insights.lead_id

JSONL source_table -> diagnostic_text_insights.source_table
JSONL source_record_id -> diagnostic_text_insights.source_record_id
JSONL source_text_type -> diagnostic_text_insights.source_text_type
JSONL source_event_at -> diagnostic_text_insights.source_event_at
JSONL source_text_hash -> diagnostic_text_insights.source_text_hash
JSONL source_text_length -> diagnostic_text_insights.source_text_length

insight.reason_category -> diagnostic_text_insights.reason_category
insight.reason_subcategory -> diagnostic_text_insights.reason_subcategory
insight.is_conversion_blocker -> diagnostic_text_insights.is_conversion_blocker
insight.buying_intent_level -> diagnostic_text_insights.buying_intent_level
insight.lead_quality_level -> diagnostic_text_insights.lead_quality_level
insight.profession_category -> diagnostic_text_insights.profession_category
insight.employment_status -> diagnostic_text_insights.employment_status

JSONL extraction_status -> diagnostic_text_insights.extraction_status
JSONL extracted_at -> diagnostic_text_insights.extracted_at
```

Do not map:

```text
insight.is_human_reason_supported
```

---

## Defaulting Rules

If an insight field is missing or null, use these defaults:

```text
reason_category = unknown
reason_subcategory = unknown
is_conversion_blocker = false
buying_intent_level = unknown
lead_quality_level = unknown
profession_category = unknown
employment_status = unknown
```

If required envelope metadata is missing, skip that insight row and increment `validation_errors`.

Required envelope metadata:

```text
clerk_org_id
lead_id
source_table
source_record_id
source_text_type
source_text_hash
```

---

## No Post-Correction Rule

Do not rewrite the LLM output.

Do not change:

```text
payment_friction -> unknown
reason_category -> unknown
is_conversion_blocker -> false
```

based on `is_human_reason_supported`.

The JSONL output is considered the source of truth for the selected fields.

Only apply:
- enum validation
- missing value defaults
- duplicate protection
- type coercion for booleans and timestamps

---

## Script To Create

Create:

```text
app/diagnostics/flatten_text_extractions.py
```

Run command:

```bash
python -m app.diagnostics.flatten_text_extractions \
  --input-path artifacts/diagnostic_text_extractions.jsonl \
  --org-id org_3ARuGHeqbbEu5FNexlpC7ElaiyW \
  --force
```

Supported arguments:

| Argument | Required | Meaning |
|---|---:|---|
| `--input-path` | Yes | Path to JSONL extraction file |
| `--org-id` | No | Defaults to `HERMON_DEFAULT_CLERK_ORG_ID` |
| `--limit` | No | Process only first N JSONL rows |
| `--dry-run` | No | Validate and summarize, but do not insert |
| `--force` | No | Delete existing rows for org before insert |
| `--create-table` | No | Create table and indexes before insert |

Default behavior:

```text
- Do not delete existing rows unless --force is passed.
- Create table/indexes if --create-table is passed.
- Insert only non-duplicate rows.
```

---

## Database Connection

Use the existing project database configuration pattern.

For table creation and insertion, use a write/admin database URL if the project already has one for diagnostic build scripts.

Preferred environment fallback order:

```text
HERMON_DIAGNOSTIC_DATABASE_URL
SUPABASE_DB_URL
HERMON_DATABASE_URL
DATABASE_URL
```

Do not expose credentials in logs.

---

## Force Mode

If `--force` is passed:

```sql
DELETE FROM diagnostic_text_insights
WHERE clerk_org_id = :org_id;
```

Then insert rows from the JSONL for that org.

Do not delete rows for other orgs.

---

## Dry Run Mode

If `--dry-run` is passed:

- Read JSONL.
- Validate rows.
- Count how many rows would be inserted.
- Count skipped and duplicate rows.
- Do not create table.
- Do not insert.
- Do not delete.

---

## Output Summary

After running, print a safe summary:

```text
org_id
jsonl_rows_read
jsonl_rows_for_org
success_jsonl_rows
non_success_jsonl_rows_skipped
insights_seen
insights_inserted
duplicates_skipped
validation_errors
force_used
dry_run
```

Do not print raw source text.
Do not print raw LLM JSON for individual leads.

---

## Safety Rules

Do not insert or store:

```text
raw source text
cleaned text
emails
phone numbers
URLs
payment links
meeting links
recording links
transcript links
provider IDs
raw payloads
prompt_path
schema_path
absolute local paths
llm_output_json
extraction_error
```

Only store the flattened safe fields listed in the table.

---

## Tests

Add tests for:

1. JSONL row with one insight creates one table row.
2. JSONL row with multiple insights creates multiple table rows.
3. Empty `insights` creates zero table rows.
4. `extraction_status != success` creates zero table rows.
5. `is_human_reason_supported` is ignored and not inserted.
6. Missing optional insight fields use defaults.
7. Invalid enum value is counted as validation error and skipped.
8. Duplicate rows are skipped.
9. `--dry-run` does not insert.
10. `--force` deletes only rows for the selected org.
11. No raw text, JSONL full payload, prompt path, or schema path is inserted.
12. Inserted rows are tenant-scoped by `clerk_org_id`.

---

## Completion Criteria

This task is complete when:

```text
1. diagnostic_text_insights table is created without is_human_reason_supported.
2. JSONL is flattened into one row per insight.
3. Only success JSONL rows are inserted.
4. Empty insights create zero rows.
5. is_human_reason_supported is ignored.
6. LLM reason/category output is inserted as-is after enum validation/defaults.
7. Duplicate rows are avoided.
8. Dry-run and force modes work.
9. Summary output is printed.
10. Tests pass.
```
