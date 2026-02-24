## Why

Garmin health data is now available locally (601 days of sleep, daily summaries, stress, activities, heart rate). 26% of sleep records are rated POOR and 55% FAIR — understanding what factors correlate with poor sleep is the first step toward actionable health insights. This analysis serves as the foundation for a broader conversational health analysis platform.

## What Changes

- **Add sleep analysis notebook**: Jupyter notebook with exploratory data analysis correlating sleep quality/duration with other health metrics
- **Add analysis utilities**: Reusable data loading and visualization helpers for querying Garmin SQLite databases
- **Produce sleep correlation findings**: Statistical analysis identifying which factors (exercise timing/intensity, stress levels, step counts, resting HR, day of week) correlate with sleep deprivation
- **Generate visual reports**: Charts showing sleep trends, correlation heatmaps, and sleep-affecting factor breakdowns

## Capabilities

### New Capabilities

- `sleep-analysis`: Core sleep deprivation analysis — data loading, metric computation, correlation analysis, and visualization of sleep quality vs contributing factors
- `analysis-utils`: Reusable utilities for loading Garmin SQLite data into pandas DataFrames, common transformations, and shared plotting functions

### Modified Capabilities

<!-- No existing capabilities are being modified — this is a new analysis layer on top of existing data -->

## Impact

- **Dependencies**: Adds `pandas`, `matplotlib`, `seaborn`, `scipy`, `jupyter` to the Python environment
- **Files**: New `analysis/` directory with notebooks and utility modules
- **Data access**: Read-only queries against existing `HealthData/DBs/*.db` files
- **No changes** to GarminDB config, sync pipeline, or database schema
