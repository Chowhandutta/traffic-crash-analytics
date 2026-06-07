# Traffic Crash Analytics & Safety Intelligence Platform

A SQL and Streamlit project that analyses Chicago traffic crash data to surface
road-safety insights: high-risk streets, peak crash times, dangerous conditions,
and crash trends over time.

Built with **Python, SQLite, Pandas, and Streamlit**. Every result shown in the
dashboard is queried live from the database (nothing is hardcoded) using advanced
SQL: CTEs, window functions (ROW_NUMBER, RANK, LAG, NTILE), a join, and CASE
expressions.

## Project structure

```
traffic_crash_analytics/
├── generate_sample_data.py   # creates a realistic synthetic CSV for testing
├── load_data.py              # loads the CSV into SQLite (table: CrashTable)
├── queries.py                # all 15 analytical queries (+1 bonus) as functions
├── app.py                    # Streamlit dashboard
├── requirements.txt
├── README.md
└── REPORT.md                 # written insights / project report
```

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Get the data. Two options:

   **Option A — use the real dataset (recommended for submission):**
   Download "Traffic Crashes - Crashes" from the Chicago Data Portal
   (data.cityofchicago.org) as CSV, save it in this folder, then load it:

   ```bash
   python load_data.py your_downloaded_file.csv
   ```

   **Option B — use synthetic sample data (to test the app immediately):**

   ```bash
   python generate_sample_data.py
   python load_data.py
   ```

   Either way this produces `crashes.db` with a table called `CrashTable`.

3. Run the dashboard:

   ```bash
   streamlit run app.py
   ```

   It opens at http://localhost:8501.

## Notes on columns

`load_data.py` is schema-flexible. It uppercases column names and, if
`CRASH_HOUR`, `CRASH_DAY_OF_WEEK`, `CRASH_MONTH`, or `year` are missing, derives
them from `CRASH_DATE`. Query 7 uses `TRAFFIC_CONTROL_DEVICE`; if your CSV names
that column differently, adjust the column name in `queries.py` (function `q7`).

## The 15 queries (+ bonus)

1. Top 5 dangerous weather + crash type combinations
2. Top 10 streets by injury crashes
3. Injury percentage per crash type
4. Peak crash hour for each month (ROW_NUMBER)
5. Top 5 night-time primary causes (hour >= 18)
6. Average injuries: daylight vs darkness
7. Traffic control device by average injuries per crash
8. Top 5 exact locations by crash frequency
9. Top 5 streets by injury rate, streets with >100 crashes (JOIN + HAVING)
10. Most common crash type per year (RANK)
11. Day of week with highest average crashes per hour
12. High-risk time slots by injury crashes (CASE bucketing)
13. Top 3 contributing causes per crash type (ROW_NUMBER)
14. Year-over-year crash growth rate (LAG)
15. Top 10 hotspot zones, rounded lat/long
16. (Bonus) Street risk quartiles (NTILE)
