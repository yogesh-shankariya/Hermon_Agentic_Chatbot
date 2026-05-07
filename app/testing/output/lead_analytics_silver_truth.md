# Lead Analytics Silver Truth

## 1. LAQ-001

**Question**

How many active leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS active_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false;
```

**Generated final answer**

There are 515 active leads.

**Execution time:** 6.989 sec
**Status:** ok

## 2. LAQ-005

**Question**

How many leads have no status assigned?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_without_status
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.status_id IS NULL;
```

**Generated final answer**

There are 0 leads with no status assigned.

**Execution time:** 8.861 sec
**Status:** ok

## 3. LAQ-002

**Question**

How many leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_created_in_period
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
```

**Generated final answer**

There were 281 leads created from 2026-04-01 to 2026-05-01.

**Execution time:** 12.610 sec
**Status:** ok

## 4. LAQ-004

**Question**

How many leads were created during the previous 3 completed months from 2026-02-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_created_in_period
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

**Generated final answer**

There were 515 leads created from 2026-02-01 through 2026-04-30.

**Execution time:** 13.427 sec
**Status:** ok

## 5. LAQ-006

**Question**

How many leads are missing a current pipeline role?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_missing_current_pipeline_role
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role IS NULL;
```

**Generated final answer**

There are 0 leads missing a current pipeline role.

**Execution time:** 10.938 sec
**Status:** ok

## 6. LAQ-003

**Question**

How many leads were created from 2026-01-01 to 2026-04-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_created_in_period
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

**Generated final answer**

There were 240 leads created from 2026-01-01 through 2026-04-01.

**Execution time:** 21.574 sec
**Status:** ok

## 7. LAQ-007

**Question**

How many leads are currently in New Lead status?

**Generated SQL**

```sql
SELECT COUNT(*) AS new_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NEW_LEAD';
```

**Generated final answer**

There are 96 leads currently in New Lead status.

**Execution time:** 12.728 sec
**Status:** ok

## 8. LAQ-008

**Question**

How many New Lead status leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS new_leads_created_in_period
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NEW_LEAD'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
```

**Generated final answer**

There were 92 leads in New Lead status created from 2026-04-01 to 2026-05-01.

**Execution time:** 13.722 sec
**Status:** ok

## 9. LAQ-012

**Question**

How many lost leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS lost_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'LOST';
```

**Generated final answer**

There are 62 lost leads.

**Execution time:** 9.463 sec
**Status:** ok

## 10. LAQ-011

**Question**

How many won leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS won_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'WON';
```

**Generated final answer**

There are 134 won leads.

**Execution time:** 10.996 sec
**Status:** ok

## 11. LAQ-013

**Question**

How many follow-up status leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS lead_count
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = :status_role;
```

**Generated final answer**

There are 46 leads in Follow Up status.

**Execution time:** 13.777 sec
**Status:** ok

## 12. LAQ-014

**Question**

How many appointment-booked leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointment_booked_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'APPOINTMENT_BOOKED';
```

**Generated final answer**

There are 37 appointment-booked leads.

**Execution time:** 11.648 sec
**Status:** ok

## 13. LAQ-015

**Question**

How many no-show leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS no_show_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NO_SHOW'
```

**Generated final answer**

There are 47 no-show leads.

**Execution time:** 11.580 sec
**Status:** ok

## 14. LAQ-016

**Question**

How many rescheduled leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS rescheduled_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = :status_role
```

**Generated final answer**

There are 22 rescheduled leads.

**Execution time:** 10.681 sec
**Status:** ok

## 15. LAQ-017

**Question**

How many canceled leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS canceled_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'CANCELED'
```

**Generated final answer**

There are 59 canceled leads.

**Execution time:** 10.238 sec
**Status:** ok

## 16. LAQ-018

**Question**

How many unqualified leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS unqualified_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'UNQUALIFIED';
```

**Generated final answer**

There are 10 unqualified leads.

**Execution time:** 12.575 sec
**Status:** ok

## 17. LAQ-009

**Question**

List leads that are currently in New Lead status.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NEW_LEAD'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching leads: 96

Showing the first 20 leads:

| Lead | Owner ID | Setter ID | Created at (UTC) |
|---|---|---|---|
| Ayman Andoh | Unassigned | No Setter | 2026-04-24 09:50 |
| Harun | Unassigned | No Setter | 2026-04-24 08:56 |
| Danko Bilbil | Unassigned | No Setter | 2026-04-23 10:57 |
| Piqueenmeta | Unassigned | No Setter | 2026-04-23 06:33 |
| Jason Stephenson | Unassigned | No Setter | 2026-04-23 06:29 |
| Lévy Fransen | Unassigned | No Setter | 2026-04-23 05:35 |
| Lusyane | Unassigned | `user_3AesMObeGeZynVoGhloMkfwanES` | 2026-04-23 02:50 |
| Kelvin springer | Unassigned | No Setter | 2026-04-22 18:56 |
| Jurgen de Hart | Unassigned | `user_3AesMObeGeZynVoGhloMkfwanES` | 2026-04-22 14:41 |
| Yassine Temsamani | Unassigned | No Setter | 2026-04-22 14:00 |
| Davy | Unassigned | No Setter | 2026-04-22 13:10 |
| Andrey | Unassigned | No Setter | 2026-04-22 11:25 |
| Martijn Baz | Unassigned | No Setter | 2026-04-22 11:25 |
| Claude Vande Velde | Unassigned | No Setter | 2026-04-22 08:33 |
| Decoster Chris | Unassigned | No Setter | 2026-04-22 07:55 |
| David Burgess | Unassigned | No Setter | 2026-04-22 07:55 |
| Frank Mennes | Unassigned | No Setter | 2026-04-22 07:55 |
| Floortje Niezen | Unassigned | No Setter | 2026-04-22 07:53 |
| Brandon Empey | Unassigned | No Setter | 2026-04-22 07:53 |
| Richard Peters van Nijenhof | Unassigned | No Setter | 2026-04-21 17:34 |

**Execution time:** 49.043 sec
**Status:** ok

## 18. LAQ-021

**Question**

How many lost leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS lost_leads_created_in_period
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'LOST'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

**Generated final answer**

There were 13 lost leads created from 2026-04-01 to 2026-05-01.

**Execution time:** 11.655 sec
**Status:** ok

## 19. LAQ-019

**Question**

How many partial-payment leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS partial_payment_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = :status_role;
```

**Generated final answer**

There are 2 partial-payment leads.

**Execution time:** 20.191 sec
**Status:** ok

## 20. LAQ-020

**Question**

How many won leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS won_leads_created_in_period
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'WON'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
```

**Generated final answer**

There were 44 won leads created from Apr 1, 2026 through May 1, 2026.

**Execution time:** 21.395 sec
**Status:** ok

## 21. LAQ-022

**Question**

How many appointment-booked leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS appointment_booked_leads_created_in_period
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'APPOINTMENT_BOOKED'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
```

**Generated final answer**

There were 33 appointment-booked leads created from 2026-04-01 to 2026-05-01.

**Execution time:** 19.655 sec
**Status:** ok

## 22. LAQ-010

**Question**

List New Lead status leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NEW_LEAD'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 92

Showing the first 20 New Lead status leads created from 2026-04-01 to 2026-05-01:

| Lead | Lead ID | Created At (UTC) | Setter |
|---|---|---|---|
| Ayman Andoh | b43745d5-4135-4cb0-a304-e78534eac70c | 2026-04-24 09:50 | No Setter |
| Harun | 5d8a588e-3964-4702-9f1c-f6722b73dd1a | 2026-04-24 08:56 | No Setter |
| Danko Bilbil | 9b3a62c3-3218-4c6d-ba78-fd078f4ad21c | 2026-04-23 10:57 | No Setter |
| Piqueenmeta | 7d7e5261-084b-46d6-a433-36ebee059cdb | 2026-04-23 06:33 | No Setter |
| Jason Stephenson | 15dcd297-0427-4318-a3c8-82eddbf46f20 | 2026-04-23 06:29 | No Setter |
| Lévy Fransen | c76ad746-a866-4646-984a-5df5edaea5ef | 2026-04-23 05:35 | No Setter |
| Lusyane | 7e10f737-c424-4b00-a8cf-8307aa9d7eb9 | 2026-04-23 02:50 | user_3AesMObeGeZynVoGhloMkfwanES |
| Kelvin springer | d58c7f53-5142-4c17-9ae2-521e79418aae | 2026-04-22 18:56 | No Setter |
| Jurgen de Hart | b41ea012-e5b8-4b94-8f97-71c195feabe9 | 2026-04-22 14:41 | user_3AesMObeGeZynVoGhloMkfwanES |
| Yassine Temsamani | f49c155f-c4b2-45b7-b3d8-4a079851a141 | 2026-04-22 14:00 | No Setter |
| Davy | 24de3e9f-500a-4be4-acf8-824c9e829517 | 2026-04-22 13:10 | No Setter |
| Andrey | 0471f24f-5922-47a2-ac13-10fba65a2f61 | 2026-04-22 11:25 | No Setter |
| Martijn Baz | 00a13d7e-9bc7-404c-a616-57860ecfd904 | 2026-04-22 11:25 | No Setter |
| Claude Vande Velde | fa97e049-7c4d-4cb0-80f6-f325dbd6e107 | 2026-04-22 08:33 | No Setter |
| Decoster Chris | d29582b0-d76a-42cb-8486-7b77dbca7114 | 2026-04-22 07:55 | No Setter |
| David Burgess | e9671c93-04da-49a7-bbba-c93e3f9cb814 | 2026-04-22 07:55 | No Setter |
| Frank Mennes | 485cacc6-4048-43fd-9442-ead188f64ff4 | 2026-04-22 07:55 | No Setter |
| Floortje Niezen | 700ed903-dcd6-4908-b0a0-da723edb62aa | 2026-04-22 07:53 | No Setter |
| Brandon Empey | 038dfbfc-8a50-460f-b1fa-07c02e216ef1 | 2026-04-22 07:53 | No Setter |
| Richard Peters van Nijenhof | 3dbe0409-ada5-4ba4-a2ad-2ad9b66ab3a5 | 2026-04-21 17:34 | No Setter |

**Execution time:** 65.738 sec
**Status:** ok

## 23. LAQ-024

**Question**

What is the lead breakdown by normalized pipeline role?

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY lead_count DESC, status_role ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the breakdown by normalized pipeline role:

| Pipeline role | Leads | % of total |
|---|---:|---:|
| Won | 134 | 26.02% |
| New Lead | 96 | 18.64% |
| Lost | 62 | 12.04% |
| Canceled | 59 | 11.46% |
| No Show | 47 | 9.13% |
| Follow Up | 46 | 8.93% |
| Appointment Booked | 37 | 7.18% |
| Rescheduled | 22 | 4.27% |
| Unqualified | 10 | 1.94% |
| Partial Payment | 2 | 0.39% |

**Execution time:** 17.432 sec
**Status:** ok

## 24. LAQ-025

**Question**

Show the lead count by exact pipeline status name.

**Generated SQL**

```sql
SELECT
  COALESCE(ss.name, 'No Status') AS status_name,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(ss.name, 'No Status')
ORDER BY lead_count DESC, status_name ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the breakdown by exact pipeline status name:

| Pipeline status | Lead count | % of total |
|---|---:|---:|
| Won | 134 | 26.02% |
| New Lead | 96 | 18.64% |
| No Sale - Lost | 62 | 12.04% |
| Canceled | 59 | 11.46% |
| No Show | 47 | 9.13% |
| No Sale - Follow Up | 46 | 8.93% |
| Call Booked | 37 | 7.18% |
| Rescheduled | 22 | 4.27% |
| No Sale - Unqualified | 10 | 1.94% |
| Deposit | 2 | 0.39% |

**Execution time:** 15.294 sec
**Status:** ok

## 25. LAQ-023

**Question**

How many no-show leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS no_show_leads_created_in_period
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NO_SHOW'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
```

**Generated final answer**

There were 22 no-show leads created from 2026-04-01 to 2026-05-01.

**Execution time:** 27.248 sec
**Status:** ok

## 26. LAQ-027

**Question**

Show exact status breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(ss.name, 'No Status') AS status_name,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY COALESCE(ss.name, 'No Status')
ORDER BY lead_count DESC, status_name ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the exact status breakdown for leads created from 2026-04-01 up to 2026-05-01:

| Status | Lead count | % of total |
|---|---:|---:|
| New Lead | 92 | 32.74% |
| Won | 44 | 15.66% |
| No Sale - Follow Up | 35 | 12.46% |
| Call Booked | 33 | 11.74% |
| Canceled | 26 | 9.25% |
| No Show | 22 | 7.83% |
| Rescheduled | 14 | 4.98% |
| No Sale - Lost | 13 | 4.63% |
| Deposit | 2 | 0.71% |

**Execution time:** 21.292 sec
**Status:** ok

## 27. LAQ-029

**Question**

Which exact status name has the most leads?

**Generated SQL**

```sql
WITH status_counts AS (
  SELECT
    COALESCE(ss.name, 'No Status') AS status_name,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY COALESCE(ss.name, 'No Status')
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM status_counts
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM status_counts
)
SELECT
  sc.status_name,
  sc.lead_count,
  t.total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM status_counts sc
CROSS JOIN max_count mc
CROSS JOIN total t
WHERE sc.lead_count = mc.max_lead_count
ORDER BY sc.status_name ASC;
```

**Generated final answer**

The exact status name with the most leads is Won: 134 leads, which is 26.02% of 515 total leads.

**Execution time:** 16.739 sec
**Status:** ok

## 28. LAQ-028

**Question**

Which pipeline role has the most leads?

**Generated SQL**

```sql
WITH role_counts AS (
  SELECT
    CAST(ss.role AS text) AS status_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role IS NOT NULL
  GROUP BY CAST(ss.role AS text)
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM role_counts
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM role_counts
)
SELECT
  rc.status_role,
  rc.lead_count,
  t.total_matching_leads,
  ROUND(rc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM role_counts rc
JOIN max_count mc
  ON rc.lead_count = mc.max_lead_count
CROSS JOIN total t
ORDER BY rc.status_role ASC;
```

**Generated final answer**

Won has the most leads: 134 out of 515 leads with a pipeline role (26.02%).

**Execution time:** 23.180 sec
**Status:** ok

## 29. LAQ-030

**Question**

List won leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'WON'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 134

Showing the first 20 records:

| Lead | Owner ID | Setter ID | Source | Created at |
|---|---|---|---|---|
| Chris Rouwhof | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-22 21:48 UTC |
| Jerry Vercammen | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-20 21:47 UTC |
| Dennis Schouten | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-20 13:35 UTC |
| Jeffrey Nussy | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-20 09:53 UTC |
| Raymond Keppel | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-20 07:34 UTC |
| Nico Siersma | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-19 07:24 UTC |
| Tori tori | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-16 22:50 UTC |
| Marek Macuk | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-16 11:47 UTC |
| Paul Jansen | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-15 21:53 UTC |
| Jan Van Dael | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-15 15:46 UTC |
| Jeroen Willemsen | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-14 16:47 UTC |
| Bart | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-14 16:39 UTC |
| Dennis Tullemans | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-14 08:12 UTC |
| Jan Mühleib | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-13 18:13 UTC |
| Jan Kraaijeveld | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-13 11:57 UTC |
| Catharina | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-12 16:00 UTC |
| Nick Jie-A-Joen | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-11 10:25 UTC |
| Sergio D'Alessandro | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-10 12:16 UTC |
| Fokko Kwant | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-10 09:15 UTC |
| Cor Coomans | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-10 08:18 UTC |

**Execution time:** 25.590 sec
**Status:** ok

## 30. LAQ-026

**Question**

Show pipeline role breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY lead_count DESC, status_role ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the pipeline role breakdown for leads created from Apr 1, 2026 to May 1, 2026:

| Pipeline role | Leads | % of total |
|---|---:|---:|
| New Lead | 92 | 32.74% |
| Won | 44 | 15.66% |
| Follow Up | 35 | 12.46% |
| Appointment Booked | 33 | 11.74% |
| Canceled | 26 | 9.25% |
| No Show | 22 | 7.83% |
| Rescheduled | 14 | 4.98% |
| Lost | 13 | 4.63% |
| Partial Payment | 2 | 0.71% |

**Execution time:** 41.977 sec
**Status:** ok

## 31. LAQ-031

**Question**

List lost leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'LOST'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 62

Showing the first 20 lost leads:

| Lead | Status | Owner ID | Setter ID | Source | Next touch point | Created at |
|---|---|---|---|---|---|---|
| Sandy | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | No setter | Other | — | 2026-04-20 |
| Bart D'heygere | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | No setter | Other | — | 2026-04-20 |
| Gabor koetse | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | `user_3AesMObeGeZynVoGhloMkfwanES` | Other | — | 2026-04-15 |
| Turan Ibrahim | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | No setter | Other | — | 2026-04-15 |
| Eugene Domatov | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | No setter | Other | — | 2026-04-15 |
| Boris Nedyalkov Nedyalkov | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | `user_3AesMObeGeZynVoGhloMkfwanES` | Other | — | 2026-04-14 |
| Michael de Block | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | No setter | Calendly | 2026-04-26 10:00 UTC | 2026-04-12 |
| Christian | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | No setter | Calendly | — | 2026-04-10 |
| Adrie Bos | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | `user_3AesMObeGeZynVoGhloMkfwanES` | Other | — | 2026-04-07 |
| Vincent Alberti | No Sale - Lost | Unassigned | No setter | Other | — | 2026-04-03 |
| Luc Koppers | No Sale - Lost | Unassigned | No setter | Other | — | 2026-04-03 |
| Ryan Pryde | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | No setter | Calendly | — | 2026-04-01 |
| Levy | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | `user_3AesMObeGeZynVoGhloMkfwanES` | Calendly | — | 2026-03-31 |
| Jurre Stip | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | `user_3AesMObeGeZynVoGhloMkfwanES` | Calendly | — | 2026-03-31 |
| Rens Van | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | `user_3AesMObeGeZynVoGhloMkfwanES` | Calendly | — | 2026-03-29 |
| Kim Maes | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | `user_3AesMObeGeZynVoGhloMkfwanES` | Calendly | — | 2026-03-27 |
| Johan Martens Martens | No Sale - Lost | `user_3ATRxXyN4j8bDHYJKRCEMAerasy` | `user_3AesMObeGeZynVoGhloMkfwanES` | Calendly | — | 2026-03-26 |
| Mehmet e | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | No setter | Other | — | 2026-03-26 |
| Liam Michiels | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | `user_3AesMObeGeZynVoGhloMkfwanES` | Calendly | — | 2026-03-26 |
| peter taylor | No Sale - Lost | `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` | No setter | Calendly | — | 2026-03-25 |

**Execution time:** 56.006 sec
**Status:** ok

## 32. LAQ-032

**Question**

List follow-up status leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'FOLLOW_UP'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 46

Showing the first 20 leads in Follow Up status:

| Lead | Status | Source | Next touch point | Created at |
|---|---|---|---|---|
| Tone veneman | No Sale - Follow Up | Other | — | 2026-04-22 18:43 UTC |
| Bob Schoutsen | No Sale - Follow Up | Other | — | 2026-04-22 17:35 UTC |
| Erik | No Sale - Follow Up | Calendly | — | 2026-04-22 07:24 UTC |
| olivier wijnen | No Sale - Follow Up | Calendly | — | 2026-04-22 05:41 UTC |
| Chris Van As | No Sale - Follow Up | Other | 2026-05-07 15:00 UTC | 2026-04-21 17:39 UTC |
| Rigo Nagels | No Sale - Follow Up | Other | — | 2026-04-21 14:19 UTC |
| Ron Richter | No Sale - Follow Up | Other | — | 2026-04-21 13:10 UTC |
| Balint Matys | No Sale - Follow Up | Other | — | 2026-04-21 07:27 UTC |
| Robin Lang | No Sale - Follow Up | Other | — | 2026-04-20 20:35 UTC |
| Brent Knudsen | No Sale - Follow Up | Other | — | 2026-04-20 15:28 UTC |
| Dirk Terpstra | No Sale - Follow Up | Other | — | 2026-04-20 14:57 UTC |
| Carolien Janzen | No Sale - Follow Up | Other | 2026-04-24 15:00 UTC | 2026-04-20 14:27 UTC |
| Maurice | No Sale - Follow Up | Other | — | 2026-04-20 13:36 UTC |
| P. Kok | No Sale - Follow Up | Other | 2026-04-27 09:00 UTC | 2026-04-20 11:43 UTC |
| Laurens | No Sale - Follow Up | Other | 2026-04-28 12:30 UTC | 2026-04-20 10:53 UTC |
| Onno Stillebroer | No Sale - Follow Up | Other | 2026-05-19 08:00 UTC | 2026-04-20 10:39 UTC |
| Matt A A | No Sale - Follow Up | Other | 2026-04-25 14:00 UTC | 2026-04-20 10:33 UTC |
| William | No Sale - Follow Up | Other | — | 2026-04-20 09:52 UTC |
| Joep Bergmans | No Sale - Follow Up | Other | 2026-04-24 15:00 UTC | 2026-04-20 08:45 UTC |
| Jan Simoens | No Sale - Follow Up | Other | — | 2026-04-20 07:44 UTC |

**Execution time:** 59.425 sec
**Status:** ok

## 33. LAQ-034

**Question**

List no-show leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'NO_SHOW'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total no-show leads: 47

Showing the first 20 no-show leads:

| Lead | Assigned to | Setter | Source | Created |
|---|---|---|---|---|
| Viliami Tuipulotu | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-22 |
| Ivan Gavel | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-22 |
| Gabe Real | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-21 |
| joseph | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-20 |
| Anthony Muone Muoneke | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-04-20 |
| Andres M | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-20 |
| Grace Kelly | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-16 |
| Alrun Ray Tokaay | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-16 |
| Ankush | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-16 |
| Javi Meijer | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-15 |
| Matthews Mokgosi | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-15 |
| Mohammad Tahir | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-14 |
| Olivier Sagata | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-13 |
| Sam monte | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-12 |
| Rakesh More | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-10 |
| David Chung | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-09 |
| Brahim Orchi | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-07 |
| EDGAR Adriano PEREIRA | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-07 |
| Laksh | Unassigned | No Setter | Other | 2026-04-05 |
| Cesar Molina | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-03 |

**Execution time:** 51.476 sec
**Status:** ok

## 34. LAQ-035

**Question**

List unqualified leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'UNQUALIFIED'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total unqualified leads: 10

Here is the complete list:

| Lead | Status | Source | Next touch point | Created at |
|---|---|---|---|---|
| Hubertus Bruekers | No Sale - Unqualified | Other | — | 26 Mar 2026 |
| Rebekka Demuynck | No Sale - Unqualified | Other | — | 26 Mar 2026 |
| Peggy-Ann Ruys | No Sale - Unqualified | Calendly | — | 20 Mar 2026 |
| Percy Hope | No Sale - Unqualified | Calendly | — | 20 Mar 2026 |
| sunny bathija | No Sale - Unqualified | Calendly | 04 Apr 2026 | 20 Mar 2026 |
| Rob | No Sale - Unqualified | Calendly | — | 17 Mar 2026 |
| Sam Timmers Timmers | No Sale - Unqualified | Calendly | — | 16 Mar 2026 |
| Tolga Ataç | No Sale - Unqualified | Calendly | — | 16 Mar 2026 |
| Demi Poortman Poortman | No Sale - Unqualified | Calendly | — | 13 Mar 2026 |
| Alannah A A | No Sale - Unqualified | Calendly | — | 08 Mar 2026 |

**Execution time:** 48.941 sec
**Status:** ok

## 35. LAQ-033

**Question**

List appointment-booked leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'APPOINTMENT_BOOKED'
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit
```

**Generated final answer**

Total matching leads: 37

These leads are currently marked as Appointment Booked.

Showing the first 20 records:

| Lead | Status | Assigned to ID | Setter ID | Source | Lead created at |
|---|---|---|---|---|---|
| Roos ’t Lam | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-24 08:10 UTC |
| Van der Veken Olivier | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-24 01:10 UTC |
| Erik Bakker | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-23 19:33 UTC |
| Bahadir | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-04-23 18:43 UTC |
| Aad Bouw | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-23 11:22 UTC |
| Steve Grainger | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-04-23 11:07 UTC |
| Nake Dragomirov | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-23 09:48 UTC |
| Issa Makhamreh | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-23 07:56 UTC |
| Erik van Hoof | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-23 07:43 UTC |
| Rene Solms | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-22 20:57 UTC |
| Zeb Oligschlager | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-22 18:37 UTC |
| Henry Stokkelaar | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-22 15:59 UTC |
| Pieter Zwartkruis | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-22 13:45 UTC |
| Peter Pavlisko | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-22 12:07 UTC |
| Sylvano van den Brink | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-22 11:25 UTC |
| Eugenio Jedi Martinez | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-22 09:26 UTC |
| Brigitte Pajonk | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-22 08:37 UTC |
| kris van rymenant | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-22 08:37 UTC |
| Robert Eduard | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-04-22 07:00 UTC |
| Jeroen van Teijlingen | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-21 17:53 UTC |

**Execution time:** 66.924 sec
**Status:** ok

## 36. LAQ-039

**Question**

Which source generated the most leads?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_counts
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM source_counts
)
SELECT
  sc.source,
  sc.lead_count,
  t.total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
JOIN max_count mc
  ON sc.lead_count = mc.max_lead_count
ORDER BY sc.source ASC;
```

**Generated final answer**

Using first-touch source, the largest source category is Unknown with 364 leads, representing 70.68% of 515 total leads.

**Execution time:** 20.819 sec
**Status:** ok

## 37. LAQ-040

**Question**

Show default lead source breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_counts
)
SELECT
  sc.source,
  sc.lead_count,
  t.total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.lead_count DESC, sc.source ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the default first-touch source breakdown:

| Source | Leads | % of total |
|---|---:|---:|
| Unknown | 136 | 48.40% |
| YouTube | 100 | 35.59% |
| Instagram | 24 | 8.54% |
| Other | 20 | 7.12% |
| Twitter / X | 1 | 0.36% |

**Execution time:** 18.292 sec
**Status:** ok

## 38. LAQ-038

**Question**

What is the default lead source breakdown?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_leads
  FROM source_counts
)
SELECT
  sc.source,
  sc.lead_count,
  t.total_leads AS total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.lead_count DESC, sc.source ASC;
```

**Generated final answer**

Total matching leads: 515

Using the default first-touch normalized lead source, here is the breakdown:

| Lead source | Leads | % of total |
|---|---:|---:|
| Unknown | 364 | 70.68% |
| YouTube | 103 | 20.00% |
| Instagram | 26 | 5.05% |
| Other | 21 | 4.08% |
| Twitter / X | 1 | 0.19% |

**Execution time:** 29.101 sec
**Status:** ok

## 39. LAQ-042

**Question**

Show the high-level lead source category breakdown.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(CAST(l.source AS text), 'Unknown')
ORDER BY lead_count DESC, source ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the high-level lead source category breakdown:

| Source category | Leads | % of total |
|---|---:|---:|
| Other | 265 | 51.46% |
| Calendly | 238 | 46.21% |
| Manual | 12 | 2.33% |

**Execution time:** 14.146 sec
**Status:** ok

## 40. LAQ-043

**Question**

Which high-level source category has the most leads?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(CAST(l.source AS text), 'Unknown') AS source_category,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY COALESCE(CAST(l.source AS text), 'Unknown')
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_counts
),
ranked AS (
  SELECT
    sc.source_category,
    sc.lead_count,
    t.total_matching_leads,
    ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total,
    DENSE_RANK() OVER (ORDER BY sc.lead_count DESC) AS lead_count_rank
  FROM source_counts sc
  CROSS JOIN total t
)
SELECT
  source_category,
  lead_count,
  total_matching_leads,
  percentage_of_total
FROM ranked
WHERE lead_count_rank = 1
ORDER BY source_category ASC;
```

**Generated final answer**

Out of 515 leads, the high-level source category with the most leads is Other, with 265 leads (51.46%).

**Execution time:** 20.142 sec
**Status:** ok

## 41. LAQ-036

**Question**

List won leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'WON'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 44

Showing the first 20 records:

| Lead | Created at |
|---|---|
| Chris Rouwhof | 2026-04-22 21:48 UTC |
| Jerry Vercammen | 2026-04-20 21:47 UTC |
| Dennis Schouten | 2026-04-20 13:35 UTC |
| Jeffrey Nussy | 2026-04-20 09:53 UTC |
| Raymond Keppel | 2026-04-20 07:34 UTC |
| Nico Siersma | 2026-04-19 07:24 UTC |
| Tori tori | 2026-04-16 22:50 UTC |
| Marek Macuk | 2026-04-16 11:47 UTC |
| Paul Jansen | 2026-04-15 21:53 UTC |
| Jan Van Dael | 2026-04-15 15:46 UTC |
| Jeroen Willemsen | 2026-04-14 16:47 UTC |
| Bart | 2026-04-14 16:39 UTC |
| Dennis Tullemans | 2026-04-14 08:12 UTC |
| Jan Mühleib | 2026-04-13 18:13 UTC |
| Jan Kraaijeveld | 2026-04-13 11:57 UTC |
| Catharina | 2026-04-12 16:00 UTC |
| Nick Jie-A-Joen | 2026-04-11 10:25 UTC |
| Sergio D'Alessandro | 2026-04-10 12:16 UTC |
| Fokko Kwant | 2026-04-10 09:15 UTC |
| Cor Coomans | 2026-04-10 08:18 UTC |

**Execution time:** 61.844 sec
**Status:** ok

## 42. LAQ-041

**Question**

Which source generated the most leads from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT COALESCE(SUM(lead_count), 0) AS total_matching_leads
  FROM source_counts
),
ranked_sources AS (
  SELECT
    sc.source,
    sc.lead_count,
    t.total_matching_leads,
    CASE
      WHEN t.total_matching_leads = 0 THEN NULL
      ELSE ROUND(sc.lead_count * 100.0 / t.total_matching_leads, 2)
    END AS percentage_of_total,
    DENSE_RANK() OVER (ORDER BY sc.lead_count DESC) AS source_rank
  FROM source_counts sc
  CROSS JOIN total t
)
SELECT
  rs.source,
  rs.lead_count,
  rs.total_matching_leads,
  rs.percentage_of_total
FROM ranked_sources rs
WHERE rs.source_rank = 1
ORDER BY rs.source ASC;
```

**Generated final answer**

From Apr 1 to May 1, 2026, the top lead source was Unknown, with 136 of 281 leads (48.40%).

**Execution time:** 35.591 sec
**Status:** ok

## 43. LAQ-044

**Question**

Show high-level source category breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(CAST(l.source AS text), 'Unknown') AS source_category,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY COALESCE(CAST(l.source AS text), 'Unknown')
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_counts
)
SELECT
  sc.source_category,
  sc.lead_count,
  t.total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.lead_count DESC, sc.source_category ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the breakdown for leads created from Apr 1, 2026 to May 1, 2026:

| Source category | Leads | % of total |
|---|---:|---:|
| Other | 254 | 90.39% |
| Calendly | 25 | 8.90% |
| Manual | 2 | 0.71% |

**Execution time:** 19.056 sec
**Status:** ok

## 44. LAQ-045

**Question**

How many leads came from Calendly source category?

**Generated SQL**

```sql
SELECT COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = :lead_source;
```

**Generated final answer**

There are 238 leads from the Calendly source category.

**Execution time:** 9.337 sec
**Status:** ok

## 45. LAQ-046

**Question**

How many leads came from Typeform source category?

**Generated SQL**

```sql
SELECT COUNT(*) AS typeform_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = 'TYPEFORM';
```

**Generated final answer**

There are 0 leads from the Typeform source category.

**Execution time:** 11.667 sec
**Status:** ok

## 46. LAQ-048

**Question**

How many manually created leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS manually_created_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = 'MANUAL';
```

**Generated final answer**

There are 12 manually created leads.

**Execution time:** 9.752 sec
**Status:** ok

## 47. LAQ-047

**Question**

How many leads came from landing page source category?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_from_landing_page
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = 'LANDING_PAGE';
```

**Generated final answer**

There are 0 leads from the Landing Page source category.

**Execution time:** 11.785 sec
**Status:** ok

## 48. LAQ-049

**Question**

How many webinar leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS webinar_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = :lead_source;
```

**Generated final answer**

There are 0 webinar leads.

**Execution time:** 12.079 sec
**Status:** ok

## 49. LAQ-050

**Question**

How many newsletter leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS newsletter_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = 'NEWSLETTER';
```

**Generated final answer**

There are 0 newsletter leads.

**Execution time:** 10.544 sec
**Status:** ok

## 50. LAQ-037

**Question**

List lost leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = 'LOST'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 13

Here is the complete list. Dates are shown in UTC.

| Lead | Source | Created at |
|---|---|---|
| Sandy | Other | 2026-04-20 11:10 UTC |
| Bart D'heygere | Other | 2026-04-20 08:19 UTC |
| Gabor koetse | Other | 2026-04-15 18:34 UTC |
| Turan Ibrahim | Other | 2026-04-15 06:45 UTC |
| Eugene Domatov | Other | 2026-04-15 05:30 UTC |
| Boris Nedyalkov Nedyalkov | Other | 2026-04-14 14:22 UTC |
| Michael de Block | Calendly | 2026-04-12 12:20 UTC |
| Christian | Calendly | 2026-04-10 05:27 UTC |
| Adrie Bos | Other | 2026-04-07 10:46 UTC |
| Vincent Alberti | Other | 2026-04-03 20:47 UTC |
| Luc Koppers | Other | 2026-04-03 06:46 UTC |
| Ryan Pryde | Calendly | 2026-04-01 15:28 UTC |
| Levy | Calendly | 2026-03-31 20:46 UTC |

**Execution time:** 84.336 sec
**Status:** ok

## 51. LAQ-051

**Question**

How many Calendly leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS calendly_leads_created_in_period
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = 'CALENDLY'
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

**Generated final answer**

There were 25 Calendly leads created in that period.

**Execution time:** 15.458 sec
**Status:** ok

## 52. LAQ-052

**Question**

How many Typeform leads were created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS typeform_leads_created
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND CAST(l.source AS text) = :lead_source
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

**Generated final answer**

There were 0 Typeform leads created from 2026-04-01 to 2026-05-01.

**Execution time:** 23.227 sec
**Status:** ok

## 53. LAQ-056

**Question**

Show normalized first-touch source distribution.

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_leads
  FROM source_counts
)
SELECT
  sc.source,
  sc.lead_count,
  t.total_leads AS total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.lead_count DESC, sc.source ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the normalized first-touch source distribution:

| Source | Leads | % of total |
|---|---:|---:|
| Unknown | 364 | 70.68% |
| YouTube | 103 | 20.00% |
| Instagram | 26 | 5.05% |
| Other | 21 | 4.08% |
| Twitter / X | 1 | 0.19% |

**Execution time:** 16.586 sec
**Status:** ok

## 54. LAQ-057

**Question**

Show normalized last-touch source distribution.

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(last_ms.name), ''),
      NULLIF(TRIM(l.last_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources last_ms
    ON last_ms.id = l.last_source_id
   AND last_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY COALESCE(
    NULLIF(TRIM(last_ms.name), ''),
    NULLIF(TRIM(l.last_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_counts
)
SELECT
  sc.source,
  sc.lead_count,
  t.total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.lead_count DESC, sc.source ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the normalized last-touch source distribution:

| Last-touch source | Leads | % of total |
|---|---:|---:|
| Unknown | 364 | 70.68% |
| YouTube | 103 | 20.00% |
| Instagram | 26 | 5.05% |
| Other | 21 | 4.08% |
| Twitter / X | 1 | 0.19% |

**Execution time:** 17.402 sec
**Status:** ok

## 55. LAQ-054

**Question**

List manually created leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = 'MANUAL'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching leads: 12

Here is the complete list:

| Lead | Status | Owner ID | Created at |
|---|---|---|---|
| David Verhaegen | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-04-01 07:56 UTC |
| Lilith Zwaan | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-04-01 07:54 UTC |
| test test | Call Booked | user_3ARuEgINlhhlbVsZYBbgBDeOEjr | 2026-03-28 09:45 UTC |
| Stan Vingerhoed | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-20 08:46 UTC |
| Andre Otten | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:35 UTC |
| Francois f | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:33 UTC |
| Kim Van den Ierssel | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:32 UTC |
| Armin hadziresic | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:30 UTC |
| Stan Van Dijck | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:27 UTC |
| Mitchel Falchou | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:25 UTC |
| Andre Diekhoff | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:16 UTC |
| Alexander Van dijkhuizen | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | 2026-03-12 21:01 UTC |

**Execution time:** 37.472 sec
**Status:** ok

## 56. LAQ-058

**Question**

Compare raw first source name and raw last source name combinations.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown') AS first_source_name,
  COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown') AS last_source_name,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY
  COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown'),
  COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, first_source_name ASC, last_source_name ASC;
```

**Generated final answer**

Total matching leads: 515

Most records are Unknown → Unknown, and nearly all leads have the same raw first and last source name.

| First source name | Last source name | Lead count | % of total |
|---|---|---:|---:|
| Unknown | Unknown | 364 | 70.68% |
| youtube | youtube | 84 | 16.31% |
| instagram | instagram | 22 | 4.27% |
| YouTube | YouTube | 19 | 3.69% |
| aff | aff | 16 | 3.11% |
| Instagram | Instagram | 4 | 0.78% |
| affiliate | affiliate | 3 | 0.58% |
| aff | affiliate | 1 | 0.19% |
| Other | Other | 1 | 0.19% |
| twitter | twitter | 1 | 0.19% |

**Execution time:** 19.451 sec
**Status:** ok

## 57. LAQ-060

**Question**

Show normalized first-touch source distribution from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_counts
)
SELECT
  sc.source,
  sc.lead_count,
  t.total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.lead_count DESC, sc.source ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the normalized first-touch source distribution for 2026-04-01 to 2026-05-01:

| First-touch source | Leads | % of total |
|---|---:|---:|
| Unknown | 136 | 48.40% |
| YouTube | 100 | 35.59% |
| Instagram | 24 | 8.54% |
| Other | 20 | 7.12% |
| Twitter / X | 1 | 0.36% |

**Execution time:** 19.966 sec
**Status:** ok

## 58. LAQ-053

**Question**

List Calendly source-category leads.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source_category,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND CAST(l.source AS text) = 'CALENDLY'
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 238

Showing the first 20 Calendly source-category leads (times in UTC):

| Lead | Status | Status category | Next touch point | Created at |
|---|---|---|---|---|
| Bahadir | Call Booked | Appointment Booked | — | 2026-04-23 18:43 |
| Steve Grainger | Call Booked | Appointment Booked | — | 2026-04-23 11:07 |
| Stephen William Bennett | Rescheduled | Rescheduled | — | 2026-04-22 20:28 |
| Erik | No Sale - Follow Up | Follow Up | — | 2026-04-22 07:24 |
| Robert Eduard | Call Booked | Appointment Booked | — | 2026-04-22 07:00 |
| olivier wijnen | No Sale - Follow Up | Follow Up | — | 2026-04-22 05:41 |
| Robert Voorn | Call Booked | Appointment Booked | — | 2026-04-21 06:41 |
| Anthony Muone Muoneke | No Show | No Show | — | 2026-04-20 09:55 |
| Michael de Block | No Sale - Lost | Lost | 2026-04-26 10:00 | 2026-04-12 12:20 |
| Chanida | No Sale - Follow Up | Follow Up | 2026-04-25 08:00 | 2026-04-11 09:47 |
| Christian | No Sale - Lost | Lost | — | 2026-04-10 05:27 |
| Yassin Oubihi | Won | Won | — | 2026-04-07 17:29 |
| Desiree | No Sale - Follow Up | Follow Up | — | 2026-04-06 05:32 |
| Ingmar De Stigter | Rescheduled | Rescheduled | — | 2026-04-05 20:50 |
| Adri Holzken | No Sale - Follow Up | Follow Up | 2026-04-06 11:03 | 2026-04-03 18:18 |
| Annette Busch | Won | Won | — | 2026-04-03 15:14 |
| Anton van Hoorn | No Show | No Show | — | 2026-04-03 12:47 |
| Tananwut Nantasoon | No Show | No Show | — | 2026-04-02 16:41 |
| Atal | Won | Won | — | 2026-04-02 16:00 |
| Marlow Warrington-Mattei | No Sale - Follow Up | Follow Up | — | 2026-04-02 13:11 |

**Execution time:** 60.582 sec
**Status:** ok

## 59. LAQ-059

**Question**

Which normalized last-touch source appears most often?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(last_ms.name), ''),
      NULLIF(TRIM(l.last_source_name), ''),
      'Unknown'
    ) AS normalized_last_touch_source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources last_ms
    ON last_ms.id = l.last_source_id
   AND last_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY COALESCE(
    NULLIF(TRIM(last_ms.name), ''),
    NULLIF(TRIM(l.last_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_counts
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM source_counts
)
SELECT
  sc.normalized_last_touch_source,
  sc.lead_count,
  t.total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
CROSS JOIN max_count mc
WHERE sc.lead_count = mc.max_lead_count
ORDER BY sc.normalized_last_touch_source ASC;
```

**Generated final answer**

The most common normalized last-touch source is Unknown, appearing on 364 of 515 leads (70.68%).

**Execution time:** 23.580 sec
**Status:** ok

## 60. LAQ-055

**Question**

List Calendly source-category leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = :lead_source
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 25

Showing the first 20 records:

| Lead | Status | Owner ID | Setter ID | Created at |
|---|---|---|---|---|
| Bahadir | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-23 18:43 UTC |
| Steve Grainger | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-23 11:07 UTC |
| Stephen William Bennett | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-22 20:28 UTC |
| Erik | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-22 07:24 UTC |
| Robert Eduard | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-22 07:00 UTC |
| olivier wijnen | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-22 05:41 UTC |
| Robert Voorn | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-21 06:41 UTC |
| Anthony Muone Muoneke | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-20 09:55 UTC |
| Michael de Block | No Sale - Lost | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-12 12:20 UTC |
| Chanida | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-11 09:47 UTC |
| Christian | No Sale - Lost | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-10 05:27 UTC |
| Yassin Oubihi | Won | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | 2026-04-07 17:29 UTC |
| Desiree | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-06 05:32 UTC |
| Ingmar De Stigter | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | 2026-04-05 20:50 UTC |
| Adri Holzken | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-03 18:18 UTC |
| Annette Busch | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-03 15:14 UTC |
| Anton van Hoorn | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-03 12:47 UTC |
| Tananwut Nantasoon | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-02 16:41 UTC |
| Atal | Won | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | 2026-04-02 16:00 UTC |
| Marlow Warrington-Mattei | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | 2026-04-02 13:11 UTC |

**Execution time:** 59.387 sec
**Status:** ok

## 61. LAQ-061

**Question**

Show normalized last-touch source distribution from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(last_ms.name), ''),
      NULLIF(TRIM(l.last_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources last_ms
    ON last_ms.id = l.last_source_id
   AND last_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY COALESCE(
    NULLIF(TRIM(last_ms.name), ''),
    NULLIF(TRIM(l.last_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lead_count) AS total_leads
  FROM source_counts
)
SELECT
  sc.source,
  sc.lead_count,
  t.total_leads AS total_matching_leads,
  ROUND(sc.lead_count * 100.0 / NULLIF(t.total_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.lead_count DESC, sc.source ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the normalized last-touch source distribution for the selected date range:

| Last-touch source | Leads | % of total |
|---|---:|---:|
| Unknown | 136 | 48.40% |
| YouTube | 100 | 35.59% |
| Instagram | 24 | 8.54% |
| Other | 20 | 7.12% |
| Twitter / X | 1 | 0.36% |

**Execution time:** 19.550 sec
**Status:** ok

## 62. LAQ-066

**Question**

Which high-level source category has the most no-show leads?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(CAST(l.source AS text), 'Unknown') AS source_category,
    COUNT(*) AS no_show_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'NO_SHOW'
  GROUP BY COALESCE(CAST(l.source AS text), 'Unknown')
),
max_count AS (
  SELECT MAX(no_show_lead_count) AS max_no_show_lead_count
  FROM source_counts
),
total AS (
  SELECT SUM(no_show_lead_count) AS total_matching_leads
  FROM source_counts
)
SELECT
  sc.source_category,
  sc.no_show_lead_count,
  t.total_matching_leads,
  ROUND(sc.no_show_lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
JOIN max_count mc
  ON sc.no_show_lead_count = mc.max_no_show_lead_count
CROSS JOIN total t
ORDER BY sc.source_category ASC;
```

**Generated final answer**

Calendly has the most no-show leads, with 28 out of 47 total no-show leads (59.57%).

**Execution time:** 19.759 sec
**Status:** ok

## 63. LAQ-064

**Question**

Which first-touch source has the most lost leads?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lost_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'LOST'
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(lost_lead_count) AS total_matching_leads
  FROM source_counts
),
max_count AS (
  SELECT MAX(lost_lead_count) AS max_lost_lead_count
  FROM source_counts
)
SELECT
  sc.source,
  sc.lost_lead_count,
  t.total_matching_leads,
  ROUND(sc.lost_lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
CROSS JOIN max_count mc
WHERE sc.lost_lead_count = mc.max_lost_lead_count
ORDER BY sc.source ASC;
```

**Generated final answer**

The first-touch source with the most lost leads is Unknown, with 57 of 62 total lost leads (91.94%).

**Execution time:** 26.274 sec
**Status:** ok

## 64. LAQ-063

**Question**

Which first-touch source has the most won leads?

**Generated SQL**

```sql
WITH won_source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS first_touch_source,
    COUNT(*) AS won_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'WON'
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
max_count AS (
  SELECT
    MAX(won_lead_count) AS max_won_lead_count,
    SUM(won_lead_count) AS total_matching_won_leads
  FROM won_source_counts
)
SELECT
  wsc.first_touch_source,
  wsc.won_lead_count,
  mc.total_matching_won_leads,
  ROUND(wsc.won_lead_count * 100.0 / NULLIF(mc.total_matching_won_leads, 0), 2) AS percentage_of_total_won_leads
FROM won_source_counts wsc
JOIN max_count mc
  ON wsc.won_lead_count = mc.max_won_lead_count
ORDER BY wsc.first_touch_source ASC;
```

**Generated final answer**

Out of 134 won leads, the largest first-touch source bucket is Unknown, with 111 won leads (82.84%).

**Execution time:** 29.415 sec
**Status:** ok

## 65. LAQ-065

**Question**

Which first-touch source has the most follow-up status leads?

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS first_touch_source,
    COUNT(*) AS follow_up_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'FOLLOW_UP'
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(follow_up_lead_count) AS total_matching_leads
  FROM source_counts
),
max_count AS (
  SELECT MAX(follow_up_lead_count) AS max_follow_up_lead_count
  FROM source_counts
)
SELECT
  sc.first_touch_source,
  sc.follow_up_lead_count,
  t.total_matching_leads,
  ROUND(sc.follow_up_lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_follow_up_leads
FROM source_counts sc
CROSS JOIN total t
JOIN max_count mc
  ON sc.follow_up_lead_count = mc.max_follow_up_lead_count
ORDER BY sc.first_touch_source ASC;
```

**Generated final answer**

Among leads in Follow Up status, the top first-touch source is Unknown with 29 leads, representing 63.04% of the 46 matching leads.

**Execution time:** 28.053 sec
**Status:** ok

## 66. LAQ-068

**Question**

How many leads have no owner assigned?

**Generated SQL**

```sql
SELECT COUNT(*) AS unassigned_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.assigned_to), '') IS NULL;
```

**Generated final answer**

There are 105 leads with no owner assigned.

**Execution time:** 9.216 sec
**Status:** ok

## 67. LAQ-062

**Question**

Show lead count by first-touch source and pipeline role.

**Generated SQL**

```sql
WITH source_role_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS first_touch_source,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ),
    COALESCE(CAST(ss.role AS text), 'NO_STATUS')
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM source_role_counts
)
SELECT
  src.first_touch_source,
  src.pipeline_role,
  src.lead_count,
  t.total_matching_leads,
  ROUND(src.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_role_counts src
CROSS JOIN total t
ORDER BY src.first_touch_source ASC, src.lead_count DESC, src.pipeline_role ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the breakdown by first-touch source and pipeline role:

| First-touch source | Pipeline role | Lead count | % of total |
|---|---|---:|---:|
| Instagram | Won | 7 | 1.36% |
| Instagram | New Lead | 6 | 1.17% |
| Instagram | Appointment Booked | 5 | 0.97% |
| Instagram | Follow Up | 2 | 0.39% |
| Instagram | Lost | 2 | 0.39% |
| Instagram | Rescheduled | 2 | 0.39% |
| Instagram | Canceled | 1 | 0.19% |
| Instagram | No Show | 1 | 0.19% |
| Other | New Lead | 9 | 1.75% |
| Other | No Show | 4 | 0.78% |
| Other | Won | 3 | 0.58% |
| Other | Rescheduled | 2 | 0.39% |
| Other | Appointment Booked | 1 | 0.19% |
| Other | Canceled | 1 | 0.19% |
| Other | Follow Up | 1 | 0.19% |
| Twitter / X | No Show | 1 | 0.19% |
| Unknown | Won | 111 | 21.55% |
| Unknown | Lost | 57 | 11.07% |
| Unknown | Canceled | 49 | 8.54% |
| Unknown | New Lead | 44 | 9.51% |

**Execution time:** 41.460 sec
**Status:** ok

## 68. LAQ-070

**Question**

Show lead count by owner ID.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS owner_id,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned')
ORDER BY lead_count DESC, owner_id ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the breakdown by owner ID:

| Owner ID | Lead count | % of total |
|---|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 234 | 45.44% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 174 | 33.79% |
| Unassigned | 105 | 20.39% |
| user_3ARuEgINlhhlbVsZYBbgBDeOEjr | 1 | 0.19% |
| user_3BTfkOX7RajuoxhqwX7nMytxEmM | 1 | 0.19% |

**Execution time:** 16.117 sec
**Status:** ok

## 69. LAQ-071

**Question**

Which owner ID has the most assigned leads?

**Generated SQL**

```sql
WITH owner_counts AS (
  SELECT
    NULLIF(TRIM(l.assigned_to), '') AS owner_id,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.assigned_to), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(l.assigned_to), '')
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM owner_counts
)
SELECT
  oc.owner_id,
  oc.lead_count
FROM owner_counts oc
JOIN max_count mc
  ON oc.lead_count = mc.max_lead_count
ORDER BY oc.owner_id ASC;
```

**Generated final answer**

Owner ID `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` has the most assigned leads, with 234 leads.

**Execution time:** 13.321 sec
**Status:** ok

## 70. LAQ-072

**Question**

Show owner assignment breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned')
ORDER BY lead_count DESC, assigned_to ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the owner assignment breakdown for leads created from 2026-04-01 to 2026-05-01:

| Owner ID | Lead count | % of total |
|---|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 112 | 39.86% |
| Unassigned | 100 | 35.59% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 69 | 24.56% |

**Execution time:** 15.995 sec
**Status:** ok

## 71. LAQ-073

**Question**

How many leads created from 2026-04-01 to 2026-05-01 have no owner assigned?

**Generated SQL**

```sql
SELECT COUNT(*) AS unassigned_leads_created_in_period
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.assigned_to), '') IS NULL
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

**Generated final answer**

There are 100 leads created from 2026-04-01 to 2026-05-01 with no owner assigned.

**Execution time:** 15.180 sec
**Status:** ok

## 72. LAQ-069

**Question**

List leads with no owner assigned.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.assigned_to), '') IS NULL
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

Total unassigned leads: 105

Showing the first 20 records:

| Lead | Current status | Created at |
|---|---|---|
| Ayman Andoh | New Lead | 2026-04-24 09:50 UTC |
| Harun | New Lead | 2026-04-24 08:56 UTC |
| Danko Bilbil | New Lead | 2026-04-23 10:57 UTC |
| Piqueenmeta | New Lead | 2026-04-23 06:33 UTC |
| Jason Stephenson | New Lead | 2026-04-23 06:29 UTC |
| Lévy Fransen | New Lead | 2026-04-23 05:35 UTC |
| Lusyane | New Lead | 2026-04-23 02:50 UTC |
| Kelvin springer | New Lead | 2026-04-22 18:56 UTC |
| Jurgen de Hart | New Lead | 2026-04-22 14:41 UTC |
| Yassine Temsamani | New Lead | 2026-04-22 14:00 UTC |
| Davy | New Lead | 2026-04-22 13:10 UTC |
| Andrey | New Lead | 2026-04-22 11:25 UTC |
| Martijn Baz | New Lead | 2026-04-22 11:25 UTC |
| Claude Vande Velde | New Lead | 2026-04-22 08:33 UTC |
| Decoster Chris | New Lead | 2026-04-22 07:55 UTC |
| David Burgess | New Lead | 2026-04-22 07:55 UTC |
| Frank Mennes | New Lead | 2026-04-22 07:55 UTC |
| Floortje Niezen | New Lead | 2026-04-22 07:53 UTC |
| Brandon Empey | New Lead | 2026-04-22 07:53 UTC |
| Richard Peters van Nijenhof | New Lead | 2026-04-21 17:34 UTC |

**Execution time:** 43.411 sec
**Status:** ok

## 73. LAQ-075

**Question**

Which owner ID has the most won leads?

**Generated SQL**

```sql
WITH owner_counts AS (
  SELECT
    NULLIF(TRIM(l.assigned_to), '') AS owner_id,
    COUNT(*) AS won_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.assigned_to), '') IS NOT NULL
    AND ss.role = 'WON'
  GROUP BY NULLIF(TRIM(l.assigned_to), '')
),
max_count AS (
  SELECT MAX(won_lead_count) AS max_won_lead_count
  FROM owner_counts
)
SELECT
  oc.owner_id,
  oc.won_lead_count
FROM owner_counts oc
JOIN max_count mc
  ON oc.won_lead_count = mc.max_won_lead_count
ORDER BY oc.owner_id ASC;
```

**Generated final answer**

The owner ID with the most won leads is `user_3AZPWYViL4vUfqNXmNLhNcYAwX4`, with 79 won leads.

**Execution time:** 21.473 sec
**Status:** ok

## 74. LAQ-076

**Question**

Which owner ID has the most lost leads?

**Generated SQL**

```sql
WITH owner_lost_counts AS (
  SELECT
    NULLIF(TRIM(l.assigned_to), '') AS owner_id,
    COUNT(*) AS lost_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'LOST'
    AND NULLIF(TRIM(l.assigned_to), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(l.assigned_to), '')
),
max_count AS (
  SELECT MAX(lost_lead_count) AS max_lost_lead_count
  FROM owner_lost_counts
),
total AS (
  SELECT COALESCE(SUM(lost_lead_count), 0) AS total_matching_leads
  FROM owner_lost_counts
)
SELECT
  olc.owner_id,
  olc.lost_lead_count,
  t.total_matching_leads
FROM owner_lost_counts olc
JOIN max_count mc
  ON olc.lost_lead_count = mc.max_lost_lead_count
CROSS JOIN total t
ORDER BY olc.owner_id ASC;
```

**Generated final answer**

Out of 60 lost leads with an assigned owner, owner ID `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` has the most, with 36 lost leads.

**Execution time:** 23.873 sec
**Status:** ok

## 75. LAQ-077

**Question**

Which owner ID has the most follow-up status leads?

**Generated SQL**

```sql
WITH owner_counts AS (
  SELECT
    NULLIF(TRIM(l.assigned_to), '') AS owner_id,
    COUNT(*) AS follow_up_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'FOLLOW_UP'
    AND NULLIF(TRIM(l.assigned_to), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(l.assigned_to), '')
),
max_count AS (
  SELECT MAX(follow_up_lead_count) AS max_follow_up_lead_count
  FROM owner_counts
)
SELECT
  oc.owner_id,
  oc.follow_up_lead_count
FROM owner_counts oc
JOIN max_count mc
  ON oc.follow_up_lead_count = mc.max_follow_up_lead_count
ORDER BY oc.owner_id ASC;
```

**Generated final answer**

The owner ID with the most Follow Up status leads is `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` with 24 leads.

**Execution time:** 17.402 sec
**Status:** ok

## 76. LAQ-080

**Question**

How many leads have no setter assigned?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_without_setter
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.setter_id), '') IS NULL;
```

**Generated final answer**

There are 405 leads with no setter assigned.

**Execution time:** 7.888 sec
**Status:** ok

## 77. LAQ-078

**Question**

Which owner ID has the most leads needing operational follow-up?

**Generated SQL**

```sql
WITH owner_counts AS (
  SELECT
    NULLIF(TRIM(l.assigned_to), '') AS owner_id,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.assigned_to), '') IS NOT NULL
    AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
      'WON',
      'LOST',
      'UNQUALIFIED',
      'CANCELED'
    )
    AND (
      l.next_touch_point_at IS NULL
      OR l.next_touch_point_at < NOW()
    )
  GROUP BY NULLIF(TRIM(l.assigned_to), '')
),
totals AS (
  SELECT
    SUM(lead_count) AS total_matching_leads,
    MAX(lead_count) AS max_lead_count
  FROM owner_counts
)
SELECT
  oc.owner_id,
  oc.lead_count,
  t.total_matching_leads,
  ROUND(oc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM owner_counts oc
CROSS JOIN totals t
WHERE oc.lead_count = t.max_lead_count
ORDER BY oc.owner_id ASC;
```

**Generated final answer**

Among assigned owners, owner ID `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` has the most leads needing operational follow-up with 86 leads, representing 57.72% of the 149 assigned leads currently needing follow-up.

**Execution time:** 23.911 sec
**Status:** ok

## 78. LAQ-082

**Question**

Show lead count by setter ID.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter')
ORDER BY lead_count DESC, setter_id ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the breakdown:

| Setter ID | Lead Count | % of total |
|---|---:|---:|
| No Setter | 405 | 78.64% |
| user_3AesMObeGeZynVoGhloMkfwanES | 108 | 20.97% |
| user_3AZfvBICuFGTCNu4QeqiP6xN03Q | 2 | 0.39% |

**Execution time:** 13.466 sec
**Status:** ok

## 79. LAQ-074

**Question**

Show lead count by owner ID and pipeline role.

**Generated SQL**

```sql
WITH grouped AS (
  SELECT
    COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS owner_id,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY
    COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned'),
    COALESCE(CAST(ss.role AS text), 'NO_STATUS')
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM grouped
)
SELECT
  t.total_matching_leads,
  JSON_AGG(
    JSON_BUILD_OBJECT(
      'owner_id', g.owner_id,
      'pipeline_role', g.pipeline_role,
      'lead_count', g.lead_count,
      'percentage_of_total', ROUND(g.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2)
    )
    ORDER BY g.owner_id ASC, g.lead_count DESC, g.pipeline_role ASC
  ) AS breakdown
FROM grouped g
CROSS JOIN total t
GROUP BY t.total_matching_leads;
```

**Generated final answer**

Total matching leads: 515

Here is the breakdown by owner ID and pipeline role:

| Owner ID | Pipeline Role | Lead Count | % of total |
|---|---|---:|---:|
| Unassigned | New Lead | 96 | 18.64% |
| Unassigned | Canceled | 3 | 0.58% |
| Unassigned | Lost | 2 | 0.39% |
| Unassigned | Follow Up | 1 | 0.19% |
| Unassigned | No Show | 1 | 0.19% |
| Unassigned | Rescheduled | 1 | 0.19% |
| Unassigned | Unqualified | 1 | 0.19% |
| user_3ARuEgINlhhlbVsZYBbgBDeOEjr | Appointment Booked | 1 | 0.19% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Won | 54 | 10.49% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Canceled | 27 | 5.24% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Lost | 24 | 4.66% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Show | 23 | 4.47% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Follow Up | 21 | 4.08% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Appointment Booked | 12 | 2.33% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Rescheduled | 7 | 1.36% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Unqualified | 6 | 1.17% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Won | 79 | 15.34% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Lost | 36 | 6.99% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Canceled | 29 | 5.63% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Appointment Booked | 24 | 4.66% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Follow Up | 24 | 4.66% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Show | 23 | 4.47% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Rescheduled | 14 | 2.72% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Unqualified | 3 | 0.58% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Partial Payment | 2 | 0.39% |
| user_3BTfkOX7RajuoxhqwX7nMytxEmM | Won | 1 | 0.19% |

**Execution time:** 70.534 sec
**Status:** ok

## 80. LAQ-083

**Question**

Which setter ID has the most leads?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(l.setter_id), '') AS setter_id,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(l.setter_id), '')
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.lead_count
FROM setter_counts sc
JOIN max_count mc
  ON sc.lead_count = mc.max_lead_count
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

The setter ID with the most leads is `user_3AesMObeGeZynVoGhloMkfwanES` with 108 leads.

**Execution time:** 10.840 sec
**Status:** ok

## 81. LAQ-081

**Question**

List leads with no setter assigned.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.setter_id), '') IS NULL
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total leads with no setter assigned: 405

Showing the first 20 records:

| Lead | Status | Source | Created at |
|---|---|---|---|
| Ayman Andoh | New Lead | Other | 2026-04-24 09:50 UTC |
| Harun | New Lead | Other | 2026-04-24 08:56 UTC |
| Roos ‘t Lam | Call Booked | Other | 2026-04-24 08:10 UTC |
| Van der Veken Olivier | Call Booked | Other | 2026-04-24 01:10 UTC |
| Erik Bakker | Call Booked | Other | 2026-04-23 19:33 UTC |
| Bahadir | Call Booked | Calendly | 2026-04-23 18:43 UTC |
| Kale green | Canceled | Other | 2026-04-23 18:41 UTC |
| Steve Grainger | Call Booked | Calendly | 2026-04-23 11:07 UTC |
| Danko Bilbil | New Lead | Other | 2026-04-23 10:57 UTC |
| Nake Dragomirov | Call Booked | Other | 2026-04-23 09:48 UTC |
| Issa Makhamreh | Call Booked | Other | 2026-04-23 07:56 UTC |
| Erik van Hoof | Call Booked | Other | 2026-04-23 07:43 UTC |
| Piqueenmeta | New Lead | Other | 2026-04-23 06:33 UTC |
| Jason Stephenson | New Lead | Other | 2026-04-23 06:29 UTC |
| Lévy Fransen | New Lead | Other | 2026-04-23 05:35 UTC |
| Chris Rouwhof | Won | Other | 2026-04-22 21:48 UTC |
| Rene Solms | Call Booked | Other | 2026-04-22 20:57 UTC |
| Stephen William Bennett | Rescheduled | Calendly | 2026-04-22 20:28 UTC |
| Kelvin springer | New Lead | Other | 2026-04-22 18:56 UTC |
| Tone veneman | No Sale - Follow Up | Other | 2026-04-22 18:43 UTC |

**Execution time:** 37.263 sec
**Status:** ok

## 82. LAQ-085

**Question**

How many leads created from 2026-04-01 to 2026-05-01 have no setter assigned?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_without_setter
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
  AND NULLIF(TRIM(l.setter_id), '') IS NULL
```

**Generated final answer**

There are 236 leads created from 2026-04-01 to 2026-05-01 with no setter assigned.

**Execution time:** 12.416 sec
**Status:** ok

## 83. LAQ-084

**Question**

Show setter breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter')
ORDER BY lead_count DESC, setter_id ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the setter breakdown for leads created from 2026-04-01 to 2026-05-01:

| Setter | Leads | % of total |
|---|---:|---:|
| No Setter | 236 | 83.99% |
| user_3AesMObeGeZynVoGhloMkfwanES | 45 | 16.01% |

**Execution time:** 24.358 sec
**Status:** ok

## 84. LAQ-088

**Question**

Which setter ID has the most appointment-booked leads?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(l.setter_id), '') AS setter_id,
    COUNT(*) AS appointment_booked_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.setter_id), '') IS NOT NULL
    AND ss.role = 'APPOINTMENT_BOOKED'
  GROUP BY NULLIF(TRIM(l.setter_id), '')
),
max_count AS (
  SELECT MAX(appointment_booked_lead_count) AS max_appointment_booked_lead_count
  FROM setter_counts
),
total AS (
  SELECT SUM(appointment_booked_lead_count) AS total_matching_leads
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.appointment_booked_lead_count,
  t.total_matching_leads,
  ROUND(sc.appointment_booked_lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM setter_counts sc
JOIN max_count mc
  ON sc.appointment_booked_lead_count = mc.max_appointment_booked_lead_count
CROSS JOIN total t
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

Out of 8 appointment-booked leads with a setter ID, `user_3AesMObeGeZynVoGhloMkfwanES` has the most with 7 leads (87.50%).

**Execution time:** 20.269 sec
**Status:** ok

## 85. LAQ-087

**Question**

Which setter ID has the most won leads?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(l.setter_id), '') AS setter_id,
    COUNT(*) AS won_lead_count
  FROM leads l
  JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.setter_id), '') IS NOT NULL
    AND ss.role = 'WON'
  GROUP BY NULLIF(TRIM(l.setter_id), '')
), stats AS (
  SELECT
    MAX(won_lead_count) AS max_won_lead_count,
    SUM(won_lead_count) AS total_matching_won_leads
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.won_lead_count,
  s.total_matching_won_leads,
  ROUND(sc.won_lead_count * 100.0 / NULLIF(s.total_matching_won_leads, 0), 2) AS percentage_of_total_won_leads
FROM setter_counts sc
CROSS JOIN stats s
WHERE sc.won_lead_count = s.max_won_lead_count
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

Among won leads with a setter ID, `user_3AesMObeGeZynVoGhloMkfwanES` has the most: 41 out of 42 won leads (97.62%).

**Execution time:** 30.885 sec
**Status:** ok

## 86. LAQ-089

**Question**

Which setter ID has the most lost leads?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(l.setter_id), '') AS setter_id,
    COUNT(*) AS lost_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.setter_id), '') IS NOT NULL
    AND ss.role = 'LOST'
  GROUP BY NULLIF(TRIM(l.setter_id), '')
),
max_count AS (
  SELECT MAX(lost_lead_count) AS max_lost_lead_count
  FROM setter_counts
),
total AS (
  SELECT SUM(lost_lead_count) AS total_matching_leads
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.lost_lead_count,
  t.total_matching_leads,
  ROUND(sc.lost_lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM setter_counts sc
JOIN max_count mc
  ON sc.lost_lead_count = mc.max_lost_lead_count
CROSS JOIN total t
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

Out of 19 lost leads with a setter ID recorded, setter ID `user_3AesMObeGeZynVoGhloMkfwanES` has the most with 19 lost leads (100.00%).

**Execution time:** 23.033 sec
**Status:** ok

## 87. LAQ-090

**Question**

Which setter ID has the most leads needing operational follow-up?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(l.setter_id), '') AS setter_id,
    COUNT(*) AS leads_needing_operational_follow_up
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.setter_id), '') IS NOT NULL
    AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
      'WON',
      'LOST',
      'UNQUALIFIED',
      'CANCELED'
    )
    AND (
      l.next_touch_point_at IS NULL
      OR l.next_touch_point_at < NOW()
    )
  GROUP BY NULLIF(TRIM(l.setter_id), '')
),
max_count AS (
  SELECT MAX(leads_needing_operational_follow_up) AS max_lead_count
  FROM setter_counts
),
total AS (
  SELECT SUM(leads_needing_operational_follow_up) AS total_matching_leads
  FROM setter_counts
)
SELECT
  sc.setter_id,
  sc.leads_needing_operational_follow_up,
  t.total_matching_leads,
  ROUND(
    sc.leads_needing_operational_follow_up * 100.0 / NULLIF(t.total_matching_leads, 0),
    2
  ) AS percentage_of_total
FROM setter_counts sc
JOIN max_count mc
  ON sc.leads_needing_operational_follow_up = mc.max_lead_count
CROSS JOIN total t
ORDER BY sc.setter_id ASC;
```

**Generated final answer**

Among leads needing operational follow-up with a setter ID, `user_3AesMObeGeZynVoGhloMkfwanES` has the most: 34 of 35 leads (97.14%).

**Execution time:** 20.219 sec
**Status:** ok

## 88. LAQ-067

**Question**

Show first-touch source and pipeline role breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH filtered_leads AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS first_touch_source,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= CAST(:start_date AS date)
    AND l.created_at < (CAST(:end_date AS date) + INTERVAL '1 day')
),
source_breakdown AS (
  SELECT
    first_touch_source,
    COUNT(*) AS source_total_leads,
    COUNT(*) FILTER (WHERE pipeline_role = 'NEW_LEAD') AS new_lead,
    COUNT(*) FILTER (WHERE pipeline_role = 'APPOINTMENT_BOOKED') AS appointment_booked,
    COUNT(*) FILTER (WHERE pipeline_role = 'NO_SHOW') AS no_show,
    COUNT(*) FILTER (WHERE pipeline_role = 'RESCHEDULED') AS rescheduled,
    COUNT(*) FILTER (WHERE pipeline_role = 'CANCELED') AS canceled,
    COUNT(*) FILTER (WHERE pipeline_role = 'PARTIAL_PAYMENT') AS partial_payment,
    COUNT(*) FILTER (WHERE pipeline_role = 'WON') AS won,
    COUNT(*) FILTER (WHERE pipeline_role = 'UNQUALIFIED') AS unqualified,
    COUNT(*) FILTER (WHERE pipeline_role = 'FOLLOW_UP') AS follow_up,
    COUNT(*) FILTER (WHERE pipeline_role = 'LOST') AS lost,
    COUNT(*) FILTER (WHERE pipeline_role = 'NO_STATUS') AS no_status
  FROM filtered_leads
  GROUP BY first_touch_source
)
SELECT
  first_touch_source,
  source_total_leads,
  SUM(source_total_leads) OVER() AS total_matching_leads,
  ROUND(source_total_leads * 100.0 / NULLIF(SUM(source_total_leads) OVER(), 0), 2) AS percentage_of_total,
  new_lead,
  appointment_booked,
  no_show,
  rescheduled,
  canceled,
  partial_payment,
  won,
  unqualified,
  follow_up,
  lost,
  no_status
FROM source_breakdown
ORDER BY source_total_leads DESC, first_touch_source ASC
```

**Generated final answer**

Total matching leads: 281

For leads created from 2026-04-01 through 2026-05-01, Unknown was the largest first-touch source, followed by YouTube.

| First-touch source | Total leads | % of total | New Lead | Appointment Booked | No Show | Rescheduled | Canceled | Follow Up | Won | Lost | Partial Payment |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Unknown | 136 | 48.40% | 40 | 9 | 10 | 9 | 18 | 18 | 24 | 8 | 0 |
| YouTube | 100 | 35.59% | 37 | 18 | 6 | 1 | 7 | 14 | 12 | 3 | 2 |
| Instagram | 24 | 8.54% | 6 | 5 | 1 | 2 | 1 | 2 | 5 | 2 | 0 |
| Other | 20 | 7.12% | 9 | 1 | 4 | 2 | 0 | 1 | 3 | 0 | 0 |
| Twitter / X | 1 | 0.36% | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |

Unqualified and No Status were 0 across all sources in this period.

**Execution time:** 175.918 sec
**Status:** ok

## 89. LAQ-092

**Question**

How many leads need operational follow-up?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_needing_operational_follow_up
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  );
```

**Generated final answer**

There are 248 leads that need operational follow-up.

**Execution time:** 16.526 sec
**Status:** ok

## 90. LAQ-094

**Question**

How many leads have overdue next touch points?

**Generated SQL**

```sql
SELECT COUNT(*) AS overdue_next_touch_points
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND l.next_touch_point_at IS NOT NULL
  AND l.next_touch_point_at < NOW();
```

**Generated final answer**

There are 18 leads with overdue next touch points.

**Execution time:** 10.943 sec
**Status:** ok

## 91. LAQ-079

**Question**

Show owner and pipeline role breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH grouped AS (
  SELECT
    COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned'),
    COALESCE(CAST(ss.role AS text), 'NO_STATUS')
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM grouped
)
SELECT
  t.total_matching_leads,
  JSON_AGG(
    JSON_BUILD_OBJECT(
      'assigned_to', g.assigned_to,
      'status_role', g.status_role,
      'lead_count', g.lead_count,
      'percentage_of_total', ROUND(g.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2)
    )
    ORDER BY g.lead_count DESC, g.assigned_to ASC, g.status_role ASC
  ) AS breakdown
FROM grouped g
CROSS JOIN total t
GROUP BY t.total_matching_leads;
```

**Generated final answer**

Total matching leads: 281

The largest segment in the requested range was unassigned new leads.

| Owner ID | Pipeline role | Count | % of total |
|---|---|---:|---:|
| Unassigned | New Lead | 92 | 32.74% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Won | 30 | 10.68% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Appointment Booked | 21 | 7.47% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Follow Up | 18 | 6.41% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Follow Up | 16 | 5.69% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Won | 14 | 4.98% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Canceled | 14 | 4.98% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Show | 14 | 4.98% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Appointment Booked | 12 | 4.27% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Canceled | 9 | 3.20% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Rescheduled | 8 | 2.85% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Show | 7 | 2.49% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Lost | 6 | 2.14% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | Rescheduled | 5 | 1.78% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Lost | 5 | 1.78% |
| Unassigned | Canceled | 3 | 1.07% |
| Unassigned | Lost | 2 | 0.71% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Partial Payment | 2 | 0.71% |
| Unassigned | Follow Up | 1 | 0.36% |
| Unassigned | No Show | 1 | 0.36% |
| Unassigned | Rescheduled | 1 | 0.36% |

**Execution time:** 131.684 sec
**Status:** ok

## 92. LAQ-093

**Question**

List leads that need operational follow-up.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  CAST(l.source AS text) AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
ORDER BY
  l.next_touch_point_at NULLS FIRST,
  l.updated_at ASC,
  l.created_at ASC,
  l.id ASC
LIMIT 20;
```

**Generated final answer**

Total matching records: 248

Showing the first 20 records:

| Lead | Status | Pipeline role | Owner ID | Setter ID | Source | Next touch point | Created | Updated |
|---|---|---|---|---|---|---|---|---|
| Pete | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-05 07:38 UTC | 2026-03-09 09:16 UTC |
| Alana | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-09 08:22 UTC | 2026-03-09 16:18 UTC |
| Maciej | Call Booked | Appointment Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-10 13:04 UTC | 2026-03-10 13:04 UTC |
| Cole jones | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-04 20:23 UTC | 2026-03-10 14:38 UTC |
| Fvnnvvb | No Show | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-09 08:10 UTC | 2026-03-10 20:47 UTC |
| test | Call Booked | Appointment Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AZfvBICuFGTCNu4QeqiP6xN03Q | Calendly | Missing | 2026-03-03 20:30 UTC | 2026-03-10 20:47 UTC |
| Marco da Costa | No Show | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-06 16:15 UTC | 2026-03-10 21:03 UTC |
| Gied Flemings | No Show | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-07 14:10 UTC | 2026-03-10 21:04 UTC |
| John Kavanagh | No Show | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-09 07:47 UTC | 2026-03-10 21:10 UTC |
| Jarret Jones | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-05 05:43 UTC | 2026-03-11 13:03 UTC |
| Jeremy & Natalie Collins | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-05 06:21 UTC | 2026-03-12 14:22 UTC |
| Sabine Shaffer | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-09 12:52 UTC | 2026-03-13 12:43 UTC |
| Kenzo radino | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-07 06:51 UTC | 2026-03-14 10:54 UTC |
| Mike Manders Manders | Call Booked | Appointment Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Calendly | Missing | 2026-03-14 06:32 UTC | 2026-03-14 18:22 UTC |
| Erik Defrenne Defrenne | Rescheduled | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Calendly | Missing | 2026-03-14 12:34 UTC | 2026-03-15 21:59 UTC |
| Roy Gerner | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-13 13:23 UTC | 2026-03-17 13:55 UTC |
| Byron Den hollander | No Show | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-16 11:36 UTC | 2026-03-17 14:08 UTC |
| paul klein | Rescheduled | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-17 13:09 UTC | 2026-03-17 21:26 UTC |
| Martin | Rescheduled | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | Missing | 2026-03-17 10:29 UTC | 2026-03-18 10:57 UTC |
| John Evans | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | Missing | 2026-03-13 08:24 UTC | 2026-03-18 11:00 UTC |

**Execution time:** 27.431 sec
**Status:** ok

## 93. LAQ-096

**Question**

How many non-terminal leads have no next touch point?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_missing_next_touch_point
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND l.next_touch_point_at IS NULL;
```

**Generated final answer**

There are 230 non-terminal leads with no next touch point.

**Execution time:** 11.532 sec
**Status:** ok

## 94. LAQ-091

**Question**

Show setter and pipeline role breakdown for leads created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH setter_role_counts AS (
  SELECT
    COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter'),
    COALESCE(CAST(ss.role AS text), 'NO_STATUS')
)
SELECT
  setter_id,
  pipeline_role,
  lead_count,
  SUM(lead_count) OVER() AS total_matching_leads,
  ROUND(lead_count * 100.0 / NULLIF(SUM(lead_count) OVER(), 0), 2) AS percentage_of_total
FROM setter_role_counts
ORDER BY setter_id ASC, lead_count DESC, pipeline_role ASC;
```

**Generated final answer**

Total matching leads: 281

Here is the setter and pipeline role breakdown for leads created from 2026-04-01 to 2026-05-01.

| Setter ID | Pipeline role | Leads | % of total |
|---|---|---:|---:|
| No Setter | New Lead | 86 | 30.60% |
| No Setter | Follow Up | 31 | 11.03% |
| No Setter | Won | 30 | 10.68% |
| No Setter | Appointment Booked | 27 | 9.61% |
| No Setter | Canceled | 22 | 7.83% |
| No Setter | No Show | 20 | 7.12% |
| No Setter | Lost | 9 | 3.20% |
| No Setter | Rescheduled | 9 | 3.20% |
| No Setter | Partial Payment | 2 | 0.71% |
| user_3AesMObeGeZynVoGhloMkfwanES | Won | 14 | 4.98% |
| user_3AesMObeGeZynVoGhloMkfwanES | Appointment Booked | 6 | 2.14% |
| user_3AesMObeGeZynVoGhloMkfwanES | New Lead | 6 | 2.14% |
| user_3AesMObeGeZynVoGhloMkfwanES | Rescheduled | 5 | 1.78% |
| user_3AesMObeGeZynVoGhloMkfwanES | Canceled | 4 | 1.42% |
| user_3AesMObeGeZynVoGhloMkfwanES | Follow Up | 4 | 1.42% |
| user_3AesMObeGeZynVoGhloMkfwanES | Lost | 4 | 1.42% |
| user_3AesMObeGeZynVoGhloMkfwanES | No Show | 2 | 0.71% |

**Execution time:** 45.740 sec
**Status:** ok

## 95. LAQ-095

**Question**

List leads with overdue next touch points.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND l.next_touch_point_at IS NOT NULL
  AND l.next_touch_point_at < NOW()
ORDER BY
  l.next_touch_point_at ASC,
  l.updated_at ASC,
  l.created_at ASC,
  l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 18

Here is the complete list:

| Lead | Lead ID | Status | Status Role | Owner ID | Setter ID | Source | Overdue next touch point |
|---|---|---|---|---|---|---|---|
| Willem Bikker | 5173bf13-f3fe-4031-b3a6-6d14b4e9f8c3 | No Show | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-21 13:00 UTC |
| M Ks | dce6294f-bf7c-4c7a-871d-c32057c0f71b | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-25 17:00 UTC |
| Wesley Helmers | 166773ec-b60c-4825-ae9f-c43cd65cb643 | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | Calendly | 2026-04-03 13:00 UTC |
| Adri Holzken | a09ce021-9e17-4abf-b82b-dcb749213aac | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-04-06 11:03 UTC |
| Mike V | abd94e22-aab3-4366-972e-b26e651b9b19 | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-04-08 09:00 UTC |
| Rolf sterk | 1241c3d9-af11-4d91-8ce0-7fcf970481f6 | Deposit | Partial Payment | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-16 18:30 UTC |
| Ricardo Brandao | 1418f781-6fc7-4720-8ba4-665434975352 | Rescheduled | Rescheduled | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-04-20 13:00 UTC |
| Martijn van Dalen van Dalen | ce6ea935-9326-413e-a28c-ad7c2ccb3f2c | No Sale - Follow Up | Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-24 11:00 UTC |
| Sjanet Van de Griendt | 12f1e54f-3e72-48a6-98ad-a206f4c782eb | No Sale - Follow Up | Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-24 11:00 UTC |
| Jason James Little Little | d185e50b-fe32-499d-b032-bb4f31ec84f1 | No Sale - Follow Up | Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-04-24 13:00 UTC |
| Joep Bergmans | 0331ed7d-3105-490c-9889-d9952034e10b | No Sale - Follow Up | Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-24 15:00 UTC |
| Carolien Janzen | 619c7104-5398-495f-b0e2-33c263321614 | No Sale - Follow Up | Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Other | 2026-04-24 15:00 UTC |
| Chanida | 0f477d75-0686-4f75-9231-d1bb0de1c2a6 | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-04-25 08:00 UTC |
| Matt A A | e2b2ecef-ae26-444c-a3a8-505ccb9f4c42 | No Sale - Follow Up | Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-25 14:00 UTC |
| P. Kok | 9d355927-9223-4199-84c5-2f0fa7927261 | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-27 09:00 UTC |
| Laurens | 33e6335f-0a2c-429d-a96c-155717799f53 | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-28 12:30 UTC |
| Andre Steenkamp | cce86b6d-6f7b-4027-9554-123dc15dae15 | No Sale - Follow Up | Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Other | 2026-04-29 08:00 UTC |
| wesley emo | 062cfc12-0b5b-464f-bac0-5051c6fa1aa7 | No Sale - Follow Up | Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Other | 2026-04-30 15:00 UTC |

**Execution time:** 30.101 sec
**Status:** ok

## 96. LAQ-098

**Question**

Show leads needing operational follow-up by pipeline role.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY lead_count DESC, pipeline_role ASC;
```

**Generated final answer**

Total matching leads: 248

Here is the breakdown by pipeline role:

| Pipeline role | Leads needing follow-up | % of total |
|---|---:|---:|
| New Lead | 96 | 38.71% |
| No Show | 47 | 18.95% |
| Follow Up | 44 | 17.74% |
| Appointment Booked | 37 | 14.92% |
| Rescheduled | 22 | 8.87% |
| Partial Payment | 2 | 0.81% |

**Execution time:** 19.242 sec
**Status:** ok

## 97. LAQ-099

**Question**

Show leads needing operational follow-up by first-touch source.

**Generated SQL**

```sql
SELECT
  COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  ) AS first_touch_source,
  COUNT(*) AS leads_needing_operational_follow_up,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
GROUP BY COALESCE(
  NULLIF(TRIM(first_ms.name), ''),
  NULLIF(TRIM(l.first_source_name), ''),
  'Unknown'
)
ORDER BY leads_needing_operational_follow_up DESC, first_touch_source ASC;
```

**Generated final answer**

Total leads needing operational follow-up: 248

Unknown and YouTube account for most leads needing operational follow-up.

| First-touch source | Leads needing operational follow-up | % of total |
|---|---:|---:|
| Unknown | 138 | 55.65% |
| YouTube | 76 | 30.65% |
| Other | 17 | 6.85% |
| Instagram | 16 | 6.45% |
| Twitter / X | 1 | 0.40% |

**Execution time:** 30.025 sec
**Status:** ok

## 98. LAQ-097

**Question**

List non-terminal leads with no next touch point.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND l.next_touch_point_at IS NULL
ORDER BY
  l.next_touch_point_at NULLS FIRST,
  l.updated_at ASC,
  l.created_at ASC,
  l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 230

Showing the first 20 records:

| Lead | Status | Owner ID | Setter ID | Source | Created | Updated |
|---|---|---|---|---|---|---|
| Pete | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-05 | 2026-03-09 |
| Alana | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-09 | 2026-03-09 |
| Maciej | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-10 | 2026-03-10 |
| Cole jones | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-04 | 2026-03-10 |
| Fvnnvvb | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-09 | 2026-03-10 |
| test | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AZfvBICuFGTCNu4QeqiP6xN03Q | Calendly | 2026-03-03 | 2026-03-10 |
| Marco da Costa | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-06 | 2026-03-10 |
| Gied Flemings | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-07 | 2026-03-10 |
| John Kavanagh | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-09 | 2026-03-10 |
| Jarret Jones | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-05 | 2026-03-11 |
| Jeremy & Natalie Collins | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-05 | 2026-03-12 |
| Sabine Shaffer | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-09 | 2026-03-13 |
| Kenzo radino | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-07 | 2026-03-14 |
| Mike Manders Manders | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Calendly | 2026-03-14 | 2026-03-14 |
| Erik Defrenne Defrenne | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | user_3AesMObeGeZynVoGhloMkfwanES | Calendly | 2026-03-14 | 2026-03-15 |
| Roy Gerner | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-13 | 2026-03-17 |
| Byron Den hollander | No Show | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-16 | 2026-03-17 |
| paul klein | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-17 | 2026-03-17 |
| Martin | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Calendly | 2026-03-17 | 2026-03-18 |
| John Evans | No Show | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Calendly | 2026-03-13 | 2026-03-18 |

**Execution time:** 34.387 sec
**Status:** ok

## 99. LAQ-086

**Question**

Show lead count by setter ID and pipeline role.

**Generated SQL**

```sql
WITH setter_role_counts AS (
  SELECT
    COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY
    COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter'),
    COALESCE(CAST(ss.role AS text), 'NO_STATUS')
),
overall AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM setter_role_counts
)
SELECT
  o.total_matching_leads,
  jsonb_agg(
    jsonb_build_object(
      'setter_id', src.setter_id,
      'pipeline_role', src.pipeline_role,
      'lead_count', src.lead_count,
      'percentage_of_total', ROUND(src.lead_count * 100.0 / NULLIF(o.total_matching_leads, 0), 2)
    )
    ORDER BY src.lead_count DESC, src.setter_id ASC, src.pipeline_role ASC
  ) AS setter_pipeline_breakdown
FROM setter_role_counts src
CROSS JOIN overall o
GROUP BY o.total_matching_leads;
```

**Generated final answer**

Total matching leads: 515

The largest lead groups are No Setter in Won (92) and New Lead (90).

| Setter ID | Pipeline role | Lead count | % of total leads |
|---|---|---:|---:|
| No Setter | Won | 92 | 17.86% |
| No Setter | New Lead | 90 | 17.48% |
| No Setter | Canceled | 47 | 9.13% |
| No Setter | Lost | 43 | 8.35% |
| No Setter | No Show | 42 | 8.16% |
| No Setter | Follow Up | 39 | 7.57% |
| No Setter | Appointment Booked | 29 | 5.63% |
| No Setter | Rescheduled | 13 | 2.52% |
| No Setter | Unqualified | 8 | 1.55% |
| No Setter | Partial Payment | 2 | 0.39% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | Won | 41 | 7.96% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | Lost | 19 | 3.69% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | Canceled | 12 | 2.33% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | Rescheduled | 9 | 1.75% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | Appointment Booked | 7 | 1.36% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | Follow Up | 7 | 1.36% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | New Lead | 6 | 1.17% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | No Show | 5 | 0.97% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | Unqualified | 2 | 0.39% |
| `user_3AZfvBICuFGTCNu4QeqiP6xN03Q` | Appointment Booked | 1 | 0.19% |
| `user_3AZfvBICuFGTCNu4QeqiP6xN03Q` | Won | 1 | 0.19% |

**Execution time:** 132.601 sec
**Status:** ok

## 100. LAQ-100

**Question**

Show leads needing operational follow-up by owner ID.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS owner_id,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
GROUP BY COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned')
ORDER BY lead_count DESC, owner_id ASC;
```

**Generated final answer**

Total leads needing operational follow-up: 248

Here is the breakdown by owner ID:

| Owner ID | Leads needing operational follow-up | % of total |
|---|---:|---:|
| Unassigned | 99 | 39.92% |
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 86 | 34.68% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 62 | 25.00% |
| user_3ARuEgINlhhlbVsZYBbgBDeOEjr | 1 | 0.40% |

**Execution time:** 22.725 sec
**Status:** ok

## 101. LAQ-101

**Question**

Show leads needing operational follow-up by setter ID.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS leads_needing_operational_follow_up,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
GROUP BY COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter')
ORDER BY leads_needing_operational_follow_up DESC, setter_id ASC;
```

**Generated final answer**

Total matching leads: 248

Most leads needing operational follow-up are currently missing a setter.

| Setter ID | Leads needing operational follow-up | % of total |
|---|---:|---:|
| No Setter | 213 | 85.89% |
| user_3AesMObeGeZynVoGhloMkfwanES | 34 | 13.71% |
| user_3AZfvBICuFGTCNu4QeqiP6xN03Q | 1 | 0.40% |

**Execution time:** 23.550 sec
**Status:** ok

## 102. LAQ-102

**Question**

How many leads have a next touch point scheduled from 2026-05-05 to 2026-06-05?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_with_scheduled_next_touch_point
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.next_touch_point_at >= CAST(:start_date AS date)
  AND l.next_touch_point_at < (CAST(:end_date AS date) + INTERVAL '1 day')
```

**Generated final answer**

There are 2 leads with a next touch point scheduled from 2026-05-05 to 2026-06-05.

**Execution time:** 18.732 sec
**Status:** ok

## 103. LAQ-106

**Question**

How many leads have WhatsApp as the next touch point type?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_with_whatsapp_next_touch_point
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.next_touch_point_type = 'WHATSAPP';
```

**Generated final answer**

There are 7 leads with WhatsApp as the next touch point type.

**Execution time:** 9.311 sec
**Status:** ok

## 104. LAQ-107

**Question**

How many leads have proposal review as the next touch point type?

**Generated SQL**

```sql
SELECT COUNT(*) AS proposal_review_next_touch_point_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.next_touch_point_type = :next_touch_point_type;
```

**Generated final answer**

There are 0 leads with Proposal Review as the next touch point type.

**Execution time:** 12.592 sec
**Status:** ok

## 105. LAQ-105

**Question**

Which next touch point type is most common?

**Generated SQL**

```sql
WITH type_counts AS (
  SELECT
    CAST(l.next_touch_point_type AS text) AS next_touch_point_type,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(CAST(l.next_touch_point_type AS text)), '') IS NOT NULL
  GROUP BY CAST(l.next_touch_point_type AS text)
),
totals AS (
  SELECT
    SUM(lead_count) AS total_matching_leads,
    MAX(lead_count) AS max_lead_count
  FROM type_counts
)
SELECT
  tc.next_touch_point_type,
  tc.lead_count,
  t.total_matching_leads,
  ROUND(tc.lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM type_counts tc
CROSS JOIN totals t
WHERE tc.lead_count = t.max_lead_count
ORDER BY tc.next_touch_point_type ASC;
```

**Generated final answer**

The most common next touch point type is Follow Up Call, with 27 leads (79.41% of the 34 leads that have a next touch point type).

**Execution time:** 27.332 sec
**Status:** ok

## 106. LAQ-108

**Question**

How many leads have follow-up call as the next touch point type?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_with_follow_up_call_next_touch_point
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.next_touch_point_type = :next_touch_point_type;
```

**Generated final answer**

There are 27 leads with follow-up call as the next touch point type.

**Execution time:** 13.306 sec
**Status:** ok

## 107. LAQ-104

**Question**

Show next touch point type breakdown for leads.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(l.next_touch_point_type AS text), 'NO_NEXT_TOUCH_POINT_TYPE') AS next_touch_point_type,
  COUNT(*) AS lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(CAST(l.next_touch_point_type AS text), 'NO_NEXT_TOUCH_POINT_TYPE')
ORDER BY lead_count DESC, next_touch_point_type ASC;
```

**Generated final answer**

Total matching leads: 515

Most leads currently do not have a next touch point type set.

| Next touch point type | Lead count | % of total |
|---|---:|---:|
| No Next Touch Point Type | 481 | 93.40% |
| Follow Up Call | 27 | 5.24% |
| WhatsApp | 7 | 1.36% |

**Execution time:** 32.346 sec
**Status:** ok

## 108. LAQ-103

**Question**

List leads with a next touch point scheduled from 2026-05-05 to 2026-06-05.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  COALESCE(CAST(l.next_touch_point_type AS text), 'Unknown') AS next_touch_point_type,
  l.next_touch_point_at,
  l.created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.next_touch_point_at >= :start_date
  AND l.next_touch_point_at < :end_date
ORDER BY l.next_touch_point_at ASC, l.created_at ASC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching leads: 2

Here is the complete list:

| Lead | Status | Owner ID | Setter ID | Next touch point type | Next touch point |
|---|---|---|---|---|---|
| Chris Van As | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | Follow Up Call | 2026-05-07 15:00 UTC |
| Onno Stillebroer | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | Follow Up Call | 2026-05-19 08:00 UTC |

**Execution time:** 37.262 sec
**Status:** ok

## 109. LAQ-110

**Question**

How many stale leads do we have?

**Generated SQL**

```sql
SELECT COUNT(*) AS stale_leads
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  );
```

**Generated final answer**

There are 248 stale leads.

**Execution time:** 13.824 sec
**Status:** ok

## 110. LAQ-112

**Question**

Show stale leads by pipeline role.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COUNT(*) AS stale_lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY stale_lead_count DESC, status_role ASC;
```

**Generated final answer**

Total stale leads: 248

Here is the breakdown by pipeline role:

| Pipeline role | Stale leads | % of total |
|---|---:|---:|
| New Lead | 96 | 38.71% |
| No Show | 47 | 18.95% |
| Follow Up | 44 | 17.74% |
| Appointment Booked | 37 | 14.92% |
| Rescheduled | 22 | 8.87% |
| Partial Payment | 2 | 0.81% |

**Execution time:** 16.824 sec
**Status:** ok

## 111. LAQ-113

**Question**

Show stale leads by exact status name.

**Generated SQL**

```sql
SELECT
  COALESCE(ss.name, 'No Status') AS status_name,
  COUNT(*) AS stale_lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
GROUP BY COALESCE(ss.name, 'No Status')
ORDER BY stale_lead_count DESC, status_name ASC;
```

**Generated final answer**

Total stale leads: 248

Here is the breakdown by exact status name:

| Status | Stale leads | % of stale leads |
|---|---:|---:|
| New Lead | 96 | 38.71% |
| No Show | 47 | 18.95% |
| No Sale - Follow Up | 44 | 17.74% |
| Call Booked | 37 | 14.92% |
| Rescheduled | 22 | 8.87% |
| Deposit | 2 | 0.81% |

**Execution time:** 16.604 sec
**Status:** ok

## 112. LAQ-114

**Question**

Show stale leads by first-touch source.

**Generated SQL**

```sql
WITH source_counts AS (
  SELECT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS first_touch_source,
    COUNT(*) AS stale_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
      'WON',
      'LOST',
      'UNQUALIFIED',
      'CANCELED'
    )
    AND (
      l.next_touch_point_at IS NULL
      OR l.next_touch_point_at < NOW()
    )
  GROUP BY COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown'
  )
),
total AS (
  SELECT SUM(stale_lead_count) AS total_matching_leads
  FROM source_counts
)
SELECT
  sc.first_touch_source,
  sc.stale_lead_count,
  t.total_matching_leads,
  ROUND(sc.stale_lead_count * 100.0 / NULLIF(t.total_matching_leads, 0), 2) AS percentage_of_total
FROM source_counts sc
CROSS JOIN total t
ORDER BY sc.stale_lead_count DESC, sc.first_touch_source ASC;
```

**Generated final answer**

Total stale leads: 248

Here is the breakdown by first-touch source:

| First-touch source | Stale leads | % of total |
|---|---:|---:|
| Unknown | 138 | 55.65% |
| YouTube | 76 | 30.65% |
| Other | 17 | 6.85% |
| Instagram | 16 | 6.45% |
| Twitter / X | 1 | 0.40% |

**Execution time:** 21.191 sec
**Status:** ok

## 113. LAQ-115

**Question**

Which owner ID has the most stale leads?

**Generated SQL**

```sql
WITH stale_owner_counts AS (
  SELECT
    NULLIF(TRIM(l.assigned_to), '') AS owner_id,
    COUNT(*) AS stale_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.assigned_to), '') IS NOT NULL
    AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
      'WON',
      'LOST',
      'UNQUALIFIED',
      'CANCELED'
    )
    AND (
      l.next_touch_point_at IS NULL
      OR l.next_touch_point_at < NOW()
    )
  GROUP BY NULLIF(TRIM(l.assigned_to), '')
),
max_count AS (
  SELECT MAX(stale_lead_count) AS max_stale_lead_count
  FROM stale_owner_counts
)
SELECT
  soc.owner_id,
  soc.stale_lead_count
FROM stale_owner_counts soc
JOIN max_count mc
  ON soc.stale_lead_count = mc.max_stale_lead_count
ORDER BY soc.owner_id ASC
```

**Generated final answer**

Owner ID `user_3AZPWYViL4vUfqNXmNLhNcYAwX4` has the most stale leads, with 86.

**Execution time:** 18.613 sec
**Status:** ok

## 114. LAQ-116

**Question**

Which setter ID has the most stale leads?

**Generated SQL**

```sql
WITH stale_setter_counts AS (
  SELECT
    NULLIF(TRIM(l.setter_id), '') AS setter_id,
    COUNT(*) AS stale_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.setter_id), '') IS NOT NULL
    AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
      'WON',
      'LOST',
      'UNQUALIFIED',
      'CANCELED'
    )
    AND (
      l.next_touch_point_at IS NULL
      OR l.next_touch_point_at < NOW()
    )
  GROUP BY NULLIF(TRIM(l.setter_id), '')
),
max_count AS (
  SELECT MAX(stale_lead_count) AS max_stale_lead_count
  FROM stale_setter_counts
),
total AS (
  SELECT SUM(stale_lead_count) AS total_matching_stale_leads
  FROM stale_setter_counts
)
SELECT
  ssc.setter_id,
  ssc.stale_lead_count,
  t.total_matching_stale_lead_count AS total_matching_stale_leads
FROM stale_setter_counts ssc
JOIN max_count mc
  ON ssc.stale_lead_count = mc.max_stale_lead_count
CROSS JOIN (
  SELECT SUM(stale_lead_count) AS total_matching_stale_lead_count
  FROM stale_setter_counts
) t
ORDER BY ssc.setter_id ASC;
```

**Generated final answer**

Out of 35 stale leads with a setter ID assigned, `user_3AesMObeGeZynVoGhloMkfwanES` has the most, with 34 stale leads.

**Execution time:** 22.421 sec
**Status:** ok

## 115. LAQ-117

**Question**

How many non-terminal leads have not been updated since 2026-02-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS non_terminal_leads_not_updated
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND l.updated_at < :cutoff_date;
```

**Generated final answer**

There are 0 non-terminal leads that have not been updated since 2026-02-01.

**Execution time:** 15.662 sec
**Status:** ok

## 116. LAQ-109

**Question**

Show next touch point type by pipeline role.

**Generated SQL**

```sql
WITH role_touch_counts AS (
  SELECT
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
    COALESCE(CAST(l.next_touch_point_type AS text), 'NO_NEXT_TOUCH_POINT_TYPE') AS next_touch_point_type,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
  GROUP BY
    COALESCE(CAST(ss.role AS text), 'NO_STATUS'),
    COALESCE(CAST(l.next_touch_point_type AS text), 'NO_NEXT_TOUCH_POINT_TYPE')
)
SELECT
  pipeline_role,
  next_touch_point_type,
  lead_count,
  SUM(lead_count) OVER (PARTITION BY pipeline_role) AS pipeline_role_total_leads,
  SUM(lead_count) OVER () AS total_matching_leads,
  ROUND(
    lead_count * 100.0 / NULLIF(SUM(lead_count) OVER (PARTITION BY pipeline_role), 0),
    2
  ) AS percentage_of_pipeline_role,
  ROUND(
    lead_count * 100.0 / NULLIF(SUM(lead_count) OVER (), 0),
    2
  ) AS percentage_of_total
FROM role_touch_counts
ORDER BY pipeline_role ASC, lead_count DESC, next_touch_point_type ASC;
```

**Generated final answer**

Total matching leads: 515

Most roles currently have no next touch point type recorded.

| Pipeline role | Next touch point type | Leads | % of pipeline role |
|---|---|---:|---:|
| Appointment Booked | No Next Touch Point Type | 37 | 100.00% |
| Canceled | No Next Touch Point Type | 58 | 98.31% |
| Canceled | Follow Up Call | 1 | 1.69% |
| Follow Up | No Next Touch Point Type | 29 | 63.04% |
| Follow Up | Follow Up Call | 12 | 26.09% |
| Follow Up | WhatsApp | 5 | 10.87% |
| Lost | No Next Touch Point Type | 55 | 88.71% |
| Lost | Follow Up Call | 5 | 8.06% |
| Lost | WhatsApp | 2 | 3.23% |
| New Lead | No Next Touch Point Type | 96 | 100.00% |
| No Show | No Next Touch Point Type | 46 | 97.87% |
| No Show | Follow Up Call | 1 | 2.13% |
| Partial Payment | Follow Up Call | 1 | 50.00% |
| Partial Payment | No Next Touch Point Type | 1 | 50.00% |
| Rescheduled | No Next Touch Point Type | 21 | 95.45% |
| Rescheduled | Follow Up Call | 1 | 4.55% |
| Unqualified | No Next Touch Point Type | 9 | 90.00% |
| Unqualified | Follow Up Call | 1 | 10.00% |
| Won | No Next Touch Point Type | 129 | 96.27% |
| Won | Follow Up Call | 5 | 3.73% |

**Execution time:** 54.017 sec
**Status:** ok

## 117. LAQ-111

**Question**

List stale leads for review.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND (
    l.next_touch_point_at IS NULL
    OR l.next_touch_point_at < NOW()
  )
ORDER BY
  l.next_touch_point_at NULLS FIRST,
  l.updated_at ASC,
  l.created_at ASC,
  l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching leads: 248

Showing the first 20 stale leads for review; all 20 below are missing a next touch point.

| Lead | Status | Stage | Created | Last updated |
|---|---|---|---|---|
| Pete | No Show | No Show | 2026-03-05 | 2026-03-09 |
| Alana | No Show | No Show | 2026-03-09 | 2026-03-09 |
| Maciej | Call Booked | Appointment Booked | 2026-03-10 | 2026-03-10 |
| Cole jones | No Show | No Show | 2026-03-04 | 2026-03-10 |
| Fvnnvvb | No Show | No Show | 2026-03-09 | 2026-03-10 |
| test | Call Booked | Appointment Booked | 2026-03-03 | 2026-03-10 |
| Marco da Costa | No Show | No Show | 2026-03-06 | 2026-03-10 |
| Gied Flemings | No Show | No Show | 2026-03-07 | 2026-03-10 |
| John Kavanagh | No Show | No Show | 2026-03-09 | 2026-03-10 |
| Jarret Jones | No Show | No Show | 2026-03-05 | 2026-03-11 |
| Jeremy & Natalie Collins | No Show | No Show | 2026-03-05 | 2026-03-12 |
| Sabine Shaffer | No Show | No Show | 2026-03-09 | 2026-03-13 |
| Kenzo radino | No Show | No Show | 2026-03-07 | 2026-03-14 |
| Mike Manders Manders | Call Booked | Appointment Booked | 2026-03-14 | 2026-03-14 |
| Erik Defrenne Defrenne | Rescheduled | Rescheduled | 2026-03-14 | 2026-03-15 |
| Roy Gerner | No Show | No Show | 2026-03-13 | 2026-03-17 |
| Byron Den hollander | No Show | No Show | 2026-03-16 | 2026-03-17 |
| paul klein | Rescheduled | Rescheduled | 2026-03-17 | 2026-03-17 |
| Martin | Rescheduled | Rescheduled | 2026-03-17 | 2026-03-18 |
| John Evans | No Show | No Show | 2026-03-13 | 2026-03-18 |

**Execution time:** 53.860 sec
**Status:** ok

## 118. LAQ-118

**Question**

List non-terminal leads that have not been updated since 2026-02-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND l.updated_at < :cutoff_date
ORDER BY l.updated_at ASC, l.created_at ASC, l.id ASC
LIMIT :limit
```

**Generated final answer**

There are no non-terminal leads that have not been updated since 2026-02-01.

**Execution time:** 26.291 sec
**Status:** ok

## 119. LAQ-120

**Question**

How many leads are missing first-touch source?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_missing_first_touch_source
FROM leads l
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(
        NULLIF(TRIM(first_ms.name), ''),
        NULLIF(TRIM(l.first_source_name), '')
      ) IS NULL;
```

**Generated final answer**

There are 364 leads missing a first-touch source.

**Execution time:** 17.710 sec
**Status:** ok

## 120. LAQ-119

**Question**

Show non-terminal leads not updated since 2026-02-01 by pipeline role.

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
  COUNT(*) AS not_updated_lead_count,
  SUM(COUNT(*)) OVER() AS total_matching_leads,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
    'WON',
    'LOST',
    'UNQUALIFIED',
    'CANCELED'
  )
  AND l.updated_at < :cutoff_date
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY not_updated_lead_count DESC, pipeline_role ASC;
```

**Generated final answer**

There are no non-terminal leads with a last update before 2026-02-01.

**Execution time:** 25.372 sec
**Status:** ok

## 121. LAQ-121

**Question**

How many leads are missing last-touch source?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_missing_last_touch_source
FROM leads l
LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(
    NULLIF(TRIM(last_ms.name), ''),
    NULLIF(TRIM(l.last_source_name), '')
  ) IS NULL;
```

**Generated final answer**

There are 364 leads missing a last-touch source.

**Execution time:** 18.795 sec
**Status:** ok

## 122. LAQ-124

**Question**

Show missing owner, missing setter, and missing next touch point counts.

**Generated SQL**

```sql
WITH lead_base AS (
  SELECT
    l.id,
    NULLIF(TRIM(l.assigned_to), '') IS NULL AS missing_owner,
    NULLIF(TRIM(l.setter_id), '') IS NULL AS missing_setter,
    (
      l.next_touch_point_at IS NULL
      AND COALESCE(CAST(ss.role AS text), 'NO_STATUS') NOT IN (
        'WON',
        'LOST',
        'UNQUALIFIED',
        'CANCELED'
      )
    ) AS missing_next_touch_point
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
)
SELECT
  COUNT(*) FILTER (WHERE missing_owner) AS missing_owner_count,
  COUNT(*) FILTER (WHERE missing_setter) AS missing_setter_count,
  COUNT(*) FILTER (WHERE missing_next_touch_point) AS missing_next_touch_point_count
FROM lead_base
```

**Generated final answer**

Here are the current counts:

| Metric | Count |
|---|---:|
| Missing owner | 105 |
| Missing setter | 405 |
| Missing next touch point | 230 |

Missing next touch point excludes leads in Won, Lost, Unqualified, and Canceled statuses.

**Execution time:** 20.626 sec
**Status:** ok

## 123. LAQ-125

**Question**

How many leads created from 2026-04-01 to 2026-05-01 are missing first-touch source?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_missing_first_touch_source
FROM leads l
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
  AND COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), '')
  ) IS NULL
```

**Generated final answer**

There are 136 leads created from 2026-04-01 to 2026-05-01 that are missing a first-touch source.

**Execution time:** 19.827 sec
**Status:** ok

## 124. LAQ-126

**Question**

How many leads created from 2026-04-01 to 2026-05-01 are missing last-touch source?

**Generated SQL**

```sql
SELECT COUNT(*) AS leads_missing_last_touch_source
FROM leads l
LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
  AND COALESCE(
    NULLIF(TRIM(last_ms.name), ''),
    NULLIF(TRIM(l.last_source_name), '')
  ) IS NULL;
```

**Generated final answer**

There are 136 leads created from 2026-04-01 to 2026-05-01 that are missing a last-touch source.

**Execution time:** 18.002 sec
**Status:** ok

## 125. LAQ-127

**Question**

List leads created from 2026-04-01 to 2026-05-01 with no status assigned.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  'No Status' AS status_name,
  'NO_STATUS' AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.next_touch_point_at,
  l.created_at,
  l.updated_at
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.status_id IS NULL
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20;
```

**Generated final answer**

I couldn’t find any leads created from 2026-04-01 to 2026-05-01 with no status assigned.

**Execution time:** 19.295 sec
**Status:** ok

## 126. LAQ-123

**Question**

List leads missing last-touch source.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(
    NULLIF(TRIM(last_ms.name), ''),
    NULLIF(TRIM(l.last_source_name), '')
  ) IS NULL
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching records: 364

Showing the first 20 most recently created leads:

| Lead | Status | Owner ID | Setter ID | Created at (UTC) |
|---|---|---|---|---|
| Bahadir | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-23 18:43 |
| Steve Grainger | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-23 11:07 |
| Lévy Fransen | New Lead | Unassigned | No Setter | 2026-04-23 05:35 |
| Stephen William Bennett | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-22 20:28 |
| Bob Schoutsen | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-22 17:35 |
| Tom ter woord | Canceled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-22 16:28 |
| Yassine Temsamani | New Lead | Unassigned | No Setter | 2026-04-22 14:00 |
| Brigitte Pajonk | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-22 08:37 |
| Decoster Chris | New Lead | Unassigned | No Setter | 2026-04-22 07:55 |
| David Burgess | New Lead | Unassigned | No Setter | 2026-04-22 07:55 |
| Frank Mennes | New Lead | Unassigned | No Setter | 2026-04-22 07:55 |
| olivier wijnen | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-22 05:41 |
| Jeroen van Teijlingen | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | user_3AesMObeGeZynVoGhloMkfwanES | 2026-04-21 17:53 |
| Ron Richter | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-21 13:10 |
| Jannes vorenholt | Rescheduled | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-21 07:45 |
| Balint Matys | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-21 07:27 |
| Wouter Jan Naborn | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-21 07:03 |
| Robert Voorn | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | No Setter | 2026-04-21 06:41 |
| Kaleb Assid | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-21 00:41 |
| Robin Lang | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | No Setter | 2026-04-20 20:35 |

**Execution time:** 51.809 sec
**Status:** ok

## 127. LAQ-122

**Question**

List leads missing first-touch source.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COALESCE(CAST(l.source AS text), 'Unknown') AS source,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), '')
  ) IS NULL
ORDER BY l.created_at DESC, l.id ASC
LIMIT 20
```

**Generated final answer**

Total matching leads: 364

Showing the first 20 leads:

| Lead ID | Lead | Status | Owner | High-level Source | Created (UTC) |
|---|---|---|---|---|---|
| ab3ec153-d594-4637-83b9-8967d2f97646 | Bahadir | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly | 2026-04-23 18:43 |
| 77738368-2d97-45b6-9cd3-6fa67ef4c338 | Steve Grainger | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly | 2026-04-23 11:07 |
| c76ad746-a866-4646-984a-5df5edaea5ef | Lévy Fransen | New Lead | Unassigned | Other | 2026-04-23 05:35 |
| c899cc7b-4296-480e-910c-add2cb1020fa | Stephen William Bennett | Rescheduled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly | 2026-04-22 20:28 |
| fe65d153-3e64-4e14-941e-3a7b87c36020 | Bob Schoutsen | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Other | 2026-04-22 17:35 |
| c7bcc555-233c-4672-9877-47ba45c26919 | Tom ter woord | Canceled | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Other | 2026-04-22 16:28 |
| f49c155f-c4b2-45b7-b3d8-4a079851a141 | Yassine Temsamani | New Lead | Unassigned | Other | 2026-04-22 14:00 |
| a957c106-389c-4805-b788-e1145347f22a | Brigitte Pajonk | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Other | 2026-04-22 08:37 |
| d29582b0-d76a-42cb-8486-7b77dbca7114 | Decoster Chris | New Lead | Unassigned | Other | 2026-04-22 07:55 |
| e9671c93-04da-49a7-bbba-c93e3f9cb814 | David Burgess | New Lead | Unassigned | Other | 2026-04-22 07:55 |
| 485cacc6-4048-43fd-9442-ead188f64ff4 | Frank Mennes | New Lead | Unassigned | Other | 2026-04-22 07:55 |
| bf6536fc-0b07-40d2-9172-11e0664aad8d | olivier wijnen | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Calendly | 2026-04-22 05:41 |
| c5e28827-790e-48bf-bf98-05c6eca38386 | Jeroen van Teijlingen | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Other | 2026-04-21 17:53 |
| d44e670c-cc2d-41ef-86d4-e6652fe217c9 | Ron Richter | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Other | 2026-04-21 13:10 |
| 9de9df91-31fb-42e8-a841-fecf67246734 | Jannes vorenholt | Rescheduled | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Other | 2026-04-21 07:45 |
| c962055d-b816-4624-a1ee-802c74e811df | Balint Matys | No Sale - Follow Up | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Other | 2026-04-21 07:27 |
| 01aaf1c6-a2f6-4aec-8ac8-ecf241b7836f | Wouter Jan Naborn | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Other | 2026-04-21 07:03 |
| 1fe67a5f-63ee-4617-bf55-38bcb27803dc | Robert Voorn | Call Booked | user_3ATRxXyN4j8bDHYJKRCEMAerasy | Calendly | 2026-04-21 06:41 |
| 476348af-e2b8-4582-8f87-c53a3593f33d | Kaleb Assid | Call Booked | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Other | 2026-04-21 00:41 |
| e4876e03-505f-4900-b938-8e743da3ceb1 | Robin Lang | No Sale - Follow Up | user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | Other | 2026-04-20 20:35 |

**Execution time:** 65.920 sec
**Status:** ok

## 128. LAQ-128

**Question**

Show the daily lead creation trend from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH days AS (
  SELECT generate_series(
    CAST(:start_date AS date),
    CAST(:end_date AS date),
    INTERVAL '1 day'
  )::date AS lead_created_date
),
daily_counts AS (
  SELECT
    d.lead_created_date,
    COUNT(l.id) AS lead_count
  FROM days d
  LEFT JOIN leads l
    ON DATE_TRUNC('day', l.created_at)::date = d.lead_created_date
   AND l.clerk_org_id = :org_id
   AND l.is_deleted = false
  GROUP BY d.lead_created_date
)
SELECT
  dc.lead_created_date,
  dc.lead_count,
  SUM(dc.lead_count) OVER() AS total_matching_leads
FROM daily_counts dc
ORDER BY dc.lead_created_date ASC;
```

**Generated final answer**

Total leads created: 281

Here is the daily trend:

| Date | Leads created |
|---|---:|
| 2026-04-01 | 6 |
| 2026-04-02 | 20 |
| 2026-04-03 | 19 |
| 2026-04-04 | 4 |
| 2026-04-05 | 3 |
| 2026-04-06 | 7 |
| 2026-04-07 | 9 |
| 2026-04-08 | 6 |
| 2026-04-09 | 10 |
| 2026-04-10 | 21 |
| 2026-04-11 | 5 |
| 2026-04-12 | 8 |
| 2026-04-13 | 6 |
| 2026-04-14 | 7 |
| 2026-04-15 | 14 |
| 2026-04-16 | 10 |
| 2026-04-17 | 4 |
| 2026-04-18 | 3 |
| 2026-04-19 | 4 |
| 2026-04-20 | 36 |
| 2026-04-21 | 30 |
| 2026-04-22 | 26 |
| 2026-04-23 | 16 |
| 2026-04-24 | 7 |
| 2026-04-25 | 0 |
| 2026-04-26 | 0 |
| 2026-04-27 | 0 |
| 2026-04-28 | 0 |
| 2026-04-29 | 0 |
| 2026-04-30 | 0 |
| 2026-05-01 | 0 |

**Execution time:** 41.800 sec
**Status:** ok

## 129. LAQ-133

**Question**

Which day had the most leads created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
WITH daily_counts AS (
  SELECT
    DATE_TRUNC('day', l.created_at)::date AS lead_created_date,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY DATE_TRUNC('day', l.created_at)::date
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM daily_counts
)
SELECT
  dc.lead_created_date,
  dc.lead_count
FROM daily_counts dc
JOIN max_count mc
  ON dc.lead_count = mc.max_lead_count
ORDER BY dc.lead_created_date ASC;
```

**Generated final answer**

Apr 20, 2026 had the most leads created in that period, with 36 leads.

**Execution time:** 16.798 sec
**Status:** ok

## 130. LAQ-129

**Question**

Show the weekly lead creation trend from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 week'
  )::date AS week_start
),
weekly_counts AS (
  SELECT
    DATE_TRUNC('week', l.created_at)::date AS week_start,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY DATE_TRUNC('week', l.created_at)::date
),
weekly_filled AS (
  SELECT
    w.week_start,
    COALESCE(wc.lead_count, 0) AS lead_count
  FROM weeks w
  LEFT JOIN weekly_counts wc
    ON wc.week_start = w.week_start
),
weekly_trend AS (
  SELECT
    wf.week_start,
    wf.lead_count,
    LAG(wf.lead_count) OVER (ORDER BY wf.week_start) AS previous_week_count,
    SUM(wf.lead_count) OVER () AS total_matching_leads
  FROM weekly_filled wf
)
SELECT
  wt.week_start,
  wt.lead_count,
  wt.previous_week_count,
  CASE
    WHEN wt.previous_week_count IS NULL OR wt.previous_week_count = 0 THEN NULL
    ELSE ROUND(
      (wt.lead_count - wt.previous_week_count) * 100.0 / wt.previous_week_count,
      2
    )
  END AS pct_change,
  wt.total_matching_leads
FROM weekly_trend wt
ORDER BY wt.week_start ASC
```

**Generated final answer**

Total leads created in this period: 515

Here is the weekly lead creation trend from 2026-02-09 to 2026-05-04:

| Week starting | Leads created | Previous week | % change |
|---|---:|---:|---:|
| 2026-02-09 | 0 | — | — |
| 2026-02-16 | 0 | 0 | — |
| 2026-02-23 | 0 | 0 | — |
| 2026-03-02 | 35 | 0 | — |
| 2026-03-09 | 86 | 35 | 145.71% |
| 2026-03-16 | 42 | 86 | -51.16% |
| 2026-03-23 | 60 | 42 | 42.86% |
| 2026-03-30 | 63 | 60 | 5.00% |
| 2026-04-06 | 66 | 63 | 4.76% |
| 2026-04-13 | 48 | 66 | -27.27% |
| 2026-04-20 | 115 | 48 | 139.58% |
| 2026-04-27 | 0 | 115 | -100.00% |
| 2026-05-04 | 0 | 0 | — |

The latest row, week starting 2026-05-04, shows 0 leads and is unchanged from the previous week.

**Execution time:** 69.626 sec
**Status:** ok

## 131. LAQ-130

**Question**

Show the monthly lead creation trend from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
monthly_counts AS (
  SELECT
    m.month_start,
    COUNT(l.id) AS lead_count
  FROM months m
  LEFT JOIN leads l
    ON DATE_TRUNC('month', l.created_at)::date = m.month_start
   AND l.clerk_org_id = :org_id
   AND l.is_deleted = false
   AND l.created_at >= :start_date
   AND l.created_at < :end_date
  GROUP BY m.month_start
),
monthly_with_change AS (
  SELECT
    month_start,
    lead_count,
    LAG(lead_count) OVER (ORDER BY month_start) AS previous_month_count
  FROM monthly_counts
)
SELECT
  month_start,
  lead_count,
  previous_month_count,
  CASE
    WHEN previous_month_count IS NULL OR previous_month_count = 0 THEN NULL
    ELSE ROUND((lead_count - previous_month_count) * 100.0 / previous_month_count, 2)
  END AS pct_change
FROM monthly_with_change
ORDER BY month_start ASC;
```

**Generated final answer**

Here is the monthly lead creation trend from May 2025 through Apr 2026:

| Month | Lead count | Previous month | % change |
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
| Mar 2026 | 234 | 0 | — |
| Apr 2026 | 281 | 234 | 20.09% |

In Apr 2026, leads increased by 47 compared with Mar 2026, a 20.09% increase.

**Execution time:** 54.573 sec
**Status:** ok

## 132. LAQ-135

**Question**

Which month had the most leads created from 2025-05-01 to 2026-05-01?

**Generated SQL**

```sql
WITH monthly_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY DATE_TRUNC('month', l.created_at)::date
),
max_count AS (
  SELECT MAX(lead_count) AS max_lead_count
  FROM monthly_counts
)
SELECT
  TO_CHAR(mc.month_start, 'Mon YYYY') AS month,
  mc.lead_count
FROM monthly_counts mc
JOIN max_count mx
  ON mc.lead_count = mx.max_lead_count
ORDER BY mc.month_start ASC;
```

**Generated final answer**

Apr 2026 had the most leads created, with 281 leads.

**Execution time:** 18.222 sec
**Status:** ok

## 133. LAQ-132

**Question**

Show monthly lead growth from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
monthly_counts AS (
  SELECT
    m.month_start,
    COUNT(l.id) AS lead_count
  FROM months m
  LEFT JOIN leads l
    ON DATE_TRUNC('month', l.created_at)::date = m.month_start
   AND l.clerk_org_id = :org_id
   AND l.is_deleted = false
   AND l.created_at >= :start_date
   AND l.created_at < :end_date
  GROUP BY m.month_start
),
monthly_trend AS (
  SELECT
    month_start,
    lead_count,
    LAG(lead_count) OVER (ORDER BY month_start) AS previous_month_count,
    SUM(lead_count) OVER () AS total_matching_leads
  FROM monthly_counts
)
SELECT
  month_start,
  lead_count,
  previous_month_count,
  CASE
    WHEN previous_month_count IS NULL OR previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (lead_count - previous_month_count) * 100.0 / previous_month_count,
      2
    )
  END AS pct_change,
  total_matching_leads
FROM monthly_trend
ORDER BY month_start ASC
```

**Generated final answer**

Total leads created from May 2025 through Apr 2026: 515

Here is the monthly trend:

| Month | Leads | Previous month | % change |
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
| Mar 2026 | 234 | 0 | — |
| Apr 2026 | 281 | 234 | 20.09% |

In Apr 2026, leads increased by 47 compared with Mar 2026, a 20.09% increase.

**Execution time:** 58.528 sec
**Status:** ok

## 134. LAQ-134

**Question**

Which week had the most leads created from 2026-02-09 to 2026-05-04?

**Generated SQL**

```sql
WITH weekly_counts AS (
  SELECT
    DATE_TRUNC('week', l.created_at)::date AS week_start,
    LEAST(
      DATE_TRUNC('week', l.created_at)::date + INTERVAL '6 days',
      (CAST(:end_date AS date) - INTERVAL '1 day')
    )::date AS week_end,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('week', l.created_at)::date,
    LEAST(
      DATE_TRUNC('week', l.created_at)::date + INTERVAL '6 days',
      (CAST(:end_date AS date) - INTERVAL '1 day')
    )::date
),
ranked_weeks AS (
  SELECT
    week_start,
    week_end,
    lead_count,
    RANK() OVER (ORDER BY lead_count DESC, week_start ASC) AS lead_count_rank
  FROM weekly_counts
)
SELECT
  week_start,
  week_end,
  lead_count
FROM ranked_weeks
WHERE lead_count_rank = 1
ORDER BY week_start ASC;
```

**Generated final answer**

From Feb 9 to May 4, 2026, the week of Apr 20–26, 2026 had the most leads created, with 115 leads.

**Execution time:** 40.851 sec
**Status:** ok

## 135. LAQ-136

**Question**

Did lead volume increase in April 2026 compared with March 2026?

**Generated SQL**

```sql
WITH month_range AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
monthly_counts AS (
  SELECT
    mr.month_start,
    COUNT(l.id) AS lead_count
  FROM month_range mr
  LEFT JOIN leads l
    ON l.clerk_org_id = :org_id
   AND l.is_deleted = false
   AND l.created_at >= mr.month_start
   AND l.created_at < mr.month_start + INTERVAL '1 month'
   AND l.created_at >= :start_date
   AND l.created_at < :end_date
  GROUP BY mr.month_start
),
ordered_months AS (
  SELECT
    month_start,
    lead_count,
    ROW_NUMBER() OVER (ORDER BY month_start ASC) AS month_order
  FROM monthly_counts
)
SELECT
  TO_CHAR(MAX(CASE WHEN month_order = 1 THEN month_start END), 'Mon YYYY') AS comparison_month,
  MAX(CASE WHEN month_order = 1 THEN lead_count END) AS comparison_month_leads,
  TO_CHAR(MAX(CASE WHEN month_order = 2 THEN month_start END), 'Mon YYYY') AS target_month,
  MAX(CASE WHEN month_order = 2 THEN lead_count END) AS target_month_leads,
  MAX(CASE WHEN month_order = 2 THEN lead_count END) - MAX(CASE WHEN month_order = 1 THEN lead_count END) AS lead_change,
  CASE
    WHEN MAX(CASE WHEN month_order = 1 THEN lead_count END) = 0 THEN NULL
    ELSE ROUND(
      (
        MAX(CASE WHEN month_order = 2 THEN lead_count END)
        - MAX(CASE WHEN month_order = 1 THEN lead_count END)
      ) * 100.0
      / MAX(CASE WHEN month_order = 1 THEN lead_count END),
      2
    )
  END AS pct_change,
  CASE
    WHEN MAX(CASE WHEN month_order = 2 THEN lead_count END) > MAX(CASE WHEN month_order = 1 THEN lead_count END) THEN 'Increased'
    WHEN MAX(CASE WHEN month_order = 2 THEN lead_count END) < MAX(CASE WHEN month_order = 1 THEN lead_count END) THEN 'Decreased'
    ELSE 'No Change'
  END AS trend
FROM ordered_months
```

**Generated final answer**

Yes—lead volume increased in April 2026 to 281 from 234 in March 2026, up by 47 leads (+20.09%).

**Execution time:** 35.937 sec
**Status:** ok

## 136. LAQ-131

**Question**

Show weekly lead growth from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', CAST(:end_date AS timestamp))::date,
    INTERVAL '1 week'
  )::date AS week_start
),
weekly_counts AS (
  SELECT
    DATE_TRUNC('week', l.created_at)::date AS week_start,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= CAST(:start_date AS date)
    AND l.created_at < (CAST(:end_date AS date) + INTERVAL '1 week')
  GROUP BY DATE_TRUNC('week', l.created_at)::date
),
weekly_filled AS (
  SELECT
    w.week_start,
    COALESCE(wc.lead_count, 0) AS lead_count
  FROM weeks w
  LEFT JOIN weekly_counts wc
    ON wc.week_start = w.week_start
),
weekly_growth AS (
  SELECT
    week_start,
    lead_count,
    LAG(lead_count) OVER (ORDER BY week_start) AS previous_week_count
  FROM weekly_filled
)
SELECT
  week_start,
  lead_count,
  previous_week_count,
  lead_count - previous_week_count AS lead_change,
  CASE
    WHEN previous_week_count IS NULL OR previous_week_count = 0 THEN NULL
    ELSE ROUND((lead_count - previous_week_count) * 100.0 / previous_week_count, 2)
  END AS pct_change
FROM weekly_growth
ORDER BY week_start ASC
```

**Generated final answer**

Here is the weekly lead growth for weeks starting 2026-02-09 through 2026-05-04.

| Week starting | Leads | Previous week | Growth | % change |
|---|---:|---:|---:|---:|
| 2026-02-09 | 0 | — | — | — |
| 2026-02-16 | 0 | 0 | 0 | — |
| 2026-02-23 | 0 | 0 | 0 | — |
| 2026-03-02 | 35 | 0 | +35 | — |
| 2026-03-09 | 86 | 35 | +51 | 145.71% |
| 2026-03-16 | 42 | 86 | -44 | -51.16% |
| 2026-03-23 | 60 | 42 | +18 | 42.86% |
| 2026-03-30 | 63 | 60 | +3 | 5.00% |
| 2026-04-06 | 66 | 63 | +3 | 4.76% |
| 2026-04-13 | 48 | 66 | -18 | -27.27% |
| 2026-04-20 | 115 | 48 | +67 | 139.58% |
| 2026-04-27 | 0 | 115 | -115 | -100.00% |
| 2026-05-04 | 0 | 0 | 0 | — |

Lead volume peaked at 115 in the week starting 2026-04-20; in the latest week starting 2026-05-04, it stayed flat at 0 versus the prior week.

**Execution time:** 84.986 sec
**Status:** ok

## 137. LAQ-138

**Question**

Show the monthly lead trend by pipeline role from 2026-02-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
roles AS (
  SELECT DISTINCT
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
),
month_role_grid AS (
  SELECT
    m.month_start,
    r.pipeline_role
  FROM months m
  CROSS JOIN roles r
),
monthly_role_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('month', l.created_at)::date,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS')
),
monthly_role_filled AS (
  SELECT
    mrg.month_start,
    mrg.pipeline_role,
    COALESCE(mrc.lead_count, 0) AS lead_count
  FROM month_role_grid mrg
  LEFT JOIN monthly_role_counts mrc
    ON mrc.month_start = mrg.month_start
   AND mrc.pipeline_role = mrg.pipeline_role
),
monthly_role_trend AS (
  SELECT
    month_start,
    pipeline_role,
    lead_count,
    LAG(lead_count) OVER (
      PARTITION BY pipeline_role
      ORDER BY month_start
    ) AS previous_month_count
  FROM monthly_role_filled
),
total AS (
  SELECT COUNT(*) AS total_matching_leads
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
)
SELECT
  mrt.month_start,
  mrt.pipeline_role,
  mrt.lead_count,
  mrt.previous_month_count,
  CASE
    WHEN mrt.previous_month_count IS NULL OR mrt.previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (mrt.lead_count - mrt.previous_month_count) * 100.0 / mrt.previous_month_count,
      2
    )
  END AS pct_change,
  t.total_matching_leads
FROM monthly_role_trend mrt
CROSS JOIN total t
ORDER BY mrt.month_start ASC, mrt.pipeline_role ASC
```

**Generated final answer**

Total matching leads: 515

Here is the monthly trend by pipeline role:

| Pipeline role | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Appointment Booked | 0 | 4 | 33 (+725.00%) |
| Canceled | 0 | 33 | 26 (-21.21%) |
| Follow Up | 0 | 11 | 35 (+218.18%) |
| Lost | 0 | 49 | 13 (-73.47%) |
| New Lead | 0 | 4 | 92 (+2200.00%) |
| No Show | 0 | 25 | 22 (-12.00%) |
| Partial Payment | 0 | 0 | 2 |
| Rescheduled | 0 | 8 | 14 (+75.00%) |
| Unqualified | 0 | 10 | 0 (-100.00%) |
| Won | 0 | 90 | 44 (-51.11%) |

In Apr 2026, New Lead rose sharply from 4 to 92 (+2200.00%) versus Mar 2026, while Won fell from 90 to 44 (-51.11%).

**Execution time:** 61.594 sec
**Status:** ok

## 138. LAQ-137

**Question**

Compare lead creation volume between 2026-03-01 to 2026-04-01 and 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) FILTER (
    WHERE l.created_at >= CAST(:period_1_start AS timestamp)
      AND l.created_at < CAST(:period_1_end AS timestamp)
  ) AS first_period_leads,
  COUNT(*) FILTER (
    WHERE l.created_at >= CAST(:period_2_start AS timestamp)
      AND l.created_at < CAST(:period_2_end AS timestamp)
  ) AS second_period_leads,
  COUNT(*) FILTER (
    WHERE l.created_at >= CAST(:period_2_start AS timestamp)
      AND l.created_at < CAST(:period_2_end AS timestamp)
  ) - COUNT(*) FILTER (
    WHERE l.created_at >= CAST(:period_1_start AS timestamp)
      AND l.created_at < CAST(:period_1_end AS timestamp)
  ) AS absolute_change,
  CASE
    WHEN COUNT(*) FILTER (
      WHERE l.created_at >= CAST(:period_1_start AS timestamp)
        AND l.created_at < CAST(:period_1_end AS timestamp)
    ) = 0 THEN NULL
    ELSE ROUND(
      (
        COUNT(*) FILTER (
          WHERE l.created_at >= CAST(:period_2_start AS timestamp)
            AND l.created_at < CAST(:period_2_end AS timestamp)
        ) - COUNT(*) FILTER (
          WHERE l.created_at >= CAST(:period_1_start AS timestamp)
            AND l.created_at < CAST(:period_1_end AS timestamp)
        )
      ) * 100.0
      / COUNT(*) FILTER (
        WHERE l.created_at >= CAST(:period_1_start AS timestamp)
          AND l.created_at < CAST(:period_1_end AS timestamp)
      ),
      2
    )
  END AS pct_change
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND (
    (l.created_at >= CAST(:period_1_start AS timestamp) AND l.created_at < CAST(:period_1_end AS timestamp))
    OR
    (l.created_at >= CAST(:period_2_start AS timestamp) AND l.created_at < CAST(:period_2_end AS timestamp))
  )
```

**Generated final answer**

Lead creation increased from 234 between 2026-03-01 and 2026-04-01 to 281 between 2026-04-01 and 2026-05-01, up 47 leads (20.09%).

**Execution time:** 65.634 sec
**Status:** ok

## 139. LAQ-143

**Question**

Show the weekly lead trend by first-touch source from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 week'
  )::date AS week_start
),
sources AS (
  SELECT DISTINCT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
),
weekly_source_grid AS (
  SELECT
    w.week_start,
    s.source
  FROM weeks w
  CROSS JOIN sources s
),
weekly_source_counts AS (
  SELECT
    DATE_TRUNC('week', l.created_at)::date AS week_start,
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('week', l.created_at)::date,
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    )
),
weekly_source_filled AS (
  SELECT
    wsg.week_start,
    wsg.source,
    COALESCE(wsc.lead_count, 0) AS lead_count
  FROM weekly_source_grid wsg
  LEFT JOIN weekly_source_counts wsc
    ON wsc.week_start = wsg.week_start
   AND wsc.source = wsg.source
),
weekly_source_trend AS (
  SELECT
    week_start,
    source,
    lead_count,
    SUM(lead_count) OVER (PARTITION BY source) AS source_total_leads,
    LAG(lead_count) OVER (
      PARTITION BY source
      ORDER BY week_start
    ) AS previous_week_count
  FROM weekly_source_filled
),
total AS (
  SELECT SUM(lead_count) AS total_leads
  FROM weekly_source_filled
)
SELECT
  wst.week_start,
  wst.source,
  wst.lead_count,
  wst.previous_week_count,
  CASE
    WHEN wst.previous_week_count IS NULL OR wst.previous_week_count = 0 THEN NULL
    ELSE ROUND(
      (wst.lead_count - wst.previous_week_count) * 100.0 / wst.previous_week_count,
      2
    )
  END AS pct_change,
  wst.source_total_leads,
  t.total_leads AS total_matching_leads
FROM weekly_source_trend wst
CROSS JOIN total t
ORDER BY wst.source_total_leads DESC, wst.source ASC, wst.week_start ASC
```

**Generated final answer**

Total matching leads: 515

Here is the weekly lead trend by first-touch source from 2026-02-09 to 2026-05-04, using week start dates:

| First-touch source | Feb 09 | Feb 16 | Feb 23 | Mar 02 | Mar 09 | Mar 16 | Mar 23 | Mar 30 | Apr 06 | Apr 13 | Apr 20 | Apr 27 | May 04 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Unknown | 0 | 0 | 0 | 35 | 85 (+142.86%) | 41 (-51.76%) | 56 (+36.59%) | 62 (+10.71%) | 35 (-43.55%) | 14 (-60.00%) | 36 (+157.14%) | 0 (-100.00%) | 0 |
| YouTube | 0 | 0 | 0 | 0 | 1 | 1 (0.00%) | 1 (0.00%) | 0 (-100.00%) | 18 | 18 (0.00%) | 64 (+255.56%) | 0 (-100.00%) | 0 |
| Instagram | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 (-100.00%) | 3 | 11 (+266.67%) | 10 (-9.09%) | 0 (-100.00%) | 0 |
| Other | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 (0.00%) | 10 (+900.00%) | 5 (-50.00%) | 4 (-20.00%) | 0 (-100.00%) | 0 |
| Twitter / X | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 (-100.00%) | 0 |

In the latest completed week shown, starting Apr 27, 2026, every source dropped to 0 leads versus the prior week, with the biggest decline coming from YouTube, down from 64.

**Execution time:** 119.093 sec
**Status:** ok

## 140. LAQ-140

**Question**

Show the monthly trend for won leads from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
monthly_counts AS (
  SELECT
    m.month_start,
    COUNT(l.id) FILTER (WHERE ss.role = 'WON') AS won_lead_count
  FROM months m
  LEFT JOIN leads l
    ON DATE_TRUNC('month', l.created_at)::date = m.month_start
   AND l.clerk_org_id = :org_id
   AND l.is_deleted = false
   AND l.created_at >= :start_date
   AND l.created_at < :end_date
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  GROUP BY m.month_start
),
monthly_trend AS (
  SELECT
    mc.month_start,
    mc.won_lead_count,
    LAG(mc.won_lead_count) OVER (ORDER BY mc.month_start) AS previous_month_count
  FROM monthly_counts mc
)
SELECT
  TO_CHAR(mt.month_start, 'Mon YYYY') AS month,
  mt.won_lead_count,
  mt.previous_month_count,
  CASE
    WHEN mt.previous_month_count IS NULL OR mt.previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (mt.won_lead_count - mt.previous_month_count) * 100.0 / mt.previous_month_count,
      2
    )
  END AS pct_change,
  SUM(mt.won_lead_count) OVER () AS total_matching_leads
FROM monthly_trend mt
ORDER BY mt.month_start ASC;
```

**Generated final answer**

Total won leads: 134

Here is the monthly trend for won leads in that range:

| Month | Won leads | Previous month | % change |
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
| Mar 2026 | 90 | 0 | — |
| Apr 2026 | 44 | 90 | -51.11% |

In Apr 2026, won leads decreased by 46 compared with Mar 2026, a 51.11% decline.

**Execution time:** 173.293 sec
**Status:** ok

## 141. LAQ-141

**Question**

Show the monthly trend for lost leads from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
lost_monthly_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COUNT(*) AS lost_lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'LOST'
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY DATE_TRUNC('month', l.created_at)::date
),
monthly_filled AS (
  SELECT
    m.month_start,
    COALESCE(lmc.lost_lead_count, 0) AS lost_lead_count
  FROM months m
  LEFT JOIN lost_monthly_counts lmc
    ON lmc.month_start = m.month_start
),
monthly_with_change AS (
  SELECT
    month_start,
    lost_lead_count,
    LAG(lost_lead_count) OVER (ORDER BY month_start) AS previous_month_count
  FROM monthly_filled
)
SELECT
  month_start,
  lost_lead_count,
  previous_month_count,
  CASE
    WHEN previous_month_count IS NULL OR previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (lost_lead_count - previous_month_count) * 100.0 / previous_month_count,
      2
    )
  END AS pct_change
FROM monthly_with_change
ORDER BY month_start ASC
```

**Generated final answer**

Here is the monthly trend for lost leads created from May 2025 through Apr 2026.

| Month | Lost leads | Previous month | % change |
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
| Mar 2026 | 49 | 0 | — |
| Apr 2026 | 13 | 49 | -73.47% |

In Apr 2026, lost leads fell from 49 in Mar 2026 to 13, a 73.47% decrease.

**Execution time:** 177.388 sec
**Status:** ok

## 142. LAQ-142

**Question**

Show the monthly trend for follow-up status leads from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
monthly_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND ss.role = 'FOLLOW_UP'
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY DATE_TRUNC('month', l.created_at)::date
),
monthly_filled AS (
  SELECT
    m.month_start,
    COALESCE(mc.lead_count, 0) AS lead_count
  FROM months m
  LEFT JOIN monthly_counts mc
    ON mc.month_start = m.month_start
),
monthly_trend AS (
  SELECT
    month_start,
    lead_count,
    LAG(lead_count) OVER (ORDER BY month_start) AS previous_month_count
  FROM monthly_filled
)
SELECT
  month_start,
  lead_count,
  previous_month_count,
  CASE
    WHEN previous_month_count IS NULL OR previous_month_count = 0 THEN NULL
    ELSE ROUND((lead_count - previous_month_count) * 100.0 / previous_month_count, 2)
  END AS pct_change
FROM monthly_trend
ORDER BY month_start ASC
```

**Generated final answer**

Here is the monthly trend for Follow Up status leads for the full months in your requested range:

| Month | Lead count | Previous month | % change |
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
| Mar 2026 | 11 | 0 | N/A |
| Apr 2026 | 35 | 11 | 218.18% |

In Apr 2026, Follow Up status leads increased to 35 from 11 in Mar 2026, a 218.18% increase.

**Execution time:** 156.581 sec
**Status:** ok

## 143. LAQ-139

**Question**

Show the weekly lead trend by pipeline role from 2026-02-09 to 2026-05-04.

**Generated SQL**

```sql
WITH weeks AS (
  SELECT generate_series(
    DATE_TRUNC('week', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('week', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 week'
  )::date AS week_start
),
roles AS (
  SELECT DISTINCT
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
),
weekly_role_grid AS (
  SELECT
    w.week_start,
    r.pipeline_role
  FROM weeks w
  CROSS JOIN roles r
),
weekly_role_counts AS (
  SELECT
    DATE_TRUNC('week', l.created_at)::date AS week_start,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS pipeline_role,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN sales_statuses ss
    ON ss.id = l.status_id
   AND ss.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('week', l.created_at)::date,
    COALESCE(CAST(ss.role AS text), 'NO_STATUS')
),
weekly_role_filled AS (
  SELECT
    wrg.week_start,
    wrg.pipeline_role,
    COALESCE(wrc.lead_count, 0) AS lead_count
  FROM weekly_role_grid wrg
  LEFT JOIN weekly_role_counts wrc
    ON wrc.week_start = wrg.week_start
   AND wrc.pipeline_role = wrg.pipeline_role
),
weekly_role_trend AS (
  SELECT
    week_start,
    pipeline_role,
    lead_count,
    LAG(lead_count) OVER (
      PARTITION BY pipeline_role
      ORDER BY week_start
    ) AS previous_week_count
  FROM weekly_role_filled
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM weekly_role_filled
)
SELECT
  wrt.week_start,
  wrt.pipeline_role,
  wrt.lead_count,
  wrt.previous_week_count,
  CASE
    WHEN wrt.previous_week_count IS NULL OR wrt.previous_week_count = 0 THEN NULL
    ELSE ROUND(
      (wrt.lead_count - wrt.previous_week_count) * 100.0 / wrt.previous_week_count,
      2
    )
  END AS pct_change,
  t.total_matching_leads
FROM weekly_role_trend wrt
CROSS JOIN total t
ORDER BY wrt.week_start ASC, wrt.pipeline_role ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the weekly trend of leads created, grouped by pipeline role:

Weeks starting Feb 09 to Mar 23:

| Pipeline Role | Feb 09 | Feb 16 | Feb 23 | Mar 02 | Mar 09 | Mar 16 | Mar 23 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Appointment Booked | 0 | 0 | 0 | 1 | 2 (+100.00%) | 0 (-100.00%) | 1 |
| Canceled | 0 | 0 | 0 | 3 | 17 (+466.67%) | 7 (-58.82%) | 5 (-28.57%) |
| Follow Up | 0 | 0 | 0 | 1 | 1 (0.00%) | 0 (-100.00%) | 5 |
| Lost | 0 | 0 | 0 | 10 | 14 (+40.00%) | 11 (-21.43%) | 13 (+18.18%) |
| New Lead | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| No Show | 0 | 0 | 0 | 8 | 9 (+12.50%) | 3 (-66.67%) | 4 (+33.33%) |
| Partial Payment | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rescheduled | 0 | 0 | 0 | 1 | 1 (0.00%) | 4 (+300.00%) | 2 (-50.00%) |
| Unqualified | 0 | 0 | 0 | 1 | 1 (0.00%) | 6 (+500.00%) | 2 (-66.67%) |
| Won | 0 | 0 | 0 | 10 | 41 (+310.00%) | 11 (-73.17%) | 24 (+118.18%) |

Weeks starting Mar 30 to May 04:

| Pipeline Role | Mar 30 | Apr 06 | Apr 13 | Apr 20 | Apr 27 | May 04 |
|---|---:|---:|---:|---:|---:|---:|
| Appointment Booked | 0 (-100.00%) | 1 | 2 (+100.00%) | 30 (+1,400.00%) | 0 (-100.00%) | 0 |
| Canceled | 5 (0.00%) | 8 (+60.00%) | 4 (-50.00%) | 10 (+150.00%) | 0 (-100.00%) | 0 |
| Follow Up | 8 (+60.00%) | 7 (-12.50%) | 3 (-57.14%) | 21 (+600.00%) | 0 (-100.00%) | 0 |
| Lost | 5 (-61.54%) | 3 (-40.00%) | 4 (+33.33%) | 2 (-50.00%) | 0 (-100.00%) | 0 |
| New Lead | 22 (+450.00%) | 20 (-9.09%) | 15 (-25.00%) | 35 (+133.33%) | 0 (-100.00%) | 0 |
| No Show | 4 (0.00%) | 6 (+50.00%) | 7 (+16.67%) | 6 (-14.29%) | 0 (-100.00%) | 0 |
| Partial Payment | 0 | 0 | 1 | 1 (0.00%) | 0 (-100.00%) | 0 |
| Rescheduled | 2 (0.00%) | 5 (+150.00%) | 2 (-60.00%) | 5 (+150.00%) | 0 (-100.00%) | 0 |
| Unqualified | 0 (-100.00%) | 0 | 0 | 0 | 0 | 0 |
| Won | 17 (-29.17%) | 16 (-5.88%) | 10 (-37.50%) | 5 (-50.00%) | 0 (-100.00%) | 0 |

The latest active week was Apr 20, 2026, when New Lead rose from 15 to 35 (+133.33%) and Appointment Booked rose from 2 to 30 (+1,400.00%).

**Execution time:** 239.030 sec
**Status:** ok

## 144. LAQ-144

**Question**

Show the monthly lead trend by first-touch source from 2026-02-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
sources AS (
  SELECT DISTINCT
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
),
monthly_source_grid AS (
  SELECT
    m.month_start,
    s.source
  FROM months m
  CROSS JOIN sources s
),
monthly_source_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    ) AS source,
    COUNT(*) AS lead_count
  FROM leads l
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('month', l.created_at)::date,
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown'
    )
),
monthly_source_filled AS (
  SELECT
    msg.month_start,
    msg.source,
    COALESCE(msc.lead_count, 0) AS lead_count
  FROM monthly_source_grid msg
  LEFT JOIN monthly_source_counts msc
    ON msc.month_start = msg.month_start
   AND msc.source = msg.source
),
monthly_source_totals AS (
  SELECT
    source,
    SUM(lead_count) AS source_total_leads
  FROM monthly_source_filled
  GROUP BY source
),
monthly_source_trend AS (
  SELECT
    msf.month_start,
    msf.source,
    msf.lead_count,
    mst.source_total_leads,
    LAG(msf.lead_count) OVER (
      PARTITION BY msf.source
      ORDER BY msf.month_start
    ) AS previous_month_count
  FROM monthly_source_filled msf
  JOIN monthly_source_totals mst
    ON mst.source = msf.source
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM monthly_source_filled
)
SELECT
  mst.month_start,
  mst.source,
  mst.lead_count,
  mst.previous_month_count,
  CASE
    WHEN mst.previous_month_count IS NULL OR mst.previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (mst.lead_count - mst.previous_month_count) * 100.0 / mst.previous_month_count,
      2
    )
  END AS pct_change,
  mst.source_total_leads,
  t.total_matching_leads
FROM monthly_source_trend mst
CROSS JOIN total t
ORDER BY mst.month_start ASC, mst.source_total_leads DESC, mst.source ASC
```

**Generated final answer**

Total matching leads: 515

Here is the monthly trend by first-touch source for Feb–Apr 2026 within your requested date range:

| First-touch source | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---|---|---|
| Unknown | 0 | 228 | 136 (-40.35%) |
| YouTube | 0 | 3 | 100 (+3,233.33%) |
| Instagram | 0 | 2 | 24 (+1,100.00%) |
| Other | 0 | 1 | 20 (+1,900.00%) |
| Twitter / X | 0 | 0 | 1 |

In Apr 2026, YouTube became the largest identified first-touch source with 100 leads, up from 3 in Mar 2026 (+3,233.33%), while Unknown fell from 228 to 136 (-40.35%).

**Execution time:** 65.805 sec
**Status:** ok

## 145. LAQ-145

**Question**

Show the monthly lead trend by high-level source category from 2026-02-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
sources AS (
  SELECT DISTINCT
    COALESCE(CAST(l.source AS text), 'Unknown') AS source_category
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
),
monthly_source_grid AS (
  SELECT
    m.month_start,
    s.source_category
  FROM months m
  CROSS JOIN sources s
),
monthly_source_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COALESCE(CAST(l.source AS text), 'Unknown') AS source_category,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('month', l.created_at)::date,
    COALESCE(CAST(l.source AS text), 'Unknown')
),
monthly_source_filled AS (
  SELECT
    msg.month_start,
    msg.source_category,
    COALESCE(msc.lead_count, 0) AS lead_count
  FROM monthly_source_grid msg
  LEFT JOIN monthly_source_counts msc
    ON msc.month_start = msg.month_start
   AND msc.source_category = msg.source_category
),
monthly_source_trend AS (
  SELECT
    month_start,
    source_category,
    lead_count,
    LAG(lead_count) OVER (
      PARTITION BY source_category
      ORDER BY month_start
    ) AS previous_month_count,
    SUM(lead_count) OVER (
      PARTITION BY source_category
    ) AS source_total_leads
  FROM monthly_source_filled
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM monthly_source_filled
)
SELECT
  mst.month_start,
  mst.source_category,
  mst.lead_count,
  mst.previous_month_count,
  CASE
    WHEN mst.previous_month_count IS NULL OR mst.previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (mst.lead_count - mst.previous_month_count) * 100.0 / mst.previous_month_count,
      2
    )
  END AS pct_change,
  mst.source_total_leads,
  t.total_matching_leads
FROM monthly_source_trend mst
CROSS JOIN total t
ORDER BY
  mst.source_total_leads DESC,
  mst.source_category ASC,
  mst.month_start ASC
```

**Generated final answer**

Total matching leads: 515

Here is the monthly trend by high-level source category for the requested period:

| Source category | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Other | 0 | 11 | 254 (+2209.09%) |
| Calendly | 0 | 213 | 25 (-88.26%) |
| Manual | 0 | 10 | 2 (-80.00%) |

In Apr 2026, Other became the dominant source at 254 leads (+2209.09% vs Mar), while Calendly dropped to 25 (-88.26%).

**Execution time:** 57.522 sec
**Status:** ok

## 146. LAQ-146

**Question**

Show the monthly lead trend by owner ID from 2026-02-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
owners AS (
  SELECT DISTINCT
    COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS owner_id
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
),
monthly_owner_grid AS (
  SELECT
    m.month_start,
    o.owner_id
  FROM months m
  CROSS JOIN owners o
),
monthly_owner_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS owner_id,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('month', l.created_at)::date,
    COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned')
),
monthly_owner_filled AS (
  SELECT
    mog.month_start,
    mog.owner_id,
    COALESCE(moc.lead_count, 0) AS lead_count
  FROM monthly_owner_grid mog
  LEFT JOIN monthly_owner_counts moc
    ON moc.month_start = mog.month_start
   AND moc.owner_id = mog.owner_id
),
monthly_owner_trend AS (
  SELECT
    mof.month_start,
    mof.owner_id,
    mof.lead_count,
    SUM(mof.lead_count) OVER (PARTITION BY mof.owner_id) AS owner_total_leads,
    LAG(mof.lead_count) OVER (
      PARTITION BY mof.owner_id
      ORDER BY mof.month_start
    ) AS previous_month_count
  FROM monthly_owner_filled mof
),
total AS (
  SELECT SUM(lead_count) AS total_matching_leads
  FROM monthly_owner_filled
)
SELECT
  mot.month_start,
  mot.owner_id,
  mot.lead_count,
  mot.previous_month_count,
  CASE
    WHEN mot.previous_month_count IS NULL OR mot.previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (mot.lead_count - mot.previous_month_count) * 100.0 / mot.previous_month_count,
      2
    )
  END AS pct_change,
  mot.owner_total_leads,
  t.total_matching_leads
FROM monthly_owner_trend mot
CROSS JOIN total t
ORDER BY mot.month_start ASC, mot.owner_total_leads DESC, mot.owner_id ASC
```

**Generated final answer**

Total matching leads: 515

Here is the monthly lead trend by owner ID for the requested range:

| Owner ID | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 0 | 122 | 112 (-8.20%) |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 0 | 105 | 69 (-34.29%) |
| Unassigned | 0 | 5 | 100 (+1,900.00%) |
| user_3ARuEgINlhhlbVsZYBbgBDeOEjr | 0 | 1 | 0 (-100.00%) |
| user_3BTfkOX7RajuoxhqwX7nMytxEmM | 0 | 1 | 0 (-100.00%) |

In Apr 2026, Unassigned leads jumped from 5 to 100 (+1,900.00%), while the two highest-volume owner IDs both declined month over month.

**Execution time:** 65.610 sec
**Status:** ok

## 147. LAQ-147

**Question**

Show the monthly lead trend by setter ID from 2026-02-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS month_start
),
setters AS (
  SELECT DISTINCT
    COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
),
monthly_setter_grid AS (
  SELECT
    m.month_start,
    s.setter_id
  FROM months m
  CROSS JOIN setters s
),
monthly_setter_counts AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY
    DATE_TRUNC('month', l.created_at)::date,
    COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter')
),
monthly_setter_filled AS (
  SELECT
    msg.month_start,
    msg.setter_id,
    COALESCE(msc.lead_count, 0) AS lead_count
  FROM monthly_setter_grid msg
  LEFT JOIN monthly_setter_counts msc
    ON msc.month_start = msg.month_start
   AND msc.setter_id = msg.setter_id
),
monthly_setter_trend AS (
  SELECT
    msf.month_start,
    msf.setter_id,
    msf.lead_count,
    SUM(msf.lead_count) OVER (
      PARTITION BY msf.setter_id
    ) AS setter_total_leads,
    LAG(msf.lead_count) OVER (
      PARTITION BY msf.setter_id
      ORDER BY msf.month_start
    ) AS previous_month_count
  FROM monthly_setter_filled msf
),
total AS (
  SELECT COALESCE(SUM(lead_count), 0) AS total_matching_leads
  FROM monthly_setter_filled
)
SELECT
  mst.month_start,
  mst.setter_id,
  mst.lead_count,
  mst.previous_month_count,
  CASE
    WHEN mst.previous_month_count IS NULL OR mst.previous_month_count = 0 THEN NULL
    ELSE ROUND(
      (mst.lead_count - mst.previous_month_count) * 100.0 / mst.previous_month_count,
      2
    )
  END AS pct_change,
  mst.setter_total_leads,
  t.total_matching_leads
FROM monthly_setter_trend mst
CROSS JOIN total t
ORDER BY mst.month_start ASC, mst.setter_id ASC;
```

**Generated final answer**

Total matching leads: 515

Here is the monthly lead trend by setter ID:

| Setter ID | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| No Setter | 0 | 169 | 236 (+39.64%) |
| user_3AesMObeGeZynVoGhloMkfwanES | 0 | 63 | 45 (-28.57%) |
| user_3AZfvBICuFGTCNu4QeqiP6xN03Q | 0 | 2 | 0 (-100.00%) |

In Apr 2026, the largest category was No Setter with 236 leads, up from 169 in Mar 2026 (+39.64%).

**Execution time:** 65.224 sec
**Status:** ok
