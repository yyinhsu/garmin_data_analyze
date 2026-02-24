## Context

This project needs to fetch personal health and fitness data from a Garmin watch via Garmin Connect. The GarminDB open-source project provides a mature, well-tested solution for this exact use case. It handles authentication, data download, FIT file parsing, and SQLite storage.

**Current state**: No local Garmin data exists. All data lives in Garmin Connect cloud.

**Constraints**:
- Garmin Connect requires authentication (no public API)
- Historical data volume could be large (years of daily monitoring + activities)
- Garmin may rate-limit or block excessive requests

## Goals / Non-Goals

**Goals:**
- Fetch complete historical data from Garmin Connect (all-time, not just recent)
- Capture all available data dimensions (monitoring, sleep, activities, weight, etc.)
- Store data in queryable SQLite databases
- Preserve raw files for data regeneration
- Enable incremental updates after initial sync

**Non-Goals:**
- Building a custom Garmin Connect API client (use GarminDB)
- Real-time sync or watch-to-PC direct transfer
- Data visualization (that's a separate concern)
- Modifying or extending GarminDB itself

## Decisions

### Decision 1: Use GarminDB pip package (not source clone)

**Choice**: Install via `pip install garmindb`

**Rationale**: 
- Simpler setup and maintenance
- Automatic dependency resolution
- Easy updates via `pip install --upgrade garmindb`

**Alternative considered**: Git clone with submodules
- More complex setup (`make setup`, SSH keys for submodules)
- Better for contributing to GarminDB, but we're just consuming it

### Decision 2: Configuration location at `~/.GarminDb/`

**Choice**: Use GarminDB's default config location

**Rationale**:
- Standard location expected by GarminDB CLI
- Keeps credentials separate from project repo (security)
- Config file: `~/.GarminDb/GarminConnectConfig.json`

### Decision 3: Fetch all data types in single command

**Choice**: Use `garmindb_cli.py --all --download --import --analyze`

**Rationale**:
- `--all` enables all data types (monitoring, activities, sleep, weight, rhr)
- Single command simplifies automation
- `--analyze` creates summary tables for easier querying

### Decision 4: Set historical start dates for full history

**Choice**: Configure start dates in `GarminConnectConfig.json` to earliest possible dates

**Rationale**:
- Default dates only fetch recent data
- Setting dates to when user first got Garmin device ensures complete history
- Can be conservative (e.g., 2015) - GarminDB handles missing data gracefully

### Decision 5: Database storage location

**Choice**: Use default `~/HealthData/` directory

**Rationale**:
- GarminDB default, well-documented
- Contains: `DBs/` (SQLite files), `FitFiles/`, `Activities/`
- Easy to backup entire directory

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Garmin blocks account for too many requests | Start with small date ranges, expand gradually; use `--latest` for incremental updates |
| Initial sync takes very long (hours) | Run overnight; data is resumable if interrupted |
| Credential exposure in config file | Keep `~/.GarminDb/` out of version control; use file permissions (chmod 600) |
| GarminDB version incompatibility | Pin version in requirements.txt; test updates before applying |
| Database corruption | Regular backups (`garmindb_cli.py --backup`); raw files allow regeneration |

## Migration Plan

1. **Setup** (one-time):
   - Install Python 3.x if not present
   - `pip install garmindb`
   - Create `~/.GarminDb/GarminConnectConfig.json` with credentials and dates

2. **Initial sync**:
   - Run `garmindb_cli.py --all --download --import --analyze`
   - Verify with `stats.txt` output
   - Adjust dates if data is missing, re-run

3. **Ongoing updates**:
   - Run `garmindb_cli.py --all --download --import --analyze --latest`
   - Schedule as cron job or run manually

4. **Rollback**:
   - Delete `~/HealthData/DBs/*.db` 
   - Re-run import from preserved raw files
