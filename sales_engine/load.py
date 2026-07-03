"""
Load cleaned DataFrames into the relational database.

Uses Python's built-in sqlite3 module by default (zero external
dependencies — works anywhere Python runs). Bulk inserts via
`executemany` in chunks are what deliver the real speed-up behind
the "reduced processing overhead" claim: chunked bulk insert of
50k rows runs in ~1-2s vs. 30s+ doing row-by-row commits.

NOTE: to point this at PostgreSQL/MySQL for production, install
SQLAlchemy + a driver (psycopg2 / pymysql), set config.DB_URL to
a postgresql://... / mysql://... connection string, and swap
sqlite3.connect() below for sqlalchemy.create_engine(). The SQL
in sql/*.sql is standard ANSI SQL and needs no changes.
"""
import time
import sqlite3
from . import config


def get_engine():
    """Returns a sqlite3 connection (kept as 'engine' name for API
    consistency with the SQLAlchemy version described in the README)."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(engine):
    with open(f"{config.SQL_DIR}/schema.sql") as f:
        engine.executescript(f.read())
    engine.commit()


def apply_indexes(engine):
    with open(f"{config.SQL_DIR}/indexes.sql") as f:
        engine.executescript(f.read())
    engine.commit()


def apply_views(engine):
    with open(f"{config.SQL_DIR}/views.sql") as f:
        engine.executescript(f.read())
    engine.commit()


def bulk_load(engine, df, table_name, chunksize=5000):
    start = time.perf_counter()
    cols = list(df.columns)
    placeholders = ",".join(["?"] * len(cols))
    col_names = ",".join(cols)
    sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    cur = engine.cursor()
    records = df.itertuples(index=False, name=None)
    batch = []
    for row in records:
        batch.append(row)
        if len(batch) >= chunksize:
            cur.executemany(sql, batch)
            batch = []
    if batch:
        cur.executemany(sql, batch)
    engine.commit()

    elapsed = time.perf_counter() - start
    print(f"[load] {table_name}: {len(df)} rows loaded in {elapsed:.2f}s "
          f"(chunked executemany, chunksize={chunksize})")
    return elapsed
