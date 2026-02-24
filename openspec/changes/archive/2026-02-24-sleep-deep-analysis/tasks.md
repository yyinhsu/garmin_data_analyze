## 1. Feature Builder — Scaffold

- [x] 1.1 Create `analysis/customized/sleep_feature_builder.py` with `build_sleep_features()` stub and `CONTROLLABILITY` dict skeleton
- [x] 1.2 Add `report_feature_completeness(df)` helper function

## 2. Feature Builder — Temporal, Lag, Rolling, Streak

- [x] 2.1 Implement temporal features: `weekday`, `is_weekend`, `month`, `sleep_start_hour`, `sleep_start_minute`, `wake_hour`, `time_in_bed_hours`
- [x] 2.2 Implement lag features: `prev1_total_sleep`, `prev1_score`, `prev1_rem_hours`, `prev1_deep_hours`, `prev1_qualifier_encoded`, `prev1_sleep_start_hour`, `prev2_total_sleep`, `prev3_total_sleep`
- [x] 2.3 Implement rolling features: `rolling_3d_sleep_avg`, `rolling_7d_sleep_avg`, `rolling_7d_score_avg`, `sleep_debt_7d`
- [x] 2.4 Implement streak counters: `consecutive_poor_sleep`, `consecutive_good_sleep`, `consecutive_exercise_days`, `consecutive_rest_days`, `days_since_last_good_sleep`
- [x] 2.5 Implement `bedtime_consistency_7d` (std of sleep_start_hour over past 7 nights)

## 3. Feature Builder — Exercise Features

- [x] 3.1 Load activities via `load_activities()`, apply `filter_nighttime_activities()`, group by date
- [x] 3.2 Compute: `had_exercise`, `n_activities`, `total_workout_duration_h`, `latest_workout_end_hour`
- [x] 3.3 Compute: `hours_workout_to_sleep` (NaN on rest days), `primary_sport`, `vigorous_ratio`
- [x] 3.4 Compute: `training_load` (daily sum), `training_load_7d` (rolling 7-day), `hrz_high_intensity_min`
- [x] 3.5 Add exercise features to `CONTROLLABILITY` dict with appropriate tags

## 4. Feature Builder — Body Battery & Daily Physiological

- [x] 4.1 Compute BB features: `bb_max`, `bb_min`, `bb_charged`, `bb_range`
- [x] 4.2 Compute daily physiological: `rhr`, `inactive_hr_avg` (from days_summary), `avg_spo2`, `avg_rr`, `rr_waking_avg`
- [x] 4.3 Compute intensity features: `moderate_activity_h`, `vigorous_activity_h`, `intensity_score`

## 5. Feature Builder — Pre-sleep Monitoring Windows

- [x] 5.1 Load `monitoring_hr` table once, sort by timestamp, convert to numpy arrays for searchsorted
- [x] 5.2 Load `stress` table once (same approach)
- [x] 5.3 Load `monitoring_rr` table once (same approach)
- [x] 5.4 Load `monitoring` table once for steps/active_calories (same approach)
- [x] 5.5 For N ∈ {1, 2, 4, 6, 8}: compute `pre_sleep_hr_avg_Nh`, `pre_sleep_hr_min_Nh`, `pre_sleep_hr_std_Nh`, `pre_sleep_hr_trend_Nh`, `pre_sleep_hr_n_readings_Nh`
- [x] 5.6 For N ∈ {1, 2, 4, 6, 8}: compute `pre_sleep_stress_avg_Nh`, `pre_sleep_stress_max_Nh`, `pre_sleep_high_stress_min_Nh`
- [x] 5.7 For N ∈ {1, 2}: compute `pre_sleep_rr_avg_Nh`, `pre_sleep_rr_std_Nh`
- [x] 5.8 For N ∈ {1, 2, 4, 8}: compute `pre_sleep_steps_Nh`, `pre_sleep_active_cal_Nh`

## 6. Feature Builder — Sleep Architecture

- [x] 6.1 Load `sleep_events`, compute `time_to_first_deep_min`, `time_to_first_rem_min` per night
- [x] 6.2 Compute `n_awakenings`, `longest_uninterrupted_sleep_h` per night
- [x] 6.3 Left-join onto main DataFrame (NaN for nights before 2025-10-01)

## 7. Notebook — Section 1: Feature Loading & Completeness

- [x] 7.1 Create `analysis/sleep_deep_analysis.ipynb` with section headers and setup cell (sys.path, imports)
- [x] 7.2 Cell: call `build_sleep_features()`, print shape and date range
- [x] 7.3 Cell: call `report_feature_completeness(df)`, display table

## 8. Notebook — Section 2: Dual-Target Correlation Analysis

- [x] 8.1 Cell: Spearman correlation table vs `score` (sorted by |r|, Bonferroni-corrected significance)
- [x] 8.2 Cell: Spearman correlation table vs `bb_charged`
- [x] 8.3 Cell: side-by-side heatmap comparing top-20 feature correlations for both targets

## 9. Notebook — Section 3: Interventional Analysis

- [x] 9.1 Cell: filter to HIGH/MEDIUM controllability features using `CONTROLLABILITY` dict
- [x] 9.2 Cell: Mann-Whitney effect size (rank-biserial) for each controllable feature, deprived vs adequate
- [x] 9.3 Cell: ranked bar chart of controllable features by |effect size| with group means annotated

## 10. Notebook — Section 4: Pre-sleep Window Comparison

- [x] 10.1 Cell: line chart of correlation(pre_sleep_hr_avg_Nh, score) for N=1,2,4,6,8
- [x] 10.2 Cell: same for `pre_sleep_stress_avg_Nh` and `pre_sleep_rr_avg_Nh`

## 11. Notebook — Section 5: Streak & Lag Analysis

- [x] 11.1 Cell: scatter + LOWESS of sleep score vs `consecutive_poor_sleep`
- [x] 11.2 Cell: correlation of `rolling_7d_sleep_avg` with next-night score
- [x] 11.3 Cell: box plot of sleep score by `consecutive_exercise_days` bucket (0, 1, 2, 3, 4+)
