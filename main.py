"""
CLI entry point.

Usage:
    python main.py              # run full ETL pipeline
    python main.py --kpis       # print KPI dashboard
    python main.py --benchmark  # run index performance benchmark
    python main.py --status     # show row counts in the database
"""
import sys
from sales_engine import pipeline, kpi_queries, benchmark, load


def show_status():
    engine = load.get_engine()
    tables = ["dim_product", "dim_customer", "dim_date", "fact_sales"]
    print("=" * 40)
    print("DATABASE STATUS")
    print("=" * 40)
    cur = engine.cursor()
    for t in tables:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:<15} {count:>8} rows")
        except Exception:
            print(f"  {t:<15}   (not loaded yet — run: python main.py)")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--kpis" in args:
        engine = load.get_engine()
        kpi_queries.print_all_kpis(engine)
    elif "--benchmark" in args:
        benchmark.run_benchmark()
    elif "--status" in args:
        show_status()
    else:
        pipeline.run_pipeline()
