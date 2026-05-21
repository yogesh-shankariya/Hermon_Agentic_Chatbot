# Chatbot vs Dashboard Metric Discrepancy

## Executive Summary

The dashboard and chatbot can currently show different numbers for questions that look the same to a business user.

This does not appear to be a raw data corruption issue. The main issue is that the chatbot sometimes uses a different metric basis than the dashboard.

The most important differences are:

- The dashboard appears to use Europe/Amsterdam business-day boundaries, while some chatbot queries use UTC/date filtering.
- The chatbot previously counted `no_show = false` as "calls taken", which incorrectly includes cancelled appointments.
- The dashboard shows payment-period cash collected, while diagnostic chatbot answers may show lifetime revenue from leads created in the period.
- The dashboard shows contracts signed during the selected period, while diagnostic chatbot answers may show lifetime signed contracts from leads created in the period.
- "New leads" was ambiguous: the dashboard means leads created in the period, while the chatbot previously interpreted it as leads currently in `NEW_LEAD` status.

## Business Impact

This creates a trust problem.

From the client perspective, the dashboard and chatbot appear to disagree on important business numbers:

- Revenue
- Contracts signed
- Calls taken
- Show rate
- New leads
- Period comparisons
- Diagnostic answers such as "what changed?"

Even if both numbers are technically explainable, the business experience is that the chatbot looks inaccurate.

## Examples Found

### 1. New Leads on May 15, 2026

User question:

> New leads on 15th May?

The chatbot answered:

> There were 4 new leads on 15 May 2026.

That answer used the wrong interpretation for dashboard parity.

What the chatbot counted:

- Leads created on May 15 that are still currently in `NEW_LEAD` status.

What the dashboard expects:

- Leads created on May 15.

Verified result:

- Dashboard-style count: 19 leads created on May 15, using Europe/Amsterdam business-day boundaries.
- Status-based count: 4 leads still in `NEW_LEAD` status.

Conclusion:

The chatbot answer was wrong for dashboard parity.

### 2. Calls Taken on May 15, 2026

The chatbot counted calls taken using:

```sql
no_show = false
```

This is too broad.

`no_show = false` means the appointment was not marked as a no-show. It does not mean the call actually happened.

Cancelled and rescheduled appointments can also have `no_show = false`.

On May 15, there were 5 cancelled appointments. The chatbot included them in calls taken.

Result:

- Chatbot calls taken: 14
- Dashboard calls taken: 9
- Difference: 5 cancelled appointments incorrectly counted by the chatbot

Conclusion:

The chatbot should exclude cancelled, rescheduled, booked-only, and future appointments from "calls taken".

### 3. Revenue / Cash Collected

The dashboard shows revenue based on actual payment activity during the selected period.

Example:

- Dashboard cash collected from May 1 to May 15: EUR 239,500

The chatbot diagnostic answer used a different basis:

- Lifetime revenue for leads created between May 1 and May 15.

Example:

- Chatbot diagnostic revenue for May 1 to May 15: EUR 129,600

These are both valid metrics, but they answer different questions.

Dashboard question:

> How much cash was collected during this period?

Diagnostic cohort question:

> How much lifetime revenue came from leads created during this period?

Conclusion:

The chatbot should not present cohort lifetime revenue as period revenue unless the user explicitly asks for cohort performance.

### 4. Contracts Signed

The dashboard counts contracts signed during the selected period using contract signed date.

Dashboard basis:

```text
contracts.signed_at inside selected period
```

The diagnostic chatbot may count signed contracts attached to leads created during the selected period.

Diagnostic cohort basis:

```text
leads.created_at inside selected period, then lifetime signed contracts for those leads
```

Conclusion:

For normal business reporting, the chatbot should use contract signed date, not lead-created cohort logic.

### 5. Timezone Difference

The dashboard appears to use Europe/Amsterdam business-day boundaries.

The chatbot sometimes uses UTC/date filtering.

That means "May 15" can represent two different 24-hour windows.

Europe/Amsterdam May 15:

```text
2026-05-14 22:00 UTC through 2026-05-15 21:59 UTC
```

UTC May 15:

```text
2026-05-15 00:00 UTC through 2026-05-15 23:59 UTC
```

Records near midnight can fall into different dates depending on the timezone.

Conclusion:

The chatbot should use the same business timezone as the dashboard: Europe/Amsterdam.

## Root Cause

The chatbot currently mixes multiple metric bases:

1. Dashboard-period metrics: metrics based on actual business activity during a date range.
2. Lead-cohort lifetime metrics: metrics based on leads created during a date range and their eventual outcomes.
3. Current-status metrics: metrics based on the current pipeline status of leads.
4. Opt-in or form-submission metrics: metrics based on acquisition submissions, not unique leads.

All of these can be useful, but they must not be silently mixed.

## Recommended Business Rule

For normal business questions, the chatbot should default to dashboard-period metrics.

| User question | Correct default basis |
|---|---|
| Revenue in May | Payments collected in May |
| Cash collected May 1-15 | Paid payments during May 1-15 |
| Contracts signed in May | Contracts signed during May |
| Calls taken on May 15 | Completed or taken appointments on May 15 |
| New leads on May 15 | Leads created on May 15 |
| What changed this month? | Dashboard-period comparison |

Cohort or lifetime metrics should only be used when the user explicitly asks for them.

| User question | Correct basis |
|---|---|
| Revenue from leads created in May | Lead-created cohort lifetime revenue |
| Lifetime value of May leads | Cohort lifetime revenue |
| Funnel performance for leads created in May | Lead-created cohort diagnostics |

## Long-Term Recommendation

The chatbot should have an independent analytics layer with clear metric definitions.

This layer should:

- Be owned by the chatbot system.
- Be rebuilt from raw source tables.
- Use Europe/Amsterdam business timezone.
- Store or compute dashboard-period metrics separately from cohort metrics.
- Version every metric definition.
- Include validation checks against known dashboard numbers.
- Clearly label every answer as dashboard-period or cohort-based.

The goal is not just to patch one answer. The goal is to make the chatbot consistently trustworthy.

## Proposed Direction

Create two separate chatbot analytics concepts.

### 1. Dashboard-Period Metrics

Used for normal business reporting.

Examples:

- New leads
- Calls booked
- Calls taken
- Show rate
- Contracts signed
- Contracted amount
- Cash collected
- Refunds
- Net collected

### 2. Lead-Cohort Diagnostics

Used for diagnostic and lifecycle questions.

Examples:

- Lifetime revenue from leads created in a period
- Funnel conversion of a lead cohort
- Source quality by lifetime outcomes
- Lead progression from created to paid

## Business Decisions Needed

The business should confirm:

1. Dashboard-period metrics are the default for normal chatbot questions.
2. Europe/Amsterdam is the official reporting timezone.
3. Cohort/lifetime metrics are allowed only when clearly requested or clearly labeled.
4. The chatbot should be validated against known dashboard numbers before being trusted for reporting.

## Final Takeaway

The chatbot is not just making small calculation mistakes. The deeper issue is that it currently lacks one consistent metric contract.

To restore trust, we need to define and enforce exactly what each business metric means, especially for date ranges.

The chatbot should not answer "revenue", "calls taken", "contracts", or "new leads" unless it uses the same metric basis the business expects.
