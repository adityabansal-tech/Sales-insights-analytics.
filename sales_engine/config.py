"""
Central configuration.
Uses SQLite by default (zero-setup, portable, works everywhere).
To point this at PostgreSQL/MySQL for production, just change DB_URL —
every other module uses SQLAlchemy so nothing else needs to change.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SQL_DIR = os.path.join(BASE_DIR, "sql")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "sales_insights.db")
DB_URL = f"sqlite:///{DB_PATH}"

# --- To use PostgreSQL instead, e.g.: ---
# DB_URL = "postgresql+psycopg2://user:password@localhost:5432/sales_insights"

CSV_FILES = {
    "dim_product": os.path.join(DATA_DIR, "dim_product.csv"),
    "dim_customer": os.path.join(DATA_DIR, "dim_customer.csv"),
    "dim_date": os.path.join(DATA_DIR, "dim_date.csv"),
    "fact_sales": os.path.join(DATA_DIR, "fact_sales.csv"),
}

LOAD_ORDER = ["dim_product", "dim_customer", "dim_date", "fact_sales"]
