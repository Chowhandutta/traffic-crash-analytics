"""
generate_sample_data.py
------------------------
Creates a realistic synthetic Chicago-style traffic crash dataset so the
project runs end to end even before the real CSV is available.

The real dataset (Chicago Data Portal) has the SAME column names this script
produces, so swapping in the real file later requires no code changes.

Run:
    python generate_sample_data.py
Output:
    sample_crashes.csv  (~40,000 rows)
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible output

OUTPUT_FILE = "sample_crashes.csv"
NUM_ROWS = 40000

# ---- Reference value pools (weighted to look like real-world distributions) ----
WEATHER = (
    ["CLEAR"] * 70 + ["RAIN"] * 12 + ["SNOW"] * 6 + ["CLOUDY/OVERCAST"] * 8
    + ["FOG/SMOKE/HAZE"] * 2 + ["FREEZING RAIN/DRIZZLE"] * 2
)
CRASH_TYPE = (
    ["REAR END"] * 28 + ["SIDESWIPE SAME DIRECTION"] * 14 + ["TURNING"] * 18
    + ["ANGLE"] * 14 + ["PARKED MOTOR VEHICLE"] * 10 + ["FIXED OBJECT"] * 6
    + ["PEDESTRIAN"] * 4 + ["REAR TO FRONT"] * 6
)
LIGHTING = (
    ["DAYLIGHT"] * 60 + ["DARKNESS - LIGHTED ROAD"] * 25 + ["DARKNESS"] * 7
    + ["DUSK"] * 5 + ["DAWN"] * 3
)
TRAFFICWAY = (
    ["NOT DIVIDED"] * 40 + ["DIVIDED - W/MEDIAN (NOT RAISED)"] * 20
    + ["ONE-WAY"] * 15 + ["FOUR WAY"] * 10 + ["DIVIDED - W/MEDIAN BARRIER"] * 10
    + ["T-INTERSECTION"] * 5
)
TRAFFIC_CONTROL = (
    ["NO CONTROLS"] * 40 + ["TRAFFIC SIGNAL"] * 30 + ["STOP SIGN/FLASHER"] * 18
    + ["UNKNOWN"] * 7 + ["YIELD"] * 3 + ["PEDESTRIAN CROSSING SIGN"] * 2
)
PRIM_CAUSE = (
    ["UNABLE TO DETERMINE"] * 30 + ["FOLLOWING TOO CLOSELY"] * 14
    + ["FAILING TO YIELD RIGHT-OF-WAY"] * 12 + ["IMPROPER OVERTAKING/PASSING"] * 8
    + ["DRIVING SKILLS/KNOWLEDGE/EXPERIENCE"] * 8 + ["IMPROPER LANE USAGE"] * 7
    + ["DISTRACTION - FROM INSIDE VEHICLE"] * 7 + ["FAILING TO REDUCE SPEED"] * 6
    + ["DISREGARDING TRAFFIC SIGNALS"] * 5 + ["WEATHER"] * 3
)
SEC_CAUSE = PRIM_CAUSE + ["NOT APPLICABLE"] * 20
STREETS = [
    "WESTERN AVE", "PULASKI RD", "CICERO AVE", "ASHLAND AVE", "HALSTED ST",
    "STONY ISLAND AVE", "KEDZIE AVE", "MICHIGAN AVE", "STATE ST", "CLARK ST",
    "MILWAUKEE AVE", "ARCHER AVE", "BROADWAY", "DAMEN AVE", "CALIFORNIA AVE",
    "LAKE SHORE DR", "OGDEN AVE", "ELSTON AVE", "FULLERTON AVE", "DIVISION ST",
    "79TH ST", "63RD ST", "47TH ST", "ROOSEVELT RD", "IRVING PARK RD",
]
SPEED_LIMITS = [15, 20, 25, 30, 30, 30, 35, 35, 40, 45]

# Hours weighted toward morning (7-9) and evening (15-18) rush
HOUR_POOL = []
for h in range(24):
    if h in (7, 8, 15, 16, 17, 18):
        HOUR_POOL += [h] * 8
    elif h in (9, 10, 11, 12, 13, 14, 19, 20):
        HOUR_POOL += [h] * 5
    else:
        HOUR_POOL += [h] * 2

START = datetime(2015, 1, 1)
END = datetime(2024, 12, 31)
SPAN_DAYS = (END - START).days


def random_injuries():
    """~78% of crashes have no injuries; the rest scale down in severity."""
    roll = random.random()
    if roll < 0.78:
        return 0, 0, 0, 0
    fatal = 1 if random.random() < 0.004 else 0
    incap = random.choice([0, 0, 1, 1, 2]) if random.random() < 0.4 else 0
    nonincap = random.choice([0, 1, 1, 2, 3])
    total = fatal + incap + nonincap
    if total == 0:
        total = 1
        nonincap = 1
    return fatal, incap, nonincap, total


def main():
    header = [
        "CRASH_RECORD_ID", "CRASH_DATE", "POSTED_SPEED_LIMIT", "WEATHER_CONDITION",
        "LIGHTING_CONDITION", "FIRST_CRASH_TYPE", "TRAFFICWAY_TYPE",
        "TRAFFIC_CONTROL_DEVICE", "PRIM_CONTRIBUTORY_CAUSE", "SEC_CONTRIBUTORY_CAUSE",
        "INJURIES_FATAL", "INJURIES_INCAPACITATING", "INJURIES_NON_INCAPACITATING",
        "INJURIES_TOTAL", "CRASH_HOUR", "CRASH_DAY_OF_WEEK", "CRASH_MONTH",
        "BEAT_OF_OCCURRENCE", "STREET_NAME", "LATITUDE", "LONGITUDE",
        "DATE_POLICE_NOTIFIED", "year",
    ]

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(NUM_ROWS):
            crash_dt = START + timedelta(
                days=random.randint(0, SPAN_DAYS),
                hours=random.choice(HOUR_POOL),
                minutes=random.randint(0, 59),
            )
            hour = crash_dt.hour
            # SQLite/Chicago convention: 1 = Sunday ... 7 = Saturday
            day_of_week = (crash_dt.weekday() + 2) % 7 or 7
            fatal, incap, nonincap, total = random_injuries()
            lat = round(41.70 + random.random() * 0.30, 6)   # Chicago bounds
            lon = round(-87.85 + random.random() * 0.35, 6)
            notified = crash_dt + timedelta(minutes=random.randint(1, 120))
            writer.writerow([
                f"CR{i:08d}",
                crash_dt.strftime("%m/%d/%Y %I:%M:%S %p"),
                random.choice(SPEED_LIMITS),
                random.choice(WEATHER),
                random.choice(LIGHTING),
                random.choice(CRASH_TYPE),
                random.choice(TRAFFICWAY),
                random.choice(TRAFFIC_CONTROL),
                random.choice(PRIM_CAUSE),
                random.choice(SEC_CAUSE),
                fatal, incap, nonincap, total,
                hour, day_of_week, crash_dt.month,
                random.randint(100, 2535),
                random.choice(STREETS),
                lat, lon,
                notified.strftime("%m/%d/%Y %I:%M:%S %p"),
                crash_dt.year,
            ])

    print(f"Wrote {NUM_ROWS} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
