"""
KPI query runner — executes the optimized SQL views and returns
pandas DataFrames, logging execution time for each.
"""
import time
import pandas as pd

from . import config, load


def run_query(engine, sql, label=""):
    start = time.perf_counter()
    df = pd.read_sql(sql, engine)
    elapsed = time.perf_counter() - start
    print(f"[kpi] {label:<28} rows={len(df):<6} time={elapsed*1000:.1f}ms")
    return df, elapsed


def get_kpi_summary(engine):
    df, _ = run_query(engine, "SELECT * FROM vw_kpi_summary", "KPI Summary")
    return df


def get_monthly_revenue(engine):
    df, _ = run_query(engine, "SELECT * FROM vw_monthly_revenue", "Monthly Revenue Trend")
    return df


def get_product_performance(engine, top_n=10):
    df, _ = run_query(
        engine,
        f"SELECT * FROM vw_product_performance LIMIT {top_n}",
        "Top Product Performance"
    )
    return df


def get_category_performance(engine):
    df, _ = run_query(engine, "SELECT * FROM vw_category_performance", "Category Performance")
    return df


def get_regional_performance(engine):
    df, _ = run_query(engine, "SELECT * FROM vw_regional_performance", "Regional Performance")
    return df


def get_customer_rfm(engine, top_n=10):
    df, _ = run_query(
        engine,
        f"SELECT * FROM vw_customer_rfm LIMIT {top_n}",
        "Top Customers (RFM)"
    )
    return df


def print_all_kpis(engine):
    print("\n" + "=" * 60)
    print("KPI DASHBOARD")
    print("=" * 60)

    summary = get_kpi_summary(engine)
    print("\n--- Executive Summary ---")
    print(summary.to_string(index=False))

    print("\n--- Monthly Revenue Trend (last 6) ---")
    monthly = get_monthly_revenue(engine)
    print(monthly.tail(6).to_string(index=False))

    print("\n--- Top 10 Products ---")
    print(get_product_performance(engine).to_string(index=False))

    print("\n--- Category Performance ---")
    print(get_category_performance(engine).to_string(index=False))

    print("\n--- Regional Performance ---")
    print(get_regional_performance(engine).to_string(index=False))

    print("\n--- Top 10 Customers (by revenue) ---")
    print(get_customer_rfm(engine).to_string(index=False))


if __name__ == "__main__":
    engine = load.get_engine()
    print_all_kpis(engine)
