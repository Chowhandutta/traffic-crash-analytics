"""
queries.py
----------
All analytical SQL queries for the Traffic Crash Analytics project.

Design notes:
  - Every query is a function that takes a sqlite3 connection and an optional
    `where_clause` (default "1=1") so the Streamlit sidebar can apply filters
    (e.g. year, weather) WITHOUT duplicating SQL.
  - Each query opens with a `base` CTE that applies the filter once, then all
    aggregation runs against `base`. This keeps the queries reusable and is also
    a clean demonstration of CTEs.
  - Advanced SQL used: CTEs, window functions (ROW_NUMBER, RANK, LAG, NTILE),
    a JOIN, CASE expressions, conditional aggregation, and HAVING.

Each entry in QUERIES has:
    key, title, insight (short business takeaway), and run(conn, where_clause).
"""

import pandas as pd


def _df(conn, sql):
    return pd.read_sql_query(sql, conn)


# 1. Top 5 weather + crash type combinations by total crashes
def q1(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT WEATHER_CONDITION,
           FIRST_CRASH_TYPE,
           COUNT(*) AS total_crashes
    FROM base
    GROUP BY WEATHER_CONDITION, FIRST_CRASH_TYPE
    ORDER BY total_crashes DESC
    LIMIT 5;
    """
    return _df(conn, sql)


# 2. Top 10 streets by number of injury crashes
def q2(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT STREET_NAME,
           COUNT(*) AS injury_crashes
    FROM base
    WHERE INJURIES_TOTAL > 0
    GROUP BY STREET_NAME
    ORDER BY injury_crashes DESC
    LIMIT 10;
    """
    return _df(conn, sql)


# 3. Percentage of crashes resulting in injuries, per crash type
def q3(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT FIRST_CRASH_TYPE,
           COUNT(*) AS total_crashes,
           SUM(CASE WHEN INJURIES_TOTAL > 0 THEN 1 ELSE 0 END) AS injury_crashes,
           ROUND(100.0 * SUM(CASE WHEN INJURIES_TOTAL > 0 THEN 1 ELSE 0 END)
                 / COUNT(*), 2) AS injury_percentage
    FROM base
    GROUP BY FIRST_CRASH_TYPE
    ORDER BY injury_percentage DESC;
    """
    return _df(conn, sql)


# 4. Peak crash hour for each month  (ROW_NUMBER window function)
def q4(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}),
    hourly AS (
        SELECT CRASH_MONTH, CRASH_HOUR, COUNT(*) AS crashes
        FROM base
        GROUP BY CRASH_MONTH, CRASH_HOUR
    ),
    ranked AS (
        SELECT CRASH_MONTH, CRASH_HOUR, crashes,
               ROW_NUMBER() OVER (PARTITION BY CRASH_MONTH
                                  ORDER BY crashes DESC) AS rn
        FROM hourly
    )
    SELECT CRASH_MONTH, CRASH_HOUR AS peak_hour, crashes
    FROM ranked
    WHERE rn = 1
    ORDER BY CRASH_MONTH;
    """
    return _df(conn, sql)


# 5. Top 5 primary causes of crashes at night (CRASH_HOUR >= 18)
def q5(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT PRIM_CONTRIBUTORY_CAUSE,
           COUNT(*) AS crashes
    FROM base
    WHERE CRASH_HOUR >= 18
    GROUP BY PRIM_CONTRIBUTORY_CAUSE
    ORDER BY crashes DESC
    LIMIT 5;
    """
    return _df(conn, sql)


# 6. Average injuries: daylight vs darkness
def q6(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT CASE
               WHEN LIGHTING_CONDITION = 'DAYLIGHT' THEN 'Daylight'
               WHEN LIGHTING_CONDITION LIKE 'DARKNESS%' THEN 'Darkness'
               ELSE 'Other (Dawn/Dusk/Unknown)'
           END AS light_group,
           COUNT(*) AS crashes,
           ROUND(AVG(INJURIES_TOTAL), 3) AS avg_injuries
    FROM base
    GROUP BY light_group
    ORDER BY avg_injuries DESC;
    """
    return _df(conn, sql)


# 7. Traffic control device with highest average injuries per crash
def q7(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT TRAFFIC_CONTROL_DEVICE,
           COUNT(*) AS crashes,
           ROUND(AVG(INJURIES_TOTAL), 3) AS avg_injuries
    FROM base
    GROUP BY TRAFFIC_CONTROL_DEVICE
    ORDER BY avg_injuries DESC;
    """
    return _df(conn, sql)


# 8. Top 5 exact locations (lat/long) by crash frequency
def q8(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT LATITUDE, LONGITUDE,
           COUNT(*) AS crashes
    FROM base
    WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
    GROUP BY LATITUDE, LONGITUDE
    ORDER BY crashes DESC
    LIMIT 5;
    """
    return _df(conn, sql)


# 9. Top 5 streets by injury rate (only streets with > 100 crashes)  -- uses a JOIN
def q9(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}),
    street_stats AS (
        SELECT STREET_NAME,
               COUNT(*) AS total_crashes,
               SUM(CASE WHEN INJURIES_TOTAL > 0 THEN 1 ELSE 0 END) AS injury_crashes
        FROM base
        GROUP BY STREET_NAME
        HAVING COUNT(*) > 100
    ),
    city AS (
        SELECT ROUND(100.0 * SUM(CASE WHEN INJURIES_TOTAL > 0 THEN 1 ELSE 0 END)
                     / COUNT(*), 2) AS city_injury_rate_pct
        FROM base
    )
    SELECT s.STREET_NAME,
           s.total_crashes,
           s.injury_crashes,
           ROUND(100.0 * s.injury_crashes / s.total_crashes, 2) AS injury_rate_pct,
           c.city_injury_rate_pct
    FROM street_stats s
    JOIN city c
    ORDER BY injury_rate_pct DESC
    LIMIT 5;
    """
    return _df(conn, sql)


# 10. Most common crash type per year  (RANK window function)
def q10(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}),
    yearly AS (
        SELECT year, FIRST_CRASH_TYPE, COUNT(*) AS crashes
        FROM base
        GROUP BY year, FIRST_CRASH_TYPE
    ),
    ranked AS (
        SELECT year, FIRST_CRASH_TYPE, crashes,
               RANK() OVER (PARTITION BY year ORDER BY crashes DESC) AS rnk
        FROM yearly
    )
    SELECT year, FIRST_CRASH_TYPE AS most_common_crash_type, crashes
    FROM ranked
    WHERE rnk = 1
    ORDER BY year;
    """
    return _df(conn, sql)


# 11. Day of week with highest average crashes per hour
def q11(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}),
    per_hour AS (
        SELECT CRASH_DAY_OF_WEEK, CRASH_HOUR, COUNT(*) AS crashes
        FROM base
        GROUP BY CRASH_DAY_OF_WEEK, CRASH_HOUR
    )
    SELECT CRASH_DAY_OF_WEEK,
           CASE CRASH_DAY_OF_WEEK
                WHEN 1 THEN 'Sunday'  WHEN 2 THEN 'Monday'
                WHEN 3 THEN 'Tuesday' WHEN 4 THEN 'Wednesday'
                WHEN 5 THEN 'Thursday' WHEN 6 THEN 'Friday'
                WHEN 7 THEN 'Saturday' END AS day_name,
           ROUND(AVG(crashes), 2) AS avg_crashes_per_hour
    FROM per_hour
    GROUP BY CRASH_DAY_OF_WEEK
    ORDER BY avg_crashes_per_hour DESC;
    """
    return _df(conn, sql)


# 12. High-risk time slots: bucket hours, find bucket with most injury crashes
def q12(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT CASE
               WHEN CRASH_HOUR BETWEEN 5 AND 11 THEN 'Morning (05-11)'
               WHEN CRASH_HOUR BETWEEN 12 AND 16 THEN 'Afternoon (12-16)'
               WHEN CRASH_HOUR BETWEEN 17 AND 20 THEN 'Evening (17-20)'
               ELSE 'Night (21-04)'
           END AS time_slot,
           COUNT(*) AS total_crashes,
           SUM(CASE WHEN INJURIES_TOTAL > 0 THEN 1 ELSE 0 END) AS injury_crashes
    FROM base
    GROUP BY time_slot
    ORDER BY injury_crashes DESC;
    """
    return _df(conn, sql)


# 13. Top 3 contributing causes per crash type  (ROW_NUMBER window function)
def q13(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}),
    cause_counts AS (
        SELECT FIRST_CRASH_TYPE, PRIM_CONTRIBUTORY_CAUSE, COUNT(*) AS crashes
        FROM base
        GROUP BY FIRST_CRASH_TYPE, PRIM_CONTRIBUTORY_CAUSE
    ),
    ranked AS (
        SELECT FIRST_CRASH_TYPE, PRIM_CONTRIBUTORY_CAUSE, crashes,
               ROW_NUMBER() OVER (PARTITION BY FIRST_CRASH_TYPE
                                  ORDER BY crashes DESC) AS rn
        FROM cause_counts
    )
    SELECT FIRST_CRASH_TYPE, PRIM_CONTRIBUTORY_CAUSE,
           crashes, rn AS rank_within_type
    FROM ranked
    WHERE rn <= 3
    ORDER BY FIRST_CRASH_TYPE, rn;
    """
    return _df(conn, sql)


# 14. Year-over-year crash growth rate  (LAG window function)
def q14(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}),
    yearly AS (
        SELECT year, COUNT(*) AS crashes
        FROM base
        GROUP BY year
    ),
    with_lag AS (
        SELECT year, crashes,
               LAG(crashes) OVER (ORDER BY year) AS prev_year_crashes
        FROM yearly
    )
    SELECT year, crashes, prev_year_crashes,
           CASE WHEN prev_year_crashes IS NULL THEN NULL
                ELSE ROUND(100.0 * (crashes - prev_year_crashes)
                           / prev_year_crashes, 2)
           END AS yoy_growth_pct
    FROM with_lag
    ORDER BY year;
    """
    return _df(conn, sql)


# 15. Hotspot zones: round lat/long to 2 decimals, top 10 zones
def q15(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause})
    SELECT ROUND(LATITUDE, 2) AS lat_zone,
           ROUND(LONGITUDE, 2) AS lon_zone,
           COUNT(*) AS crashes
    FROM base
    WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
    GROUP BY lat_zone, lon_zone
    ORDER BY crashes DESC
    LIMIT 10;
    """
    return _df(conn, sql)


# 16 (BONUS). Rank streets into risk quartiles  (NTILE window function)
def q16(conn, where_clause="1=1"):
    sql = f"""
    WITH base AS (SELECT * FROM CrashTable WHERE {where_clause}),
    street_stats AS (
        SELECT STREET_NAME, COUNT(*) AS total_crashes
        FROM base
        GROUP BY STREET_NAME
    )
    SELECT STREET_NAME, total_crashes,
           NTILE(4) OVER (ORDER BY total_crashes DESC) AS risk_quartile
    FROM street_stats
    ORDER BY total_crashes DESC;
    """
    return _df(conn, sql)


# Registry consumed by the Streamlit app and the test runner
QUERIES = [
    ("q1",  "1. Top 5 Dangerous Weather + Crash Type Combinations",
     "These weather/collision pairings produce the most crashes, so authorities can pre-position resources before bad weather and insurers can price these risk patterns.",
     q1),
    ("q2",  "2. Top 10 Streets by Injury Crashes",
     "These corridors carry the heaviest injury burden and are the highest-priority candidates for engineering fixes, enforcement, and ambulance staging.",
     q2),
    ("q3",  "3. Injury Percentage by Crash Type",
     "Crash types with a high injury percentage are the most harmful per event, even if they are not the most frequent, which helps prioritise prevention campaigns.",
     q3),
    ("q4",  "4. Peak Crash Hour for Each Month",
     "Knowing the riskiest hour in each month lets traffic police and emergency services schedule patrols and shifts around predictable monthly peaks.",
     q4),
    ("q5",  "5. Top 5 Primary Causes at Night (Hour >= 18)",
     "Night-time crashes cluster around a few causes, so targeted interventions like lighting, signage, and DUI enforcement can address most of them.",
     q5),
    ("q6",  "6. Average Injuries: Daylight vs Darkness",
     "Comparing average injury counts shows whether darkness raises crash severity, informing investment in street lighting and reflective infrastructure.",
     q6),
    ("q7",  "7. Traffic Control Device by Average Injuries per Crash",
     "Device types linked to higher average injuries flag intersections where the existing control may be inadequate and an upgrade could reduce harm.",
     q7),
    ("q8",  "8. Top 5 Exact Locations by Crash Frequency",
     "These precise GPS points are repeat-offender spots that warrant a site-level safety audit such as signal timing or sightline fixes.",
     q8),
    ("q9",  "9. Top 5 Streets by Injury Rate (>100 crashes)",
     "Filtering out low-volume streets surfaces corridors that are not just busy but disproportionately injurious versus the city average shown alongside.",
     q9),
    ("q10", "10. Most Common Crash Type per Year",
     "Tracking the dominant crash type each year reveals whether the city's main safety problem is shifting and whether past interventions worked.",
     q10),
    ("q11", "11. Day of Week with Highest Average Crashes per Hour",
     "The busiest day per hour helps balance patrol rosters and emergency staffing across the week rather than spreading them evenly.",
     q11),
    ("q12", "12. High-Risk Time Slots by Injury Crashes",
     "The time bucket with the most injury crashes is where added enforcement and rapid-response readiness will save the most lives.",
     q12),
    ("q13", "13. Top 3 Contributing Causes per Crash Type",
     "Pairing each crash type with its leading causes tells planners exactly which behaviour to target for each kind of collision.",
     q13),
    ("q14", "14. Year-over-Year Crash Growth Rate",
     "The YoY trend shows whether crashes are rising or falling, which is the headline metric for evaluating overall road-safety policy.",
     q14),
    ("q15", "15. Top 10 Hotspot Zones (rounded lat/long)",
     "Grouping nearby crashes into zones highlights broad problem areas for neighbourhood-level planning, not just single intersections.",
     q15),
    ("q16", "Bonus. Street Risk Quartiles (NTILE)",
     "Quartile 1 streets are the most crash-prone 25 percent and should receive the first wave of safety funding.",
     q16),
]
