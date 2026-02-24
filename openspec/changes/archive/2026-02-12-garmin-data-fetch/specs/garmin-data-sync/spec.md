## ADDED Requirements

### Requirement: Full historical data sync

The system SHALL download and import all historical data from Garmin Connect for all enabled data types.

#### Scenario: Initial full sync execution
- **WHEN** user runs `garmindb_cli.py --all --download --import --analyze`
- **THEN** system SHALL download all monitoring files from configured start date to today
- **AND** system SHALL download all activity files from configured start date to today
- **AND** system SHALL download sleep, weight, and RHR data from configured start dates

#### Scenario: Data imported to SQLite databases
- **WHEN** download completes
- **THEN** system SHALL create/update SQLite databases in `~/HealthData/DBs/`
- **AND** `garmin.db` SHALL contain monitoring and daily summary data
- **AND** `garmin_activities.db` SHALL contain activity data with laps and records
- **AND** `garmin_summary.db` SHALL contain daily, weekly, monthly, yearly summaries

### Requirement: Incremental sync for ongoing updates

The system SHALL support incremental updates to fetch only new data since last sync.

#### Scenario: Incremental sync execution
- **WHEN** user runs `garmindb_cli.py --all --download --import --analyze --latest`
- **THEN** system SHALL only download data newer than last sync timestamp
- **AND** system SHALL import new data into existing databases

#### Scenario: Incremental sync is idempotent
- **WHEN** incremental sync is run multiple times with no new Garmin data
- **THEN** database content SHALL remain unchanged
- **AND** no duplicate records SHALL be created

### Requirement: Raw file preservation

The system SHALL preserve all downloaded raw files for data regeneration.

#### Scenario: FIT files retained
- **WHEN** monitoring or activity FIT files are downloaded
- **THEN** files SHALL be stored in `~/HealthData/FitFiles/`
- **AND** files SHALL not be deleted after import

#### Scenario: JSON files retained
- **WHEN** sleep, weight, or RHR JSON data is downloaded
- **THEN** files SHALL be stored in appropriate subdirectories under `~/HealthData/`
- **AND** files SHALL not be deleted after import

#### Scenario: Database regeneration from raw files
- **WHEN** user deletes database files and re-runs import
- **THEN** databases SHALL be fully regenerated from preserved raw files
- **AND** no re-download from Garmin Connect SHALL be required

### Requirement: Sync progress and statistics

The system SHALL provide visibility into sync progress and data completeness.

#### Scenario: Statistics file generated
- **WHEN** sync completes with `--analyze` flag
- **THEN** system SHALL generate `stats.txt` with data summary
- **AND** summary SHALL include date ranges of downloaded data
- **AND** summary SHALL include record counts per data type

#### Scenario: Log file for troubleshooting
- **WHEN** sync is executed
- **THEN** detailed logs SHALL be written to `garmindb.log`
- **AND** logs SHALL include any errors or warnings encountered
