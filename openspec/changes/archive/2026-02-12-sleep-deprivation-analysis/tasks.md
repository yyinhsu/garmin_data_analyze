## 1. Environment Setup

- [x] 1.1 Add analysis dependencies (pandas, matplotlib, seaborn, scipy, jupyter) to requirements.txt
- [x] 1.2 Install dependencies in the existing .venv
- [x] 1.3 Create `analysis/` directory structure

## 2. Analysis Utilities Module (`analysis/garmin_utils.py`)

- [x] 2.1 Implement database connection helpers with automatic path resolution for all 4 DBs
- [x] 2.2 Implement `load_sleep_data()` — load sleep table joined with daily_summary and resting_hr
- [x] 2.3 Implement `load_activities()` — load activities with time_bucket classification and optional rare sport grouping
- [x] 2.4 Implement `classify_sleep(df)` — add is_deprived and sleep_quality columns based on score < 60 / POOR / < 6h
- [x] 2.5 Implement `report_completeness(df, columns)` — data completeness summary per column
- [x] 2.6 Implement `compute_correlations(df, target_col, feature_cols)` — Spearman correlation with p-values
- [x] 2.7 Implement `compare_groups(df, group_col, metric_col)` — Mann-Whitney U test with effect size
- [x] 2.8 Implement plotting helpers: `plot_correlation_heatmap`, `plot_group_comparison`, `plot_time_series` with consistent seaborn styling

## 3. Sleep Analysis Notebook — Data Loading & Overview (`analysis/sleep_analysis.ipynb`)

- [x] 3.1 Create notebook with imports, seaborn theme setup, and data loading using garmin_utils
- [x] 3.2 Add data completeness report section
- [x] 3.3 Add sleep deprivation classification and summary statistics (count/percentage deprived vs adequate)
- [x] 3.4 Add sleep score distribution chart with threshold line at 60

## 4. Sleep Analysis Notebook — Correlation & Group Comparison

- [x] 4.1 Add correlation heatmap: sleep score vs daytime metrics (steps, calories, stress, resting HR, body battery, floors, active minutes)
- [x] 4.2 Add ranked correlation table with p-values and significance flags
- [x] 4.3 Add group comparison (deprived vs adequate): box/violin plots for each daytime metric with Mann-Whitney p-values
- [x] 4.4 Add minimum sample size warnings where applicable

## 5. Sleep Analysis Notebook — Activity Timing Analysis

- [x] 5.1 Add activity loading with time bucket classification (Morning/Afternoon/Evening/Late Night)
- [x] 5.2 Add sleep quality comparison across activity timing buckets (bar/box plots)
- [x] 5.3 Add exercise day vs rest day sleep comparison with statistical test
- [x] 5.4 Add sport type analysis with rare types grouped as "Other"

## 6. Sleep Analysis Notebook — Temporal Patterns

- [x] 6.1 Add day-of-week sleep quality analysis (bar chart + significance testing)
- [x] 6.2 Add weekend vs weekday comparison with Mann-Whitney test
- [x] 6.3 Add sleep score and duration time series with 7-day and 30-day rolling averages
- [x] 6.4 Add sustained sleep deprivation detection (3+ consecutive deprived nights highlighted)

## 7. Sleep Analysis Notebook — Sleep Stages & Summary

- [x] 7.1 Add sleep stage proportion analysis (stacked bar: deprived vs adequate)
- [x] 7.2 Add deep sleep correlation with sleep score and next-day body battery (scatter plots)
- [x] 7.3 Add findings summary section: ranked factors, significance, caveats

## 8. Validation

- [x] 8.1 Run notebook end-to-end and verify all cells execute without errors
- [x] 8.2 Verify all charts render inline with proper labels, titles, and legends
- [x] 8.3 Review findings summary for accuracy and appropriate caveats
