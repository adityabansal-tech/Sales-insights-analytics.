import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sales_insights.db")
OUT_PATH = os.path.join(BASE_DIR, "dashboard_data.json")

queries = {
    "kpi": "SELECT * FROM vw_kpi_summary",
    "monthly": "SELECT year, month, month_name, total_revenue, total_profit, order_count FROM vw_monthly_revenue ORDER BY year, month",
    "products": "SELECT product_name, category, sub_category, total_revenue, total_profit, units_sold FROM vw_product_performance ORDER BY total_revenue DESC LIMIT 50",
    "categories": "SELECT category, total_revenue, total_profit, margin_pct, order_count FROM vw_category_performance ORDER BY total_revenue DESC",
    "regional": "SELECT region, country, total_revenue, order_count, avg_order_value FROM vw_regional_performance ORDER BY total_revenue DESC",
    "customers": "SELECT customer_id, customer_name, segment, last_order_date, frequency, monetary_value FROM vw_customer_rfm ORDER BY monetary_value DESC LIMIT 200",
}

# Try to read benchmark results from logs/benchmark_results.txt if present
BENCH_PATH = os.path.join(BASE_DIR, "logs", "benchmark_results.txt")

def fetch_benchmark():
    if not os.path.exists(BENCH_PATH):
        return None
    with open(BENCH_PATH, "r", encoding="utf-8") as f:
        txt = f.read().strip()
    # Simple parse
    data = {"raw": txt}
    try:
        for line in txt.splitlines():
            if line.lower().startswith("without indexes") or "without indexes" in line.lower():
                # e.g. Without indexes: avg=121.6ms (min=114.3ms, max=126.5ms)
                parts = line.split("avg=")
                if len(parts) > 1:
                    val = parts[1].split("ms")[0]
                    data["without_avg_ms"] = float(val)
            if line.lower().startswith("with indexes") or "with indexes" in line.lower():
                parts = line.split("avg=")
                if len(parts) > 1:
                    val = parts[1].split("ms")[0]
                    data["with_avg_ms"] = float(val)
            if line.lower().startswith("speedup:") or "speedup:" in line.lower():
                try:
                    data["speedup_pct"] = float(line.split(":")[-1].strip().replace("%",""))
                except Exception:
                    pass
    except Exception:
        pass
    return data


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit("Database not found. Run python main.py to generate it.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    out = {}
    for key, q in queries.items():
        cur.execute(q)
        rows = [dict(r) for r in cur.fetchall()]
        out[key] = rows

    bench = fetch_benchmark()
    out["benchmark"] = bench

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
