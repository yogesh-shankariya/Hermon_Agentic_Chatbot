# Revenue Analytics Silver Truth

## 1. RAQ-004

**Question**

What was the gross paid revenue from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  p.currency,
  COUNT(*) AS paid_payment_count,
  SUM(p.amount) AS gross_paid_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
  AND p.paid_at >= :start_date
  AND p.paid_at < :end_date
GROUP BY p.currency
ORDER BY gross_paid_amount DESC, p.currency ASC
```

**Generated final answer**

The gross paid revenue from 2026-04-01 to 2026-05-01 was EUR 26,500,000 across 65 paid payments.

**Execution time:** 16.637 sec
**Status:** ok

## 2. RAQ-002

**Question**

What is our gross paid revenue before refunds?

**Generated SQL**

```sql
SELECT
  p.currency,
  SUM(p.amount) AS gross_paid_amount,
  COUNT(*) AS paid_payment_count
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
GROUP BY p.currency
ORDER BY gross_paid_amount DESC, p.currency ASC;
```

**Generated final answer**

Your gross paid revenue before refunds is EUR 56,425,000.00 from 158 paid payments.

**Execution time:** 17.859 sec
**Status:** ok

## 3. RAQ-001

**Question**

How much net collected revenue have we collected so far?

**Generated SQL**

```sql
WITH paid_payments AS (
  SELECT
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
  GROUP BY p.currency
), succeeded_refunds AS (
  SELECT
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.currency
)
SELECT
  COALESCE(pp.currency, sr.currency) AS currency,
  COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue
FROM paid_payments pp
FULL OUTER JOIN succeeded_refunds sr
  ON sr.currency = pp.currency
ORDER BY currency ASC;
```

**Generated final answer**

Your net collected revenue so far is EUR 56,075,000.00.

**Execution time:** 20.317 sec
**Status:** ok

## 4. RAQ-003

**Question**

How much net collected revenue did we collect from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
WITH paid_payments AS (
  SELECT
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY p.currency
), succeeded_refunds AS (
  SELECT
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY r.currency
)
SELECT
  COALESCE(pp.currency, sr.currency) AS currency,
  COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue
FROM paid_payments pp
FULL OUTER JOIN succeeded_refunds sr
  ON sr.currency = pp.currency
ORDER BY currency ASC;
```

**Generated final answer**

From 2026-04-01 to 2026-05-01, net collected revenue was EUR 26,500,000.00.

**Execution time:** 22.776 sec
**Status:** ok

## 5. RAQ-005

**Question**

How much revenue did we collect across the previous 3 completed months from 2026-02-01 to 2026-05-01?

**Generated SQL**

```sql
WITH paid_payments AS (
  SELECT
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY p.currency
), succeeded_refunds AS (
  SELECT
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY r.currency
)
SELECT
  COALESCE(pp.currency, sr.currency) AS currency,
  COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue
FROM paid_payments pp
FULL OUTER JOIN succeeded_refunds sr
  ON sr.currency = pp.currency
ORDER BY currency ASC;
```

**Generated final answer**

Across Feb–Apr 2026 (2026-02-01 to 2026-05-01), net collected revenue was EUR 56,075,000, based on EUR 56,425,000 in paid payments minus EUR 350,000 in succeeded refunds.

**Execution time:** 35.072 sec
**Status:** ok

## 6. RAQ-007

**Question**

Compare gross paid amount and refunded amount for revenue collected from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH paid_payments AS (
  SELECT
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY p.currency
), succeeded_refunds AS (
  SELECT
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY r.currency
)
SELECT
  COALESCE(pp.currency, sr.currency) AS currency,
  COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue,
  ROUND(
    COALESCE(sr.refunded_amount, 0) * 100.0 / NULLIF(COALESCE(pp.gross_paid_amount, 0), 0),
    2
  ) AS refunded_as_percent_of_gross
FROM paid_payments pp
FULL OUTER JOIN succeeded_refunds sr
  ON sr.currency = pp.currency
ORDER BY currency ASC;
```

**Generated final answer**

From 2026-04-01 to 2026-05-01, gross paid amount was EUR 26,500,000.00 and refunded amount was EUR 0.00, so net collected revenue was EUR 26,500,000.00.

**Execution time:** 41.373 sec
**Status:** ok

## 7. RAQ-006

**Question**

Show net collected revenue by currency from 2026-01-01 to 2026-04-01.

**Generated SQL**

```sql
WITH paid_payments AS (
  SELECT
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY p.currency
), succeeded_refunds AS (
  SELECT
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY r.currency
)
SELECT
  COALESCE(pp.currency, sr.currency) AS currency,
  COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue
FROM paid_payments pp
FULL OUTER JOIN succeeded_refunds sr
  ON sr.currency = pp.currency
ORDER BY currency ASC;
```

**Generated final answer**

Here is the net collected revenue by currency for 2026-01-01 through 2026-04-01:

| Currency | Gross paid | Refunded | Net collected revenue |
|---|---:|---:|---:|
| EUR | 30,905,000.00 | 350,000.00 | 30,555,000.00 |

**Execution time:** 43.508 sec
**Status:** ok

## 8. RAQ-010

**Question**

Show monthly gross paid revenue from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS payment_month
), currencies AS (
  SELECT DISTINCT p.currency
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
), monthly_amounts AS (
  SELECT
    DATE_TRUNC('month', p.paid_at)::date AS payment_month,
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY DATE_TRUNC('month', p.paid_at)::date, p.currency
), monthly_filled AS (
  SELECT
    m.payment_month,
    c.currency,
    COALESCE(ma.gross_paid_amount, 0) AS gross_paid_amount
  FROM months m
  CROSS JOIN currencies c
  LEFT JOIN monthly_amounts ma
    ON ma.payment_month = m.payment_month
   AND ma.currency = c.currency
), monthly_with_previous AS (
  SELECT
    payment_month,
    currency,
    gross_paid_amount,
    LAG(gross_paid_amount) OVER (
      PARTITION BY currency
      ORDER BY payment_month ASC
    ) AS previous_period_gross_paid_amount
  FROM monthly_filled
)
SELECT
  payment_month,
  currency,
  gross_paid_amount,
  previous_period_gross_paid_amount,
  CASE
    WHEN previous_period_gross_paid_amount IS NULL OR previous_period_gross_paid_amount = 0 THEN NULL
    ELSE ROUND(
      ((gross_paid_amount - previous_period_gross_paid_amount)::numeric / previous_period_gross_paid_amount) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(gross_paid_amount) OVER (PARTITION BY currency) AS total_gross_paid_amount_for_currency
FROM monthly_with_previous
ORDER BY payment_month ASC, currency ASC
```

**Generated final answer**

Total gross paid revenue: EUR 56,425,000

Here is the monthly gross paid revenue trend for May 2025 through Apr 2026:

| Month | Gross paid revenue | Previous month | % change |
|---|---:|---:|---:|
| May 2025 | EUR 0 | — | — |
| Jun 2025 | EUR 0 | EUR 0 | — |
| Jul 2025 | EUR 0 | EUR 0 | — |
| Aug 2025 | EUR 0 | EUR 0 | — |
| Sep 2025 | EUR 0 | EUR 0 | — |
| Oct 2025 | EUR 0 | EUR 0 | — |
| Nov 2025 | EUR 0 | EUR 0 | — |
| Dec 2025 | EUR 0 | EUR 0 | — |
| Jan 2026 | EUR 0 | EUR 0 | — |
| Feb 2026 | EUR 0 | EUR 0 | — |
| Mar 2026 | EUR 29,925,000 | EUR 0 | — |
| Apr 2026 | EUR 26,500,000 | EUR 29,925,000 | -11.45% |

In Apr 2026, gross paid revenue was EUR 26,500,000, down 11.45% from EUR 29,925,000 in Mar 2026.

**Execution time:** 52.416 sec
**Status:** ok

## 9. RAQ-009

**Question**

Show the monthly net revenue trend from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS revenue_month
), currencies AS (
  SELECT DISTINCT currency
  FROM (
    SELECT p.currency
    FROM payments p
    WHERE p.clerk_org_id = :org_id
      AND p.is_deleted = false
      AND p.status = 'PAID'
      AND p.paid_at >= :start_date
      AND p.paid_at < :end_date

    UNION

    SELECT r.currency
    FROM refunds r
    JOIN payments p
      ON p.id = r.payment_id
     AND p.clerk_org_id = r.clerk_org_id
     AND p.is_deleted = false
    WHERE r.clerk_org_id = :org_id
      AND r.status = 'SUCCEEDED'
      AND COALESCE(r.refunded_at, r.created_at) >= :start_date
      AND COALESCE(r.refunded_at, r.created_at) < :end_date
  ) currencies_in_range
), monthly_grid AS (
  SELECT
    m.revenue_month,
    c.currency
  FROM months m
  CROSS JOIN currencies c
), monthly_paid AS (
  SELECT
    DATE_TRUNC('month', p.paid_at)::date AS revenue_month,
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY DATE_TRUNC('month', p.paid_at)::date, p.currency
), monthly_refunds AS (
  SELECT
    DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date AS revenue_month,
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date, r.currency
), monthly_net AS (
  SELECT
    mg.revenue_month,
    mg.currency,
    COALESCE(mp.gross_paid_amount, 0) AS gross_paid_amount,
    COALESCE(mr.refunded_amount, 0) AS refunded_amount,
    COALESCE(mp.gross_paid_amount, 0) - COALESCE(mr.refunded_amount, 0) AS net_collected_revenue
  FROM monthly_grid mg
  LEFT JOIN monthly_paid mp
    ON mp.revenue_month = mg.revenue_month
   AND mp.currency = mg.currency
  LEFT JOIN monthly_refunds mr
    ON mr.revenue_month = mg.revenue_month
   AND mr.currency = mg.currency
), monthly_with_previous AS (
  SELECT
    revenue_month,
    currency,
    gross_paid_amount,
    refunded_amount,
    net_collected_revenue,
    LAG(net_collected_revenue) OVER (
      PARTITION BY currency
      ORDER BY revenue_month ASC
    ) AS previous_period_net_collected_revenue
  FROM monthly_net
)
SELECT
  revenue_month,
  currency,
  gross_paid_amount,
  refunded_amount,
  net_collected_revenue,
  previous_period_net_collected_revenue,
  CASE
    WHEN previous_period_net_collected_revenue IS NULL OR previous_period_net_collected_revenue = 0 THEN NULL
    ELSE ROUND(
      ((net_collected_revenue - previous_period_net_collected_revenue)::numeric / previous_period_net_collected_revenue) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(net_collected_revenue) OVER (PARTITION BY currency) AS total_net_collected_revenue_for_currency
FROM monthly_with_previous
ORDER BY revenue_month ASC, currency ASC
```

**Generated final answer**

Total net revenue from May 2025 through Apr 2026 was EUR 56,075,000; all amounts below are in EUR.

| Month | Gross paid | Refunded | Net revenue | Previous month | % change |
|---|---:|---:|---:|---:|---:|
| May 2025 | 0 | 0 | 0 | — | — |
| Jun 2025 | 0 | 0 | 0 | 0 | — |
| Jul 2025 | 0 | 0 | 0 | 0 | — |
| Aug 2025 | 0 | 0 | 0 | 0 | — |
| Sep 2025 | 0 | 0 | 0 | 0 | — |
| Oct 2025 | 0 | 0 | 0 | 0 | — |
| Nov 2025 | 0 | 0 | 0 | 0 | — |
| Dec 2025 | 0 | 0 | 0 | 0 | — |
| Jan 2026 | 0 | 0 | 0 | 0 | — |
| Feb 2026 | 0 | 0 | 0 | 0 | — |
| Mar 2026 | 29,925,000 | 350,000 | 29,575,000 | 0 | — |
| Apr 2026 | 26,500,000 | 0 | 26,500,000 | 29,575,000 | -10.40% |

In Apr 2026, net revenue decreased by EUR 3,075,000 versus Mar 2026, a 10.40% decline.

**Execution time:** 73.502 sec
**Status:** ok

## 10. RAQ-008

**Question**

Show the daily revenue trend from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH date_range AS (
  SELECT generate_series(
    CAST(:start_date AS date),
    (CAST(:end_date AS date) - INTERVAL '1 day')::date,
    INTERVAL '1 day'
  )::date AS payment_date
), currencies AS (
  SELECT DISTINCT currency
  FROM (
    SELECT p.currency
    FROM payments p
    WHERE p.clerk_org_id = :org_id
      AND p.is_deleted = false
      AND p.status = 'PAID'
      AND p.paid_at >= CAST(:start_date AS timestamp)
      AND p.paid_at < CAST(:end_date AS timestamp)

    UNION

    SELECT r.currency
    FROM refunds r
    JOIN payments p
      ON p.id = r.payment_id
     AND p.clerk_org_id = r.clerk_org_id
     AND p.is_deleted = false
    WHERE r.clerk_org_id = :org_id
      AND r.status = 'SUCCEEDED'
      AND COALESCE(r.refunded_at, r.created_at) >= CAST(:start_date AS timestamp)
      AND COALESCE(r.refunded_at, r.created_at) < CAST(:end_date AS timestamp)
  ) currencies_in_range
), daily_grid AS (
  SELECT
    dr.payment_date,
    c.currency
  FROM date_range dr
  CROSS JOIN currencies c
), daily_paid AS (
  SELECT
    DATE_TRUNC('day', p.paid_at)::date AS payment_date,
    p.currency,
    COUNT(*) AS paid_payment_count,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= CAST(:start_date AS timestamp)
    AND p.paid_at < CAST(:end_date AS timestamp)
  GROUP BY DATE_TRUNC('day', p.paid_at)::date, p.currency
), daily_refunds AS (
  SELECT
    DATE_TRUNC('day', COALESCE(r.refunded_at, r.created_at))::date AS payment_date,
    r.currency,
    COUNT(*) AS succeeded_refund_count,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= CAST(:start_date AS timestamp)
    AND COALESCE(r.refunded_at, r.created_at) < CAST(:end_date AS timestamp)
  GROUP BY DATE_TRUNC('day', COALESCE(r.refunded_at, r.created_at))::date, r.currency
)
SELECT
  dg.payment_date,
  dg.currency,
  COALESCE(dp.paid_payment_count, 0) AS paid_payment_count,
  COALESCE(dp.gross_paid_amount, 0) AS gross_paid_amount,
  COALESCE(dr.succeeded_refund_count, 0) AS succeeded_refund_count,
  COALESCE(dr.refunded_amount, 0) AS refunded_amount,
  COALESCE(dp.gross_paid_amount, 0) - COALESCE(dr.refunded_amount, 0) AS net_collected_revenue
FROM daily_grid dg
LEFT JOIN daily_paid dp
  ON dp.payment_date = dg.payment_date
 AND dp.currency = dg.currency
LEFT JOIN daily_refunds dr
  ON dr.payment_date = dg.payment_date
 AND dr.currency = dg.currency
ORDER BY dg.payment_date ASC, dg.currency ASC
```

**Generated final answer**

Here is the daily net revenue trend in EUR from 2026-04-01 to 2026-05-01; no succeeded refunds were recorded in this period.

| Date | Net Revenue |
|---|---:|
| 2026-04-01 | 980,000 |
| 2026-04-02 | 400,000 |
| 2026-04-03 | 2,080,000 |
| 2026-04-04 | 1,180,000 |
| 2026-04-05 | 300,000 |
| 2026-04-06 | 500,000 |
| 2026-04-07 | 1,000,000 |
| 2026-04-08 | 1,430,000 |
| 2026-04-09 | 1,050,000 |
| 2026-04-10 | 1,930,000 |
| 2026-04-11 | 1,480,000 |
| 2026-04-12 | 820,000 |
| 2026-04-13 | 750,000 |
| 2026-04-14 | 1,460,000 |
| 2026-04-15 | 480,000 |
| 2026-04-16 | 500,000 |
| 2026-04-17 | 1,750,000 |
| 2026-04-18 | 1,700,000 |
| 2026-04-19 | 250,000 |
| 2026-04-20 | 500,000 |
| 2026-04-21 | 2,000,000 |
| 2026-04-22 | 480,000 |
| 2026-04-23 | 2,180,000 |
| 2026-04-24 | 1,300,000 |
| 2026-04-25 | 0 |
| 2026-04-26 | 0 |
| 2026-04-27 | 0 |
| 2026-04-28 | 0 |
| 2026-04-29 | 0 |
| 2026-04-30 | 0 |
| 2026-05-01 | 0 |

**Execution time:** 80.281 sec
**Status:** ok

## 11. RAQ-012

**Question**

Which month had the highest net collected revenue from 2025-05-01 to 2026-05-01?

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS revenue_month
), currencies AS (
  SELECT DISTINCT p.currency
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date

  UNION

  SELECT DISTINCT r.currency
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
), monthly_grid AS (
  SELECT
    m.revenue_month,
    c.currency
  FROM months m
  CROSS JOIN currencies c
), paid_payments AS (
  SELECT
    DATE_TRUNC('month', p.paid_at)::date AS revenue_month,
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY DATE_TRUNC('month', p.paid_at)::date, p.currency
), succeeded_refunds AS (
  SELECT
    DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date AS revenue_month,
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date, r.currency
), monthly_net_revenue AS (
  SELECT
    mg.revenue_month,
    mg.currency,
    COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
    COALESCE(sr.refunded_amount, 0) AS refunded_amount,
    COALESCE(pp.gross_paid_amount, 0) - COALESCE(sr.refunded_amount, 0) AS net_collected_revenue
  FROM monthly_grid mg
  LEFT JOIN paid_payments pp
    ON pp.revenue_month = mg.revenue_month
   AND pp.currency = mg.currency
  LEFT JOIN succeeded_refunds sr
    ON sr.revenue_month = mg.revenue_month
   AND sr.currency = mg.currency
), ranked_months AS (
  SELECT
    revenue_month,
    currency,
    gross_paid_amount,
    refunded_amount,
    net_collected_revenue,
    DENSE_RANK() OVER (
      PARTITION BY currency
      ORDER BY net_collected_revenue DESC
    ) AS revenue_rank
  FROM monthly_net_revenue
)
SELECT
  revenue_month,
  currency,
  gross_paid_amount,
  refunded_amount,
  net_collected_revenue
FROM ranked_months
WHERE revenue_rank = 1
ORDER BY currency ASC, revenue_month ASC;
```

**Generated final answer**

Within 2025-05-01 to 2026-05-01, March 2026 had the highest net collected revenue at EUR 29,575,000.

**Execution time:** 43.723 sec
**Status:** ok

## 12. RAQ-011

**Question**

Show the monthly signed contract value trend from 2025-05-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS signed_month
), currencies AS (
  SELECT DISTINCT c.currency
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND c.signed_at >= :start_date
    AND c.signed_at < :end_date
), monthly_grid AS (
  SELECT
    m.signed_month,
    cur.currency
  FROM months m
  CROSS JOIN currencies cur
), monthly_counts AS (
  SELECT
    DATE_TRUNC('month', c.signed_at)::date AS signed_month,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND c.signed_at >= :start_date
    AND c.signed_at < :end_date
  GROUP BY DATE_TRUNC('month', c.signed_at)::date, c.currency
), monthly_filled AS (
  SELECT
    mg.signed_month,
    mg.currency,
    COALESCE(mc.signed_contract_count, 0) AS signed_contract_count,
    COALESCE(mc.signed_contract_value, 0) AS signed_contract_value
  FROM monthly_grid mg
  LEFT JOIN monthly_counts mc
    ON mc.signed_month = mg.signed_month
   AND mc.currency = mg.currency
), monthly_with_previous AS (
  SELECT
    signed_month,
    currency,
    signed_contract_count,
    signed_contract_value,
    LAG(signed_contract_value) OVER (
      PARTITION BY currency
      ORDER BY signed_month ASC
    ) AS previous_period_signed_contract_value
  FROM monthly_filled
)
SELECT
  signed_month,
  currency,
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
  SUM(signed_contract_value) OVER (PARTITION BY currency) AS total_signed_contract_value_for_currency
FROM monthly_with_previous
ORDER BY signed_month ASC, currency ASC
```

**Generated final answer**

Total signed contract value in the period: EUR 58,040,000

Here is the monthly trend:

| Month | Signed contract value | Previous month | % change |
|---|---:|---:|---:|
| May 2025 | EUR 0 | — | — |
| Jun 2025 | EUR 0 | EUR 0 | — |
| Jul 2025 | EUR 0 | EUR 0 | — |
| Aug 2025 | EUR 0 | EUR 0 | — |
| Sep 2025 | EUR 0 | EUR 0 | — |
| Oct 2025 | EUR 0 | EUR 0 | — |
| Nov 2025 | EUR 0 | EUR 0 | — |
| Dec 2025 | EUR 0 | EUR 0 | — |
| Jan 2026 | EUR 0 | EUR 0 | — |
| Feb 2026 | EUR 0 | EUR 0 | — |
| Mar 2026 | EUR 31,020,000 | EUR 0 | — |
| Apr 2026 | EUR 27,020,000 | EUR 31,020,000 | -12.89% |

In Apr 2026, signed contract value decreased by EUR 4,000,000 versus Mar 2026, a 12.89% decrease.

**Execution time:** 66.555 sec
**Status:** ok

## 13. RAQ-015

**Question**

What is the payment breakdown by status?

**Generated SQL**

```sql
SELECT
  CAST(p.status AS text) AS payment_status,
  p.currency,
  COUNT(*) AS payment_count,
  SUM(p.amount) AS total_amount,
  SUM(COUNT(*)) OVER() AS total_matching_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
GROUP BY CAST(p.status AS text), p.currency
ORDER BY payment_count DESC, payment_status ASC, p.currency ASC;
```

**Generated final answer**

Total matching payments: 212

Here is the breakdown by status (all amounts in EUR):

| Payment status | Payment count | Total amount (EUR) | % of total |
|---|---:|---:|---:|
| Paid | 158 | 56,425,000 | 74.53% |
| Pending | 30 | 10,925,000 | 14.15% |
| Lost | 15 | 4,900,100 | 7.08% |
| Draft | 4 | 400,000 | 1.89% |
| Failed | 4 | 905,000 | 1.89% |
| Refunded | 1 | 350,000 | 0.47% |

**Execution time:** 26.927 sec
**Status:** ok

## 14. RAQ-016

**Question**

What is the payment amount breakdown by payment type?

**Generated SQL**

```sql
SELECT
  CAST(p.type AS text) AS payment_type,
  p.currency,
  COUNT(*) AS payment_count,
  SUM(p.amount) AS total_amount,
  SUM(COUNT(*)) OVER() AS total_matching_payments,
  ROUND(
    SUM(p.amount) * 100.0 / NULLIF(SUM(SUM(p.amount)) OVER (PARTITION BY p.currency), 0),
    2
  ) AS percentage_of_currency_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
GROUP BY CAST(p.type AS text), p.currency
ORDER BY total_amount DESC, payment_type ASC, p.currency ASC;
```

**Generated final answer**

Total matching payments: 212

All matching payments are in EUR; here is the breakdown by payment type.

| Payment Type | Payment Count | Amount (EUR) | % of total amount |
|---|---:|---:|---:|
| First Payment | 160 | 62,385,100.00 | 84.41% |
| Deposit | 45 | 10,820,000.00 | 14.64% |
| Instalment | 7 | 700,000.00 | 0.95% |

**Execution time:** 34.400 sec
**Status:** ok

## 15. RAQ-018

**Question**

How many payments do we have by currency?

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(CAST(p.currency AS text)), ''), 'Unknown') AS currency,
  COUNT(*) AS payment_count,
  SUM(COUNT(*)) OVER() AS total_matching_payments,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
GROUP BY COALESCE(NULLIF(TRIM(CAST(p.currency AS text)), ''), 'Unknown')
ORDER BY payment_count DESC, currency ASC;
```

**Generated final answer**

Total matching payments: 212

All 212 payments are in EUR (100.00%).

**Execution time:** 17.606 sec
**Status:** ok

## 16. RAQ-017

**Question**

What is the payment provider breakdown by paid payment volume?

**Generated SQL**

```sql
SELECT
  COALESCE(CAST(p.payment_provider AS text), 'UNKNOWN') AS payment_provider,
  COUNT(*) AS paid_payment_count,
  SUM(COUNT(*)) OVER () AS total_paid_payments,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0),
    2
  ) AS percentage_of_total_paid_payments
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
GROUP BY COALESCE(CAST(p.payment_provider AS text), 'UNKNOWN')
ORDER BY paid_payment_count DESC, payment_provider ASC;
```

**Generated final answer**

Total paid payments: 158

Here is the breakdown by payment provider:

| Payment provider | Paid payments | % of total |
|---|---:|---:|
| Whop | 109 | 68.99% |
| Manual | 49 | 31.01% |

**Execution time:** 23.648 sec
**Status:** ok

## 17. RAQ-020

**Question**

Show payment provider breakdown for paid payments collected from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  CAST(p.payment_provider AS text) AS payment_provider,
  p.currency,
  COUNT(*) AS paid_payment_count,
  SUM(p.amount) AS gross_paid_amount,
  SUM(COUNT(*)) OVER() AS total_paid_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_paid_payments
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
  AND p.paid_at >= :start_date
  AND p.paid_at < :end_date
GROUP BY CAST(p.payment_provider AS text), p.currency
ORDER BY gross_paid_amount DESC, payment_provider ASC, p.currency ASC;
```

**Generated final answer**

Total matching paid payments: 65

Here is the payment provider breakdown for paid payments collected from 2026-04-01 to 2026-05-01:

| Payment provider | Currency | Paid payments | Gross paid amount | % of paid payments |
|---|---|---:|---:|---:|
| Whop | EUR | 51 | 20,270,000.00 | 78.46% |
| Manual | EUR | 14 | 6,230,000.00 | 21.54% |

**Execution time:** 24.571 sec
**Status:** ok

## 18. RAQ-013

**Question**

Show revenue collected by payment provider month by month from 2026-02-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS payment_month
), provider_currency_pairs AS (
  SELECT DISTINCT
    CAST(p.payment_provider AS text) AS payment_provider,
    p.currency
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date

  UNION

  SELECT DISTINCT
    CAST(p.payment_provider AS text) AS payment_provider,
    r.currency
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
), month_provider_currency_grid AS (
  SELECT
    m.payment_month,
    pcp.payment_provider,
    pcp.currency
  FROM months m
  CROSS JOIN provider_currency_pairs pcp
), paid_monthly AS (
  SELECT
    DATE_TRUNC('month', p.paid_at)::date AS payment_month,
    CAST(p.payment_provider AS text) AS payment_provider,
    p.currency,
    COUNT(*) AS paid_payment_count,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY DATE_TRUNC('month', p.paid_at)::date, CAST(p.payment_provider AS text), p.currency
), refunded_monthly AS (
  SELECT
    DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date AS payment_month,
    CAST(p.payment_provider AS text) AS payment_provider,
    r.currency,
    COUNT(*) AS succeeded_refund_count,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date, CAST(p.payment_provider AS text), r.currency
), monthly_net AS (
  SELECT
    g.payment_month,
    g.payment_provider,
    g.currency,
    COALESCE(pm.paid_payment_count, 0) AS paid_payment_count,
    COALESCE(pm.gross_paid_amount, 0) AS gross_paid_amount,
    COALESCE(rm.succeeded_refund_count, 0) AS succeeded_refund_count,
    COALESCE(rm.refunded_amount, 0) AS refunded_amount,
    COALESCE(pm.gross_paid_amount, 0) - COALESCE(rm.refunded_amount, 0) AS net_collected_revenue
  FROM month_provider_currency_grid g
  LEFT JOIN paid_monthly pm
    ON pm.payment_month = g.payment_month
   AND pm.payment_provider = g.payment_provider
   AND pm.currency = g.currency
  LEFT JOIN refunded_monthly rm
    ON rm.payment_month = g.payment_month
   AND rm.payment_provider = g.payment_provider
   AND rm.currency = g.currency
), monthly_with_previous AS (
  SELECT
    payment_month,
    payment_provider,
    currency,
    paid_payment_count,
    gross_paid_amount,
    succeeded_refund_count,
    refunded_amount,
    net_collected_revenue,
    LAG(net_collected_revenue) OVER (
      PARTITION BY payment_provider, currency
      ORDER BY payment_month ASC
    ) AS previous_period_net_collected_revenue
  FROM monthly_net
)
SELECT
  payment_month,
  payment_provider,
  currency,
  paid_payment_count,
  gross_paid_amount,
  succeeded_refund_count,
  refunded_amount,
  net_collected_revenue,
  previous_period_net_collected_revenue,
  CASE
    WHEN previous_period_net_collected_revenue IS NULL OR previous_period_net_collected_revenue = 0 THEN NULL
    ELSE ROUND(
      ((net_collected_revenue - previous_period_net_collected_revenue)::numeric / previous_period_net_collected_revenue) * 100,
      2
    )
  END AS percentage_change_from_previous_period,
  SUM(net_collected_revenue) OVER (PARTITION BY currency) AS total_net_collected_revenue_for_currency
FROM monthly_with_previous
ORDER BY payment_month ASC, currency ASC, net_collected_revenue DESC, payment_provider ASC
```

**Generated final answer**

Total collected revenue (net of succeeded refunds): EUR 56,075,000

Here is the EUR month-by-month breakdown by payment provider from Feb 2026 through Apr 2026:

| Payment provider | Feb 2026 | Mar 2026 | Apr 2026 |
|---|---:|---:|---:|
| Whop | 0 | 17,545,000 | 20,270,000 (+15.53%) |
| Manual | 0 | 12,030,000 | 6,230,000 (-48.21%) |

In Apr 2026, Whop increased by EUR 2,725,000 versus Mar 2026 (+15.53%), while Manual decreased by EUR 5,800,000 (-48.21%).

**Execution time:** 82.326 sec
**Status:** ok

## 19. RAQ-019

**Question**

Show payment status breakdown for payments created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  CAST(p.status AS text) AS payment_status,
  p.currency,
  COUNT(*) AS payment_count,
  SUM(p.amount) AS total_amount,
  SUM(COUNT(*)) OVER() AS total_matching_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.created_at >= :start_date
  AND p.created_at < :end_date
GROUP BY CAST(p.status AS text), p.currency
ORDER BY payment_count DESC, payment_status ASC, p.currency ASC;
```

**Generated final answer**

Total matching payments: 90

Paid payments dominated the period, accounting for 71.11% of all payments created.

| Payment status | Currency | Payment count | Total amount | % of total |
|---|---|---:|---:|---:|
| Paid | EUR | 64 | 25,730,000 | 71.11% |
| Pending | EUR | 14 | 6,230,000 | 15.56% |
| Lost | EUR | 10 | 3,480,000 | 11.11% |
| Draft | EUR | 2 | 150,000 | 2.22% |

**Execution time:** 33.869 sec
**Status:** ok

## 20. RAQ-014

**Question**

Show net revenue by program month by month from 2026-02-01 to 2026-05-01.

**Generated SQL**

```sql
WITH months AS (
  SELECT generate_series(
    DATE_TRUNC('month', CAST(:start_date AS timestamp))::date,
    DATE_TRUNC('month', (CAST(:end_date AS timestamp) - INTERVAL '1 day'))::date,
    INTERVAL '1 month'
  )::date AS revenue_month
), paid_monthly AS (
  SELECT
    DATE_TRUNC('month', p.paid_at)::date AS revenue_month,
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    p.currency,
    COUNT(*) AS paid_payment_count,
    SUM(p.amount) AS gross_paid_amount
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
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY DATE_TRUNC('month', p.paid_at)::date, COALESCE(pr.name, 'Unknown Program'), p.currency
), refund_monthly AS (
  SELECT
    DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date AS revenue_month,
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    COALESCE(r.currency, p.currency) AS currency,
    COUNT(*) AS succeeded_refund_count,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  LEFT JOIN contracts c
    ON c.id = p.contract_id
   AND c.clerk_org_id = p.clerk_org_id
   AND c.is_deleted = false
  LEFT JOIN programs pr
    ON pr.id = c.program_id
   AND pr.clerk_org_id = c.clerk_org_id
   AND pr.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY DATE_TRUNC('month', COALESCE(r.refunded_at, r.created_at))::date, COALESCE(pr.name, 'Unknown Program'), COALESCE(r.currency, p.currency)
), program_currency_pairs AS (
  SELECT program_name, currency
  FROM paid_monthly
  UNION
  SELECT program_name, currency
  FROM refund_monthly
), monthly_grid AS (
  SELECT
    m.revenue_month,
    pcp.program_name,
    pcp.currency
  FROM months m
  CROSS JOIN program_currency_pairs pcp
), monthly_filled AS (
  SELECT
    mg.revenue_month,
    mg.program_name,
    mg.currency,
    COALESCE(pm.paid_payment_count, 0) AS paid_payment_count,
    COALESCE(pm.gross_paid_amount, 0) AS gross_paid_amount,
    COALESCE(rm.succeeded_refund_count, 0) AS succeeded_refund_count,
    COALESCE(rm.refunded_amount, 0) AS refunded_amount,
    COALESCE(pm.gross_paid_amount, 0) - COALESCE(rm.refunded_amount, 0) AS net_collected_revenue
  FROM monthly_grid mg
  LEFT JOIN paid_monthly pm
    ON pm.revenue_month = mg.revenue_month
   AND pm.program_name = mg.program_name
   AND pm.currency = mg.currency
  LEFT JOIN refund_monthly rm
    ON rm.revenue_month = mg.revenue_month
   AND rm.program_name = mg.program_name
   AND rm.currency = mg.currency
), monthly_with_previous AS (
  SELECT
    revenue_month,
    program_name,
    currency,
    paid_payment_count,
    gross_paid_amount,
    succeeded_refund_count,
    refunded_amount,
    net_collected_revenue,
    LAG(net_collected_revenue) OVER (
      PARTITION BY program_name, currency
      ORDER BY revenue_month ASC
    ) AS previous_month_net_collected_revenue
  FROM monthly_filled
)
SELECT
  revenue_month,
  program_name,
  currency,
  paid_payment_count,
  gross_paid_amount,
  succeeded_refund_count,
  refunded_amount,
  net_collected_revenue,
  previous_month_net_collected_revenue,
  CASE
    WHEN previous_month_net_collected_revenue IS NULL OR previous_month_net_collected_revenue = 0 THEN NULL
    ELSE ROUND(
      ((net_collected_revenue - previous_month_net_collected_revenue)::numeric / previous_month_net_collected_revenue) * 100,
      2
    )
  END AS percentage_change_from_previous_month,
  SUM(net_collected_revenue) OVER (PARTITION BY currency) AS total_net_collected_revenue_for_currency
FROM monthly_with_previous
ORDER BY currency ASC, program_name ASC, revenue_month ASC
```

**Generated final answer**

Total net revenue: EUR 56,075,000

Here is the monthly net revenue by program for Feb to Apr 2026.

| Program | Feb 2026 (EUR) | Mar 2026 (EUR) | Apr 2026 (EUR) |
|---|---:|---:|---:|
| Freedom Academy | 0 | 29,575,000 | 26,500,000 (-10.40%) |

In Apr 2026, Freedom Academy net revenue was 26,500,000 EUR, down from 29,575,000 EUR in Mar 2026 (-10.40%).

**Execution time:** 84.344 sec
**Status:** ok

## 21. RAQ-024

**Question**

How much outstanding payment amount is still due?

**Generated SQL**

```sql
SELECT
  p.currency,
  COUNT(*) AS outstanding_payment_count,
  SUM(p.amount) AS outstanding_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status IN ('PENDING', 'FAILED')
GROUP BY p.currency
ORDER BY outstanding_amount DESC, p.currency ASC;
```

**Generated final answer**

There is EUR 11,830,000.00 still due across 34 outstanding payments.

**Execution time:** 14.224 sec
**Status:** ok

## 22. RAQ-023

**Question**

Which currency has the highest paid payment amount?

**Generated SQL**

```sql
WITH currency_totals AS (
  SELECT
    p.currency,
    COUNT(*) AS paid_payment_count,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
  GROUP BY p.currency
), ranked_currencies AS (
  SELECT
    currency,
    paid_payment_count,
    gross_paid_amount,
    RANK() OVER (ORDER BY gross_paid_amount DESC, currency ASC) AS amount_rank
  FROM currency_totals
)
SELECT
  currency,
  paid_payment_count,
  gross_paid_amount
FROM ranked_currencies
WHERE amount_rank = 1
ORDER BY currency ASC
```

**Generated final answer**

EUR has the highest paid payment amount, with 56,425,000 across 158 paid payments.

**Execution time:** 17.913 sec
**Status:** ok

## 23. RAQ-021

**Question**

Show payment type breakdown for payments due from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  CAST(p.type AS text) AS payment_type,
  p.currency,
  COUNT(*) AS payment_count,
  SUM(p.amount) AS total_amount,
  SUM(COUNT(*)) OVER() AS total_matching_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.due_date >= :start_date
  AND p.due_date < :end_date
GROUP BY CAST(p.type AS text), p.currency
ORDER BY payment_count DESC, payment_type ASC, p.currency ASC;
```

**Generated final answer**

Total matching payments: 85

Here is the breakdown by payment type for payments due from Apr 1, 2026 to May 1, 2026.

| Payment type | Currency | Count | Total amount | % of total payments |
|---|---|---:|---:|---:|
| First Payment | EUR | 60 | 28,330,000.00 | 70.59% |
| Deposit | EUR | 24 | 6,630,000.00 | 28.24% |
| Instalment | EUR | 1 | 125,000.00 | 1.18% |

**Execution time:** 38.473 sec
**Status:** ok

## 24. RAQ-022

**Question**

Which payment provider collected the most gross paid revenue?

**Generated SQL**

```sql
WITH provider_revenue AS (
  SELECT
    CAST(p.payment_provider AS text) AS payment_provider,
    p.currency,
    COUNT(*) AS paid_payment_count,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
  GROUP BY CAST(p.payment_provider AS text), p.currency
), ranked AS (
  SELECT
    payment_provider,
    currency,
    paid_payment_count,
    gross_paid_amount,
    RANK() OVER (
      PARTITION BY currency
      ORDER BY gross_paid_amount DESC
    ) AS revenue_rank
  FROM provider_revenue
)
SELECT
  payment_provider,
  currency,
  paid_payment_count,
  gross_paid_amount
FROM ranked
WHERE revenue_rank = 1
ORDER BY currency ASC, payment_provider ASC;
```

**Generated final answer**

Whop collected the most gross paid revenue: EUR 37,815,000.00 across 109 paid payments.

**Execution time:** 24.878 sec
**Status:** ok

## 25. RAQ-025

**Question**

How much overdue payment amount do we have?

**Generated SQL**

```sql
SELECT
  p.currency,
  COUNT(*) AS overdue_payment_count,
  SUM(p.amount) AS overdue_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status IN ('PENDING', 'FAILED')
  AND p.due_date IS NOT NULL
  AND p.due_date < NOW()
GROUP BY p.currency
ORDER BY overdue_amount DESC, p.currency ASC;
```

**Generated final answer**

The overdue payment amount is EUR 11,830,000.00 across 34 overdue payments.

**Execution time:** 18.070 sec
**Status:** ok

## 26. RAQ-027

**Question**

How much payment amount is due from 2026-05-05 to 2026-06-05?

**Generated SQL**

```sql
SELECT
  p.currency,
  COUNT(*) AS due_payment_count,
  SUM(p.amount) AS due_amount
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status IN ('PENDING', 'FAILED')
  AND p.due_date >= :start_date
  AND p.due_date < :end_date
GROUP BY p.currency
ORDER BY due_amount DESC, p.currency ASC;
```

**Generated final answer**

There are no pending or failed payments due from May 5, 2026 through June 5, 2026.

**Execution time:** 24.059 sec
**Status:** ok

## 27. RAQ-028

**Question**

List payments due from 2026-05-05 to 2026-06-05.

**Generated SQL**

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
  p.amount,
  p.currency,
  p.due_date,
  p.paid_at,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
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
  AND p.due_date >= :start_date
  AND p.due_date < :end_date
ORDER BY p.due_date ASC NULLS LAST, p.created_at ASC, p.id ASC
LIMIT :limit
```

**Generated final answer**

There are no unpaid payments due from 2026-05-05 to 2026-06-05.

**Execution time:** 27.377 sec
**Status:** ok

## 28. RAQ-031

**Question**

How many payments were paid from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS paid_payment_count
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'PAID'
  AND p.paid_at >= :start_date
  AND p.paid_at < :end_date
```

**Generated final answer**

There were 65 paid payments from 2026-04-01 to 2026-05-01.

**Execution time:** 14.239 sec
**Status:** ok

## 29. RAQ-026

**Question**

List overdue payments that need collection follow-up.

**Generated SQL**

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
  p.amount,
  p.currency,
  p.due_date,
  p.paid_at,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
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

**Generated final answer**

Total matching records: 34

Showing the first 20 records:

| Due date | Lead | Amount | Payment status | Payment type | Provider | Contract status | Payment ID |
|---|---|---:|---|---|---|---|---|
| 2026-03-14 | Eem Bonhke Bonhke | 370,000 EUR | Pending | First Payment | Whop | Draft | c21a57c4-906e-4a19-a661-b73090d48abe |
| 2026-03-15 | Giulio Cinelli | 370,000 EUR | Pending | First Payment | Whop | Draft | 44b18e52-86a5-4930-9597-78ac7a17130a |
| 2026-03-15 | Giulio Cinelli | 185,000 EUR | Failed | First Payment | Whop | Draft | 4e36f60f-be16-430e-a1f7-f91c01967846 |
| 2026-03-16 | Giulio Cinelli | 185,000 EUR | Pending | Deposit | Whop | Draft | 4b805f43-bfa6-4963-b0a4-013562dbd3f6 |
| 2026-03-18 | Rivelino Sharbini Sharbini | 370,000 EUR | Pending | First Payment | Whop | Draft | 9cccd943-368d-4487-a1aa-c9c67581e63c |
| 2026-03-19 | Els Van de Catsye Van de Catsye | 370,000 EUR | Failed | First Payment | Whop | Draft | 0085ffd2-56b3-41ec-aabf-ae71df936313 |
| 2026-03-20 | Nicolas Nuyts Nuyts | 200,000 EUR | Failed | First Payment | Whop | Draft | 9c4df985-68c0-453c-852a-3ae6daa6b9f5 |
| 2026-03-20 | Rich evers evers | 370,000 EUR | Pending | First Payment | Whop | Draft | b4daf62a-fb73-4d03-884c-998b02307bcd |
| 2026-03-20 | Frederik Elout | 370,000 EUR | Pending | First Payment | Whop | Draft | ba81257e-6f7e-4c55-825e-cc2a81b446df |
| 2026-03-21 | Nicolas Nuyts Nuyts | 170,000 EUR | Pending | Deposit | Whop | Draft | 39207c17-41ab-4422-b1b7-401ca3f042da |
| 2026-03-23 | Erich Taljaard | 250,000 EUR | Pending | First Payment | Manual | Signed | 67f665e0-5a70-41ed-bee3-21ab2e217463 |
| 2026-03-25 | Ermand Oussoren | 370,000 EUR | Pending | First Payment | Whop | Draft | dd495cbf-e9c3-4616-b632-59b6a3f21a45 |
| 2026-03-26 | Ryan De waard | 150,000 EUR | Failed | First Payment | Whop | Draft | 2c5f180e-5785-4dba-8c16-7dcc2bca12d5 |
| 2026-03-26 | Mehmet e | 350,000 EUR | Pending | First Payment | Whop | Draft | 9c3d502a-65be-4f6d-a73b-4bdcd9564a45 |
| 2026-03-26 | Mehmet e | 150,000 EUR | Pending | First Payment | Whop | Draft | 6666aaf3-cc1b-495e-b08e-c3339108f93a |
| 2026-03-27 | Ryan De waard | 350,000 EUR | Pending | Deposit | Whop | Draft | 3b284ab2-9c27-4488-9b23-19199ec3b78c |
| 2026-03-27 | Mehmet e | 200,000 EUR | Pending | Deposit | Whop | Draft | 8cb98ff5-7682-4a69-8b9a-684709fd2c76 |
| 2026-03-27 | abel | 100,000 EUR | Pending | First Payment | Whop | Draft | b5305887-6bdb-4a92-a779-87fd85b09bf6 |
| 2026-03-28 | Angelique Jaspers | 500,000 EUR | Pending | First Payment | Whop | Draft | ff1596fe-57b1-4d13-b830-5282e2797bda |
| 2026-03-31 | Michael De cock De cock | 220,000 EUR | Pending | Deposit | Whop | Signed | b0e89a9d-417e-441b-947d-559842bcccd6 |

**Execution time:** 67.448 sec
**Status:** ok

## 30. RAQ-029

**Question**

List failed payments for review.

**Generated SQL**

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
  p.amount,
  p.currency,
  p.due_date,
  p.failure_reason,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  CAST(c.status AS text) AS contract_status,
  p.created_at,
  p.updated_at
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
  AND p.status = 'FAILED'
ORDER BY p.due_date ASC NULLS LAST, p.created_at ASC, p.id ASC
LIMIT 50;
```

**Generated final answer**

Total failed payments: 4

Here is the complete list:

| Lead | Amount | Due date | Failure reason | Payment ID |
|---|---:|---|---|---|
| Giulio Cinelli | 185,000 EUR | 15 Mar 2026 | Your bank could not verify your identity through 3D Secure. This typically happens when incorrect verification details (password, SMS code, or biometric) are entered. Please ensure you're entering the correct information your bank sent you. | `4e36f60f-be16-430e-a1f7-f91c01967846` |
| Els Van de Catsye Van de Catsye | 370,000 EUR | 19 Mar 2026 | Your payment was declined. Please try a new card or contact the provider for more information (Ex: Klarna). | `0085ffd2-56b3-41ec-aabf-ae71df936313` |
| Nicolas Nuyts Nuyts | 200,000 EUR | 20 Mar 2026 | Your card was declined. Please use a different card or contact your bank. | `9c4df985-68c0-453c-852a-3ae6daa6b9f5` |
| Ryan De waard | 150,000 EUR | 26 Mar 2026 | Your bank has declined this transaction. Please try a different card or contact your bank. | `2c5f180e-5785-4dba-8c16-7dcc2bca12d5` |

**Execution time:** 77.409 sec
**Status:** ok

## 31. RAQ-034

**Question**

What is the count and amount of draft payments?

**Generated SQL**

```sql
SELECT
  p.currency,
  COUNT(*) AS draft_payment_count,
  SUM(p.amount) AS draft_payment_amount,
  SUM(COUNT(*)) OVER() AS total_matching_draft_payments
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'DRAFT'
GROUP BY p.currency
ORDER BY draft_payment_amount DESC, p.currency ASC;
```

**Generated final answer**

There are 4 draft payments totaling EUR 400,000.00.

**Execution time:** 18.784 sec
**Status:** ok

## 32. RAQ-035

**Question**

What is the count and amount of lost payments?

**Generated SQL**

```sql
SELECT
  p.currency,
  COUNT(*) AS lost_payment_count,
  SUM(p.amount) AS lost_payment_amount,
  SUM(COUNT(*)) OVER() AS total_matching_lost_payments
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND p.status = 'LOST'
GROUP BY p.currency
ORDER BY lost_payment_amount DESC, p.currency ASC;
```

**Generated final answer**

There are 15 lost payments totaling EUR 4,900,100.00.

**Execution time:** 21.307 sec
**Status:** ok

## 33. RAQ-032

**Question**

List paid payments collected from 2026-04-01 to 2026-05-01.

**Generated SQL**

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
  p.amount,
  p.currency,
  p.due_date,
  p.paid_at,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
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
  AND p.status = 'PAID'
  AND p.paid_at >= :start_date
  AND p.paid_at < :end_date
ORDER BY p.paid_at DESC NULLS LAST, p.created_at DESC, p.id ASC
LIMIT 50;
```

**Generated final answer**

Total matching payments: 65

Showing the first 20 payments collected from 2026-04-01 up to 2026-05-01:

| Client | Payment type | Provider | Amount | Currency | Paid at | Contract status |
|---|---|---|---:|---|---|---|
| Jeffrey Nussy | First Payment | Whop | 500,000 | EUR | 24 Apr 2026 09:52 | Draft |
| Tori tori | First Payment | Whop | 500,000 | EUR | 24 Apr 2026 03:57 | Signed |
| Dennis Schouten | Deposit | Whop | 300,000 | EUR | 24 Apr 2026 03:11 | Signed |
| Chris Rouwhof | First Payment | Whop | 500,000 | EUR | 23 Apr 2026 13:04 | Signed |
| Peter Post | First Payment | Whop | 500,000 | EUR | 23 Apr 2026 11:29 | Signed |
| Sjors Marckelbach | First Payment | Whop | 500,000 | EUR | 23 Apr 2026 10:57 | Signed |
| Nagasaki Elena | First Payment | Manual | 480,000 | EUR | 23 Apr 2026 10:39 | Signed |
| Dennis Schouten | Deposit | Whop | 200,000 | EUR | 23 Apr 2026 08:06 | Signed |
| Richard | First Payment | Manual | 480,000 | EUR | 22 Apr 2026 05:30 | Signed |
| Rolf sterk | Deposit | Whop | 500,000 | EUR | 21 Apr 2026 16:47 | Signed |
| Bart | First Payment | Whop | 500,000 | EUR | 21 Apr 2026 15:20 | Signed |
| Jerry Vercammen | First Payment | Whop | 500,000 | EUR | 21 Apr 2026 12:59 | Signed |
| Jan Kraaijeveld | First Payment | Whop | 500,000 | EUR | 21 Apr 2026 07:57 | Signed |
| Nico Siersma | First Payment | Whop | 500,000 | EUR | 20 Apr 2026 08:55 | Signed |
| Marek Macuk | Deposit | Whop | 50,000 | EUR | 19 Apr 2026 10:07 | Signed |
| Marek Macuk | Deposit | Whop | 200,000 | EUR | 18 Apr 2026 22:43 | Signed |
| Jeroen Willemsen | Deposit | Whop | 200,000 | EUR | 18 Apr 2026 17:25 | Signed |
| Paul Jansen | First Payment | Whop | 500,000 | EUR | 18 Apr 2026 15:44 | Signed |
| Sergio D'Alessandro | First Payment | Whop | 500,000 | EUR | 18 Apr 2026 06:24 | Signed |
| Dennis Tullemans | First Payment | Manual | 500,000 | EUR | 17 Apr 2026 22:24 | Signed |

**Execution time:** 94.285 sec
**Status:** ok

## 34. RAQ-030

**Question**

List pending payments that are not paid yet.

**Generated SQL**

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
  p.amount,
  p.currency,
  p.due_date,
  p.paid_at,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
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
  AND p.status = 'PENDING'
ORDER BY p.due_date ASC NULLS LAST, p.created_at ASC, p.id ASC
LIMIT 50
```

**Generated final answer**

Total pending payments: 30

Showing the first 20 records:

| Payment ID | Lead | Type | Provider | Amount | Due date | Program | Contract status |
|---|---|---|---|---:|---|---|---|
| `c21a57c4-906e-4a19-a661-b73090d48abe` | Eem Bonhke Bonhke | First Payment | Whop | 370,000 EUR | 2026-03-14 | Freedom Academy | Draft |
| `44b18e52-86a5-4930-9597-78ac7a17130a` | Giulio Cinelli | First Payment | Whop | 370,000 EUR | 2026-03-15 | Freedom Academy | Draft |
| `4b805f43-bfa6-4963-b0a4-013562dbd3f6` | Giulio Cinelli | Deposit | Whop | 185,000 EUR | 2026-03-16 | Freedom Academy | Draft |
| `9cccd943-368d-4487-a1aa-c9c67581e63c` | Rivelino Sharbini Sharbini | First Payment | Whop | 370,000 EUR | 2026-03-18 | Freedom Academy | Draft |
| `b4daf62a-fb73-4d03-884c-998b02307bcd` | Rich evers evers | First Payment | Whop | 370,000 EUR | 2026-03-20 | Freedom Academy | Draft |
| `ba81257e-6f7e-4c55-825e-cc2a81b446df` | Frederik Elout | First Payment | Whop | 370,000 EUR | 2026-03-20 | Freedom Academy | Draft |
| `39207c17-41ab-4422-b1b7-401ca3f042da` | Nicolas Nuyts Nuyts | Deposit | Whop | 170,000 EUR | 2026-03-21 | Freedom Academy | Draft |
| `67f665e0-5a70-41ed-bee3-21ab2e217463` | Erich Taljaard | First Payment | Manual | 250,000 EUR | 2026-03-23 | Freedom Academy | Signed |
| `dd495cbf-e9c3-4616-b632-59b6a3f21a45` | Ermand Oussoren | First Payment | Whop | 370,000 EUR | 2026-03-25 | Freedom Academy | Draft |
| `9c3d502a-65be-4f6d-a73b-4bdcd9564a45` | Mehmet e | First Payment | Whop | 350,000 EUR | 2026-03-26 | Freedom Academy | Draft |
| `6666aaf3-cc1b-495e-b08e-c3339108f93a` | Mehmet e | First Payment | Whop | 150,000 EUR | 2026-03-26 | Freedom Academy | Draft |
| `3b284ab2-9c27-4488-9b23-19199ec3b78c` | Ryan De waard | Deposit | Whop | 350,000 EUR | 2026-03-27 | Freedom Academy | Draft |
| `8cb98ff5-7682-4a69-8b9a-684709fd2c76` | Mehmet e | Deposit | Whop | 200,000 EUR | 2026-03-27 | Freedom Academy | Draft |
| `b5305887-6bdb-4a92-a779-87fd85b09bf6` | abel | First Payment | Whop | 100,000 EUR | 2026-03-27 | Freedom Academy | Draft |
| `ff1596fe-57b1-4d13-b830-5282e2797bda` | Angelique Jaspers | First Payment | Whop | 500,000 EUR | 2026-03-28 | Freedom Academy | Draft |
| `b0e89a9d-417e-441b-947d-559842bcccd6` | Michael De cock De cock | Deposit | Whop | 220,000 EUR | 2026-03-31 | Freedom Academy | Signed |
| `c055c0d1-b621-4ce6-9291-5d27c11732fd` | abel | First Payment | Whop | 200,000 EUR | 2026-04-01 | Freedom Academy | Signed |
| `9eee3df9-1eef-4852-ae24-f3fdaa8c3747` | Vedran | First Payment | Whop | 500,000 EUR | 2026-04-03 | Freedom Academy | Draft |
| `e73c6705-7806-46cb-8bd6-8acf112cc64d` | Rivelino Sharbini Sharbini | First Payment | Whop | 500,000 EUR | 2026-04-03 | Freedom Academy | Draft |
| `72b566f6-3be5-467c-bd2b-8cdf30340698` | wesley emo | First Payment | Whop | 500,000 EUR | 2026-04-14 | Freedom Academy | Draft |

**Execution time:** 111.818 sec
**Status:** ok

## 35. RAQ-037

**Question**

What is the contract breakdown by status?

**Generated SQL**

```sql
SELECT
  CAST(c.status AS text) AS contract_status,
  COUNT(*) AS contract_count,
  SUM(COUNT(*)) OVER() AS total_matching_contracts,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
GROUP BY CAST(c.status AS text)
ORDER BY contract_count DESC, contract_status ASC;
```

**Generated final answer**

Total matching contracts: 181

Signed contracts make up most of your contracts.

| Contract status | Count | % of total |
|---|---:|---:|
| Signed | 136 | 75.14% |
| Draft | 29 | 16.02% |
| Voided | 14 | 7.73% |
| Sent | 2 | 1.10% |

**Execution time:** 22.810 sec
**Status:** ok

## 36. RAQ-036

**Question**

What is the count and amount of refunded payments?

**Generated SQL**

```sql
WITH refunded_payments AS (
  SELECT
    r.payment_id,
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.payment_id, r.currency
)
SELECT
  rp.currency,
  COUNT(*) AS refunded_payment_count,
  SUM(rp.refunded_amount) AS refunded_payment_amount,
  SUM(COUNT(*)) OVER() AS total_matching_refunded_payments
FROM refunded_payments rp
GROUP BY rp.currency
ORDER BY refunded_payment_amount DESC, rp.currency ASC;
```

**Generated final answer**

There is 1 refunded payment totaling EUR 350,000.00.

**Execution time:** 48.841 sec
**Status:** ok

## 37. RAQ-033

**Question**

Which unpaid payments have the oldest due dates?

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  p.id AS payment_id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  CAST(p.type AS text) AS payment_type,
  CAST(p.status AS text) AS payment_status,
  p.amount,
  p.currency,
  p.due_date
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
ORDER BY p.due_date ASC, p.created_at ASC, p.id ASC
LIMIT 50
```

**Generated final answer**

Total unpaid payments with due dates: 34

Showing the first 20, ordered by oldest due date:

| Due date | Client | Payment type | Status | Payment ID |
|---|---|---|---|---|
| 2026-03-14 | Eem Bonhke Bonhke | First Payment | Pending | `c21a57c4-906e-4a19-a661-b73090d48abe` |
| 2026-03-15 | Giulio Cinelli | First Payment | Pending | `44b18e52-86a5-4930-9597-78ac7a17130a` |
| 2026-03-15 | Giulio Cinelli | First Payment | Failed | `4e36f60f-be16-430e-a1f7-f91c01967846` |
| 2026-03-16 | Giulio Cinelli | Deposit | Pending | `4b805f43-bfa6-4963-b0a4-013562dbd3f6` |
| 2026-03-18 | Rivelino Sharbini Sharbini | First Payment | Pending | `9cccd943-368d-4487-a1aa-c9c67581e63c` |
| 2026-03-19 | Els Van de Catsye Van de Catsye | First Payment | Failed | `0085ffd2-56b3-41ec-aabf-ae71df936313` |
| 2026-03-20 | Nicolas Nuyts Nuyts | First Payment | Failed | `9c4df985-68c0-453c-852a-3ae6daa6b9f5` |
| 2026-03-20 | Rich evers evers | First Payment | Pending | `b4daf62a-fb73-4d03-884c-998b02307bcd` |
| 2026-03-20 | Frederik Elout | First Payment | Pending | `ba81257e-6f7e-4c55-825e-cc2a81b446df` |
| 2026-03-21 | Nicolas Nuyts Nuyts | Deposit | Pending | `39207c17-41ab-4422-b1b7-401ca3f042da` |
| 2026-03-23 | Erich Taljaard | First Payment | Pending | `67f665e0-5a70-41ed-bee3-21ab2e217463` |
| 2026-03-25 | Ermand Oussoren | First Payment | Pending | `dd495cbf-e9c3-4616-b632-59b6a3f21a45` |
| 2026-03-26 | Ryan De waard | First Payment | Failed | `2c5f180e-5785-4dba-8c16-7dcc2bca12d5` |
| 2026-03-26 | Mehmet e | First Payment | Pending | `9c3d502a-65be-4f6d-a73b-4bdcd9564a45` |
| 2026-03-26 | Mehmet e | First Payment | Pending | `6666aaf3-cc1b-495e-b08e-c3339108f93a` |
| 2026-03-27 | Ryan De waard | Deposit | Pending | `3b284ab2-9c27-4488-9b23-19199ec3b78c` |
| 2026-03-27 | Mehmet e | Deposit | Pending | `8cb98ff5-7682-4a69-8b9a-684709fd2c76` |
| 2026-03-27 | abel | First Payment | Pending | `b5305887-6bdb-4a92-a779-87fd85b09bf6` |
| 2026-03-28 | Angelique Jaspers | First Payment | Pending | `ff1596fe-57b1-4d13-b830-5282e2797bda` |
| 2026-03-31 | Michael De cock De cock | Deposit | Pending | `b0e89a9d-417e-441b-947d-559842bcccd6` |

**Execution time:** 98.593 sec
**Status:** ok

## 38. RAQ-039

**Question**

How many contracts are signed, sent, viewed, withdrawn, draft, or voided?

**Generated SQL**

```sql
WITH requested_statuses AS (
  SELECT
    rs.contract_status,
    rs.sort_order
  FROM (VALUES
    ('SIGNED'::text, 1),
    ('SENT'::text, 2),
    ('VIEWED'::text, 3),
    ('WITHDRAWN'::text, 4),
    ('DRAFT'::text, 5),
    ('VOIDED'::text, 6)
  ) AS rs(contract_status, sort_order)
), status_counts AS (
  SELECT
    CAST(c.status AS text) AS contract_status,
    COUNT(*) AS contract_count
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status IN ('SIGNED', 'SENT', 'VIEWED', 'WITHDRAWN', 'DRAFT', 'VOIDED')
  GROUP BY CAST(c.status AS text)
)
SELECT
  rs.contract_status,
  COALESCE(sc.contract_count, 0) AS contract_count,
  SUM(COALESCE(sc.contract_count, 0)) OVER() AS total_matching_contracts,
  ROUND(
    COALESCE(sc.contract_count, 0) * 100.0
    / NULLIF(SUM(COALESCE(sc.contract_count, 0)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM requested_statuses rs
LEFT JOIN status_counts sc
  ON sc.contract_status = rs.contract_status
ORDER BY rs.sort_order ASC;
```

**Generated final answer**

Total matching contracts: 181

Most contracts are signed.

| Contract status | Count | % of total |
|---|---:|---:|
| Signed | 136 | 75.14% |
| Sent | 2 | 1.10% |
| Viewed | 0 | 0.00% |
| Withdrawn | 0 | 0.00% |
| Draft | 29 | 16.02% |
| Voided | 14 | 7.73% |

**Execution time:** 30.387 sec
**Status:** ok

## 39. RAQ-038

**Question**

What is the contract status breakdown for contracts created from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  CAST(c.status AS text) AS contract_status,
  COUNT(*) AS contract_count,
  SUM(COUNT(*)) OVER() AS total_matching_contracts,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.created_at >= :start_date
  AND c.created_at < :end_date
GROUP BY CAST(c.status AS text)
ORDER BY contract_count DESC, contract_status ASC;
```

**Generated final answer**

Total matching contracts: 74

Here is the status breakdown for contracts created from 2026-04-01 to 2026-05-01:

| Contract status | Count | % of total |
|---|---:|---:|
| Signed | 55 | 74.32% |
| Draft | 10 | 13.51% |
| Voided | 7 | 9.46% |
| Sent | 2 | 2.70% |

**Execution time:** 34.088 sec
**Status:** ok

## 40. RAQ-043

**Question**

How many contracts were sent from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS contracts_sent_in_period
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.sent_at >= :start_date
  AND c.sent_at < :end_date
```

**Generated final answer**

There were 63 contracts sent from 2026-04-01 to 2026-05-01.

**Execution time:** 14.143 sec
**Status:** ok

## 41. RAQ-041

**Question**

List sent or viewed contracts that are not signed yet.

**Generated SQL**

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
  c.total_value,
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
LIMIT 50
```

**Generated final answer**

Total matching contracts: 2

Here is the complete list:

| Contract ID | Client | Program | Type | Status | Contract value | Sent at |
|---|---|---|---|---|---:|---|
| 1391aa50-da41-41f0-911d-51a9c98bbc00 | Chanida | Freedom Academy | Paid in Full | Sent | 500,000 EUR | 2026-04-22 07:23 UTC |
| 5a81812c-69ec-4986-9aea-71dfa76fa473 | Robert Eduard | Freedom Academy | Paid in Full | Sent | 480,000 EUR | 2026-04-24 09:28 UTC |

**Execution time:** 34.602 sec
**Status:** ok

## 42. RAQ-044

**Question**

How many contracts were signed from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS signed_contract_count
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.signed_at >= :start_date
  AND c.signed_at < :end_date;
```

**Generated final answer**

There were 55 contracts signed from 2026-04-01 to 2026-05-01.

**Execution time:** 12.472 sec
**Status:** ok

## 43. RAQ-042

**Question**

List voided contracts with their value and voided date.

**Generated SQL**

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
  c.total_value AS contract_value,
  c.currency,
  c.voided_at::date AS voided_date
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
  AND c.status = 'VOIDED'
ORDER BY c.voided_at DESC NULLS LAST, c.created_at DESC, c.id ASC
LIMIT 50;
```

**Generated final answer**

Total matching records: 14

Here is the complete list:

| Contract ID | Client | Value | Voided date |
|---|---|---:|---|
| 2fba8d37-b0e2-4afa-8eec-41bd9dd885a0 | Chanida | EUR 500,000.00 | 2026-04-22 |
| 901d553e-f0ff-46f6-8c81-15eca9f288fb | Catharina | EUR 500,000.00 | 2026-04-17 |
| ff28dbe1-87ad-46ad-852a-28967f805523 | Mwata Belgrave | EUR 480,000.00 | 2026-04-08 |
| 0086731b-169c-4799-8be2-62bc8d371d20 | abel | EUR 500,000.00 | 2026-04-08 |
| 9d7d1d6c-7496-44b6-91d8-53e3b16a9d28 | Atal | EUR 500,000.00 | 2026-04-06 |
| 709fb4aa-9fc6-41e9-b38e-ac4983740ed1 | Rutger Vogelezang | EUR 500,000.00 | 2026-04-02 |
| 67a2fa97-694f-4333-bcb2-968547dfc923 | Rutger Vogelezang | EUR 500,000.00 | 2026-04-02 |
| 0fcd418d-c483-4f56-b37f-adea9ab66462 | ken tomita | EUR 350,000.00 | 2026-04-01 |
| 7e383246-2362-4c6b-b620-69491e221b7e | test test | EUR 100.00 | 2026-03-30 |
| 57c35d14-066a-42ee-b965-8c9e23f09c97 | Ali | EUR 350,000.00 | 2026-03-29 |
| 306536ae-a627-40a1-9b05-ed0c4b56b926 | Nout besteman | EUR 370,000.00 | 2026-03-26 |
| c33c7b4d-c27e-428b-8542-756e630f5f40 | Andrej Radisa | EUR 370,000.00 | 2026-03-25 |
| 39a24a93-984f-42a3-b7ed-7eef8ff996a8 | Ali | EUR 350,000.00 | 2026-03-20 |
| 309bef32-4a78-45a5-91a4-dd78cd7b6b99 | Richard Roos | EUR 350,000.00 | 2026-03-20 |

**Execution time:** 43.923 sec
**Status:** ok

## 44. RAQ-045

**Question**

How many contracts were voided from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS voided_contract_count
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'VOIDED'
  AND c.voided_at >= :start_date
  AND c.voided_at < :end_date
```

**Generated final answer**

There were 8 contracts voided between 2026-04-01 and 2026-05-01.

**Execution time:** 16.686 sec
**Status:** ok

## 45. RAQ-046

**Question**

What is the total signed contract value by currency?

**Generated SQL**

```sql
SELECT
  c.currency,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) AS signed_contract_value,
  SUM(COUNT(*)) OVER() AS total_matching_signed_contracts
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
GROUP BY c.currency
ORDER BY signed_contract_value DESC, c.currency ASC;
```

**Generated final answer**

There are 136 signed contracts, all in EUR, with a total signed contract value of 58,040,000.

**Execution time:** 20.685 sec
**Status:** ok

## 46. RAQ-047

**Question**

What is the signed contract value from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  c.currency,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) AS signed_contract_value
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
  AND c.signed_at >= :start_date
  AND c.signed_at < :end_date
GROUP BY c.currency
ORDER BY signed_contract_value DESC, c.currency ASC;
```

**Generated final answer**

The signed contract value from Apr 1, 2026 to May 1, 2026 was €27,020,000 across 55 signed contracts.

**Execution time:** 22.694 sec
**Status:** ok

## 47. RAQ-048

**Question**

What is the contract signed rate?

**Generated SQL**

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

**Generated final answer**

Out of 181 contracts, 136 were signed. The contract signed rate is 75.14%.

**Execution time:** 10.374 sec
**Status:** ok

## 48. RAQ-049

**Question**

What is the sent-to-signed contract rate?

**Generated SQL**

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

**Generated final answer**

Out of 152 sent-or-later contracts, 136 were signed, for a sent-to-signed contract rate of 89.47%.

**Execution time:** 13.818 sec
**Status:** ok

## 49. RAQ-040

**Question**

List signed contracts.

**Generated SQL**

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
  c.total_value,
  c.currency,
  COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer') AS closer_id,
  COALESCE(NULLIF(TRIM(c.setter_id), ''), 'No Setter') AS setter_id,
  c.sent_at,
  c.signed_at,
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
LIMIT :limit;
```

**Generated final answer**

Total signed contracts: 136

Showing the first 20 most recently signed contracts:

| Contract ID | Client | Program | Type | Value | Signed at |
|---|---|---|---|---:|---|
| 43a10040-e5d6-4111-b5cc-c12e74a8c073 | Tori tori | Freedom Academy | Paid in Full | 500,000 EUR | 24 Apr 2026 05:35 |
| 7cc89abb-58a1-4d59-b2d3-9c0cb00a9eb1 | Raymond Keppel | Freedom Academy | Paid in Full | 500,000 EUR | 23 Apr 2026 18:59 |
| 8040e78e-b8c1-423d-9de3-948ed426371e | Chris Rouwhof | Freedom Academy | Paid in Full | 500,000 EUR | 23 Apr 2026 13:04 |
| 91a320d7-08bb-4997-9b29-63ad6a0fa96c | Peter Post | Freedom Academy | Paid in Full | 500,000 EUR | 23 Apr 2026 11:20 |
| 9f8a23ba-fc86-4c49-be5a-599d9c1b853e | Sjors Marckelbach | Freedom Academy | Paid in Full | 500,000 EUR | 23 Apr 2026 10:54 |
| b5324a28-f837-4e88-b288-4d5b476d2b0f | Nagasaki Elena | Freedom Academy | Paid in Full | 480,000 EUR | 23 Apr 2026 10:39 |
| 5894cbcf-ed14-4935-9d16-fbea0af669ba | Dennis Schouten | Freedom Academy | Paid in Full | 500,000 EUR | 23 Apr 2026 08:07 |
| ff3a67fb-f7f8-4ba7-9525-cffa88b00066 | Richard | Freedom Academy | Paid in Full | 480,000 EUR | 22 Apr 2026 05:30 |
| 65fd1d3c-e497-4aa2-a15d-7de0dbaf5e57 | Bart | Freedom Academy | Paid in Full | 500,000 EUR | 21 Apr 2026 15:20 |
| e7b19342-0b86-435c-9970-417839b01716 | Jerry Vercammen | Freedom Academy | Paid in Full | 500,000 EUR | 21 Apr 2026 12:59 |
| 8b216c79-7be4-4e4a-b37e-ae46fd046159 | Jan Kraaijeveld | Freedom Academy | Paid in Full | 500,000 EUR | 21 Apr 2026 07:59 |
| 30784702-be45-4416-b6b9-1465979fd7db | Nico Siersma | Freedom Academy | Paid in Full | 500,000 EUR | 20 Apr 2026 08:56 |
| 46de7033-740d-4a27-8ee4-f3a599b7f77f | Paul Jansen | Freedom Academy | Paid in Full | 500,000 EUR | 18 Apr 2026 16:35 |
| 6a390c8c-48d9-435e-8e49-7572e9a784df | Marek Macuk | Freedom Academy | Paid in Full | 500,000 EUR | 18 Apr 2026 14:25 |
| 00806b09-4afb-4cda-8469-993ebd04d724 | Sergio D'Alessandro | Freedom Academy | Paid in Full | 500,000 EUR | 18 Apr 2026 06:26 |
| d9d97efc-a515-481b-a8c6-201f59eea7fd | Dennis Tullemans | Freedom Academy | Paid in Full | 500,000 EUR | 17 Apr 2026 22:24 |
| 8280707c-15d4-47e0-8833-e6487168ae8a | Jeroen Willemsen | Freedom Academy | Paid in Full | 500,000 EUR | 17 Apr 2026 16:08 |
| 1b290eb3-ef44-46b8-a46f-4ff13662f642 | Silviu Enache | Freedom Academy | Paid in Full | 500,000 EUR | 17 Apr 2026 14:17 |
| f90af28b-fdec-423d-81f3-cb397f9d1bb2 | Catharina | Freedom Academy | Paid in Full | 500,000 EUR | 17 Apr 2026 11:38 |
| 5c3de970-d45c-4e6d-9064-3ad4e677ade1 | Cor Coomans | Freedom Academy | Paid in Full | 500,000 EUR | 17 Apr 2026 10:53 |

**Execution time:** 88.985 sec
**Status:** ok

## 50. RAQ-051

**Question**

Which contract type has the highest signed contract value?

**Generated SQL**

```sql
WITH contract_type_values AS (
  SELECT
    CAST(c.type AS text) AS contract_type,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
  GROUP BY CAST(c.type AS text), c.currency
), ranked AS (
  SELECT
    contract_type,
    currency,
    signed_contract_count,
    signed_contract_value,
    SUM(signed_contract_value) OVER (PARTITION BY currency) AS total_signed_contract_value_for_currency,
    RANK() OVER (PARTITION BY currency ORDER BY signed_contract_value DESC) AS value_rank
  FROM contract_type_values
)
SELECT
  contract_type,
  currency,
  signed_contract_count,
  signed_contract_value,
  ROUND(
    signed_contract_value * 100.0 / NULLIF(total_signed_contract_value_for_currency, 0),
    2
  ) AS percentage_of_currency_signed_value
FROM ranked
WHERE value_rank = 1
ORDER BY currency ASC, contract_type ASC;
```

**Generated final answer**

Paid in Full (PIF) has the highest signed contract value: EUR 57,690,000 across 135 signed contracts, representing 99.40% of total signed contract value.

**Execution time:** 27.660 sec
**Status:** ok

## 51. RAQ-053

**Question**

Show sent-to-signed rate for contracts sent from 2026-01-01 to 2026-04-01.

**Generated SQL**

```sql
SELECT
  COUNT(*) AS sent_contracts,
  COUNT(*) FILTER (WHERE c.status = 'SIGNED') AS signed_contracts,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE c.status = 'SIGNED') / NULLIF(COUNT(*), 0),
    2
  ) AS sent_to_signed_rate_percent
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status IN ('SENT', 'VIEWED', 'SIGNED', 'WITHDRAWN', 'VOIDED')
  AND c.sent_at >= :start_date
  AND c.sent_at < :end_date
```

**Generated final answer**

Out of 90 contracts sent from 2026-01-01 through 2026-04-01, 84 were signed, for a sent-to-signed rate of 93.33%.

**Execution time:** 37.170 sec
**Status:** ok

## 52. RAQ-052

**Question**

Show signed contract value by currency from 2026-01-01 to 2026-04-01.

**Generated SQL**

```sql
SELECT
  c.currency,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) AS signed_contract_value,
  SUM(COUNT(*)) OVER() AS total_matching_contracts
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
  AND c.signed_at >= :start_date
  AND c.signed_at < :end_date
GROUP BY c.currency
ORDER BY signed_contract_value DESC, c.currency ASC;
```

**Generated final answer**

Total signed contracts: 83

Here is the signed contract value breakdown by currency for 2026-01-01 to 2026-04-01:

| Currency | Signed contracts | Signed contract value |
|---|---:|---:|
| EUR | 83 | 32,000,000.00 |

**Execution time:** 59.456 sec
**Status:** ok

## 53. RAQ-054

**Question**

Which program generated the most net collected revenue?

**Generated SQL**

```sql
WITH payment_revenue AS (
  SELECT
    p.id AS payment_id,
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    p.currency,
    p.amount AS paid_amount
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
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.payment_id, r.currency
), program_net_revenue AS (
  SELECT
    pr.program_name,
    pr.currency,
    COUNT(DISTINCT pr.payment_id) AS paid_payment_count,
    SUM(pr.paid_amount) AS gross_paid_amount,
    SUM(COALESCE(rt.refunded_amount, 0)) AS refunded_amount,
    SUM(pr.paid_amount) - SUM(COALESCE(rt.refunded_amount, 0)) AS net_collected_revenue
  FROM payment_revenue pr
  LEFT JOIN refund_totals rt
    ON rt.payment_id = pr.payment_id
   AND rt.currency = pr.currency
  GROUP BY pr.program_name, pr.currency
), ranked_programs AS (
  SELECT
    program_name,
    currency,
    paid_payment_count,
    gross_paid_amount,
    refunded_amount,
    net_collected_revenue,
    RANK() OVER (PARTITION BY currency ORDER BY net_collected_revenue DESC) AS revenue_rank
  FROM program_net_revenue
)
SELECT
  program_name,
  currency,
  paid_payment_count,
  gross_paid_amount,
  refunded_amount,
  net_collected_revenue
FROM ranked_programs
WHERE revenue_rank = 1
ORDER BY currency ASC, program_name ASC;
```

**Generated final answer**

Freedom Academy generated the most net collected revenue at EUR 56,425,000 from 158 paid payments, with EUR 0 in succeeded refunds.

**Execution time:** 34.841 sec
**Status:** ok

## 54. RAQ-050

**Question**

What is the signed contract value by contract type?

**Generated SQL**

```sql
SELECT
  CASE
    WHEN c.type = 'PIF' THEN 'Paid in Full'
    WHEN c.type = 'PP' THEN 'Payment Plan'
    WHEN c.type = 'SUBSCRIPTION' THEN 'Subscription'
    ELSE 'Unknown'
  END AS contract_type,
  c.currency,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) AS signed_contract_value,
  SUM(COUNT(*)) OVER () AS total_signed_contracts,
  SUM(COUNT(*)) OVER (PARTITION BY c.currency) AS total_signed_contracts_in_currency,
  SUM(SUM(c.total_value)) OVER (PARTITION BY c.currency) AS total_signed_contract_value_in_currency,
  ROUND(
    SUM(c.total_value) * 100.0
    / NULLIF(SUM(SUM(c.total_value)) OVER (PARTITION BY c.currency), 0),
    2
  ) AS percentage_of_currency_signed_contract_value
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
GROUP BY
  CASE
    WHEN c.type = 'PIF' THEN 'Paid in Full'
    WHEN c.type = 'PP' THEN 'Payment Plan'
    WHEN c.type = 'SUBSCRIPTION' THEN 'Subscription'
    ELSE 'Unknown'
  END,
  c.currency
ORDER BY c.currency ASC, signed_contract_value DESC, contract_type ASC;
```

**Generated final answer**

Total signed contracts with value: 136  
Total signed contract value (EUR): 58,040,000

Here is the breakdown by contract type:

| Contract type | Signed contracts | Signed contract value (EUR) | % of EUR total |
|---|---:|---:|---:|
| Paid in Full | 135 | 57,690,000 | 99.40% |
| Payment Plan | 1 | 350,000 | 0.60% |

**Execution time:** 64.079 sec
**Status:** ok

## 55. RAQ-056

**Question**

Show signed contract value by program.

**Generated SQL**

```sql
SELECT
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  c.currency,
  COUNT(*) AS signed_contract_count,
  SUM(c.total_value) AS signed_contract_value,
  SUM(COUNT(*)) OVER() AS total_signed_contracts,
  SUM(SUM(c.total_value)) OVER (PARTITION BY c.currency) AS total_signed_contract_value_for_currency,
  ROUND(
    (SUM(c.total_value)::numeric * 100.0) /
    NULLIF(SUM(SUM(c.total_value)) OVER (PARTITION BY c.currency), 0),
    2
  ) AS percentage_of_signed_contract_value
FROM contracts c
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.total_value IS NOT NULL
GROUP BY COALESCE(pr.name, 'Unknown Program'), c.currency
ORDER BY signed_contract_value DESC, program_name ASC, c.currency ASC;
```

**Generated final answer**

Total signed contracts: 136

All signed contract value is currently under Freedom Academy.

| Program | Currency | Signed contracts | Signed contract value | % of total signed contract value |
|---|---|---:|---:|---:|
| Freedom Academy | EUR | 136 | 58,040,000 | 100.00% |

**Execution time:** 48.671 sec
**Status:** ok

## 56. RAQ-059

**Question**

Which program has the highest paid payment count?

**Generated SQL**

```sql
WITH program_payment_counts AS (
  SELECT
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    COUNT(*) AS paid_payment_count,
    SUM(COUNT(*)) OVER () AS total_paid_payments,
    ROUND(
      COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0),
      2
    ) AS percentage_of_total_paid_payments
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
  GROUP BY COALESCE(pr.name, 'Unknown Program')
), ranked AS (
  SELECT
    program_name,
    paid_payment_count,
    total_paid_payments,
    percentage_of_total_paid_payments,
    RANK() OVER (ORDER BY paid_payment_count DESC) AS payment_count_rank
  FROM program_payment_counts
)
SELECT
  program_name,
  paid_payment_count,
  total_paid_payments,
  percentage_of_total_paid_payments
FROM ranked
WHERE payment_count_rank = 1
ORDER BY program_name ASC;
```

**Generated final answer**

Freedom Academy has the highest paid payment count with 158 paid payments.

**Execution time:** 36.363 sec
**Status:** ok

## 57. RAQ-055

**Question**

Show net collected revenue by program.

**Generated SQL**

```sql
WITH payment_revenue AS (
  SELECT
    p.id AS payment_id,
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    p.currency,
    p.amount AS paid_amount
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
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.payment_id, r.currency
), program_net_revenue AS (
  SELECT
    pr.program_name,
    pr.currency,
    COUNT(DISTINCT pr.payment_id) AS paid_payment_count,
    SUM(pr.paid_amount) AS gross_paid_amount,
    SUM(COALESCE(rt.refunded_amount, 0)) AS refunded_amount,
    SUM(pr.paid_amount) - SUM(COALESCE(rt.refunded_amount, 0)) AS net_collected_revenue
  FROM payment_revenue pr
  LEFT JOIN refund_totals rt
    ON rt.payment_id = pr.payment_id
   AND rt.currency = pr.currency
  GROUP BY pr.program_name, pr.currency
)
SELECT
  program_name,
  currency,
  paid_payment_count,
  gross_paid_amount,
  refunded_amount,
  net_collected_revenue,
  COUNT(*) OVER (PARTITION BY currency) AS total_matching_programs,
  SUM(net_collected_revenue) OVER (PARTITION BY currency) AS total_net_collected_revenue,
  ROUND(
    net_collected_revenue * 100.0
    / NULLIF(SUM(net_collected_revenue) OVER (PARTITION BY currency), 0),
    2
  ) AS percentage_of_currency_net_revenue
FROM program_net_revenue
ORDER BY currency ASC, net_collected_revenue DESC, program_name ASC;
```

**Generated final answer**

Only one program has net collected revenue in the current data, totaling EUR 56,425,000.

| Program | Currency | Paid payments | Gross paid revenue | Refunded | Net collected revenue | % of currency total |
|---|---|---:|---:|---:|---:|---:|
| Freedom Academy | EUR | 158 | 56,425,000 | 0 | 56,425,000 | 100.00% |

**Execution time:** 90.307 sec
**Status:** ok

## 58. RAQ-057

**Question**

Show net collected revenue by program from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH paid_by_program AS (
  SELECT
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    p.currency,
    COUNT(*) AS paid_payment_count,
    SUM(p.amount) AS gross_paid_amount
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
    AND p.paid_at >= :start_date
    AND p.paid_at < :end_date
  GROUP BY COALESCE(pr.name, 'Unknown Program'), p.currency
), refunds_by_program AS (
  SELECT
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  LEFT JOIN contracts c
    ON c.id = p.contract_id
   AND c.clerk_org_id = p.clerk_org_id
   AND c.is_deleted = false
  LEFT JOIN programs pr
    ON pr.id = c.program_id
   AND pr.clerk_org_id = c.clerk_org_id
   AND pr.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND COALESCE(r.refunded_at, r.created_at) >= :start_date
    AND COALESCE(r.refunded_at, r.created_at) < :end_date
  GROUP BY COALESCE(pr.name, 'Unknown Program'), r.currency
), combined AS (
  SELECT
    COALESCE(pp.program_name, rbp.program_name) AS program_name,
    COALESCE(pp.currency, rbp.currency) AS currency,
    COALESCE(pp.paid_payment_count, 0) AS paid_payment_count,
    COALESCE(pp.gross_paid_amount, 0) AS gross_paid_amount,
    COALESCE(rbp.refunded_amount, 0) AS refunded_amount,
    COALESCE(pp.gross_paid_amount, 0) - COALESCE(rbp.refunded_amount, 0) AS net_collected_revenue
  FROM paid_by_program pp
  FULL OUTER JOIN refunds_by_program rbp
    ON rbp.program_name = pp.program_name
   AND rbp.currency = pp.currency
)
SELECT
  program_name,
  currency,
  paid_payment_count,
  gross_paid_amount,
  refunded_amount,
  net_collected_revenue,
  SUM(net_collected_revenue) OVER (PARTITION BY currency) AS total_net_collected_revenue_for_currency,
  CASE
    WHEN SUM(net_collected_revenue) OVER (PARTITION BY currency) = 0 THEN NULL
    ELSE ROUND(net_collected_revenue * 100.0 / SUM(net_collected_revenue) OVER (PARTITION BY currency), 2)
  END AS percentage_of_currency_net_revenue
FROM combined
ORDER BY net_collected_revenue DESC, program_name ASC, currency ASC
```

**Generated final answer**

Total net collected revenue: EUR 26,500,000.00

Here is the breakdown:

| Program | Currency | Paid payments | Gross paid revenue | Refunded amount | Net collected revenue | % of currency total |
|---|---|---:|---:|---:|---:|---:|
| Freedom Academy | EUR | 65 | 26,500,000.00 | 0.00 | 26,500,000.00 | 100.00% |

**Execution time:** 63.380 sec
**Status:** ok

## 59. RAQ-058

**Question**

Show signed contract value by program from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH signed_contracts AS (
  SELECT
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  LEFT JOIN programs pr
    ON pr.id = c.program_id
   AND pr.clerk_org_id = c.clerk_org_id
   AND pr.is_deleted = false
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND c.signed_at >= :start_date
    AND c.signed_at < :end_date
  GROUP BY COALESCE(pr.name, 'Unknown Program'), c.currency
)
SELECT
  program_name,
  currency,
  signed_contract_count,
  signed_contract_value,
  SUM(signed_contract_count) OVER () AS total_signed_contracts,
  SUM(signed_contract_value) OVER (PARTITION BY currency) AS total_signed_contract_value_in_currency,
  ROUND(
    signed_contract_value * 100.0 / NULLIF(SUM(signed_contract_value) OVER (PARTITION BY currency), 0),
    2
  ) AS percentage_of_signed_contract_value_in_currency
FROM signed_contracts
ORDER BY currency ASC, signed_contract_value DESC, program_name ASC;
```

**Generated final answer**

Total signed contracts: 55

Total signed contract value (EUR): 27,020,000.00

Between 2026-04-01 and 2026-05-01, all signed contract value came from Freedom Academy.

| Program | Currency | Signed contracts | Signed contract value | % of EUR total |
|---|---|---:|---:|---:|
| Freedom Academy | EUR | 55 | 27,020,000.00 | 100.00% |

**Execution time:** 64.061 sec
**Status:** ok

## 60. RAQ-060

**Question**

Which program has the highest refunded amount?

**Generated SQL**

```sql
WITH program_refunds AS (
  SELECT
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    r.currency,
    COUNT(*) AS succeeded_refund_count,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  LEFT JOIN contracts c
    ON c.id = p.contract_id
   AND c.clerk_org_id = p.clerk_org_id
   AND c.is_deleted = false
  LEFT JOIN programs pr
    ON pr.id = c.program_id
   AND pr.clerk_org_id = c.clerk_org_id
   AND pr.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY COALESCE(pr.name, 'Unknown Program'), r.currency
), ranked AS (
  SELECT
    program_name,
    currency,
    succeeded_refund_count,
    refunded_amount,
    RANK() OVER (PARTITION BY currency ORDER BY refunded_amount DESC) AS refund_rank
  FROM program_refunds
)
SELECT
  program_name,
  currency,
  succeeded_refund_count,
  refunded_amount
FROM ranked
WHERE refund_rank = 1
ORDER BY currency ASC, program_name ASC
```

**Generated final answer**

Freedom Academy has the highest refunded amount at EUR 350,000.00 from 1 succeeded refund.

**Execution time:** 37.538 sec
**Status:** ok

## 61. RAQ-062

**Question**

Which closer sold the most signed contract value?

**Generated SQL**

```sql
WITH closer_values AS (
  SELECT
    NULLIF(TRIM(c.closer_id), '') AS closer_id,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND NULLIF(TRIM(c.closer_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(c.closer_id), ''), c.currency
), ranked AS (
  SELECT
    closer_id,
    currency,
    signed_contract_count,
    signed_contract_value,
    RANK() OVER (PARTITION BY currency ORDER BY signed_contract_value DESC) AS value_rank
  FROM closer_values
)
SELECT
  closer_id,
  currency,
  signed_contract_count,
  signed_contract_value
FROM ranked
WHERE value_rank = 1
ORDER BY currency ASC, closer_id ASC;
```

**Generated final answer**

The closer with the highest signed contract value is `user_3AZPWYViL4vUfqNXmNLhNcYAwX4`, with 80 signed contracts totaling EUR 35,070,000.

**Execution time:** 28.709 sec
**Status:** ok

## 62. RAQ-061

**Question**

Show program performance with paid payment count, gross paid amount, refunds, and net revenue.

**Generated SQL**

```sql
WITH payment_revenue AS (
  SELECT
    p.id AS payment_id,
    COALESCE(pr.name, 'Unknown Program') AS program_name,
    p.currency,
    p.amount AS paid_amount
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
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.payment_id, r.currency
), program_performance AS (
  SELECT
    payment_revenue.program_name,
    payment_revenue.currency,
    COUNT(DISTINCT payment_revenue.payment_id) AS paid_payment_count,
    SUM(payment_revenue.paid_amount) AS gross_paid_amount,
    SUM(COALESCE(refund_totals.refunded_amount, 0)) AS refunded_amount,
    SUM(payment_revenue.paid_amount) - SUM(COALESCE(refund_totals.refunded_amount, 0)) AS net_collected_revenue
  FROM payment_revenue
  LEFT JOIN refund_totals
    ON refund_totals.payment_id = payment_revenue.payment_id
   AND refund_totals.currency = payment_revenue.currency
  GROUP BY payment_revenue.program_name, payment_revenue.currency
)
SELECT
  program_name,
  currency,
  paid_payment_count,
  gross_paid_amount,
  refunded_amount,
  net_collected_revenue,
  SUM(paid_payment_count) OVER () AS total_matching_paid_payments
FROM program_performance
ORDER BY net_collected_revenue DESC, program_name ASC, currency ASC;
```

**Generated final answer**

Total paid payments included: 158

Here is the program performance:

| Program | Currency | Paid payment count | Gross paid amount | Refunds | Net revenue |
|---|---|---:|---:|---:|---:|
| Freedom Academy | EUR | 158 | 56,425,000.00 | 0.00 | 56,425,000.00 |

**Execution time:** 53.040 sec
**Status:** ok

## 63. RAQ-065

**Question**

Which setter is attached to the highest signed contract value?

**Generated SQL**

```sql
WITH setter_values AS (
  SELECT
    NULLIF(TRIM(c.setter_id), '') AS setter_id,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND NULLIF(TRIM(c.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(c.setter_id), ''), c.currency
), ranked AS (
  SELECT
    setter_id,
    currency,
    signed_contract_count,
    signed_contract_value,
    RANK() OVER (PARTITION BY currency ORDER BY signed_contract_value DESC) AS value_rank
  FROM setter_values
)
SELECT
  setter_id,
  currency,
  signed_contract_count,
  signed_contract_value
FROM ranked
WHERE value_rank = 1
ORDER BY currency ASC, setter_id ASC;
```

**Generated final answer**

The setter with the highest signed contract value is `user_3AesMObeGeZynVoGhloMkfwanES`, with 37 signed contracts totaling EUR 16,890,000.

**Execution time:** 22.929 sec
**Status:** ok

## 64. RAQ-063

**Question**

Show signed contract value by closer.

**Generated SQL**

```sql
WITH closer_values AS (
  SELECT
    COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer') AS closer_id,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
  GROUP BY COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer'), c.currency
)
SELECT
  closer_id,
  currency,
  signed_contract_count,
  signed_contract_value,
  SUM(signed_contract_count) OVER () AS total_signed_contracts,
  SUM(signed_contract_value) OVER (PARTITION BY currency) AS total_signed_contract_value_for_currency,
  ROUND(
    signed_contract_value * 100.0 / NULLIF(SUM(signed_contract_value) OVER (PARTITION BY currency), 0),
    2
  ) AS percentage_of_currency_signed_contract_value
FROM closer_values
ORDER BY currency ASC, signed_contract_value DESC, closer_id ASC;
```

**Generated final answer**

Total signed contracts: 136  
Total signed contract value (EUR): 58,040,000

Here is the breakdown by closer:

| Closer ID | Signed contracts | Signed contract value (EUR) | % of EUR signed value |
|---|---:|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 80 | 35,070,000 | 60.42% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 55 | 22,620,000 | 38.97% |
| user_3BTfkOX7RajuoxhqwX7nMytxEmM | 1 | 350,000 | 0.60% |

**Execution time:** 46.896 sec
**Status:** ok

## 65. RAQ-066

**Question**

Show signed contract count by closer from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer') AS closer_id,
  COUNT(*) AS signed_contract_count,
  SUM(COUNT(*)) OVER() AS total_signed_contracts,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_signed_contracts
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
  AND c.status = 'SIGNED'
  AND c.signed_at >= :start_date
  AND c.signed_at < :end_date
GROUP BY COALESCE(NULLIF(TRIM(c.closer_id), ''), 'No Closer')
ORDER BY signed_contract_count DESC, closer_id ASC;
```

**Generated final answer**

Total signed contracts: 55

Here is the breakdown by closer for 2026-04-01 to 2026-05-01:

| Closer ID | Signed contract count | % of total |
|---|---:|---:|
| user_3AZPWYViL4vUfqNXmNLhNcYAwX4 | 35 | 63.64% |
| user_3ATRxXyN4j8bDHYJKRCEMAerasy | 19 | 34.55% |
| user_3BTfkOX7RajuoxhqwX7nMytxEmM | 1 | 1.82% |

**Execution time:** 26.602 sec
**Status:** ok

## 66. RAQ-068

**Question**

Which closer has the most signed contracts?

**Generated SQL**

```sql
WITH closer_counts AS (
  SELECT
    NULLIF(TRIM(c.closer_id), '') AS closer_id,
    COUNT(*) AS signed_contract_count
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND NULLIF(TRIM(c.closer_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(c.closer_id), '')
), ranked AS (
  SELECT
    closer_id,
    signed_contract_count,
    SUM(signed_contract_count) OVER() AS total_matching_signed_contracts,
    RANK() OVER (ORDER BY signed_contract_count DESC) AS contract_count_rank
  FROM closer_counts
)
SELECT
  closer_id,
  signed_contract_count,
  total_matching_signed_contracts
FROM ranked
WHERE contract_count_rank = 1
ORDER BY closer_id ASC;
```

**Generated final answer**

The closer ID with the most signed contracts is `user_3AZPWYViL4vUfqNXmNLhNcYAwX4`, with 80 signed contracts out of 136 signed contracts that have a closer assigned.

**Execution time:** 25.071 sec
**Status:** ok

## 67. RAQ-064

**Question**

Show signed contract value by setter.

**Generated SQL**

```sql
WITH setter_values AS (
  SELECT
    COALESCE(NULLIF(TRIM(c.setter_id), ''), 'No Setter') AS setter_id,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
  GROUP BY COALESCE(NULLIF(TRIM(c.setter_id), ''), 'No Setter'), c.currency
)
SELECT
  setter_id,
  currency,
  signed_contract_count,
  signed_contract_value,
  SUM(signed_contract_count) OVER() AS total_signed_contracts,
  SUM(signed_contract_value) OVER (PARTITION BY currency) AS total_signed_contract_value_for_currency,
  ROUND(
    signed_contract_value * 100.0 / NULLIF(SUM(signed_contract_value) OVER (PARTITION BY currency), 0),
    2
  ) AS percentage_of_currency_signed_contract_value
FROM setter_values
ORDER BY currency ASC, signed_contract_value DESC, setter_id ASC;
```

**Generated final answer**

Across 136 signed contracts, total signed contract value is EUR 58,040,000.

| Setter | Signed contracts | Signed contract value (EUR) | % of total value |
|---|---:|---:|---:|
| No Setter | 98 | 40,780,000 | 70.26% |
| user_3AesMObeGeZynVoGhloMkfwanES | 37 | 16,890,000 | 29.10% |
| user_3AZfvBICuFGTCNu4QeqiP6xN03Q | 1 | 370,000 | 0.64% |

**Execution time:** 62.084 sec
**Status:** ok

## 68. RAQ-071

**Question**

How much succeeded refund amount do we have?

**Generated SQL**

```sql
SELECT
  r.currency,
  COUNT(*) AS succeeded_refund_count,
  SUM(r.amount) AS succeeded_refund_amount
FROM refunds r
WHERE r.clerk_org_id = :org_id
  AND r.status = 'SUCCEEDED'
GROUP BY r.currency
ORDER BY succeeded_refund_amount DESC, r.currency ASC;
```

**Generated final answer**

The succeeded refund amount is EUR 350,000.00 across 1 succeeded refund.

**Execution time:** 15.724 sec
**Status:** ok

## 69. RAQ-069

**Question**

Which setter has the most signed contracts?

**Generated SQL**

```sql
WITH setter_counts AS (
  SELECT
    NULLIF(TRIM(c.setter_id), '') AS setter_id,
    COUNT(*) AS signed_contract_count
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND NULLIF(TRIM(c.setter_id), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(c.setter_id), '')
), ranked AS (
  SELECT
    setter_id,
    signed_contract_count,
    SUM(signed_contract_count) OVER () AS total_matching_signed_contracts,
    ROUND(
      signed_contract_count * 100.0 / NULLIF(SUM(signed_contract_count) OVER (), 0),
      2
    ) AS percentage_of_total,
    RANK() OVER (ORDER BY signed_contract_count DESC) AS setter_rank
  FROM setter_counts
)
SELECT
  setter_id,
  signed_contract_count,
  percentage_of_total,
  total_matching_signed_contracts
FROM ranked
WHERE setter_rank = 1
ORDER BY setter_id ASC;
```

**Generated final answer**

The setter with the most signed contracts is user_3AesMObeGeZynVoGhloMkfwanES, with 37 signed contracts (97.37% of 38 setter-attributed signed contracts).

**Execution time:** 34.297 sec
**Status:** ok

## 70. RAQ-073

**Question**

How much succeeded refund amount was completed from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  r.currency,
  COUNT(*) AS succeeded_refund_count,
  SUM(r.amount) AS succeeded_refund_amount
FROM refunds r
WHERE r.clerk_org_id = :org_id
  AND r.status = 'SUCCEEDED'
  AND COALESCE(r.refunded_at, r.created_at) >= :start_date
  AND COALESCE(r.refunded_at, r.created_at) < :end_date
GROUP BY r.currency
ORDER BY succeeded_refund_amount DESC, r.currency ASC;
```

**Generated final answer**

There were no succeeded refunds completed from 2026-04-01 to 2026-05-01, so the succeeded refund amount was 0.

**Execution time:** 15.831 sec
**Status:** ok

## 71. RAQ-070

**Question**

What is the refund amount by refund status?

**Generated SQL**

```sql
WITH refund_status_totals AS (
  SELECT
    CAST(r.status AS text) AS refund_status,
    r.currency,
    COUNT(*) AS refund_count,
    SUM(r.amount) AS refund_amount
  FROM refunds r
  WHERE r.clerk_org_id = :org_id
  GROUP BY CAST(r.status AS text), r.currency
)
SELECT
  refund_status,
  currency,
  refund_count,
  refund_amount,
  SUM(refund_count) OVER () AS total_matching_refunds,
  SUM(refund_amount) OVER (PARTITION BY currency) AS total_refund_amount_in_currency,
  ROUND(
    refund_amount * 100.0 / NULLIF(SUM(refund_amount) OVER (PARTITION BY currency), 0),
    2
  ) AS percentage_of_currency_refund_amount
FROM refund_status_totals
ORDER BY refund_amount DESC, refund_status ASC, currency ASC;
```

**Generated final answer**

Total matching refunds: 1

Here is the breakdown:

| Refund status | Currency | Refund count | Refund amount | Share of currency total |
|---|---|---:|---:|---:|
| Succeeded | EUR | 1 | 350,000.00 | 100.00% |

**Execution time:** 38.001 sec
**Status:** ok

## 72. RAQ-072

**Question**

What is the refund rate by currency?

**Generated SQL**

```sql
WITH paid_payments AS (
  SELECT
    p.currency,
    SUM(p.amount) AS gross_paid_amount
  FROM payments p
  WHERE p.clerk_org_id = :org_id
    AND p.is_deleted = false
    AND p.status = 'PAID'
  GROUP BY p.currency
), succeeded_refunds AS (
  SELECT
    r.currency,
    SUM(r.amount) AS refunded_amount
  FROM refunds r
  JOIN payments p
    ON p.id = r.payment_id
   AND p.clerk_org_id = r.clerk_org_id
   AND p.is_deleted = false
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
  GROUP BY r.currency
)
SELECT
  pp.currency,
  pp.gross_paid_amount,
  COALESCE(sr.refunded_amount, 0) AS refunded_amount,
  ROUND(COALESCE(sr.refunded_amount, 0) * 100.0 / NULLIF(pp.gross_paid_amount, 0), 2) AS refund_rate_percent,
  COUNT(*) OVER() AS total_matching_currencies
FROM paid_payments pp
LEFT JOIN succeeded_refunds sr
  ON sr.currency = pp.currency
ORDER BY refund_rate_percent DESC NULLS LAST, pp.currency ASC;
```

**Generated final answer**

Total currencies: 1

For EUR, the refund rate is 0.62%, with EUR 350,000 refunded against EUR 56,425,000 in paid payments.

**Execution time:** 36.515 sec
**Status:** ok

## 73. RAQ-067

**Question**

Show signed contract value by setter from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
WITH setter_values AS (
  SELECT
    COALESCE(NULLIF(TRIM(c.setter_id), ''), 'No Setter') AS setter_id,
    c.currency,
    COUNT(*) AS signed_contract_count,
    SUM(c.total_value) AS signed_contract_value
  FROM contracts c
  WHERE c.clerk_org_id = :org_id
    AND c.is_deleted = false
    AND c.status = 'SIGNED'
    AND c.total_value IS NOT NULL
    AND c.signed_at >= :start_date
    AND c.signed_at < :end_date
  GROUP BY COALESCE(NULLIF(TRIM(c.setter_id), ''), 'No Setter'), c.currency
)
SELECT
  setter_id,
  currency,
  signed_contract_count,
  signed_contract_value,
  SUM(signed_contract_count) OVER () AS total_matching_contracts,
  SUM(signed_contract_value) OVER (PARTITION BY currency) AS total_signed_contract_value_for_currency,
  ROUND(
    signed_contract_value * 100.0
      / NULLIF(SUM(signed_contract_value) OVER (PARTITION BY currency), 0),
    2
  ) AS percentage_of_currency_total_value
FROM setter_values
ORDER BY currency ASC, signed_contract_value DESC, setter_id ASC;
```

**Generated final answer**

Total matching signed contracts: 55

Here is the breakdown of EUR 27,020,000 in signed contract value by setter for 2026-04-01 to 2026-05-01:

| Setter | Signed contracts | Signed contract value | % of total value |
|---|---:|---:|---:|
| No Setter | 35 | EUR 17,250,000 | 63.84% |
| `user_3AesMObeGeZynVoGhloMkfwanES` | 20 | EUR 9,770,000 | 36.16% |

**Execution time:** 75.795 sec
**Status:** ok

## 74. RAQ-074

**Question**

Show refund status breakdown for refunds created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  CAST(r.status AS text) AS refund_status,
  COUNT(*) AS refund_count,
  SUM(COUNT(*)) OVER() AS total_matching_refunds,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM refunds r
WHERE r.clerk_org_id = :org_id
  AND r.created_at >= :start_date
  AND r.created_at < :end_date
GROUP BY CAST(r.status AS text)
ORDER BY refund_count DESC, refund_status ASC;
```

**Generated final answer**

There were no refunds created from 2026-04-01 to 2026-05-01.

**Execution time:** 26.991 sec
**Status:** ok

## 75. RAQ-075

**Question**

List failed refunds.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  r.id,
  r.payment_id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  r.amount AS refund_amount,
  r.currency,
  CAST(r.status AS text) AS refund_status,
  CAST(r.payment_provider AS text) AS payment_provider,
  CAST(p.status AS text) AS payment_status,
  r.reason AS refund_reason,
  r.failure_reason,
  r.created_at
FROM refunds r
LEFT JOIN payments p
  ON p.id = r.payment_id
 AND p.clerk_org_id = r.clerk_org_id
 AND p.is_deleted = false
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
WHERE r.clerk_org_id = :org_id
  AND r.status = 'FAILED'
ORDER BY r.created_at DESC, r.id ASC
LIMIT 50;
```

**Generated final answer**

There are no failed refunds.

**Execution time:** 30.906 sec
**Status:** ok

## 76. RAQ-078

**Question**

What is the invoice breakdown by status?

**Generated SQL**

```sql
SELECT
  CAST(i.status AS text) AS invoice_status,
  i.currency,
  COUNT(*) AS invoice_count,
  SUM(i.amount) AS invoice_amount,
  SUM(COUNT(*)) OVER() AS total_matching_invoices,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM invoices i
WHERE i.clerk_org_id = :org_id
GROUP BY CAST(i.status AS text), i.currency
ORDER BY invoice_count DESC, invoice_status ASC, i.currency ASC;
```

**Generated final answer**

There are no invoices in your data, so there’s no invoice breakdown by status to show.

**Execution time:** 13.854 sec
**Status:** ok

## 77. RAQ-077

**Question**

Which payment provider has the highest succeeded refund amount?

**Generated SQL**

```sql
WITH provider_refunds AS (
  SELECT
    CAST(r.payment_provider AS text) AS payment_provider,
    r.currency,
    COUNT(*) AS succeeded_refund_count,
    SUM(r.amount) AS succeeded_refund_amount
  FROM refunds r
  WHERE r.clerk_org_id = :org_id
    AND r.status = 'SUCCEEDED'
    AND r.payment_provider IS NOT NULL
  GROUP BY CAST(r.payment_provider AS text), r.currency
), ranked AS (
  SELECT
    payment_provider,
    currency,
    succeeded_refund_count,
    succeeded_refund_amount,
    RANK() OVER (
      PARTITION BY currency
      ORDER BY succeeded_refund_amount DESC
    ) AS refund_amount_rank
  FROM provider_refunds
)
SELECT
  payment_provider,
  currency,
  succeeded_refund_count,
  succeeded_refund_amount
FROM ranked
WHERE refund_amount_rank = 1
ORDER BY currency ASC, payment_provider ASC;
```

**Generated final answer**

Manual has the highest succeeded refund amount: EUR 350,000.00 across 1 succeeded refund.

**Execution time:** 25.388 sec
**Status:** ok

## 78. RAQ-079

**Question**

How many invoices were issued from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT COUNT(*) AS invoices_issued
FROM invoices i
WHERE i.clerk_org_id = :org_id
  AND i.issued_at >= :start_date
  AND i.issued_at < :end_date;
```

**Generated final answer**

There were 0 invoices issued from 2026-04-01 to 2026-05-01.

**Execution time:** 18.724 sec
**Status:** ok

## 79. RAQ-076

**Question**

List initiated refunds that are not succeeded yet.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  r.id AS refund_id,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  CAST(r.payment_provider AS text) AS payment_provider,
  r.amount,
  r.currency,
  COALESCE(NULLIF(TRIM(r.reason), ''), 'No reason provided') AS refund_reason,
  r.created_at AS initiated_at
FROM refunds r
LEFT JOIN payments p
  ON p.id = r.payment_id
 AND p.clerk_org_id = r.clerk_org_id
 AND p.is_deleted = false
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
WHERE r.clerk_org_id = :org_id
  AND r.status = 'INITIATED'
ORDER BY r.created_at DESC, r.id ASC
LIMIT 50
```

**Generated final answer**

There are no initiated refunds that have not succeeded yet.

**Execution time:** 39.634 sec
**Status:** ok

## 80. RAQ-081

**Question**

How many payments have invoices attached?

**Generated SQL**

```sql
SELECT
  COUNT(DISTINCT p.id) AS payments_with_invoices
FROM payments p
JOIN invoices i
  ON i.payment_id = p.id
 AND i.clerk_org_id = p.clerk_org_id
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false;
```

**Generated final answer**

There are 0 payments with invoices attached.

**Execution time:** 14.064 sec
**Status:** ok

## 81. RAQ-080

**Question**

How much invoice amount was paid from 2026-04-01 to 2026-05-01?

**Generated SQL**

```sql
SELECT
  i.currency,
  SUM(i.amount) AS paid_invoice_amount
FROM invoices i
WHERE i.clerk_org_id = :org_id
  AND i.status = 'PAID'
  AND i.paid_at >= :start_date
  AND i.paid_at < :end_date
GROUP BY i.currency
ORDER BY paid_invoice_amount DESC, i.currency ASC;
```

**Generated final answer**

No invoice amount was paid from 2026-04-01 to 2026-05-01.

**Execution time:** 15.862 sec
**Status:** ok

## 82. RAQ-082

**Question**

How many payments are missing invoices?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS payments_missing_invoices
FROM payments p
LEFT JOIN invoices i
  ON i.payment_id = p.id
 AND i.clerk_org_id = p.clerk_org_id
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND i.id IS NULL
```

**Generated final answer**

There are 212 payments missing invoices.

**Execution time:** 18.325 sec
**Status:** ok

## 83. RAQ-086

**Question**

How many payments have payment links?

**Generated SQL**

```sql
SELECT
  COUNT(DISTINCT p.id) AS payments_with_payment_links
FROM payments p
JOIN payment_links pl
  ON pl.payment_id = p.id
 AND pl.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false;
```

**Generated final answer**

There are 150 payments with payment links.

**Execution time:** 13.921 sec
**Status:** ok

## 84. RAQ-085

**Question**

What is the payment link breakdown by status?

**Generated SQL**

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

**Generated final answer**

Total matching payment links: 151

Most payment links have already been used.

| Status | Count | % of total |
|---|---:|---:|
| Used | 97 | 64.24% |
| Active | 44 | 29.14% |
| Invalid | 10 | 6.62% |

**Execution time:** 17.815 sec
**Status:** ok

## 85. RAQ-084

**Question**

List refunded invoices.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  i.id,
  COALESCE(NULLIF(TRIM(i.invoice_number), ''), 'No Invoice Number') AS invoice_number,
  COALESCE(
    NULLIF(TRIM(l.full_name), ''),
    NULLIF(TRIM(CONCAT_WS(' ', l.first_name, l.last_name)), ''),
    l.first_name,
    'Unknown Lead'
  ) AS display_name,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  i.amount,
  i.currency,
  i.issued_at,
  i.paid_at,
  i.created_at
FROM invoices i
LEFT JOIN leads l
  ON l.id = i.to_client_id
 AND l.clerk_org_id = i.clerk_org_id
 AND l.is_deleted = false
LEFT JOIN payments p
  ON p.id = i.payment_id
 AND p.clerk_org_id = i.clerk_org_id
 AND p.is_deleted = false
LEFT JOIN contracts c
  ON c.id = i.contract_id
 AND c.clerk_org_id = i.clerk_org_id
 AND c.is_deleted = false
LEFT JOIN programs pr
  ON pr.id = c.program_id
 AND pr.clerk_org_id = c.clerk_org_id
 AND pr.is_deleted = false
WHERE i.clerk_org_id = :org_id
  AND i.status = 'REFUNDED'
ORDER BY COALESCE(i.paid_at, i.issued_at, i.created_at) DESC NULLS LAST, i.id ASC
LIMIT 50;
```

**Generated final answer**

There are no refunded invoices.

**Execution time:** 24.310 sec
**Status:** ok

## 86. RAQ-087

**Question**

How many payments are missing payment links?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS payments_missing_payment_links
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND NOT EXISTS (
    SELECT 1
    FROM payment_links pl
    WHERE pl.payment_id = p.id
      AND pl.is_deleted = false
  )
```

**Generated final answer**

There are 62 payments missing payment links.

**Execution time:** 13.200 sec
**Status:** ok

## 87. RAQ-088

**Question**

How many active payment links do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS active_payment_link_count
FROM payment_links pl
JOIN payments p
  ON p.id = pl.payment_id
 AND p.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND pl.is_deleted = false
  AND pl.status = 'ACTIVE'
```

**Generated final answer**

There are 44 active payment links.

**Execution time:** 11.999 sec
**Status:** ok

## 88. RAQ-089

**Question**

How many used payment links do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS used_payment_links
FROM payment_links pl
JOIN payments p
  ON p.id = pl.payment_id
 AND p.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND pl.is_deleted = false
  AND pl.status = 'USED';
```

**Generated final answer**

There are 97 used payment links.

**Execution time:** 11.452 sec
**Status:** ok

## 89. RAQ-090

**Question**

How many invalid payment links do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS invalid_payment_link_count
FROM payment_links pl
JOIN payments p
  ON p.id = pl.payment_id
 AND p.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND pl.is_deleted = false
  AND pl.status = 'INVALID';
```

**Generated final answer**

There are 10 invalid payment links.

**Execution time:** 11.914 sec
**Status:** ok

## 90. RAQ-091

**Question**

What is the payment proof coverage for payments?

**Generated SQL**

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

**Generated final answer**

Out of 212 payments, 22 have uploaded payment proofs and 190 do not. Payment proof coverage is 10.38%.

**Execution time:** 14.136 sec
**Status:** ok

## 91. RAQ-092

**Question**

How many payments are missing uploaded payment proofs?

**Generated SQL**

```sql
SELECT COUNT(*) AS payments_missing_uploaded_payment_proofs
FROM payments p
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND NOT EXISTS (
    SELECT 1
    FROM payment_proofs pp
    WHERE pp.payment_id = p.id
      AND pp.clerk_org_id = p.clerk_org_id
      AND pp.is_deleted = false
  );
```

**Generated final answer**

There are 190 payments missing uploaded payment proofs.

**Execution time:** 14.410 sec
**Status:** ok

## 92. RAQ-095

**Question**

What is the subscription breakdown by status?

**Generated SQL**

```sql
SELECT
  CAST(cs.status AS text) AS subscription_status,
  COUNT(*) AS subscription_count,
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

**Generated final answer**

There are no subscriptions to break down by status.

**Execution time:** 23.082 sec
**Status:** ok

## 93. RAQ-096

**Question**

What is our current active subscription MRR by currency?

**Generated SQL**

```sql
SELECT
  cs.currency,
  COUNT(*) AS active_subscription_count,
  ROUND(SUM(
    CASE
      WHEN cs.billing_interval = 'WEEKLY' THEN cs.amount_per_cycle * 52.0 / 12.0
      WHEN cs.billing_interval = 'MONTHLY' THEN cs.amount_per_cycle
      WHEN cs.billing_interval = 'YEARLY' THEN cs.amount_per_cycle / 12.0
      ELSE NULL
    END
  ), 2) AS mrr,
  SUM(COUNT(*)) OVER() AS total_active_subscriptions
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
  AND cs.status = 'ACTIVE'
GROUP BY cs.currency
ORDER BY mrr DESC, cs.currency ASC;
```

**Generated final answer**

There are no active subscriptions right now, so there is no current active subscription MRR to report by currency.

**Execution time:** 24.105 sec
**Status:** ok

## 94. RAQ-083

**Question**

List payments that are missing invoices.

**Generated SQL**

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
  p.amount,
  p.currency,
  p.due_date,
  p.paid_at,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
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
  AND NOT EXISTS (
    SELECT 1
    FROM invoices i
    WHERE i.payment_id = p.id
      AND i.clerk_org_id = p.clerk_org_id
  )
ORDER BY p.paid_at DESC NULLS LAST, p.created_at DESC, p.id ASC
LIMIT 50
```

**Generated final answer**

Total matching payments without invoices: 212

Showing the first 20 payments:

| Lead | Payment type | Status | Provider | Amount | Due date | Paid at | Program | Contract status |
|---|---|---|---|---|---|---|---|---|
| Jeffrey Nussy | First Payment | Paid | Whop | 500,000 EUR | 2026-04-24 | 2026-04-24 | Freedom Academy | Draft |
| Tori tori | First Payment | Paid | Whop | 500,000 EUR | 2026-04-23 | 2026-04-24 | Freedom Academy | Signed |
| Dennis Schouten | Deposit | Paid | Whop | 300,000 EUR | 2026-04-23 | 2026-04-24 | Freedom Academy | Signed |
| Chris Rouwhof | First Payment | Paid | Whop | 500,000 EUR | 2026-04-23 | 2026-04-23 | Freedom Academy | Signed |
| Peter Post | First Payment | Paid | Whop | 500,000 EUR | 2026-04-23 | 2026-04-23 | Freedom Academy | Signed |
| Sjors Marckelbach | First Payment | Paid | Whop | 500,000 EUR | 2026-04-23 | 2026-04-23 | Freedom Academy | Signed |
| Nagasaki Elena | First Payment | Paid | Manual | 480,000 EUR | 2026-04-23 | 2026-04-23 | Freedom Academy | Signed |
| Dennis Schouten | Deposit | Paid | Whop | 200,000 EUR | 2026-04-23 | 2026-04-23 | Freedom Academy | Signed |
| Richard | First Payment | Paid | Manual | 480,000 EUR | 2026-04-21 | 2026-04-22 | Freedom Academy | Signed |
| Rolf sterk | Deposit | Paid | Whop | 500,000 EUR | 2026-04-16 | 2026-04-21 | Freedom Academy | Signed |
| Bart | First Payment | Paid | Whop | 500,000 EUR | 2026-04-21 | 2026-04-21 | Freedom Academy | Signed |
| Jerry Vercammen | First Payment | Paid | Whop | 500,000 EUR | 2026-04-21 | 2026-04-21 | Freedom Academy | Signed |
| Jan Kraaijeveld | First Payment | Paid | Whop | 500,000 EUR | 2026-04-21 | 2026-04-21 | Freedom Academy | Signed |
| Nico Siersma | First Payment | Paid | Whop | 500,000 EUR | 2026-04-20 | 2026-04-20 | Freedom Academy | Signed |
| Marek Macuk | Deposit | Paid | Whop | 50,000 EUR | 2026-04-19 | 2026-04-19 | Freedom Academy | Signed |
| Marek Macuk | Deposit | Paid | Whop | 200,000 EUR | 2026-04-19 | 2026-04-18 | Freedom Academy | Signed |
| Jeroen Willemsen | Deposit | Paid | Whop | 200,000 EUR | 2026-04-18 | 2026-04-18 | Freedom Academy | Signed |
| Paul Jansen | First Payment | Paid | Whop | 500,000 EUR | 2026-04-17 | 2026-04-18 | Freedom Academy | Signed |
| Sergio D'Alessandro | First Payment | Paid | Whop | 500,000 EUR | 2026-04-18 | 2026-04-18 | Freedom Academy | Signed |
| Dennis Tullemans | First Payment | Paid | Manual | 500,000 EUR | 2026-04-17 | 2026-04-17 | Freedom Academy | Signed |

**Execution time:** 73.365 sec
**Status:** ok

## 95. RAQ-097

**Question**

How many active subscriptions do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS active_subscription_count
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
  AND cs.status = 'ACTIVE';
```

**Generated final answer**

There are 0 active subscriptions.

**Execution time:** 12.327 sec
**Status:** ok

## 96. RAQ-098

**Question**

How many past-due subscriptions do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS past_due_subscription_count
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
  AND cs.status = 'PAST_DUE';
```

**Generated final answer**

There are 0 past-due subscriptions.

**Execution time:** 11.313 sec
**Status:** ok

## 97. RAQ-099

**Question**

List past-due subscriptions.

**Generated SQL**

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
  cs.amount_per_cycle,
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
LIMIT 50
```

**Generated final answer**

There are no past-due subscriptions.

**Execution time:** 16.983 sec
**Status:** ok

## 98. RAQ-100

**Question**

How many subscriptions have cancellation scheduled?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS cancellation_scheduled_subscription_count
FROM contract_subscriptions cs
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND cs.is_deleted = false
  AND cs.status = 'CANCELLATION_SCHEDULED';
```

**Generated final answer**

There are 0 subscriptions with cancellation scheduled.

**Execution time:** 18.324 sec
**Status:** ok

## 99. RAQ-102

**Question**

Which subscriptions have next billing dates from 2026-05-05 to 2026-06-05?

**Generated SQL**

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
  cs.amount_per_cycle,
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
  AND cs.next_billing_date >= CAST(:start_date AS date)
  AND cs.next_billing_date < (CAST(:end_date AS date) + INTERVAL '1 day')
ORDER BY cs.next_billing_date ASC, cs.id ASC
LIMIT :limit
```

**Generated final answer**

No subscriptions have next billing dates between 2026-05-05 and 2026-06-05.

**Execution time:** 29.894 sec
**Status:** ok

## 100. RAQ-101

**Question**

List subscriptions with cancellation scheduled.

**Generated SQL**

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
  cs.amount_per_cycle,
  CAST(cs.billing_interval AS text) AS billing_interval,
  cs.currency,
  cs.current_period_end,
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
  AND (
    cs.status = 'CANCELLATION_SCHEDULED'
    OR cs.cancel_at_period_end = true
  )
ORDER BY cs.current_period_end ASC NULLS LAST, cs.next_billing_date ASC NULLS LAST, cs.id ASC
LIMIT 50;
```

**Generated final answer**

There are no subscriptions with cancellation scheduled.

**Execution time:** 39.521 sec
**Status:** ok

## 101. RAQ-093

**Question**

List payments that have uploaded payment proofs.

**Generated SQL**

```sql
WITH proof_agg AS (
  SELECT
    pp.payment_id,
    COUNT(*) AS proof_count,
    MAX(pp.created_at) AS latest_proof_uploaded_at
  FROM payment_proofs pp
  WHERE pp.clerk_org_id = :org_id
    AND pp.is_deleted = false
  GROUP BY pp.payment_id
)
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
  p.amount,
  p.currency,
  p.due_date,
  p.paid_at,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
  CAST(c.status AS text) AS contract_status,
  pa.proof_count,
  pa.latest_proof_uploaded_at,
  p.created_at
FROM proof_agg pa
JOIN payments p
  ON p.id = pa.payment_id
 AND p.clerk_org_id = :org_id
 AND p.is_deleted = false
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
ORDER BY pa.latest_proof_uploaded_at DESC, p.created_at DESC, p.id ASC
LIMIT 50
```

**Generated final answer**

Total matching records: 22

Showing the first 20 payments with uploaded payment proofs:

| Payment ID | Client | Amount (EUR) | Payment type | Paid date | Latest proof upload |
|---|---|---:|---|---|---|
| 67f07842-749a-43ed-8cc2-348595a5a1d4 | Richard | 480,000 | First Payment | 2026-04-22 | 2026-04-22 |
| fc5d20f2-fff1-4890-a478-ec837883ac32 | Dennis Tullemans | 500,000 | First Payment | 2026-04-17 | 2026-04-17 |
| 046ae3bf-adc6-49ed-9a01-d6e65897a1ff | Jan Mühleib | 480,000 | First Payment | 2026-04-15 | 2026-04-15 |
| d7dbe4e5-fae1-4977-b6c7-bbf4292b250d | Fokko Kwant | 480,000 | First Payment | 2026-04-14 | 2026-04-14 |
| 6f840b53-d304-4d4f-9ac8-49c1ea24c819 | Georg Seidler | 480,000 | First Payment | 2026-04-10 | 2026-04-10 |
| 0e2caa6e-6ea2-42b4-bda6-1050563b37d6 | Robert Gary Gersteling Gersteling | 480,000 | First Payment | 2026-04-08 | 2026-04-08 |
| e756fec5-af38-41d2-9686-a54895999d86 | Frans Van Eijck Van Eijck | 480,000 | Deposit | 2026-03-31 | 2026-03-31 |
| c7405d84-a873-4ed1-9e79-d2fe91ddb989 | Yuri | 480,000 | First Payment | 2026-03-29 | 2026-03-29 |
| fe53a379-c103-48ae-a3c2-0efb384cec2e | Martje van de Poll | 350,000 | First Payment | 2026-03-25 | 2026-03-25 |
| f4ad702e-4d30-4a35-8942-64c2f310b96e | Nuno Miguel Lorena Birne Caetano | 350,000 | First Payment | 2026-03-25 | 2026-03-25 |
| bccca6ce-af3f-4440-ad17-a25a97960a60 | Bart Loeffen | 350,000 | First Payment | 2026-03-25 | 2026-03-25 |
| 4230d051-f5d4-4c39-937a-743ba9ff6565 | Jeremy Vervoort Vervoort | 350,000 | First Payment | 2026-03-25 | 2026-03-25 |
| a0599508-2f12-4774-957e-0aec66374644 | Nout besteman | 350,000 | First Payment | 2026-03-25 | 2026-03-25 |
| 7343729f-90f4-4715-96a7-1e10bf15fb85 | Edgar | 350,000 | First Payment | 2026-03-24 | 2026-03-24 |
| 7ce547eb-f5a6-4c79-9c6c-867f75a7225d | Sandor Jonas | 350,000 | First Payment | 2026-03-23 | 2026-03-23 |
| eab3e565-f16f-49e8-85c9-3945dfdeaee7 | Erich Taljaard | 100,000 | Deposit | 2026-03-23 | 2026-03-23 |
| 56bacf3d-10bc-409c-873e-e554d2ef20cf | Valentina | 350,000 | First Payment | 2026-03-23 | 2026-03-23 |
| 3d084f58-5b60-43c4-b8ce-a278e76cafb4 | Jamie Van der Haegen Van der Haegen | 350,000 | First Payment | 2026-03-20 | 2026-03-20 |
| e17d9521-5f9b-4098-87ed-d01f9f7cb53d | Hanneke Hoenderdaal Hoenderdaal | 350,000 | First Payment | 2026-03-16 | 2026-03-16 |
| 2b7f881b-a4ba-449e-8eee-212691337e7c | Petro Termond Termond | 350,000 | First Payment | 2026-03-16 | 2026-03-16 |

**Execution time:** 93.492 sec
**Status:** ok

## 102. RAQ-105

**Question**

What is the subscription checkout link breakdown by status?

**Generated SQL**

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

**Generated final answer**

There are no subscription checkout links to break down by status.

**Execution time:** 12.568 sec
**Status:** ok

## 103. RAQ-094

**Question**

List payments missing uploaded payment proofs.

**Generated SQL**

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
  p.amount,
  p.currency,
  p.due_date,
  p.paid_at,
  COALESCE(pr.name, 'Unknown Program') AS program_name,
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
LEFT JOIN payment_proofs pp
  ON pp.payment_id = p.id
 AND pp.clerk_org_id = p.clerk_org_id
 AND pp.is_deleted = false
WHERE p.clerk_org_id = :org_id
  AND p.is_deleted = false
  AND pp.id IS NULL
ORDER BY p.paid_at DESC NULLS LAST, p.created_at DESC, p.id ASC
LIMIT 50
```

**Generated final answer**

Total payments without uploaded proofs: 190

Showing the first 20 most recent payments:

| Payment ID | Client | Type | Status | Provider | Amount | Currency | Due date | Paid at |
|---|---|---|---|---|---:|---|---|---|
| 4be84c94-0ba6-4998-b529-8dd5fd01ac2e | Jeffrey Nussy | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-24 | 2026-04-24 09:52 UTC |
| 73ae74a6-f01d-4a20-9b11-1533ce7c1215 | Tori tori | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-23 | 2026-04-24 03:57 UTC |
| 1b19b66b-317c-494e-b4b9-cb5d8fa11b04 | Dennis Schouten | Deposit | Paid | Whop | 300,000 | EUR | 2026-04-23 | 2026-04-24 03:11 UTC |
| b29e194e-277f-4e58-9e36-00209c8f1814 | Chris Rouwhof | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-23 | 2026-04-23 13:04 UTC |
| 642f9234-f382-4720-bdda-377e32c8c72d | Peter Post | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-23 | 2026-04-23 11:29 UTC |
| 389702b3-d471-4b55-b82e-b8e63f194ec4 | Sjors Marckelbach | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-23 | 2026-04-23 10:57 UTC |
| 7ab9b71a-200f-4b60-b6cc-9400fb61325c | Nagasaki Elena | First Payment | Paid | Manual | 480,000 | EUR | 2026-04-23 | 2026-04-23 10:39 UTC |
| 4d2de45f-3a45-4b7d-9030-834d9067f55f | Dennis Schouten | Deposit | Paid | Whop | 200,000 | EUR | 2026-04-23 | 2026-04-23 08:06 UTC |
| 4cb1a09c-d3ee-4476-bf99-82de01d164bb | Rolf sterk | Deposit | Paid | Whop | 500,000 | EUR | 2026-04-16 | 2026-04-21 16:47 UTC |
| 68be5fb3-eb63-4beb-a813-668c3c34a038 | Bart | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-21 | 2026-04-21 15:20 UTC |
| fa0c21a6-f8c6-4e42-bc8f-9a9d27a59c39 | Jerry Vercammen | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-21 | 2026-04-21 12:59 UTC |
| fa57727b-70dd-4ad8-8ca3-09b465c99427 | Jan Kraaijeveld | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-21 | 2026-04-21 07:57 UTC |
| ff484bb7-db7b-4818-8fff-ed3260bcd49f | Nico Siersma | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-20 | 2026-04-20 08:55 UTC |
| 93ac97ba-84b4-49ed-a6bd-a969ef44d998 | Marek Macuk | Deposit | Paid | Whop | 50,000 | EUR | 2026-04-19 | 2026-04-19 10:07 UTC |
| 9d86e426-1b1a-44c8-a6ca-7392b29de1be | Marek Macuk | Deposit | Paid | Whop | 200,000 | EUR | 2026-04-19 | 2026-04-18 22:43 UTC |
| a16f9866-bb28-4488-8067-7b22fb04dec6 | Jeroen Willemsen | Deposit | Paid | Whop | 200,000 | EUR | 2026-04-18 | 2026-04-18 17:25 UTC |
| dcf91a92-abc1-489b-a6ba-1cecb3030330 | Paul Jansen | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-17 | 2026-04-18 15:44 UTC |
| 82183ed9-8611-4d1f-add3-6fce04633956 | Sergio D'Alessandro | First Payment | Paid | Whop | 500,000 | EUR | 2026-04-18 | 2026-04-18 06:24 UTC |
| 69804a71-44aa-44ba-9bcf-a95c3ca4603a | Jeroen Willemsen | Deposit | Paid | Whop | 300,000 | EUR | 2026-04-17 | 2026-04-17 16:02 UTC |
| 2391963e-4c09-49b5-9461-f0cf7d84c04e | Silviu Enache | First Payment | Paid | Whop | 200,000 | EUR | 2026-04-17 | 2026-04-17 14:15 UTC |

**Execution time:** 99.935 sec
**Status:** ok

## 104. RAQ-106

**Question**

How many active subscription checkout links do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS active_subscription_checkout_link_count
FROM subscription_checkout_links scl
JOIN contract_subscriptions cs
  ON cs.id = scl.subscription_id
 AND cs.is_deleted = false
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND scl.is_deleted = false
  AND scl.status = 'ACTIVE';
```

**Generated final answer**

There are 0 active subscription checkout links.

**Execution time:** 11.768 sec
**Status:** ok

## 105. RAQ-107

**Question**

How many used subscription checkout links do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS used_subscription_checkout_link_count
FROM subscription_checkout_links scl
JOIN contract_subscriptions cs
  ON cs.id = scl.subscription_id
 AND cs.is_deleted = false
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND scl.is_deleted = false
  AND scl.status = 'USED';
```

**Generated final answer**

There are 0 used subscription checkout links.

**Execution time:** 10.204 sec
**Status:** ok

## 106. RAQ-108

**Question**

How many invalid subscription checkout links do we have?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS invalid_subscription_checkout_link_count
FROM subscription_checkout_links scl
JOIN contract_subscriptions cs
  ON cs.id = scl.subscription_id
 AND cs.is_deleted = false
JOIN contracts c
  ON c.id = cs.contract_id
 AND c.is_deleted = false
WHERE c.clerk_org_id = :org_id
  AND scl.is_deleted = false
  AND scl.status = 'INVALID';
```

**Generated final answer**

There are 0 invalid subscription checkout links.

**Execution time:** 10.339 sec
**Status:** ok

## 107. RAQ-104

**Question**

Which subscription provider has the highest active MRR?

**Generated SQL**

```sql
WITH provider_mrr AS (
  SELECT
    COALESCE(CAST(cs.payment_provider AS text), 'UNKNOWN') AS subscription_provider,
    cs.currency,
    COUNT(*) AS active_subscription_count,
    SUM(
      CASE
        WHEN cs.billing_interval = 'WEEKLY' THEN cs.amount_per_cycle * 52.0 / 12.0
        WHEN cs.billing_interval = 'MONTHLY' THEN cs.amount_per_cycle
        WHEN cs.billing_interval = 'YEARLY' THEN cs.amount_per_cycle / 12.0
        ELSE NULL
      END
    ) AS active_mrr
  FROM contract_subscriptions cs
  JOIN contracts c
    ON c.id = cs.contract_id
   AND c.is_deleted = false
  WHERE c.clerk_org_id = :org_id
    AND cs.is_deleted = false
    AND cs.status = 'ACTIVE'
  GROUP BY COALESCE(CAST(cs.payment_provider AS text), 'UNKNOWN'), cs.currency
), ranked AS (
  SELECT
    subscription_provider,
    currency,
    active_subscription_count,
    active_mrr,
    SUM(active_subscription_count) OVER (PARTITION BY currency) AS total_active_subscriptions,
    SUM(active_mrr) OVER (PARTITION BY currency) AS total_active_mrr_for_currency,
    ROUND(
      active_mrr * 100.0 / NULLIF(SUM(active_mrr) OVER (PARTITION BY currency), 0),
      2
    ) AS percentage_of_active_mrr,
    RANK() OVER (
      PARTITION BY currency
      ORDER BY active_mrr DESC NULLS LAST
    ) AS mrr_rank
  FROM provider_mrr
)
SELECT
  subscription_provider,
  currency,
  active_subscription_count,
  ROUND(active_mrr, 2) AS active_mrr,
  total_active_subscriptions,
  ROUND(total_active_mrr_for_currency, 2) AS total_active_mrr_for_currency,
  percentage_of_active_mrr
FROM ranked
WHERE mrr_rank = 1
ORDER BY currency ASC, subscription_provider ASC;
```

**Generated final answer**

I couldn’t find any active subscriptions, so no subscription provider currently has active MRR.

**Execution time:** 48.273 sec
**Status:** ok

## 108. RAQ-103

**Question**

Show subscription revenue collected by provider.

**Generated SQL**

```sql
SELECT
  CAST(c.type AS text) AS contract_type,
  COUNT(*) AS contract_count,
  SUM(COALESCE(c.total_value, 0)) AS total_contract_value
FROM contracts c
WHERE c.clerk_org_id = :org_id
  AND c.is_deleted = false
GROUP BY CAST(c.type AS text)
ORDER BY contract_count DESC, contract_type ASC
```

**Generated final answer**

There is no collected subscription revenue by provider in the current data—no paid subscription payments were found.

**Execution time:** 88.981 sec
**Status:** ok

## 109. RAQ-110

**Question**

How many pending unmatched payments need reconciliation?

**Generated SQL**

```sql
SELECT
  COUNT(*) AS pending_unmatched_payments_needing_reconciliation
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING';
```

**Generated final answer**

I couldn’t retrieve a reliable count right now due to a data access issue with unmatched payment reconciliation records.

**Execution time:** 65.090 sec
**Status:** error

**Error:** DatabaseError: Execution failed on sql 'SELECT * FROM (SELECT
  COUNT(*) AS pending_unmatched_payments_needing_reconciliation
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING') AS _safe_query LIMIT 20': (psycopg.errors.UndefinedTable) relation "unmatched_payments" does not exist
LINE 3: FROM unmatched_payments up
             ^
[SQL: SELECT * FROM (SELECT
  COUNT(*) AS pending_unmatched_payments_needing_reconciliation
FROM unmatched_payments up
WHERE up.clerk_org_id = %(org_id)s
  AND up.status = 'PENDING') AS _safe_query LIMIT 20]
[parameters: {'org_id': 'org_3ARuGHeqbbEu5FNexlpC7ElaiyW'}]
(Background on this error at: https://sqlalche.me/e/20/f405)

## 110. RAQ-111

**Question**

What amount is sitting in pending unmatched payments?

**Generated SQL**

```sql
SELECT
  up.currency,
  COUNT(*) AS pending_unmatched_payment_count,
  SUM(up.amount) AS pending_unmatched_payment_amount,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING'
GROUP BY up.currency
ORDER BY pending_unmatched_payment_amount DESC, up.currency ASC;
```

**Generated final answer**

I can’t retrieve that right now because unmatched payment records aren’t available in the current workspace.

**Execution time:** 65.656 sec
**Status:** error

**Error:** DatabaseError: Execution failed on sql 'SELECT * FROM (SELECT
  up.currency,
  COUNT(*) AS pending_unmatched_payment_count,
  SUM(up.amount) AS pending_unmatched_payment_amount,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING'
GROUP BY up.currency
ORDER BY pending_unmatched_payment_amount DESC, up.currency ASC) AS _safe_query LIMIT 20': (psycopg.errors.UndefinedTable) relation "unmatched_payments" does not exist
LINE 6: FROM unmatched_payments up
             ^
[SQL: SELECT * FROM (SELECT
  up.currency,
  COUNT(*) AS pending_unmatched_payment_count,
  SUM(up.amount) AS pending_unmatched_payment_amount,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments
FROM unmatched_payments up
WHERE up.clerk_org_id = %(org_id)s
  AND up.status = 'PENDING'
GROUP BY up.currency
ORDER BY pending_unmatched_payment_amount DESC, up.currency ASC) AS _safe_query LIMIT 20]
[parameters: {'org_id': 'org_3ARuGHeqbbEu5FNexlpC7ElaiyW'}]
(Background on this error at: https://sqlalche.me/e/20/f405)

## 111. RAQ-112

**Question**

List pending unmatched payments for reconciliation.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  up.id,
  CAST(up.provider AS text) AS payment_provider,
  up.amount,
  up.currency,
  CAST(up.status AS text) AS unmatched_payment_status,
  up.customer_name,
  up.description,
  up.is_manually_attached,
  up.created_at,
  up.updated_at
FROM public.unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING'
ORDER BY up.created_at ASC, up.id ASC
LIMIT 50;
```

**Generated final answer**

I can’t list pending unmatched payments right now because unmatched payment reconciliation data isn’t available in this workspace yet.

**Execution time:** 78.202 sec
**Status:** error

**Error:** DatabaseError: Execution failed on sql 'SELECT * FROM (SELECT
  COUNT(*) OVER() AS total_matching_rows,
  up.id,
  CAST(up.provider AS text) AS payment_provider,
  up.amount,
  up.currency,
  CAST(up.status AS text) AS unmatched_payment_status,
  up.customer_name,
  up.description,
  up.is_manually_attached,
  up.created_at,
  up.updated_at
FROM public.unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'PENDING'
ORDER BY up.created_at ASC, up.id ASC
LIMIT 50) AS _safe_query LIMIT 20': (psycopg.errors.UndefinedTable) relation "public.unmatched_payments" does not exist
LINE 13: FROM public.unmatched_payments up
              ^
[SQL: SELECT * FROM (SELECT
  COUNT(*) OVER() AS total_matching_rows,
  up.id,
  CAST(up.provider AS text) AS payment_provider,
  up.amount,
  up.currency,
  CAST(up.status AS text) AS unmatched_payment_status,
  up.customer_name,
  up.description,
  up.is_manually_attached,
  up.created_at,
  up.updated_at
FROM public.unmatched_payments up
WHERE up.clerk_org_id = %(org_id)s
  AND up.status = 'PENDING'
ORDER BY up.created_at ASC, up.id ASC
LIMIT 50) AS _safe_query LIMIT 20]
[parameters: {'org_id': 'org_3ARuGHeqbbEu5FNexlpC7ElaiyW'}]
(Background on this error at: https://sqlalche.me/e/20/f405)

## 112. RAQ-109

**Question**

What is the unmatched payment breakdown by status?

**Generated SQL**

```sql
SELECT
  CAST(up.status AS text) AS unmatched_payment_status,
  COUNT(*) AS unmatched_payment_count,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
GROUP BY CAST(up.status AS text)
ORDER BY unmatched_payment_count DESC, unmatched_payment_status ASC;
```

**Generated final answer**

I’m unable to retrieve that breakdown right now because unmatched payment records aren’t available in the connected dataset for this workspace.

**Execution time:** 108.148 sec
**Status:** error

**Error:** DatabaseError: Execution failed on sql 'SELECT * FROM (SELECT
  CAST(up.status AS text) AS unmatched_payment_status,
  COUNT(*) AS unmatched_payment_count,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM unmatched_payments up
WHERE up.clerk_org_id = :org_id
GROUP BY CAST(up.status AS text)
ORDER BY unmatched_payment_count DESC, unmatched_payment_status ASC) AS _safe_query LIMIT 20': (psycopg.errors.UndefinedTable) relation "unmatched_payments" does not exist
LINE 6: FROM unmatched_payments up
             ^
[SQL: SELECT * FROM (SELECT
  CAST(up.status AS text) AS unmatched_payment_status,
  COUNT(*) AS unmatched_payment_count,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 2) AS percentage_of_total
FROM unmatched_payments up
WHERE up.clerk_org_id = %(org_id)s
GROUP BY CAST(up.status AS text)
ORDER BY unmatched_payment_count DESC, unmatched_payment_status ASC) AS _safe_query LIMIT 20]
[parameters: {'org_id': 'org_3ARuGHeqbbEu5FNexlpC7ElaiyW'}]
(Background on this error at: https://sqlalche.me/e/20/f405)

## 113. RAQ-113

**Question**

Which provider has the most pending unmatched payments?

**Generated SQL**

```sql
WITH provider_counts AS (
  SELECT
    CAST(up.provider AS text) AS payment_provider,
    COUNT(*) AS pending_unmatched_payment_count
  FROM public.unmatched_payments up
  WHERE up.clerk_org_id = :org_id
    AND up.status = 'PENDING'
  GROUP BY CAST(up.provider AS text)
), ranked_providers AS (
  SELECT
    payment_provider,
    pending_unmatched_payment_count,
    SUM(pending_unmatched_payment_count) OVER () AS total_pending_unmatched_payments,
    ROUND(
      pending_unmatched_payment_count * 100.0 / NULLIF(SUM(pending_unmatched_payment_count) OVER (), 0),
      2
    ) AS percentage_of_total_pending_unmatched_payments,
    RANK() OVER (ORDER BY pending_unmatched_payment_count DESC) AS provider_rank
  FROM provider_counts
)
SELECT
  payment_provider,
  pending_unmatched_payment_count,
  total_pending_unmatched_payments,
  percentage_of_total_pending_unmatched_payments
FROM ranked_providers
WHERE provider_rank = 1
ORDER BY payment_provider ASC;
```

**Generated final answer**

I can’t determine that right now because unmatched payment records aren’t available in the current workspace data.

**Execution time:** 84.585 sec
**Status:** error

**Error:** DatabaseError: Execution failed on sql 'SELECT * FROM (WITH provider_counts AS (
  SELECT
    CAST(up.provider AS text) AS payment_provider,
    COUNT(*) AS pending_unmatched_payment_count
  FROM public.unmatched_payments up
  WHERE up.clerk_org_id = :org_id
    AND up.status = 'PENDING'
  GROUP BY CAST(up.provider AS text)
), ranked_providers AS (
  SELECT
    payment_provider,
    pending_unmatched_payment_count,
    SUM(pending_unmatched_payment_count) OVER () AS total_pending_unmatched_payments,
    ROUND(
      pending_unmatched_payment_count * 100.0 / NULLIF(SUM(pending_unmatched_payment_count) OVER (), 0),
      2
    ) AS percentage_of_total_pending_unmatched_payments,
    RANK() OVER (ORDER BY pending_unmatched_payment_count DESC) AS provider_rank
  FROM provider_counts
)
SELECT
  payment_provider,
  pending_unmatched_payment_count,
  total_pending_unmatched_payments,
  percentage_of_total_pending_unmatched_payments
FROM ranked_providers
WHERE provider_rank = 1
ORDER BY payment_provider ASC) AS _safe_query LIMIT 20': (psycopg.errors.UndefinedTable) relation "public.unmatched_payments" does not exist
LINE 5:   FROM public.unmatched_payments up
               ^
[SQL: SELECT * FROM (WITH provider_counts AS (
  SELECT
    CAST(up.provider AS text) AS payment_provider,
    COUNT(*) AS pending_unmatched_payment_count
  FROM public.unmatched_payments up
  WHERE up.clerk_org_id = %(org_id)s
    AND up.status = 'PENDING'
  GROUP BY CAST(up.provider AS text)
), ranked_providers AS (
  SELECT
    payment_provider,
    pending_unmatched_payment_count,
    SUM(pending_unmatched_payment_count) OVER () AS total_pending_unmatched_payments,
    ROUND(
      pending_unmatched_payment_count * 100.0 / NULLIF(SUM(pending_unmatched_payment_count) OVER (), 0),
      2
    ) AS percentage_of_total_pending_unmatched_payments,
    RANK() OVER (ORDER BY pending_unmatched_payment_count DESC) AS provider_rank
  FROM provider_counts
)
SELECT
  payment_provider,
  pending_unmatched_payment_count,
  total_pending_unmatched_payments,
  percentage_of_total_pending_unmatched_payments
FROM ranked_providers
WHERE provider_rank = 1
ORDER BY payment_provider ASC) AS _safe_query LIMIT 20]
[parameters: {'org_id': 'org_3ARuGHeqbbEu5FNexlpC7ElaiyW'}]
(Background on this error at: https://sqlalche.me/e/20/f405)

## 114. RAQ-115

**Question**

How many unmatched payments were manually attached?

**Generated SQL**

```sql
SELECT
  column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'payments'
ORDER BY ordinal_position ASC;
```

**Generated final answer**

I can’t determine that right now because unmatched payment records aren’t available in this workspace.

**Execution time:** 62.149 sec
**Status:** ok

## 115. RAQ-116

**Question**

List attached unmatched payments.

**Generated SQL**

```sql
SELECT
  COUNT(*) OVER() AS total_matching_rows,
  up.id,
  CAST(up.provider AS text) AS payment_provider,
  up.amount,
  up.currency,
  CAST(up.status AS text) AS unmatched_payment_status,
  up.customer_name,
  up.description,
  up.attached_payment_id,
  up.is_manually_attached,
  up.created_at,
  up.updated_at
FROM public.unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'ATTACHED'
ORDER BY up.updated_at DESC, up.created_at DESC, up.id ASC
LIMIT 50;
```

**Generated final answer**

I can’t list attached unmatched payments right now because unmatched payment records aren’t available in the current workspace.

**Execution time:** 69.438 sec
**Status:** error

**Error:** DatabaseError: Execution failed on sql 'SELECT * FROM (SELECT
  COUNT(*) OVER() AS total_matching_rows,
  up.id,
  CAST(up.provider AS text) AS payment_provider,
  up.amount,
  up.currency,
  CAST(up.status AS text) AS unmatched_payment_status,
  up.customer_name,
  up.description,
  up.attached_payment_id,
  up.is_manually_attached,
  up.created_at,
  up.updated_at
FROM public.unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.status = 'ATTACHED'
ORDER BY up.updated_at DESC, up.created_at DESC, up.id ASC
LIMIT 50) AS _safe_query LIMIT 20': (psycopg.errors.UndefinedTable) relation "public.unmatched_payments" does not exist
LINE 14: FROM public.unmatched_payments up
              ^
[SQL: SELECT * FROM (SELECT
  COUNT(*) OVER() AS total_matching_rows,
  up.id,
  CAST(up.provider AS text) AS payment_provider,
  up.amount,
  up.currency,
  CAST(up.status AS text) AS unmatched_payment_status,
  up.customer_name,
  up.description,
  up.attached_payment_id,
  up.is_manually_attached,
  up.created_at,
  up.updated_at
FROM public.unmatched_payments up
WHERE up.clerk_org_id = %(org_id)s
  AND up.status = 'ATTACHED'
ORDER BY up.updated_at DESC, up.created_at DESC, up.id ASC
LIMIT 50) AS _safe_query LIMIT 20]
[parameters: {'org_id': 'org_3ARuGHeqbbEu5FNexlpC7ElaiyW'}]
(Background on this error at: https://sqlalche.me/e/20/f405)

## 116. RAQ-114

**Question**

Show unmatched payment status breakdown for records created from 2026-04-01 to 2026-05-01.

**Generated SQL**

```sql
SELECT
  CAST(up.status AS text) AS unmatched_payment_status,
  COUNT(*) AS unmatched_payment_count,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM public.unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.created_at >= :start_date
  AND up.created_at < :end_date
GROUP BY CAST(up.status AS text)
ORDER BY unmatched_payment_count DESC, unmatched_payment_status ASC
```

**Generated final answer**

I couldn’t retrieve that breakdown because unmatched payment data isn’t available in the current database connection right now.

**Execution time:** 113.785 sec
**Status:** error

**Error:** DatabaseError: Execution failed on sql 'SELECT * FROM (SELECT
  CAST(up.status AS text) AS unmatched_payment_status,
  COUNT(*) AS unmatched_payment_count,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM public.unmatched_payments up
WHERE up.clerk_org_id = :org_id
  AND up.created_at >= :start_date
  AND up.created_at < :end_date
GROUP BY CAST(up.status AS text)
ORDER BY unmatched_payment_count DESC, unmatched_payment_status ASC) AS _safe_query LIMIT 20': (psycopg.errors.UndefinedTable) relation "public.unmatched_payments" does not exist
LINE 9: FROM public.unmatched_payments up
             ^
[SQL: SELECT * FROM (SELECT
  CAST(up.status AS text) AS unmatched_payment_status,
  COUNT(*) AS unmatched_payment_count,
  SUM(COUNT(*)) OVER() AS total_matching_unmatched_payments,
  ROUND(
    COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0),
    2
  ) AS percentage_of_total
FROM public.unmatched_payments up
WHERE up.clerk_org_id = %(org_id)s
  AND up.created_at >= %(start_date)s
  AND up.created_at < %(end_date)s
GROUP BY CAST(up.status AS text)
ORDER BY unmatched_payment_count DESC, unmatched_payment_status ASC) AS _safe_query LIMIT 20]
[parameters: {'org_id': 'org_3ARuGHeqbbEu5FNexlpC7ElaiyW', 'start_date': '2026-04-01', 'end_date': '2026-05-01'}]
(Background on this error at: https://sqlalche.me/e/20/f405)
