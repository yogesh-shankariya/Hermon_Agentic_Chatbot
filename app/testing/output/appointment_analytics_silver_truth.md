# Appointment Analytics Silver Truth

## 1. AAQ-001

**Question**

How many appointments do we have in total?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointment_count
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false;
```

**Generated final answer**

There are 451 appointments in total.

**Execution time:** 10.264 sec
**Status:** ok

## 2. AAQ-003

**Question**

How many calls were scheduled from 2026-01-01 to 2026-04-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS calls_scheduled_in_period
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date;
```

**Generated final answer**

There were 230 calls scheduled from 2026-01-01 up to, but not including, 2026-04-01.

**Execution time:** 16.806 sec
**Status:** ok

## 3. AAQ-004

**Question**

How many appointments were created in the system from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointments_created_in_period
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.created_at >= :start_date
  AND a.created_at < :end_date;
```

**Generated final answer**

There were 205 appointments created in the system from 2026-04-01 to 2026-05-01.

**Execution time:** 17.513 sec
**Status:** ok

## 4. AAQ-002

**Question**

How many appointments were scheduled from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointments_scheduled_in_period
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date;
```

**Generated final answer**

There were 218 appointments scheduled from 2026-04-01 to 2026-05-01.

**Execution time:** 18.244 sec
**Status:** ok

## 5. AAQ-006

**Question**

How many past appointments do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS past_appointments
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW();
```

**Generated final answer**

There are 450 past appointments.

**Execution time:** 8.893 sec
**Status:** ok

## 6. AAQ-007

**Question**

How many completed attended calls do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS completed_attended_calls
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND a.no_show = false;
```

**Generated final answer**

There are 396 completed attended calls.

**Execution time:** 12.693 sec
**Status:** ok

## 7. AAQ-010

**Question**

How many appointments have no setter assigned?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointments_without_setter
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND NULLIF(TRIM(a.setter_id), '') IS NULL;
```

**Generated final answer**

There are 358 appointments with no setter assigned.

**Execution time:** 11.053 sec
**Status:** ok

## 8. AAQ-005

**Question**

How many calls were added to the system from 2026-01-01 to 2026-04-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointments_created_in_period
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.created_at >= :start_date
  AND a.created_at < :end_date;
```

**Generated final answer**

There were 251 calls added to the system from 2026-01-01 through 2026-04-01.

**Execution time:** 30.409 sec
**Status:** ok

## 9. AAQ-009

**Question**

How many appointments have no host assigned?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointments_without_host
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND NULLIF(TRIM(a.host_id), '') IS NULL;
```

**Generated final answer**

There are no appointments without a host assigned.

**Execution time:** 12.588 sec
**Status:** ok

## 10. AAQ-008

**Question**

How many upcoming appointments are scheduled from 2026-05-05 to 2026-06-05?

**Generated SQL**

```sql
SELECT COUNT(*) AS upcoming_appointments
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time >= NOW()
```

**Generated final answer**

There is 1 upcoming appointment scheduled between May 5, 2026 and June 5, 2026.

**Execution time:** 27.268 sec
**Status:** ok

## 11. AAQ-014

**Question**

List appointments that have no host assigned.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND NULLIF(TRIM(a.host_id), '') IS NULL
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20;
```

**Generated final answer**

There are no appointments without a host assigned.

**Execution time:** 22.932 sec
**Status:** ok

## 12. AAQ-013

**Question**

List upcoming appointments scheduled from 2026-05-05 to 2026-06-05.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= NOW()
  AND a.schedule_time >= CAST(:start_date AS date)
  AND a.schedule_time < CAST(:end_date AS date) + INTERVAL '1 day'
ORDER BY a.schedule_time ASC, a.id ASC
LIMIT 20
```

**Generated final answer**

Total upcoming appointments in this date range: 1

Here is the complete list:

| Lead | Scheduled time | Event | Call category | Outcome | Source |
|---|---|---|---|---|---|
| Pascal van Leeuwen | 29 May 2026, 14:00 UTC | Qualification Call Freedom Academy (TF) | Sales Call | No Sale - Follow Up | Calendly |

**Execution time:** 45.273 sec
**Status:** ok

## 13. AAQ-016

**Question**

List appointments without an outcome set.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  'No Outcome' AS outcome_name,
  'NO_OUTCOME' AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.outcome_id IS NULL
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20;
```

**Generated final answer**

There are no appointments without an outcome set.

**Execution time:** 30.204 sec
**Status:** ok

## 14. AAQ-015

**Question**

List appointments that have no setter assigned.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND NULLIF(TRIM(a.setter_id), '') IS NULL
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching appointments: 358

Showing the first 20 appointments:

| Appointment ID | Scheduled time (UTC) | Lead | Event | Category | Outcome | Host ID | Source |
|---|---|---|---|---|---|---|---|
| 3ade1793-ba69-47e0-9ba1-27be6dd2f1e9 | 2026-05-05 13:00 | Ricardo Brandao | Strategy Call - Freedom - FU | Sales Call | Rescheduled | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |
| 1015339c-c476-424a-9d7d-3c3c6916cd24 | 2026-05-01 08:00 | Wesley Helmers | Qualification Call Freedom Academy (DMB) | Sales Call | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |
| 855bb48d-d0f3-4507-a5d2-e8168cc38aab | 2026-04-30 16:00 | Stephen William Bennett | Qualification Call Didi Bam Bam | Sales Call | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| d805d4b6-32fd-4ed4-a59d-76224d49573d | 2026-04-29 08:00 | Andre Steenkamp | Qualification Call Freedom Academy (TF) | Sales Call | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |
| 9cd689c3-9eec-4881-9db9-554ab6b90e9a | 2026-04-28 15:00 | Robert Voorn | Strategy Call - Freedom - (FU) | Sales Call | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |
| 63c52d25-6828-4bc1-adf7-d4cddc83bc39 | 2026-04-27 12:00 | Van der Veken Olivier | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |
| 64fcfad6-dd75-4e90-bbf6-239606afe477 | 2026-04-27 11:00 | Erik Bakker | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |
| c3c20a0f-8d8f-43f9-9ef2-8690900b8a73 | 2026-04-27 10:00 | Bahadir | Qualification Call Didi Bam Bam | Sales Call | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |
| f303cd0a-2ecd-4a46-b094-444665c19f76 | 2026-04-27 06:00 | Steve Grainger | Qualification Call Didi Bam Bam | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 8ba8ab47-7e8a-4a05-9e85-07bd833f7156 | 2026-04-26 18:00 | Roos ‘t Lam | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 3c46f3ca-64ee-4c8e-a0bb-29726819c99c | 2026-04-26 15:30 | Rob Schwarz | Qualification Call Freedom Academy (TF) | Sales Call | Canceled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 776a904d-e8df-4406-ada7-7ec3759c4ad1 | 2026-04-26 11:00 | Rene Solms | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 43dc2a30-2875-4649-95f9-e71f7df45bb8 | 2026-04-26 10:00 | Henry Stokkelaar | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| b47ac875-50da-46cd-92b4-330603f4eb59 | 2026-04-26 09:00 | Tom ter woord | Qualification Call Freedom Academy (TF) | Sales Call | Canceled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 2b6d4fb6-60a4-436b-a3c9-eba720748a7b | 2026-04-26 07:00 | Nake Dragomirov | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 52612ec3-1226-488b-894e-2145b2507c8f | 2026-04-26 06:00 | Aad Bouw | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| cf3f301d-f728-4483-bf04-0bae88df970b | 2026-04-26 06:00 | Kale green | Qualification Call Freedom Academy (TF) | Sales Call | Canceled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 87e4a8c1-2f37-40f4-8822-b0a8a08ef1e8 | 2026-04-25 15:00 | Bryan Casica | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 8e149174-dcf8-4255-892d-66d834e9c81f | 2026-04-25 14:00 | Eugenio Jedi Martinez | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly |
| 1b7169ce-2aa3-4071-bc08-394c8f40f6ff | 2026-04-25 13:00 | Sylvano van den Brink | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly |

**Execution time:** 40.520 sec
**Status:** ok

## 15. AAQ-012

**Question**

List completed attended calls from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
  AND a.no_show = false
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT :limit
```

**Generated final answer**

Total matching calls: 194

Showing the first 20 calls:

| Scheduled time (UTC) | Lead | Event | Outcome |
|---|---|---|---|
| 2026-04-30 16:00 | Stephen William Bennett | Qualification Call Didi Bam Bam | Rescheduled |
| 2026-04-29 11:00 | Albert de Bruin | Qualification Call Freedom Academy (TF) | Rescheduled |
| 2026-04-29 08:00 | Andre Steenkamp | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-28 15:00 | Robert Voorn | Strategy Call - Freedom - (FU) | Call Booked |
| 2026-04-27 12:00 | Van der Veken Olivier | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-27 11:00 | Erik Bakker | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-27 10:00 | Bahadir | Qualification Call Didi Bam Bam | Call Booked |
| 2026-04-27 06:00 | Steve Grainger | Qualification Call Didi Bam Bam | Call Booked |
| 2026-04-26 18:00 | Roos ‘t Lam | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 15:30 | Rob Schwarz | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-26 11:00 | Rene Solms | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 10:00 | Henry Stokkelaar | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 09:00 | Tom ter woord | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-26 07:00 | Nake Dragomirov | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 06:00 | Aad Bouw | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 06:00 | Kale green | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-25 15:00 | Bryan Casica | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-25 14:00 | Eugenio Jedi Martinez | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-25 13:00 | Sylvano van den Brink | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-25 12:00 | Constantin | Qualification Call Freedom Academy (TF) | Rescheduled |

**Execution time:** 65.121 sec
**Status:** ok

## 16. AAQ-019

**Question**

What is the appointment no-show rate?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW();
```

**Generated final answer**

Out of 450 past appointments, 54 were no-shows. The appointment no-show rate is 12.00%.

**Execution time:** 12.702 sec
**Status:** ok

## 17. AAQ-020

**Question**

What was the appointment no-show rate from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW();
```

**Generated final answer**

From 2026-04-01 to 2026-05-01, there were 24 no-shows out of 218 appointments, for a no-show rate of 11.01%.

**Execution time:** 15.187 sec
**Status:** ok

## 18. AAQ-021

**Question**

How many past appointments were no-shows?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW();
```

**Generated final answer**

Out of 450 past appointments, 54 were no-shows. The appointment no-show rate is 12.00%.

**Execution time:** 18.006 sec
**Status:** ok

## 19. AAQ-022

**Question**

How many no-show appointments were scheduled from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS no_show_appointments
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.no_show = true
```

**Generated final answer**

There were 24 no-show appointments scheduled from Apr 1, 2026 through Apr 30, 2026.

**Execution time:** 19.615 sec
**Status:** ok

## 20. AAQ-018

**Question**

List past appointments that do not have a Fathom record.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  false AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND NOT EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  )
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 368

Showing the first 20 most recent past appointments without a Fathom record:

| Scheduled time | Lead | Event | Outcome |
|---|---|---|---|
| 2026-05-05 13:00 UTC | Ricardo Brandao | Strategy Call - Freedom - FU | Rescheduled |
| 2026-05-01 08:00 UTC | Wesley Helmers | Qualification Call Freedom Academy (DMB) | No Sale - Follow Up |
| 2026-04-30 16:00 UTC | Stephen William Bennett | Qualification Call Didi Bam Bam | Rescheduled |
| 2026-04-29 11:00 UTC | Albert de Bruin | Qualification Call Freedom Academy (TF) | Rescheduled |
| 2026-04-29 08:00 UTC | Andre Steenkamp | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-28 15:00 UTC | Robert Voorn | Strategy Call - Freedom - (FU) | Call Booked |
| 2026-04-27 12:00 UTC | Van der Veken Olivier | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-27 11:00 UTC | Erik Bakker | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-27 10:00 UTC | Bahadir | Qualification Call Didi Bam Bam | Call Booked |
| 2026-04-27 06:00 UTC | Steve Grainger | Qualification Call Didi Bam Bam | Call Booked |
| 2026-04-26 18:00 UTC | Roos ‘t Lam | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 15:30 UTC | Rob Schwarz | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-26 11:00 UTC | Rene Solms | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 10:00 UTC | Henry Stokkelaar | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 09:00 UTC | Tom ter woord | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-26 07:00 UTC | Nake Dragomirov | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 06:00 UTC | Aad Bouw | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 06:00 UTC | Kale green | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-25 15:00 UTC | Bryan Casica | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-25 14:00 UTC | Eugenio Jedi Martinez | Qualification Call Freedom Academy (TF) | Call Booked |

**Execution time:** 53.549 sec
**Status:** ok

## 21. AAQ-017

**Question**

List appointments with a linked Fathom record.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id AS appointment_id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  true AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  )
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20
```

**Generated final answer**

Total matching appointments: 82

Showing the first 20 most recent appointments with a linked Fathom record:

| Scheduled time | Lead | Event | Outcome |
|---|---|---|---|
| 2026-04-24 09:00 UTC | Jeffrey Nussy | Strategy Call - Freedom - FU | Won |
| 2026-04-24 09:00 UTC | Robert Eduard | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-24 08:00 UTC | Mario van Beek | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-24 07:00 UTC | Erik van Hoof | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-23 18:00 UTC | Raymond Keppel | Qualification Call Freedom Academy (TF) | Won |
| 2026-04-23 18:00 UTC | Frank | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-23 15:00 UTC | mitar sekulic | Qualification Call Freedom Academy (TF) | Rescheduled |
| 2026-04-23 12:00 UTC | Chris Rouwhof | Qualification Call Freedom Academy (TF) | Won |
| 2026-04-23 11:45 UTC | Erik | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-23 10:30 UTC | Sjors Marckelbach | Qualification Call Freedom Academy (TF) | Won |
| 2026-04-23 09:30 UTC | Nagasaki Elena | Qualification Call Freedom Academy (TF) | Won |
| 2026-04-23 09:00 UTC | Carolien Janzen | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-23 07:30 UTC | Jan Simoens | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-23 07:00 UTC | Dennis Schouten | Qualification Call Freedom Academy (TF) | Won |
| 2026-04-22 17:30 UTC | Balint Matys | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-22 14:30 UTC | Chris Van As | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-22 10:00 UTC | Rigo Nagels | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-22 08:00 UTC | olivier wijnen | Qualification Call Didi Bam Bam | No Sale - Follow Up |
| 2026-04-22 07:00 UTC | Chanida | Strategy Call - Freedom - (FU) | No Sale - Follow Up |
| 2026-04-21 19:00 UTC | Matt A A | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |

**Execution time:** 63.994 sec
**Status:** ok

## 22. AAQ-011

**Question**

List appointments scheduled from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
ORDER BY a.schedule_time ASC, a.id ASC
LIMIT 20
```

**Generated final answer**

Total matching appointments: 218

Showing the first 20 appointments (times in UTC):

| Scheduled time (UTC) | Lead | Event | Outcome | No-show | Source | Fathom record |
|---|---|---|---|---|---|---|
| 2026-04-01 07:00 | Levy | Qualification Call Freedom Academy (DMB) | No Sale - Lost | No | Calendly | No |
| 2026-04-01 13:00 | Gordon Keller | Qualification Call Freedom Academy (DMB) | Won | No | Calendly | No |
| 2026-04-01 14:00 | Marc Van schendel | Strategy Call - Freedom - (FU) | Won | No | Calendly | No |
| 2026-04-01 18:00 | Rutger Vogelezang | Qualification Call Freedom Academy (DMB) | Won | No | Calendly | No |
| 2026-04-02 09:00 | Mike V | Qualification Call Freedom Academy (TF) | No Sale - Follow Up | No | Calendly | No |
| 2026-04-02 12:00 | Ryan Pryde | Qualification Call Freedom Academy (TF) | No Sale - Lost | No | Calendly | Yes |
| 2026-04-02 14:00 | Mitchel Nijholt | Qualification Call Freedom Academy (DMB) | Canceled | No | Calendly | No |
| 2026-04-03 07:00 | Sylvia Georgiev Georgiev | Qualification Call Freedom Academy (DMB) | Won | No | Calendly | No |
| 2026-04-03 08:00 | Patrick Koldijk | Qualification Call Freedom Academy (TF) | Won | No | Calendly | No |
| 2026-04-03 11:00 | Lets first check | Qualification Call Freedom Academy (TF) | Canceled | No | Calendly | No |
| 2026-04-03 11:00 | Rivelino Sharbini Sharbini | Qualification Call Freedom Academy (TF) | Canceled | No | Calendly | No |
| 2026-04-03 11:00 | abel | Qualification Call Freedom Academy (DMB) | Canceled | No | Calendly | No |
| 2026-04-03 13:30 | Michiel | Strategy Call - Freedom - FU | No Sale - Follow Up | No | Calendly | No |
| 2026-04-03 13:30 | Michiel | Qualification Call Freedom Academy (TF) | Rescheduled | No | Calendly | No |
| 2026-04-03 14:30 | Tananwut Nantasoon | Qualification Call Freedom Academy (TF) | No Show | Yes | Calendly | No |
| 2026-04-03 15:30 | Marlow Warrington-Mattei | Qualification Call Freedom Academy (DMB) | No Sale - Follow Up | No | Calendly | No |
| 2026-04-03 18:30 | Martin | Qualification Call Freedom Academy (DMB) | Canceled | No | Calendly | No |
| 2026-04-04 06:00 | Lucas Johannes Fransen | Qualification Call Freedom Academy (TF) | Won | No | Calendly | No |
| 2026-04-04 07:00 | Jurre Stip | Qualification Call Freedom Academy (DMB) | No Sale - Lost | No | Calendly | No |
| 2026-04-04 08:00 | Vedran | Qualification Call Freedom Academy (TF) | No Sale - Follow Up | No | Calendly | Yes |

**Execution time:** 110.220 sec
**Status:** ok

## 23. AAQ-023

**Question**

Which event type has the highest no-show rate?

**Generated SQL**

```sql
WITH event_type_no_shows AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0) AS no_show_rate_percent_exact
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
  GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
),
ranked_event_types AS (
  SELECT
    event_name,
    total_past_appointments,
    no_show_appointments,
    ROUND(no_show_rate_percent_exact, 2) AS no_show_rate_percent,
    DENSE_RANK() OVER (ORDER BY no_show_rate_percent_exact DESC) AS no_show_rate_rank,
    SUM(total_past_appointments) OVER () AS total_matching_past_appointments
  FROM event_type_no_shows
)
SELECT
  event_name,
  total_past_appointments,
  no_show_appointments,
  no_show_rate_percent,
  total_matching_past_appointments
FROM ranked_event_types
WHERE no_show_rate_rank = 1
ORDER BY total_past_appointments DESC, event_name ASC;
```

**Generated final answer**

Across 450 past appointments, the event type with the highest no-show rate is `Unknown`: 1 no-show out of 1 past appointment (100.00%).

**Execution time:** 33.890 sec
**Status:** ok

## 24. AAQ-027

**Question**

Which setter has the highest appointment no-show rate?

**Generated SQL**

```sql
WITH setter_no_show_rates AS (
  SELECT
    NULLIF(TRIM(a.setter_id), '') AS setter_id,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true)::numeric / NULLIF(COUNT(*), 0) AS no_show_rate_percent_exact
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND NULLIF(TRIM(a.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.setter_id), '')
), ranked_setters AS (
  SELECT
    setter_id,
    total_past_appointments,
    no_show_appointments,
    ROUND(no_show_rate_percent_exact, 2) AS no_show_rate_percent,
    SUM(total_past_appointments) OVER () AS total_matching_past_appointments,
    DENSE_RANK() OVER (ORDER BY no_show_rate_percent_exact DESC) AS no_show_rate_rank
  FROM setter_no_show_rates
)
SELECT
  setter_id,
  total_past_appointments,
  no_show_appointments,
  no_show_rate_percent,
  total_matching_past_appointments
FROM ranked_setters
WHERE no_show_rate_rank = 1
ORDER BY total_past_appointments DESC, setter_id ASC;
```

**Generated final answer**

Based on past appointments with an assigned setter, setter ID `user_3AesMObeGeZynVoGhloMkfwanES` has the highest appointment no-show rate at 4.40% (4 no-shows out of 91 past appointments).

**Execution time:** 34.515 sec
**Status:** ok

## 25. AAQ-028

**Question**

Show no-show rate by event type from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent,
  SUM(COUNT(*)) OVER() AS total_matching_past_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total_past_appointments
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY no_show_rate_percent DESC NULLS LAST, total_past_appointments DESC, event_name ASC;
```

**Generated final answer**

Total past appointments: 218

Here is the no-show rate by event type for 2026-04-01 to 2026-05-01:

| Event Type | Past Appointments | No-Shows | No-Show Rate | % of Total Past Appointments |
|---|---:|---:|---:|---:|
| Qualification Call Freedom Academy (TF) | 178 | 22 | 12.36% | 81.65% |
| Qualification Call Freedom Academy (DMB) | 15 | 1 | 6.67% | 6.88% |
| Strategy Call - Freedom - (FU) | 15 | 1 | 6.67% | 6.88% |
| Qualification Call Didi Bam Bam | 4 | 0 | 0.00% | 1.83% |
| Strategy Call - Freedom - FU | 4 | 0 | 0.00% | 1.83% |
| Strategy Call - Freedom (TFT) | 2 | 0 | 0.00% | 0.92% |

**Execution time:** 25.693 sec
**Status:** ok

## 26. AAQ-026

**Question**

Which host has the highest appointment no-show rate?

**Generated SQL**

```sql
WITH host_rates AS (
  SELECT
    NULLIF(TRIM(a.host_id), '') AS host_id,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true)::numeric / NULLIF(COUNT(*), 0) AS no_show_rate
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND NULLIF(TRIM(a.host_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.host_id), '')
),
overall_totals AS (
  SELECT COALESCE(SUM(total_past_appointments), 0) AS total_matching_past_appointments
  FROM host_rates
),
max_rate AS (
  SELECT MAX(no_show_rate) AS max_no_show_rate
  FROM host_rates
)
SELECT
  hr.host_id,
  hr.total_past_appointments,
  hr.no_show_appointments,
  ROUND(hr.no_show_rate * 100, 2) AS no_show_rate_percent,
  ot.total_matching_past_appointments
FROM host_rates hr
CROSS JOIN overall_totals ot
JOIN max_rate mr
  ON hr.no_show_rate = mr.max_no_show_rate
ORDER BY hr.total_past_appointments DESC, hr.host_id ASC;
```

**Generated final answer**

Across 450 past appointments with an assigned host, `user_3ATRxXyN4j8bDHYJKRCEMAerasy` has the highest appointment no-show rate at 14.21% (28 no-shows out of 197 past appointments).

**Execution time:** 40.238 sec
**Status:** ok

## 27. AAQ-024

**Question**

Which call category has the highest no-show rate?

**Generated SQL**

```sql
WITH category_rates AS (
  SELECT
    CAST(a.snapshot_call_category AS text) AS call_category,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0) AS no_show_rate_percent_raw
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.snapshot_call_category IS NOT NULL
  GROUP BY CAST(a.snapshot_call_category AS text)
),
ranked AS (
  SELECT
    call_category,
    total_past_appointments,
    no_show_appointments,
    ROUND(no_show_rate_percent_raw, 2) AS no_show_rate_percent,
    SUM(total_past_appointments) OVER () AS total_matching_past_appointments,
    DENSE_RANK() OVER (ORDER BY no_show_rate_percent_raw DESC NULLS LAST) AS no_show_rate_rank
  FROM category_rates
)
SELECT
  call_category,
  total_past_appointments,
  no_show_appointments,
  no_show_rate_percent,
  total_matching_past_appointments
FROM ranked
WHERE no_show_rate_rank = 1
ORDER BY total_past_appointments DESC, call_category ASC;
```

**Generated final answer**

Among past appointments with a recorded call category, Sales Call has the highest no-show rate at 12.00% (54 no-shows out of 450 appointments).

**Execution time:** 52.735 sec
**Status:** ok

## 28. AAQ-025

**Question**

Which appointment source has the highest no-show rate?

**Generated SQL**

```sql
WITH source_rates AS (
  SELECT
    CAST(a.source AS text) AS appointment_source,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
      2
    ) AS no_show_rate_percent,
    SUM(COUNT(*)) OVER() AS total_matching_past_appointments
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.source IS NOT NULL
  GROUP BY CAST(a.source AS text)
),
ranked_sources AS (
  SELECT
    sr.appointment_source,
    sr.total_past_appointments,
    sr.no_show_appointments,
    sr.no_show_rate_percent,
    sr.total_matching_past_appointments,
    DENSE_RANK() OVER (
      ORDER BY sr.no_show_rate_percent DESC NULLS LAST
    ) AS no_show_rate_rank
  FROM source_rates sr
)
SELECT
  appointment_source,
  total_past_appointments,
  no_show_appointments,
  no_show_rate_percent,
  total_matching_past_appointments
FROM ranked_sources
WHERE no_show_rate_rank = 1
ORDER BY total_past_appointments DESC, appointment_source ASC;
```

**Generated final answer**

Among past appointments with a recorded source, Calendly has the highest no-show rate at 12.00% (54 no-shows out of 450 appointments).

**Execution time:** 61.638 sec
**Status:** ok

## 29. AAQ-030

**Question**

Show no-show rate by setter from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent,
  SUM(COUNT(*)) OVER() AS total_matching_past_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total_past_appointments
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
GROUP BY COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter')
ORDER BY no_show_rate_percent DESC NULLS LAST, total_past_appointments DESC, setter_id ASC
```

**Generated final answer**

Total past appointments in range: 218

Here is the no-show rate by setter ID:

| Setter ID | Past appointments | No-shows | No-show rate | % of total appointments |
|---|---:|---:|---:|---:|
| No Setter | 171 | 22 | 12.87% | 78.44% |
| user_3AesMObeGeZynVoGhloMkfwanES | 47 | 2 | 4.26% | 21.56% |

**Execution time:** 26.721 sec
**Status:** ok

## 30. AAQ-029

**Question**

Show no-show rate by host from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent,
  SUM(COUNT(*)) OVER() AS total_matching_past_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total_past_appointments
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
GROUP BY COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host')
ORDER BY no_show_rate_percent DESC NULLS LAST, total_past_appointments DESC, host_id ASC;
```

**Generated final answer**

Total past appointments in this period: 218

Here is the no-show rate by host for 2026-04-01 to 2026-05-01:

| Host ID | Past appointments | No-shows | No-show rate | % of period appointments |
|---|---:|---:|---:|---:|
| `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | 89 | 10 | 11.24% | 40.83% |
| `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | 129 | 14 | 10.85% | 59.17% |

**Execution time:** 33.651 sec
**Status:** ok

## 31. AAQ-033

**Question**

What is the appointment outcome breakdown?

**Generated SQL**

```sql
SELECT
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY
  COALESCE(outcome.name, 'No Outcome'),
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME')
ORDER BY appointment_count DESC, outcome_name ASC;
```

**Generated final answer**

Total appointments: 451

Here is the breakdown:

| Outcome | Appointments | % of total |
|---|---:|---:|
| Won | 128 | 28.38% |
| Canceled | 78 | 17.29% |
| No Sale - Follow Up | 76 | 16.85% |
| No Show | 49 | 10.86% |
| No Sale - Lost | 41 | 9.09% |
| Call Booked | 40 | 8.87% |
| Rescheduled | 26 | 5.76% |
| No Sale - Unqualified | 11 | 2.44% |
| Deposit | 2 | 0.44% |

**Execution time:** 21.293 sec
**Status:** ok

## 32. AAQ-034

**Question**

Show appointment outcome breakdown from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
GROUP BY
  COALESCE(outcome.name, 'No Outcome'),
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME')
ORDER BY appointment_count DESC, outcome_name ASC;
```

**Generated final answer**

Total matching appointments: 218

Here is the outcome breakdown for 2026-04-01 to 2026-05-01:

| Outcome | Count | % of total |
|---|---:|---:|
| Won | 52 | 23.85% |
| No Sale - Follow Up | 42 | 19.27% |
| Canceled | 38 | 17.43% |
| Call Booked | 33 | 15.14% |
| No Show | 22 | 10.09% |
| Rescheduled | 18 | 8.26% |
| No Sale - Lost | 12 | 5.50% |
| No Sale - Unqualified | 1 | 0.46% |

**Execution time:** 23.033 sec
**Status:** ok

## 33. AAQ-035

**Question**

What is the appointment breakdown by call category?

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN') AS call_category,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN')
ORDER BY appointment_count DESC, call_category ASC;
```

**Generated final answer**

Total matching appointments: 451

Here is the breakdown:

| Call category | Appointments | % of total |
|---|---:|---:|
| Sales Call | 451 | 100.00% |

**Execution time:** 17.790 sec
**Status:** ok

## 34. AAQ-036

**Question**

What is the appointment source breakdown?

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(a.source AS text), 'UNKNOWN') AS appointment_source,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(CAST(a.source AS text), 'UNKNOWN')
ORDER BY appointment_count DESC, appointment_source ASC;
```

**Generated final answer**

Total matching appointments: 451

All 451 appointments were sourced via Calendly, representing 100.00% of the total.

**Execution time:** 17.299 sec
**Status:** ok

## 35. AAQ-032

**Question**

List recent no-show appointments.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND a.no_show = true
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT :limit;
```

**Generated final answer**

Total matching appointments: 54

Showing the first 20 appointments, most recent first:

| Scheduled time (UTC) | Lead | Event | Outcome label |
|---|---|---|---|
| 2026-04-23 19:00 | Andres M | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-23 08:30 | Anthony Muone Muoneke | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-23 06:00 | Viliami Tuipulotu | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-22 14:00 | Ivan Gavel | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-21 16:00 | Gabe Real | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-20 17:00 | Katia Gemis | Qualification Call Freedom Academy (TF) | Rescheduled |
| 2026-04-20 14:30 | joseph | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-20 14:00 | Grace Kelly | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-20 07:00 | Ankush | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-19 06:00 | Javi Meijer | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-17 17:00 | Mohammad Tahir | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-17 13:00 | Alrun Ray Tokaay | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-16 08:30 | Matthews Mokgosi | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-15 10:00 | Olivier Sagata | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-13 18:30 | Rakesh More | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-13 13:00 | Sam monte | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-13 12:00 | David Chung | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-08 19:00 | Brahim Orchi | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-08 10:00 | Johan Martens Martens | Qualification Call Freedom Academy (DMB) | No Sale - Lost |
| 2026-04-08 09:00 | EDGAR Adriano PEREIRA | Qualification Call Freedom Academy (TF) | No Show |

**Execution time:** 60.713 sec
**Status:** ok

## 36. AAQ-038

**Question**

Show call category breakdown from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN') AS call_category,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
GROUP BY COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN')
ORDER BY appointment_count DESC, call_category ASC;
```

**Generated final answer**

Total matching appointments: 218

From 2026-04-01 to 2026-05-01, all appointments were Sales Call (218, 100.00%).

**Execution time:** 20.274 sec
**Status:** ok

## 37. AAQ-039

**Question**

Show appointment source breakdown from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(a.source AS text), 'UNKNOWN') AS appointment_source,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
GROUP BY COALESCE(CAST(a.source AS text), 'UNKNOWN')
ORDER BY appointment_count DESC, appointment_source ASC;
```

**Generated final answer**

Total matching appointments: 218

Here is the breakdown:

| Appointment Source | Count | % of total |
|---|---:|---:|
| Calendly | 218 | 100.00% |

**Execution time:** 18.324 sec
**Status:** ok

## 38. AAQ-037

**Question**

What is the appointment breakdown by event type?

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY appointment_count DESC, event_name ASC;
```

**Generated final answer**

Total appointments: 451

Here is the breakdown by event type:

| Event Type | Appointments | % of total |
|---|---:|---:|
| Qualification Call Freedom Academy (TF) | 255 | 56.54% |
| Qualification Call Freedom Academy (DMB) | 71 | 15.74% |
| Strategy Call - Freedom | 40 | 8.87% |
| Strategy Call - Freedom - (FU) | 26 | 5.76% |
| Strategy Call - Freedom - FU | 25 | 5.54% |
| Strategy Call - Freedom (TFT) | 22 | 4.88% |
| Qualification Call Freedom Academy (DML) | 6 | 1.33% |
| Qualification Call Didi Bam Bam | 4 | 0.89% |
| Qualification Call Freedom Academy (DM) | 1 | 0.22% |
| Unknown | 1 | 0.22% |

**Execution time:** 32.514 sec
**Status:** ok

## 39. AAQ-040

**Question**

Show event type breakdown from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY appointment_count DESC, event_name ASC
```

**Generated final answer**

Total matching appointments: 218

Here is the event type breakdown:

| Event type | Appointments | % of total |
|---|---:|---:|
| Qualification Call Freedom Academy (TF) | 178 | 81.65% |
| Qualification Call Freedom Academy (DMB) | 15 | 6.88% |
| Strategy Call - Freedom - (FU) | 15 | 6.88% |
| Qualification Call Didi Bam Bam | 4 | 1.83% |
| Strategy Call - Freedom - FU | 4 | 1.83% |
| Strategy Call - Freedom (TFT) | 2 | 0.92% |

**Execution time:** 20.987 sec
**Status:** ok

## 40. AAQ-041

**Question**

Which appointment outcome is most common?

**Generated SQL**

```sql
WITH outcome_counts AS (
  SELECT
    COALESCE(outcome.name, 'No Outcome') AS outcome_name,
    COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
    COUNT(*) AS appointment_count,
    SUM(COUNT(*)) OVER() AS total_matching_appointments,
    ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
  FROM appointments a
  LEFT JOIN sales_statuses outcome
    ON outcome.id = a.outcome_id
   AND outcome.clerk_org_id = a.clerk_org_id
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
  GROUP BY
    COALESCE(outcome.name, 'No Outcome'),
    COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME')
), max_count AS (
  SELECT MAX(appointment_count) AS max_appointment_count
  FROM outcome_counts
)
SELECT
  oc.outcome_name,
  oc.outcome_role,
  oc.appointment_count,
  oc.total_matching_appointments,
  oc.percentage_of_total
FROM outcome_counts oc
JOIN max_count mc
  ON oc.appointment_count = mc.max_appointment_count
ORDER BY oc.outcome_name ASC;
```

**Generated final answer**

The most common appointment outcome is Won: 128 of 451 appointments (28.38%).

**Execution time:** 18.850 sec
**Status:** ok

## 41. AAQ-031

**Question**

List no-show appointments scheduled from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  ) AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
  AND a.no_show = true
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT :limit
```

**Generated final answer**

Total matching records: 24

Showing the first 20 no-show appointments scheduled from Apr 1 to May 1, 2026:

| Scheduled time (UTC) | Lead | Event | Recorded outcome |
|---|---|---|---|
| 2026-04-23 19:00 | Andres M | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-23 08:30 | Anthony Muone Muoneke | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-23 06:00 | Viliami Tuipulotu | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-22 14:00 | Ivan Gavel | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-21 16:00 | Gabe Real | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-20 17:00 | Katia Gemis | Qualification Call Freedom Academy (TF) | Rescheduled |
| 2026-04-20 14:30 | joseph | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-20 14:00 | Grace Kelly | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-20 07:00 | Ankush | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-19 06:00 | Javi Meijer | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-17 17:00 | Mohammad Tahir | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-17 13:00 | Alrun Ray Tokaay | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-16 08:30 | Matthews Mokgosi | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-15 10:00 | Olivier Sagata | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-13 18:30 | Rakesh More | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-13 13:00 | Sam monte | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-13 12:00 | David Chung | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-08 19:00 | Brahim Orchi | Qualification Call Freedom Academy (TF) | No Show |
| 2026-04-08 10:00 | Johan Martens Martens | Qualification Call Freedom Academy (DMB) | No Sale - Lost |
| 2026-04-08 09:00 | EDGAR Adriano PEREIRA | Qualification Call Freedom Academy (TF) | No Show |

**Execution time:** 85.599 sec
**Status:** ok

## 42. AAQ-042

**Question**

Which call category has the most appointments?

**Generated SQL**

```sql
WITH category_counts AS (
  SELECT
    COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN') AS call_category,
    COUNT(*) AS appointment_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
  GROUP BY COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN')
), totals AS (
  SELECT
    SUM(appointment_count) AS total_matching_appointments,
    MAX(appointment_count) AS max_appointment_count
  FROM category_counts
)
SELECT
  cc.call_category,
  cc.appointment_count,
  t.total_matching_appointments,
  ROUND(cc.appointment_count * 100.0 / NULLIF(t.total_matching_appointments, 0), 2) AS percentage_of_total
FROM category_counts cc
CROSS JOIN totals t
WHERE cc.appointment_count = t.max_appointment_count
ORDER BY cc.call_category ASC;
```

**Generated final answer**

The call category with the most appointments is Sales Call, with 451 appointments (100.00% of all 451 appointments).

**Execution time:** 22.365 sec
**Status:** ok

## 43. AAQ-046

**Question**

Show appointments by host.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host')
ORDER BY appointment_count DESC, host_id ASC;
```

**Generated final answer**

Total matching appointments: 451

Here is the breakdown by host ID:

| Host ID | Appointments | % of total |
|---|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 252 | 55.88% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 198 | 43.90% |
| user_3ARuEgINlhhlbVsZYBbgBDeOEjr | 1 | 0.22% |

**Execution time:** 15.251 sec
**Status:** ok

## 44. AAQ-043

**Question**

Which appointment source has the most bookings?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(CAST(a.source AS text), 'UNKNOWN') AS appointment_source,
    COUNT(*) AS appointment_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
  GROUP BY COALESCE(CAST(a.source AS text), 'UNKNOWN')
),
max_count AS (
  SELECT MAX(appointment_count) AS max_appointment_count
  FROM source_counts
),
totals AS (
  SELECT SUM(appointment_count) AS total_matching_appointments
  FROM source_counts
)
SELECT
  sc.appointment_source,
  sc.appointment_count,
  t.total_matching_appointments,
  ROUND(sc.appointment_count * 100.0 / NULLIF(t.total_matching_appointments, 0), 2) AS percentage_of_total
FROM source_counts sc
JOIN max_count mc
  ON sc.appointment_count = mc.max_appointment_count
CROSS JOIN totals t
ORDER BY sc.appointment_source ASC;
```

**Generated final answer**

Calendly has the most bookings with 451 appointments, accounting for 100.00% of all bookings.

**Execution time:** 25.741 sec
**Status:** ok

## 45. AAQ-044

**Question**

Which event type has the most appointments?

**Generated SQL**

```sql
WITH event_counts AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS appointment_count
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
  GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
), ranked AS (
  SELECT
    event_name,
    appointment_count,
    SUM(appointment_count) OVER() AS total_matching_appointments,
    ROUND(appointment_count * 100.0 / NULLIF(SUM(appointment_count) OVER(), 0), 2) AS percentage_of_total,
    MAX(appointment_count) OVER() AS max_appointment_count
  FROM event_counts
)
SELECT
  event_name,
  appointment_count,
  total_matching_appointments,
  percentage_of_total
FROM ranked
WHERE appointment_count = max_appointment_count
ORDER BY event_name ASC;
```

**Generated final answer**

The event type with the most appointments is **Qualification Call Freedom Academy (TF)**, with **255** of **451** total appointments (**56.54%**).

**Execution time:** 20.037 sec
**Status:** ok

## 46. AAQ-045

**Question**

Which host has the most appointments?

**Generated SQL**

```sql
WITH host_counts AS (
  SELECT
    NULLIF(TRIM(a.host_id), '') AS host_id,
    COUNT(*) AS appointment_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND NULLIF(TRIM(a.host_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.host_id), '')
),
max_count AS (
  SELECT MAX(appointment_count) AS max_appointment_count
  FROM host_counts
)
SELECT
  hc.host_id,
  hc.appointment_count
FROM host_counts hc
JOIN max_count mc
  ON hc.appointment_count = mc.max_appointment_count
ORDER BY hc.host_id ASC;
```

**Generated final answer**

The host with the most appointments is host ID `user_3AZPWYViL4vUfqNXmNLhNcYAwX4`, with 252 appointments.

**Execution time:** 20.513 sec
**Status:** ok

## 47. AAQ-047

**Question**

Show appointments by host from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
GROUP BY COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host')
ORDER BY appointment_count DESC, host_id ASC;
```

**Generated final answer**

Total matching appointments: 218

Here is the breakdown for 2026-04-01 to 2026-05-01:

| Host ID | Appointments | % of total |
|---|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 129 | 59.17% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 89 | 40.83% |

**Execution time:** 19.093 sec
**Status:** ok

## 48. AAQ-049

**Question**

Which host has the most no-show appointments?

**Generated SQL**

```sql
WITH host_no_shows AS (
  SELECT
    NULLIF(TRIM(a.host_id), '') AS host_id,
    COUNT(*) AS no_show_appointment_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.no_show = true
    AND NULLIF(TRIM(a.host_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.host_id), '')
),
max_count AS (
  SELECT MAX(no_show_appointment_count) AS max_no_show_appointment_count
  FROM host_no_shows
)
SELECT
  hns.host_id,
  hns.no_show_appointment_count
FROM host_no_shows hns
JOIN max_count mc
  ON hns.no_show_appointment_count = mc.max_no_show_appointment_count
ORDER BY hns.host_id ASC;
```

**Generated final answer**

The host with the most no-show appointments is `user_3ATRxXyN4j8bDHYJKRCEMAerasy`, with 28 past no-show appointments.

**Execution time:** 16.274 sec
**Status:** ok

## 49. AAQ-048

**Question**

Which host completed the most attended calls?

**Generated SQL**

```sql
WITH host_counts AS (
  SELECT
    NULLIF(TRIM(a.host_id), '') AS host_id,
    COUNT(*) AS completed_attended_calls
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.no_show = false
    AND NULLIF(TRIM(a.host_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.host_id), '')
),
max_count AS (
  SELECT MAX(completed_attended_calls) AS max_completed_attended_calls
  FROM host_counts
)
SELECT
  hc.host_id,
  hc.completed_attended_calls
FROM host_counts hc
JOIN max_count mc
  ON hc.completed_attended_calls = mc.max_completed_attended_calls
ORDER BY hc.host_id ASC;
```

**Generated final answer**

The host with the most completed attended calls is `user_3AZPWYViL4vUfqNXmNLhNcYAwX4`, with 226 calls.

**Execution time:** 25.491 sec
**Status:** ok

## 50. AAQ-050

**Question**

Show attended call count and no-show count by host.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COUNT(*) FILTER (WHERE a.no_show = false) AS attended_call_count,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_count,
  COUNT(*) AS total_past_appointments,
  SUM(COUNT(*)) OVER() AS total_matching_past_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
GROUP BY COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host')
ORDER BY attended_call_count DESC, no_show_count DESC, host_id ASC;
```

**Generated final answer**

Total past appointments: 450

Here is the breakdown by host for past scheduled calls:

| Host ID | Attended calls | No-shows | Total past appointments | No-show rate |
|---|---:|---:|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 226 | 26 | 252 | 10.32% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 169 | 28 | 197 | 14.21% |
| user_3ARuEgINlhhlbVsZYBbgBDeOEjr | 1 | 0 | 1 | 0.00% |

**Execution time:** 24.704 sec
**Status:** ok

## 51. AAQ-051

**Question**

Which setter booked the most appointments?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(a.setter_id), '') AS setter_id,
    COUNT(*) AS appointment_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND NULLIF(TRIM(a.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.setter_id), '')
),
max_count AS (
  SELECT
    MAX(appointment_count) AS max_appointment_count,
    SUM(appointment_count) AS total_matching_appointments
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.appointment_count,
  mc.total_matching_appointments,
  ROUND(sc.appointment_count * 100.0 / NULLIF(mc.total_matching_appointments, 0), 2) AS percentage_of_total
FROM setter_counts sc
JOIN max_count mc
  ON sc.appointment_count = mc.max_appointment_count
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

The setter with the most booked appointments is `user_3AesMObeGeZynVoGhloMkfwanES`, with 92 of the 93 appointments that have a setter assigned (98.92%).

**Execution time:** 24.512 sec
**Status:** ok

## 52. AAQ-052

**Question**

Show appointments by setter.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter')
ORDER BY appointment_count DESC, setter_id ASC;
```

**Generated final answer**

Total matching appointments: 451

Most appointments are currently recorded without a setter.

| Setter ID | Appointments | % of total |
|---|---:|---:|
| No Setter | 358 | 79.38% |
| user_3AesMObeGeZynVoGhloMkfwanES | 92 | 20.40% |
| user_3AZfvBICuFGTCNu4QeqiP6xN03Q | 1 | 0.22% |

**Execution time:** 19.864 sec
**Status:** ok

## 53. AAQ-053

**Question**

Show appointments by setter from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
GROUP BY COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter')
ORDER BY appointment_count DESC, setter_id ASC;
```

**Generated final answer**

Total matching appointments: 218

Here is the breakdown by setter for 2026-04-01 to 2026-05-01:

| Setter | Appointments | % of total |
|---|---:|---:|
| No Setter | 171 | 78.44% |
| user_3AesMObeGeZynVoGhloMkfwanES | 47 | 21.56% |

**Execution time:** 18.938 sec
**Status:** ok

## 54. AAQ-054

**Question**

Which setter booked the most attended calls?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(a.setter_id), '') AS setter_id,
    COUNT(*) AS attended_call_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.no_show = false
    AND NULLIF(TRIM(a.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.setter_id), '')
),
stats AS (
  SELECT
    MAX(attended_call_count) AS max_attended_call_count,
    SUM(attended_call_count) AS total_matching_attended_calls
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.attended_call_count,
  st.total_matching_attended_calls,
  ROUND(sc.attended_call_count * 100.0 / NULLIF(st.total_matching_attended_calls, 0), 2) AS percentage_of_total
FROM setter_counts sc
CROSS JOIN stats st
WHERE sc.attended_call_count = st.max_attended_call_count
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

Total attended calls with a recorded setter: 88

The setter ID with the most attended calls is `user_3AesMObeGeZynVoGhloMkfwanES`, with 87 attended calls (98.86% of the total).

**Execution time:** 25.051 sec
**Status:** ok

## 55. AAQ-056

**Question**

Show attended call count and no-show count by setter.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) FILTER (WHERE a.no_show = false) AS attended_call_count,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_count,
  COUNT(*) AS total_past_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent,
  SUM(COUNT(*)) OVER() AS total_matching_past_appointments
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
GROUP BY COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter')
ORDER BY total_past_appointments DESC, setter_id ASC;
```

**Generated final answer**

Total past appointments: 450

Here is the attended vs no-show breakdown by setter:

| Setter | Attended calls | No-shows | Total past appointments | No-show rate |
|---|---:|---:|---:|---:|
| No Setter | 308 | 50 | 358 | 13.97% |
| user_3AesMObeGeZynVoGhloMkfwanES | 87 | 4 | 91 | 4.40% |
| user_3AZfvBICuFGTCNu4QeqiP6xN03Q | 1 | 0 | 1 | 0.00% |

**Execution time:** 23.445 sec
**Status:** ok

## 56. AAQ-055

**Question**

Which setter has the most no-show appointments?

**Generated SQL**

```sql
WITH setter_no_show_counts AS (
  SELECT
    NULLIF(TRIM(a.setter_id), '') AS setter_id,
    COUNT(*) AS no_show_appointments
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.no_show = true
    AND NULLIF(TRIM(a.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.setter_id), '')
), totals AS (
  SELECT
    SUM(no_show_appointments) AS total_matching_no_show_appointments,
    MAX(no_show_appointments) AS max_no_show_appointments
  FROM setter_no_show_counts
)
SELECT
  snc.setter_id,
  snc.no_show_appointments,
  t.total_matching_no_show_appointments,
  ROUND(
    snc.no_show_appointments * 100.0 / NULLIF(t.total_matching_no_show_appointments, 0),
    2
  ) AS percentage_of_total_no_show_appointments
FROM setter_no_show_counts snc
CROSS JOIN totals t
WHERE snc.no_show_appointments = t.max_no_show_appointments
ORDER BY snc.setter_id ASC;
```

**Generated final answer**

Among past appointments with an assigned setter, `user_3AesMObeGeZynVoGhloMkfwanES` has the most no-show appointments with 4, representing 100.00% of setter-assigned no-shows.

**Execution time:** 28.839 sec
**Status:** ok

## 57. AAQ-058

**Question**

Which event type has the most attended calls?

**Generated SQL**

```sql
WITH attended_event_counts AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS attended_calls
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.no_show = false
  GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
),
max_count AS (
  SELECT MAX(attended_calls) AS max_attended_calls
  FROM attended_event_counts
),
totals AS (
  SELECT SUM(attended_calls) AS total_matching_attended_calls
  FROM attended_event_counts
)
SELECT
  aec.event_name,
  aec.attended_calls,
  t.total_matching_attended_calls,
  ROUND(aec.attended_calls * 100.0 / NULLIF(t.total_matching_attended_calls, 0), 2) AS percentage_of_total_attended_calls
FROM attended_event_counts aec
JOIN max_count mc
  ON aec.attended_calls = mc.max_attended_calls
CROSS JOIN totals t
ORDER BY aec.event_name ASC;
```

**Generated final answer**

Qualification Call Freedom Academy (TF) has the most attended calls, with 221 out of 396 total attended calls (55.81%).

**Execution time:** 22.116 sec
**Status:** ok

## 58. AAQ-061

**Question**

How many event types are ignored?

**Generated SQL**

```sql
SELECT COUNT(*) AS ignored_event_type_count
FROM appointment_event_types aet
WHERE aet.clerk_org_id = :org_id
  AND aet.is_deleted = false
  AND aet.is_ignored = true;
```

**Generated final answer**

There is 1 ignored event type.

**Execution time:** 9.827 sec
**Status:** ok

## 59. AAQ-057

**Question**

Show event type performance with appointments, no-shows, and no-show rate.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
    2
  ) AS no_show_rate_percent,
  SUM(COUNT(*)) OVER() AS total_matching_past_appointments
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY total_past_appointments DESC, no_show_rate_percent DESC NULLS LAST, event_name ASC;
```

**Generated final answer**

Total past appointments: 450

Here is the event type performance based on past appointments:

| Event type | Appointments | No-shows | No-show rate |
|---|---:|---:|---:|
| Qualification Call Freedom Academy (TF) | 254 | 33 | 12.99% |
| Qualification Call Freedom Academy (DMB) | 71 | 3 | 4.23% |
| Strategy Call - Freedom | 40 | 12 | 30.00% |
| Strategy Call - Freedom - (FU) | 26 | 1 | 3.85% |
| Strategy Call - Freedom - FU | 25 | 1 | 4.00% |
| Strategy Call - Freedom (TFT) | 22 | 3 | 13.64% |
| Qualification Call Freedom Academy (DML) | 6 | 0 | 0.00% |
| Qualification Call Didi Bam Bam | 4 | 0 | 0.00% |
| Unknown | 1 | 1 | 100.00% |
| Qualification Call Freedom Academy (DM) | 1 | 0 | 0.00% |

**Execution time:** 31.630 sec
**Status:** ok

## 60. AAQ-062

**Question**

How many event types are marked as favourite?

**Generated SQL**

```sql
SELECT COUNT(*) AS favourite_event_type_count
FROM appointment_event_types aet
WHERE aet.clerk_org_id = :org_id
  AND aet.is_deleted = false
  AND aet.is_favourite = true;
```

**Generated final answer**

There are 2 event types marked as favourite.

**Execution time:** 10.650 sec
**Status:** ok

## 61. AAQ-065

**Question**

How many past appointments are missing Fathom records?

**Generated SQL**

```sql
SELECT COUNT(*) AS past_appointments_missing_fathom_records
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND NOT EXISTS (
    SELECT 1
    FROM fathom_call_records f
    WHERE f.appointment_id = a.id
      AND f.clerk_org_id = a.clerk_org_id
  );
```

**Generated final answer**

There are 368 past appointments missing Fathom records.

**Execution time:** 11.272 sec
**Status:** ok

## 62. AAQ-063

**Question**

What is the Fathom coverage for past appointments?

**Generated SQL**

```sql
SELECT
  COUNT(DISTINCT a.id) AS total_past_appointments,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) AS appointments_with_fathom,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NULL) AS appointments_without_fathom,
  ROUND(
    100.0 * COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) / NULLIF(COUNT(DISTINCT a.id), 0),
    2
  ) AS fathom_coverage_percent
FROM appointments a
LEFT JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW();
```

**Generated final answer**

Out of 450 past appointments, 82 have Fathom records and 368 do not. Fathom coverage is 18.22%.

**Execution time:** 15.380 sec
**Status:** ok

## 63. AAQ-059

**Question**

Which event type has the most no-shows?

**Generated SQL**

```sql
WITH event_stats AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
      2
    ) AS no_show_rate_percent
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
  GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
),
max_count AS (
  SELECT MAX(no_show_appointments) AS max_no_show_appointments
  FROM event_stats
),
totals AS (
  SELECT COALESCE(SUM(no_show_appointments), 0) AS total_matching_no_show_appointments
  FROM event_stats
)
SELECT
  es.event_name,
  es.total_past_appointments,
  es.no_show_appointments,
  es.no_show_rate_percent,
  t.total_matching_no_show_appointments,
  ROUND(es.no_show_appointments * 100.0 / NULLIF(t.total_matching_no_show_appointments, 0), 2) AS percentage_of_total_no_shows
FROM event_stats es
JOIN max_count mc
  ON es.no_show_appointments = mc.max_no_show_appointments
CROSS JOIN totals t
WHERE es.no_show_appointments > 0
ORDER BY es.event_name ASC;
```

**Generated final answer**

Out of 54 past no-show appointments, **Qualification Call Freedom Academy (TF)** had the most no-shows with **33** (61.11% of all no-shows) and a **12.99%** no-show rate across **254** past appointments.

**Execution time:** 38.735 sec
**Status:** ok

## 64. AAQ-064

**Question**

What was the Fathom coverage for appointments scheduled from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  COUNT(DISTINCT a.id) AS total_past_appointments,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) AS appointments_with_fathom,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NULL) AS appointments_without_fathom,
  ROUND(
    100.0 * COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) / NULLIF(COUNT(DISTINCT a.id), 0),
    2
  ) AS fathom_coverage_percent
FROM appointments a
LEFT JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW();
```

**Generated final answer**

For appointments scheduled between 2026-04-01 and 2026-05-01, 74 of 218 had linked Fathom records and 144 did not, so Fathom coverage was 33.94%.

**Execution time:** 26.418 sec
**Status:** ok

## 65. AAQ-066

**Question**

How many appointments scheduled from 2026-04-01 to 2026-05-01 are missing Fathom records?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointments_missing_fathom_records
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND NOT EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  );
```

**Generated final answer**

There are 144 appointments scheduled from 2026-04-01 to 2026-05-01 that are missing Fathom records.

**Execution time:** 13.764 sec
**Status:** ok

## 66. AAQ-060

**Question**

Show current event type catalog by call category.

**Generated SQL**

```sql
WITH current_event_types AS (
  SELECT
    CASE CAST(aet.call_category AS text)
      WHEN 'SALES_CALL' THEN 'Sales Call'
      WHEN 'COACHING_CALL' THEN 'Coaching Call'
      WHEN 'TRIAGE_CALL' THEN 'Triage Call'
      ELSE 'No Call Category'
    END AS call_category,
    COALESCE(NULLIF(TRIM(aet.event_type_name), ''), 'Unnamed Event Type') AS event_type_name
  FROM appointment_event_types aet
  WHERE aet.clerk_org_id = :org_id
    AND aet.is_deleted = false
)
SELECT
  call_category,
  COUNT(*) AS event_type_count,
  STRING_AGG(event_type_name, ', ' ORDER BY event_type_name) AS event_types,
  SUM(COUNT(*)) OVER() AS total_matching_event_types
FROM current_event_types
GROUP BY call_category
ORDER BY
  CASE call_category
    WHEN 'Sales Call' THEN 1
    WHEN 'Coaching Call' THEN 2
    WHEN 'Triage Call' THEN 3
    WHEN 'No Call Category' THEN 4
    ELSE 5
  END,
  call_category ASC;
```

**Generated final answer**

Total current event types: 13

All current event types are currently categorized as Sales Call.

**Sales Call**
- 30 Minute Meeting
- 30 Minute Meeting
- 30 Minute Meeting
- Qualification Call Didi Bam Bam
- Qualification Call Freedom Academy (DM)
- Qualification Call Freedom Academy (DMB-short)
- Qualification Call Freedom Academy (DMB)
- Qualification Call Freedom Academy (DML)
- Qualification Call Freedom Academy (TF)
- Qualification Call The Bitcoin Family
- Strategy Call - Freedom - (FU)
- Strategy Call - Freedom - FU
- Strategy Call - Freedom (TFT)

**Execution time:** 70.036 sec
**Status:** ok

## 67. AAQ-069

**Question**

Show Fathom coverage by event type.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(DISTINCT a.id) AS total_past_appointments,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) AS appointments_with_fathom,
  COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NULL) AS appointments_without_fathom,
  ROUND(
    100.0 * COUNT(DISTINCT a.id) FILTER (WHERE f.id IS NOT NULL) / NULLIF(COUNT(DISTINCT a.id), 0),
    2
  ) AS fathom_coverage_percent,
  SUM(COUNT(DISTINCT a.id)) OVER() AS total_matching_past_appointments,
  ROUND(
    COUNT(DISTINCT a.id) * 100.0 / NULLIF(SUM(COUNT(DISTINCT a.id)) OVER(), 0),
    2
  ) AS percentage_of_total_past_appointments
FROM appointments a
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
LEFT JOIN fathom_call_records f
  ON f.appointment_id = a.id
 AND f.clerk_org_id = a.clerk_org_id
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY fathom_coverage_percent DESC NULLS LAST, total_past_appointments DESC, event_name ASC;
```

**Generated final answer**

Total past appointments: 450

Here is the Fathom coverage by event type for past appointments:

| Event type | Past appointments | With Fathom | Without Fathom | Coverage | % of past appointments |
|---|---:|---:|---:|---:|---:|
| Qualification Call Freedom Academy (TF) | 254 | 66 | 188 | 25.98% | 56.44% |
| Qualification Call Didi Bam Bam | 4 | 1 | 3 | 25.00% | 0.89% |
| Strategy Call - Freedom - (FU) | 26 | 6 | 20 | 23.08% | 5.78% |
| Qualification Call Freedom Academy (DMB) | 71 | 6 | 65 | 8.45% | 15.78% |
| Strategy Call - Freedom - FU | 25 | 2 | 23 | 8.00% | 5.56% |
| Strategy Call - Freedom (TFT) | 22 | 1 | 21 | 4.55% | 4.89% |
| Strategy Call - Freedom | 40 | 0 | 40 | 0.00% | 8.89% |
| Qualification Call Freedom Academy (DML) | 6 | 0 | 6 | 0.00% | 1.33% |
| Qualification Call Freedom Academy (DM) | 1 | 0 | 1 | 0.00% | 0.22% |
| Unknown | 1 | 0 | 1 | 0.00% | 0.22% |

**Execution time:** 30.295 sec
**Status:** ok

## 68. AAQ-070

**Question**

Show Fathom coverage by host.

**Generated SQL**

```sql
WITH appointment_fathom_flags AS (
  SELECT
    a.id AS appointment_id,
    COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
    EXISTS (
      SELECT 1
      FROM fathom_call_records f
      WHERE f.appointment_id = a.id
        AND f.clerk_org_id = a.clerk_org_id
    ) AS has_fathom_record
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
)
SELECT
  host_id,
  COUNT(*) AS total_past_appointments,
  COUNT(*) FILTER (WHERE has_fathom_record) AS appointments_with_fathom,
  COUNT(*) FILTER (WHERE NOT has_fathom_record) AS appointments_without_fathom,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE has_fathom_record) / NULLIF(COUNT(*), 0),
    2
  ) AS fathom_coverage_percent,
  SUM(COUNT(*)) OVER() AS total_matching_past_appointments
FROM appointment_fathom_flags
GROUP BY host_id
ORDER BY total_past_appointments DESC, host_id ASC;
```

**Generated final answer**

Total past appointments: 450

Here is the Fathom coverage by host:

| Host ID | Past Appointments | With Fathom | Without Fathom | Fathom Coverage |
|---|---:|---:|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 252 | 54 | 198 | 21.43% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 197 | 28 | 169 | 14.21% |
| user_3ARuEgINlhhlbVsZYBbgBDeOEjr | 1 | 0 | 1 | 0.00% |

**Execution time:** 38.126 sec
**Status:** ok

## 69. AAQ-071

**Question**

How many Fathom calls have summaries?

**Generated SQL**

```sql
SELECT COUNT(*) AS calls_with_summaries
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND NULLIF(TRIM(f.summary), '') IS NOT NULL;
```

**Generated final answer**

There are 81 Fathom calls with summaries.

**Execution time:** 14.243 sec
**Status:** ok

## 70. AAQ-067

**Question**

List appointments missing Fathom records.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  false AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND NOT EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  )
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20;
```

**Generated final answer**

Total past appointments missing Fathom records: 368

Showing the first 20, ordered by most recent scheduled time:

| Appointment ID | Scheduled time (UTC) | Lead | Event | Outcome | Source |
|---|---|---|---|---|---|
| 3ade1793-ba69-47e0-9ba1-27be6dd2f1e9 | 2026-05-05 13:00 | Ricardo Brandao | Strategy Call - Freedom - FU | Rescheduled | Calendly |
| 1015339c-c476-424a-9d7d-3c3c6916cd24 | 2026-05-01 08:00 | Wesley Helmers | Qualification Call Freedom Academy (DMB) | No Sale - Follow Up | Calendly |
| 855bb48d-d0f3-4507-a5d2-e8168cc38aab | 2026-04-30 16:00 | Stephen William Bennett | Qualification Call Didi Bam Bam | Rescheduled | Calendly |
| 9d9cbc9c-849f-48ad-aa6d-7d2e9426e242 | 2026-04-29 11:00 | Albert de Bruin | Qualification Call Freedom Academy (TF) | Rescheduled | Calendly |
| d805d4b6-32fd-4ed4-a59d-76224d49573d | 2026-04-29 08:00 | Andre Steenkamp | Qualification Call Freedom Academy (TF) | No Sale - Follow Up | Calendly |
| 9cd689c3-9eec-4881-9db9-554ab6b90e9a | 2026-04-28 15:00 | Robert Voorn | Strategy Call - Freedom - (FU) | Call Booked | Calendly |
| 63c52d25-6828-4bc1-adf7-d4cddc83bc39 | 2026-04-27 12:00 | Van der Veken Olivier | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| 64fcfad6-dd75-4e90-bbf6-239606afe477 | 2026-04-27 11:00 | Erik Bakker | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| c3c20a0f-8d8f-43f9-9ef2-8690900b8a73 | 2026-04-27 10:00 | Bahadir | Qualification Call Didi Bam Bam | Call Booked | Calendly |
| f303cd0a-2ecd-4a46-b094-444665c19f76 | 2026-04-27 06:00 | Steve Grainger | Qualification Call Didi Bam Bam | Call Booked | Calendly |
| 8ba8ab47-7e8a-4a05-9e85-07bd833f7156 | 2026-04-26 18:00 | Roos ‘t Lam | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| 3c46f3ca-64ee-4c8e-a0bb-29726819c99c | 2026-04-26 15:30 | Rob Schwarz | Qualification Call Freedom Academy (TF) | Canceled | Calendly |
| 776a904d-e8df-4406-ada7-7ec3759c4ad1 | 2026-04-26 11:00 | Rene Solms | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| 43dc2a30-2875-4649-95f9-e71f7df45bb8 | 2026-04-26 10:00 | Henry Stokkelaar | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| b47ac875-50da-46cd-92b4-330603f4eb59 | 2026-04-26 09:00 | Tom ter woord | Qualification Call Freedom Academy (TF) | Canceled | Calendly |
| 2b6d4fb6-60a4-436b-a3c9-eba720748a7b | 2026-04-26 07:00 | Nake Dragomirov | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| 52612ec3-1226-488b-894e-2145b2507c8f | 2026-04-26 06:00 | Aad Bouw | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| cf3f301d-f728-4483-bf04-0bae88df970b | 2026-04-26 06:00 | Kale green | Qualification Call Freedom Academy (TF) | Canceled | Calendly |
| 87e4a8c1-2f37-40f4-8822-b0a8a08ef1e8 | 2026-04-25 15:00 | Bryan Casica | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |
| 8e149174-dcf8-4255-892d-66d834e9c81f | 2026-04-25 14:00 | Eugenio Jedi Martinez | Qualification Call Freedom Academy (TF) | Call Booked | Calendly |

**Execution time:** 60.210 sec
**Status:** ok

## 71. AAQ-075

**Question**

How many Fathom calls have action items?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS calls_with_action_items
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.action_items IS NOT NULL
  AND f.action_items::text NOT IN ('null', '[]', '{}');
```

**Generated final answer**

There are 79 Fathom calls with action items.

**Execution time:** 13.669 sec
**Status:** ok

## 72. AAQ-076

**Question**

How many Fathom calls have objections?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS calls_with_objections
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.objections IS NOT NULL
  AND f.objections::text NOT IN ('null', '[]', '{}')
```

**Generated final answer**

There are 0 Fathom calls with objections.

**Execution time:** 17.959 sec
**Status:** ok

## 73. AAQ-068

**Question**

List appointments scheduled from 2026-04-01 to 2026-05-01 that are missing Fathom records.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  false AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time >= :start_date
  AND a.schedule_time < :end_date
  AND a.schedule_time < NOW()
  AND NOT EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  )
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20
```

**Generated final answer**

Total matching appointments: 144

Showing the first 20 appointments missing Fathom records in that window:

| Scheduled time (UTC) | Lead | Event | Outcome |
|---|---|---|---|
| 2026-04-30 16:00 | Stephen William Bennett | Qualification Call Didi Bam Bam | Rescheduled |
| 2026-04-29 11:00 | Albert de Bruin | Qualification Call Freedom Academy (TF) | Rescheduled |
| 2026-04-29 08:00 | Andre Steenkamp | Qualification Call Freedom Academy (TF) | No Sale - Follow Up |
| 2026-04-28 15:00 | Robert Voorn | Strategy Call - Freedom - (FU) | Call Booked |
| 2026-04-27 12:00 | Van der Veken Olivier | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-27 11:00 | Erik Bakker | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-27 10:00 | Bahadir | Qualification Call Didi Bam Bam | Call Booked |
| 2026-04-27 06:00 | Steve Grainger | Qualification Call Didi Bam Bam | Call Booked |
| 2026-04-26 18:00 | Roos ‘t Lam | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 15:30 | Rob Schwarz | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-26 11:00 | Rene Solms | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 10:00 | Henry Stokkelaar | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 09:00 | Tom ter woord | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-26 07:00 | Nake Dragomirov | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 06:00 | Aad Bouw | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-26 06:00 | Kale green | Qualification Call Freedom Academy (TF) | Canceled |
| 2026-04-25 15:00 | Bryan Casica | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-25 14:00 | Eugenio Jedi Martinez | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-25 13:00 | Sylvano van den Brink | Qualification Call Freedom Academy (TF) | Call Booked |
| 2026-04-25 12:00 | Constantin | Qualification Call Freedom Academy (TF) | Rescheduled |

**Execution time:** 94.393 sec
**Status:** ok

## 74. AAQ-078

**Question**

List Fathom calls with objections.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  f.objections,
  f.call_duration_seconds,
  f.call_started_at,
  f.call_ended_at
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.objections IS NOT NULL
  AND f.objections::text NOT IN ('null', '[]', '{}')
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 20;
```

**Generated final answer**

There are no Fathom calls with objections.

**Execution time:** 22.079 sec
**Status:** ok

## 75. AAQ-073

**Question**

List Fathom call summaries from calls started from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  f.call_started_at,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  f.summary
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.call_started_at >= :start_date
  AND f.call_started_at < :end_date
  AND NULLIF(TRIM(f.summary), '') IS NOT NULL
ORDER BY f.call_started_at DESC, f.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 75

Showing the first 20 call summaries:

| Started at (UTC) | Lead | Call title | Summary highlight |
|---|---|---|---|
| 2026-04-24 09:06 | Jeffrey Nussy | Onboarding Call - Jeffrey Joins Freedom Academy | Onboard Jeffrey to the Freedom Academy to achieve financial independence |
| 2026-04-24 09:03 | Robert Eduard | Onboarding Call - Rob's Freedom Academy Enrollment | Onboard Rob to the Freedom Academy crypto program |
| 2026-04-24 08:05 | Mario van Beek | Follow-Up Scheduled for Freedom Academy Enrollment | Explore the Freedom Academy program for Mario’s financial and emigration goals |
| 2026-04-24 07:11 | Erik van Hoof | Exploring Freedom Academy - Follow-Up Scheduled | Explore the Freedom Academy as a path to financial independence for Erik |
| 2026-04-23 18:05 | Raymond Keppel | Raymond Keppel - Freedom Academy Enrollment | Evaluate the Freedom Academy program for Raymond’s financial goals |
| 2026-04-23 12:00 | Chris Rouwhof | Onboarding Call - Chris Rouwhof Joins Freedom Academy | Onboard Chris Rouwhof to the Freedom Academy |
| 2026-04-23 10:17 | Sjors Marckelbach | Sale Closed - Sjors Joins Freedom Academy | Evaluate the Freedom Academy program for Sjors’s crypto investment goals |
| 2026-04-23 09:29 | Nagasaki Elena | Elena Joins Freedom Academy for Crypto Trading | Onboard Elena to the Freedom Academy to grow her crypto portfolio |
| 2026-04-23 09:03 | Carolien Janzen | Exploring Freedom Academy for Financial Independence | Explore how the Freedom Academy can help Ger & Caroline achieve financial independence |
| 2026-04-23 07:27 | Jan Simoens | Intro Call - Assessing Crypto Community Fit | Introductory call for the Freedom Academy crypto community |
| 2026-04-23 07:05 | Dennis Schouten | Sale - Dennis Joins Freedom Academy Program | Evaluate the Freedom Academy program for Dennis’s passive income goals |
| 2026-04-22 17:28 | Balint Matys | Exploring Freedom Academy for Passive Crypto Income | Explore the Freedom Academy for generating passive crypto income |
| 2026-04-22 14:57 | Chris Van As | Commitment to Freedom Academy - Payment Delayed | Explore Freedom Academy as a path to financial independence for a move to Thailand |
| 2026-04-22 11:00 | Erik | Qualification Call Freedom Academy (TF) | Explore Freedom Academy as a crypto investment solution for Albert |
| 2026-04-22 10:05 | Rigo Nagels | Qualification Call Freedom Academy (TF) | Evaluate the Freedom Academy for Rigo Nagels’ financial and emigration goals |
| 2026-04-22 10:05 | Rigo Nagels | Qualification Call Freedom Academy (TF) | Qualify Maurice Kroon for the Freedom Academy crypto program |
| 2026-04-22 07:59 | olivier wijnen | Qualification Call Didi Bam Bam | Explore Freedom Academy’s crypto passive income solution for Andre |
| 2026-04-22 07:00 | Chanida | Strategy Call - Freedom - (FU) | Clarify crypto bot strategy and finalize onboarding |
| 2026-04-21 19:05 | Matt A A | Follow-Up Scheduled - Freedom Academy Discussion | Explain the Freedom Academy’s crypto income generation model to Matt |
| 2026-04-21 17:29 | Dirk Terpstra | Exploring Investment Options - Follow-Up Needed | Explore how Freedom Academy can help Dirk invest and live off his new capital |

**Execution time:** 74.848 sec
**Status:** ok

## 76. AAQ-077

**Question**

List Fathom calls with action items.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  COALESCE(f.call_started_at, a.schedule_time, f.created_at) AS call_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  f.action_items
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.action_items IS NOT NULL
  AND f.action_items::text NOT IN ('null', '[]', '{}')
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 79

Showing the first 20 records:

| Call time | Lead | Call title | Action items |
|---|---|---|---|
| Apr 24, 2026 09:06 UTC | Jeffrey Nussy | Onboarding Call - Jeffrey Joins Freedom Academy | Complete onboarding: pay €5k via bank transfer; enter email in Beau's WhatsApp link; notify Beau; receive access; schedule bot setup w/ Justin.<br>Sell Audi; deploy proceeds to bot. |
| Apr 24, 2026 09:03 UTC | Robert Eduard | Onboarding Call - Rob's Freedom Academy Enrollment | WhatsApp Tom when BitMyMoney BTC sale clears; then pay €5k via link (card/bank).<br>WhatsApp Rob payment link when ready; then activate account and intro to Community Manager. |
| Apr 24, 2026 08:05 UTC | Mario van Beek | Follow-Up Scheduled for Freedom Academy Enrollment | Decide on Freedom Academy enrollment; inform Beau by Apr 30.<br>Send Mario new meeting link for Apr 30 check-in (same time). |
| Apr 24, 2026 07:11 UTC | Erik van Hoof | Exploring Freedom Academy - Follow-Up Scheduled | Review Freedom Academy bot calculator + performance w/ partner; prep questions for Beau.<br>Send Erik Zoom link for Apr 26 14:00 follow-up; host call w/ Erik + partner. |
| Apr 23, 2026 18:05 UTC | Raymond Keppel | Raymond Keppel - Freedom Academy Enrollment | WhatsApp Raymond Discord link + onboarding steps; then Raymond joins Discord + opens bot setup ticket.<br>Check bank transfer status; confirm receipt; update Raymond if bounced.<br>Log in to WOP; start course videos/docs. |
| Apr 23, 2026 12:00 UTC | Chris Rouwhof | Onboarding Call - Chris Rouwhof Joins Freedom Academy | WhatsApp Chris's details to Didi's nephew; he'll WhatsApp Chris to schedule bot setup. |
| Apr 23, 2026 10:17 UTC | Sjors Marckelbach | Sale Closed - Sjors Joins Freedom Academy | Send Sjors WhatsApp w/ Discord link; then Sjors join Discord and open 1:1 bot setup ticket.<br>Confirm Sjors received access email; if not, grant manual access. |
| Apr 23, 2026 09:29 UTC | Nagasaki Elena | Elena Joins Freedom Academy for Crypto Trading | Send Elena crypto-friendly residency examples (Panama/Dubai/Cyprus).<br>Forward Elena's BTC tx screenshot to finance; activate account on confirmation; notify Elena via WhatsApp. |
| Apr 23, 2026 09:03 UTC | Carolien Janzen | Exploring Freedom Academy for Financial Independence | Send USDT flexible savings details to Beau.<br>Send follow-up call link to Carolien for Apr 24 17:00. |
| Apr 23, 2026 07:27 UTC | Jan Simoens | Intro Call - Assessing Crypto Community Fit | Stop Zoom recording for Jan Simoens call. |
| Apr 23, 2026 07:05 UTC | Dennis Schouten | Sale - Dennis Joins Freedom Academy Program | WhatsApp Dennis €3k payment link; then Dennis pays after limit increase.<br>Check email for Wop access; if missing after 10 min WhatsApp Beau.<br>WhatsApp Beau 4h from now to confirm €3k payment; then complete onboarding/community access. |
| Apr 22, 2026 17:28 UTC | Balint Matys | Exploring Freedom Academy for Passive Crypto Income | Reserve Freedom Academy slot for Balint 24h; WhatsApp Balint for decision. |
| Apr 22, 2026 14:57 UTC | Chris Van As | Commitment to Freedom Academy - Payment Delayed | Evaluate 60/40 BTC vs 100% trading; calculate capital allocation.<br>Send €5,000 payment to Beau by May 7–8; then Beau grants access + Justin adds to WhatsApp.<br>Attend follow-up call w/ Chris on May 7–8. |
| Apr 22, 2026 11:00 UTC | Erik | Qualification Call Freedom Academy (TF) | Send Albert calendar invite for Apr 29 13:00 follow-up.<br>WhatsApp Albert on Apr 27 to confirm Apr 29 13:00 follow-up. |
| Apr 22, 2026 10:05 UTC | Rigo Nagels | Qualification Call Freedom Academy (TF) | Calculate costs for car + rent + fuel + insurance vs current expenses; decide Freedom Academy enrollment.<br>Send Rigo Zoom link for follow-up call Fri 17:00–18:00. |
| Apr 22, 2026 10:05 UTC | Rigo Nagels | Qualification Call Freedom Academy (TF) | Watch Freedom Academy video from Tom; send feedback to Tom.<br>Reschedule Zoom w/ Maurice to Fri same time; send invite. |
| Apr 22, 2026 07:59 UTC | olivier wijnen | Qualification Call Didi Bam Bam | Research Palau ID for exchange KYC; assess Bluefin/Bybit/OKX feasibility.<br>Check EUR/USD rate; calculate Freedom Academy fee in USD.<br>Attend follow-up Zoom w/ Tom on Apr 29; decide join/no-join. |
| Apr 22, 2026 07:00 UTC | Chanida | Strategy Call - Freedom - (FU) | Send new EUR payment link to Chanida via WhatsApp; then activate acct on receipt of screenshot.<br>Pay EUR via bank transfer to Etienne; send WhatsApp screenshot to Tom; then schedule onboarding call w/ CM. |
| Apr 21, 2026 19:05 UTC | Matt A A | Follow-Up Scheduled - Freedom Academy Discussion | Review Freedom Academy materials w/ wife; discuss enrollment.<br>Send Matt calendar invite + link for Thu 10:00 Dubai / 08:00 Amsterdam follow-up. |
| Apr 21, 2026 17:29 UTC | Dirk Terpstra | Exploring Investment Options - Follow-Up Needed | Confirm w/ team: Canada KYC/funding/off-ramp/Singapore card; Mexico residency; then WhatsApp Dirk EOW to schedule follow-up. |

**Execution time:** 44.439 sec
**Status:** ok

## 77. AAQ-080

**Question**

How many Fathom calls from 2026-04-01 to 2026-05-01 have action items?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS calls_with_action_items
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.call_started_at >= :start_date
  AND f.call_started_at < :end_date
  AND f.action_items IS NOT NULL
  AND f.action_items::text NOT IN ('null', '[]', '{}')
```

**Generated final answer**

There were 73 Fathom calls with action items from 2026-04-01 to 2026-05-01.

**Execution time:** 14.436 sec
**Status:** ok

## 78. AAQ-081

**Question**

What is the average Fathom call duration?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS calls_with_duration,
  ROUND(AVG(f.call_duration_seconds) / 60.0, 2) AS avg_call_duration_minutes
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.call_duration_seconds IS NOT NULL;
```

**Generated final answer**

The average Fathom call duration is 43.01 minutes, based on 83 calls with recorded duration.

**Execution time:** 12.281 sec
**Status:** ok

## 79. AAQ-072

**Question**

List appointments with Fathom summaries.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  f.summary,
  f.call_duration_seconds,
  f.call_started_at,
  f.call_ended_at
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND NULLIF(TRIM(f.summary), '') IS NOT NULL
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 81

Showing the first 20 records, ordered by latest call start (UTC). Some appointments may appear more than once when multiple Fathom records are linked:

| Started | Lead | Call title | Fathom summary preview |
|---|---|---|---|
| 2026-04-24 09:06 | Jeffrey Nussy | Onboarding Call - Jeffrey Joins Freedom Academy | Onboarding for financial independence |
| 2026-04-24 09:03 | Robert Eduard | Onboarding Call - Rob's Freedom Academy Enrollment | Onboarding into the crypto program |
| 2026-04-24 08:05 | Mario van Beek | Follow-Up Scheduled for Freedom Academy Enrollment | Financial and emigration goals discussion |
| 2026-04-24 07:11 | Erik van Hoof | Exploring Freedom Academy - Follow-Up Scheduled | Financial independence goals discussion |
| 2026-04-23 18:05 | Raymond Keppel | Raymond Keppel - Freedom Academy Enrollment | Program fit for financial goals |
| 2026-04-23 12:00 | Chris Rouwhof | Onboarding Call - Chris Rouwhof Joins Freedom Academy | Freedom Academy onboarding |
| 2026-04-23 10:17 | Sjors Marckelbach | Sale Closed - Sjors Joins Freedom Academy | Crypto investment goals discussion |
| 2026-04-23 09:29 | Nagasaki Elena | Elena Joins Freedom Academy for Crypto Trading | Onboarding to grow a crypto portfolio |
| 2026-04-23 09:03 | Carolien Janzen | Exploring Freedom Academy for Financial Independence | Financial independence discussion |
| 2026-04-23 07:27 | Jan Simoens | Intro Call - Assessing Crypto Community Fit | Intro call for the crypto community |
| 2026-04-23 07:05 | Dennis Schouten | Sale - Dennis Joins Freedom Academy Program | Passive income goals evaluation |
| 2026-04-22 17:28 | Balint Matys | Exploring Freedom Academy for Passive Crypto Income | Passive crypto income discussion |
| 2026-04-22 14:57 | Chris Van As | Commitment to Freedom Academy - Payment Delayed | Financial independence and Thailand move |
| 2026-04-22 11:00 | Erik | Qualification Call Freedom Academy (TF) | Crypto investment options discussion |
| 2026-04-22 10:05 | Rigo Nagels | Qualification Call Freedom Academy (TF) | Financial and emigration goals evaluation |
| 2026-04-22 10:05 | Rigo Nagels | Qualification Call Freedom Academy (TF) | Prospect qualification for the crypto program |
| 2026-04-22 07:59 | olivier wijnen | Qualification Call Didi Bam Bam | Crypto passive income options discussion |
| 2026-04-22 07:00 | Chanida | Strategy Call - Freedom - (FU) | Bot strategy and onboarding clarification |
| 2026-04-21 19:05 | Matt A A | Follow-Up Scheduled - Freedom Academy Discussion | Income generation model walkthrough |
| 2026-04-21 17:29 | Dirk Terpstra | Exploring Investment Options - Follow-Up Needed | Investing new capital for lifestyle freedom |

**Execution time:** 120.839 sec
**Status:** ok

## 80. AAQ-082

**Question**

What was the average Fathom call duration from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS calls_with_duration,
  ROUND(AVG(f.call_duration_seconds) / 60.0, 2) AS avg_call_duration_minutes
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.call_duration_seconds IS NOT NULL
  AND f.call_started_at >= :start_date
  AND f.call_started_at < :end_date;
```

**Generated final answer**

From 2026-04-01 to 2026-05-01, the average Fathom call duration was 45.15 minutes across 75 calls with recorded duration.

**Execution time:** 25.383 sec
**Status:** ok

## 81. AAQ-074

**Question**

List Fathom call summaries with key points and action items.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(
    NULLIF(TRIM(f.ai_generated_title), ''),
    NULLIF(TRIM(a.snapshot_event_name), ''),
    'Untitled Call'
  ) AS call_title,
  f.summary,
  f.key_points,
  f.action_items
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND (
    NULLIF(TRIM(f.summary), '') IS NOT NULL
    OR (f.key_points IS NOT NULL AND f.key_points::text NOT IN ('null', '[]', '{}'))
    OR (f.action_items IS NOT NULL AND f.action_items::text NOT IN ('null', '[]', '{}'))
  )
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching Fathom call records: 81

Showing the first 20 records:

Here are the most recent Fathom call summaries with captured action items; in these 20 rows, the separate key points field is empty, so the summary column reflects Fathom’s takeaways.

| Scheduled (UTC) | Call | Summary / key points | Action items |
|---|---|---|---|
| 24 Apr 2026 09:00 | Onboarding Call - Jeffrey Joins Freedom Academy | Onboarding for Freedom Academy; Jeffrey committed to the €5,000 fee and plans to fund the bot by selling assets. | Complete €5,000 transfer<br>Enter email in Beau’s WhatsApp link and notify him<br>Sell Audi and deploy proceeds to the bot |
| 24 Apr 2026 09:00 | Onboarding Call - Rob's Freedom Academy Enrollment | Rob joined to generate passive income from BTC; a trust concern was resolved, but BitMyMoney transfer limits forced a bank-transfer workaround. | Notify Tom when the BTC sale clears<br>Pay €5,000 via bank/card link<br>Receive account activation and community intro |
| 24 Apr 2026 08:00 | Follow-Up Scheduled for Freedom Academy Enrollment | Mario wants financial freedom and eventual emigration; he needs to free up capital before the 30 Apr decision point. | Decide on enrollment by 30 Apr<br>Send new meeting link for the 30 Apr check-in |
| 24 Apr 2026 07:00 | Exploring Freedom Academy - Follow-Up Scheduled | Erik wants passive income from idle capital and is positive on the Academy, but needs partner approval before deciding. | Review calculator/performance with partner and prepare questions<br>Send Zoom link for the 26 Apr follow-up |
| 23 Apr 2026 18:00 | Raymond Keppel - Freedom Academy Enrollment | Raymond wants to reduce work hours and joined for lifetime access; onboarding and Discord setup are next. | Send Raymond the Discord link and onboarding steps<br>Check transfer status and confirm receipt<br>Start course materials |
| 23 Apr 2026 12:00 | Onboarding Call - Chris Rouwhof Joins Freedom Academy | Chris joined the Academy for €5,000 to structure crypto wealth and prepare for a future move; bot setup is next. | Pass Chris’s details to Didi’s nephew to schedule bot setup |
| 23 Apr 2026 10:30 | Sale Closed - Sjors Joins Freedom Academy | Sjors bought lifetime access to restart his passive-income setup after his Bybit bot stopped working. | Send Sjors the Discord link<br>Confirm access email or grant manual access |
| 23 Apr 2026 09:30 | Elena Joins Freedom Academy for Crypto Trading | Elena joined using 0.073 BTC to grow her crypto portfolio and pursue a digital-nomad lifestyle despite Japanese tax constraints. | Send crypto-friendly residency examples<br>Forward BTC screenshot to finance and activate the account |
| 23 Apr 2026 09:00 | Exploring Freedom Academy for Financial Independence | Ger & Caroline want financial independence and emigration within 3 years, but need more time before committing. | Send USDT flexible savings details<br>Send the 24 Apr follow-up call link |
| 23 Apr 2026 07:30 | Intro Call - Assessing Crypto Community Fit | Intro call focused on fit for the crypto community; recording was stopped immediately at the prospect’s request. | Stop Zoom recording |
| 23 Apr 2026 07:00 | Sale - Dennis Joins Freedom Academy Program | Dennis joined for the self-custody model and direct access to Didi; €2,000 was paid, with €3,000 still due after a bank-limit increase. | Send €3,000 payment link<br>Check WOP access email<br>Confirm payment later that day and finish onboarding |
| 22 Apr 2026 17:30 | Exploring Freedom Academy for Passive Crypto Income | Balint is weighing the value of the Academy blueprint and support against self-managing bots with the same capital. | Reserve a slot for 24 hours<br>WhatsApp Balint for a final decision |
| 22 Apr 2026 14:30 | Commitment to Freedom Academy - Payment Delayed | Chris wants €5,000/month in passive income to support a Thailand move and has committed, but payment is delayed until early May. | Evaluate 60/40 vs 100% trading allocation<br>Send the €5,000 payment by 7–8 May<br>Attend the follow-up call |
| 23 Apr 2026 11:45 | Qualification Call Freedom Academy (TF) | Albert wants to deploy business capital but needs full transparency on exchange terms before deciding. | Send the 29 Apr 13:00 calendar invite<br>WhatsApp a reminder on 27 Apr |
| 22 Apr 2026 10:00 | Qualification Call Freedom Academy (TF) | Rigo wants passive income to support emigration, but the €5,000 fee is a major affordability concern versus keeping a safety net. | Calculate relocation/living costs vs current expenses<br>Send the Friday follow-up Zoom link |
| 22 Apr 2026 10:00 | Qualification Call Freedom Academy (TF) | Maurice wants a trustworthy crypto community, but the call was misaligned because he confused Freedom Academy with the active-trading program. | Watch the intro video and send feedback<br>Reschedule Zoom to Friday at the same time |
| 22 Apr 2026 08:00 | Qualification Call Didi Bam Bam | Andre wants about $1,500/month passive income from crypto, but exchange access from Thailand is the main blocker. | Research Palau ID and exchange feasibility<br>Check EUR/USD and the fee in USD<br>Attend the 29 Apr follow-up |
| 22 Apr 2026 07:00 | Strategy Call - Freedom - (FU) | Chanida clarified how the DCA bot works, how self-custody is preserved, and how onboarding proceeds after payment. | Send new EUR payment link<br>Pay by bank transfer and send WhatsApp screenshot<br>Schedule community-manager onboarding |
| 21 Apr 2026 19:00 | Follow-Up Scheduled - Freedom Academy Discussion | Matt wants to understand the Academy’s passive-income model and will review it with his spouse before a follow-up decision. | Review materials with wife<br>Send the Thursday follow-up invite |
| 21 Apr 2026 17:30 | Exploring Investment Options - Follow-Up Needed | Dirk wants to invest house-sale proceeds into BTC and live off passive income, but Canadian KYC/funding/off-ramp rules are the main blocker. | Confirm Canada KYC/funding/card strategy with the team<br>WhatsApp Dirk by end of week |

**Execution time:** 113.258 sec
**Status:** ok

## 82. AAQ-083

**Question**

Show average call duration by event type.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  COUNT(*) AS calls_with_duration,
  ROUND(AVG(f.call_duration_seconds) / 60.0, 2) AS avg_call_duration_minutes,
  SUM(COUNT(*)) OVER() AS total_calls_with_duration,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_duration_records
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.call_duration_seconds IS NOT NULL
GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
ORDER BY avg_call_duration_minutes DESC NULLS LAST, calls_with_duration DESC, event_name ASC;
```

**Generated final answer**

Total calls with duration: 83

Here is the breakdown:

| Event Type | Calls with Duration | Avg Call Duration (min) | % of Call Records |
|---|---:|---:|---:|
| Qualification Call Didi Bam Bam | 1 | 65.33 | 1.20% |
| Strategy Call - Freedom - FU | 2 | 53.83 | 2.41% |
| Qualification Call Freedom Academy (TF) | 67 | 44.53 | 80.72% |
| Qualification Call Freedom Academy (DMB) | 6 | 37.82 | 7.23% |
| Strategy Call - Freedom - (FU) | 6 | 29.40 | 7.23% |
| Strategy Call - Freedom (TFT) | 1 | 10.33 | 1.20% |

**Execution time:** 23.339 sec
**Status:** ok

## 83. AAQ-084

**Question**

Which event type has the longest average call duration?

**Generated SQL**

```sql
WITH event_type_durations AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS calls_with_duration,
    AVG(f.call_duration_seconds)::numeric AS avg_call_duration_seconds
  FROM fathom_call_records f
  JOIN appointments a
    ON a.id = f.appointment_id
   AND a.clerk_org_id = f.clerk_org_id
   AND a.is_deleted = false
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE f.clerk_org_id = :org_id
    AND f.call_duration_seconds IS NOT NULL
  GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
),
max_avg AS (
  SELECT MAX(avg_call_duration_seconds) AS max_avg_call_duration_seconds
  FROM event_type_durations
),
totals AS (
  SELECT SUM(calls_with_duration) AS total_calls_with_duration
  FROM event_type_durations
)
SELECT
  etd.event_name,
  etd.calls_with_duration,
  ROUND(etd.avg_call_duration_seconds / 60.0, 2) AS avg_call_duration_minutes,
  t.total_calls_with_duration
FROM event_type_durations etd
JOIN max_avg m
  ON etd.avg_call_duration_seconds = m.max_avg_call_duration_seconds
CROSS JOIN totals t
ORDER BY etd.calls_with_duration DESC, etd.event_name ASC;
```

**Generated final answer**

Across 83 calls with duration data, Qualification Call Didi Bam Bam has the longest average call duration at 65.33 minutes, based on 1 call.

**Execution time:** 26.617 sec
**Status:** ok

## 84. AAQ-085

**Question**

Show average call duration by host.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COUNT(*) AS calls_with_duration,
  ROUND(AVG(f.call_duration_seconds) / 60.0, 2) AS avg_call_duration_minutes,
  SUM(COUNT(*)) OVER() AS total_calls_with_duration,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_duration_records
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.call_duration_seconds IS NOT NULL
GROUP BY COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host')
ORDER BY avg_call_duration_minutes DESC NULLS LAST, calls_with_duration DESC, host_id ASC;
```

**Generated final answer**

Total calls with duration: 83

Here is the average call duration by host:

| Host ID | Calls with duration | Avg. call duration | % of calls with duration |
|---|---:|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 55 | 43.96 min | 66.27% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 28 | 41.15 min | 33.73% |

**Execution time:** 25.082 sec
**Status:** ok

## 85. AAQ-086

**Question**

Which host has the longest average call duration?

**Generated SQL**

```sql
WITH host_duration AS (
  SELECT
    NULLIF(TRIM(a.host_id), '') AS host_id,
    COUNT(*) AS calls_with_duration,
    AVG(f.call_duration_seconds) AS avg_call_duration_seconds
  FROM fathom_call_records f
  JOIN appointments a
    ON a.id = f.appointment_id
   AND a.clerk_org_id = f.clerk_org_id
   AND a.is_deleted = false
  WHERE f.clerk_org_id = :org_id
    AND f.call_duration_seconds IS NOT NULL
    AND NULLIF(TRIM(a.host_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.host_id), '')
),
max_avg AS (
  SELECT MAX(avg_call_duration_seconds) AS max_avg_call_duration_seconds
  FROM host_duration
)
SELECT
  hd.host_id,
  hd.calls_with_duration,
  ROUND(hd.avg_call_duration_seconds / 60.0, 2) AS avg_call_duration_minutes
FROM host_duration hd
JOIN max_avg ma
  ON hd.avg_call_duration_seconds = ma.max_avg_call_duration_seconds
ORDER BY hd.host_id ASC;
```

**Generated final answer**

Host `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` has the longest average call duration at 43.96 minutes, based on 55 calls with recorded duration.

**Execution time:** 25.259 sec
**Status:** ok

## 86. AAQ-079

**Question**

List Fathom calls that have either action items or objections.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  COALESCE(f.call_started_at, a.schedule_time, f.created_at) AS call_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  CASE
    WHEN f.action_items IS NOT NULL AND f.action_items::text NOT IN ('null', '[]', '{}') THEN true
    ELSE false
  END AS has_action_items,
  CASE
    WHEN f.objections IS NOT NULL AND f.objections::text NOT IN ('null', '[]', '{}') THEN true
    ELSE false
  END AS has_objections,
  f.action_items,
  f.objections
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND (
    (f.action_items IS NOT NULL AND f.action_items::text NOT IN ('null', '[]', '{}'))
    OR
    (f.objections IS NOT NULL AND f.objections::text NOT IN ('null', '[]', '{}'))
  )
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching Fathom calls: 79

Showing the latest 20 calls:

| Call time | Lead | Call title | Action items | Objections |
|---|---|---|---|---|
| 2026-04-24 09:06:25 UTC | Jeffrey Nussy | Onboarding Call - Jeffrey Joins Freedom Academy | Yes | No |
| 2026-04-24 09:03:19 UTC | Robert Eduard | Onboarding Call - Rob's Freedom Academy Enrollment | Yes | No |
| 2026-04-24 08:05:37 UTC | Mario van Beek | Follow-Up Scheduled for Freedom Academy Enrollment | Yes | No |
| 2026-04-24 07:11:34 UTC | Erik van Hoof | Exploring Freedom Academy - Follow-Up Scheduled | Yes | No |
| 2026-04-23 18:05:56 UTC | Raymond Keppel | Raymond Keppel - Freedom Academy Enrollment | Yes | No |
| 2026-04-23 12:00:32 UTC | Chris Rouwhof | Onboarding Call - Chris Rouwhof Joins Freedom Academy | Yes | No |
| 2026-04-23 10:17:03 UTC | Sjors Marckelbach | Sale Closed - Sjors Joins Freedom Academy | Yes | No |
| 2026-04-23 09:29:11 UTC | Nagasaki Elena | Elena Joins Freedom Academy for Crypto Trading | Yes | No |
| 2026-04-23 09:03:32 UTC | Carolien Janzen | Exploring Freedom Academy for Financial Independence | Yes | No |
| 2026-04-23 07:27:57 UTC | Jan Simoens | Intro Call - Assessing Crypto Community Fit | Yes | No |
| 2026-04-23 07:05:10 UTC | Dennis Schouten | Sale - Dennis Joins Freedom Academy Program | Yes | No |
| 2026-04-22 17:28:27 UTC | Balint Matys | Exploring Freedom Academy for Passive Crypto Income | Yes | No |
| 2026-04-22 14:57:50 UTC | Chris Van As | Commitment to Freedom Academy - Payment Delayed | Yes | No |
| 2026-04-22 11:00:10 UTC | Erik | Qualification Call Freedom Academy (TF) | Yes | No |
| 2026-04-22 10:05:56 UTC | Rigo Nagels | Qualification Call Freedom Academy (TF) | Yes | No |
| 2026-04-22 10:05:42 UTC | Rigo Nagels | Qualification Call Freedom Academy (TF) | Yes | No |
| 2026-04-22 07:59:18 UTC | olivier wijnen | Qualification Call Didi Bam Bam | Yes | No |
| 2026-04-22 07:00:49 UTC | Chanida | Strategy Call - Freedom - (FU) | Yes | No |
| 2026-04-21 19:05:25 UTC | Matt A A | Follow-Up Scheduled - Freedom Academy Discussion | Yes | No |
| 2026-04-21 17:29:45 UTC | Dirk Terpstra | Exploring Investment Options - Follow-Up Needed | Yes | No |

**Execution time:** 73.563 sec
**Status:** ok

## 87. AAQ-088

**Question**

How many Fathom calls have an AI-suggested outcome?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS calls_with_ai_suggested_outcome
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.ai_suggested_outcome IS NOT NULL;
```

**Generated final answer**

There are 78 Fathom calls with an AI-suggested outcome.

**Execution time:** 10.469 sec
**Status:** ok

## 88. AAQ-089

**Question**

How many Fathom outcomes were applied?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS applied_fathom_outcomes
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.outcome_applied = true;
```

**Generated final answer**

No Fathom outcomes have been applied.

**Execution time:** 10.748 sec
**Status:** ok

## 89. AAQ-093

**Question**

How many Fathom records are not matched to any appointment?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS unmatched_fathom_records
FROM fathom_call_records f
WHERE f.clerk_org_id = :org_id
  AND f.appointment_id IS NULL;
```

**Generated final answer**

There are 10 Fathom records not matched to any appointment.

**Execution time:** 11.157 sec
**Status:** ok

## 90. AAQ-087

**Question**

What is the breakdown of AI-suggested Fathom outcomes?

**Generated SQL**

```sql
SELECT
  COALESCE(ai_outcome.name, 'No AI Suggested Outcome') AS ai_suggested_outcome_name,
  COALESCE(CAST(ai_outcome.role AS text), 'NO_AI_OUTCOME') AS ai_suggested_outcome_role,
  COUNT(*) AS fathom_record_count,
  SUM(COUNT(*)) OVER() AS total_matching_fathom_records,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total,
  ROUND(AVG(f.ai_confidence_score), 2) AS avg_ai_confidence_score,
  COUNT(*) FILTER (WHERE f.outcome_applied = true) AS applied_count,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE f.outcome_applied = true) / NULLIF(COUNT(*), 0),
    2
  ) AS applied_rate_percent
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN sales_statuses ai_outcome
  ON ai_outcome.id = f.ai_suggested_outcome
 AND ai_outcome.clerk_org_id = f.clerk_org_id
WHERE f.clerk_org_id = :org_id
GROUP BY
  COALESCE(ai_outcome.name, 'No AI Suggested Outcome'),
  COALESCE(CAST(ai_outcome.role AS text), 'NO_AI_OUTCOME')
ORDER BY fathom_record_count DESC, ai_suggested_outcome_name ASC;
```

**Generated final answer**

Total matching Fathom records: 83

Most AI-suggested outcomes were No Sale - Follow Up, followed by Won.

| AI-suggested outcome | Role | Fathom records | % of total | Avg AI confidence score | Applied count | Applied rate |
|---|---|---:|---:|---:|---:|---:|
| No Sale - Follow Up | Follow Up | 49 | 59.04% | 0.84 | 0 | 0.00% |
| Won | Won | 21 | 25.30% | 0.95 | 0 | 0.00% |
| No AI Suggested Outcome | No AI Outcome | 5 | 6.02% | — | 0 | 0.00% |
| Deposit | Partial Payment | 4 | 4.82% | 0.84 | 0 | 0.00% |
| No Sale - Lost | Lost | 2 | 2.41% | 0.90 | 0 | 0.00% |
| Rescheduled | Rescheduled | 2 | 2.41% | 0.88 | 0 | 0.00% |

**Execution time:** 44.129 sec
**Status:** ok

## 91. AAQ-091

**Question**

Which AI-suggested outcome has the highest average confidence score?

**Generated SQL**

```sql
WITH outcome_confidence AS (
  SELECT
    COALESCE(ai_outcome.name, 'Unknown AI Suggested Outcome') AS ai_suggested_outcome_name,
    COALESCE(CAST(ai_outcome.role AS text), 'UNKNOWN_AI_OUTCOME') AS ai_suggested_outcome_role,
    COUNT(*) AS fathom_record_count,
    AVG(f.ai_confidence_score::numeric) AS avg_ai_confidence_score_raw,
    SUM(COUNT(*)) OVER() AS total_matching_fathom_records
  FROM fathom_call_records f
  JOIN appointments a
    ON a.id = f.appointment_id
   AND a.clerk_org_id = f.clerk_org_id
   AND a.is_deleted = false
  LEFT JOIN sales_statuses ai_outcome
    ON ai_outcome.id = f.ai_suggested_outcome
   AND ai_outcome.clerk_org_id = f.clerk_org_id
  WHERE f.clerk_org_id = :org_id
    AND f.ai_suggested_outcome IS NOT NULL
    AND f.ai_confidence_score IS NOT NULL
  GROUP BY
    COALESCE(ai_outcome.name, 'Unknown AI Suggested Outcome'),
    COALESCE(CAST(ai_outcome.role AS text), 'UNKNOWN_AI_OUTCOME')
),
max_avg AS (
  SELECT MAX(avg_ai_confidence_score_raw) AS max_avg_ai_confidence_score_raw
  FROM outcome_confidence
)
SELECT
  oc.ai_suggested_outcome_name,
  oc.ai_suggested_outcome_role,
  ROUND(oc.avg_ai_confidence_score_raw, 2) AS avg_ai_confidence_score,
  oc.fathom_record_count,
  oc.total_matching_fathom_records
FROM outcome_confidence oc
JOIN max_avg m
  ON oc.avg_ai_confidence_score_raw = m.max_avg_ai_confidence_score_raw
ORDER BY oc.fathom_record_count DESC, oc.ai_suggested_outcome_name ASC
```

**Generated final answer**

Across 78 Fathom records with AI-suggested outcomes and confidence scores, **Won** has the highest average confidence score at **0.95**, based on **21** records.

**Execution time:** 37.981 sec
**Status:** ok

## 92. AAQ-090

**Question**

Show applied versus not-applied Fathom outcomes.

**Generated SQL**

```sql
SELECT
  CASE
    WHEN f.outcome_applied IS TRUE THEN 'Applied'
    ELSE 'Not Applied'
  END AS outcome_application_status,
  COUNT(*) AS fathom_record_count,
  SUM(COUNT(*)) OVER() AS total_matching_fathom_records,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.ai_suggested_outcome IS NOT NULL
GROUP BY CASE
  WHEN f.outcome_applied IS TRUE THEN 'Applied'
  ELSE 'Not Applied'
END
ORDER BY fathom_record_count DESC, outcome_application_status ASC;
```

**Generated final answer**

Across 78 Fathom records with AI-suggested outcomes, all were not applied, so no applied outcomes were found.

**Execution time:** 49.763 sec
**Status:** ok

## 93. AAQ-095

**Question**

Show Fathom match strategy breakdown.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(CAST(f.match_strategy AS text)), ''), 'Unknown') AS match_strategy,
  COUNT(*) AS fathom_record_count,
  SUM(COUNT(*)) OVER() AS total_matching_fathom_records,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM fathom_call_records f
WHERE f.clerk_org_id = :org_id
GROUP BY COALESCE(NULLIF(TRIM(CAST(f.match_strategy AS text)), ''), 'Unknown')
ORDER BY fathom_record_count DESC, match_strategy ASC;
```

**Generated final answer**

Total matching Fathom records: 93

Most Fathom records used the Host Email Timestamp match strategy.

| Match strategy | Fathom records | % of total |
|---|---:|---:|
| Host Email Timestamp | 73 | 78.49% |
| Unknown | 10 | 10.75% |
| Host Timestamp Invitee Email | 5 | 5.38% |
| Timestamp Only | 4 | 4.30% |
| Host Timestamp Invitee | 1 | 1.08% |

**Execution time:** 32.454 sec
**Status:** ok

## 94. AAQ-096

**Question**

How many Fathom records were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS fathom_records_created_in_period
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.created_at >= :start_date
  AND f.created_at < :end_date;
```

**Generated final answer**

There were 75 Fathom records created from 2026-04-01 to 2026-05-01.

**Execution time:** 25.432 sec
**Status:** ok

## 95. AAQ-092

**Question**

List Fathom calls where the AI outcome was not applied.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  COALESCE(f.call_started_at, a.schedule_time, f.created_at) AS call_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  COALESCE(ai_outcome.name, 'Unknown AI Suggested Outcome') AS ai_suggested_outcome_name,
  COALESCE(current_outcome.name, 'No Outcome') AS current_appointment_outcome_name,
  ROUND(f.ai_confidence_score, 2) AS ai_confidence_score
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses ai_outcome
  ON ai_outcome.id = f.ai_suggested_outcome
 AND ai_outcome.clerk_org_id = f.clerk_org_id
LEFT JOIN sales_statuses current_outcome
  ON current_outcome.id = a.outcome_id
 AND current_outcome.clerk_org_id = a.clerk_org_id
WHERE f.clerk_org_id = :org_id
  AND f.ai_suggested_outcome IS NOT NULL
  AND f.outcome_applied IS NOT TRUE
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 78

Showing the first 20 most recent records:

| Call time (UTC) | Lead | Call title | AI suggested outcome | Current appointment outcome | AI confidence score |
|---|---|---|---|---|---:|
| 2026-04-24 09:06 | Jeffrey Nussy | Onboarding Call - Jeffrey Joins Freedom Academy | Won | Won | 0.95 |
| 2026-04-24 09:03 | Robert Eduard | Onboarding Call - Rob's Freedom Academy Enrollment | Won | Call Booked | 0.85 |
| 2026-04-24 08:05 | Mario van Beek | Follow-Up Scheduled for Freedom Academy Enrollment | No Sale - Follow Up | Call Booked | 0.85 |
| 2026-04-24 07:11 | Erik van Hoof | Exploring Freedom Academy - Follow-Up Scheduled | No Sale - Follow Up | Call Booked | 0.85 |
| 2026-04-23 18:05 | Raymond Keppel | Raymond Keppel - Freedom Academy Enrollment | Won | Won | 0.95 |
| 2026-04-23 12:00 | Chris Rouwhof | Onboarding Call - Chris Rouwhof Joins Freedom Academy | Won | Won | 0.95 |
| 2026-04-23 10:17 | Sjors Marckelbach | Sale Closed - Sjors Joins Freedom Academy | Won | Won | 0.95 |
| 2026-04-23 09:29 | Nagasaki Elena | Elena Joins Freedom Academy for Crypto Trading | Won | Won | 0.95 |
| 2026-04-23 09:03 | Carolien Janzen | Exploring Freedom Academy for Financial Independence | No Sale - Follow Up | No Sale - Follow Up | 0.85 |
| 2026-04-23 07:27 | Jan Simoens | Intro Call - Assessing Crypto Community Fit | No Sale - Follow Up | No Sale - Follow Up | 0.75 |
| 2026-04-23 07:05 | Dennis Schouten | Sale - Dennis Joins Freedom Academy Program | Won | Won | 0.95 |
| 2026-04-22 17:28 | Balint Matys | Exploring Freedom Academy for Passive Crypto Income | No Sale - Follow Up | No Sale - Follow Up | 0.80 |
| 2026-04-22 14:57 | Chris Van As | Commitment to Freedom Academy - Payment Delayed | No Sale - Follow Up | No Sale - Follow Up | 0.85 |
| 2026-04-21 19:05 | Matt A A | Follow-Up Scheduled - Freedom Academy Discussion | No Sale - Follow Up | No Sale - Follow Up | 0.85 |
| 2026-04-21 17:29 | Dirk Terpstra | Exploring Investment Options - Follow-Up Needed | No Sale - Follow Up | No Sale - Follow Up | 0.85 |
| 2026-04-21 17:07 | Brent Knudsen | Follow-Up Needed - Brent's Crypto Tax Strategy | No Sale - Follow Up | No Sale - Follow Up | 0.85 |
| 2026-04-21 15:58 | Gabe Real | Follow-Up Scheduled - Research on AI Trading Bots | No Sale - Follow Up | No Show | 0.85 |
| 2026-04-21 15:02 | Joep Bergmans | Interest in Freedom Academy - Follow-Up Scheduled | No Sale - Follow Up | No Sale - Follow Up | 0.85 |
| 2026-04-21 12:16 | Jerry Vercammen | Onboarding Jerry Vercammen to Freedom Academy | Won | Won | 0.95 |
| 2026-04-21 11:29 | Onno Stillebroer | Home Equity for Crypto Income - Follow-Up Scheduled | No Sale - Follow Up | No Sale - Follow Up | 0.85 |

**Execution time:** 79.623 sec
**Status:** ok

## 96. AAQ-094

**Question**

List unmatched Fathom records.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  f.fathom_call_id,
  f.fathom_meeting_id,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), 'Untitled Call') AS call_title,
  f.summary,
  f.call_duration_seconds,
  f.call_started_at,
  f.call_ended_at,
  f.created_at
FROM fathom_call_records f
WHERE f.clerk_org_id = :org_id
  AND f.appointment_id IS NULL
ORDER BY COALESCE(f.call_started_at, f.created_at) DESC, f.id ASC
LIMIT 20;
```

**Generated final answer**

Total unmatched Fathom records: 10

Here is the complete list of Fathom records not linked to an appointment:

| Fathom record ID | Call title | Call started (UTC) | Duration |
|---|---|---|---|
| 304e29ff-8485-488f-b11d-d628ad5dbc0b | Daily Sync - Client Issues and Follow-Up Plans | 2026-04-24 06:31 | 24m 54s |
| 4d81ecde-4551-4a65-a7a5-1849ff9038ce | Daily Sync - Lead Quality and Follow-Up Challenges | 2026-04-24 06:31 | 24m 56s |
| 1e133d60-0222-4d42-be11-6662ed51d161 | Follow-Up Scheduled - Jannes's Investment Decision | 2026-04-22 16:00 | 32m 03s |
| 1e31ea8e-f3e7-4768-a5b8-e719816fb408 | Untitled Call | 2026-04-22 06:05 | 13m 21s |
| 116e3bc5-65ed-49c5-91bc-92e637eefa21 | Debrief - Unqualified Prospect Interaction | 2026-04-21 14:44 | 9m 41s |
| 327098b7-a990-4ad6-ba48-ef549ac34d6d | Sales Strategy Meeting - €30k Goal Set | 2026-04-17 06:29 | 5m 05s |
| 8bb76f38-02d7-4d2d-8722-ea712205b737 | Sales Strategy Review and Follow-Up Planning | 2026-04-17 06:29 | 32m 03s |
| 6b575a5b-0e09-4195-b16e-7f12559da72e | Follow-Up Needed: Investment Discussion Scheduled | 2026-04-16 18:01 | 42m 22s |
| 6c5470a1-ab4a-4ea9-b4b0-bb4883addc0b | Exploring Freedom Academy for Financial Goals | 2026-04-16 09:58 | 47m 09s |
| 9a10a1ec-cd56-4328-8948-f1aa5dcded31 | Operational Review and Pricing Strategy Discussion | 2026-03-30 06:30 | 28m 17s |

**Execution time:** 69.064 sec
**Status:** ok

## 97. AAQ-099

**Question**

Show the monthly appointment trend from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS appointment_month
),
monthly_counts AS (
  SELECT
    m.appointment_month,
    COUNT(a.id) AS appointment_count
  FROM months m
  LEFT JOIN appointments a
    ON DATE_TRUNC('month', a.schedule_time)::date = m.appointment_month
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
  GROUP BY m.appointment_month
),
monthly_with_previous AS (
  SELECT
    appointment_month,
    appointment_count,
    LAG(appointment_count) OVER (ORDER BY appointment_month ASC) AS previous_period_appointment_count
  FROM monthly_counts
)
SELECT
  appointment_month,
  appointment_count,
  previous_period_appointment_count,
  CASE
    WHEN previous_period_appointment_count IS NULL OR previous_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - previous_period_appointment_count)::numeric / previous_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(appointment_count) OVER() AS total_matching_appointments
FROM monthly_with_previous
ORDER BY appointment_month ASC;
```

**Generated final answer**

There were 448 appointments scheduled from May 2025 through Apr 2026.

| Month | Appointments | Previous month | % change |
|---|---:|---:|---:|
| May 2025 | 0 | N/A | N/A |
| Jun 2025 | 0 | 0 | N/A |
| Jul 2025 | 0 | 0 | N/A |
| Aug 2025 | 0 | 0 | N/A |
| Sep 2025 | 0 | 0 | N/A |
| Oct 2025 | 0 | 0 | N/A |
| Nov 2025 | 0 | 0 | N/A |
| Dec 2025 | 0 | 0 | N/A |
| Jan 2026 | 0 | 0 | N/A |
| Feb 2026 | 0 | 0 | N/A |
| Mar 2026 | 230 | 0 | N/A |
| Apr 2026 | 218 | 230 | -5.22% |

In Apr 2026, appointments decreased by 12 compared with Mar 2026, a 5.22% decline.

**Execution time:** 39.064 sec
**Status:** ok

## 98. AAQ-098

**Question**

Show the weekly appointment trend from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 week'
  )::date AS appointment_week
),
weekly_counts AS (
  SELECT
    w.appointment_week,
    COUNT(a.id) AS appointment_count
  FROM weeks w
  LEFT JOIN appointments a
    ON DATE_TRUNC('week', a.schedule_time)::date = w.appointment_week
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
  GROUP BY w.appointment_week
),
weekly_with_previous AS (
  SELECT
    appointment_week,
    appointment_count,
    LAG(appointment_count) OVER (ORDER BY appointment_week ASC) AS previous_period_appointment_count
  FROM weekly_counts
)
SELECT
  appointment_week,
  appointment_count,
  previous_period_appointment_count,
  CASE
    WHEN previous_period_appointment_count IS NULL OR previous_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - previous_period_appointment_count)::numeric / previous_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(appointment_count) OVER() AS total_matching_appointments
FROM weekly_with_previous
ORDER BY appointment_week ASC
```

**Generated final answer**

Total matching appointments: 449

Here is the weekly trend:

| Week starting | Appointments | Previous week | % change |
|---|---:|---:|---:|
| 2026-02-09 | 0 | — | — |
| 2026-02-16 | 0 | 0 | — |
| 2026-02-23 | 0 | 0 | — |
| 2026-03-02 | 10 | 0 | — |
| 2026-03-09 | 65 | 10 | 550.00% |
| 2026-03-16 | 69 | 65 | 6.15% |
| 2026-03-23 | 69 | 69 | 0.00% |
| 2026-03-30 | 43 | 69 | -37.68% |
| 2026-04-06 | 47 | 43 | 9.30% |
| 2026-04-13 | 43 | 47 | -8.51% |
| 2026-04-20 | 94 | 43 | 118.60% |
| 2026-04-27 | 9 | 94 | -90.43% |
| 2026-05-04 | 0 | 9 | -100.00% |

In the week starting 2026-05-04, there were 0 appointments within the selected range, down from 9 in the previous week (-100.00%).

**Execution time:** 53.893 sec
**Status:** ok

## 99. AAQ-101

**Question**

Show monthly appointment growth from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS appointment_month
),
monthly_counts AS (
  SELECT
    m.appointment_month,
    COUNT(a.id) AS appointment_count
  FROM months m
  LEFT JOIN appointments a
    ON DATE_TRUNC('month', a.schedule_time)::date = m.appointment_month
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
  GROUP BY m.appointment_month
),
monthly_with_previous AS (
  SELECT
    appointment_month,
    appointment_count,
    LAG(appointment_count) OVER (ORDER BY appointment_month ASC) AS previous_period_appointment_count
  FROM monthly_counts
)
SELECT
  appointment_month,
  appointment_count,
  previous_period_appointment_count,
  CASE
    WHEN previous_period_appointment_count IS NULL OR previous_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - previous_period_appointment_count)::numeric / previous_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(appointment_count) OVER() AS total_matching_appointments
FROM monthly_with_previous
ORDER BY appointment_month ASC
```

**Generated final answer**

Total matching appointments: 448

Here is the monthly appointment growth from May 2025 through Apr 2026:

| Month | Appointments | Previous month | % change |
|---|---:|---:|---:|
| May 2025 | 0 | — | — |
| Jun 2025 | 0 | 0 | — |
| Jul 2025 | 0 | 0 | — |
| Aug 2025 | 0 | 0 | — |
| Sep 2025 | 0 | 0 | — |
| Oct 2025 | 0 | 0 | — |
| Nov 2025 | 0 | 0 | — |
| Dec 2025 | 0 | 0 | — |
| Jan 2026 | 0 | 0 | — |
| Feb 2026 | 0 | 0 | — |
| Mar 2026 | 230 | 0 | — |
| Apr 2026 | 218 | 230 | -5.22% |

Appointments appeared in Mar 2026 and then declined slightly in Apr 2026, dropping from 230 to 218 (-5.22%).

**Execution time:** 36.522 sec
**Status:** ok

## 100. AAQ-097

**Question**

Show the daily appointment trend from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH days AS (
  SELECT generate_series(
    CAST(:start_date AS date),
    CAST(:end_date AS date),
    INTERVAL '1 day'
  )::date AS appointment_date
)
SELECT
  d.appointment_date,
  COUNT(a.id) AS appointment_count,
  SUM(COUNT(a.id)) OVER () AS total_matching_appointments
FROM days d
LEFT JOIN appointments a
  ON a.clerk_org_id = :org_id
 AND a.is_deleted = false
 AND a.schedule_time >= d.appointment_date
 AND a.schedule_time < d.appointment_date + INTERVAL '1 day'
GROUP BY d.appointment_date
ORDER BY d.appointment_date ASC
```

**Generated final answer**

From 2026-04-01 to 2026-05-01, there were 219 scheduled appointments.

| Date | Appointments |
|---|---:|
| 2026-04-01 | 4 |
| 2026-04-02 | 3 |
| 2026-04-03 | 9 |
| 2026-04-04 | 10 |
| 2026-04-05 | 0 |
| 2026-04-06 | 5 |
| 2026-04-07 | 12 |
| 2026-04-08 | 6 |
| 2026-04-09 | 8 |
| 2026-04-10 | 8 |
| 2026-04-11 | 3 |
| 2026-04-12 | 5 |
| 2026-04-13 | 7 |
| 2026-04-14 | 10 |
| 2026-04-15 | 8 |
| 2026-04-16 | 4 |
| 2026-04-17 | 12 |
| 2026-04-18 | 0 |
| 2026-04-19 | 2 |
| 2026-04-20 | 14 |
| 2026-04-21 | 15 |
| 2026-04-22 | 10 |
| 2026-04-23 | 17 |
| 2026-04-24 | 17 |
| 2026-04-25 | 13 |
| 2026-04-26 | 8 |
| 2026-04-27 | 4 |
| 2026-04-28 | 1 |
| 2026-04-29 | 2 |
| 2026-04-30 | 1 |
| 2026-05-01 | 1 |

**Execution time:** 80.940 sec
**Status:** ok

## 101. AAQ-102

**Question**

Show daily no-show trend from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH days AS (
  SELECT generate_series(
    CAST(:start_date AS date),
    (CAST(:end_date AS date) - INTERVAL '1 day')::date,
    INTERVAL '1 day'
  )::date AS appointment_date
),
daily_no_shows AS (
  SELECT
    d.appointment_date,
    COUNT(a.id) AS no_show_appointments
  FROM days d
  LEFT JOIN appointments a
    ON a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.no_show = true
   AND a.schedule_time >= d.appointment_date
   AND a.schedule_time < d.appointment_date + INTERVAL '1 day'
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
   AND a.schedule_time < NOW()
  GROUP BY d.appointment_date
  ORDER BY d.appointment_date ASC
)
SELECT
  SUM(no_show_appointments) AS total_matching_no_show_appointments,
  JSON_AGG(
    JSON_BUILD_OBJECT(
      'appointment_date', appointment_date,
      'no_show_appointments', no_show_appointments
    )
    ORDER BY appointment_date ASC
  ) AS daily_no_show_trend
FROM daily_no_shows
```

**Generated final answer**

Total no-show appointments: 24

Here is the daily no-show trend from 2026-04-01 to 2026-05-01:

| Date | No-show appointments |
|---|---:|
| 2026-04-01 | 0 |
| 2026-04-02 | 0 |
| 2026-04-03 | 1 |
| 2026-04-04 | 1 |
| 2026-04-05 | 0 |
| 2026-04-06 | 1 |
| 2026-04-07 | 1 |
| 2026-04-08 | 2 |
| 2026-04-09 | 1 |
| 2026-04-10 | 0 |
| 2026-04-11 | 0 |
| 2026-04-12 | 0 |
| 2026-04-13 | 2 |
| 2026-04-14 | 1 |
| 2026-04-15 | 1 |
| 2026-04-16 | 1 |
| 2026-04-17 | 2 |
| 2026-04-18 | 0 |
| 2026-04-19 | 1 |
| 2026-04-20 | 4 |
| 2026-04-21 | 1 |
| 2026-04-22 | 1 |
| 2026-04-23 | 2 |
| 2026-04-24 | 1 |
| 2026-04-25 | 0 |
| 2026-04-26 | 0 |
| 2026-04-27 | 0 |
| 2026-04-28 | 0 |
| 2026-04-29 | 0 |
| 2026-04-30 | 0 |
| 2026-05-01 | 0 |

**Execution time:** 71.194 sec
**Status:** ok

## 102. AAQ-100

**Question**

Show weekly appointment growth from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 week'
  )::date AS appointment_week
),
weekly_counts AS (
  SELECT
    w.appointment_week,
    COUNT(a.id) AS appointment_count
  FROM weeks w
  LEFT JOIN appointments a
    ON DATE_TRUNC('week', a.schedule_time)::date = w.appointment_week
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
  GROUP BY w.appointment_week
),
weekly_with_previous AS (
  SELECT
    appointment_week,
    appointment_count,
    LAG(appointment_count) OVER (ORDER BY appointment_week ASC) AS previous_period_appointment_count
  FROM weekly_counts
)
SELECT
  appointment_week,
  appointment_count,
  previous_period_appointment_count,
  CASE
    WHEN previous_period_appointment_count IS NULL OR previous_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - previous_period_appointment_count)::numeric / previous_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(appointment_count) OVER() AS total_matching_appointments
FROM weekly_with_previous
ORDER BY appointment_week ASC
```

**Generated final answer**

Total matching appointments: 449

Here is the weekly appointment growth, grouped by week starting date:

| Week starting | Appointments | Previous week | % change |
|---|---:|---:|---:|
| 2026-02-09 | 0 | — | — |
| 2026-02-16 | 0 | 0 | — |
| 2026-02-23 | 0 | 0 | — |
| 2026-03-02 | 10 | 0 | — |
| 2026-03-09 | 65 | 10 | 550.00% |
| 2026-03-16 | 69 | 65 | 6.15% |
| 2026-03-23 | 69 | 69 | 0.00% |
| 2026-03-30 | 43 | 69 | -37.68% |
| 2026-04-06 | 47 | 43 | 9.30% |
| 2026-04-13 | 43 | 47 | -8.51% |
| 2026-04-20 | 94 | 43 | 118.60% |
| 2026-04-27 | 9 | 94 | -90.43% |

In the week starting 2026-04-27, appointments fell by 85 compared with the previous week, a 90.43% decrease.

**Execution time:** 96.691 sec
**Status:** ok

## 103. AAQ-104

**Question**

Show monthly no-show trend from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS appointment_month
),
monthly_counts AS (
  SELECT
    m.appointment_month,
    COUNT(a.id) AS total_past_appointments,
    COUNT(a.id) FILTER (WHERE a.no_show = true) AS no_show_appointments
  FROM months m
  LEFT JOIN appointments a
    ON DATE_TRUNC('month', a.schedule_time)::date = m.appointment_month
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
   AND a.schedule_time < NOW()
  GROUP BY m.appointment_month
),
monthly_with_previous AS (
  SELECT
    appointment_month,
    total_past_appointments,
    no_show_appointments,
    LAG(no_show_appointments) OVER (ORDER BY appointment_month ASC) AS previous_period_no_show_appointments
  FROM monthly_counts
)
SELECT
  appointment_month,
  total_past_appointments,
  no_show_appointments,
  ROUND(100.0 * no_show_appointments / NULLIF(total_past_appointments, 0), 2) AS no_show_rate_percent,
  previous_period_no_show_appointments,
  CASE
    WHEN previous_period_no_show_appointments IS NULL OR previous_period_no_show_appointments = 0 THEN NULL
    ELSE ROUND(
      ((no_show_appointments - previous_period_no_show_appointments)::numeric / previous_period_no_show_appointments) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(no_show_appointments) OVER() AS total_matching_no_show_appointments
FROM monthly_with_previous
ORDER BY appointment_month ASC;
```

**Generated final answer**

Total no-show appointments in this period: 54

Here is the monthly no-show trend for May 2025 through Apr 2026:

| Month | Past appointments | No-shows | No-show rate | Previous month no-shows | % change |
|---|---:|---:|---:|---:|---:|
| May 2025 | 0 | 0 | — | — | — |
| Jun 2025 | 0 | 0 | — | 0 | — |
| Jul 2025 | 0 | 0 | — | 0 | — |
| Aug 2025 | 0 | 0 | — | 0 | — |
| Sep 2025 | 0 | 0 | — | 0 | — |
| Oct 2025 | 0 | 0 | — | 0 | — |
| Nov 2025 | 0 | 0 | — | 0 | — |
| Dec 2025 | 0 | 0 | — | 0 | — |
| Jan 2026 | 0 | 0 | — | 0 | — |
| Feb 2026 | 0 | 0 | — | 0 | — |
| Mar 2026 | 230 | 30 | 13.04% | 0 | — |
| Apr 2026 | 218 | 24 | 11.01% | 30 | -20.00% |

In Apr 2026, no-shows decreased by 6 compared with Mar 2026, a 20.00% decrease, and the no-show rate moved from 13.04% to 11.01%.

**Execution time:** 60.409 sec
**Status:** ok

## 104. AAQ-103

**Question**

Show weekly no-show trend from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', CAST(:end_date AS timestamp))::date,
    INTERVAL '1 week'
  )::date AS appointment_week
),
weekly_counts AS (
  SELECT
    w.appointment_week,
    COUNT(a.id) AS total_past_appointments,
    COUNT(a.id) FILTER (WHERE a.no_show = true) AS no_show_appointments
  FROM weeks w
  LEFT JOIN appointments a
    ON DATE_TRUNC('week', a.schedule_time)::date = w.appointment_week
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= CAST(:start_date AS date)
   AND a.schedule_time < (CAST(:end_date AS date) + INTERVAL '1 day')
   AND a.schedule_time < NOW()
  GROUP BY w.appointment_week
),
weekly_with_previous AS (
  SELECT
    appointment_week,
    total_past_appointments,
    no_show_appointments,
    ROUND(
      100.0 * no_show_appointments / NULLIF(total_past_appointments, 0),
      2
    ) AS no_show_rate_percent,
    LAG(no_show_appointments) OVER (ORDER BY appointment_week ASC) AS previous_week_no_show_appointments
  FROM weekly_counts
)
SELECT
  appointment_week,
  total_past_appointments,
  no_show_appointments,
  no_show_rate_percent,
  previous_week_no_show_appointments,
  CASE
    WHEN previous_week_no_show_appointments IS NULL OR previous_week_no_show_appointments = 0 THEN NULL
    ELSE ROUND(
      ((no_show_appointments - previous_week_no_show_appointments)::numeric / previous_week_no_show_appointments) * 100,
      2
    )
  END AS percentage_change_from_previous_week,
  SUM(total_past_appointments) OVER () AS total_matching_past_appointments,
  SUM(no_show_appointments) OVER () AS total_matching_no_show_appointments
FROM weekly_with_previous
ORDER BY appointment_week ASC
```

**Generated final answer**

From 2026-02-09 to 2026-05-04, there were 54 no-shows out of 449 past appointments.

| Week starting | Past appointments | No-shows | No-show rate | Previous week no-shows | WoW change |
|---|---:|---:|---:|---:|---:|
| 2026-02-09 | 0 | 0 | — | — | — |
| 2026-02-16 | 0 | 0 | — | 0 | — |
| 2026-02-23 | 0 | 0 | — | 0 | — |
| 2026-03-02 | 10 | 3 | 30.00% | 0 | — |
| 2026-03-09 | 65 | 12 | 18.46% | 3 | +300.00% |
| 2026-03-16 | 69 | 8 | 11.59% | 12 | -33.33% |
| 2026-03-23 | 69 | 6 | 8.70% | 8 | -25.00% |
| 2026-03-30 | 43 | 3 | 6.98% | 6 | -50.00% |
| 2026-04-06 | 47 | 5 | 10.64% | 3 | +66.67% |
| 2026-04-13 | 43 | 8 | 18.60% | 5 | +60.00% |
| 2026-04-20 | 94 | 9 | 9.57% | 8 | +12.50% |
| 2026-04-27 | 9 | 0 | 0.00% | 9 | -100.00% |
| 2026-05-04 | 0 | 0 | — | 0 | — |

In the latest week with appointments, 2026-04-27, no-shows fell to 0 from 9 the prior week, a 100.00% decrease.

**Execution time:** 85.689 sec
**Status:** ok

## 105. AAQ-109

**Question**

Where are most appointments coming from by source?

**Generated SQL**

```sql
SELECT
  CAST(a.source AS text) AS appointment_source,
  COUNT(*) AS appointment_count,
  SUM(COUNT(*)) OVER() AS total_matching_appointments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM appointments a
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
GROUP BY CAST(a.source AS text)
ORDER BY appointment_count DESC, appointment_source ASC;
```

**Generated final answer**

Total appointments: 451

All appointments are coming from Calendly (451, 100.00%).

**Execution time:** 16.320 sec
**Status:** ok

## 106. AAQ-106

**Question**

Show monthly appointment trend by call category from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS appointment_month
),
categories AS (
  SELECT DISTINCT
    COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN') AS call_category
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
),
monthly_category_counts AS (
  SELECT
    m.appointment_month,
    c.call_category,
    COUNT(a.id) AS appointment_count
  FROM months m
  CROSS JOIN categories c
  LEFT JOIN appointments a
    ON DATE_TRUNC('month', a.schedule_time)::date = m.appointment_month
   AND COALESCE(CAST(a.snapshot_call_category AS text), 'UNKNOWN') = c.call_category
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
  GROUP BY m.appointment_month, c.call_category
),
monthly_category_with_previous AS (
  SELECT
    appointment_month,
    call_category,
    appointment_count,
    LAG(appointment_count) OVER (
      PARTITION BY call_category
      ORDER BY appointment_month ASC
    ) AS previous_period_appointment_count
  FROM monthly_category_counts
)
SELECT
  appointment_month,
  call_category,
  appointment_count,
  previous_period_appointment_count,
  CASE
    WHEN previous_period_appointment_count IS NULL OR previous_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - previous_period_appointment_count)::numeric / previous_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(appointment_count) OVER() AS total_matching_appointments
FROM monthly_category_with_previous
ORDER BY appointment_month ASC, call_category ASC;
```

**Generated final answer**

Total matching appointments: 448

Here is the monthly trend by call category:

| Call category | May 2025 | Jun 2025 | Jul 2025 | Aug 2025 | Sep 2025 | Oct 2025 | Nov 2025 | Dec 2025 | Jan 2026 | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sales Call | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 230 | 218 (-5.22%) |

In Apr 2026, Sales Call appointments decreased by 12 compared with Mar 2026, a 5.22% decrease.

**Execution time:** 58.564 sec
**Status:** ok

## 107. AAQ-110

**Question**

Which call category is driving the most booked calls?

**Generated SQL**

```sql
WITH category_counts AS (
  SELECT
    CAST(a.snapshot_call_category AS text) AS call_category,
    COUNT(*) AS booked_call_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.snapshot_call_category IS NOT NULL
  GROUP BY CAST(a.snapshot_call_category AS text)
),
max_count AS (
  SELECT MAX(booked_call_count) AS max_booked_call_count
  FROM category_counts
)
SELECT
  cc.call_category,
  cc.booked_call_count,
  SUM(cc.booked_call_count) OVER() AS total_matching_appointments,
  ROUND(cc.booked_call_count * 100.0 / NULLIF(SUM(cc.booked_call_count) OVER(), 0), 2) AS percentage_of_total
FROM category_counts cc
JOIN max_count mc
  ON cc.booked_call_count = mc.max_booked_call_count
ORDER BY cc.call_category ASC;
```

**Generated final answer**

Among calls with a recorded category, Sales Call is driving the most bookings with 451 booked calls.

**Execution time:** 33.009 sec
**Status:** ok

## 108. AAQ-111

**Question**

Which event type should we review because it has the highest no-show rate?

**Generated SQL**

```sql
WITH event_type_no_show_rates AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    (100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0)) AS no_show_rate_percent_exact,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
      2
    ) AS no_show_rate_percent,
    SUM(COUNT(*)) OVER() AS total_matching_past_appointments
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
  GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
),
max_rate AS (
  SELECT MAX(no_show_rate_percent_exact) AS max_no_show_rate_percent_exact
  FROM event_type_no_show_rates
)
SELECT
  et.event_name,
  et.total_past_appointments,
  et.no_show_appointments,
  et.no_show_rate_percent,
  et.total_matching_past_appointments
FROM event_type_no_show_rates et
JOIN max_rate mr
  ON et.no_show_rate_percent_exact = mr.max_no_show_rate_percent_exact
ORDER BY et.total_past_appointments DESC, et.event_name ASC;
```

**Generated final answer**

Total past appointments analyzed: 450

The event type to review is “Unknown” — it has the highest no-show rate at 100.00% (1 no-show out of 1 past appointment), so this looks like a very small-sample outlier.

**Execution time:** 37.810 sec
**Status:** ok

## 109. AAQ-112

**Question**

Which host needs the most no-show follow-up?

**Generated SQL**

```sql
WITH host_no_show_stats AS (
  SELECT
    NULLIF(TRIM(a.host_id), '') AS host_id,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
      2
    ) AS no_show_rate_percent
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND NULLIF(TRIM(a.host_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.host_id), '')
),
ranked_hosts AS (
  SELECT
    host_id,
    total_past_appointments,
    no_show_appointments,
    no_show_rate_percent,
    SUM(no_show_appointments) OVER() AS total_matching_no_show_appointments,
    ROUND(
      100.0 * no_show_appointments / NULLIF(SUM(no_show_appointments) OVER(), 0),
      2
    ) AS percentage_of_all_no_shows,
    DENSE_RANK() OVER (ORDER BY no_show_appointments DESC) AS no_show_rank
  FROM host_no_show_stats
  WHERE no_show_appointments > 0
)
SELECT
  host_id,
  no_show_appointments,
  total_past_appointments,
  no_show_rate_percent,
  percentage_of_all_no_shows,
  total_matching_no_show_appointments
FROM ranked_hosts
WHERE no_show_rank = 1
ORDER BY host_id ASC;
```

**Generated final answer**

Based on past appointments, host `user_3ATRxXyN4j8bDHYJKRCEMAerasy` needs the most no-show follow-up with 28 no-shows out of 197 past appointments (14.21% no-show rate), accounting for 51.85% of all 54 no-shows.

**Execution time:** 36.369 sec
**Status:** ok

## 110. AAQ-108

**Question**

Show monthly no-show rate by event type from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS appointment_month
),
event_types AS (
  SELECT DISTINCT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
    AND a.schedule_time < NOW()
),
monthly_counts AS (
  SELECT
    DATE_TRUNC('month', a.schedule_time)::date AS appointment_month,
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
    AND a.schedule_time < NOW()
  GROUP BY
    DATE_TRUNC('month', a.schedule_time)::date,
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
),
month_event_matrix AS (
  SELECT
    m.appointment_month,
    et.event_name
  FROM months m
  CROSS JOIN event_types et
),
monthly_filled AS (
  SELECT
    mem.appointment_month,
    mem.event_name,
    COALESCE(mc.total_past_appointments, 0) AS total_past_appointments,
    COALESCE(mc.no_show_appointments, 0) AS no_show_appointments,
    CASE
      WHEN COALESCE(mc.total_past_appointments, 0) = 0 THEN NULL
      ELSE ROUND(100.0 * COALESCE(mc.no_show_appointments, 0) / mc.total_past_appointments, 2)
    END AS no_show_rate_percent
  FROM month_event_matrix mem
  LEFT JOIN monthly_counts mc
    ON mc.appointment_month = mem.appointment_month
   AND mc.event_name = mem.event_name
),
with_previous AS (
  SELECT
    appointment_month,
    event_name,
    total_past_appointments,
    no_show_appointments,
    no_show_rate_percent,
    LAG(total_past_appointments) OVER (PARTITION BY event_name ORDER BY appointment_month ASC) AS previous_period_total_past_appointments,
    LAG(no_show_appointments) OVER (PARTITION BY event_name ORDER BY appointment_month ASC) AS previous_period_no_show_appointments,
    LAG(no_show_rate_percent) OVER (PARTITION BY event_name ORDER BY appointment_month ASC) AS previous_period_no_show_rate_percent,
    SUM(total_past_appointments) OVER (PARTITION BY event_name) AS event_type_total_past_appointments,
    SUM(no_show_appointments) OVER (PARTITION BY event_name) AS event_type_total_no_show_appointments,
    SUM(total_past_appointments) OVER () AS total_matching_past_appointments
  FROM monthly_filled
)
SELECT
  appointment_month,
  event_name,
  total_past_appointments,
  no_show_appointments,
  no_show_rate_percent,
  previous_period_total_past_appointments,
  previous_period_no_show_appointments,
  previous_period_no_show_rate_percent,
  CASE
    WHEN previous_period_no_show_rate_percent IS NULL OR no_show_rate_percent IS NULL THEN NULL
    ELSE ROUND(no_show_rate_percent - previous_period_no_show_rate_percent, 2)
  END AS no_show_rate_change_percentage_points,
  event_type_total_past_appointments,
  event_type_total_no_show_appointments,
  total_matching_past_appointments
FROM with_previous
ORDER BY event_type_total_past_appointments DESC, event_name ASC, appointment_month ASC
```

**Generated final answer**

Total past appointments in the period: 448

No past appointments were found from May 2025 through Feb 2026, so the monthly rates appear only for Mar and Apr 2026. Cells show no-show rate with no-shows/appointments.

| Event type | Mar 2026 | Apr 2026 |
|---|---|---|
| Qualification Call Freedom Academy (TF) | 14.47% (11/76) | 12.36% (22/178) |
| Qualification Call Freedom Academy (DMB) | 3.64% (2/55) | 6.67% (1/15) |
| Strategy Call - Freedom | 30.00% (12/40) | — |
| Strategy Call - Freedom - (FU) | 0.00% (0/11) | 6.67% (1/15) |
| Strategy Call - Freedom - FU | 5.00% (1/20) | 0.00% (0/4) |
| Strategy Call - Freedom (TFT) | 15.00% (3/20) | 0.00% (0/2) |
| Qualification Call Freedom Academy (DML) | 0.00% (0/6) | — |
| Qualification Call Didi Bam Bam | — | 0.00% (0/4) |
| Qualification Call Freedom Academy (DM) | 0.00% (0/1) | — |
| Unknown | 100.00% (1/1) | — |

In Apr 2026, Qualification Call Freedom Academy (TF) remained the highest-volume event type, and its no-show rate improved from 14.47% in Mar 2026 to 12.36% in Apr 2026.

**Execution time:** 96.558 sec
**Status:** ok

## 111. AAQ-105

**Question**

Show weekly appointment trend by event type from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 week'
  )::date AS appointment_week
),
event_types AS (
  SELECT DISTINCT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
),
weekly_event_counts AS (
  SELECT
    DATE_TRUNC('week', a.schedule_time)::date AS appointment_week,
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS appointment_count
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
  GROUP BY
    DATE_TRUNC('week', a.schedule_time)::date,
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
),
grid AS (
  SELECT
    w.appointment_week,
    e.event_name
  FROM weeks w
  CROSS JOIN event_types e
),
weekly_with_previous AS (
  SELECT
    g.appointment_week,
    g.event_name,
    COALESCE(wec.appointment_count, 0) AS appointment_count,
    LAG(COALESCE(wec.appointment_count, 0)) OVER (
      PARTITION BY g.event_name
      ORDER BY g.appointment_week ASC
    ) AS previous_period_appointment_count,
    SUM(COALESCE(wec.appointment_count, 0)) OVER (PARTITION BY g.event_name) AS event_type_total_appointments,
    SUM(COALESCE(wec.appointment_count, 0)) OVER () AS total_matching_appointments
  FROM grid g
  LEFT JOIN weekly_event_counts wec
    ON wec.appointment_week = g.appointment_week
   AND wec.event_name = g.event_name
)
SELECT
  appointment_week,
  event_name,
  appointment_count,
  previous_period_appointment_count,
  CASE
    WHEN previous_period_appointment_count IS NULL OR previous_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - previous_period_appointment_count)::numeric / previous_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  event_type_total_appointments,
  total_matching_appointments
FROM weekly_with_previous
ORDER BY appointment_week ASC, event_type_total_appointments DESC, event_name ASC
```

**Generated final answer**

Total matching appointments: 449

Qualification Call Freedom Academy (TF) drove most of the weekly appointment volume in this period.

| Event type | Feb 09 | Feb 16 | Feb 23 | Mar 02 | Mar 09 | Mar 16 | Mar 23 | Mar 30 | Apr 06 | Apr 13 | Apr 20 | Apr 27 | May 04 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qualification Call Freedom Academy (TF) | 0 | 0 | 0 | 5 | 33 (+560.00%) | 19 (-42.42%) | 17 (-10.53%) | 14 (-17.65%) | 35 (+150.00%) | 40 (+14.29%) | 87 (+117.50%) | 4 (-95.40%) | 0 (-100.00%) |
| Qualification Call Freedom Academy (DMB) | 0 | 0 | 0 | 1 | 10 (+900.00%) | 17 (+70.00%) | 19 (+11.76%) | 17 (-10.53%) | 5 (-70.59%) | 1 (-80.00%) | 0 (-100.00%) | 1 | 0 (-100.00%) |
| Strategy Call - Freedom | 0 | 0 | 0 | 3 | 16 (+433.33%) | 17 (+6.25%) | 3 (-82.35%) | 1 (-66.67%) | 0 (-100.00%) | 0 | 0 | 0 | 0 |
| Strategy Call - Freedom - (FU) | 0 | 0 | 0 | 0 | 0 | 1 | 5 (+400.00%) | 9 (+80.00%) | 6 (-33.33%) | 1 (-83.33%) | 3 (+200.00%) | 1 (-66.67%) | 0 (-100.00%) |
| Strategy Call - Freedom - FU | 0 | 0 | 0 | 0 | 3 | 12 (+300.00%) | 5 (-58.33%) | 1 (-80.00%) | 0 (-100.00%) | 1 | 2 (+100.00%) | 0 (-100.00%) | 0 |
| Strategy Call - Freedom (TFT) | 0 | 0 | 0 | 0 | 0 | 1 | 19 (+1800.00%) | 0 (-100.00%) | 1 | 0 (-100.00%) | 1 | 0 (-100.00%) | 0 |
| Qualification Call Freedom Academy (DML) | 0 | 0 | 0 | 1 | 3 (+200.00%) | 2 (-33.33%) | 0 (-100.00%) | 0 | 0 | 0 | 0 | 0 | 0 |
| Qualification Call Didi Bam Bam | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3 (+200.00%) | 0 (-100.00%) |
| Qualification Call Freedom Academy (DM) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 (-100.00%) | 0 | 0 | 0 | 0 |
| Unknown | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 (-100.00%) | 0 | 0 | 0 | 0 | 0 |

In the week of May 04, Qualification Call Freedom Academy (TF) fell from 4 appointments to 0, a 100.00% decrease from the prior week.

**Execution time:** 162.057 sec
**Status:** ok

## 112. AAQ-107

**Question**

Show weekly no-show trend by host from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 week'
  )::date AS appointment_week
),
hosts AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
    COUNT(*) AS total_no_show_appointments
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.no_show = true
    AND a.schedule_time >= :start_date
    AND a.schedule_time < :end_date
    AND a.schedule_time < NOW()
  GROUP BY COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host')
),
top_hosts AS (
  SELECT
    host_id,
    total_no_show_appointments,
    ROW_NUMBER() OVER (ORDER BY total_no_show_appointments DESC, host_id ASC) AS host_rank
  FROM hosts
),
weekly_host_no_shows AS (
  SELECT
    w.appointment_week,
    th.host_id,
    COUNT(a.id) AS no_show_appointments,
    th.total_no_show_appointments
  FROM weeks w
  JOIN top_hosts th
    ON th.host_rank <= 20
  LEFT JOIN appointments a
    ON DATE_TRUNC('week', a.schedule_time)::date = w.appointment_week
   AND COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') = th.host_id
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.no_show = true
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
   AND a.schedule_time < NOW()
  GROUP BY
    w.appointment_week,
    th.host_id,
    th.total_no_show_appointments
),
weekly_with_previous AS (
  SELECT
    appointment_week,
    host_id,
    no_show_appointments,
    LAG(no_show_appointments) OVER (
      PARTITION BY host_id
      ORDER BY appointment_week ASC
    ) AS previous_period_no_show_appointments,
    total_no_show_appointments
  FROM weekly_host_no_shows
)
SELECT
  appointment_week,
  host_id,
  no_show_appointments,
  previous_period_no_show_appointments,
  CASE
    WHEN previous_period_no_show_appointments IS NULL
      OR previous_period_no_show_appointments = 0 THEN NULL
    ELSE ROUND(
      ((no_show_appointments - previous_period_no_show_appointments)::numeric
        / previous_period_no_show_appointments) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(no_show_appointments) OVER () AS total_matching_no_show_appointments
FROM weekly_with_previous
ORDER BY appointment_week ASC, total_no_show_appointments DESC, host_id ASC
```

**Generated final answer**

Total no-shows: 54

Here is the weekly no-show trend by host, grouped by week start date:

| Host ID | Feb 9 | Feb 16 | Feb 23 | Mar 2 | Mar 9 | Mar 16 | Mar 23 | Mar 30 | Apr 6 | Apr 13 | Apr 20 | Apr 27 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | 0 | 0 | 0 | 2 | 6 (+200.00%) | 6 (0.00%) | 3 (-50.00%) | 2 (-33.33%) | 3 (+50.00%) | 1 (-66.67%) | 5 (+400.00%) | 0 (-100.00%) |
| `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | 0 | 0 | 0 | 1 | 6 (+500.00%) | 2 (-66.67%) | 3 (+50.00%) | 1 (-66.67%) | 2 (+100.00%) | 7 (+250.00%) | 4 (-42.86%) | 0 (-100.00%) |

In the latest week starting Apr 27, 2026, no-shows dropped to 0 for both hosts, down from 5 and 4 in the previous week.

**Execution time:** 111.403 sec
**Status:** ok

## 113. AAQ-113

**Question**

Which setter is booking the highest number of attended calls?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(a.setter_id), '') AS setter_id,
    COUNT(*) AS attended_call_count
  FROM appointments a
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
    AND a.no_show = false
    AND NULLIF(TRIM(a.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(a.setter_id), '')
),
max_count AS (
  SELECT MAX(attended_call_count) AS max_attended_call_count
  FROM setter_counts
),
totals AS (
  SELECT COALESCE(SUM(attended_call_count), 0) AS total_matching_attended_calls
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.attended_call_count,
  t.total_matching_attended_calls,
  ROUND(sc.attended_call_count * 100.0 / NULLIF(t.total_matching_attended_calls, 0), 2) AS percentage_of_total
FROM setter_counts sc
JOIN max_count mc
  ON sc.attended_call_count = mc.max_attended_call_count
CROSS JOIN totals t
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

Across past attended calls with a setter assigned, the top setter is `user_3AesMObeGeZynVoGhloMkfwanES`, with 87 attended calls out of 88 total (98.86%).

**Execution time:** 21.490 sec
**Status:** ok

## 114. AAQ-116

**Question**

Which calls mention objections in the Fathom record?

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  COALESCE(f.call_started_at, a.schedule_time, f.created_at) AS call_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  f.objections::text AS objections
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.objections IS NOT NULL
  AND f.objections::text NOT IN ('null', '[]', '{}')
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT 20;
```

**Generated final answer**

There are no calls that mention objections in the Fathom record.

**Execution time:** 15.893 sec
**Status:** ok

## 115. AAQ-114

**Question**

Which appointments need operational attention because they are missing Fathom records?

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  a.id,
  a.schedule_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  COALESCE(outcome.name, 'No Outcome') AS outcome_name,
  COALESCE(CAST(outcome.role AS text), 'NO_OUTCOME') AS outcome_role,
  a.no_show,
  CAST(a.source AS text) AS appointment_source,
  COALESCE(NULLIF(TRIM(a.host_id), ''), 'No Host') AS host_id,
  COALESCE(NULLIF(TRIM(a.setter_id), ''), 'No Setter') AS setter_id,
  false AS has_fathom_record
FROM appointments a
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = a.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN sales_statuses outcome
  ON outcome.id = a.outcome_id
 AND outcome.clerk_org_id = a.clerk_org_id
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE a.clerk_org_id = :org_id
  AND a.is_deleted = false
  AND a.schedule_time < NOW()
  AND NOT EXISTS (
    SELECT 1
    FROM fathom_call_records f_check
    WHERE f_check.appointment_id = a.id
      AND f_check.clerk_org_id = a.clerk_org_id
  )
ORDER BY a.schedule_time DESC, a.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching appointments: 368

Showing the first 20 past appointments without a linked Fathom record:

| Scheduled time | Lead | Event | Call category | Outcome | Source | Host ID | Setter ID |
|---|---|---|---|---|---|---|---|
| 2026-05-05 13:00 UTC | Ricardo Brandao | Strategy Call - Freedom - FU | Sales Call | Rescheduled | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter |
| 2026-05-01 08:00 UTC | Wesley Helmers | Qualification Call Freedom Academy (DMB) | Sales Call | No Sale - Follow Up | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter |
| 2026-04-30 16:00 UTC | Stephen William Bennett | Qualification Call Didi Bam Bam | Sales Call | Rescheduled | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-29 11:00 UTC | Albert de Bruin | Qualification Call Freedom Academy (TF) | Sales Call | Rescheduled | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES |
| 2026-04-29 08:00 UTC | Andre Steenkamp | Qualification Call Freedom Academy (TF) | Sales Call | No Sale - Follow Up | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter |
| 2026-04-28 15:00 UTC | Robert Voorn | Strategy Call - Freedom - (FU) | Sales Call | Call Booked | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter |
| 2026-04-27 12:00 UTC | Van der Veken Olivier | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter |
| 2026-04-27 11:00 UTC | Erik Bakker | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter |
| 2026-04-27 10:00 UTC | Bahadir | Qualification Call Didi Bam Bam | Sales Call | Call Booked | Calendly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter |
| 2026-04-27 06:00 UTC | Steve Grainger | Qualification Call Didi Bam Bam | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 18:00 UTC | Roos ‘t Lam | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 15:30 UTC | Rob Schwarz | Qualification Call Freedom Academy (TF) | Sales Call | Canceled | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 11:00 UTC | Rene Solms | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 10:00 UTC | Henry Stokkelaar | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 09:00 UTC | Tom ter woord | Qualification Call Freedom Academy (TF) | Sales Call | Canceled | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 07:00 UTC | Nake Dragomirov | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 06:00 UTC | Aad Bouw | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-26 06:00 UTC | Kale green | Qualification Call Freedom Academy (TF) | Sales Call | Canceled | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-25 15:00 UTC | Bryan Casica | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |
| 2026-04-25 14:00 UTC | Eugenio Jedi Martinez | Qualification Call Freedom Academy (TF) | Sales Call | Call Booked | Calendly | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter |

**Execution time:** 47.612 sec
**Status:** ok

## 116. AAQ-117

**Question**

Which appointment event types have both high volume and no-shows?

**Generated SQL**

```sql
WITH event_type_stats AS (
  SELECT
    COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
    COUNT(*) AS total_past_appointments,
    COUNT(*) FILTER (WHERE a.no_show = true) AS no_show_appointments,
    ROUND(
      100.0 * COUNT(*) FILTER (WHERE a.no_show = true) / NULLIF(COUNT(*), 0),
      2
    ) AS no_show_rate_percent
  FROM appointments a
  LEFT JOIN appointment_event_types aet
    ON aet.id = a.appointment_event_type_id
   AND aet.clerk_org_id = a.clerk_org_id
   AND aet.is_deleted = false
  WHERE a.clerk_org_id = :org_id
    AND a.is_deleted = false
    AND a.schedule_time < NOW()
  GROUP BY COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type')
)
SELECT
  event_name,
  total_past_appointments,
  no_show_appointments,
  no_show_rate_percent,
  SUM(total_past_appointments) OVER() AS total_matching_past_appointments,
  ROUND(
    total_past_appointments * 100.0 / NULLIF(SUM(total_past_appointments) OVER(), 0),
    2
  ) AS percentage_of_total_past_appointments
FROM event_type_stats
WHERE no_show_appointments > 0
ORDER BY no_show_appointments DESC, total_past_appointments DESC, no_show_rate_percent DESC, event_name ASC;
```

**Generated final answer**

Total past appointments across event types with at least one no-show: 439

Qualification Call Freedom Academy (TF) stands out most on both volume and no-shows, while Strategy Call - Freedom has a notably high no-show rate.

| Event type | Past appointments | No-shows | No-show rate | Share of matching volume |
|---|---:|---:|---:|---:|
| Qualification Call Freedom Academy (TF) | 254 | 33 | 12.99% | 57.86% |
| Strategy Call - Freedom | 40 | 12 | 30.00% | 9.11% |
| Qualification Call Freedom Academy (DMB) | 71 | 3 | 4.23% | 16.17% |
| Strategy Call - Freedom (TFT) | 22 | 3 | 13.64% | 5.01% |
| Strategy Call - Freedom - (FU) | 26 | 1 | 3.85% | 5.92% |
| Strategy Call - Freedom - FU | 25 | 1 | 4.00% | 5.69% |
| Unknown | 1 | 1 | 100.00% | 0.23% |

**Execution time:** 56.202 sec
**Status:** ok

## 117. AAQ-118

**Question**

What changed in appointment volume from 2026-02-01 to 2026-05-01?

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS appointment_month
),
monthly_counts AS (
  SELECT
    m.appointment_month,
    COUNT(a.id) AS appointment_count
  FROM months m
  LEFT JOIN appointments a
    ON DATE_TRUNC('month', a.schedule_time)::date = m.appointment_month
   AND a.clerk_org_id = :org_id
   AND a.is_deleted = false
   AND a.schedule_time >= :start_date
   AND a.schedule_time < :end_date
  GROUP BY m.appointment_month
),
monthly_with_metrics AS (
  SELECT
    appointment_month,
    appointment_count,
    LAG(appointment_count) OVER (ORDER BY appointment_month ASC) AS previous_period_appointment_count,
    FIRST_VALUE(appointment_count) OVER (ORDER BY appointment_month ASC) AS first_period_appointment_count
  FROM monthly_counts
)
SELECT
  appointment_month,
  appointment_count,
  previous_period_appointment_count,
  CASE
    WHEN previous_period_appointment_count IS NULL OR previous_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - previous_period_appointment_count)::numeric / previous_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  first_period_appointment_count,
  appointment_count - first_period_appointment_count AS absolute_change_from_first_period,
  CASE
    WHEN first_period_appointment_count = 0 THEN NULL
    ELSE ROUND(
      ((appointment_count - first_period_appointment_count)::numeric / first_period_appointment_count) * 100,
      2
    )
  END AS percentage_change_from_first_period,
  SUM(appointment_count) OVER() AS total_matching_appointments
FROM monthly_with_metrics
ORDER BY appointment_month ASC
```

**Generated final answer**

From Feb 2026 through Apr 2026, there were 448 scheduled appointments. Volume was 0 in Feb, rose sharply to 230 in Mar, then eased to 218 in Apr.

| Month | Appointments | Previous month | % change |
|---|---:|---:|---:|
| Feb 2026 | 0 | N/A | N/A |
| Mar 2026 | 230 | 0 | N/A |
| Apr 2026 | 218 | 230 | -5.22% |

In Apr 2026, appointment volume decreased to 218 from 230 in Mar 2026, a 5.22% decrease.

**Execution time:** 70.836 sec
**Status:** ok

## 118. AAQ-115

**Question**

Which calls have follow-up action items captured by Fathom?

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  f.id AS fathom_record_id,
  a.id AS appointment_id,
  COALESCE(f.call_started_at, a.schedule_time, f.created_at) AS call_time,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(NULLIF(TRIM(f.ai_generated_title), ''), NULLIF(TRIM(a.snapshot_event_name), ''), 'Untitled Call') AS call_title,
  COALESCE(NULLIF(TRIM(a.snapshot_event_name), ''), aet.event_type_name, 'Unknown Event Type') AS event_name,
  CAST(a.snapshot_call_category AS text) AS call_category,
  f.action_items
FROM fathom_call_records f
JOIN appointments a
  ON a.id = f.appointment_id
 AND a.clerk_org_id = f.clerk_org_id
 AND a.is_deleted = false
LEFT JOIN leads l
  ON l.id = a.lead_id
 AND l.clerk_org_id = f.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN appointment_event_types aet
  ON aet.id = a.appointment_event_type_id
 AND aet.clerk_org_id = a.clerk_org_id
 AND aet.is_deleted = false
WHERE f.clerk_org_id = :org_id
  AND f.action_items IS NOT NULL
  AND f.action_items::text NOT IN ('null', '[]', '{}', '""')
ORDER BY COALESCE(f.call_started_at, a.schedule_time, f.created_at) DESC, f.id ASC
LIMIT :limit;
```

**Generated final answer**

Total matching calls: 79

Showing the first 20 most recent calls:

| Call time | Call | Follow-up actions |
|---|---|---|
| 24 Apr 2026 09:06 UTC | Jeffrey Nussy — Onboarding Call - Jeffrey Joins Freedom Academy | • Complete onboarding: pay €5k via bank transfer; enter email in Beau's WhatsApp link; notify Beau; receive access; schedule bot setup w/ Justin<br>• Sell Audi; deploy proceeds to bot |
| 24 Apr 2026 09:03 UTC | Robert Eduard — Onboarding Call - Rob's Freedom Academy Enrollment | • WhatsApp Tom when BitMyMoney BTC sale clears; then pay €5k via link (card/bank)<br>• WhatsApp Rob payment link when ready; then activate account and intro to Community Manager |
| 24 Apr 2026 08:05 UTC | Mario van Beek — Follow-Up Scheduled for Freedom Academy Enrollment | • Decide on Freedom Academy enrollment; inform Beau by Apr 30<br>• Send Mario new meeting link for Apr 30 check-in (same time) |
| 24 Apr 2026 07:11 UTC | Erik van Hoof — Exploring Freedom Academy - Follow-Up Scheduled | • Review Freedom Academy bot calculator + performance w/ partner; prep questions for Beau<br>• Send Erik Zoom link for Apr 26 14:00 follow-up; host call w/ Erik + partner |
| 23 Apr 2026 18:05 UTC | Raymond Keppel — Raymond Keppel - Freedom Academy Enrollment | • WhatsApp Raymond Discord link + onboarding steps; then Raymond joins Discord + opens bot setup ticket<br>• Check bank transfer status; confirm receipt; update Raymond if bounced<br>• Log in to WOP; start course videos/docs |
| 23 Apr 2026 12:00 UTC | Chris Rouwhof — Onboarding Call - Chris Rouwhof Joins Freedom Academy | • WhatsApp Chris's details to Didi's nephew; he'll WhatsApp Chris to schedule bot setup |
| 23 Apr 2026 10:17 UTC | Sjors Marckelbach — Sale Closed - Sjors Joins Freedom Academy | • Send Sjors WhatsApp w/ Discord link; then Sjors join Discord and open 1:1 bot setup ticket<br>• Confirm Sjors received access email; if not, grant manual access |
| 23 Apr 2026 09:29 UTC | Nagasaki Elena — Elena Joins Freedom Academy for Crypto Trading | • Send Elena crypto-friendly residency examples (Panama/Dubai/Cyprus)<br>• Forward Elena's BTC tx screenshot to finance; activate account on confirmation; notify Elena via WhatsApp |
| 23 Apr 2026 09:03 UTC | Carolien Janzen — Exploring Freedom Academy for Financial Independence | • Send USDT flexible savings details to Beau<br>• Send follow-up call link to Carolien for Apr 24 17:00 |
| 23 Apr 2026 07:27 UTC | Jan Simoens — Intro Call - Assessing Crypto Community Fit | • Stop Zoom recording for Jan Simoens call |
| 23 Apr 2026 07:05 UTC | Dennis Schouten — Sale - Dennis Joins Freedom Academy Program | • WhatsApp Dennis €3k payment link; then Dennis pays after limit increase<br>• Check email for Wop access; if missing after 10 min WhatsApp Beau<br>• WhatsApp Beau 4h from now to confirm €3k payment; then complete onboarding/community access |
| 22 Apr 2026 17:28 UTC | Balint Matys — Exploring Freedom Academy for Passive Crypto Income | • Reserve Freedom Academy slot for Balint 24h; WhatsApp Balint for decision |
| 22 Apr 2026 14:57 UTC | Chris Van As — Commitment to Freedom Academy - Payment Delayed | • Evaluate 60/40 BTC vs 100% trading; calculate capital allocation<br>• Send €5,000 payment to Beau by May 7–8; then Beau grants access + Justin adds to WhatsApp<br>• Attend follow-up call w/ Chris on May 7–8 |
| 22 Apr 2026 11:00 UTC | Erik — Qualification Call Freedom Academy (TF) | • Send Albert calendar invite for Apr 29 13:00 follow-up<br>• WhatsApp Albert on Apr 27 to confirm Apr 29 13:00 follow-up |
| 22 Apr 2026 10:05 UTC | Rigo Nagels — Qualification Call Freedom Academy (TF) | • Calculate costs for car + rent + fuel + insurance vs current expenses; decide Freedom Academy enrollment<br>• Send Rigo Zoom link for follow-up call Fri 17:00–18:00 |
| 22 Apr 2026 10:05 UTC | Rigo Nagels — Qualification Call Freedom Academy (TF) | • Watch Freedom Academy video from Tom; send feedback to Tom<br>• Reschedule Zoom w/ Maurice to Fri same time; send invite |
| 22 Apr 2026 07:59 UTC | olivier wijnen — Qualification Call Didi Bam Bam | • Research Palau ID for exchange KYC; assess Bluefin/Bybit/OKX feasibility<br>• Check EUR/USD rate; calculate Freedom Academy fee in USD<br>• Attend follow-up Zoom w/ Tom on Apr 29; decide join/no-join |
| 22 Apr 2026 07:00 UTC | Chanida — Strategy Call - Freedom - (FU) | • Send new EUR payment link to Chanida via WhatsApp; then activate acct on receipt of screenshot<br>• Pay EUR via bank transfer to Etienne; send WhatsApp screenshot to Tom; then schedule onboarding call w/ CM |
| 21 Apr 2026 19:05 UTC | Matt A A — Follow-Up Scheduled - Freedom Academy Discussion | • Review Freedom Academy materials w/ wife; discuss enrollment<br>• Send Matt calendar invite + link for Thu 10:00 Dubai / 08:00 Amsterdam follow-up |
| 21 Apr 2026 17:29 UTC | Dirk Terpstra — Exploring Investment Options - Follow-Up Needed | • Confirm w/ team: Canada KYC/funding/off-ramp/Singapore card; Mexico residency; then WhatsApp Dirk EOW to schedule follow-up |

**Execution time:** 107.206 sec
**Status:** ok
