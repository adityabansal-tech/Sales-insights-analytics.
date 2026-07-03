-- ============================================================
-- Sales Insights & Relational Database Analytics
-- Star Schema: fact_sales + dim_product + dim_customer + dim_date
-- ============================================================

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_product (
    product_id      INTEGER PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    sub_category    TEXT NOT NULL,
    unit_cost       REAL NOT NULL
);

CREATE TABLE dim_customer (
    customer_id     INTEGER PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    segment         TEXT NOT NULL,      -- Consumer, Corporate, Home Office
    country         TEXT NOT NULL,
    region           TEXT NOT NULL
);

CREATE TABLE dim_date (
    date_id         TEXT PRIMARY KEY,   -- ISO date string YYYY-MM-DD
    day             INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    quarter         INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    is_weekend      INTEGER NOT NULL    -- 0/1
);

CREATE TABLE fact_sales (
    line_id         INTEGER PRIMARY KEY,
    order_id        TEXT NOT NULL,
    order_date      TEXT NOT NULL REFERENCES dim_date(date_id),
    ship_date       TEXT,
    customer_id     INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    product_id      INTEGER NOT NULL REFERENCES dim_product(product_id),
    quantity        INTEGER NOT NULL,
    unit_price      REAL NOT NULL,
    discount        REAL NOT NULL,
    sales_amount    REAL NOT NULL,
    profit          REAL NOT NULL
);
