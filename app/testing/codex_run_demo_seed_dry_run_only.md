# Codex Prompt — Run Demo Seed Script Dry Run Only

## Goal

Run only the dry-run for the updated demo seed script.

Do not run the actual seed yet.

---

## Command to Run

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --dry-run
```

---

## Strict Instructions

Do not run:

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --force
```

Do not insert, update, delete, clean, truncate, or seed anything in the database yet.

This step is only to verify the planned dummy/demo data before any database write happens.

---

## Share the Full Dry-Run Output

After running dry-run, share the full terminal output.

Make sure the output includes:

```text
planned row counts
monthly lead distribution
source distribution
scenario distribution
appointment counts
completed appointment count
Fathom record count
diagnostic_text_insights count
validation/safety messages
any warnings about optional tables
```

---

## Expected Key Counts

The dry-run output should be close to:

```text
leads: 500
opt_ins: 650
appointments: 445
completed appointments: 285
fathom_call_records: 285
payments: 190
refunds: 12
diagnostic_text_insights: 405
diagnostic_lead_snapshot expected: 500
```

If any count is meaningfully different, explain why before proceeding.

---

## Fathom Rule to Confirm

Confirm that the dry-run shows:

```text
completed appointments = fathom_call_records
completed appointments missing Fathom = 0
Fathom records for no-show appointments = 0
Fathom records for canceled appointments = 0
Fathom records for rescheduled appointments = 0
Fathom records for future appointments = 0
```

For this client demo, completed/attended calls must have 100% Fathom coverage.

---

## Optional Table Check

Before actual seed later, confirm whether any dummy-org rows already exist in these optional tables:

```text
invoices
payment_links
payment_proofs
contract_subscriptions
subscription_checkout_links
unmatched_payments
```

For this first demo, these tables should not be seeded by default.

If rows already exist for:

```text
org_dummy_client_demo_001
```

then stop and report that before running actual seed.

---

## Live Org Safety Check Before Actual Seed

Before any future `--force` run, make sure this placeholder in `seed_demo_data.py` is replaced:

```python
"REPLACE_WITH_LIVE_CLIENT_ORG_ID_BEFORE_RUNNING"
```

It must be replaced with the real live client org ID inside:

```python
BLOCKED_ORG_IDS
```

Do not run actual seed until this is done.

---

## Next Step

After dry-run, do not proceed automatically.

Share the output for review.

Only after review and approval should the actual seed command be considered:

```bash
python scripts/seed_demo_data.py --org-id org_dummy_client_demo_001 --force
```
