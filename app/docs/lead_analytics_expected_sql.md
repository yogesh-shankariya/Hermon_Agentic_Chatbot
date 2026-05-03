# Lead Analytics Expected SQL and Tabular Answers

This file is the manual test matrix for the `lead_analytics` skill.

Expected answer means the raw tabular data returned by SQL/source data, not the final AI prose response.

## Global Expectations

| Rule | Expected behavior |
|---|---|
| Tenant filter | Every SQL pattern must use `l.clerk_org_id = :org_id` for lead queries. |
| Soft deletes | Exclude deleted leads with `l.is_deleted = false` unless the user explicitly asks about deleted leads. |
| SQL shape | Generate exactly one PostgreSQL `SELECT` or `WITH ... SELECT` statement. |
| Safety | Never generate write/admin SQL, multiple statements, `SELECT *`, hardcoded org IDs, secrets, raw payloads, or credentials. |
| Parameters | Use named parameters such as `:org_id`, `:start_date`, `:end_date`, `:status_role`, `:status_name`, `:lead_source`, `:owner_id`, `:setter_id`, `:cutoff_date`, `:limit`, and `:search_text`. |
| Joins | Join `sales_statuses` and `marketing_sources` with matching `clerk_org_id`. |
| List defaults | Default list limit is `20` unless the user asks for a specific limit. |
| Contact details | Do not include email or phone unless the user explicitly asks for contact details. |
| Owner/setter names | `assigned_to` and `setter_id` are user IDs. Do not invent names. |
| Operational follow-up | Exclude terminal roles `WON`, `LOST`, `UNQUALIFIED`, and `CANCELED` by default for stale/overdue/no-next-touch questions. |

## Question Coverage Matrix

| ID | User question to test | Expected SQL pattern | Params | Expected raw answer table |
|---|---|---|---|---|
| Q001 | How many active leads do we have? | P001 | `:org_id` | `active_leads` |
| Q002 | How many leads do we have? | P001 | `:org_id` | `active_leads` |
| Q003 | How many non-deleted leads are there? | P001 | `:org_id` | `active_leads` |
| Q004 | How many deleted leads do we have? | P002 | `:org_id` | `deleted_leads` |
| Q005 | How many leads do we have including deleted leads? | P003 | `:org_id` | `total_leads_including_deleted` |
| Q006 | Break down active leads by pipeline role. | P004 | `:org_id` | `status_role`, `lead_count` |
| Q007 | What is the lead breakdown by status role? | P004 | `:org_id` | `status_role`, `lead_count` |
| Q008 | Break down active leads by exact status. | P005 | `:org_id` | `status_name`, `lead_count` |
| Q009 | What is the lead breakdown by pipeline status name? | P005 | `:org_id` | `status_name`, `lead_count` |
| Q010 | Which pipeline statuses exist? | P006 | `:org_id` | `status_name`, `status_role`, `is_default`, `is_system`, `status_description` |
| Q011 | Show status setup by role. | P007 | `:org_id` | `status_role`, `status_count` |
| Q012 | How many new leads are there? | P008 | `:org_id`, `:status_role = 'NEW_LEAD'` | `lead_count` |
| Q013 | How many appointment booked leads are there? | P008 | `:org_id`, `:status_role = 'APPOINTMENT_BOOKED'` | `lead_count` |
| Q014 | How many no-show leads are there? | P008 | `:org_id`, `:status_role = 'NO_SHOW'` | `lead_count` |
| Q015 | How many rescheduled leads are there? | P008 | `:org_id`, `:status_role = 'RESCHEDULED'` | `lead_count` |
| Q016 | How many canceled leads are there? | P008 | `:org_id`, `:status_role = 'CANCELED'` | `lead_count` |
| Q017 | How many partial payment leads are there? | P008 | `:org_id`, `:status_role = 'PARTIAL_PAYMENT'` | `lead_count` |
| Q018 | How many won leads are there? | P008 | `:org_id`, `:status_role = 'WON'` | `lead_count` |
| Q019 | How many unqualified leads are there? | P008 | `:org_id`, `:status_role = 'UNQUALIFIED'` | `lead_count` |
| Q020 | How many follow-up leads are there? | P008 | `:org_id`, `:status_role = 'FOLLOW_UP'` | `lead_count` |
| Q021 | How many lost leads are there? | P008 | `:org_id`, `:status_role = 'LOST'` | `lead_count` |
| Q022 | Which leads are new leads? | P009 | `:org_id`, `:status_role = 'NEW_LEAD'`, `:limit` | `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |
| Q023 | Which leads are no-show? | P009 | `:org_id`, `:status_role = 'NO_SHOW'`, `:limit` | list lead columns |
| Q024 | Which leads are won? | P009 | `:org_id`, `:status_role = 'WON'`, `:limit` | list lead columns |
| Q025 | How many leads are in exact status No Sale - Follow Up? | P010 | `:org_id`, `:status_name` | `lead_count` |
| Q026 | Which leads are in exact status No Sale - Follow Up? | P011 | `:org_id`, `:status_name`, `:limit` | list lead columns |
| Q027 | How many leads have no status? | P012 | `:org_id` | `leads_without_status` |
| Q028 | Which leads have no status? | P013 | `:org_id`, `:limit` | list lead columns |
| Q029 | How many leads have a missing or orphaned status? | P014 | `:org_id` | `leads_with_missing_status_join` |
| Q030 | How many leads came from each source? | P015 | `:org_id` | `source`, `lead_count` |
| Q031 | Which source has the most leads? | P016 | `:org_id`, `:limit = 1` | `source`, `lead_count` |
| Q032 | How many Calendly leads do we have? | P017 | `:org_id`, `:lead_source = 'CALENDLY'` | `lead_count` |
| Q033 | How many manual leads do we have? | P017 | `:org_id`, `:lead_source = 'MANUAL'` | `lead_count` |
| Q034 | How many Typeform leads do we have? | P017 | `:org_id`, `:lead_source = 'TYPEFORM'` | `lead_count` |
| Q035 | How many webinar leads do we have? | P017 | `:org_id`, `:lead_source = 'WEBINAR'` | `lead_count` |
| Q036 | How many newsletter leads do we have? | P017 | `:org_id`, `:lead_source = 'NEWSLETTER'` | `lead_count` |
| Q037 | How many landing page leads do we have? | P017 | `:org_id`, `:lead_source = 'LANDING_PAGE'` | `lead_count` |
| Q038 | How many other-source leads do we have? | P017 | `:org_id`, `:lead_source = 'OTHER'` | `lead_count` |
| Q039 | Which leads came from Calendly? | P018 | `:org_id`, `:lead_source`, `:limit` | list lead columns |
| Q040 | Break down leads by first source name. | P019 | `:org_id` | `first_source_name`, `lead_count` |
| Q041 | Break down leads by last source name. | P020 | `:org_id` | `last_source_name`, `lead_count` |
| Q042 | Break down leads by first and last source. | P021 | `:org_id` | `first_source_name`, `last_source_name`, `lead_count` |
| Q043 | Which first source has the most leads? | P022 | `:org_id`, `:limit = 1` | `first_source_name`, `lead_count` |
| Q044 | Which last source has the most leads? | P023 | `:org_id`, `:limit = 1` | `last_source_name`, `lead_count` |
| Q045 | Break down leads by normalized first marketing source. | P024 | `:org_id` | `normalized_first_source`, `lead_count` |
| Q046 | Break down leads by normalized last marketing source. | P025 | `:org_id` | `normalized_last_source`, `lead_count` |
| Q047 | Show marketing source metadata. | P026 | `:org_id` | `source_name`, `aliases`, `description`, `is_archived` |
| Q048 | Which marketing sources are archived? | P027 | `:org_id` | `source_name`, `aliases`, `description` |
| Q049 | How many leads are assigned to each owner? | P028 | `:org_id` | `assigned_to`, `lead_count` |
| Q050 | How many leads are assigned to each rep? | P028 | `:org_id` | `assigned_to`, `lead_count` |
| Q051 | How many leads are assigned to each setter? | P029 | `:org_id` | `setter_id`, `lead_count` |
| Q052 | How many leads have no owner? | P030 | `:org_id` | `unassigned_leads` |
| Q053 | Which leads have no owner? | P031 | `:org_id`, `:limit` | `id`, `display_name`, `status_name`, `status_role`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |
| Q054 | How many leads have no setter? | P032 | `:org_id` | `leads_without_setter` |
| Q055 | Which leads have no setter? | P033 | `:org_id`, `:limit` | `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |
| Q056 | How many leads are assigned to owner user_abc? | P034 | `:org_id`, `:owner_id` | `lead_count` |
| Q057 | Which leads are assigned to owner user_abc? | P035 | `:org_id`, `:owner_id`, `:limit` | list lead columns |
| Q058 | How many leads are assigned to setter user_abc? | P036 | `:org_id`, `:setter_id` | `lead_count` |
| Q059 | Which leads are assigned to setter user_abc? | P037 | `:org_id`, `:setter_id`, `:limit` | list lead columns |
| Q060 | How many leads have no next touch point? | P038 | `:org_id` | `leads_missing_next_touch_point` |
| Q061 | Which leads have no next touch point? | P039 | `:org_id`, `:limit` | list lead columns |
| Q062 | How many leads are overdue for follow-up? | P040 | `:org_id` | `overdue_next_touch_points` |
| Q063 | Which leads are overdue for follow-up? | P041 | `:org_id`, `:limit` | list lead columns |
| Q064 | Which leads need follow-up? | P042 | `:org_id`, `:limit` | list lead columns |
| Q065 | Which leads are stale? | P042 | `:org_id`, `:limit` | list lead columns |
| Q066 | Which leads are stuck? | P042 | `:org_id`, `:limit` | list lead columns |
| Q067 | Count stale leads by status. | P043 | `:org_id` | `status_name`, `status_role`, `stale_lead_count` |
| Q068 | How many leads need follow-up today? | P044 | `:org_id`, `:start_date`, `:end_date` | `leads_due_in_period` |
| Q069 | Which leads need follow-up today? | P045 | `:org_id`, `:start_date`, `:end_date`, `:limit` | list lead columns |
| Q070 | Break down follow-ups by next touch point type. | P046 | `:org_id` | `next_touch_point_type`, `lead_count` |
| Q071 | How many leads need a WhatsApp follow-up? | P047 | `:org_id`, `:next_touch_point_type = 'WHATSAPP'` | `lead_count` |
| Q072 | Which leads need an email follow-up? | P048 | `:org_id`, `:next_touch_point_type = 'EMAIL'`, `:limit` | list lead columns |
| Q073 | Leads not updated since a cutoff date by status. | P049 | `:org_id`, `:cutoff_date` | `status_name`, `status_role`, `not_updated_lead_count` |
| Q074 | Which leads have not been updated since a cutoff date? | P050 | `:org_id`, `:cutoff_date`, `:limit` | list lead columns |
| Q075 | How many leads were created today? | P051 | `:org_id`, `:start_date`, `:end_date` | `leads_created_in_period` |
| Q076 | How many leads were created this week? | P051 | `:org_id`, `:start_date`, `:end_date` | `leads_created_in_period` |
| Q077 | How many leads were created this month? | P051 | `:org_id`, `:start_date`, `:end_date` | `leads_created_in_period` |
| Q078 | How many new leads were created this month? | P052 | `:org_id`, `:start_date`, `:end_date`, `:status_role = 'NEW_LEAD'` | `new_leads_created_in_period` |
| Q079 | Lead creation trend by day. | P053 | `:org_id`, `:start_date`, `:end_date` | `lead_created_date`, `lead_count` |
| Q080 | Lead creation trend by week. | P054 | `:org_id`, `:start_date`, `:end_date` | `week_start`, `lead_count` |
| Q081 | Lead creation trend by month. | P055 | `:org_id`, `:start_date`, `:end_date` | `month_start`, `lead_count` |
| Q082 | Compare lead growth month over month. | P056 | `:org_id`, `:start_date`, `:end_date` | `month_start`, `lead_count`, `previous_month_lead_count`, `percentage_change_from_previous_month` |
| Q083 | Break down created leads by source for a date range. | P057 | `:org_id`, `:start_date`, `:end_date` | `source`, `lead_count` |
| Q084 | Break down created leads by status role for a date range. | P058 | `:org_id`, `:start_date`, `:end_date` | `status_role`, `lead_count` |
| Q085 | Show recent leads. | P059 | `:org_id`, `:limit` | list lead columns |
| Q086 | Show recent leads with emails and phone numbers. | P060 | `:org_id`, `:limit` | `id`, `display_name`, `email`, `phone_e164`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `created_at` |
| Q087 | Find leads named John. | P061 | `:org_id`, `:search_text`, `:limit` | list lead columns |
| Q088 | Find lead by email john@example.com. | P062 | `:org_id`, `:email`, `:limit` | contact detail columns |
| Q089 | How many leads are missing email? | P063 | `:org_id` | `leads_missing_email` |
| Q090 | Which leads are missing phone number? | P064 | `:org_id`, `:limit` | `id`, `display_name`, `email`, `phone_e164`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `created_at` |
| Q091 | Which deleted leads exist? | P065 | `:org_id`, `:limit` | `id`, `display_name`, `status_name`, `status_role`, `source`, `deleted_at`, `created_at` |
| Q092 | How many duplicate lead emails exist? | P066 | `:org_id` | `duplicate_email_count` |
| Q093 | Which lead emails are duplicated? | P067 | `:org_id`, `:limit` | `email`, `lead_count` |
| Q094 | How many leads are missing first source name? | P068 | `:org_id` | `leads_missing_first_source_name` |
| Q095 | How many leads are missing last source name? | P069 | `:org_id` | `leads_missing_last_source_name` |
| Q096 | How many leads have orphaned first marketing source IDs? | P070 | `:org_id` | `orphaned_first_source_ids` |
| Q097 | How many leads have orphaned last marketing source IDs? | P071 | `:org_id` | `orphaned_last_source_ids` |
| Q098 | Revenue by lead source. | N/A | N/A | No SQL. Out of scope; use `revenue_analytics`. |
| Q099 | Appointment no-show rate by host. | N/A | N/A | No SQL. Out of scope; use `appointment_analytics`. |
| Q100 | UTM campaign conversion by landing page. | N/A | N/A | No SQL. Out of scope; use `acquisition_analytics`. |
| Q101 | Full summary for one lead with notes, calls, contracts, and payments. | N/A | N/A | No SQL. Out of scope; use `lead_360`. |
| Q102 | Check webhook payloads or provider credentials. | N/A | N/A | No SQL. Out of scope; integration/admin skill only. |
| Q103 | Delete old leads. | N/A | N/A | No SQL. Refuse write/admin request. |

## SQL Patterns

### P001 - Count Active Leads

| Expected raw answer table |
|---|
| `active_leads` |

```sql
SELECT COUNT(*) AS active_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false;
```

### P002 - Count Deleted Leads

| Expected raw answer table |
|---|
| `deleted_leads` |

```sql
SELECT COUNT(*) AS deleted_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = true;
```

### P003 - Count All Leads Including Deleted

| Expected raw answer table |
|---|
| `total_leads_including_deleted` |

```sql
SELECT COUNT(*) AS total_leads_including_deleted
FROM leads l
WHERE l.clerk_org_id = :org_id;
```

### P004 - Leads by Normalized Status Role

| Expected raw answer table |
|---|
| `status_role`, `lead_count` |

```sql
SELECT
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COUNT(*) AS lead_count
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY lead_count DESC, status_role ASC;
```

### P005 - Leads by Exact Status Name

| Expected raw answer table |
|---|
| `status_name`, `lead_count` |

```sql
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
ORDER BY lead_count DESC, status_name ASC;
```

### P006 - List Pipeline Statuses

| Expected raw answer table |
|---|
| `status_name`, `status_role`, `is_default`, `is_system`, `status_description` |

```sql
SELECT
  ss.name AS status_name,
  CAST(ss.role AS text) AS status_role,
  ss.is_default,
  ss.is_system,
  ss.description AS status_description
FROM sales_statuses ss
WHERE ss.clerk_org_id = :org_id
ORDER BY ss.is_default DESC, ss.name ASC;
```

### P007 - Status Setup by Role

| Expected raw answer table |
|---|
| `status_role`, `status_count` |

```sql
SELECT
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COUNT(*) AS status_count
FROM sales_statuses ss
WHERE ss.clerk_org_id = :org_id
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY status_count DESC, status_role ASC;
```

### P008 - Count Leads by Specific Normalized Status Role

| Expected raw answer table |
|---|
| `lead_count` |

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

### P009 - List Leads by Specific Normalized Status Role

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND ss.role = :status_role
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P010 - Count Leads by Exact Status Name

| Expected raw answer table |
|---|
| `lead_count` |

```sql
SELECT COUNT(*) AS lead_count
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.name = :status_name;
```

### P011 - List Leads by Exact Status Name

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND ss.name = :status_name
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P012 - Count Leads with No Status ID

| Expected raw answer table |
|---|
| `leads_without_status` |

```sql
SELECT COUNT(*) AS leads_without_status
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.status_id IS NULL;
```

### P013 - List Leads with No Status ID

| Expected raw answer table |
|---|
| `id`, `display_name`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
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
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P014 - Count Leads with Missing Status Join

| Expected raw answer table |
|---|
| `leads_with_missing_status_join` |

```sql
SELECT COUNT(*) AS leads_with_missing_status_join
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.id IS NULL;
```

### P015 - Leads by Source Enum

| Expected raw answer table |
|---|
| `source`, `lead_count` |

```sql
SELECT
  l.source,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY l.source
ORDER BY lead_count DESC, l.source ASC;
```

### P016 - Top Source Enum

| Expected raw answer table |
|---|
| `source`, `lead_count` |

```sql
SELECT
  l.source,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY l.source
ORDER BY lead_count DESC, l.source ASC
LIMIT :limit;
```

### P017 - Count Leads by Specific Source Enum

| Expected raw answer table |
|---|
| `lead_count` |

```sql
SELECT COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.source = :lead_source;
```

### P018 - List Leads by Specific Source Enum

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND l.source = :lead_source
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P019 - Leads by First Source Name

| Expected raw answer table |
|---|
| `first_source_name`, `lead_count` |

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown') AS first_source_name,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, first_source_name ASC;
```

### P020 - Leads by Last Source Name

| Expected raw answer table |
|---|
| `last_source_name`, `lead_count` |

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown') AS last_source_name,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, last_source_name ASC;
```

### P021 - Leads by First and Last Source Names

| Expected raw answer table |
|---|
| `first_source_name`, `last_source_name`, `lead_count` |

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown') AS first_source_name,
  COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown') AS last_source_name,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY
  COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown'),
  COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, first_source_name ASC, last_source_name ASC;
```

### P022 - Top First Source Name

| Expected raw answer table |
|---|
| `first_source_name`, `lead_count` |

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown') AS first_source_name,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.first_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, first_source_name ASC
LIMIT :limit;
```

### P023 - Top Last Source Name

| Expected raw answer table |
|---|
| `last_source_name`, `lead_count` |

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown') AS last_source_name,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.last_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, last_source_name ASC
LIMIT :limit;
```

### P024 - Leads by Normalized First Marketing Source

| Expected raw answer table |
|---|
| `normalized_first_source`, `lead_count` |

```sql
SELECT
  COALESCE(first_ms.name, NULLIF(TRIM(l.first_source_name), ''), 'Unknown') AS normalized_first_source,
  COUNT(*) AS lead_count
FROM leads l
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(first_ms.name, NULLIF(TRIM(l.first_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, normalized_first_source ASC;
```

### P025 - Leads by Normalized Last Marketing Source

| Expected raw answer table |
|---|
| `normalized_last_source`, `lead_count` |

```sql
SELECT
  COALESCE(last_ms.name, NULLIF(TRIM(l.last_source_name), ''), 'Unknown') AS normalized_last_source,
  COUNT(*) AS lead_count
FROM leads l
LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(last_ms.name, NULLIF(TRIM(l.last_source_name), ''), 'Unknown')
ORDER BY lead_count DESC, normalized_last_source ASC;
```

### P026 - Marketing Source Metadata

| Expected raw answer table |
|---|
| `source_name`, `aliases`, `description`, `is_archived` |

```sql
SELECT
  ms.name AS source_name,
  ms.aliases,
  ms.description,
  ms.is_archived
FROM marketing_sources ms
WHERE ms.clerk_org_id = :org_id
ORDER BY ms.is_archived ASC, ms.name ASC;
```

### P027 - Archived Marketing Sources

| Expected raw answer table |
|---|
| `source_name`, `aliases`, `description` |

```sql
SELECT
  ms.name AS source_name,
  ms.aliases,
  ms.description
FROM marketing_sources ms
WHERE ms.clerk_org_id = :org_id
  AND ms.is_archived = true
ORDER BY ms.name ASC;
```

### P028 - Leads by Owner

| Expected raw answer table |
|---|
| `assigned_to`, `lead_count` |

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned')
ORDER BY lead_count DESC, assigned_to ASC;
```

### P029 - Leads by Setter

| Expected raw answer table |
|---|
| `setter_id`, `lead_count` |

```sql
SELECT
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter')
ORDER BY lead_count DESC, setter_id ASC;
```

### P030 - Count Leads with No Owner

| Expected raw answer table |
|---|
| `unassigned_leads` |

```sql
SELECT COUNT(*) AS unassigned_leads
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.assigned_to), '') IS NULL;
```

### P031 - List Leads with No Owner

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
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
  AND NULLIF(TRIM(l.assigned_to), '') IS NULL
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P032 - Count Leads with No Setter

| Expected raw answer table |
|---|
| `leads_without_setter` |

```sql
SELECT COUNT(*) AS leads_without_setter
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.setter_id), '') IS NULL;
```

### P033 - List Leads with No Setter

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
LIMIT :limit;
```

### P034 - Count Leads by Owner

| Expected raw answer table |
|---|
| `lead_count` |

```sql
SELECT COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.assigned_to = :owner_id;
```

### P035 - List Leads by Owner

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND l.assigned_to = :owner_id
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P036 - Count Leads by Setter

| Expected raw answer table |
|---|
| `lead_count` |

```sql
SELECT COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.setter_id = :setter_id;
```

### P037 - List Leads by Setter

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND l.setter_id = :setter_id
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P038 - Count Leads Missing Next Touch Point

| Expected raw answer table |
|---|
| `leads_missing_next_touch_point` |

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

### P039 - List Leads Missing Next Touch Point

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
ORDER BY l.updated_at ASC, l.created_at ASC, l.id ASC
LIMIT :limit;
```

### P040 - Count Overdue Next Touch Points

| Expected raw answer table |
|---|
| `overdue_next_touch_points` |

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

### P041 - List Overdue Next Touch Points

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
ORDER BY l.next_touch_point_at ASC, l.updated_at ASC, l.created_at ASC, l.id ASC
LIMIT :limit;
```

### P042 - List Stale or Stuck Leads

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
LIMIT :limit;
```

### P043 - Stale Leads by Status

| Expected raw answer table |
|---|
| `status_name`, `status_role`, `stale_lead_count` |

```sql
SELECT
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COUNT(*) AS stale_lead_count
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
GROUP BY
  COALESCE(ss.name, 'No Status'),
  COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY stale_lead_count DESC, status_name ASC;
```

### P044 - Count Leads Due for Follow-Up in a Period

| Expected raw answer table |
|---|
| `leads_due_in_period` |

```sql
SELECT COUNT(*) AS leads_due_in_period
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
  AND l.next_touch_point_at >= :start_date
  AND l.next_touch_point_at < :end_date;
```

### P045 - List Leads Due for Follow-Up in a Period

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND l.next_touch_point_at >= :start_date
  AND l.next_touch_point_at < :end_date
ORDER BY l.next_touch_point_at ASC, l.created_at ASC, l.id ASC
LIMIT :limit;
```

### P046 - Leads by Next Touch Point Type

| Expected raw answer table |
|---|
| `next_touch_point_type`, `lead_count` |

```sql
SELECT
  COALESCE(CAST(l.next_touch_point_type AS text), 'NO_NEXT_TOUCH_POINT_TYPE') AS next_touch_point_type,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
GROUP BY COALESCE(CAST(l.next_touch_point_type AS text), 'NO_NEXT_TOUCH_POINT_TYPE')
ORDER BY lead_count DESC, next_touch_point_type ASC;
```

### P047 - Count Leads by Next Touch Point Type

| Expected raw answer table |
|---|
| `lead_count` |

```sql
SELECT COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.next_touch_point_type = :next_touch_point_type;
```

### P048 - List Leads by Next Touch Point Type

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND l.next_touch_point_type = :next_touch_point_type
ORDER BY l.next_touch_point_at ASC NULLS LAST, l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P049 - Leads Not Updated Since Cutoff by Status

| Expected raw answer table |
|---|
| `status_name`, `status_role`, `not_updated_lead_count` |

```sql
SELECT
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COUNT(*) AS not_updated_lead_count
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.updated_at < :cutoff_date
GROUP BY
  COALESCE(ss.name, 'No Status'),
  COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY not_updated_lead_count DESC, status_name ASC;
```

### P050 - List Leads Not Updated Since Cutoff

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND l.updated_at < :cutoff_date
ORDER BY l.updated_at ASC, l.created_at ASC, l.id ASC
LIMIT :limit;
```

### P051 - Count Leads Created in a Date Range

| Expected raw answer table |
|---|
| `leads_created_in_period` |

```sql
SELECT COUNT(*) AS leads_created_in_period
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

### P052 - Count New Leads Created in a Date Range

| Expected raw answer table |
|---|
| `new_leads_created_in_period` |

```sql
SELECT COUNT(*) AS new_leads_created_in_period
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND ss.role = :status_role
  AND l.created_at >= :start_date
  AND l.created_at < :end_date;
```

### P053 - Lead Creation Trend by Day

| Expected raw answer table |
|---|
| `lead_created_date`, `lead_count` |

```sql
SELECT
  DATE_TRUNC('day', l.created_at)::date AS lead_created_date,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY DATE_TRUNC('day', l.created_at)::date
ORDER BY lead_created_date ASC;
```

### P054 - Lead Creation Trend by Week

| Expected raw answer table |
|---|
| `week_start`, `lead_count` |

```sql
SELECT
  DATE_TRUNC('week', l.created_at)::date AS week_start,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY DATE_TRUNC('week', l.created_at)::date
ORDER BY week_start ASC;
```

### P055 - Lead Creation Trend by Month

| Expected raw answer table |
|---|
| `month_start`, `lead_count` |

```sql
SELECT
  DATE_TRUNC('month', l.created_at)::date AS month_start,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY DATE_TRUNC('month', l.created_at)::date
ORDER BY month_start ASC;
```

### P056 - Month over Month Lead Growth

| Expected raw answer table |
|---|
| `month_start`, `lead_count`, `previous_month_lead_count`, `percentage_change_from_previous_month` |

```sql
WITH monthly_leads AS (
  SELECT
    DATE_TRUNC('month', l.created_at)::date AS month_start,
    COUNT(*) AS lead_count
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND l.created_at >= :start_date
    AND l.created_at < :end_date
  GROUP BY DATE_TRUNC('month', l.created_at)::date
)
SELECT
  month_start,
  lead_count,
  LAG(lead_count) OVER (ORDER BY month_start) AS previous_month_lead_count,
  ROUND(
    (
      (lead_count - LAG(lead_count) OVER (ORDER BY month_start))::numeric
      / NULLIF(LAG(lead_count) OVER (ORDER BY month_start), 0)::numeric
    ) * 100,
    2
  ) AS percentage_change_from_previous_month
FROM monthly_leads
ORDER BY month_start ASC;
```

### P057 - Created Leads by Source in a Date Range

| Expected raw answer table |
|---|
| `source`, `lead_count` |

```sql
SELECT
  l.source,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.created_at >= :start_date
  AND l.created_at < :end_date
GROUP BY l.source
ORDER BY lead_count DESC, l.source ASC;
```

### P058 - Created Leads by Status Role in a Date Range

| Expected raw answer table |
|---|
| `status_role`, `lead_count` |

```sql
SELECT
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
GROUP BY COALESCE(CAST(ss.role AS text), 'NO_STATUS')
ORDER BY lead_count DESC, status_role ASC;
```

### P059 - Recent Leads

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P060 - Recent Leads with Contact Details

| Expected raw answer table |
|---|
| `id`, `display_name`, `email`, `phone_e164`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `created_at` |

```sql
SELECT
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  l.email,
  l.phone_e164,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P061 - Search Leads by Name

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `next_touch_point_at`, `created_at`, `updated_at` |

```sql
SELECT
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
  AND (
    l.full_name ILIKE :search_text
    OR l.first_name ILIKE :search_text
    OR l.last_name ILIKE :search_text
    OR CONCAT_WS(' ', l.first_name, l.last_name) ILIKE :search_text
  )
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P062 - Find Lead by Email

| Expected raw answer table |
|---|
| `id`, `display_name`, `email`, `phone_e164`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `created_at`, `updated_at` |

```sql
SELECT
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  l.email,
  l.phone_e164,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.created_at,
  l.updated_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND LOWER(l.email) = LOWER(:email)
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P063 - Count Leads Missing Email

| Expected raw answer table |
|---|
| `leads_missing_email` |

```sql
SELECT COUNT(*) AS leads_missing_email
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.email), '') IS NULL;
```

### P064 - List Leads Missing Phone Number

| Expected raw answer table |
|---|
| `id`, `display_name`, `email`, `phone_e164`, `status_name`, `status_role`, `assigned_to`, `setter_id`, `source`, `created_at` |

```sql
SELECT
  l.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  l.email,
  l.phone_e164,
  COALESCE(ss.name, 'No Status') AS status_name,
  COALESCE(CAST(ss.role AS text), 'NO_STATUS') AS status_role,
  COALESCE(NULLIF(TRIM(l.assigned_to), ''), 'Unassigned') AS assigned_to,
  COALESCE(NULLIF(TRIM(l.setter_id), ''), 'No Setter') AS setter_id,
  l.source,
  l.created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.phone_e164), '') IS NULL
ORDER BY l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P065 - List Deleted Leads

| Expected raw answer table |
|---|
| `id`, `display_name`, `status_name`, `status_role`, `source`, `deleted_at`, `created_at` |

```sql
SELECT
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
  l.deleted_at,
  l.created_at
FROM leads l
LEFT JOIN sales_statuses ss
  ON ss.id = l.status_id
 AND ss.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = true
ORDER BY l.deleted_at DESC NULLS LAST, l.created_at DESC, l.id ASC
LIMIT :limit;
```

### P066 - Count Duplicate Lead Emails

| Expected raw answer table |
|---|
| `duplicate_email_count` |

```sql
WITH duplicate_emails AS (
  SELECT
    LOWER(TRIM(l.email)) AS normalized_email
  FROM leads l
  WHERE l.clerk_org_id = :org_id
    AND l.is_deleted = false
    AND NULLIF(TRIM(l.email), '') IS NOT NULL
  GROUP BY LOWER(TRIM(l.email))
  HAVING COUNT(*) > 1
)
SELECT COUNT(*) AS duplicate_email_count
FROM duplicate_emails;
```

### P067 - List Duplicate Lead Emails

| Expected raw answer table |
|---|
| `email`, `lead_count` |

```sql
SELECT
  LOWER(TRIM(l.email)) AS email,
  COUNT(*) AS lead_count
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.email), '') IS NOT NULL
GROUP BY LOWER(TRIM(l.email))
HAVING COUNT(*) > 1
ORDER BY lead_count DESC, email ASC
LIMIT :limit;
```

### P068 - Count Leads Missing First Source Name

| Expected raw answer table |
|---|
| `leads_missing_first_source_name` |

```sql
SELECT COUNT(*) AS leads_missing_first_source_name
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.first_source_name), '') IS NULL;
```

### P069 - Count Leads Missing Last Source Name

| Expected raw answer table |
|---|
| `leads_missing_last_source_name` |

```sql
SELECT COUNT(*) AS leads_missing_last_source_name
FROM leads l
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND NULLIF(TRIM(l.last_source_name), '') IS NULL;
```

### P070 - Count Orphaned First Marketing Source IDs

| Expected raw answer table |
|---|
| `orphaned_first_source_ids` |

```sql
SELECT COUNT(*) AS orphaned_first_source_ids
FROM leads l
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.first_source_id IS NOT NULL
  AND first_ms.id IS NULL;
```

### P071 - Count Orphaned Last Marketing Source IDs

| Expected raw answer table |
|---|
| `orphaned_last_source_ids` |

```sql
SELECT COUNT(*) AS orphaned_last_source_ids
FROM leads l
LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
WHERE l.clerk_org_id = :org_id
  AND l.is_deleted = false
  AND l.last_source_id IS NOT NULL
  AND last_ms.id IS NULL;
```

## Enum Variant Coverage

| Enum | Values that must be tested |
|---|---|
| `SalesStatusRole` | `NEW_LEAD`, `APPOINTMENT_BOOKED`, `NO_SHOW`, `RESCHEDULED`, `CANCELED`, `PARTIAL_PAYMENT`, `WON`, `UNQUALIFIED`, `FOLLOW_UP`, `LOST` |
| `LeadSource` | `CALENDLY`, `MANUAL`, `TYPEFORM`, `WEBINAR`, `NEWSLETTER`, `LANDING_PAGE`, `OTHER` |
| `NextTouchPointType` | `PHONE_CALL`, `WHATSAPP`, `EMAIL`, `FOLLOW_UP_CALL`, `PROPOSAL_REVIEW`, `OTHER` |

## Unsupported Question Expectations

| User question type | Expected behavior |
|---|---|
| Revenue, invoices, refunds, contracts, payments, subscriptions | No SQL from `lead_analytics`; route to `revenue_analytics`. |
| Appointment no-show rate, no-shows by host, event, call date, or appointment type | No SQL from `lead_analytics`; route to `appointment_analytics`. |
| UTM, form answers, traffic attribution, landing-page conversion | No SQL from `lead_analytics`; route to `acquisition_analytics`. |
| Full single-lead timeline with notes, calls, contracts, payments | No SQL from `lead_analytics`; route to `lead_360`. |
| Provider integrations, credentials, API keys, webhooks, raw payloads | No SQL from `lead_analytics`; refuse or route to integration/admin skill. |
| Any write/admin request such as delete, update, create, export via COPY, analyze, vacuum | No SQL execution; refuse unsafe request. |
