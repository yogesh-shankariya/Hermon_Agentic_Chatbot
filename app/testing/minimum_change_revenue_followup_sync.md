# Minimum-Change Fix: Keep Revenue Trend and Revenue-Drop Follow-Up in Sync

## Goal

Fix the mismatch where:

- A direct SQL revenue trend answer uses payment-period revenue.
- The follow-up diagnostic answer explains a different metric using lead-created cohort revenue.

The current architecture is mostly working. Do not redesign it. Make the smallest safe change so follow-up questions preserve the same metric basis as the previous answer.

---

## Problem

Example:

User asks:

```text
show me revenue trend
```

Current route:

```text
sql_analytics
```

The SQL answer uses payment-period gross paid revenue:

```text
Feb 2026: €68,500
Mar 2026: €72,500
Apr 2026: €63,000
April dropped by €9,500 vs March.
```

Then user asks:

```text
what caused revenue drop?
```

Current route:

```text
diagnostic_analytics
```

The diagnostic answer uses lead-created cohort lifetime net collected revenue:

```text
Mar cohort: €59,500
Apr cohort: €61,500
April did not drop; it increased by €2,000.
```

This is inconsistent from the user’s point of view because the follow-up is supposed to explain the previous revenue drop, not switch to a different revenue definition.

---

## Root Cause

The router treats “what caused revenue drop?” as a broad diagnostic question and sends it to `diagnostic_analytics`.

That is correct for standalone broad questions like:

```text
Why did revenue drop last month?
```

But it is incorrect when the previous answer already established a specific SQL metric, period, and revenue basis.

The missing piece is metric-continuity handling for follow-up questions.

---

## Minimum-Change Principle

Do not add a new diagnostic table.

Do not rewrite the SQL analytics agent.

Do not change existing diagnostic tools.

Do not change the router output schema unless absolutely necessary.

Make this a prompt and context-planning fix first:

1. Update `router.md`.
2. Add a small guardrail to `diagnostic_analytics.md`.
3. Optionally add lightweight metric metadata to conversation history if the app already stores route/answer metadata.

---

## Desired Behavior

When the previous answer was:

```text
sql_analytics
```

and the user asks a follow-up such as:

```text
why did it drop?
what caused the drop?
what caused revenue drop?
why did revenue decrease?
explain this drop
why did this metric fall?
```

the router must preserve the previous SQL metric basis.

For the example above, the standalone question should become:

```text
Explain why gross paid revenue by payment date dropped from €72,500 in Mar 2026 to €63,000 in Apr 2026, using the same revenue basis as the previous revenue trend answer.
```

Route:

```text
sql_analytics
```

Not:

```text
diagnostic_analytics
```

---

## Router Change

Update `router.md` with this rule under `Context Rules` or `Decision Rules`.

```md
## Metric-Continuity Rule For Follow-Up Questions

If the current question asks why, what caused, explain, reason for, root cause, what happened, why did it drop, why did it increase, or similar causal wording, first check whether the latest previous Q&A turn contains a direct SQL analytics metric answer.

If the latest previous answer came from `sql_analytics` and the current question refers to that previous metric using wording such as "it", "this", "that", "drop", "increase", "decrease", "trend", "above", "previous", or repeats the same metric name, preserve the previous metric basis in the standalone question.

Preserve all available previous metric context:
- metric name
- amount type, such as gross paid revenue, net collected revenue, paid payment count, signed contract value, lead count, appointment count
- date field or basis, such as payment date, lead created date, appointment scheduled date, contract signed date
- period being compared
- current value
- previous value
- absolute change
- percentage change

In this case, route the follow-up to the same analytics family as the previous metric unless the user explicitly asks to switch to a broader business diagnosis.

For revenue/payment/contract trend follow-ups from SQL analytics, route to `sql_analytics`, not `diagnostic_analytics`, when the previous answer used payment-period revenue, gross paid revenue, net collected revenue by paid_at, paid payment count, refund amount, payment provider, program, or contract/payment tables.

Do not route this follow-up to `diagnostic_analytics` only because it contains "why" or "what caused". The previous metric basis takes priority.

Example:

Previous user question:
"show me revenue trend"

Previous answer:
"Trend period: Feb 2026 through Apr 2026. Gross paid revenue fell from €72,500 in Mar 2026 to €63,000 in Apr 2026."

Current user question:
"what caused revenue drop?"

Correct router output:
{
  "route": "sql_analytics",
  "history_count": 1,
  "standalone_question": "Explain why gross paid revenue by payment date dropped from €72,500 in Mar 2026 to €63,000 in Apr 2026, using the same revenue basis as the previous revenue trend answer."
}

Incorrect router output:
{
  "route": "diagnostic_analytics",
  "history_count": 0,
  "standalone_question": "What caused revenue to drop?"
}
```

---

## Diagnostic Analytics Guardrail

Update `diagnostic_analytics.md` with this guardrail.

```md
## Guardrail: Do Not Explain SQL Payment-Period Revenue Drops With Cohort Revenue

If the user asks to explain a revenue drop, revenue increase, or revenue trend that came from a previous `sql_analytics` answer, inspect the standalone question and previous context.

If the previous SQL answer used payment-period revenue, gross paid revenue, net collected revenue by payment date, paid payment count, refund amount, or any payment-table timing basis, do not explain it using `diagnostic_lead_snapshot` cohort revenue.

The diagnostic snapshot uses lead-created cohort logic and lifetime outcomes for leads created in the selected period. It cannot explain the exact payment-period revenue movement from the SQL revenue trend.

In that case, return a brief handoff-style answer:

"The previous revenue trend used payment-period revenue, but diagnostic analytics uses lead-created cohort revenue. I should not explain that payment-period drop using the diagnostic cohort snapshot. Please route this follow-up to SQL revenue analytics using the same revenue basis as the previous answer."

Do not call diagnostic tools for this case.

Only use diagnostic analytics when:
- the user asks a standalone broad business-diagnosis question, or
- the previous answer also used diagnostic cohort metrics, or
- the user explicitly asks for lead-cohort performance, funnel diagnosis, source quality, or conversion-quality diagnosis.
```

---

## SQL Analytics Behavior

No major SQL agent rewrite is required.

However, make sure the SQL agent can handle the rewritten standalone question:

```text
Explain why gross paid revenue by payment date dropped from €72,500 in Mar 2026 to €63,000 in Apr 2026, using the same revenue basis as the previous revenue trend answer.
```

Expected SQL analytics behavior:

1. Use `revenue_analytics` as the primary skill.
2. Keep the same revenue basis:
   - gross paid revenue
   - paid payments only
   - payment date / `paid_at`
   - Mar 2026 vs Apr 2026
3. Do not switch to lead-created cohort revenue.
4. Produce a small comparison that can explain the drop, for example:
   - paid payment count
   - gross paid amount
   - average paid payment amount
   - optionally program breakdown
   - optionally payment provider breakdown
   - optionally source breakdown if supported and useful

The answer should clearly say:

```text
This explains the payment-period gross paid revenue drop, not lead-cohort revenue.
```

---

## Optional Lightweight Metric Contract

If the app already stores local conversation metadata, add a small metric contract for SQL answers. This is optional but recommended.

Do not force a schema migration if it is not already easy.

Suggested metadata:

```json
{
  "route": "sql_analytics",
  "metric_basis": "payment_period",
  "metric_name": "gross_paid_revenue",
  "amount_type": "gross_paid",
  "date_field": "paid_at",
  "grain": "payment",
  "period_start": "2026-02-01",
  "period_end": "2026-05-01",
  "latest_period": "Apr 2026",
  "previous_period": "Mar 2026",
  "latest_value": 63000,
  "previous_value": 72500,
  "absolute_change": -9500,
  "percentage_change": -13.10
}
```

Then router can use this metadata instead of trying to infer everything from answer text.

If metadata is not available, use latest Q&A text as the source of context.

---

## Where To Apply Changes

Apply minimum changes in this order:

1. `router.md`
   - Add the Metric-Continuity Rule.
   - Add the example for revenue trend follow-up.

2. `diagnostic_analytics.md`
   - Add the guardrail that prevents diagnostic cohort revenue from explaining SQL payment-period revenue drops.

3. Optional application layer
   - If route and answer metadata are already stored, store `metric_basis`, `amount_type`, `date_field`, `grain`, and compared periods.
   - Do not add this if it requires heavy refactoring.

---

## Test Cases

### Test 1: Revenue Trend Follow-Up

Previous Q&A:

```text
Q: show me revenue trend
A: Gross paid revenue fell from €72,500 in Mar 2026 to €63,000 in Apr 2026.
```

Current question:

```text
what caused revenue drop?
```

Expected router output:

```json
{
  "route": "sql_analytics",
  "history_count": 1,
  "standalone_question": "Explain why gross paid revenue by payment date dropped from €72,500 in Mar 2026 to €63,000 in Apr 2026, using the same revenue basis as the previous revenue trend answer."
}
```

### Test 2: Standalone Diagnostic Question

Current question:

```text
why did revenue drop last month?
```

No previous SQL metric context.

Expected route:

```json
{
  "route": "diagnostic_analytics",
  "history_count": 0,
  "standalone_question": "Why did revenue drop last month?"
}
```

### Test 3: Explicit Lead-Cohort Switch

Previous Q&A:

```text
Q: show me revenue trend
A: Gross paid revenue by payment date dropped in April.
```

Current question:

```text
what about lead cohort performance, why did April leads monetize weaker?
```

Expected route:

```json
{
  "route": "diagnostic_analytics",
  "history_count": 1,
  "standalone_question": "Explain lead-created cohort performance for April leads compared with the previous period, focusing on why April leads monetized weaker."
}
```

### Test 4: Lead Trend Follow-Up

Previous Q&A:

```text
Q: show me lead trend
A: Leads increased from 90 in Mar 2026 to 108 in Apr 2026.
```

Current question:

```text
why did it increase?
```

Expected route:

```json
{
  "route": "sql_analytics",
  "history_count": 1,
  "standalone_question": "Explain why lead count increased from 90 in Mar 2026 to 108 in Apr 2026, using the same lead-created date basis as the previous lead trend answer."
}
```

### Test 5: Diagnostic Must Not Override Payment Basis

Input to diagnostic flow:

```text
Explain why gross paid revenue by payment date dropped from €72,500 in Mar 2026 to €63,000 in Apr 2026, using the same revenue basis as the previous revenue trend answer.
```

Expected diagnostic behavior if wrongly routed:

```text
Do not call diagnostic tools.
Return a safe message saying this should be handled by SQL revenue analytics because diagnostic revenue is lead-cohort based.
```

---

## Acceptance Criteria

This fix is complete when:

- A follow-up asking “what caused revenue drop?” after a SQL revenue trend stays in `sql_analytics`.
- The rewritten standalone question contains the previous revenue basis and compared months.
- Diagnostic analytics no longer explains SQL payment-period revenue movement with lead-created cohort revenue.
- Standalone broad diagnostic questions still route to `diagnostic_analytics`.
- Existing direct metric questions continue to route as before.
- Existing diagnostic questions such as “where are we losing people in the funnel?” continue to route as before.
- No new table or major architecture change is introduced.

---

## Final Expected User Experience

User:

```text
show me revenue trend
```

Assistant:

```text
Gross paid revenue dropped from €72,500 in Mar 2026 to €63,000 in Apr 2026.
```

User:

```text
what caused revenue drop?
```

Assistant should not say:

```text
April cohort revenue did not drop.
```

Assistant should say something like:

```text
The payment-period gross paid revenue drop came from fewer/lower paid payments in April compared with March. This uses the same payment-date revenue basis as the previous trend answer.
```
