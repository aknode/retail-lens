SELECT country,ROUND(SUM(net_amount),2) net_revenue,
 COUNT(DISTINCT CASE WHEN gross_amount>0 THEN invoice_no END) orders,
 COUNT(DISTINCT customer_id) known_customers FROM filtered GROUP BY country ORDER BY net_revenue DESC