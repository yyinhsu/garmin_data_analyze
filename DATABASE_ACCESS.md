# Accessing Garmin SQLite Databases

All databases are located at `./HealthData/DBs/`.

## 1. Command Line (sqlite3)

```bash
# Open a database
sqlite3 ./HealthData/DBs/garmin.db

# List all tables
.tables

# See table schema
.schema daily_summary

# Example queries
SELECT * FROM daily_summary ORDER BY day DESC LIMIT 10;
SELECT * FROM sleep ORDER BY day DESC LIMIT 10;
SELECT * FROM resting_hr ORDER BY day DESC LIMIT 10;
```

```bash
# Activities database
sqlite3 ./HealthData/DBs/garmin_activities.db
SELECT sport, COUNT(*) FROM activities GROUP BY sport;
```

```bash
# Monitoring (HR, steps, stress)
sqlite3 ./HealthData/DBs/garmin_monitoring.db
.tables
```

## 2. Python (in your venv)

```bash
source .venv/bin/activate
pip install pandas  # if not already installed
python
```

```python
import sqlite3
import pandas as pd
from pathlib import Path

db_dir = Path.home() / "HealthData" / "DBs"

# Load daily summaries
conn = sqlite3.connect(db_dir / "garmin.db")
df = pd.read_sql("SELECT * FROM daily_summary ORDER BY day DESC", conn)
print(df.head())
conn.close()

# Load activities
conn = sqlite3.connect(db_dir / "garmin_activities.db")
activities = pd.read_sql("SELECT * FROM activities ORDER BY start_time DESC", conn)
print(activities[['start_time', 'sport', 'distance', 'calories']].head(20))
conn.close()
```

## 3. VS Code SQLite Extension

Install the **SQLite Viewer** extension in VS Code, then open any `.db` file directly from `./HealthData/DBs/`.

## 4. Key Tables Reference

| Database | Table | What's in it |
|----------|-------|-------------|
| garmin.db | `daily_summary` | Steps, calories, distance per day |
| garmin.db | `sleep` | Sleep duration, deep/light/REM |
| garmin.db | `resting_hr` | Resting heart rate per day |
| garmin.db | `stress` | Stress level readings |
| garmin_activities.db | `activities` | All activities (sport, duration, HR, calories) |
| garmin_activities.db | `activity_records` | Second-by-second activity data |
| garmin_monitoring.db | `monitoring_hr` | Minute-by-minute heart rate |
| garmin_summary.db | `days_summary` | Aggregated daily stats |
