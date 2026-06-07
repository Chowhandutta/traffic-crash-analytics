# Project Report: Traffic Crash Analytics & Safety Intelligence Platform

## 1. Objective

Analyse a large structured dataset of Chicago traffic crashes using SQL to find
patterns, risk factors, and trends, then present the results in an interactive
Streamlit dashboard with a business insight attached to each query.

## 2. Approach

- **Phase 1 — Loading:** `load_data.py` reads the CSV in chunks and writes it to
  a SQLite database (`crashes.db`, table `CrashTable`). Column names are
  normalised and time columns are derived from `CRASH_DATE` if absent. Indexes
  are added on the most-queried columns for speed.
- **Phase 2 — Exploration:** basic COUNT / GROUP BY / ORDER BY queries to confirm
  distributions of crash type, weather, lighting, and hour.
- **Phase 3 — Advanced SQL:** 15 analytical queries (plus one bonus) in
  `queries.py`. Each query is a function that accepts an optional WHERE clause so
  the dashboard filters reuse the same SQL. Advanced concepts used:
  - **CTEs:** every query uses a `base` CTE to apply filters once.
  - **Window functions:** ROW_NUMBER (Q4, Q13), RANK (Q10), LAG (Q14), NTILE (bonus).
  - **Join:** Q9 joins per-street stats against a city-wide average.
  - **Conditional aggregation / CASE:** injury-rate and time-slot bucketing.
  - **HAVING:** Q9 keeps only streets with more than 100 crashes.
- **Phase 4 — Streamlit:** `app.py` runs each query live against the database and
  shows a title, a table (`st.dataframe`), and a one-line business insight.
  Sidebar filters for year and weather rebuild the SQL WHERE clause dynamically.

## 3. Key insight categories (interpretation guide)

The exact numbers depend on the dataset loaded. With the real Chicago data,
expect to read the outputs like this:

- **High-risk streets (Q2, Q9):** major arterial roads dominate injury crashes by
  volume, but the *injury rate* query separates merely-busy streets from
  genuinely dangerous ones, which is the better target for engineering fixes.
- **Peak times (Q4, Q11, Q12):** crashes concentrate around morning and evening
  rush hours; the time-slot query identifies the single bucket carrying the most
  injuries, which is where enforcement and ambulance readiness pay off most.
- **Dangerous conditions (Q1, Q6, Q7):** weather/crash-type pairings and lighting
  comparisons show whether bad weather and darkness raise crash frequency and
  severity, justifying lighting and signage investment.
- **Causes (Q5, Q13):** a small number of contributory causes (following too
  closely, failure to yield, distraction) drive most crashes, so prevention
  campaigns can be tightly targeted.
- **Trends (Q10, Q14):** the year-over-year growth rate is the headline safety
  metric; the per-year dominant crash type shows whether the core problem is
  shifting over time.
- **Hotspots (Q8, Q15, bonus):** exact points and rounded zones pinpoint where to
  send site audits, while the NTILE quartiles give a simple funding-priority tier.

## 4. Deliverables

- Python source: `generate_sample_data.py`, `load_data.py`, `queries.py`, `app.py`
- SQLite database: `crashes.db` (table `CrashTable`)
- Streamlit dashboard showing all query outputs in table format with insights
- `README.md` with setup steps and `REPORT.md` (this file)

## 5. How to run

See `README.md`. In short: install requirements, load a CSV with `load_data.py`,
then `streamlit run app.py`.
