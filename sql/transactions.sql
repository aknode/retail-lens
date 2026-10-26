SELECT invoice_no,invoice_date,country,customer_id,stock_code,description,quantity,unit_price,
 ROUND(net_amount,2) net_amount FROM filtered ORDER BY invoice_date DESC,invoice_no,line_id LIMIT 100