#!/usr/bin/env python3
"""
check_data.py — Verify GarminDB data completeness.

Queries all SQLite databases in ~/HealthData/DBs/ and reports:
- Record counts per table
- Date ranges (min/max)
- Database file sizes
"""

import os
import sqlite3
import sys
from pathlib import Path


HEALTH_DATA_DIR = Path(__file__).resolve().parent / "HealthData"
DB_DIR = HEALTH_DATA_DIR / "DBs"

# Tables to check in each database, with their date column name
DB_TABLES = {
    "garmin.db": {
        "days_summary": "day",
        "sleep": "day",
        "weight": "day",
        "resting_heart_rate": "day",
        "stress": "day",
    },
    "garmin_monitoring.db": {
        "monitoring_hr": "timestamp",
        "monitoring_intensity": "timestamp",
        "monitoring_climb": "timestamp",
    },
    "garmin_activities.db": {
        "activities": "start_time",
        "activity_laps": "start_time",
        "activity_records": "timestamp",
    },
    "garmin_summary.db": {
        "weeks_summary": "first_day",
        "months_summary": "first_day",
        "years_summary": "first_day",
    },
}


def check_database(db_path: Path, tables: dict[str, str]) -> None:
    """Check a single database file."""
    if not db_path.exists():
        print(f"  MISSING: {db_path}")
        return

    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"  File: {db_path.name} ({size_mb:.1f} MB)")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all actual tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        actual_tables = {row[0] for row in cursor.fetchall()}

        for table, date_col in tables.items():
            if table not in actual_tables:
                print(f"    {table}: TABLE NOT FOUND")
                continue

            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]

            if count == 0:
                print(f"    {table}: 0 records")
                continue

            # Try to get date range
            try:
                cursor.execute(
                    f"SELECT MIN([{date_col}]), MAX([{date_col}]) FROM [{table}]"
                )
                min_date, max_date = cursor.fetchone()
                print(f"    {table}: {count:,} records ({min_date} to {max_date})")
            except sqlite3.OperationalError:
                print(f"    {table}: {count:,} records (date column '{date_col}' not found)")

        # Also list any tables we didn't explicitly check
        unchecked = actual_tables - set(tables.keys())
        if unchecked:
            print(f"    Other tables: {', '.join(sorted(unchecked))}")

        conn.close()
    except sqlite3.Error as e:
        print(f"    ERROR: {e}")


def main() -> None:
    print("=" * 60)
    print("GarminDB Data Verification Report")
    print("=" * 60)
    print()

    if not DB_DIR.exists():
        print(f"ERROR: Database directory not found: {DB_DIR}")
        print("Have you run 'garmindb_cli.py --all --download --import --analyze' yet?")
        sys.exit(1)

    for db_name, tables in DB_TABLES.items():
        db_path = DB_DIR / db_name
        print(f"\n[{db_name}]")
        check_database(db_path, tables)

    # Check stats file
    stats_file = HEALTH_DATA_DIR / "stats.txt"
    print(f"\n[Stats File]")
    if stats_file.exists():
        print(f"  {stats_file} exists ({stats_file.stat().st_size} bytes)")
    else:
        print(f"  {stats_file}: NOT FOUND")

    # List data directories
    print(f"\n[Data Directories]")
    if HEALTH_DATA_DIR.exists():
        for item in sorted(HEALTH_DATA_DIR.iterdir()):
            if item.is_dir():
                file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                print(f"  {item.name}/: {file_count} files")
    else:
        print(f"  {HEALTH_DATA_DIR}: NOT FOUND")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
