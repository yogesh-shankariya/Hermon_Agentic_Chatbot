# Codex Update — Scope Diagnostic Table Formatting Change

## Context

The current diagnostic answer format for funnel-loss questions is already working well.

Do not change the existing answer format for questions like:

```text
Where are we losing people in the funnel?
Where are we losing leads?
Where is the funnel leaking?
Where are leads dropping?
```

These answers should keep their current format unless there is a specific bug or obvious readability issue.

---

## Required Scope Change

The new table-led diagnostic answer formatting should apply mainly to broad overview questions only.

Apply the new table-led structure to questions like:

```text
What's going on?
What is happening overall?
Give me a business overview.
What should I pay attention to?
What needs attention?
How is the business doing?
```

Do not apply it globally to every diagnostic answer.

---

## Important Exception — Funnel-Loss Questions

Do not change the existing format for funnel-loss questions.

Examples:

```text
Where are we losing people in the funnel?
Where are we losing leads?
Where is the funnel leaking?
Where are people dropping off?
Which funnel stage has the biggest drop?
```

For these questions:

```text
Keep the current diagnostic answer format.
Keep the current funnel-loss explanation style.
Do not force the new "Funnel view / Step conversion view / Source view" format.
Do not add extra tables unless the existing answer already uses them or the tool output clearly requires them.
```

Reason:

```text
The current answer for funnel-loss questions is already good and client-friendly.
Changing it may break a format that is working well.
```

---

## Where the New Format Should Be Used

Use the new table-led overview format only for broad overview questions.

Recommended structure for broad overview questions:

```text
1. One-line summary
2. Funnel view table
3. Step conversion view table
4. Source view table if source evidence is available
5. Short interpretation
6. Recommended next action
7. Cohort revenue caveat if revenue values are mentioned
```

Example questions:

```text
What's going on?
What should I pay attention to?
Give me a business overview.
What is happening overall?
How is the business performing?
```

---

## General Table Rule

Use tables when they improve clarity.

Good uses of tables:

```text
metric comparisons
funnel stage summaries
source comparisons
month-over-month comparisons
current vs previous period comparisons
step conversion rates
```

Do not force tables for:

```text
simple answers
unsupported metric responses
short caveat-only explanations
one-lead narrative answers
existing funnel-loss answers that are already working well
```

---

## Final Instruction

Implement the formatting improvement with narrow scope.

Do not change good existing diagnostic formats unnecessarily.

The goal is:

```text
Improve broad overview answers without breaking existing funnel-loss answers.
```
