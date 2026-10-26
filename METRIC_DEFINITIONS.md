# Metric definitions

| Metric | Definition |
|---|---|
| Gross sales | Sum of quantity × unit price for positive-quantity lines on noncancelled invoices |
| Returns | Absolute value of negative-quantity or cancellation-invoice lines |
| Net revenue | Gross sales minus returns |
| Sales orders | Distinct invoices with at least one positive-sales line in the selected window |
| Average order value | Gross sales divided by sales orders; returns are reported separately |
| Return value ratio | Return value divided by gross sales, not the fraction of returned orders |
| Known buyers | Distinct identified customers with positive sales in the window |
| Repeat buyer | Known buyer with at least two distinct positive-sales invoices in the window |
| Repeat purchase rate | Repeat buyers divided by known buyers |
| RFM recency | Integer days from selected end date to latest positive-sales timestamp |
| RFM frequency | Distinct positive-sales invoices for a known customer in the selected window |
| RFM monetary | Net transaction value for the known customer in the window |
| Acquisition cohort | Month of first positive sale observed in the complete source warehouse |
| Cohort retention | Distinct cohort customers purchasing in a month divided by full observed cohort size |

RFM scores use `NTILE(5)`; larger recency scores indicate more recent activity.
Frequency and monetary scores grow with their respective values. Customer ID
breaks ties deterministically, so identical values can receive different
quintiles. Labels are simple rules, not learned customer classes. The RFM report
shows the top 200 customers by monetary value, not the entire population.

Cohort acquisition uses the full warehouse to avoid redefining a customer as new
after filtering. The date range filters activity. A recursive calendar includes
zero-activity observed months and omits future months. Country-specific cohorts
are deliberately rejected until country-level acquisition rules are implemented.
Boundaries and December 2011 may be partial; recent cohorts have shorter follow-up.
Retention is transaction activity, not contractual subscription retention.

Revenue does not imply profit. Costs, taxes, shipping adjustments and exchange
rates are unavailable. Currency conversion and inflation adjustment are not
performed. Anonymous customer activity cannot be linked across invoices.
