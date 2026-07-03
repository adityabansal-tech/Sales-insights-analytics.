-- ============================================================
-- KPI Analytics Views
-- Power BI and the Python KPI runner both query THESE views,
-- not the raw fact_sales table.
-- ============================================================

-- 1. Monthly revenue trend + Month-over-Month growth %
DROP VIEW IF EXISTS vw_monthly_revenue;
CREATE VIEW vw_monthly_revenue AS
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.sales_amount), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2)       AS total_profit,
    COUNT(DISTINCT f.order_id)    AS order_count
FROM fact_sales f
JOIN dim_date d ON f.order_date = d.date_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;

-- 2. Product performance benchmark: rank + running total (Pareto view)
DROP VIEW IF EXISTS vw_product_performance;
CREATE VIEW vw_product_performance AS
SELECT
    p.product_name,
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales_amount), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2)       AS total_profit,
    SUM(f.quantity)               AS units_sold,
    RANK() OVER (ORDER BY SUM(f.sales_amount) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name, p.category, p.sub_category
ORDER BY total_revenue DESC;

-- 3. Category-level performance
DROP VIEW IF EXISTS vw_category_performance;
CREATE VIEW vw_category_performance AS
SELECT
    p.category,
    ROUND(SUM(f.sales_amount), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2)       AS total_profit,
    ROUND(SUM(f.profit) / NULLIF(SUM(f.sales_amount), 0) * 100, 2) AS margin_pct,
    COUNT(DISTINCT f.order_id)    AS order_count
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- 4. Regional performance
DROP VIEW IF EXISTS vw_regional_performance;
CREATE VIEW vw_regional_performance AS
SELECT
    c.region,
    c.country,
    ROUND(SUM(f.sales_amount), 2) AS total_revenue,
    COUNT(DISTINCT f.order_id)    AS order_count,
    ROUND(SUM(f.sales_amount) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.region, c.country
ORDER BY total_revenue DESC;

-- 5. Customer RFM (Recency, Frequency, Monetary)
DROP VIEW IF EXISTS vw_customer_rfm;
CREATE VIEW vw_customer_rfm AS
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    MAX(f.order_date)             AS last_order_date,
    COUNT(DISTINCT f.order_id)    AS frequency,
    ROUND(SUM(f.sales_amount), 2) AS monetary_value
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment
ORDER BY monetary_value DESC;

-- 6. Executive KPI summary (single row — powers dashboard cards)
DROP VIEW IF EXISTS vw_kpi_summary;
CREATE VIEW vw_kpi_summary AS
SELECT
    ROUND(SUM(sales_amount), 2)                         AS total_revenue,
    ROUND(SUM(profit), 2)                                AS total_profit,
    ROUND(SUM(profit) / NULLIF(SUM(sales_amount),0)*100,2) AS margin_pct,
    COUNT(DISTINCT order_id)                             AS total_orders,
    ROUND(SUM(sales_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM fact_sales;
