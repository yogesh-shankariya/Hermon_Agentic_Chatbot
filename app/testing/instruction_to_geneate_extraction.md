# Codex Task: Generate Diagnostic Text Extraction JSONL

## Goal

Build a script/module that extracts cleaned text candidates for diagnostic text analysis, calls the existing LLM prompt/schema, validates the response, and stores the validated LLM output as JSONL.

Do not create the final `diagnostic_text_insights` table yet.
Do not flatten into database rows yet.
This task is only to generate and store validated JSON/JSONL extraction output.


## Assumptions

The diagnostic LLM prompt and Pydantic schema already exist.

Codex will be given these paths:

```text
PROMPT_PATH = /Users/mitulkanani/Desktop/Projects/Hermon_Agentic_Chatbot/app/prompts/extract_context/1_0_0.yaml
SCHEMA_PATH = /Users/mitulkanani/Desktop/Projects/Hermon_Agentic_Chatbot/app/schema/context_extraction.py
````

Use those files. Do not recreate the prompt/schema unless imports fail.



## Output Format

Use JSONL as the primary output format.

One JSON object per source text item.

Recommended output file:

```text
artifacts/diagnostic_text_extractions.jsonl
```

Each JSONL row should use this envelope:

```json
{
  "clerk_org_id": "org_xxx",
  "lead_id": "lead_uuid",
  "source_table": "fathom_call_records",
  "source_record_id": "record_uuid",
  "source_text_type": "fathom_summary",
  "source_event_at": "2026-04-10T10:30:00Z",
  "source_text_hash": "sha256_hash",
  "source_text_length": 1234,
  "extraction_status": "success",
  "llm_output_json": {
    "insights": [
      {
        "reason_category": "price_or_budget",
        "reason_subcategory": "price_too_high",
        "is_conversion_blocker": true,
        "is_human_reason_supported": true,
        "buying_intent_level": "medium",
        "lead_quality_level": "medium_quality",
        "profession_category": "unknown",
        "employment_status": "unknown"
      }
    ]
  },
  "extraction_error": null,
  "extraction_model": "configured_model_name",
  "prompt_path": "<path_to_prompt>",
  "schema_path": "<path_to_schema>",
  "extracted_at": "2026-05-14T10:00:00Z"
}
```

For skipped/failed records, still write one JSONL row with:

```json
{
  "extraction_status": "skipped_empty",
  "llm_output_json": {"insights": []},
  "extraction_error": null
}
```

---

## Allowed `extraction_status` Values

Use only:

```text
success
skipped_empty
skipped_too_short
skipped_duplicate
skipped_no_signal
validation_failed
llm_failed
```

Meaning:

| Status              | Meaning                                         |
| ------------------- | ----------------------------------------------- |
| `success`           | LLM call succeeded and schema validation passed |
| `skipped_empty`     | Text was null/blank after cleaning              |
| `skipped_too_short` | Text was too small to contain useful signal     |
| `skipped_duplicate` | Same source hash already processed              |
| `skipped_no_signal` | LLM returned valid empty `insights`             |
| `validation_failed` | LLM response failed Pydantic validation         |
| `llm_failed`        | LLM call failed after retries                   |

---

## Source Text Candidates

Extract text from available source tables only if the columns exist in the repo schema.

Candidate sources:

```text
fathom_call_records.summary
fathom_call_records.key_points
fathom_call_records.action_items
fathom_call_records.objections
fathom_call_records.ai_rationale

lead_notes.note

appointments.notes

contracts.notes
contracts.voided_reason

payments.note
payments.failure_reason

refunds.reason
refunds.failure_reason

contract_subscriptions.cancellation_reason

opt_in_question_answers.question + opt_in_question_answers.answer
```

For opt-in question answers, combine question and answer like this:

```text
Question: <question>
Answer: <answer>
```

This is important for profession and employment extraction.

---

## Required Source Metadata

For every candidate text item, include:

```text
clerk_org_id
lead_id
source_table
source_record_id
source_text_type
source_event_at
source_text_hash
source_text_length
```

Use these `source_text_type` values:

```text
fathom_summary
fathom_key_points
fathom_action_items
fathom_objections
fathom_ai_rationale
lead_note
appointment_note
contract_note
contract_voided_reason
payment_note
payment_failure_reason
refund_reason
refund_failure_reason
subscription_cancellation_reason
opt_in_question_answer
```

---

## Tenant Scope

Every source query must be scoped by organization.

Use:

```text
HERMON_DEFAULT_CLERK_ORG_ID
```

as the default org for MVP.

Required filters:

```sql
WHERE <table>.clerk_org_id = :org_id
```

For child tables without `clerk_org_id`, join through parent table.

Examples:

```sql
opt_in_question_answers -> opt_ins -> clerk_org_id
traffic_attributions -> opt_ins -> clerk_org_id
contract_subscriptions -> contracts -> clerk_org_id
```

Do not process data across organizations.

---

## Text Cleaning Rules

Before sending text to LLM:

1. Normalize whitespace.
2. Remove URLs.
3. Remove emails.
4. Remove phone numbers.
5. Remove payment links.
6. Remove meeting links.
7. Remove recording links.
8. Remove transcript links.
9. Remove obvious provider IDs.
10. Strip markdown links.
11. Skip blank text.
12. Skip very short text if it is unlikely to contain a signal.

Do not log full raw text.

Do not store full raw text in the JSONL output.

Store only:

```text
source_text_hash
source_text_length
validated LLM output
status/error metadata
```

---

## Hashing and Deduplication

Generate:

```text
source_text_hash = sha256(cleaned_text)
```

Deduplicate by:

```text
clerk_org_id
lead_id
source_table
source_record_id
source_text_type
source_text_hash
```

If a duplicate is found, write a JSONL row with:

```text
extraction_status = skipped_duplicate
```

or skip writing duplicate rows if the script has a `--skip-duplicates` flag.

---

## LLM Call

For each cleaned source text item:

1. Load prompt from `PROMPT_PATH`.
2. Load/import schema from `SCHEMA_PATH`.
3. Pass these variables into prompt:

```text
source_table
source_text_type
cleaned_text
```

4. Call the configured OpenAI model.
5. Parse the returned JSON.
6. Validate using the Pydantic response schema.
7. Write one JSONL envelope row.

The LLM output must match:

```json
{
  "insights": []
}
```

or:

```json
{
  "insights": [
    {
      "reason_category": "...",
      "reason_subcategory": "...",
      "is_conversion_blocker": true,
      "is_human_reason_supported": true,
      "buying_intent_level": "...",
      "lead_quality_level": "...",
      "profession_category": "...",
      "employment_status": "..."
    }
  ]
}
```

---

## Empty Insight Handling

If the LLM returns:

```json
{"insights": []}
```

then store the row as:

```text
extraction_status = skipped_no_signal
```

This is not an error.

---

## Retry Logic

Use simple retries for LLM failures:

```text
max_retries = 2
```

Retry only for:

```text
transient API failure
timeout
rate limit
invalid JSON
schema validation failure
```

After retries fail, write:

```text
extraction_status = llm_failed
```

or:

```text
extraction_status = validation_failed
```

with a safe short `extraction_error`.

Do not include raw text in `extraction_error`.

---

## Script Interface

Create one script/module, for example:

```text
app/diagnostics/text_extraction_jsonl.py
```

It should support:

```bash
python -m app.diagnostics.text_extraction_jsonl \
  --org-id org_xxx \
  --prompt-path <path_to_prompt> \
  --schema-path <path_to_schema> \
  --output-path artifacts/diagnostic_text_extractions.jsonl \
  --limit 100
```

Arguments:

| Argument         | Required | Meaning                                                   |
| ---------------- | -------: | --------------------------------------------------------- |
| `--org-id`       |       No | Defaults to `HERMON_DEFAULT_CLERK_ORG_ID`                 |
| `--prompt-path`  |      Yes | Path to stored extraction prompt                          |
| `--schema-path`  |      Yes | Path to stored Pydantic schema                            |
| `--output-path`  |       No | Defaults to `artifacts/diagnostic_text_extractions.jsonl` |
| `--limit`        |       No | Limit source text items for testing                       |
| `--source-table` |       No | Optional filter for one source table                      |
| `--dry-run`      |       No | Collect and clean candidates but do not call LLM          |
| `--overwrite`    |       No | Recreate output file                                      |
| `--append`       |       No | Append to existing JSONL                                  |

Default behavior:

```text
append mode
skip duplicate hashes already present in existing output file
```

---

## Required Functions

Implement clean functions so they can be tested:

```python
collect_text_candidates(...)
clean_text(...)
hash_text(...)
load_existing_hashes(...)
call_llm_for_candidate(...)
validate_llm_output(...)
write_jsonl_row(...)
run_extraction(...)
```

---

## Safety Rules

Do not:

```text
write to production database
create tables
alter tables
drop tables
insert into diagnostic_text_insights
update diagnostic_lead_snapshot
store raw full text
store emails
store phone numbers
store URLs
store payment links
store meeting links
store recording links
store transcript links
store provider IDs
print raw text to console
```

This task only creates JSONL extraction output.

---

## Testing

Add tests for:

1. `clean_text` removes emails, phone numbers, URLs, payment links, meeting links, recording links, and transcript links.
2. `hash_text` returns stable hash for same cleaned text.
3. Empty text returns `skipped_empty`.
4. Duplicate hash returns `skipped_duplicate`.
5. Valid LLM output passes schema validation.
6. Invalid enum fails validation.
7. Empty insights output is stored as `skipped_no_signal`.
8. JSONL row contains required metadata fields.
9. No raw cleaned text is written into JSONL.
10. `--dry-run` does not call LLM.

---

## Completion Criteria

This task is complete when:

```text
1. JSONL extraction script exists.
2. Script loads prompt and schema from provided paths.
3. Script collects candidate text from approved source columns.
4. Every candidate is tenant-scoped by org.
5. Text is cleaned before LLM call.
6. Output is validated with Pydantic schema.
7. Validated output is written to JSONL.
8. Failed/skipped rows are written with safe status.
9. Raw full text is not stored in JSONL.
10. Tests pass.
```

```
```
