# Codex Addendum: Remove Issue-Pattern Table From Default Diagnostic Funnel Answers

## Goal

Update diagnostic analytics answer behavior so normal funnel-leakage and post-call conversion answers show only the individual issue view.

Do not show the issue-pattern / reason-combination table by default.

This change is required because the issue-pattern table is technically correct but confusing for business users. It can show a lower count for a single issue pattern while the individual issue table shows a higher count for the same issue appearing anywhere.

Example confusion:

```text
Issue pattern table:
Not ready yet / needs more time = 12

Individual issue table:
Not ready yet / needs more time = 50
```

This happens because:

```text
12 = leads where that was the full detected issue pattern
50 = leads where that issue appeared anywhere, alone or with other issues
```

Even though this is mathematically valid, it is not ideal for client-facing diagnostic answers.

---

## Required Change

For normal diagnostic answers, remove the issue-pattern / reason-combination table.

Use only the individual issue table.

This applies to questions such as:

```text
Where are we losing people in the funnel?
Why are leads not converting?
Why are completed-call leads not signing?
Why are people not paying after calls?
What are the main post-call blockers?
Where is the funnel leaking?
```

---

## Default Final Answer Structure

For funnel leakage questions with text insights, use this structure:

```text
<One-line diagnosis>

For leads created between <display_start_date> and <display_end_date>, <total_leads> leads entered the funnel.

<Funnel stage table>

What this means:
<short explanation of largest stuck groups>

Known reasons for the biggest stuck group: <friendly stuck group label>

One lead can have multiple issues, so this table does not sum to <selected_stuck_group_count>.

<Individual issue table>

Coverage note:
<coverage explanation>

Recommended next action:
<1-2 practical business actions>
```

Do not include an issue-pattern table unless the user explicitly asks for issue combinations.

---

## Funnel Stage Table

Keep the mutually exclusive final-stage funnel table.

The funnel stage rows must sum to total leads.

Use this table format:

```markdown
| Funnel stage | Leads | What this means |
|---|---:|---|
| Never booked a call | <never_booked> | Leads did not reach the appointment stage |
| Booked but did not complete call | <booked_not_completed> | Leads booked a call but did not attend/complete it |
| Completed call but did not sign | <completed_not_signed> | Leads attended the call but did not move to signed contract |
| Signed but not paid | <signed_not_paid> | Leads signed but payment was not completed |
| Paid / converted | <paid_converted> | Leads completed the paid conversion path |
| **Total** | **<total_leads>** | All leads in the selected period |
```

Validation:

```text
never_booked
+ booked_not_completed
+ completed_not_signed
+ signed_not_paid
+ paid_converted
= total_leads
```

If this validation fails, do not show the funnel stage table.

---

## Individual Issue View

Use this as the only default text-reason table.

Use this table format:

```markdown
| Individual issue | Leads with this issue | % of stuck leads | % of all issue mentions |
|---|---:|---:|---:|
```

Before the table, always add:

```text
One lead can have multiple issues, so this table does not sum to <selected_stuck_group_count>.
```

Where:

```text
selected_stuck_group_count = the biggest stuck group count selected from the funnel table
```

Example:

```text
One lead can have multiple issues, so this table does not sum to 158.
```

---

## Individual Issue Counting Rules

Use lead-level distinct counts.

Do not count raw text insight rows as leads.

For each issue:

```text
leads_with_issue = COUNT(DISTINCT lead_id) where the issue appeared for that lead
```

Percent calculations:

```text
% of stuck leads =
  leads_with_issue / selected_stuck_group_count

% of all issue mentions =
  leads_with_issue / total_known_lead_issue_mentions
```

Where:

```text
total_known_lead_issue_mentions = sum of distinct-lead issue counts across all known issue categories
```

One lead can contribute to multiple issue categories.

Therefore:

```text
sum(leads_with_issue) can be greater than selected_stuck_group_count
```

This is expected.

---

## Display Limits

Default:

```text
individual_issue_distribution: top 10
```

Only show top 20 if the user explicitly asks:

```text
show more
show top 20
give me detailed breakdown
show all major reasons
```

Do not show all reason enum values by default.

If there are more issue categories beyond the displayed limit, optionally add this sentence:

```text
Showing the top 10 known issues. Smaller issue groups are not shown in this table.
```

---

## Unknown And Missing Text Handling

Do not include `unknown` as a normal issue in the individual issue ranking by default.

Show missing/unknown reason information in the coverage note instead.

Coverage note should include:

```text
selected_stuck_group_count
leads_with_text_insights
known_reason_leads
leads_without_text_insights
unknown_reason_leads
```

Use business-friendly wording:

```text
The text reason analysis is directional. Out of <selected_stuck_group_count> leads in this stuck group, <leads_with_text_insights> had usable text insight coverage. <known_reason_leads> had a known reason, <leads_without_text_insights> had no usable text insight, and <unknown_reason_leads> had text but the reason was still unclear.
```

If text coverage is low, add:

```text
Reason coverage is limited, so treat this as directional rather than a complete explanation.
```

---

## User-Friendly Labels

Never show raw enum values in the final answer.

Use user-friendly labels.

Examples:

```text
timing_issue -> Not ready yet / needs more time
needs_partner_approval -> Waiting for partner or decision-maker approval
follow_up_pending -> Follow-up still pending
needs_more_information -> Needs clearer information
trust_issue -> Needs more trust or proof
price_or_budget -> Price or budget concern
payment_friction -> Payment issue or payment not completed
technical_issue -> Link or technical issue
no_show -> Missed or cancelled call
poor_fit -> Not a strong fit
unknown -> Reason not clear
```

Do not show snake_case values unless the user explicitly asks for raw technical fields.

---

## Do Not Show Issue-Pattern Table By Default

Do not show tables with these titles by default:

```text
Issue patterns found in stuck leads
Issue combination
Reason combination distribution
Exact issue combination per lead
Issue pattern found in leads
```

Do not show columns like:

```text
Issue pattern found in leads
Exact issue combination
Issue combination
```

Do not show rows like:

```text
Other issues
Other lower-volume combinations
Other lower-volume patterns
```

because these belong to the issue-pattern / combination view, which should not be part of default business answers.

---

## When Issue-Pattern Table Is Allowed

Only show the issue-pattern / combination table if the user explicitly asks for it.

Allowed trigger examples:

```text
Show issue combinations.
What combinations of issues did leads have?
Show reason combinations.
How many leads had multiple issues together?
What issue patterns appeared together?
```

Even then:

- Explain clearly that each lead appears once in the combination table.
- Keep top 10 by default.
- Use user-friendly labels.
- Ensure the issue-pattern table sums to the selected stuck group count.

---

## Tool Output Guidance

The backend text reason tool may still compute issue-pattern distributions internally for validation or optional use.

However, for default diagnostic answers, the final agent response should consume only:

```text
individual_issue_distribution
text_insight_coverage
recommended_focus
limitations
```

The final answer should ignore or hide:

```text
reason_combination_distribution
issue_pattern_distribution
```

unless the user explicitly asks for combinations.

---

## Correct Sample Output Section

Use this style:

```markdown
Known reasons for the biggest stuck group: Completed call but did not sign

One lead can have multiple issues, so this table does not sum to 158.

| Individual issue | Leads with this issue | % of stuck leads | % of all issue mentions |
|---|---:|---:|---:|
| Not ready yet / needs more time | 50 | 31.65% | 19.31% |
| Waiting for partner or decision-maker approval | 35 | 22.15% | 13.51% |
| Follow-up still pending | 32 | 20.25% | 12.36% |
| Needs clearer information | 28 | 17.72% | 10.81% |
| Needs more trust or proof | 22 | 13.92% | 8.49% |
| Price or budget concern | 19 | 12.03% | 7.34% |
| Payment issue or payment not completed | 15 | 9.49% | 5.79% |
| Link or technical issue | 10 | 6.33% | 3.86% |
| Missed or cancelled call | 9 | 5.70% | 3.47% |
| Not a strong fit | 9 | 5.70% | 3.47% |
```

Do not add an issue-pattern table after this section in normal answers.

---

## Tests To Add

### Test 1: Default Funnel Answer Does Not Include Issue Patterns

For this question:

```text
Where are we losing people in the funnel?
```

The final answer must include:

```text
Individual issue
Leads with this issue
```

The final answer must not include:

```text
Issue pattern found in leads
Issue combination
Reason combination distribution
Exact issue combination
Other issues
```

### Test 2: Individual Issue Table Can Exceed Cohort Total

If selected stuck group count is 158 and the individual issue table contains issue counts whose sum is greater than 158, the answer is valid only if it includes:

```text
One lead can have multiple issues, so this table does not sum to 158.
```

### Test 3: Explicit Combination Request

If the user asks:

```text
Show issue combinations for completed-call leads who did not sign.
```

Then the final answer may show an issue-pattern / combination table.

The table must:

```text
count each lead once
sum to the selected stuck group count
use user-friendly labels
use top 10 by default
```

### Test 4: Raw Enum Values Are Not Shown

The final answer must not show raw enum values such as:

```text
timing_issue
needs_partner_approval
price_or_budget
trust_issue
payment_friction
```

unless the user explicitly asks for raw technical fields.

### Test 5: Funnel Stage Total Still Matches

The final answer must still validate:

```text
never_booked
+ booked_not_completed
+ completed_not_signed
+ signed_not_paid
+ paid_converted
= total_leads
```

---

## Completion Criteria

This task is complete only when:

- Normal funnel leakage answers show the individual issue table only.
- Issue-pattern / reason-combination tables are hidden by default.
- Issue-pattern tables appear only when explicitly requested.
- Individual issue table uses distinct lead counts.
- Individual issue table includes the note that one lead can have multiple issues.
- Raw enum values are converted into user-friendly labels.
- Funnel stage counts remain mutually exclusive and sum to total leads.
- Text reason cohort matches the selected stuck group count.
