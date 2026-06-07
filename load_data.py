"""
load_data.py
------------
Loads the traffic crash CSV into a SQLite database table called CrashTable.

Works with either:
  - sample_crashes.csv  (from generate_sample_data.py), or
  - the real Chicago Traffic Crashes export (same column names).

It is schema-flexible: it loads whatever columns the CSV contains, normalizes
the column names to UPPERCASE, and derives CRASH_HOUR / CRASH_DAY_OF_WEEK /
CRASH_MONTH / year from CRASH_DATE if those columns are missing.

Run:
    python load_data.py                 # uses sample_crashes.csv
    python load_data.py my_file.csv     # uses a custom CSV
Output:
    crashes.db  (SQLite database, table = CrashTable)
"""

import sys
import sqlite3
import pandas as pd

DB_FILE = "crashes.db"
TABLE_NAME = "CrashTable"
DEFAULT_CSV = "sample_crashes.csv"
CHUNK = 50000  # read large CSVs in chunks to stay memory-safe


def normalize_columns(df):
    """Uppercase and strip column names so queries can rely on a fixed schema."""
    df.columns = [c.strip().upper() if c.strip().lower() != "year" else "year"
                  for c in df.columns]
    return df


def add_derived_columns(df):
    """Create time columns from CRASH_DATE only if they are not already present."""
    if "CRASH_DATE" not in df.columns:
        return df
    parsed = pd.to_datetime(df["CRASH_DATE"], errors="coerce")
    if "CRASH_HOUR" not in df.columns:
        df["CRASH_HOUR"] = parsed.dt.hour
    if "CRASH_MONTH" not in df.columns:
        df["CRASH_MONTH"] = parsed.dt.month
    if "CRASH_DAY_OF_WEEK" not in df.columns:
        # 1 = Sunday ... 7 = Saturday (Chicago/SQLite convention)
        df["CRASH_DAY_OF_WEEK"] = (parsed.dt.weekday + 2) % 7
        df.loc[df["CRASH_DAY_OF_WEEK"] == 0, "CRASH_DAY_OF_WEEK"] = 7
    if "year" not in df.columns:
        df["year"] = parsed.dt.year.astype("Int64").astype(str)
    return df


def load(csv_path):
    print(f"Loading '{csv_path}' into '{DB_FILE}' (table: {TABLE_NAME}) ...")
    conn = sqlite3.connect(DB_FILE)
    # Fresh load each run
    conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()

    total = 0
    first_chunk = True
    for chunk in pd.read_csv(csv_path, chunksize=CHUNK, low_memory=False):
        chunk = normalize_columns(chunk)
        chunk = add_derived_columns(chunk)
        chunk.to_sql(
            TABLE_NAME, conn,
            if_exists="replace" if first_chunk else "append",
            index=False,
        )
        first_chunk = False
        total += len(chunk)
        print(f"  ... {total} rows loaded")

    # Indexes for faster grouping/filtering on common query columns
    for col in ("year", "STREET_NAME", "FIRST_CRASH_TYPE",
                "WEATHER_CONDITION", "CRASH_HOUR"):
        try:
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{col.lower()} "
                f"ON {TABLE_NAME}('{col}')"
            )
        except sqlite3.OperationalError:
            pass  # column not present in this CSV
    conn.commit()

    # Verification summary
    rows = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({TABLE_NAME})")]
    print("\nLoad complete.")
    print(f"  Row count : {rows}")
    print(f"  Columns   : {len(cols)}")
    print(f"  Schema    : {', '.join(cols)}")
    conn.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    load(path)
