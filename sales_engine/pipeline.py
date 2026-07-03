"""
Orchestrates the full ETL run: extract (CSV) -> transform -> load -> index -> views.
Run with: python -m sales_engine.pipeline
"""
import os
import time
import pandas as pd

from . import config, transform, load


def run_pipeline():
    print("=" * 60)
    print("SALES INSIGHTS ETL PIPELINE")
    print("=" * 60)

    engine = load.get_engine()

    # fresh schema each run (idempotent demo pipeline)
    print("\n[1/5] Applying schema...")
    load.apply_schema(engine)

    print("\n[2/5] Extracting + transforming...")
    dim_product = transform.clean_dimension(pd.read_csv(config.CSV_FILES["dim_product"], encoding="utf-8"), "product_id")
    dim_customer = transform.clean_dimension(pd.read_csv(config.CSV_FILES["dim_customer"], encoding="utf-8"), "customer_id")
    dim_date = transform.clean_dimension(pd.read_csv(config.CSV_FILES["dim_date"], encoding="utf-8"), "date_id")
    fact_sales = transform.clean_fact_sales(pd.read_csv(config.CSV_FILES["fact_sales"], encoding="utf-8"))

    print("\n[3/5] Loading into database...")
    total_start = time.perf_counter()
    load.bulk_load(engine, dim_product, "dim_product")
    load.bulk_load(engine, dim_customer, "dim_customer")
    load.bulk_load(engine, dim_date, "dim_date")
    load.bulk_load(engine, fact_sales, "fact_sales", chunksize=5000)
    total_elapsed = time.perf_counter() - total_start
    print(f"[load] TOTAL load time: {total_elapsed:.2f}s for {len(fact_sales)} fact rows")

    print("\n[4/5] Applying indexes...")
    load.apply_indexes(engine)

    print("\n[5/5] Applying analytics views...")
    load.apply_views(engine)

    # log the run
    log_path = os.path.join(config.LOG_DIR, "pipeline_log.csv")
    log_exists = os.path.exists(log_path)
    with open(log_path, "a") as f:
        if not log_exists:
            f.write("timestamp,fact_rows_loaded,total_load_seconds\n")
        f.write(f"{pd.Timestamp.now()},{len(fact_sales)},{total_elapsed:.3f}\n")

    print("\n✅ Pipeline complete.")
    return engine


if __name__ == "__main__":
    run_pipeline()
