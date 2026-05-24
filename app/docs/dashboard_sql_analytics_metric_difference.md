# Dashboard vs SQL Analytics Metric Difference

## What Is The Issue?

The dashboard and chatbot are using different definitions for appointment-based KPI metrics.

The dashboard KPI cards do not simply count every appointment row. For dashboard-style metrics, appointments are first deduplicated by lead, using the latest appointment for that lead inside the selected period. Then the dashboard applies KPI-specific rules, such as excluding cancelled or rescheduled appointments from scheduled calls.

The chatbot SQL analytics answer counted raw appointment rows for some metrics. That makes the chatbot numbers higher when a lead has multiple appointment rows due to rescheduling, cancellation, rebooking, or unresolved outcomes.

This is a metric-definition issue, not a timezone issue. The dashboard is using Asia/Kolkata for this org, and the SQL tool is also configured for Asia/Kolkata.

## Example: May 1 To May 15, 2026

User question:

```text
new leads, booking rate, booked call, scheduled calls, calls taken, no shows in 1st may to may 15?
```

Dashboard values shown:

| Metric | Dashboard |
|---|---:|
| New Leads | 209 |
| Booking Rate | 70.33% |
| Booked Calls | 147 |
| Scheduled Calls | 97 |
| Calls Taken | 89 |
| No Show | 8 |

Chatbot answered:

| Metric | Chatbot |
|---|---:|
| New Leads | 209 |
| Booking Rate | 75.12% |
| Booked Calls | 157 |
| Scheduled Calls | 157 |
| Calls Taken | 149 |
| No Show | 8 |

## Why The Difference Happens

### New Leads

There is no mismatch here.

Both systems count non-deleted leads created in the selected date range.

```text
New Leads = 209
```

### Booked Calls

The booked-call mismatch is caused by counting different things.

The chatbot counted appointment rows:

```text
Raw appointment rows in the period = 157
```

The dashboard counts leads with appointments:

```text
Unique leads with appointments, deduped to latest appointment per lead
```

So the dashboard shows:

```text
Booked Calls = 147
```

The important difference is:

```text
Chatbot: 1 appointment row = 1 booked call
Dashboard: 1 lead = max 1 booked call in the selected period
```

This matters because one lead can have more than one appointment row in the same date range.

Example:

| Lead | Appointment row | What happened | Chatbot count | Dashboard count |
|---|---|---|---:|---:|
| Lead A | May 3 appointment | Original booking | 1 | 0 |
| Lead A | May 7 appointment | Rescheduled/rebooked latest appointment | 1 | 1 |

In this example, the chatbot counts 2 booked calls because there are 2 appointment rows. The dashboard counts 1 booked call because there is only 1 lead, and it keeps the latest appointment for that lead.

That is what happened in the May 1 to May 15 data:

```text
157 appointment rows
147 unique latest-appointment leads
10 extra rows are repeat appointment activity for leads already counted once
```

So booked calls are different because the chatbot counted duplicate appointment history, while the dashboard counted deduped lead-level bookings.

### Scheduled Calls

The chatbot reused the raw appointment count:

```text
Scheduled Calls = 157
```

The dashboard excludes latest appointments that are cancelled or rescheduled:

```text
Scheduled Calls = latest appointment per lead is not CANCELED or RESCHEDULED
```

So the dashboard shows:

```text
Scheduled Calls = 97
```

### Calls Taken

The chatbot effectively used this broad logic:

```sql
a.no_show = false
```

That is not enough to prove a call was taken.

An appointment can have `no_show = false` and still be cancelled, rescheduled, or unresolved. For dashboard-style SQL analytics, calls taken should be based on the latest past appointment per lead and completed/taken outcomes, not only on `no_show = false`.

Completed/taken outcomes are:

```text
WON
PARTIAL_PAYMENT
FOLLOW_UP
LOST
UNQUALIFIED
```

This is why the chatbot showed:

```text
Calls Taken = 149
```

while the dashboard showed:

```text
Calls Taken = 89
```

### No Show

There is no mismatch in this example.

Both systems returned:

```text
No Show = 8
```

### Booking Rate

Booking rate depends on booked calls.

The chatbot used its raw booked-call count:

```text
157 / 209 * 100 = 75.12%
```

The dashboard used the dashboard booked-call count:

```text
147 / 209 * 100 = 70.33%
```

So the booking rate mismatch is caused by the booked-call definition mismatch.

## Change Needed In SQL Analytics

For dashboard-style KPI wording, SQL analytics should use dashboard-style definitions:

| User wording | Correct SQL analytics basis |
|---|---|
| New Leads | Leads created in the selected period |
| Booked Calls | Unique leads with at least one appointment in the period, deduped to latest appointment per lead |
| Scheduled Calls | Deduped latest appointment is not cancelled or rescheduled |
| Calls Taken | Deduped latest past appointment has a completed/taken outcome |
| No Show | Deduped latest past appointment is marked no-show or has no-show outcome |
| Booking Rate | Booked Calls divided by New Leads |

The fix should update SQL analytics instructions so dashboard-style questions do not use raw appointment row counts.
