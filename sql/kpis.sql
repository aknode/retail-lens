SELECT ROUND(SUM(gross_amount),2) gross_sales, ROUND(SUM(return_amount),2) returns,
 ROUND(SUM(net_amount),2) net_revenue,
 COUNT(DISTINCT CASE WHEN gross_amount>0 THEN invoice_no END) sales_orders,
 COUNT(DISTINCT CASE WHEN gross_amount>0 THEN customer_id END) known_buyers,
 ROUND(SUM(gross_amount)/NULLIF(COUNT(DISTINCT CASE WHEN gross_amount>0 THEN invoice_no END),0),2) average_order_value,
 ROUND(1.0*SUM(return_amount)/NULLIF(SUM(gross_amount),0),4) return_value_ratio FROM filtered