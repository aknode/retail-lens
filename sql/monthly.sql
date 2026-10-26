SELECT strftime('%Y-%m',invoice_date) month,ROUND(SUM(gross_amount),2) gross_sales,
 ROUND(SUM(return_amount),2) returns,ROUND(SUM(net_amount),2) net_revenue,
 COUNT(DISTINCT CASE WHEN gross_amount>0 THEN invoice_no END) orders FROM filtered GROUP BY month ORDER BY month