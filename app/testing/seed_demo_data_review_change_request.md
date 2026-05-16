# Seed Demo Data Script — Required Changes Before Running

## Context

Codex has already created:

```text
scripts/seed_demo_data.py
```

This review assumes the table below already exists:

```text
diagnostic_text_insights
```

So do **not** add `CREATE TABLE IF NOT EXISTS diagnostic_text_insights` unless the project later requires it.

The goal of this change request is to make the seed script safer and more client-demo friendly before running it against the database.

---

## 1. Do Not Create or Modify `diagnostic_text_insights` Table

The `diagnostic_text_insights` table already exists.

Do not add table creation logic for it.

Still keep:

```text
diagnostic_text_insights
```

as a required seeded table.

Still validate that the table exists during schema smoke check.

If the table is missing, the script should fail clearly with a message such as:

```text
diagnostic_text_insights table is missing. Run the diagnostic text insights migration before seeding demo data.
```

---

## 2. Make Future Appointments Relative to Runtime Date

Current issue:

The script uses a fixed demo reference date:

```python
DEMO_REFERENCE_DATE = datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)
```

This is fine for the current demo, but future appointments may become past appointments later.

If the diagnostic snapshot builder uses database `NOW()`, old future appointments can later appear as past non-no-show appointments without Fathom, which may create false Fathom coverage issues.

### Required Change

For future appointments, calculate the base date like this:

```python
runtime_now = datetime.now(timezone.utc)
future_base = max(DEMO_REFERENCE_DATE, runtime_now)
```

Then generate future appointments after `future_base`.

Example:

```python
future_schedule_time = future_base + timedelta(days=random.randint(2, 30))
```

### Rule

Future appointments must always be in the future relative to the actual runtime date.

No future appointment should receive a Fathom record.

---

## 3. Align Booked-Not-Completed Lead Status With Appointment Outcome

Current issue:

For booked-not-completed leads, lead status and appointment outcome can be chosen independently.

This can create confusing cases like:

```text
lead current status = RESCHEDULED
appointment outcome = No Show
```

or:

```text
lead current status = CANCELED
appointment outcome = No Show
```

This is not always a database error, but it can confuse client demo questions.

### Required Change

For the `booked_not_completed` scenario, appointment outcome should follow the lead status role.

Use this mapping:

| Lead status role | Appointment kind | Appointment outcome role | no_show |
|---|---|---|---:|
| `NO_SHOW` | `no_show` | `NO_SHOW` | true |
| `CANCELED` | `canceled` | `CANCELED` | false |
| `RESCHEDULED` | `rescheduled` | `RESCHEDULED` | false |

### Rule

Do not randomly assign appointment kind for booked-not-completed leads after the status is selected.

The lead status and appointment outcome should tell the same story.

---

## 4. Keep Fathom Coverage Rule Strict

The existing logic already mostly follows the correct rule.

Keep this rule exactly:

| Appointment scenario | Fathom record? |
|---|---:|
| Completed / attended past appointment | Yes, exactly one |
| No-show | No |
| Canceled | No |
| Rescheduled | No |
| Future appointment | No |
| Deleted appointment | No |

### Required Validation

Add or strengthen validation for:

```text
Every completed/attended past appointment has exactly one Fathom record.
No no-show appointment has a Fathom record.
No canceled appointment has a Fathom record.
No rescheduled appointment has a Fathom record.
No future appointment has a Fathom record.
No appointment has more than one Fathom record.
completed_calls_missing_fathom_count = 0.
completed_call_fathom_coverage_rate = 100.00.
```

---

## 5. Add More Scenario-to-Revenue Validation

Add validation checks to confirm the generated business journey is consistent.

### Required Validations

```text
Paid / converted leads have at least one PAID payment.
Paid / converted leads have a SIGNED contract.
Signed-but-not-paid leads have a SIGNED contract.
Signed-but-not-paid leads have at least one PENDING or FAILED payment.
Completed-call-but-not-signed leads do not have PAID payments.
Lead-only / never-booked leads do not have appointments, contracts, or payments.
Booked-not-completed leads do not have contracts or payments.
Unqualified leads do not have payments.
Refunds connect only to valid PAID payments.
Refund amount does not exceed original payment amount.
```

### Why

These checks prevent client-visible inconsistencies such as:

```text
unqualified lead with payment
lead-only record with contract
signed-not-paid lead without contract
paid lead without paid payment
```

---

## 6. Add Diagnostic Text Insight Relationship Validation

Since the script creates deterministic `diagnostic_text_insights` from generated Fathom/lead scenarios, validate those relationships.

### Required Validations

```text
Every diagnostic_text_insights row has clerk_org_id = org_dummy_client_demo_001.
Every diagnostic_text_insights row joins to a valid active lead.
Every Fathom-derived diagnostic_text_insights row has source_table = fathom_call_records.
Every Fathom-derived diagnostic_text_insights row has source_record_id pointing to an existing Fathom record.
Every Fathom-derived diagnostic_text_insights row has source_event_at = fathom_call_records.call_started_at.
Every source_text_hash is non-empty.
Every source_text_length is greater than 0.
extraction_status = success for seeded demo insights.
```

### Rule

Do not call the LLM during seed.

Do not run a separate extraction job.

Use the generated Fathom story template and scenario mapping directly.

---

## 7. Reduce Repeated Fathom Summary Text

Current issue:

The script uses a small number of Fathom story templates.

This is technically correct, but if the client asks for recent Fathom summaries or objections, repeated text can look obviously dummy/generated.

### Required Change

Keep the same story-template approach, but add light variation.

Do not create completely random or inconsistent stories.

For each Fathom story type, add either:

```text
3 to 5 text variants
```

or inject safe lead-specific details into the summary.

Use details already generated in dummy data:

```text
program name
lead goal
challenge
budget range
decision-maker status
source
follow-up action
start timeline
```

### Example

Instead of repeating:

```text
The lead was interested but needed more time.
```

Vary it naturally:

```text
The lead understood the offer but wanted a few more days to review the details before signing.
```

```text
The lead was interested in the program, but the decision was not urgent for them this week.
```

```text
The lead asked good questions but wanted to compare the offer with their current priorities before committing.
```

### Rule

The story type should remain consistent with the scenario.

Do not make a `paid_converted` lead sound like a lost lead.

Do not make a `signed_not_paid` lead sound like they rejected the offer.

---

## 8. Improve Validation Failure Handling

Current issue:

If base data is committed and the diagnostic snapshot or final validations fail later, the dummy org can be left partially seeded.

### Required Change

Add clear failure behavior.

Preferred option:

```text
If final validation fails after any write, safely clean up only org_dummy_client_demo_001 in a new transaction.
```

Alternative acceptable option:

```text
If validation fails after commit, print a clear error telling the user that base demo rows may already exist and they must rerun with --force after fixing the issue.
```

### Preferred Error Message

```text
Validation failed after seed attempt.
Dummy org data may have been partially written.
Run the script again with --force after fixing the issue, or allow automatic cleanup for org_dummy_client_demo_001 only.
```

### Safety Rule

Any automatic cleanup must only affect:

```text
org_dummy_client_demo_001
```

Never clean live org data.

Never truncate tables.

---

## 9. Keep Optional Tables Skipped

Confirm the script still does not seed these tables by default:

```text
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
provider_integrations
provider_credentials
webhook_events
integration_health_checks
audit_logs
notification_logs
raw payload tables
secret/token/API key tables
```

If existing rows are found in optional tables for the dummy org, print a warning only.

Do not create new rows in those tables for the first demo.

---

## 10. Keep Demo Data Safe

Confirm these fields remain null or safe:

```text
fathom_call_records.raw_payload = null
fathom_call_records.recording_url = null
fathom_call_records.transcript_url = null
appointments.meeting_url = null
appointments.recording_url = null
opt_ins.raw_payload = null
opt_ins.ip_address = null
opt_ins.user_agent = null
payments.external_payment_id = null or safe non-real placeholder only
refunds.external_refund_id = null or safe non-real placeholder only
```

Do not generate:

```text
real names
real emails
real phone numbers
real payment links
real meeting links
real recording links
real transcript links
real webhook payloads
real provider IDs
secrets
tokens
API keys
```

---

## 11. Run Order After Changes

After Codex applies the changes, do not run `--force` immediately.

First run:

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --dry-run
```

Review the dry-run output.

Only after dry-run looks correct, run the actual seed command:

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --force
```

---

## 12. Definition of Done

This change request is complete when:

```text
Future appointments are always future relative to runtime date.
Booked-not-completed appointment outcome matches lead status role.
Fathom coverage validation is strict.
Scenario-to-revenue validation is added.
Diagnostic text insight relationship validation is added.
Fathom summaries have light variation and do not look repeated.
Validation failure handling is safer and clearer.
Optional/admin tables remain skipped.
No LLM call is used during seed.
No live org data can be touched.
```
