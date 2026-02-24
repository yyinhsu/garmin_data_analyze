## ADDED Requirements

### Requirement: Sleep data loading and preparation

The system SHALL load sleep data from garmin.db and prepare it for analysis by joining with related daily metrics.

#### Scenario: Sleep records loaded with daily context
- **WHEN** the sleep analysis notebook is executed
- **THEN** system SHALL load all records from the `sleep` table in garmin.db
- **AND** system SHALL join sleep records with `daily_summary` on the same date
- **AND** system SHALL join with `resting_hr` on the same date
- **AND** the resulting DataFrame SHALL contain sleep duration, sleep stages (deep, light, REM, awake), sleep score, qualifier, and daily metrics (steps, calories, stress avg, resting HR, body battery)

#### Scenario: Missing data handled gracefully
- **WHEN** sleep records have NULL values for score, qualifier, or sleep stages
- **THEN** system SHALL retain the record with NaN values (not drop it)
- **AND** each analysis section SHALL filter NaN rows relevant to that specific analysis
- **AND** system SHALL report data completeness (count of non-null values per column)

### Requirement: Sleep deprivation classification

The system SHALL classify each sleep record as "sleep deprived" or "adequate" based on defined thresholds.

#### Scenario: Sleep deprivation definition applied
- **WHEN** sleep records are classified
- **THEN** a record SHALL be marked as "sleep deprived" if sleep score < 60
- **OR** if qualifier is "POOR"
- **OR** if total sleep duration < 6 hours
- **AND** all other records SHALL be marked as "adequate"

#### Scenario: Classification summary reported
- **WHEN** classification is complete
- **THEN** system SHALL display the count and percentage of deprived vs adequate nights
- **AND** system SHALL display a distribution chart of sleep scores with the threshold marked

### Requirement: Correlation analysis between sleep quality and daytime metrics

The system SHALL compute correlations between sleep quality metrics and same-day daytime factors.

#### Scenario: Correlation matrix generated
- **WHEN** correlation analysis is executed
- **THEN** system SHALL compute Spearman rank correlation between sleep score and: steps, calories, stress avg, resting HR, body battery, floors climbed, active minutes
- **AND** system SHALL display a correlation heatmap visualization
- **AND** system SHALL report correlation coefficients with p-values

#### Scenario: Statistically significant correlations highlighted
- **WHEN** correlation results are displayed
- **THEN** correlations with p-value < 0.05 SHALL be highlighted
- **AND** system SHALL rank factors by absolute correlation strength

### Requirement: Group comparison between deprived and adequate sleep

The system SHALL compare daytime metrics between sleep-deprived and adequate sleep nights using statistical tests.

#### Scenario: Group means compared
- **WHEN** group comparison is executed
- **THEN** system SHALL compute mean and median of each daytime metric for deprived vs adequate groups
- **AND** system SHALL run Mann-Whitney U test for each metric
- **AND** system SHALL display results with p-values and effect sizes
- **AND** system SHALL produce box plot or violin plot visualizations for each compared metric

#### Scenario: Minimum sample size enforced
- **WHEN** a group has fewer than 10 records
- **THEN** system SHALL display a warning that results may not be reliable
- **AND** system SHALL still compute and display the results with the caveat noted

### Requirement: Activity timing and sleep quality analysis

The system SHALL analyze how exercise timing and intensity relate to subsequent sleep quality.

#### Scenario: Activities bucketed by time of day
- **WHEN** activity timing analysis is executed
- **THEN** system SHALL load activities from garmin_activities.db
- **AND** system SHALL categorize each activity into: Morning (before 12:00), Afternoon (12:00–17:00), Evening (17:00–20:00), Late Night (after 20:00)
- **AND** system SHALL join activity data with that night's sleep record

#### Scenario: Sleep quality compared across activity timing buckets
- **WHEN** bucketed activity data is available
- **THEN** system SHALL compare average sleep score across timing buckets
- **AND** system SHALL compare sleep score on exercise days vs rest days
- **AND** system SHALL produce bar chart or box plot visualizations for each comparison
- **AND** groups with fewer than 10 samples SHALL display a warning

#### Scenario: Rare sport types grouped
- **WHEN** an activity sport type has fewer than 10 sessions
- **THEN** system SHALL group it into an "Other" category for sport-type analysis

### Requirement: Temporal pattern analysis

The system SHALL analyze sleep quality patterns across time dimensions (day-of-week, weekend/weekday, trends over time).

#### Scenario: Day-of-week patterns displayed
- **WHEN** temporal analysis is executed
- **THEN** system SHALL compute average sleep score and duration by day of week
- **AND** system SHALL produce a bar chart showing sleep quality by day of week
- **AND** system SHALL highlight statistically significant differences between days

#### Scenario: Weekend vs weekday comparison
- **WHEN** weekend/weekday analysis is executed
- **THEN** system SHALL compare sleep metrics (score, duration, deep sleep %) for weekend vs weekday nights
- **AND** system SHALL run a statistical test (Mann-Whitney U) for the comparison
- **AND** system SHALL display results with visualization

#### Scenario: Sleep trend over time
- **WHEN** trend analysis is executed
- **THEN** system SHALL plot sleep score and duration as time series over the full date range
- **AND** system SHALL include a rolling average (7-day and 30-day) overlay
- **AND** system SHALL visually indicate periods of sustained sleep deprivation (3+ consecutive deprived nights)

### Requirement: Sleep stage analysis

The system SHALL analyze the distribution and trends of sleep stages (deep, light, REM, awake).

#### Scenario: Sleep stage proportions displayed
- **WHEN** sleep stage analysis is executed
- **THEN** system SHALL compute the average proportion of each sleep stage (deep, light, REM, awake)
- **AND** system SHALL compare stage proportions between deprived and adequate nights
- **AND** system SHALL produce stacked bar charts or pie charts showing stage distribution

#### Scenario: Deep sleep correlation examined
- **WHEN** deep sleep analysis is executed
- **THEN** system SHALL compute correlation between deep sleep duration/percentage and sleep score
- **AND** system SHALL compute correlation between deep sleep and next-day body battery
- **AND** system SHALL display scatter plots with trend lines

### Requirement: Analysis outputs and findings summary

The system SHALL produce a clear summary of findings at the end of the analysis notebook.

#### Scenario: Key findings summarized
- **WHEN** all analysis sections are complete
- **THEN** the notebook SHALL contain a summary section listing the top factors correlated with sleep deprivation
- **AND** the summary SHALL rank factors by statistical significance and effect size
- **AND** the summary SHALL note important caveats (correlation ≠ causation, confounding variables, data limitations)

#### Scenario: All visualizations render inline
- **WHEN** the notebook is executed end-to-end
- **THEN** all charts SHALL render inline in the notebook
- **AND** charts SHALL use consistent styling (seaborn theme, readable font sizes, proper labels)
- **AND** charts SHALL include titles, axis labels, and legends where appropriate
