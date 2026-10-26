SELECT stock_code,MAX(description) product,ROUND(SUM(net_amount),2) net_revenue,
 SUM(CASE WHEN gross_amount>0 THEN quantity ELSE 0 END) units_sold,
 ROUND(SUM(return_amount),2) returns FROM filtered GROUP BY stock_code ORDER BY net_revenue DESC LIMIT 30