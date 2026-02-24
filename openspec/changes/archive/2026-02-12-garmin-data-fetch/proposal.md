## Why

I have a Garmin watch with years of health and activity data stored in Garmin Connect. I want to own my data locally, analyze it freely, and not be limited by Garmin's web interface. Using GarminDB, I can fetch all historical data across all available dimensions into SQLite databases for custom analysis.

## What Changes

- **Add GarminDB integration**: Set up and configure the GarminDB Python package to connect to Garmin Connect
- **Configure full historical fetch**: Set start dates to capture all-time history (not just recent data)
- **Enable all data dimensions**: Configure downloads for all available data types:
  - Daily monitoring (all-day heart rate, steps, stress, intensity minutes, floors climbed)
  - Sleep data (sleep stages, duration, quality scores)
  - Weight and body composition
  - Resting heart rate trends
  - Activities (runs, walks, cycling, swimming, etc. with detailed lap/record data)
  - Weekly, monthly, and yearly summaries
- **Store data locally**: Create SQLite databases with all parsed data for offline analysis
- **Preserve raw files**: Keep downloaded JSON and FIT files for data regeneration

## Capabilities

### New Capabilities

- `garmin-config`: Configuration setup for GarminDB including credentials and date ranges
- `garmin-data-sync`: Data fetching pipeline to download and import all Garmin data dimensions
- `garmin-data-schema`: SQLite database schema documentation for querying the imported data

### Modified Capabilities

<!-- No existing capabilities are being modified -->

## Impact

- **Dependencies**: Adds `garmindb` Python package and its dependencies
- **Storage**: SQLite databases will be created (size depends on data history length)
- **Credentials**: Requires Garmin Connect username/password stored in config file
- **Network**: Initial full sync may take time depending on years of history
- **File System**: Creates `~/.GarminDb/` directory for config and data storage
