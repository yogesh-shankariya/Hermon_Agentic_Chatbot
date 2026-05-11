# Skill: `revenue_analytics`

## Short Description

Use this skill for read-only SQL questions about revenue, contracts, programs, payments, payment links, payment proofs, refunds, invoices, subscriptions, and unmatched payments.

This skill must generate SQL only. The application will execute the SQL through a safe read-only database helper.

## When To Use This Skill

Use `revenue_analytics` for read-only SQL analytics questions related to revenue, payments, contracts, programs, refunds, invoices, payment links, payment proofs, subscriptions, MRR, and unmatched payment reconciliation.

Use this skill for:

- Net collected revenue, using paid payments minus succeeded refunds.
- Gross paid revenue from paid payments.
- Revenue collected by today, week, month, or custom date range.
- Revenue trends by day, week, month, or custom date range.
- Revenue breakdowns by currency, payment provider, program, lead source, or payment type.
- Payment counts and payment amount breakdowns by status, type, provider, or currency.
- Pending, failed, lost, refunded, overdue, outstanding, or due-soon payment analysis.
- Lists of payments by status, due date, paid date, provider, type, program, or contract.
- Payment provider performance based on collected revenue or paid payment volume.
- Program performance based on collected revenue, net revenue, signed contract value, or payment volume.
- Source performance based on collected revenue, net revenue, signed contract value, or paid payment volume.
- Contract counts by status, such as draft, sent, viewed, withdrawn, signed, or voided.
- Signed contract value and booked sales value.
- Contract signed rate and sent-to-signed contract rate.
- Contract breakdowns by status, type, closer, setter, program, or currency.
- Lists of unsigned contracts, sent but not signed contracts, viewed but not signed contracts, or voided contracts.
- Closer performance based on signed contract value or signed contract count.
- Setter performance based on signed contract value or signed contract count.
- Refund totals, succeeded refund amounts, failed refunds, initiated refunds, and refund rate.
- Invoice counts and invoice amount breakdowns by paid or refunded status.
- Payments with invoices or missing invoices.
- Payments with payment links, missing payment links, active payment links, used payment links, or invalid payment links.
- Payments with uploaded payment proofs or missing payment proofs.
- Subscription counts by active, pending, past due, cancellation scheduled, or cancelled status.
- Current MRR from active subscriptions.
- Subscription revenue, billing cycle, billing interval, next billing date, cancellation, and past-due analysis.
- Subscription checkout link counts by active, used, or invalid status.
- Unmatched payment counts and amounts by pending, attached, or ignored status.
- Unmatched payment reconciliation analysis by provider, currency, amount, customer name, or manual attachment status.

## When Not To Use This Skill

Do not use this skill for:

- Lead-only counts, lead status, lead source breakdowns, stale leads, missing owners, missing setters, or lead creation trends. Use `lead_analytics`.
- Appointment counts, booked calls, no-show rates, appointment outcomes, Fathom coverage, Fathom call summaries, objections, action items, or call duration. Use `appointment_analytics`.
- Form-answer, UTM, landing-page, traffic attribution, or opt-in question analysis. Use `acquisition_analytics`.
- Provider integration health, webhook troubleshooting, credential validation, API keys, webhook payloads, or connection status. Use an integration/admin skill.

If the user question requires tables outside `programs`, `contracts`, `contract_subscriptions`, `subscription_checkout_links`, `payments`, `payment_links`, `payment_proofs`, `refunds`, `invoices`, `unmatched_payments`, `leads`, or `marketing_sources`, do not use this skill unless the required logic is explicitly listed in this file.

## Cross-Skill SQL Composition Rules

This skill is the primary skill when the main metric is revenue, payment amount, refund amount, contract value, signed value, MRR, outstanding amount, overdue amount, payment count, refund count, invoice amount, or subscription amount.

When `revenue_analytics` is primary:
- This skill controls the metric definition, base table, date field, aggregation grain, payment logic, refund logic, contract logic, subscription logic, and money calculation.
- Supporting skills may be loaded only to clarify dimensions, source/status meaning, or safe join context.
- Do not let a supporting skill override revenue, payment, refund, contract, invoice, or subscription calculations.

Allowed supporting skill usage:
- Use `lead_analytics` as supporting when the revenue question is broken down by lead source, first source, last source, marketing source, lead status context, lead owner, or lead setter.
- Use `acquisition_analytics` as supporting only to understand acquisition terms such as UTM campaign, UTM source, UTM medium, landing page, referrer, provider form, form, or opt-in source.
- Do not generate revenue by UTM campaign, landing page, referrer, form, or opt-in source unless an approved revenue attribution join is explicitly defined in this skill.
- Use `appointment_analytics` as supporting only when the user asks to compare revenue with appointment or call metrics.
- Do not join appointment tables into revenue SQL unless an explicit revenue-to-appointment rule is listed.

Conflict rule:
- If this skill conflicts with a supporting skill, follow `revenue_analytics` for metric logic.
- Supporting skills are used only for dimension meaning, status/source interpretation, fallback expressions, and safe join context.

Examples:
- "Revenue by source" -> primary `revenue_analytics`, supporting `lead_analytics`.
- "Net collected revenue by first source" -> primary `revenue_analytics`, supporting `lead_analytics`.
- "Signed contract value by source" -> primary `revenue_analytics`, supporting `lead_analytics`.
- "Revenue by UTM campaign" -> unsupported unless an approved revenue-to-UTM attribution rule is added.
- "Revenue by landing page" -> unsupported unless an approved revenue-to-landing-page attribution rule is added.

## SQL Generation Rules

Generate exactly one read-only PostgreSQL SQL statement.

Allowed statements:

- `SELECT`
- `WITH ... SELECT`

Never generate:

- `INSERT`
- `UPDATE`
- `DELETE`
- `UPSERT`
- `MERGE`
- `DROP`
- `ALTER`
- `CREATE`
- `TRUNCATE`
- `GRANT`
- `REVOKE`
- `COPY`
- `CALL`
- `DO`
- `VACUUM`
- `ANALYZE`
- `EXPLAIN ANALYZE`

Do not generate multiple SQL statements.

Do not use `SELECT *`.

Do not expose secrets, webhook payloads, API keys, encrypted credentials, raw payloads, provider credentials, or private integration data.

Never select:

```text
payment_links.url
subscription_checkout_links.url
payment_links.provider_link_id
subscription_checkout_links.provider_link_id
payments.external_payment_id
contract_subscriptions.external_subscription_id
unmatched_payments.external_payment_id
unmatched_payments.webhook_event_id
payment_proofs.file_key
```

Only select these fields if the user explicitly asks for provider/debug identifiers or payment/subscription links, and even then return only the minimum required fields.

Every business query must include an organization filter.

For payment-first queries, use:

```sql
WHERE p.clerk_org_id = :org_id
```

For contract-first queries, use:

```sql
WHERE c.clerk_org_id = :org_id
```

For program-first queries, use:

```sql
WHERE pr.clerk_org_id = :org_id
```

For refund-first queries, use:

```sql
WHERE r.clerk_org_id = :org_id
```

For invoice-first queries, use:

```sql
WHERE i.clerk_org_id = :org_id
```

For unmatched-payment queries, use:

```sql
WHERE up.clerk_org_id = :org_id
```

For `programs`, `contracts`, `contract_subscriptions`, `subscription_checkout_links`, `payments`, `payment_links`, and `payment_proofs`, always exclude soft-deleted rows unless the user explicitly asks about deleted records:

```sql
AND <alias>.is_deleted = false
```

`refunds`, `invoices`, and `unmatched_payments` do not have `is_deleted` in the current schema, so do not add a soft-delete filter to those tables.

For `leads`, exclude soft-deleted rows by default when joining to lead identity:

```sql
AND l.is_deleted = false
```

Always use parameterized SQL for organization scope and dynamic values.

Use named parameters such as:

- `:org_id`
- `:start_date`
- `:end_date`
- `:payment_status`
- `:contract_status`
- `:payment_provider`
- `:payment_type`
- `:contract_type`
- `:program_id`
- `:closer_id`
- `:setter_id`
- `:currency`
- `:limit`

Do not hardcode the organization ID in generated agent SQL except in local manual debugging.

For aggregate analytics questions, return aggregate columns only.

For list-style questions such as "which payments", "show contracts", or "list subscriptions", select only the fields needed to answer the question, add a deterministic `ORDER BY`, and cap the result with a reasonable `LIMIT` unless the user asks for a specific limit.

Default list limit: `50`.

Do not include lead email or phone fields unless the user explicitly asks for contact details.

`closer_id`, `setter_id`, `created_by`, `uploaded_by`, and similar user fields are user IDs. Do not invent user names unless a future user/profile table is available in another skill.

When joining one-to-many tables such as refunds, payment links, payment proofs, or invoices, use `COUNT(DISTINCT ...)` or pre-aggregate the child table to avoid double-counting payments or contracts.

## Count vs List Intent Rule

If the user asks "how many", "count", "total", "number of", "amount", "sum", "revenue", or "value", generate an aggregate query.

If the user asks "which", "show me", "list", "who had", "give me the payments", "give me the contracts", or "give me the subscriptions", generate a list query.

Do not answer list-style revenue questions using only `COUNT(*)`.

## Primary Tables

## `programs`

One row is one product/program that can be sold through contracts.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Program primary key. | Join from `contracts.program_id`. |
| `clerk_org_id` | Tenant/organization ID. | Required filter. |
| `name` | Program name. | Program revenue and contract reporting. |
| `price_minor` | Program price in minor units. | Catalog/list price analysis only. Divide by 100.0 for major units if needed. |
| `payment_type` | Program payment type enum. | One-time vs subscription program reporting. |
| `billing_interval` | Billing interval for subscription programs. | Subscription context. |
| `notes` | Program notes. | Avoid unless explicitly asked. |
| `template_id` | Contract template ID. | Template/admin context only. |
| `template_name` | Contract template name. | Template/admin context only. |
| `send_without_payment` | Whether contracts can be sent without payment. | Setup/admin context. |
| `is_archived` | Archived program flag. | Usually keep for historical reporting. |
| `created_by` | Creator user ID. | Admin context only. |
| `created_at` | Program creation datetime. | Program setup trends only. |
| `updated_at` | Last update datetime. | Setup/admin context only. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Required default filter for program-first queries:

```sql
WHERE pr.clerk_org_id = :org_id
  AND pr.is_deleted = false
```

## `contracts`

One row is one contract linked to a lead and a program.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Contract primary key. | Join key and contract identity. |
| `clerk_org_id` | Tenant/organization ID. | Required filter. |
| `lead_id` | Lead linked to the contract. | Join to `leads.id`. |
| `program_id` | Program sold in the contract. | Join to `programs.id`. |
| `closer_id` | Closer user ID. | Closer contract value/performance. |
| `setter_id` | Setter user ID. | Setter contract value/performance. |
| `type` | Contract payment type enum. | PIF, payment plan, or subscription. |
| `total_value` | Contract value stored in minor units. | Signed contract value, pipeline contract value. Divide by 100.0 for business-facing amounts. |
| `currency` | Contract currency. | Currency-specific reporting. |
| `status` | Contract status enum. | Contract funnel and signed/voided/sent analysis. |
| `created_with_template` | Whether created from template. | Setup/admin context. |
| `notes` | Contract notes. | Avoid unless explicitly asked. |
| `esign_template_id` | eSignature template ID. | Provider/debug context only. |
| `esign_contract_id` | eSignature contract ID. | Provider/debug context only. |
| `voided_reason` | Reason contract was voided. | Voided contract analysis. |
| `voided_by` | User ID who voided contract. | Admin context only. |
| `voided_at` | When contract was voided. | Voided contract timing. |
| `sent_at` | When contract was sent. | Sent contract timing. |
| `signed_at` | When contract was signed. | Signed contract timing and signed value. |
| `created_by` | Creator user ID. | Admin context only. |
| `created_at` | Contract creation datetime. | Created contract trend. |
| `updated_at` | Last update datetime. | Recency/debug context only. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Required default filter:

```sql
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
```

## `payments`

One row is one expected or collected payment linked to a contract and lead.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Payment primary key. | Join key and payment identity. |
| `contract_id` | Contract linked to payment. | Join to `contracts.id`. |
| `subscription_id` | Subscription linked to payment, when applicable. | Subscription payment analysis. |
| `lead_id` | Lead linked to payment. | Join to `leads.id`. |
| `clerk_org_id` | Tenant/organization ID. | Required filter. |
| `type` | Payment type enum. | First payment, deposit, instalment, or subscription cycle. |
| `payment_provider` | Payment provider enum. | Stripe, Whop, Manual, Mollie reporting. |
| `status` | Payment status enum. | Paid, pending, failed, lost, refunded, draft analysis. |
| `amount` | Payment amount stored in minor units. | Revenue and outstanding amount. Divide by 100.0 for business-facing amounts. |
| `due_date` | Payment due date. | Due, overdue, due-soon analysis. |
| `paid_at` | Payment paid datetime. | Collected revenue timing. |
| `currency` | Payment currency. | Currency-specific reporting. |
| `note` | Payment note. | Avoid unless explicitly asked. |
| `failure_reason` | Failure reason. | Failed payment analysis. |
| `external_payment_id` | Provider payment ID. | Provider/debug context only. |
| `billing_cycle_number` | Subscription cycle number. | Subscription cycle analysis. |
| `created_by` | Creator user ID. | Admin context only. |
| `created_at` | Payment record creation datetime. | Payment setup trend only. |
| `updated_at` | Last update datetime. | Recency/debug context only. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Required default filter:

```sql
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
```

## `contract_subscriptions`

One row is one subscription created from a subscription contract.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Subscription primary key. | Join key. |
| `contract_id` | Contract linked to subscription. | Join to `contracts.id`. |
| `billing_interval` | Billing interval enum. | MRR normalization. |
| `amount_per_cycle` | Subscription amount per billing cycle stored in minor units. | MRR and subscription value. Divide by 100.0 for business-facing amounts. |
| `currency` | Subscription currency. | Currency-specific subscription reporting. |
| `status` | Subscription status enum. | Active, past due, cancelled analysis. |
| `payment_provider` | Payment provider enum. | Subscription provider reporting. |
| `external_subscription_id` | Provider subscription ID. | Provider/debug context only. |
| `billing_cycles_paid` | Number of paid billing cycles. | Subscription collection context. |
| `total_collected` | Total collected through subscription, stored in minor units. | Subscription collection reporting. Divide by 100.0 for business-facing amounts. |
| `current_period_start` | Current period start. | Subscription period reporting. |
| `current_period_end` | Current period end. | Renewal/period reporting. |
| `next_billing_date` | Next billing date. | Upcoming billing analysis. |
| `started_at` | Subscription start datetime. | Subscription start trend. |
| `cancel_at_period_end` | Whether cancellation is scheduled. | Cancellation risk analysis. |
| `cancelled_at` | Cancellation datetime. | Cancelled subscription trend. |
| `cancellation_reason` | Cancellation reason. | Cancellation reason list/context. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Join from contracts:

```sql
LEFT JOIN contract_subscriptions cs
  ON cs.contract_id = c.id
 AND c.clerk_org_id = :org_id
 AND cs.is_deleted = false
```

The subscription table does not have `clerk_org_id`, so always scope subscription queries through `contracts`.

## `payment_links`

One row is one payment checkout link for a payment.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Payment link primary key. | Link identity. |
| `payment_id` | Payment linked to this checkout link. | Join to `payments.id`. |
| `provider_link_id` | Provider link ID. | Provider/debug context only. |
| `provider_plan_id` | Provider plan ID. | Provider/debug context only. |
| `url` | Checkout URL. | Display only when explicitly asked. |
| `status` | Payment link status enum. | Active, used, invalid analysis. |
| `provider_invalidation_status` | Provider invalidation status. | Payment link invalidation analysis. |
| `note` | Link note. | Avoid unless explicitly asked. |
| `created_by` | Creator user ID. | Admin context only. |
| `created_at` | Link creation datetime. | Link creation trend. |
| `updated_at` | Last update datetime. | Recency/debug context only. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Join from payments:

```sql
LEFT JOIN payment_links pl
  ON pl.payment_id = p.id
 AND pl.is_deleted = false
```

Payment links do not have `clerk_org_id`, so always scope payment link queries through `payments`.

## `subscription_checkout_links`

One row is one checkout link for a subscription.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Subscription checkout link primary key. | Link identity. |
| `subscription_id` | Subscription linked to this checkout link. | Join to `contract_subscriptions.id`. |
| `provider_link_id` | Provider link ID. | Provider/debug context only. |
| `provider_plan_id` | Provider plan ID. | Provider/debug context only. |
| `url` | Checkout URL. | Display only when explicitly asked. |
| `status` | Link status enum. | Active, used, invalid analysis. |
| `provider_invalidation_status` | Provider invalidation status. | Link invalidation analysis. |
| `note` | Link note. | Avoid unless explicitly asked. |
| `created_by` | Creator user ID. | Admin context only. |
| `created_at` | Link creation datetime. | Link creation trend. |
| `updated_at` | Last update datetime. | Recency/debug context only. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Subscription checkout links do not have `clerk_org_id`, so always scope these queries through `contract_subscriptions -> contracts`.

## `payment_proofs`

One row is one uploaded proof file for a payment.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Payment proof primary key. | Proof identity. |
| `payment_id` | Payment linked to proof. | Join to `payments.id`. |
| `clerk_org_id` | Tenant/organization ID. | Required filter for proof-first queries. |
| `file_key` | Storage key. | Do not select. |
| `file_name` | File name. | Display only when explicitly asked. |
| `mime_type` | File type. | Proof type analysis. |
| `file_size_bytes` | File size. | Storage analysis only. |
| `uploaded_by` | Uploader user ID. | Admin context only. |
| `created_at` | Upload datetime. | Proof upload timing. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

## `refunds`

One row is one refund attempt or refund record linked to a payment.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Refund primary key. | Refund identity. |
| `payment_id` | Payment linked to refund. | Join to `payments.id`. |
| `clerk_org_id` | Tenant/organization ID. | Required filter. |
| `amount` | Refund amount stored in minor units. | Refund totals and net revenue calculation. Divide by 100.0 for business-facing amounts. |
| `currency` | Refund currency. | Currency-specific reporting. |
| `status` | Refund status enum. | Initiated, succeeded, failed analysis. |
| `reason` | Refund reason. | Refund reason context/list. |
| `external_refund_id` | Provider refund ID. | Provider/debug context only. |
| `payment_provider` | Refund provider. | Provider refund reporting. |
| `refunded_at` | Refund completion datetime. | Refund timing. |
| `failure_reason` | Failed refund reason. | Failed refund analysis. |
| `created_by` | Creator user ID. | Admin context only. |
| `created_at` | Refund record creation datetime. | Refund creation trend. |

Refunds do not have `is_deleted`, so do not add a soft-delete filter to this table.

## `invoices`

One row is one invoice linked to a contract, payment, and lead.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Invoice primary key. | Invoice identity. |
| `contract_id` | Contract linked to invoice. | Join to `contracts.id`. |
| `payment_id` | Payment linked to invoice. | Join to `payments.id`. |
| `invoice_number` | Invoice number. | Display only when useful. |
| `clerk_org_id` | Tenant/organization ID. | Required filter. |
| `from_org_id` | Sender organization ID. | Usually not needed. |
| `to_client_id` | Lead/client ID. | Join to `leads.id`. |
| `amount` | Invoice amount stored in minor units. | Invoice totals. Divide by 100.0 for business-facing amounts. |
| `currency` | Invoice currency. | Currency-specific reporting. |
| `status` | Invoice status enum. | Paid/refunded invoice reporting. |
| `issued_at` | Invoice issue datetime. | Invoice timing. |
| `paid_at` | Invoice paid datetime. | Paid invoice timing. |
| `created_at` | Invoice creation datetime. | Invoice creation trend. |

Invoices do not have `is_deleted`, so do not add a soft-delete filter to this table.

## `unmatched_payments`

One row is one provider payment event that could not yet be attached to a known payment.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Unmatched payment primary key. | Identity. |
| `clerk_org_id` | Tenant/organization ID. | Required filter. |
| `provider` | Payment provider enum. | Provider analysis. |
| `external_payment_id` | Provider payment ID. | Provider/debug context only. |
| `amount` | Payment amount stored in minor units. | Unmatched amount analysis. Divide by 100.0 for business-facing amounts. |
| `currency` | Currency. | Currency-specific reporting. |
| `status` | Unmatched status enum. | Pending, attached, ignored analysis. |
| `customer_email` | Provider customer email. | Contact detail only when explicitly requested. |
| `customer_name` | Provider customer name. | Display context. |
| `description` | Provider description. | Light context only. |
| `webhook_event_id` | Webhook event ID. | Do not select. |
| `attached_payment_id` | Payment this was attached to. | Attachment analysis. |
| `is_manually_attached` | Whether manually attached. | Reconciliation analysis. |
| `created_at` | Created datetime. | Unmatched payment timing. |
| `updated_at` | Updated datetime. | Recency/debug context. |

Do not use this table for webhook payload analysis. Use an integration/admin skill for provider or webhook troubleshooting.

## `leads`

Use this table only when revenue answers need lead/client display context or lead-source attribution.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Lead primary key. | Join from contracts, payments, invoices. |
| `clerk_org_id` | Tenant/organization ID. | Required join safety. |
| `first_name` | First name. | Display and search. |
| `last_name` | Last name. | Display and search. |
| `full_name` | Generated/display full name. | Display and search. |
| `email` | Lead email. | Only when explicitly requested. |
| `phone_e164` | Phone number. | Only when explicitly requested. |
| `source` | High-level lead source enum. | Use only when the user asks for high-level source category, such as Calendly or Manual. |
| `first_source_id` | First normalized marketing source ID. | Default source attribution for revenue by source. Join to `marketing_sources.id`. |
| `first_source_name` | First source snapshot/name. | Fallback display value when `first_source_id` is missing or unmatched. |
| `last_source_id` | Last normalized marketing source ID. | Use only for latest-source or last-touch revenue attribution. Join to `marketing_sources.id`. |
| `last_source_name` | Last source snapshot/name. | Fallback display value when `last_source_id` is missing or unmatched. |
| `is_deleted` | Soft-delete flag. | Usually filter false. |

Join from payments:

```sql
LEFT JOIN leads l
  ON l.id = p.lead_id
 AND l.clerk_org_id = p.clerk_org_id
 AND l.is_deleted = false
```

Join from contracts:

```sql
LEFT JOIN leads l
  ON l.id = c.lead_id
 AND l.clerk_org_id = c.clerk_org_id
 AND l.is_deleted = false
```

Do not use this skill for lead-only analytics. Use `lead_analytics` for lead-only questions.

## `marketing_sources`

One row is one normalized marketing source used by leads for first-touch and last-touch attribution.

Important columns:

| Column | Meaning | Use |
|---|---|---|
| `id` | Marketing source primary key. | Join from `leads.first_source_id` or `leads.last_source_id`. |
| `clerk_org_id` | Tenant/organization ID. | Required join safety. |
| `name` | Normalized source name. | Source-attributed revenue reporting. |
| `aliases` | Alternate source aliases. | Source normalization context only. |
| `description` | Source description. | Optional explanation when explicitly useful. |
| `is_archived` | Archived source flag. | Usually keep for historical attribution. |

Correct first-touch source join:

```sql
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
```

Correct last-touch source join:

```sql
LEFT JOIN marketing_sources last_ms
  ON last_ms.id = l.last_source_id
 AND last_ms.clerk_org_id = l.clerk_org_id
```

Do not join marketing sources by name. Use `l.first_source_name` or `l.last_source_name` only as fallback display values when the corresponding source ID is missing or unmatched.

## Enums

## `ContractStatus`

Business-defined values:

```text
DRAFT
SENT
VIEWED
WITHDRAWN
SIGNED
VOIDED
```

Meaning:

| Value | Meaning |
|---|---|
| `DRAFT` | Contract has been drafted but not sent. |
| `SENT` | Contract was sent to the client. |
| `VIEWED` | Client viewed the contract. |
| `WITHDRAWN` | Contract was withdrawn. |
| `SIGNED` | Contract was signed. |
| `VOIDED` | Contract was voided. |

## `ContractPaymentType`

Business-defined values:

```text
PIF
PP
SUBSCRIPTION
```

Meaning:

| Value | Meaning |
|---|---|
| `PIF` | Paid in full contract. |
| `PP` | Payment plan contract. |
| `SUBSCRIPTION` | Subscription contract. |

## `PaymentType`

Business-defined values:

```text
FIRST_PAYMENT
DEPOSIT
INSTALMENT
SUBSCRIPTION_CYCLE
```

## `PaymentStatus`

Business-defined values:

```text
DRAFT
PENDING
PAID
FAILED
LOST
REFUNDED
```

Meaning:

| Value | Meaning |
|---|---|
| `DRAFT` | Payment has been drafted but not issued/active. |
| `PENDING` | Payment is expected but not paid yet. |
| `PAID` | Payment was successfully paid. |
| `FAILED` | Payment attempt failed. |
| `LOST` | Payment is no longer expected/collectible. |
| `REFUNDED` | Payment was refunded. |

## `PaymentProvider`

Business-defined values:

```text
STRIPE
WHOP
MANUAL
MOLLIE
```

## `RefundStatus`

Business-defined values:

```text
INITIATED
SUCCEEDED
FAILED
```

Use only `SUCCEEDED` refunds when calculating net collected revenue.

## `InvoiceStatus`

Business-defined values:

```text
PAID
REFUNDED
```

## `ContractSubscriptionStatus`

Business-defined values:

```text
PENDING
ACTIVE
PAST_DUE
CANCELLATION_SCHEDULED
CANCELLED
```

## `PaymentLinkStatus`

Business-defined values:

```text
ACTIVE
USED
INVALID
```

## `UnmatchedPaymentStatus`

Business-defined values:

```text
PENDING
ATTACHED
IGNORED
```

## Business Interpretation Rules

## Monetary Storage and Reporting Rules

Money-like database columns are stored in minor units even when the database type is decimal.

Always divide these fields by `100.0` when returning business-facing money values:

- `payments.amount`
- `refunds.amount`
- `contracts.total_value`
- `contract_subscriptions.amount_per_cycle`
- `contract_subscriptions.total_collected`
- `invoices.amount`
- `unmatched_payments.amount`
- `programs.price_minor`

For aggregate queries, divide the aggregate result:

```sql
SUM(p.amount) / 100.0 AS gross_paid_amount
```

For list-style queries, return the converted amount under the normal business column name:

```sql
p.amount / 100.0 AS amount
```

Only expose raw stored minor-unit values when the user explicitly asks for raw database/debug values, and name those columns with a `_minor` suffix.

## Default Revenue Meaning

When the user says "revenue", "collected revenue", "how much money collected", or "payment revenue" without further detail, use paid payments as the base and subtract succeeded refunds.

Default net collected revenue:

- include non-deleted payments where `p.status = 'PAID'`
- use `p.paid_at` for revenue timing
- subtract refunds where `r.status = 'SUCCEEDED'`
- report as a single EUR total unless the user explicitly asks for a currency breakdown

## EUR Currency Reporting Rule

For this implementation, assume all monetary reporting is in EUR.

Default behavior:

- Do not group revenue, payment, refund, contract value, subscription, MRR, or outstanding amount queries by currency unless the user explicitly asks for a currency breakdown.
- Do not show `currency` as a normal grouped dimension in default aggregate outputs.
- In final answers, format monetary values as EUR or €.
- Keep currency fields available in list-style queries only when useful for transparency, but aggregate analytics should not split rows by currency by default.

Important:

- Do not remove currency columns from the schema or database logic.
- Do not change stored currency values.
- Do not hardcode fake conversions or FX logic.
- Do not merge currencies if the user explicitly asks for multi-currency analysis in the future.
- If the user explicitly asks "by currency", "currency breakdown", or "show currencies", then group by currency.
- If the query is for debugging or reconciliation and currency is relevant, include currency.
- Otherwise, default to a single EUR total.

There is no FX table in this skill. Do not invent currency conversion.

If the user asks for gross collected revenue, use only paid payments and do not subtract refunds.

If the user asks for signed revenue, booked revenue, sales value, or contract value, use signed contracts and `contracts.total_value`.

## Payment Timing Rules

For collected revenue, paid payments, or revenue collected during a period, use:

```sql
p.paid_at >= :start_date
AND p.paid_at < :end_date
```

For payments due during a period, use:

```sql
p.due_date >= :start_date
AND p.due_date < :end_date
```

For payments created during a period, use:

```sql
p.created_at >= :start_date
AND p.created_at < :end_date
```

Use `p.created_at` only when the user asks when payment records were created or added.

## Contract Timing Rules

For signed contracts or signed contract value, use:

```sql
c.signed_at >= :start_date
AND c.signed_at < :end_date
```

For sent contracts, use:

```sql
c.sent_at >= :start_date
AND c.sent_at < :end_date
```

For voided contracts, use:

```sql
c.voided_at >= :start_date
AND c.voided_at < :end_date
```

For contracts created during a period, use:

```sql
c.created_at >= :start_date
AND c.created_at < :end_date
```

If the user simply asks "contracts this month" without saying signed/sent/created, use `c.created_at` and make the SQL column name clear, such as `contracts_created_in_period`.

## Refund Timing Rules

For refund amount during a period, prefer `r.refunded_at` when available for succeeded refunds.

For refund records created during a period, use `r.created_at` only when the user asks when refunds were created or initiated.

Default succeeded refund timing:

```sql
COALESCE(r.refunded_at, r.created_at) >= :start_date
AND COALESCE(r.refunded_at, r.created_at) < :end_date
```

## Outstanding and Overdue Payment Rules

When the user asks for outstanding payments, unpaid payments, open payments, or money still due, include non-deleted payments where:

```sql
p.status IN ('PENDING', 'FAILED')
```

Do not include `DRAFT`, `LOST`, `PAID`, or `REFUNDED` in default outstanding amounts.

When the user asks for overdue payments, use:

```sql
p.status IN ('PENDING', 'FAILED')
AND p.due_date IS NOT NULL
AND p.due_date < NOW()
```

When the user asks for payments due soon, use application-provided date parameters:

```sql
p.status IN ('PENDING', 'FAILED')
AND p.due_date >= :start_date
AND p.due_date < :end_date
```

## Signed Contract Value Rules

When the user asks for signed contract value, sales value, booked revenue, or contract sales, use:

```sql
c.status = 'SIGNED'
AND c.total_value IS NOT NULL
```

Use `c.signed_at` for signed timing when the user provides a period.

Do not treat signed contract value as collected cash. Collected cash must come from paid payments.

## Contract Signed Rate Rules

When the user asks for contract signed rate, calculate the percentage of non-deleted contracts with `status = 'SIGNED'`.

If the user asks for sent-to-signed rate, exclude drafts from the denominator:

```sql
c.status IN ('SENT', 'VIEWED', 'SIGNED', 'WITHDRAWN', 'VOIDED')
```

## Subscription MRR Rules

When the user asks for MRR, use active subscriptions by default:

```sql
cs.status = 'ACTIVE'
```

Normalize `amount_per_cycle` to monthly amount using `billing_interval`:

```sql
CASE
  WHEN cs.billing_interval = 'WEEKLY' THEN (cs.amount_per_cycle / 100.0) * 52.0 / 12.0
  WHEN cs.billing_interval = 'MONTHLY' THEN cs.amount_per_cycle / 100.0
  WHEN cs.billing_interval = 'YEARLY' THEN (cs.amount_per_cycle / 100.0) / 12.0
  ELSE NULL
END
```

Report MRR as a single EUR total unless the user explicitly asks for a currency breakdown.

Do not include deleted subscriptions or deleted contracts.

## Program Revenue Rules

When the user asks which program generated the most revenue, use paid payments joined through contracts to programs, and subtract succeeded refunds if the user asks for net revenue.

For signed program value, use signed contracts joined to programs.

For catalog/program setup price, use `programs.price_minor / 100.0`, not payment or contract revenue.

## Source Attribution Rules

When the user asks for "revenue by source", "which source generated the most revenue", "source revenue", or "source performance" without specifying a source type, use first-touch source by default:

```text
payments -> contracts -> leads.first_source_id -> marketing_sources.id
```

Use this display expression for default first-touch source:

```sql
COALESCE(
  NULLIF(TRIM(first_ms.name), ''),
  NULLIF(TRIM(l.first_source_name), ''),
  'Unknown Source'
) AS first_source
```

If the user asks for latest source, last source, last-touch source, or source before conversion, use:

```text
payments -> contracts -> leads.last_source_id -> marketing_sources.id
```

Use this display expression for last-touch source:

```sql
COALESCE(
  NULLIF(TRIM(last_ms.name), ''),
  NULLIF(TRIM(l.last_source_name), ''),
  'Unknown Source'
) AS last_source
```

If the user asks for high-level source category, enum source, Calendly/Manual/Typeform/Webinar/Newsletter/Landing Page source, use `l.source` and do not join `marketing_sources`.

Join leads for payment revenue attribution like this, falling back from `payments.lead_id` to the linked contract's `lead_id`:

```sql
LEFT JOIN contracts c
  ON c.id = p.contract_id
 AND c.clerk_org_id = p.clerk_org_id
 AND c.is_deleted = false
LEFT JOIN leads l
  ON l.id = COALESCE(p.lead_id, c.lead_id)
 AND l.clerk_org_id = p.clerk_org_id
 AND l.is_deleted = false
```

Join leads for signed contract value attribution like this:

```sql
LEFT JOIN leads l
  ON l.id = c.lead_id
 AND l.clerk_org_id = c.clerk_org_id
 AND l.is_deleted = false
```

For collected revenue by source:

- use paid payments as the base
- use `p.paid_at` for collected revenue timing
- subtract succeeded refunds for net collected revenue
- attribute refunds to the source of the original payment
- report as a single EUR total unless the user explicitly asks for a currency breakdown
- include `Unknown Source` by default so unattributed revenue is visible

For signed contract value by source:

- use signed contracts as the base
- use `c.signed_at` for signed value timing
- use `c.total_value / 100.0`
- do not subtract refunds because signed value is not collected cash

Do not use `opt_ins`, `traffic_attributions`, UTM fields, landing pages, referrers, or form answers in this skill. If the user asks for revenue by UTM campaign, landing page, referrer, ad, or form-answer source, say that revenue attribution for those acquisition dimensions is not supported yet.

## Default List Output Rules

For list-style payment queries, default output fields are:

- `total_matching_rows`
- `p.id`
- `display_name`
- `payment_type`
- `payment_status`
- `payment_provider`
- `amount`
- `currency`
- `due_date`
- `paid_at`
- `program_name`
- `contract_status`
- `created_at`

Use this display name expression:

```sql
COALESCE(
  NULLIF(TRIM(l.full_name), ''),
  NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
  l.first_name,
  'Unknown Lead'
) AS display_name
```

For list-style contract queries, default output fields are:

- `total_matching_rows`
- `c.id`
- `display_name`
- `program_name`
- `contract_type`
- `contract_status`
- `total_value`
- `currency`
- `closer_id`
- `setter_id`
- `sent_at`
- `signed_at`
- `voided_at`
- `created_at`

For list-style subscription queries, default output fields are:

- `total_matching_rows`
- `cs.id`
- `c.id AS contract_id`
- `display_name`
- `program_name`
- `subscription_status`
- `payment_provider`
- `amount_per_cycle`
- `billing_interval`
- `currency`
- `next_billing_date`
- `cancel_at_period_end`
- `cancelled_at`

Do not include lead email, lead phone, checkout URLs, external payment IDs, external subscription IDs, file keys, or webhook event IDs unless the user explicitly asks for those details.

The list-style `amount`, `total_value`, and `amount_per_cycle` fields should be returned as major-unit business values by default, not raw stored minor units.

Use `COUNT(*) OVER() AS total_matching_rows` for list-style queries with a `LIMIT`, so the final answer can show the exact total before the limited rows.

Use `LIMIT :limit` when the application passes a limit.

If the application does not pass a limit and the user does not request one, use:

```sql
LIMIT 50
```

Always use deterministic ordering, such as:

```sql
ORDER BY p.paid_at DESC NULLS LAST, p.created_at DESC, p.id ASC
```

or, for overdue payment lists:

```sql
ORDER BY p.due_date ASC NULLS LAST, p.created_at ASC, p.id ASC
```

## Common Query Patterns

## Net Collected Revenue

Use this for default revenue questions.

```sql
WITH paid_payments AS (
  SELECT
    SUM(p.amount) / 100.0 AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
), succeeded_refunds AS (
  SELECT
    SUM(r.amount) / 100.0 AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
)
SELECT
  COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue
FROM paid_payments pp
CROSS JOIN succeeded_refunds sr;
```

## Net Collected Revenue in a Date Range

```sql
WITH paid_payments AS (
  SELECT
    SUM(p.amount) / 100.0 AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
), succeeded_refunds AS (
  SELECT
    SUM(r.amount) / 100.0 AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
)
SELECT
  COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue
FROM paid_payments pp
CROSS JOIN succeeded_refunds sr;
```

## Gross Paid Revenue

```sql
SELECT
  SUM(p.amount) / 100.0 AS gross_paid_amount,
  COUNT(*) AS paid_payment_count
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID';
```

## Paid Revenue by Payment Provider

```sql
SELECT
  CAST(p.payment_provider AS text) AS payment_provider,
  COUNT(*) AS paid_payment_count,
  SUM(p.amount) / 100.0 AS gross_paid_amount,
  SUM(COUNT(*)) OVER() AS total_paid_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_paid_payments
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
GROUP BY CAST(p.payment_provider AS text)
ORDER BY gross_paid_amount DESC, payment_provider ASC;
```

## Payment Breakdown by Status

```sql
SELECT
  CAST(p.status AS text) AS payment_status,
  COUNT(*) AS payment_count,
  SUM(p.amount) / 100.0 AS total_amount,
  SUM(COUNT(*)) OVER() AS total_matching_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
GROUP BY CAST(p.status AS text)
ORDER BY payment_count DESC, payment_status ASC;
```

## Payment Breakdown by Type

```sql
SELECT
  CAST(p.type AS text) AS payment_type,
  COUNT(*) AS payment_count,
  SUM(p.amount) / 100.0 AS total_amount,
  SUM(COUNT(*)) OVER() AS total_matching_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
GROUP BY CAST(p.type AS text)
ORDER BY payment_count DESC, payment_type ASC;
```

## Outstanding Payment Amount

```sql
SELECT
  COUNT(*) AS outstanding_payment_count,
  SUM(p.amount) / 100.0 AS outstanding_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status IN ('PENDING', 'FAILED');
```

## Overdue Payment Amount

```sql
SELECT
  COUNT(*) AS overdue_payment_count,
  SUM(p.amount) / 100.0 AS overdue_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status IN ('PENDING', 'FAILED')
  AND p.due_date IS NOT NULL
  AND p.due_date < NOW();
```

## List Overdue Payments

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  p.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  CAST(p.type AS text) AS payment_type,
  CAST(p.status AS text) AS payment_status,
  CAST(p.payment_provider AS text) AS payment_provider,
  p.amount / 100.0 AS amount,
  p.currency,
  p.due_date,
  p.paid_at,
  pr.name AS program_name,
  CAST(c.status AS text) AS contract_status,
  p.created_at
FROM payments p
LEFT JOIN leads l
  ON l.id = p.lead_id
 AND l.clerk_org_id = p.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN contracts c
  ON c.id = p.contract_id
 AND c.clerk_org_id = p.clerk_org_id
 AND c.is_deleted = false
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status IN ('PENDING', 'FAILED')
  AND p.due_date IS NOT NULL
  AND p.due_date < NOW()
ORDER BY p.due_date ASC, p.created_at ASC, p.id ASC
LIMIT 50;
```

## Payments Due in a Date Range

```sql
SELECT
  COUNT(*) AS due_payment_count,
  SUM(p.amount) / 100.0 AS due_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status IN ('PENDING', 'FAILED')
  AND p.due_date >= :start_date
  AND p.due_date < :end_date;
```

## Contract Breakdown by Status

```sql
SELECT
  CAST(c.status AS text) AS contract_status,
  COUNT(*) AS contract_count,
  SUM(COALESCE(c.total_value, 0)) / 100.0 AS total_contract_value,
  SUM(COUNT(*)) OVER() AS total_matching_contracts,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
GROUP BY CAST(c.status AS text)
ORDER BY contract_count DESC, contract_status ASC;
```

## Signed Contract Value

```sql
SELECT
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) / 100.0 AS signed_contract_value
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL;
```

## Signed Contract Value in a Date Range

```sql
SELECT
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) / 100.0 AS signed_contract_value
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
  AND c.signed_at >= :start_date
  AND c.signed_at < :end_date;
```

## Contract Signed Rate

```sql
SELECT
  COUNT(*) AS total_contracts,
  COUNT(*) FILTER (WHERE c.status = 'SIGNED') AS signed_contracts,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE c.status = 'SIGNED') / NULLIF(COUNT(*), 0),
    2
  ) AS signed_rate_percent
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false;
```

## Sent-to-Signed Contract Rate

```sql
SELECT
  COUNT(*) AS sent_or_later_contracts,
  COUNT(*) FILTER (WHERE c.status = 'SIGNED') AS signed_contracts,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE c.status = 'SIGNED') / NULLIF(COUNT(*), 0),
    2
  ) AS sent_to_signed_rate_percent
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status IN ('SENT', 'VIEWED', 'SIGNED', 'WITHDRAWN', 'VOIDED');
```

## Signed Contract Value by Program

```sql
SELECT
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) / 100.0 AS signed_contract_value,
  SUM(COUNT(*)) OVER() AS total_signed_contracts,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_signed_contracts
FROM contracts c
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
GROUP BY COALESCE(pr.name, 'Unknown Program')
ORDER BY signed_contract_value DESC, program_name ASC;
```

## Net Collected Revenue by Program

```sql
WITH payment_revenue AS (
  SELECT
    p.id AS payment_id,
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    p.amount / 100.0 AS paid_amount
  FROM payments p
  LEFT JOIN contracts c
    ON c.id = p.contract_id
   AND c.clerk_org_id = p.clerk_org_id
   AND c.is_deleted = false
  LEFT JOIN programs pr
    ON pr.id = c.program_id
   AND pr.clerk_org_id = c.clerk_org_id
   AND pr.is_deleted = false
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
), refund_totals AS (
  SELECT
    r.payment_id,
    SUM(r.amount) / 100.0 AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.payment_id
)
SELECT
  pr.program_name,
  COUNT(DISTINCT pr.payment_id) AS paid_payment_count,
  SUM(pr.paid_amount) AS gross_paid_amount,
  SUM(COALESCE(rt.refunded_amount, 0)) AS refunded_amount,
  SUM(pr.paid_amount) - SUM(COALESCE(rt.refunded_amount, 0)) AS net_collected_revenue
FROM payment_revenue pr
LEFT JOIN refund_totals rt
  ON rt.payment_id = pr.payment_id
GROUP BY pr.program_name
ORDER BY net_collected_revenue DESC, pr.program_name ASC;
```

## Net Collected Revenue by First-Touch Source

Use this for:

- revenue by source
- net revenue by source
- collected revenue by source
- which source generated the most revenue
- source revenue performance

Default source means first-touch normalized marketing source.

```sql
WITH payment_revenue AS (
  SELECT
    p.id AS payment_id,
    COALESCE(
      NULLIF(TRIM(first_ms.name), ''),
      NULLIF(TRIM(l.first_source_name), ''),
      'Unknown Source'
    ) AS first_source,
    p.amount / 100.0 AS paid_amount
  FROM payments p
  LEFT JOIN contracts c
    ON c.id = p.contract_id
   AND c.clerk_org_id = p.clerk_org_id
   AND c.is_deleted = false
  LEFT JOIN leads l
    ON l.id = COALESCE(p.lead_id, c.lead_id)
   AND l.clerk_org_id = p.clerk_org_id
   AND l.is_deleted = false
  LEFT JOIN marketing_sources first_ms
    ON first_ms.id = l.first_source_id
   AND first_ms.clerk_org_id = l.clerk_org_id
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
), refund_totals AS (
  SELECT
    r.payment_id,
    SUM(r.amount) / 100.0 AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.payment_id
), source_revenue AS (
  SELECT
    pr.first_source,
    COUNT(DISTINCT pr.payment_id) AS paid_payment_count,
    SUM(pr.paid_amount) AS gross_paid_amount,
    SUM(COALESCE(rt.refunded_amount, 0)) AS refunded_amount,
    SUM(pr.paid_amount) - SUM(COALESCE(rt.refunded_amount, 0)) AS net_collected_revenue
  FROM payment_revenue pr
  LEFT JOIN refund_totals rt
    ON rt.payment_id = pr.payment_id
  GROUP BY pr.first_source
)
SELECT
  first_source,
  paid_payment_count,
  gross_paid_amount,
  refunded_amount,
  net_collected_revenue,
  COUNT(*) OVER() AS total_matching_sources,
  SUM(paid_payment_count) OVER() AS total_paid_payments,
  SUM(net_collected_revenue) OVER() AS total_net_collected_revenue,
  CASE
    WHEN SUM(net_collected_revenue) OVER() = 0 THEN NULL
    ELSE ROUND(
      net_collected_revenue * 100.0
      / SUM(net_collected_revenue) OVER(),
      2
    )
  END AS percentage_of_total_net_revenue
FROM source_revenue
ORDER BY net_collected_revenue DESC, first_source ASC;
```

For a date-range version, use the same joins and source expression, but split the logic into `paid_by_source` and `refunds_by_source` CTEs:

- filter paid revenue with `p.paid_at >= :start_date AND p.paid_at < :end_date`
- filter succeeded refunds with `COALESCE(r.refunded_at, r.created_at) >= :start_date AND COALESCE(r.refunded_at, r.created_at) < :end_date`
- `FULL OUTER JOIN` the two CTEs by `source` so refunds completed during the period are included even if the original payment was collected outside the period

For latest-source revenue, use the same pattern but join `last_ms` through `l.last_source_id` and display `last_source`.

For high-level source category revenue, use `COALESCE(CAST(l.source AS text), 'Unknown Source')` and do not join `marketing_sources`.

## Signed Contract Value by First-Touch Source

Use this for source-attributed booked revenue, sales value, signed contract value, or contract value.

```sql
SELECT
  COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown Source'
  ) AS first_source,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) / 100.0 AS signed_contract_value,
  SUM(COUNT(*)) OVER() AS total_signed_contracts,
  SUM(SUM(c.total_value)) OVER() / 100.0 AS total_signed_contract_value,
  ROUND(
    SUM(c.total_value) * 100.0
    / NULLIF(SUM(SUM(c.total_value)) OVER(), 0),
    2
  ) AS percentage_of_total_signed_value
FROM contracts c
LEFT JOIN leads l
  ON l.id = c.lead_id
 AND l.clerk_org_id = c.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN marketing_sources first_ms
  ON first_ms.id = l.first_source_id
 AND first_ms.clerk_org_id = l.clerk_org_id
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
GROUP BY
  COALESCE(
    NULLIF(TRIM(first_ms.name), ''),
    NULLIF(TRIM(l.first_source_name), ''),
    'Unknown Source'
  )
ORDER BY signed_contract_value DESC, first_source ASC;
```

## Signed Contract Value by Closer

```sql
SELECT
  COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer') AS closer_id,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) / 100.0 AS signed_contract_value,
  SUM(COUNT(*)) OVER() AS total_signed_contracts,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_signed_contracts
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
GROUP BY COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer')
ORDER BY signed_contract_value DESC, closer_id ASC;
```

## Top Actual Closer by Signed Contract Value

Use this when the user asks:

- which closer sold the most
- top closer by signed contract value
- best closer by contract value

Exclude missing closer values. Do not return `No Closer` as the top closer unless the user explicitly asks to include contracts without a closer.

This query returns all closers tied for the highest signed contract value.

```sql
WITH closer_values AS (
  SELECT
    NULLIF(TRIM(c.closer_id), '') AS closer_id,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) / 100.0 AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND NULLIF(TRIM(c.closer_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(c.closer_id), '')
), ranked AS (
  SELECT
    closer_id,
    signed_contract_count,
    signed_contract_value,
    RANK() OVER (ORDER BY signed_contract_value DESC) AS value_rank
  FROM closer_values
)
SELECT
  closer_id,
  signed_contract_count,
  signed_contract_value
FROM ranked
WHERE value_rank = 1
ORDER BY closer_id ASC;
```

## List Signed Contracts

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  c.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  CAST(c.type AS text) AS contract_type,
  CAST(c.status AS text) AS contract_status,
  c.total_value / 100.0 AS total_value,
  c.currency,
  COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer') AS closer_id,
  COALESCE(NULLIF(TRIM(c.setter_id), ''), 'No Setter') AS setter_id,
  c.sent_at,
  c.signed_at,
  c.voided_at,
  c.created_at
FROM contracts c
LEFT JOIN leads l
  ON l.id = c.lead_id
 AND l.clerk_org_id = c.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
ORDER BY c.signed_at DESC NULLS LAST, c.created_at DESC, c.id ASC
LIMIT 50;
```

## List Sent or Viewed Contracts Not Signed

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  c.id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  CAST(c.type AS text) AS contract_type,
  CAST(c.status AS text) AS contract_status,
  c.total_value / 100.0 AS total_value,
  c.currency,
  COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer') AS closer_id,
  COALESCE(NULLIF(TRIM(c.setter_id), ''), 'No Setter') AS setter_id,
  c.sent_at,
  c.signed_at,
  c.voided_at,
  c.created_at
FROM contracts c
LEFT JOIN leads l
  ON l.id = c.lead_id
 AND l.clerk_org_id = c.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status IN ('SENT', 'VIEWED')
ORDER BY c.sent_at ASC NULLS LAST, c.created_at ASC, c.id ASC
LIMIT 50;
```

## Refund Amount by Status

```sql
SELECT
  CAST(r.status AS text) AS refund_status,
  COUNT(*) AS refund_count,
  SUM(r.amount) / 100.0 AS refund_amount,
  SUM(COUNT(*)) OVER() AS total_matching_refunds,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM refunds r
WHERE r.clerk_org_id = :org_id
GROUP BY CAST(r.status AS text)
ORDER BY refund_count DESC, refund_status ASC;
```

## Succeeded Refund Amount

```sql
SELECT
  COUNT(*) AS succeeded_refund_count,
  SUM(r.amount) / 100.0 AS succeeded_refund_amount
FROM refunds r
WHERE r.clerk_org_id = :org_id
  AND r.status = 'SUCCEEDED';
```

## Refund Rate

Refund rate compares succeeded refund amount against paid payment amount.

```sql
WITH paid_payments AS (
  SELECT
    SUM(p.amount) / 100.0 AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
), succeeded_refunds AS (
  SELECT
    SUM(r.amount) / 100.0 AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
)
SELECT
  pp.gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  ROUND(COALESCE(sr.refunded_amount, 0) * 100.0 / NULLIF(pp.gross_paid_amount, 0), 2) AS refund_rate_percent
FROM paid_payments pp
CROSS JOIN succeeded_refunds sr;
```

## Invoice Breakdown by Status

```sql
SELECT
  CAST(i.status AS text) AS invoice_status,
  COUNT(*) AS invoice_count,
  SUM(i.amount) / 100.0 AS invoice_amount,
  SUM(COUNT(*)) OVER() AS total_matching_invoices,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM invoices i
WHERE i.clerk_org_id = :org_id
GROUP BY CAST(i.status AS text)
ORDER BY invoice_count DESC, invoice_status ASC;
```

## Payment Link Breakdown by Status

```sql
SELECT
  CAST(pl.status AS text) AS payment_link_status,
  COUNT(*) AS payment_link_count,
  SUM(COUNT(*)) OVER() AS total_matching_payment_links,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM payment_links pl
JOIN payments p
  ON p.id = pl.payment_id
 AND p.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND pl.is_deleted = false
GROUP BY CAST(pl.status AS text)
ORDER BY payment_link_count DESC, payment_link_status ASC;
```

## Payments with Payment Links

```sql
SELECT
  COUNT(DISTINCT p.id) AS total_payments,
  COUNT(DISTINCT p.id) FILTER (WHERE pl.id IS NOT NULL) AS payments_with_links,
  COUNT(DISTINCT p.id) FILTER (WHERE pl.id IS NULL) AS payments_without_links,
  ROUND(
    100.0 * COUNT(DISTINCT p.id) FILTER (WHERE pl.id IS NOT NULL) / NULLIF(COUNT(DISTINCT p.id), 0),
    2
  ) AS payment_link_coverage_percent
FROM payments p
LEFT JOIN payment_links pl
  ON pl.payment_id = p.id
 AND pl.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false;
```

## Payments with Payment Proofs

```sql
SELECT
  COUNT(DISTINCT p.id) AS total_payments,
  COUNT(DISTINCT p.id) FILTER (WHERE pp.id IS NOT NULL) AS payments_with_proofs,
  COUNT(DISTINCT p.id) FILTER (WHERE pp.id IS NULL) AS payments_without_proofs,
  ROUND(
    100.0 * COUNT(DISTINCT p.id) FILTER (WHERE pp.id IS NOT NULL) / NULLIF(COUNT(DISTINCT p.id), 0),
    2
  ) AS payment_proof_coverage_percent
FROM payments p
LEFT JOIN payment_proofs pp
  ON pp.payment_id = p.id
 AND pp.clerk_org_id = p.clerk_org_id
 AND pp.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false;
```

## Subscription Breakdown by Status

```sql
SELECT
  CAST(cs.status AS text) AS subscription_status,
  COUNT(*) AS subscription_count,
  SUM(cs.amount_per_cycle) / 100.0 AS total_amount_per_cycle,
  SUM(COUNT(*)) OVER() AS total_matching_subscriptions,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
GROUP BY CAST(cs.status AS text)
ORDER BY subscription_count DESC, subscription_status ASC;
```

## Active Subscription MRR

```sql
SELECT
  COUNT(*) AS active_subscription_count,
  ROUND(SUM(
    CASE
      WHEN cs.billing_interval = 'WEEKLY' THEN (cs.amount_per_cycle / 100.0) * 52.0 / 12.0
      WHEN cs.billing_interval = 'MONTHLY' THEN cs.amount_per_cycle / 100.0
      WHEN cs.billing_interval = 'YEARLY' THEN (cs.amount_per_cycle / 100.0) / 12.0
      ELSE NULL
    END), 2) AS mrr
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
  AND cs.status = 'ACTIVE';
```

## Subscriptions Past Due

```sql
SELECT
  COUNT(*) AS past_due_subscription_count,
  SUM(cs.amount_per_cycle) / 100.0 AS amount_per_cycle_past_due
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
  AND cs.status = 'PAST_DUE';
```

## List Past Due Subscriptions

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  cs.id,
  c.id AS contract_id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  CAST(cs.status AS text) AS subscription_status,
  CAST(cs.payment_provider AS text) AS payment_provider,
  cs.amount_per_cycle / 100.0 AS amount_per_cycle,
  CAST(cs.billing_interval AS text) AS billing_interval,
  cs.currency,
  cs.next_billing_date,
  cs.cancel_at_period_end,
  cs.cancelled_at
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
LEFT JOIN leads l
  ON l.id = c.lead_id
 AND l.clerk_org_id = c.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
  AND cs.status = 'PAST_DUE'
ORDER BY cs.next_billing_date ASC NULLS LAST, cs.updated_at DESC, cs.id ASC
LIMIT 50;
```

## Subscription Checkout Link Breakdown by Status

```sql
SELECT
  CAST(scl.status AS text) AS subscription_link_status,
  COUNT(*) AS subscription_link_count,
  SUM(COUNT(*)) OVER() AS total_matching_subscription_links,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM subscription_checkout_links scl
JOIN contract_subscriptions cs
  ON cs.id = scl.subscription_id
 AND cs.is_deleted = false
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND scl.is_deleted = false
GROUP BY CAST(scl.status AS text)
ORDER BY subscription_link_count DESC, subscription_link_status ASC;
```

## Unmatched Payment Breakdown by Status

```sql
SELECT
  CAST(up.status AS text) AS unmatched_payment_status,
  CAST(up.provider AS text) AS payment_provider,
  COUNT(*) AS unmatched_payment_count,
  SUM(up.amount) / 100.0 AS unmatched_payment_amount,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
GROUP BY CAST(up.status AS text), CAST(up.provider AS text)
ORDER BY unmatched_payment_count DESC, unmatched_payment_status ASC, payment_provider ASC;
```

## Pending Unmatched Payments

```sql
SELECT
  COUNT(*) AS pending_unmatched_payment_count,
  SUM(up.amount) / 100.0 AS pending_unmatched_payment_amount
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING';
```

## List Pending Unmatched Payments

Do not include `external_payment_id`, `webhook_event_id`, or raw provider payloads.

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  up.id,
  CAST(up.provider AS text) AS payment_provider,
  up.amount / 100.0 AS amount,
  up.currency,
  CAST(up.status AS text) AS unmatched_payment_status,
  up.customer_name,
  up.description,
  up.is_manually_attached,
  up.created_at,
  up.updated_at
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING'
ORDER BY up.created_at ASC, up.id ASC
LIMIT 50;
```

## Revenue Trend by Day

Use this for daily collected revenue trend. This returns gross paid amount only. Use the net revenue pattern if the user explicitly asks for net trend.

```sql
SELECT
  DATE_TRUNC('day', p.paid_at)::date AS payment_date,
  COUNT(*) AS paid_payment_count,
  SUM(p.amount) / 100.0 AS gross_paid_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
  AND p.paid_at IS NOT NULL
GROUP BY DATE_TRUNC('day', p.paid_at)::date
ORDER BY payment_date ASC;
```

## Revenue Trend by Day in a Date Range

```sql
SELECT
  DATE_TRUNC('day', p.paid_at)::date AS payment_date,
  COUNT(*) AS paid_payment_count,
  SUM(p.amount) / 100.0 AS gross_paid_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
  AND p.paid_at >= :start_date
  AND p.paid_at < :end_date
GROUP BY DATE_TRUNC('day', p.paid_at)::date
ORDER BY payment_date ASC;
```

## Monthly Revenue Trend with Percentage Change

Use this when the user asks for monthly revenue growth, monthly revenue change, or month-over-month revenue trend.

This pattern uses gross paid amount and returns one EUR series by default.

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', :start_date::timestamp)::date,
    DATE_TRUNC('month', (:end_date::timestamp - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS payment_month
), monthly_grid AS (
  SELECT
    m.payment_month
  FROM months m
), monthly_counts AS (
  SELECT
    DATE_TRUNC('month', p.paid_at)::date AS payment_month,
    COUNT(*) AS paid_payment_count,
    SUM(p.amount) / 100.0 AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY DATE_TRUNC('month', p.paid_at)::date
), monthly_filled AS (
  SELECT
    mg.payment_month,
    COALESCE(mc.paid_payment_count, 0) AS paid_payment_count,
    COALESCE(mc.gross_paid_amount, 0) AS gross_paid_amount
  FROM monthly_grid mg
  LEFT JOIN monthly_counts mc
    ON mc.payment_month = mg.payment_month
), monthly_with_previous AS (
  SELECT
    payment_month,
    paid_payment_count,
    gross_paid_amount,
    LAG(gross_paid_amount) OVER (
      ORDER BY payment_month ASC
    ) AS previous_period_gross_paid_amount
  FROM monthly_filled
)
SELECT
  payment_month,
  paid_payment_count,
  gross_paid_amount,
  previous_period_gross_paid_amount,
  CASE
    WHEN previous_period_gross_paid_amount IS NULL OR previous_period_gross_paid_amount = 0 THEN NULL
    ELSE ROUND(
      ((gross_paid_amount - previous_period_gross_paid_amount)::numeric / previous_period_gross_paid_amount) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(gross_paid_amount) OVER() AS total_gross_paid_amount
FROM monthly_with_previous
ORDER BY payment_month ASC;
```

## Monthly Signed Contract Value Trend with Percentage Change

Use this when the user asks for monthly signed contract value growth, signed sales trend, or booked revenue trend.

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', :start_date::timestamp)::date,
    DATE_TRUNC('month', (:end_date::timestamp - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS signed_month
), monthly_grid AS (
  SELECT
    m.signed_month
  FROM months m
), monthly_counts AS (
  SELECT
    DATE_TRUNC('month', c.signed_at)::date AS signed_month,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) / 100.0 AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND c.signed_at >= :start_date
    AND c.signed_at < :end_date
  GROUP BY DATE_TRUNC('month', c.signed_at)::date
), monthly_filled AS (
  SELECT
    mg.signed_month,
    COALESCE(mc.signed_contract_count, 0) AS signed_contract_count,
    COALESCE(mc.signed_contract_value, 0) AS signed_contract_value
  FROM monthly_grid mg
  LEFT JOIN monthly_counts mc
    ON mc.signed_month = mg.signed_month
), monthly_with_previous AS (
  SELECT
    signed_month,
    signed_contract_count,
    signed_contract_value,
    LAG(signed_contract_value) OVER (
      ORDER BY signed_month ASC
    ) AS previous_period_signed_contract_value
  FROM monthly_filled
)
SELECT
  signed_month,
  signed_contract_count,
  signed_contract_value,
  previous_period_signed_contract_value,
  CASE
    WHEN previous_period_signed_contract_value IS NULL OR previous_period_signed_contract_value = 0 THEN NULL
    ELSE ROUND(
      ((signed_contract_value - previous_period_signed_contract_value)::numeric / previous_period_signed_contract_value) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(signed_contract_value) OVER() AS total_signed_contract_value
FROM monthly_with_previous
ORDER BY signed_month ASC;
```

## Mistakes To Avoid

- Do not count deleted programs, contracts, subscriptions, payment links, subscription checkout links, payments, or payment proofs unless explicitly requested.
- Do not add `is_deleted` filters to `refunds`, `invoices`, or `unmatched_payments`, because those fields do not exist in the current schema.
- Do not calculate collected revenue from contracts. Use payments for collected revenue.
- Do not calculate signed contract value from payments. Use signed contracts and `contracts.total_value`.
- Do not group or split monetary aggregates by currency unless the user explicitly asks for a currency breakdown or reconciliation by currency.
- Do not claim net revenue unless succeeded refunds have been subtracted.
- Do not use `payments.created_at` as payment revenue timing unless the user asks when payment records were created.
- Do not use `contracts.created_at` as signed revenue timing. Use `signed_at` for signed contract value.
- Do not include `DRAFT`, `LOST`, `PAID`, or `REFUNDED` in outstanding payment amounts by default.
- Do not expose payment checkout URLs, subscription checkout URLs, provider payment IDs, provider subscription IDs, provider link IDs, file keys, webhook event IDs, API keys, credentials, or raw provider/webhook payloads.
- Do not join child tables like refunds, invoices, payment links, or proofs without guarding against double-counting payments or contracts.
- Do not join contracts to programs, leads, or payments without matching `clerk_org_id` where both tables have it.
- Do not scope subscription or subscription checkout link queries directly by `clerk_org_id`, because those tables do not have `clerk_org_id`; scope through `contracts`.
- Do not invent closer, setter, creator, uploader, or owner names from IDs.
- Do not include lead email or phone unless explicitly requested.
- Do not use `SELECT *`.
- Do not generate SQL without a tenant filter.
- Do not generate non-read SQL.
- Do not answer lead-only, appointment, acquisition, integration, or full lead timeline questions from this skill.

## Related Skills

- `lead_analytics`: lead counts, lead statuses, lead sources, owners, setters, stale leads, follow-up.
- `appointment_analytics`: appointments, appointment outcomes, appointment no-show rate, Fathom call records.
- `acquisition_analytics`: opt-ins, form answers, UTM, traffic attribution, landing pages.
- `lead_360`: single-lead complete view across notes, calls, contracts, payments, and timeline.
- `integration_health`: provider connections, webhook health, API validation, integration failures.
- `semantic_context`: pgvector or hybrid semantic search over notes, call summaries, objections, action items, payment notes, refund reasons, and form answers.
