# Apr 1 To May 15 Booking And Scheduled Difference

## Short Version

For Apr 1, 2026 through May 15, 2026, the chatbot and dashboard are using the same date window for the metrics that match:

| Metric | Chatbot / SQL | Dashboard |
|---|---:|---:|
| New Leads | 558 | 558 |
| Calls Taken | 229 | 229 |
| No Show | 36 | 36 |

So this is not a timezone issue and not a May 15 inclusivity issue.

The mismatch is only here:

| Metric | Chatbot / SQL | Dashboard | Difference |
|---|---:|---:|---:|
| Booked Calls | 369 | 367 | +2 |
| Booking Rate | 66.13% | 65.77% | caused by booked calls |
| Scheduled Calls | 264 | 263 | +1 |

Booking rate is different only because booked calls are different:

```text
Chatbot:   369 / 558 * 100 = 66.13%
Dashboard: 367 / 558 * 100 = 65.77%
```

## Correct Date Window Used

For inclusive business wording:

```text
Apr 1 to May 15
```

the SQL window should be:

```text
start_date = 2026-04-01 00:00:00 Asia/Kolkata
end_date   = 2026-05-16 00:00:00 Asia/Kolkata
```

This keeps May 15 included and May 16 excluded.

Using this window gives:

```text
New leads = 558
Calls taken = 229
No show = 36
```

Those match the dashboard, so the window is correct.

## What SQL Analytics Is Counting

The dashboard/backend definition says:

```text
Booked Calls = unique leads with at least one appointment in the period,
using their latest appointment, any outcome.
```

That means:

1. Take appointments in the selected schedule_time window.
2. Deduplicate to one latest appointment per lead.
3. Count the latest rows.

With current data:

```text
latest appointment rows per lead = 369
```

So SQL analytics returns:

```text
Booked Calls = 369
```

## Why Scheduled Calls Are Off By 1

Current latest-per-lead outcome breakdown includes this row:

```text
APPOINTMENT_BOOKED = 1
```

The current backend-style scheduled definition is:

```text
Scheduled Calls = latest appointment is not CANCELED and not RESCHEDULED
```

Under that definition, `APPOINTMENT_BOOKED` is still scheduled, so SQL counts it:

```text
Scheduled Calls = 264
```

If that one unresolved `APPOINTMENT_BOOKED` row is excluded:

```text
264 - 1 = 263
```

That matches the dashboard screenshot.

So the scheduled-call difference is caused by one latest appointment whose outcome is still:

```text
APPOINTMENT_BOOKED / Call Booked
```

## Why Booked Calls Are Off By 2

Booked calls are trickier.

The current backend/dashboard text says booked calls are:

```text
any outcome
```

So, by that written definition, the count is:

```text
Booked Calls = 369
```

If we exclude the same unresolved `APPOINTMENT_BOOKED` row:

```text
369 - 1 = 368
```

But the dashboard shows:

```text
Booked Calls = 367
```

So there is still one extra row that the screenshot is not counting.

The notable extra edge row in current data is a latest appointment that is now `CANCELED` and was updated after the selected period:

```text
appointment_id: 14c9bd0e-317b-468a-937b-a16be178f109
lead_id:        2af980cf-5a16-4cbb-8096-cacb8f6d8ad6
scheduled:      2026-04-15 18:30 Asia/Kolkata
created:        2026-04-12 15:01 Asia/Kolkata
updated:        2026-05-18 02:18 Asia/Kolkata
current outcome: CANCELED
```

If SQL excludes both:

```text
1 unresolved APPOINTMENT_BOOKED latest row
1 CANCELED latest row updated after the selected period
```

then:

```text
369 - 2 = 367
```

That matches the dashboard screenshot, but this is not the stated booked-call definition.

## Important Conclusion

Do not blindly change SQL analytics to `367` just because the screenshot shows `367`.

The stated definition says:

```text
Booked Calls = any outcome, latest appointment per lead.
```

That gives:

```text
369
```

To get the dashboard screenshot value:

```text
367
```

we would need to add extra exclusions that are not clearly stated:

```text
exclude APPOINTMENT_BOOKED
exclude one CANCELED row updated after the selected period
```

That may be:

- a dashboard cache/data-state mismatch,
- an unstated dashboard filter,
- an unstated business rule,
- or a bug in the dashboard card.

## Recommendation

Do not change the SQL definition yet.

The safe rule is:

```text
Use the documented/backend definition unless product confirms that Booked Calls should exclude unresolved APPOINTMENT_BOOKED rows or post-period cancellation updates.
```

The one change that might be reasonable after confirmation:

```text
Scheduled Calls should exclude APPOINTMENT_BOOKED if the dashboard intentionally treats unresolved bookings as not scheduled.
```

But for Booked Calls, the screenshot contradicts the written definition, so changing SQL analytics now would risk making the chatbot less correct.
