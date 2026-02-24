## ADDED Requirements

### Requirement: Database connection management

The analysis-utils module SHALL provide functions for connecting to Garmin SQLite databases.

#### Scenario: Database paths resolved automatically
- **WHEN** a utility function is called to load data
- **THEN** it SHALL resolve database paths relative to the project root (`HealthData/DBs/`)
- **AND** it SHALL support garmin.db, garmin_activities.db, garmin_monitoring.db, and garmin_summary.db

#### Scenario: Database connection errors handled
- **WHEN** a database file does not exist at the expected path
- **THEN** the function SHALL raise a clear error message indicating which database is missing
- **AND** the error message SHALL include the expected path

### Requirement: Sleep data loading utility

The module SHALL provide a function to load sleep data joined with daily context metrics.

#### Scenario: Load sleep data with daily metrics
- **WHEN** `load_sleep_data()` is called
- **THEN** it SHALL return a pandas DataFrame with columns from the `sleep` table
- **AND** it SHALL join with `daily_summary` on the date column
- **AND** it SHALL join with `resting_hr` on the date column
- **AND** date columns SHALL be parsed as datetime types
- **AND** duration columns SHALL be converted to hours (float) for analysis

#### Scenario: Column naming is consistent
- **WHEN** tables are joined
- **THEN** overlapping column names SHALL be disambiguated with table prefixes (e.g., `sleep_` or `daily_`)
- **AND** the returned DataFrame SHALL have descriptive, snake_case column names

### Requirement: Activity data loading utility

The module SHALL provide a function to load activity data with timing classification.

#### Scenario: Load activities with timing buckets
- **WHEN** `load_activities()` is called
- **THEN** it SHALL return a pandas DataFrame with activity records from garmin_activities.db
- **AND** each activity SHALL have a `time_bucket` column: "Morning" (before 12:00), "Afternoon" (12:00–17:00), "Evening" (17:00–20:00), "Late Night" (after 20:00)
- **AND** each activity SHALL have a `date` column (date of the activity, for joining with sleep data)

#### Scenario: Activity types with small samples grouped
- **WHEN** `load_activities(group_rare=True)` is called with grouping enabled
- **THEN** sport types with fewer than 10 sessions SHALL be relabeled as "Other"

### Requirement: Sleep deprivation classification utility

The module SHALL provide a function to classify sleep records as deprived or adequate.

#### Scenario: Classification applied to DataFrame
- **WHEN** `classify_sleep(df)` is called with a sleep DataFrame
- **THEN** it SHALL add a boolean column `is_deprived` where True means sleep deprived
- **AND** the criteria SHALL be: sleep score < 60 OR qualifier == "POOR" OR total sleep < 6 hours
- **AND** it SHALL add a categorical column `sleep_quality` with values "Deprived" or "Adequate"

### Requirement: Shared plotting functions

The module SHALL provide reusable plotting helper functions with consistent styling.

#### Scenario: Plot style configured
- **WHEN** any plotting function is called
- **THEN** it SHALL apply a consistent seaborn theme
- **AND** figures SHALL use readable font sizes (title ≥ 14pt, labels ≥ 12pt)
- **AND** figures SHALL have proper axis labels and titles

#### Scenario: Correlation heatmap helper
- **WHEN** `plot_correlation_heatmap(df, columns)` is called
- **THEN** it SHALL compute Spearman correlation matrix for the specified columns
- **AND** it SHALL render an annotated heatmap with correlation coefficients
- **AND** it SHALL return the correlation matrix and p-value matrix as DataFrames

#### Scenario: Group comparison plot helper
- **WHEN** `plot_group_comparison(df, group_col, metric_cols)` is called
- **THEN** it SHALL produce box plots or violin plots comparing metric distributions across groups
- **AND** it SHALL annotate each plot with the Mann-Whitney U test p-value

#### Scenario: Time series plot helper
- **WHEN** `plot_time_series(df, date_col, value_col, rolling_windows)` is called
- **THEN** it SHALL plot the raw values as a line chart
- **AND** it SHALL overlay rolling averages for each specified window size
- **AND** it SHALL include a legend distinguishing raw values from each rolling average

### Requirement: Statistical test utilities

The module SHALL provide helper functions for common statistical tests used in the analysis.

#### Scenario: Correlation with p-values
- **WHEN** `compute_correlations(df, target_col, feature_cols)` is called
- **THEN** it SHALL return a DataFrame with Spearman correlation coefficient and p-value for each feature
- **AND** results SHALL be sorted by absolute correlation strength
- **AND** a column SHALL indicate statistical significance (p < 0.05)

#### Scenario: Group comparison test
- **WHEN** `compare_groups(df, group_col, metric_col)` is called
- **THEN** it SHALL run Mann-Whitney U test between groups
- **AND** it SHALL return test statistic, p-value, and effect size (rank-biserial correlation)
- **AND** it SHALL return group means and medians

### Requirement: Data completeness reporting

The module SHALL provide a function to report data completeness for analysis columns.

#### Scenario: Completeness report generated
- **WHEN** `report_completeness(df, columns)` is called
- **THEN** it SHALL return a summary showing for each column: total count, non-null count, null count, and completeness percentage
- **AND** it SHALL flag columns with less than 80% completeness as potentially unreliable
