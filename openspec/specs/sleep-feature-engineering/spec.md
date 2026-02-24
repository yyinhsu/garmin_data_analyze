## ADDED Requirements

### Requirement: Feature builder module

`analysis/customized/sleep_feature_builder.py` SHALL provide a `build_sleep_features()` function that returns a single pandas DataFrame with one row per night (up to 601 rows) and all engineered features as columns.

#### Scenario: build_sleep_features returns complete DataFrame

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL return a DataFrame indexed by `day` (date)
- **AND** it SHALL contain all feature groups defined in this spec
- **AND** rows with no sleep data SHALL be excluded
- **AND** `filter_nighttime_activities` SHALL be applied before computing exercise features

#### Scenario: Missing data handled with NaN

- **WHEN** a feature cannot be computed for a given night (e.g., no sleep.start, sparse monitoring data)
- **THEN** the value SHALL be NaN (not 0 or a sentinel value)
- **AND** a completeness summary SHALL be printable via a `report_feature_completeness(df)` helper

---

### Requirement: Temporal features

The builder SHALL compute the following temporal features from `sleep.day`, `sleep.start`, and `sleep.end`.

#### Scenario: Temporal columns produced

- **WHEN** `build_sleep_features()` is called
- **THEN** the DataFrame SHALL contain: `weekday` (string Mon–Sun), `is_weekend` (bool), `month` (int 1–12), `sleep_start_hour` (float, e.g. 1.5 = 01:30), `sleep_start_minute` (int), `wake_hour` (float), `time_in_bed_hours` (float)
- **AND** `sleep_start_hour` SHALL be NaN when `sleep.start` is NULL

---

### Requirement: Lag and rolling sleep features

The builder SHALL compute lag and rolling window features from the sleep table, sorted by date ascending.

#### Scenario: Lag features computed

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL include `prev1_total_sleep`, `prev1_score`, `prev1_rem_hours`, `prev1_deep_hours`, `prev1_qualifier_encoded` (POOR=0, FAIR=1, GOOD=2, EXCELLENT=3), `prev1_sleep_start_hour`, `prev2_total_sleep`, `prev3_total_sleep`
- **AND** the first N rows SHALL have NaN for lag-N features

#### Scenario: Rolling features computed

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL include `rolling_3d_sleep_avg`, `rolling_7d_sleep_avg`, `rolling_7d_score_avg`, `sleep_debt_7d` (49 - rolling 7-day total sleep hours, capped at 0)

---

### Requirement: Streak features

The builder SHALL compute consecutive-day streak counters.

#### Scenario: Streak counters produced

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL include `consecutive_poor_sleep` (nights in a row with score < 60 or qualifier POOR, counting up to and including the current night), `consecutive_good_sleep`, `consecutive_exercise_days`, `consecutive_rest_days`, `days_since_last_good_sleep`
- **AND** streaks SHALL reset to 0 (or 1 for current night) when the condition breaks

---

### Requirement: Exercise features

The builder SHALL compute per-day exercise aggregates from the filtered activities table (nighttime filter applied).

#### Scenario: Exercise features produced

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL include: `had_exercise` (bool), `n_activities` (int, 0 on rest days), `total_workout_duration_h`, `latest_workout_end_hour` (float, NaN on rest days), `hours_workout_to_sleep` (NaN on rest days or when sleep.start is NULL), `primary_sport` (most frequent sport that day, encoded as string), `training_load` (sum of activities.training_load that day), `training_load_7d` (rolling 7-day sum), `hrz_high_intensity_min` (hrz_4_time + hrz_5_time in minutes), `vigorous_ratio` (vigorous duration / total duration, NaN on rest days)
- **AND** `hours_workout_to_sleep` SHALL be NaN (not 0) on rest days

---

### Requirement: Body battery features

The builder SHALL include body battery metrics from `daily_summary`.

#### Scenario: BB features produced

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL include `bb_max`, `bb_min`, `bb_charged`, `bb_range` (max - min)
- **AND** `bb_charged` SHALL be the primary secondary analysis target alongside `score`

---

### Requirement: Pre-sleep monitoring features

The builder SHALL compute physiological aggregates for time windows of 1, 2, 4, 6, and 8 hours before `sleep.start` using per-minute monitoring data.

#### Scenario: Pre-sleep HR features computed

- **WHEN** `build_sleep_features()` is called
- **THEN** for each window N ∈ {1, 2, 4, 6, 8}, the DataFrame SHALL include:
  `pre_sleep_hr_avg_Nh`, `pre_sleep_hr_min_Nh`, `pre_sleep_hr_std_Nh`, `pre_sleep_hr_trend_Nh` (avg HR in second half of window minus first half — negative = HR dropping = relaxing), `pre_sleep_hr_n_readings_Nh` (coverage count)
- **AND** all values SHALL be NaN when `sleep.start` is NULL or the window has zero readings

#### Scenario: Pre-sleep stress features computed

- **WHEN** `build_sleep_features()` is called
- **THEN** for each N ∈ {1, 2, 4, 6, 8}: `pre_sleep_stress_avg_Nh`, `pre_sleep_stress_max_Nh`, `pre_sleep_high_stress_min_Nh` (minutes with stress > 50)

#### Scenario: Pre-sleep HRV proxy features computed

- **WHEN** `build_sleep_features()` is called
- **THEN** for N ∈ {1, 2}: `pre_sleep_rr_avg_Nh` (avg RR interval in ms — higher = more relaxed), `pre_sleep_rr_std_Nh`

#### Scenario: Pre-sleep activity features computed

- **WHEN** `build_sleep_features()` is called
- **THEN** for N ∈ {1, 2, 4, 8}: `pre_sleep_steps_Nh`, `pre_sleep_active_cal_Nh`

#### Scenario: Monitoring data loaded efficiently

- **WHEN** `build_sleep_features()` processes pre-sleep windows
- **THEN** each monitoring table SHALL be loaded once into memory and sorted by timestamp
- **AND** `numpy.searchsorted` SHALL be used to locate window boundaries per night (not per-row SQL queries)

---

### Requirement: Sleep architecture features

The builder SHALL compute sleep architecture features from `sleep_events` where available.

#### Scenario: Architecture features produced with partial coverage

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL include `time_to_first_deep_min`, `time_to_first_rem_min`, `n_awakenings`, `longest_uninterrupted_sleep_h`
- **AND** nights before 2025-10-01 (no sleep_events data) SHALL have NaN for these columns
- **AND** the completeness report SHALL flag these as partial-coverage features

---

### Requirement: Additional physiological features

The builder SHALL include the following daily physiological metrics.

#### Scenario: Physiological features produced

- **WHEN** `build_sleep_features()` is called
- **THEN** it SHALL include: `rhr` (from daily_summary), `inactive_hr_avg` (from days_summary), `avg_spo2` (from sleep), `avg_rr` (from sleep — respiratory rate), `rr_waking_avg` (from daily_summary), `moderate_activity_h`, `vigorous_activity_h`, `intensity_score` (moderate_h + 2 × vigorous_h), `bedtime_consistency_7d` (std of sleep_start_hour over past 7 nights)
