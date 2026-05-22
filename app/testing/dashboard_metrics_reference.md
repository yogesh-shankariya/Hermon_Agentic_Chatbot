# Hermon Dashboard Metrics Reference

This document summarizes the dashboard metrics currently defined in `hermon-backend`.
It is intended as a chatbot matching/reference file, so it keeps the exact metric keys,
frontend labels, repo descriptions where they exist, and the code-derived calculation
rules used by the dashboard.

## Source Of Truth

Primary backend files:

- `hermon-backend/src/modules/dashboard/dashboard.types.ts`
  - Defines dashboard metric keys, action item keys, leaderboard metric keys, and response field names.
- `hermon-backend/src/modules/dashboard/dashboard.constants.ts`
  - Defines KPI labels, KPI descriptions, KPI types, Meta metric descriptions, KPI data sources, and detail column metadata.
- `hermon-backend/src/modules/dashboard/core/kpi-calculator.ts`
  - Defines the shared KPI calculation logic used by the KPI bar, KPI chart, KPI detail rows, and leaderboard.
- `hermon-backend/src/modules/dashboard/services/dashboard-kpi-bar.service.ts`
  - Builds the KPI bar response, current period values, previous period values, growth percent, average growth, and Meta ad metrics.
- `hermon-backend/src/modules/dashboard/services/dashboard-kpi-chart.service.ts`
  - Builds time-series data for a single KPI key.
- `hermon-backend/src/modules/dashboard/services/dashboard-kpi-detail.service.ts`
  - Builds drill-down detail rows for a single KPI key.
- `hermon-backend/src/modules/dashboard/services/dashboard-leaderboard.service.ts`
  - Defines leaderboard metric labels and maps leaderboard keys to KPI calculator fields.
- `hermon-backend/src/modules/dashboard/services/dashboard-action-items.service.ts`
  - Defines action item count/list behavior.
- `hermon-backend/src/modules/dashboard/services/dashboard-chart.service.ts`
  - Defines the cash/revenue chart metrics.
- `hermon-backend/src/modules/dashboard/services/dashboard-calls-booked-pie.service.ts`
  - Defines the calls-booked pie chart metrics.
- `hermon-backend/src/modules/dashboard/services/dashboard-calendar-availability.service.ts`
  - Defines calendar availability, availability indicator, and revenue-at-risk metrics.

## Storage Model

The main dashboard KPI values are not stored in a dashboard metrics table. They are
computed live from source tables whenever the dashboard endpoints are called.

Primary source tables used for KPI computation:

- `leads`
- `appointments`
- `contracts`
- `payments`
- `refunds`
- `meta_campaign_spend` for Meta ad spend metrics

Dashboard-specific stored data:

- `calendar_availability_snapshots`
  - This table stores cached Calendly availability data such as total slots, booked slots,
    remaining slots, per-block slot data, fetch time, and expiry time.
  - It is a cache for calendar availability, not a general KPI metric store.

Other related storage:

- `saved_views`
  - Stores saved filters, columns, and sorting preferences.
  - It does not store dashboard KPI values or KPI definitions.

## Shared KPI Computation Rules

The shared KPI calculator deduplicates appointment-based metrics by lead. For each
lead, only the latest appointment in the input period is used for most appointment
metrics.

Appointment outcome role groups:

- Completed/taken outcomes are `WON`, `PARTIAL_PAYMENT`, `FOLLOW_UP`, `LOST`, and `UNQUALIFIED`.
- Excluded/scheduled-false outcomes are `CANCELED` and `RESCHEDULED`.
- New cash payment types are `FIRST_PAYMENT` and `DEPOSIT`.

Important appointment predicates:

- Scheduled appointment: latest appointment has no outcome or the outcome is not canceled/rescheduled.
- Taken call: latest past appointment has a completed/taken outcome.
- No-show: latest past appointment has outcome `NO_SHOW` or has `no_show = true`.
- Follow-up: latest appointment outcome is follow-up, or lead has `next_touch_point_at`, or lead sales status is follow-up.
- Deposit: latest past appointment outcome is `PARTIAL_PAYMENT`.
- Upcoming: latest appointment schedule time is in the future.

The same shared calculator is used by:

- KPI bar values
- KPI chart bucket values
- KPI detail row sets
- Leaderboard per-user values

## Core KPI Bar Metrics

These keys are defined in `KPI_KEYS` and `KPI_CONFIG`.

| Metric key | Label | Type | Repo description | Calculation and matching notes |
|---|---|---:|---|---|
| `new_leads` | New Leads | number | Total number of new leads created within the period, based on lead creation date. | Counts `leads` where `created_at` is inside the selected date range and the lead is not deleted. Match user questions like "new leads", "lead count", "leads created", "how many leads came in". |
| `booking_rate` | Booking Rate | percent | calls_booked / new_leads * 100. | Uses booked calls divided by new leads. Drill-down rows show the booked-call numerator set because the denominator comes from leads. Match "booking rate", "lead to booked call rate", "percent of leads that booked". |
| `calls_booked` | Booked Calls | number | Unique leads with at least one appointment (any outcome) in the period, using their latest appointment. | Counts unique leads that have at least one appointment in the period. The latest appointment per lead is used after deduplication. Match "booked calls", "calls booked", "appointments booked". |
| `calls_scheduled` | Scheduled Calls | number | Unique leads whose latest appointment is NOT cancelled or rescheduled. | Counts deduped latest appointments that are not canceled or rescheduled. Match "scheduled calls", "valid scheduled calls", "non-canceled appointments". |
| `calls_taken` | Calls Taken | number | Unique leads whose latest past appointment has a completed outcome (won, deposit, no-sale-follow-up, no-sale-lost, no-sale-unqualified). | Counts deduped past appointments whose outcome role is in the taken/completed group. Match "calls taken", "completed calls", "calls attended", "held calls". |
| `upcoming` | Upcoming | number | Unique leads whose latest appointment is scheduled in the future. | Counts deduped latest appointments where `schedule_time` is greater than now. Match "upcoming calls", "future appointments", "scheduled in future". |
| `cancelled` | Cancelled | number | Unique leads whose latest appointment outcome is 'canceled'. | Counts deduped latest appointments with outcome role `CANCELED`. Match "cancelled calls", "canceled appointments", "appointments canceled". |
| `no_show` | No Show | number | Unique leads whose latest past appointment is marked no-show or has outcome 'no-show'. | Counts deduped past appointments with outcome role `NO_SHOW` or `no_show = true`. Match "no show", "no-shows", "missed appointments". |
| `rescheduled` | Rescheduled | number | Unique leads whose latest past appointment outcome is 'rescheduled'. | Counts deduped past appointments with outcome role `RESCHEDULED`. Match "rescheduled calls", "rescheduled appointments". |
| `deposit_by_status` | Deposit | number | Unique leads whose latest past appointment outcome is 'deposit'. | Counts deduped past appointments with outcome role `PARTIAL_PAYMENT`. Match "deposit", "partial payment outcome", "deposit status". |
| `follow_up` | Follow Up | number | Unique leads whose latest appointment outcome is 'no-sale-follow-up', or who have a next touch point set, or whose lead status is 'no-sale-follow-up'. | Counts deduped latest appointments that meet any follow-up condition. Match "follow up", "follow-ups", "next touch point", "no-sale follow-up". |
| `contract_signed` | Contracts Signed | number | Number of contracts with status SIGNED and signed_at within the period. | Counts signed contracts where `signed_at` is inside the selected date range and the contract is not deleted. Match "contracts signed", "signed contracts", "deals closed" when user means contract count. |
| `contracted_amount` | Contracted Amount | currency | Sum of total_value across all signed contracts in the period. | Sums signed contract value in the selected period. For subscription contracts, the calculator falls back to the subscription amount per cycle when total value is not present. Match "contracted amount", "contract value", "revenue contracted", "signed contract value". |
| `closed_without_call` | Closed Without Call | number | Signed contracts whose lead had no appointment in the period. | Counts signed contracts whose lead is not present in the deduped appointment lead set for the same period. Match "closed without call", "signed without appointment", "contracts without calls". |
| `cash_collected` | Cash Collected | currency | Sum of PAID payments in the period minus any associated succeeded refunds. | Sums paid payment amounts in the selected period and subtracts succeeded refunds attached to those payments. Match "cash collected", "collected cash", "paid amount", "net cash collected". |
| `new_cash_collected` | New Cash Collected | currency | Sum of PAID payments of type FIRST_PAYMENT or DEPOSIT in the period. | Sums paid payments where payment type is `FIRST_PAYMENT` or `DEPOSIT`. Match "new cash", "first payments", "deposit payments", "new money collected". |
| `refunded_amount` | Refunded | currency | Sum of all succeeded refunds with refunded_at in the period. | Sums succeeded refunds where `refunded_at` is inside the selected date range. Match "refunds", "refunded amount", "money refunded". |
| `show_rate_percent` | Show Rate (Scheduled) | percent | calls_taken / scheduled calls with a past schedule date * 100. | Uses calls taken divided by scheduled calls whose schedule date is in the past. Future scheduled calls are excluded from the denominator. Match "show rate scheduled", "attendance rate for scheduled calls". |
| `adjusted_show_rate_percent` | Show Rate (Booked) | percent | calls_taken / calls_booked * 100. | Uses calls taken divided by all booked calls. Match "show rate booked", "show rate of booked calls", "adjusted show rate". |
| `cancel_rate_percent` | Cancel Rate | percent | cancelled / calls_booked * 100. | Uses cancelled calls divided by booked calls. Match "cancel rate", "cancellation rate", "percent canceled". |
| `closing_rate_booked_percent` | Close Rate (Scheduled) | percent | contract_signed / calls_scheduled * 100. | Uses signed contracts divided by scheduled calls. The label says scheduled, but the key uses `booked` historically. Match "close rate scheduled", "closing rate on scheduled calls". |
| `closing_rate_taken_percent` | Close Rate (Taken) | percent | contract_signed / calls_taken * 100. | Uses signed contracts divided by calls taken. Match "close rate taken", "closing rate from attended calls", "contract close rate from taken calls". |
| `cash_per_call_booked` | Cash / Call Scheduled | currency | new_cash_collected / calls_scheduled. | Uses new cash collected divided by scheduled calls. The key uses `booked`, but the label and formula denominator are scheduled calls. Match "cash per scheduled call", "cash per call scheduled". |
| `cash_per_call_taken` | Cash / Call Taken | currency | new_cash_collected / calls_taken. | Uses new cash collected divided by calls taken. Match "cash per taken call", "cash per completed call", "cash per attended call". |

## Meta Ad KPI Metrics

These metrics are defined in `META_METRIC_METAS` and `META_KPI_CONFIG`. They are surfaced
in the KPI bar `available_metrics` only when Meta Ads is connected and at least one selected
Meta campaign/ad account is available.

| Metric key | Label | Type | Repo description | Calculation and matching notes |
|---|---|---:|---|---|
| `ad_spend` | Ad Spend | currency | Total Meta ad spend in the period (organization currency). | Sums `meta_campaign_spend.spend_converted` for selected campaigns and selected ad accounts in the selected period. Match "ad spend", "Meta spend", "Facebook spend". |
| `cost_per_lead` | Cost per Lead | currency | Ad spend / new leads in the period. | Uses Meta ad spend divided by new leads. Match "CPL", "cost per lead". |
| `cost_per_call` | Cost per Call | currency | Ad spend / calls booked in the period. | Uses Meta ad spend divided by booked calls. Match "cost per call", "cost per booked call". |
| `cost_per_call_taken` | Cost per Call Taken | currency | Ad spend / calls taken in the period. | Uses Meta ad spend divided by calls taken. Match "cost per attended call", "cost per taken call". |
| `cost_per_acquisition` | Cost per Acquisition | currency | Ad spend / contracts signed in the period. | Uses Meta ad spend divided by signed contracts. Match "CPA", "cost per acquisition", "cost per signed contract". |
| `roas` | ROAS | ratio | Cash collected / ad spend (ratio). | Uses cash collected divided by Meta ad spend. Match "ROAS", "return on ad spend". |

## KPI Detail Row Modules

The KPI detail endpoint returns drill-down rows for one KPI key. The metric key decides
which module and row shape is returned.

| KPI key or group | Detail module | Drill-down behavior |
|---|---|---|
| `new_leads` | lead | Shows leads created in the selected date range. |
| Appointment metrics | appointment | Shows appointment rows after latest-appointment-per-lead deduplication and the relevant metric predicate. Applies to `calls_booked`, `calls_scheduled`, `calls_taken`, `upcoming`, `cancelled`, `no_show`, `rescheduled`, `deposit_by_status`, `follow_up`, `show_rate_percent`, `adjusted_show_rate_percent`, `cancel_rate_percent`, and `booking_rate`. |
| Contract metrics | contract | Shows signed contract rows. Applies to `contract_signed`, `contracted_amount`, `closed_without_call`, `closing_rate_booked_percent`, and `closing_rate_taken_percent`. |
| Payment metrics | payment | Shows payment rows. Applies to `cash_collected`, `new_cash_collected`, `cash_per_call_booked`, and `cash_per_call_taken`. |
| Refund metric | payment | Shows refund rows for `refunded_amount`. |

## KPI Chart Metrics

The KPI chart endpoint accepts one `KPI_KEYS` metric key and returns a time series for that
metric. It uses the same metric definitions and calculator as the KPI bar.

Chart granularity is selected by date range:

- Daily when the range is under 31 days.
- Weekly when the range is at least 31 days and under 183 days.
- Monthly when the range is at least 183 days.

KPI chart data sources:

| Metric key | Source data used by chart |
|---|---|
| `new_leads` | leads |
| `booking_rate` | appointments, leads |
| `calls_booked` | appointments |
| `calls_scheduled` | appointments |
| `calls_taken` | appointments |
| `upcoming` | appointments |
| `cancelled` | appointments |
| `no_show` | appointments |
| `rescheduled` | appointments |
| `deposit_by_status` | appointments |
| `follow_up` | appointments |
| `contract_signed` | contracts |
| `contracted_amount` | contracts |
| `closed_without_call` | appointments, contracts |
| `cash_collected` | payments |
| `new_cash_collected` | payments |
| `refunded_amount` | refunds |
| `show_rate_percent` | appointments |
| `adjusted_show_rate_percent` | appointments |
| `cancel_rate_percent` | appointments |
| `closing_rate_booked_percent` | appointments, contracts |
| `closing_rate_taken_percent` | appointments, contracts |
| `cash_per_call_booked` | appointments, payments |
| `cash_per_call_taken` | appointments, payments |

## Dashboard Action Item Metrics

These are count/list metrics defined in `ACTION_ITEM_KEYS`.

| Metric key | Label to use | Description and behavior |
|---|---|---|
| `today_appointments` | Today Appointments | Count and list of appointments scheduled for today for the selected organization and role scope. For closers it filters by host/closer, for setters by setter, and for triagers by triager. |
| `payments_at_risk` | Payments At Risk | Count and list of payments considered at risk by the payment domain service. The dashboard action item delegates count/list logic to `PaymentService.countPaymentsAtRisk` and `PaymentService.getPaymentsAtRisk`. |
| `follow_ups` | Follow Ups | Count and list of due-today or overdue lead follow-ups. The dashboard action item delegates count/list logic to `LeadService.countFollowUps` and `LeadService.getFollowUps`. |
| `pending_contracts` | Pending Contracts | Count and list of pending contracts for the dashboard action item card. The dashboard action item delegates count/list logic to `ContractService.countPendingContracts` and `ContractService.getPendingContracts`. |
| `missing_outcomes` | Missing Outcomes | Count and list of sales or triage appointments that need an outcome. The dashboard action item delegates count/list logic to `AppointmentService.countMissingOutcomes` and `AppointmentService.getMissingOutcomes`. |

## Cash And Revenue Chart Metrics

These metrics are returned by the general dashboard chart endpoint, not the KPI chart endpoint.

| Metric field | Label to use | Description and behavior |
|---|---|---|
| `cash_amount` | Cash Amount | Sum of paid payment amounts in each date bucket. It is calculated from `payments` where status is `PAID`, `paid_at` is inside the selected date range, and the payment is not deleted. |
| `revenue_amount` | Revenue Amount | Sum of signed contract total values in each date bucket. It is calculated from `contracts` where status is `SIGNED`, `signed_at` is inside the selected date range, and the contract is not deleted. |
| `total_cash_amount` | Total Cash Amount | Sum of all `cash_amount` values across the chart response. |
| `total_revenue_amount` | Total Revenue Amount | Sum of all `revenue_amount` values across the chart response. |

## Calls Booked Pie Metrics

These metrics are returned by the calls-booked pie endpoint.

| Metric field | Label to use | Description and behavior |
|---|---|---|
| `total_calls_booked` | Total Calls Booked | Total appointment count for the selected filters. The service groups appointments by `appointment_event_type_id` and `snapshot_event_name`, then sums the group counts. |
| `slices[].event_type_name` | Event Type Name | Display name for the appointment event type slice. Manual appointments are grouped under `Manual`. Provider event names include call category where appropriate. Duplicate event names are disambiguated with owner name. |
| `slices[].total_calls_booked` | Calls Booked For Slice | Number of booked calls in that event type slice. |
| `slices[].percentage` | Slice Percentage | Slice booked calls divided by `total_calls_booked`, multiplied by 100 and rounded to two decimals. |

## Calendar Availability Metrics

These metrics are returned by the calendar availability endpoint. Calendly slot data is cached
in `calendar_availability_snapshots` for 30 minutes. Revenue-at-risk values are computed from
fresh 90-day historical appointment and contract/payment data.

Calendar availability constants:

- Cache TTL: 30 minutes.
- Forward availability window: 7 days.
- Historical window for show rate, close rate, and average deal value: 90 days.
- Close attribution window: 30 days after a call.
- Minimum appointments per time block before revenue estimates are shown: 5.
- Minimum deals per time block before revenue estimates are shown: 2.
- Time buckets: `morning`, `afternoon`, `evening`, `night`.

| Metric field | Label to use | Description and behavior |
|---|---|---|
| `total_slots` | Total Slots | Total available plus booked Calendly slots for the selected event type in the next 7-day window. |
| `booked_slots` | Booked Slots | Number of scheduled Calendly events for the selected event type in the next 7-day window. |
| `remaining_slots` | Remaining Slots | Number of available Calendly invitee slots remaining for the selected event type in the next 7-day window. |
| `availability_percent` | Availability Percent | `remaining_slots / total_slots * 100`, rounded to two decimals. If total slots are zero, the value is zero. |
| `availability_indicator` | Availability Indicator | Green when availability is at least 50 percent, yellow when availability is at least 25 percent and below 50 percent, and red when below 25 percent. |
| `total_revenue_at_risk` | Total Revenue At Risk | Sum of revenue-at-risk values across all returned time blocks. |
| `has_sufficient_data` | Has Sufficient Data | True when at least one returned time block has enough historical appointments and deals to calculate revenue estimates. |
| `insufficient_data_message` | Insufficient Data Message | Returned when there is not enough historical data to calculate revenue at risk. The message is: "Revenue at Risk will be calculated once sufficient historical data is available." |
| `time_blocks[].booked_slots` | Time Block Booked Slots | Number of booked slots in a specific date and time-of-day bucket. |
| `time_blocks[].show_rate` | Time Block Show Rate | Historical calls taken divided by historical calls scheduled for that time bucket. Null means insufficient historical data. |
| `time_blocks[].close_rate` | Time Block Close Rate | Historical deals closed divided by historical calls taken for that time bucket. Null means insufficient historical data. |
| `time_blocks[].avg_deal_value` | Time Block Average Deal Value | Historical total revenue divided by historical deals closed for that time bucket. Null means insufficient historical data. |
| `time_blocks[].revenue_per_slot` | Revenue Per Slot | `show_rate * close_rate * avg_deal_value` for the time bucket. Null means insufficient historical data. |
| `time_blocks[].revenue_at_risk` | Revenue At Risk | `booked_slots * revenue_per_slot` for the time block. Zero is used when there is insufficient data. |
| `time_blocks[].has_sufficient_data` | Time Block Has Sufficient Data | True when the time bucket has at least the configured minimum historical appointments and deals. |

## Leaderboard Metrics

Leaderboard metric keys are defined in `LEADERBOARD_METRIC_KEYS`. The labels and types are
defined in `DashboardLeaderboardService`. Most leaderboard metrics map to the shared KPI
calculator; setter-only metrics are computed separately from appointment call categories.

Leaderboard tabs:

- `closer`
- `setter`
- `triager`

Role grouping:

- Closer tab uses appointment `host_id`, contract `closer_id`, and payment `closer_id`.
- Setter tab uses appointment `setter_id`, contract `setter_id`, and payment `setter_id`.
- Triager tab uses appointment `host_id` for triage appointments, contract `triager_id`, and payment `triager_id`.

| Metric key | Label | Type | Description and behavior |
|---|---|---:|---|
| `deals_closed` | Deals Closed | number | Maps to the core KPI `contract_signed`. Counts signed contracts for each leaderboard user in the selected period. |
| `contracted_amount` | Contracted Amount | currency | Maps to the core KPI `contracted_amount`. Sums signed contract values for each leaderboard user in the selected period. |
| `cash_collected` | Cash Collected | currency | Maps to the core KPI `cash_collected`. Sums paid payments minus associated succeeded refunds for each leaderboard user. |
| `new_cash_collected` | New Cash Collected | currency | Maps to the core KPI `new_cash_collected`. Sums paid `FIRST_PAYMENT` and `DEPOSIT` payments for each leaderboard user. |
| `refunded_amount` | Refunded | currency | Maps to the core KPI `refunded_amount`. Sums succeeded refunds for each leaderboard user. |
| `calls_booked` | Booked Calls | number | Maps to the core KPI `calls_booked`. Counts unique leads with appointments for each leaderboard user. |
| `calls_scheduled` | Scheduled Calls | number | Maps to the core KPI `calls_scheduled`. Counts unique leads whose latest appointment is not canceled or rescheduled for each leaderboard user. |
| `calls_taken` | Calls Taken | number | Maps to the core KPI `calls_taken`. Counts completed/taken calls for each leaderboard user. |
| `close_rate_scheduled_percent` | Close Rate (Scheduled) | percent | Maps to core KPI `closing_rate_booked_percent`, which uses signed contracts divided by scheduled calls. |
| `close_rate_taken_percent` | Close Rate (Taken) | percent | Maps to core KPI `closing_rate_taken_percent`, which uses signed contracts divided by calls taken. |
| `show_rate_scheduled_percent` | Show Rate (Scheduled) | percent | Maps to core KPI `show_rate_percent`, which uses calls taken divided by past scheduled calls. |
| `show_rate_booked_percent` | Show Rate (Booked) | percent | Maps to core KPI `adjusted_show_rate_percent`, which uses calls taken divided by booked calls. |
| `cancel_rate_percent` | Cancel Rate | percent | Maps to core KPI `cancel_rate_percent`, which uses cancelled calls divided by booked calls. |
| `closed_without_call` | Closed Without Call | number | Maps to core KPI `closed_without_call`. Counts signed contracts whose lead had no appointment in the selected period. |
| `cash_per_call_scheduled` | Cash / Call Scheduled | currency | Maps to core KPI `cash_per_call_booked`, which uses new cash collected divided by scheduled calls. |
| `cash_per_call_taken` | Cash / Call Taken | currency | Maps to core KPI `cash_per_call_taken`, which uses new cash collected divided by calls taken. |
| `no_show` | No Show | number | Maps to core KPI `no_show`. Counts no-show calls for each leaderboard user. |
| `deposit_by_status` | Deposit | number | Maps to core KPI `deposit_by_status`. Counts latest past appointment outcomes that are deposit/partial payment. |
| `sales_calls` | Sales Calls | number | Setter-only metric. Counts appointments assigned to the setter where `snapshot_call_category` is `SALES_CALL`. |
| `triage_calls` | Triage Calls | number | Setter-only metric. Counts appointments assigned to the setter where `snapshot_call_category` is `TRIAGE_CALL`. |
| `triage_to_sales_percent` | Triage > Sales % | percent | Setter-only metric. Uses `sales_calls / triage_calls * 100`. If triage calls are zero, the value is zero. |
| `show_rate_triage_percent` | Show Rate Triage | percent | Setter-only metric. Runs the shared KPI calculator on the setter's triage appointments and uses `show_rate_percent`. |
| `show_rate_sales_percent` | Show Rate Sales | percent | Setter-only metric. Runs the shared KPI calculator on the setter's sales appointments and uses `show_rate_percent`. |

## Chatbot Matching Guidance

Use the exact metric keys for internal matching and the labels/descriptions for natural
language matching.

Recommended matching priority:

1. Match exact metric key first, for example `cash_collected`.
2. Match exact label second, for example "Cash Collected".
3. Match obvious aliases from the description and calculation notes, for example:
   - "revenue collected" or "paid amount" -> `cash_collected`
   - "signed deals" or "deals closed" -> `contract_signed` or leaderboard `deals_closed`
   - "appointments booked" -> `calls_booked`
   - "appointments held" or "attended calls" -> `calls_taken`
   - "attendance rate" -> `show_rate_percent` or `adjusted_show_rate_percent` depending on denominator
   - "cancellation percentage" -> `cancel_rate_percent`
   - "cost per acquisition" or "CPA" -> `cost_per_acquisition`
   - "return on ad spend" -> `roas`
4. If the user asks for a leaderboard ranking, prefer `LEADERBOARD_METRIC_KEYS`.
5. If the user asks for drill-down rows or "show me the records behind this", use KPI detail behavior.
6. If the user asks about stored dashboard metrics, answer that KPI values are computed live and not stored in a dashboard metrics table, except calendar availability snapshots are cached.

