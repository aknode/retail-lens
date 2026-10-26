, activity AS (SELECT customer_id,CAST(julianday(:end)-julianday(MAX(CASE WHEN gross_amount>0 THEN invoice_date END)) AS INTEGER) recency_days,
COUNT(DISTINCT CASE WHEN gross_amount>0 THEN invoice_no END) frequency,ROUND(SUM(net_amount),2) monetary
FROM filtered WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING frequency>0),
scored AS (SELECT *,NTILE(5) OVER(ORDER BY recency_days DESC,customer_id) r_score,
NTILE(5) OVER(ORDER BY frequency,customer_id) f_score,NTILE(5) OVER(ORDER BY monetary,customer_id) m_score FROM activity)
SELECT *,CASE WHEN r_score>=4 AND f_score>=4 THEN 'Champions' WHEN r_score<=2 AND f_score>=4 THEN 'At risk'
WHEN r_score>=4 THEN 'Recent buyers' ELSE 'Developing' END segment FROM scored ORDER BY monetary DESC LIMIT 200