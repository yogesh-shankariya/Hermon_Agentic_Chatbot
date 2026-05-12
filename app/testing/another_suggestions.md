Since money is confirmed as minor unit, keep `/ 100.0`.

Apart from money, I recommend these changes only:

**1. Add Fathom missing coverage fields**

Currently you have:

```text
has_fathom_record
fathom_record_count
```

This is useful, but for diagnostic questions like “which source has many calls but poor call evidence?”, add:

```text
past_appointments_missing_fathom_count
fathom_coverage_rate
```

Why: appointment skill treats Fathom coverage mainly on past appointments, because upcoming appointments are not expected to have Fathom records. 

**2. Clarify contract count meaning**

Your columns:

```text
sent_contract_count
viewed_contract_count
signed_contract_count
```

can be misunderstood.

If `sent_contract_count` means current contract status = `SENT`, then signed contracts will not be included even if they were sent earlier.

I recommend either rename or clarify:

```text
sent_contract_count = current status SENT only
viewed_contract_count = current status VIEWED only
signed_contract_count = current status SIGNED only
```

Better add lifecycle fields:

```text
contract_sent_lifecycle_count
contract_viewed_lifecycle_count
```

where:

```text
contract_sent_lifecycle_count = count where sent_at is not null
contract_viewed_lifecycle_count = count where viewed_at is not null, only if viewed_at exists in schema
```

If `viewed_at` does not exist, do not add viewed lifecycle count.

**3. Use fallback for latest event type name**

For `latest_event_type_name`, instruct Codex to use:

```sql
COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
```

This matches existing appointment analytics guidance: historical reports should prefer `snapshot_event_name`, with `appointment_event_types.event_type_name` only as fallback. 

**4. Add database check constraints**

You already have validation checks, but I would add DB constraints too:

```text
source_confidence IN ('high', 'medium', 'low')
funnel_stage IN (...)
conversion_outcome IN (...)
contract_currency = 'EUR'
payment_currency = 'EUR'
```

This protects the table if refresh logic changes later.

**5. Make JSON flags null-safe**

For `source_quality_flags` and `data_quality_flags`, tell Codex not to produce arrays with nulls.

Bad:

```json
[null, "missing_first_source", null]
```

Good:

```json
["missing_first_source"]
```

Recommended instruction:

```text
Build JSON flag arrays using null-safe logic. Do not leave null values inside source_quality_flags or data_quality_flags.
```

**6. Add refresh transaction requirement**

Because you are doing delete-and-reinsert, it must run inside one transaction:

```text
BEGIN
DELETE org rows
INSERT fresh org rows
RUN validation checks
COMMIT
```

If validation fails:

```text
ROLLBACK
```

This is important because otherwise the org can temporarily have zero diagnostic rows if insert fails after delete.

**7. Add one validation for source row coverage**

Add this validation:

```text
For every active non-deleted lead in the selected org, exactly one diagnostic snapshot row must exist.
```

You already say row count should match active leads, but “exactly one row per active lead” is stronger because it catches duplicate/missing lead IDs.

**8. Be strict on one-to-many joins**

Tell Codex to pre-aggregate child tables before joining to leads:

```text
opt_ins
appointments
fathom_call_records
contracts
payments
refunds
```

This avoids row multiplication. Revenue skill already warns to pre-aggregate one-to-many child tables to avoid double-counting. 

**My final recommendation**

The file is good. I would only add these corrections:

```text
1. Add Fathom missing coverage fields.
2. Clarify current-status vs lifecycle contract counts.
3. Use snapshot_event_name with event type fallback.
4. Add DB check constraints.
5. Make JSON flag arrays null-safe.
6. Run delete-insert-validation inside one transaction.
7. Strengthen exactly-one-row-per-active-lead validation.
8. Pre-aggregate all child tables before joining to leads.
```

After these, it is safe to give to Codex.
