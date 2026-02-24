## Tasks

### garmin-config

- [x] Install Python 3.12 via Homebrew
- [x] Create Python venv at `.venv/` with Python 3.12
- [x] Install `garmindb` package via pip
- [x] Create `requirements.txt` pinning `garmindb>=3.6.7`
- [x] Create `~/.GarminDb/GarminConnectConfig.json` with credentials and date ranges
- [x] Set config file permissions to chmod 600
- [x] Configure `enabled_stats` with all data types enabled (monitoring, steps, itime, sleep, rhr, weight, activities)
- [x] Configure `directories.base_dir` to project-local `./HealthData/`

### garmin-data-sync

- [x] Run full historical download: `garmindb_cli.py --all --download --import --analyze`
- [x] Verify all 4 SQLite databases created with data (garmin.db, garmin_monitoring.db, garmin_activities.db, garmin_summary.db)
- [x] Verify raw FIT files preserved in `HealthData/FitFiles/`
- [x] Verify JSON files preserved (Sleep, Weight, RHR directories)
- [x] Create `sync_garmin.sh` script for incremental (`--latest`) and full re-downloads
- [x] Create `check_data.py` verification script to query all databases and report completeness

### garmin-data-schema

- [x] Create `DATABASE_ACCESS.md` documenting table locations and example queries
- [x] Verify key tables populated: activities (615), sleep (601), resting_hr (588), monitoring_hr (658K), daily_summary (601)

### Project setup

- [x] Create `.gitignore` excluding `.venv/`, `HealthData/`, logs, credentials, `__pycache__/`
