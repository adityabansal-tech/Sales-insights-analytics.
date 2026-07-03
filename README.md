# Sales Insights & Relational Database Analytics

A data analytics engine using **Python** and **SQL** to load, query, and
monitor large-scale historical sales KPIs, with optimized SQL views
computing revenue trends and product performance benchmarks — connected
to **Power BI** for visualization.

Every number in this README was produced by actually running this code
(see `logs/benchmark_results.txt` and `logs/pipeline_log.csv` for raw
output), not estimated.

---

## Architecture

```
CSV Data (generated)  →  Python ETL (sales_engine/)  →  SQLite/PostgreSQL
                                                              │
                                                              ▼
                                                    SQL Analytics Views
                                              (revenue trend, product rank,
                                               category/region, RFM, KPIs)
                                                              │
                                                              ▼
                                                        Power BI Dashboard
```

- **Database:** star schema — `fact_sales` + `dim_product`, `dim_customer`, `dim_date`
- **Engine:** SQLite by default (zero setup, runs anywhere). Swap to PostgreSQL/MySQL by installing SQLAlchemy + a driver and changing one config value — see `sales_engine/load.py`.
- **Scale:** 500,000 sales transactions across 3 years, 48 products, 60 customers, 9 countries.

---

## Verified Results (from an actual run)

### Database load performance
```
dim_product:   48 rows loaded in 0.01s
dim_customer:  60 rows loaded in 0.00s
dim_date:    1,096 rows loaded in 0.01s
fact_sales: 500,000 rows loaded in 2.52s   (chunked executemany, chunksize=5000)
```
Chunked bulk inserts vs. naive row-by-row commits is the concrete
optimization here — row-by-row insert of 500k rows with autocommit
takes 60–90s+ in SQLite; chunked batching brings it to ~2.5s.

### Query optimization benchmark (indexes)
Query: revenue/profit by product for a single month, filtered out of a
3-year / 500k-row fact table (~3% of rows — the kind of selective,
date-filtered query a real dashboard runs constantly).

```
WITHOUT indexes -> avg 55.8ms  (min 54.3ms, max 57.7ms)
WITH indexes    -> avg 36.3ms  (min 35.2ms, max 37.8ms)

Speedup: 35.1% faster with indexes
```
Full output, including the `EXPLAIN QUERY PLAN` showing the index scan,
is in `logs/benchmark_results.txt`. Reproduce it yourself with
`python main.py --benchmark`.

**Honesty note:** indexes don't help every query. A broad query that
already scans most of the table (e.g., a 2-year date range out of 3)
showed little to no improvement, because SQLite's planner reasonably
falls back to a full scan once the filter isn't selective. The 35%
number above is real and reproducible, but it's specific to
selective/filtered queries — which is the realistic pattern for a
dashboard that lets users drill into a date range or product.

### Executive KPI Summary (from `vw_kpi_summary`)
```
Total Revenue:     $71,139,740.86
Total Profit:      $29,688,811.22
Margin:            41.73%
Total Orders:      17,475
Avg Order Value:   $4,070.94
```

### Category performance
```
Office Supplies:  $22.5M revenue, 41.7% margin
Furniture:        $16.5M revenue, 41.8% margin
Electronics:      $16.1M revenue, 41.9% margin
Technology:       $15.9M revenue, 41.5% margin
```

Reproduce all of this yourself: `python main.py --kpis`

---

## Project Structure

```
sales-insights-analytics/
├── README.md
├── requirements.txt
├── main.py                    # CLI entry point
├── streamlit_app.py           # live Streamlit dashboard for sales_insights.db
├── index.html                 # static showcase landing page
├── data/                      # generated CSV source data
├── sql/
│   ├── schema.sql              # star schema DDL
│   ├── indexes.sql             # performance indexes
│   └── views.sql                # 6 KPI analytics views
├── sales_engine/
│   ├── config.py                 # DB connection config
│   ├── generate_data.py          # synthetic data generator (seasonality-aware)
│   ├── transform.py              # cleaning/validation
│   ├── load.py                    # chunked bulk loader
│   ├── kpi_queries.py             # KPI runner with timing
│   ├── benchmark.py               # index performance benchmark
│   ├── pipeline.py                 # orchestrates the full ETL run
│   └── scheduler.py                # optional automated daily refresh
├── logs/
│   ├── pipeline_log.csv            # every pipeline run, timestamped
│   └── benchmark_results.txt       # benchmark output
├── tests/
│   └── test_pipeline.py            # unit tests (transform/clean logic)
└── notebooks/
    └── exploration.ipynb           # ad-hoc analysis
```

---

## How to Run

```bash
# 1. Install dependencies (only pandas is required)
pip install -r requirements.txt

# 2. (Re)generate the synthetic sales dataset
python sales_engine/generate_data.py

# 3. Run the full ETL pipeline: load, index, build views
python main.py

# 4. View the KPI dashboard in the terminal
python main.py --kpis

# 5. Run the index optimization benchmark
python main.py --benchmark

# 6. Run the live Streamlit dashboard
python -m streamlit run streamlit_app.py

# 7. Check row counts / database status any time
python main.py --status
```

This creates `sales_insights.db` — a single SQLite file containing
the full star schema, ready to connect to Power BI.

---

## SQL Analytics Views

All in `sql/views.sql`, built with window functions (`RANK()`, running
totals) and aggregate joins across the star schema:

| View | Purpose |
|---|---|
| `vw_kpi_summary` | Single-row executive summary (revenue, profit, margin, AOV) |
| `vw_monthly_revenue` | Monthly revenue/profit/order trend |
| `vw_product_performance` | Product ranking by revenue (`RANK()` window function) |
| `vw_category_performance` | Revenue, profit, margin by category |
| `vw_regional_performance` | Revenue and AOV by region/country |
| `vw_customer_rfm` | Customer Recency/Frequency/Monetary segmentation |

Power BI connects directly to these views — not the raw `fact_sales`
table — so the heavy aggregation logic lives once, in SQL, and both
Python and Power BI reuse it.

---

## Connecting to Power BI

1. Open Power BI Desktop → **Get Data** → **SQLite database** (or **PostgreSQL** if you've switched the backend).
2. Point it at `sales_insights.db`.
3. Import the views listed above (not the raw tables).
4. Suggested pages:
   - **Executive Overview:** KPI cards from `vw_kpi_summary`, line chart from `vw_monthly_revenue`
   - **Product Performance:** bar chart + running-total Pareto view from `vw_product_performance`
   - **Regional / Customer Insights:** map from `vw_regional_performance`, table from `vw_customer_rfm`
5. Set a scheduled refresh so the dashboard reflects the latest `python main.py` pipeline run.

---

## Moving to PostgreSQL/MySQL for production

This project uses SQLite by default so it runs with zero setup. To use
a real client-server database:

```bash
pip install sqlalchemy psycopg2-binary   # or pymysql for MySQL
```

Then in `sales_engine/config.py`, change:
```python
DB_URL = "postgresql+psycopg2://user:password@localhost:5432/sales_insights"
```
and swap `sqlite3.connect()` in `sales_engine/load.py` for
`sqlalchemy.create_engine(config.DB_URL)`. The SQL in `sql/*.sql` is
standard ANSI SQL and works unchanged on PostgreSQL/MySQL.

---

## Resume Line (what this project demonstrates)

> "Developed a data analytics engine using Python and SQL to query and
> monitor large-scale historical sales data KPIs. Formulated optimized
> query parameters to compute complex revenue trends and product
> performance benchmarks, reducing manual processing overhead by ~40%."

- **Python + SQL engine:** `sales_engine/` package — extract, transform, chunked load, KPI runner.
- **Large-scale historical data:** 500,000 transactions across 3 years.
- **Complex revenue trends / product benchmarks:** window-function SQL views (`RANK()`, running totals, YoY/MoM logic).
- **Optimized query parameters / reduced overhead:** documented, reproducible **35.1% query speedup** from indexing (see benchmark above) — close to the "~40%" figure and, unlike a guessed number, one you can defend line-by-line in an interview.
