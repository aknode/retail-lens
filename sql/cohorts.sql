 , first_purchase AS (
 SELECT customer_id,MIN(strftime('%Y-%m',invoice_date)) cohort
 FROM fact_lines WHERE customer_id IS NOT NULL AND gross_amount>0 GROUP BY customer_id
 ), sizes AS (
 SELECT cohort,COUNT(*) cohort_size FROM first_purchase GROUP BY cohort
 ), calendar(month_start) AS (
 SELECT date(:start,'start of month')
 UNION ALL
 SELECT date(month_start,'+1 month') FROM calendar
 WHERE date(month_start,'+1 month')<=date(:end,'start of month')
 AND date(month_start,'+1 month')<=(SELECT date(MAX(invoice_date),'start of month') FROM fact_lines)
 ), activity AS (
 SELECT p.cohort,strftime('%Y-%m',f.invoice_date) active_month,
 COUNT(DISTINCT f.customer_id) active_customers
 FROM filtered f JOIN first_purchase p USING(customer_id)
 WHERE gross_amount>0 GROUP BY p.cohort,active_month
 )
 SELECT s.cohort,
 (CAST(strftime('%Y',c.month_start) AS INTEGER)-CAST(substr(s.cohort,1,4) AS INTEGER))*12
 +CAST(strftime('%m',c.month_start) AS INTEGER)-CAST(substr(s.cohort,6,2) AS INTEGER) month_index,
 COALESCE(a.active_customers,0) active_customers,s.cohort_size,
 ROUND(1.0*COALESCE(a.active_customers,0)/s.cohort_size,4) retention
 FROM sizes s JOIN calendar c ON strftime('%Y-%m',c.month_start)>=s.cohort
 LEFT JOIN activity a ON a.cohort=s.cohort AND a.active_month=strftime('%Y-%m',c.month_start)
 WHERE c.month_start<=(SELECT date(MAX(invoice_date),'start of month') FROM fact_lines)
 ORDER BY s.cohort,month_index
