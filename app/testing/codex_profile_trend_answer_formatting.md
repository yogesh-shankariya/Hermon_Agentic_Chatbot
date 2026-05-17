# Codex Update — Format Profile Trend Answers Like Existing Source Trend Answers

## Goal

For profile trend questions like:

```text
Monthly leads trend by profession.
Show profession trend by month.
Which professions are joining recently?
Monthly leads trend by employment status.
```

format the final answer like the existing source trend answer.

The final output should be business-friendly and pivoted by month.

---

## Desired Final Answer Shape

Use this style:

```text
Trend period: Feb 2026 through Apr 2026 (default previous 3 completed months)
Total matching leads: 280
In Apr 2026, Business Owner generated the most leads at 28, up 40.00% from Mar 2026
```

Then show a pivot-style table:

```text
Profession | Feb 2026 | Mar 2026 | Apr 2026
Business Owner | 16 | 20 (+25.00%) | 28 (+40.00%)
Employee | 14 | 15 (+7.14%) | 16 (+6.67%)
Self-employed | 11 | 13 (+18.18%) | 16 (+23.08%)
```

---

## Important Rule

The SQL should remain row-based.

Do not generate hardcoded SQL pivot columns.

The SQL result should return:

```text
month
month_start
profession
lead_count
previous_period_lead_count
percentage_change
total_matching_leads
```

The final answer can format those rows into a pivot table.

---

## Applies To

Apply this trend formatting to:

```text
monthly leads trend by profession
monthly lead trend by profession
profession trend by month
which professions joined recently
which professions are increasing recently
monthly leads trend by employment status
employment status trend by month
```

---

## Profile Trend Summary Rules

Before the table, include:

```text
Trend period: <first month> through <last month> (<default/date-range note>)
Total matching leads: <total>
In <latest month>, <top profile group> generated the most leads at <count>, <change text from previous month>
```

Example:

```text
Trend period: Feb 2026 through Apr 2026 (default previous 3 completed months)
Total matching leads: 280
In Apr 2026, Business Owner generated the most leads at 28, up 40.00% from Mar 2026
```

If previous month value is zero or missing, use:

```text
In Apr 2026, Business Owner generated the most leads at 28.
```

Do not invent percentage change if denominator is zero or unavailable.

---

## Table Format

For profession trend:

```markdown
| Profession | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Business Owner | 16 | 20 (+25.00%) | 28 (+40.00%) |
| Employee | 14 | 15 (+7.14%) | 16 (+6.67%) |
```

For employment status trend:

```markdown
| Employment status | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Full-time employed | 26 | 29 (+11.54%) | 35 (+20.69%) |
| Business owner | 18 | 22 (+22.22%) | 28 (+27.27%) |
```

---

## Sorting

Default sort for the final pivot table:

```text
Sort by latest month lead_count descending.
```

If tied:

```text
Sort by total lead_count across the displayed period descending.
Then sort alphabetically.
```

---

## Percentage Change Display

For each month after the first month, show:

```text
<count> (<percentage_change>%)
```

Examples:

```text
20 (+25.00%)
15 (-6.25%)
8 (0.00%)
```

For the first month, show only count:

```text
16
```

If previous period count is zero or null:

```text
<count> (new)
```

or just:

```text
<count>
```

Prefer simple display:

```text
<count>
```

if percentage cannot be safely calculated.

---

## SQL Requirements

For profile monthly trend SQL, return row-based data like:

```text
month_start
month_label
profile_value
lead_count
previous_period_lead_count
percentage_change
total_matching_leads
```

Use latest lead-level profile answer logic.

For profession:

```text
latest non-empty answer to "What do you do for work?"
```

For employment status:

```text
latest non-empty answer to "What is your employment status?"
```

Use lead-created month:

```text
DATE_TRUNC('month', leads.created_at)
```

Use distinct lead count:

```text
COUNT(DISTINCT l.id)
```

Do not count opt-ins unless the user explicitly asks for opt-ins/submissions.

---

## Wording Rule

For lead-level profile trends, include this wording:

```text
This is based on the latest lead-level opt-in profile answer.
```

Optional short version:

```text
Based on latest lead-level profile answers.
```

Do not say:

```text
exact opt-in submission trend
```

unless the query is opt-in-level.

---

## Example Final Answer

```markdown
Trend period: Feb 2026 through Apr 2026 (default previous 3 completed months)
Total matching leads: 280
In Apr 2026, Business Owner generated the most leads at 28, up 40.00% from Mar 2026

Based on latest lead-level profile answers.

| Profession | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Business Owner | 16 | 20 (+25.00%) | 28 (+40.00%) |
| Employee | 14 | 15 (+7.14%) | 16 (+6.67%) |
| Self-employed | 11 | 13 (+18.18%) | 16 (+23.08%) |
| Sales or Marketing | 9 | 10 (+11.11%) | 12 (+20.00%) |
| Trader / Investor | 7 | 9 (+28.57%) | 11 (+22.22%) |
| Technology | 9 | 9 (0.00%) | 11 (+22.22%) |
| Healthcare | 6 | 6 (0.00%) | 7 (+16.67%) |
| Student | 5 | 4 (-20.00%) | 4 (0.00%) |
| Retired | 3 | 3 (0.00%) | 2 (-33.33%) |
| Unemployed | 2 | 1 (-50.00%) | 1 (0.00%) |
```

---

## Do Not Do

Do not:

```text
Do not answer profile trend questions as unsupported.
Do not use diagnostic analytics for generic profile trends.
Do not create a diagnostic profile trend tool.
Do not generate SQL pivot columns.
Do not count opt-ins when the user asks lead trend.
Do not omit the period summary.
Do not show a long paragraph when a trend table is clearer.
```
