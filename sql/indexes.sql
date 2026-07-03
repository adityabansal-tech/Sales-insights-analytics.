-- ============================================================
-- Performance indexes for fact_sales
-- These are what let large aggregate queries (revenue trends,
-- product benchmarks) run against indexed columns instead of
-- full table scans.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sales_date     ON fact_sales(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_product  ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_order    ON fact_sales(order_id);

-- composite index for the most common query pattern:
-- "revenue by product over a date range"
CREATE INDEX IF NOT EXISTS idx_sales_date_product ON fact_sales(order_date, product_id);
