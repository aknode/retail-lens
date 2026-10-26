, orders AS (SELECT customer_id,COUNT(DISTINCT invoice_no) n FROM filtered
WHERE customer_id IS NOT NULL AND gross_amount>0 GROUP BY customer_id)
SELECT COUNT(*) known_buyers,SUM(CASE WHEN n>1 THEN 1 ELSE 0 END) repeat_buyers,
ROUND(1.0*SUM(CASE WHEN n>1 THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),4) repeat_purchase_rate FROM orders