# Testing Output Notes

Files in this directory are generated artifacts from previous silver-truth runs.

Do not treat `revenue_analytics_silver_truth.md` or `revenue_analytics_silver_truth.csv` as monetary ground truth until they are regenerated with the current revenue prompt. The current revenue skill requires source money fields such as `payments.amount`, `refunds.amount`, and `contracts.total_value` to be divided by `100.0` for business-facing amounts.

Diagnostic snapshot money fields are different: `diagnostic_lead_snapshot` stores already-converted major-unit EUR values, so diagnostic snapshot outputs must not be divided by `100` again.
