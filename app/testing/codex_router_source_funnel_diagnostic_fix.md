# Codex Implementation Instruction: Route Weak Source Funnel Performance to Diagnostic Analytics

## Goal

Fix router behavior for questions like:

```text
Which source has the weakest funnel performance?
```

This question must route to:

```json
{
  "route": "diagnostic_analytics",
  "history_count": 0,
  "standalone_question": "Which source has the weakest funnel performance?"
}
```

Currently it is being routed to `sql_analytics`. That is incorrect because the question is asking for source-level funnel diagnosis across multiple funnel stages, not a direct SQL metric/table.

## Scope

Make minimum changes.

Update only the router prompt/configuration unless tests require a small fixture update.

Do not change:

- SQL analytics skills
- diagnostic analytics tool logic
- diagnostic analytics answer instructions
- lead_analytics
- appointment_analytics
- revenue_analytics
- acquisition_analytics
- lead_profile_analytics

## Reason

The router currently allows `sql_analytics` for direct metric/report questions, including funnel analytics and source performance. That makes the phrase “source funnel performance” ambiguous.

However, “weakest funnel performance” means the user wants diagnostic interpretation across the funnel, such as:

- lead to booked call
- booked to completed call
- completed call to signed contract
- signed to paid
- paid conversion
- collected revenue quality
- misleading/high-volume but weak-conversion source patterns

This should be handled by `diagnostic_analytics`, specifically source diagnostic logic, not by normal SQL analytics.

## Required Router Change

In `router.md`, add a new explicit decision rule before the generic rule that prefers `sql_analytics` for direct metric reports.

Add this section under `## Decision Rules`:

```md
Route source-level funnel quality questions to `diagnostic_analytics` when the user asks for weakest, worst, poor, weak, underperforming, bottleneck, leaking, or misleading source performance across the funnel.

These questions are diagnostic because they require comparing multiple funnel stages and interpreting source quality, not returning one direct metric.

Examples:
- Which source has the weakest funnel performance?
- Which source has the worst funnel performance?
- Which source is weakest across the funnel?
- Which source has weak conversion through the funnel?
- Which source is leaking the most in the funnel?
- Which source has high leads but weak conversion?
- Which source books calls but does not convert?
- Which source completes calls but does not sign?
- Which source signs but does not pay?
```

## Required Ambiguous Routing Examples

In the `## Ambiguous Routing Examples` section of `router.md`, add these examples:

```md
- "Which source has the weakest funnel performance?" → `diagnostic_analytics`
- "Which source has the worst funnel performance?" → `diagnostic_analytics`
- "Which source is weakest across the funnel?" → `diagnostic_analytics`
- "Which source has weak conversion through the funnel?" → `diagnostic_analytics`
- "Which source is leaking the most in the funnel?" → `diagnostic_analytics`
- "Which source has high leads but weak conversion?" → `diagnostic_analytics`
- "Which source books calls but does not convert?" → `diagnostic_analytics`
- "Which source completes calls but does not sign?" → `diagnostic_analytics`
- "Which source signs but does not pay?" → `diagnostic_analytics`
```

## Keep These Existing SQL Routes Unchanged

Do not over-route all source questions to diagnostic analytics.

These should remain `sql_analytics`:

```md
- "Which source generated the most revenue?" → `sql_analytics`
- "Show revenue by source." → `sql_analytics`
- "Show appointment count by source." → `sql_analytics`
- "Show no-show rate by source." → `sql_analytics`
- "Show funnel by source." → `sql_analytics`
- "Lead trend by source." → `sql_analytics`
```

Reason: these are direct metric/table questions, not diagnostic interpretation.

## Diagnostic Flow Expectation

For:

```text
Which source has the weakest funnel performance?
```

The router should output:

```json
{
  "route": "diagnostic_analytics",
  "history_count": 0,
  "standalone_question": "Which source has the weakest funnel performance?"
}
```

The diagnostic agent should then use source diagnostic tooling, normally:

```text
get_diagnostic_source_snapshot
```

Use `source_basis = "first"` unless the user explicitly says latest source, last source, last-touch source, or recent source.

## Regression Tests to Add

Add or update router tests for these cases.

### Must route to diagnostic_analytics

```json
[
  {
    "question": "Which source has the weakest funnel performance?",
    "expected_route": "diagnostic_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Which source has the worst funnel performance?",
    "expected_route": "diagnostic_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Which source is leaking the most in the funnel?",
    "expected_route": "diagnostic_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Which source has high leads but weak conversion?",
    "expected_route": "diagnostic_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Which source books calls but does not convert?",
    "expected_route": "diagnostic_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Which source completes calls but does not sign?",
    "expected_route": "diagnostic_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Which source signs but does not pay?",
    "expected_route": "diagnostic_analytics",
    "expected_history_count": 0
  }
]
```

### Must remain sql_analytics

```json
[
  {
    "question": "Which source generated the most revenue?",
    "expected_route": "sql_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Show revenue by source.",
    "expected_route": "sql_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Show appointment count by source.",
    "expected_route": "sql_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Show no-show rate by source.",
    "expected_route": "sql_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Show funnel by source.",
    "expected_route": "sql_analytics",
    "expected_history_count": 0
  },
  {
    "question": "Lead trend by source.",
    "expected_route": "sql_analytics",
    "expected_history_count": 0
  }
]
```

## Acceptance Criteria

The implementation is complete when:

1. `Which source has the weakest funnel performance?` routes to `diagnostic_analytics`.
2. The standalone question remains exactly the user question when no history is needed.
3. `history_count` remains `0` for independent source-funnel questions.
4. Direct metric questions like `Show revenue by source` and `Show no-show rate by source` still route to `sql_analytics`.
5. No SQL skill selection logic is changed.
6. No diagnostic tool implementation is changed.
7. Existing router output format remains valid JSON only.

## Important Note

Do not solve this by adding a special case in the SQL agent.

This is a router disambiguation issue. The router must send source-level funnel quality and weakest/worst source questions to `diagnostic_analytics` before the SQL analytics flow starts.
