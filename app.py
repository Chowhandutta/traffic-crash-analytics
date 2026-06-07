"""
app.py
------
Streamlit dashboard for the Traffic Crash Analytics & Safety Intelligence Platform.

Every table shown here is executed live from the SQLite database (crashes.db) via
queries.py -- nothing is hardcoded. Sidebar filters (year, weather) rebuild the
SQL WHERE clause and re-run all queries dynamically.

Run:
    streamlit run app.py
"""

import os
import sqlite3
import pandas as pd
import streamlit as st

import queries

DB_FILE = "crashes.db"

st.set_page_config(
    page_title="Traffic Crash Analytics & Safety Intelligence",
    page_icon="🚦",
    layout="wide",
)


@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


@st.cache_data
def get_filter_options():
    """Pull distinct years and weather conditions for the sidebar controls."""
    conn = get_connection()
    years = pd.read_sql_query(
        "SELECT DISTINCT year FROM CrashTable "
        "WHERE year IS NOT NULL ORDER BY year", conn
    )["year"].astype(str).tolist()
    weather = pd.read_sql_query(
        "SELECT DISTINCT WEATHER_CONDITION FROM CrashTable "
        "WHERE WEATHER_CONDITION IS NOT NULL ORDER BY WEATHER_CONDITION", conn
    )["WEATHER_CONDITION"].tolist()
    return years, weather


def build_where_clause(selected_years, selected_weather):
    """Turn sidebar selections into a safe SQL WHERE clause."""
    clauses = []
    if selected_years:
        year_list = ", ".join("'" + str(y).replace("'", "") + "'"
                              for y in selected_years)
        clauses.append(f"year IN ({year_list})")
    if selected_weather:
        w_list = ", ".join("'" + w.replace("'", "''") + "'"
                          for w in selected_weather)
        clauses.append(f"WEATHER_CONDITION IN ({w_list})")
    return " AND ".join(clauses) if clauses else "1=1"


def main():
    if not os.path.exists(DB_FILE):
        st.error(
            f"Database '{DB_FILE}' not found. Run `python load_data.py` first "
            "to build it from your CSV."
        )
        st.stop()

    conn = get_connection()

    st.title("🚦 Traffic Crash Analytics & Safety Intelligence Platform")
    st.caption(
        "All results are queried live from a SQLite database using advanced SQL "
        "(CTEs, window functions, joins). Use the sidebar to filter."
    )

    # ---------------- Sidebar filters ----------------
    years, weather = get_filter_options()
    st.sidebar.header("Filters")
    selected_years = st.sidebar.multiselect("Year", years, default=[])
    selected_weather = st.sidebar.multiselect("Weather condition", weather, default=[])
    where_clause = build_where_clause(selected_years, selected_weather)

    st.sidebar.markdown("---")
    st.sidebar.caption("Active SQL filter:")
    st.sidebar.code(where_clause, language="sql")

    # ---------------- Top-line metrics ----------------
    base = f"WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}) "
    total_crashes = pd.read_sql_query(
        base + "SELECT COUNT(*) AS n FROM base", conn)["n"].iloc[0]
    total_injuries = pd.read_sql_query(
        base + "SELECT COALESCE(SUM(INJURIES_TOTAL),0) AS n FROM base",
        conn)["n"].iloc[0]
    total_fatal = pd.read_sql_query(
        base + "SELECT COALESCE(SUM(INJURIES_FATAL),0) AS n FROM base",
        conn)["n"].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total crashes", f"{int(total_crashes):,}")
    c2.metric("Total injuries", f"{int(total_injuries):,}")
    c3.metric("Total fatalities", f"{int(total_fatal):,}")
    st.markdown("---")

    # ---------------- All queries ----------------
    for key, title, insight, fn in queries.QUERIES:
        st.subheader(title)
        try:
            df = fn(conn, where_clause)
            if df.empty:
                st.warning("No rows for the current filter selection.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"**Business insight:** {insight}")
        except Exception as e:
            st.error(f"Query failed: {e}")
        st.markdown("---")


if __name__ == "__main__":
    main()
