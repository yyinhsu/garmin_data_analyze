## ADDED Requirements

### Requirement: Lifestyle signal features
The builder SHALL expose `calories_consumed` and `steps` (daily walking steps) from the `daily_summary` table as top-level feature columns, and add them to the `CONTROLLABILITY` dict.

#### Scenario: Lifestyle columns present
- **WHEN** `build_sleep_features()` is called
- **THEN** the DataFrame SHALL contain `calories_consumed` (float, kcal) and `steps` (int) sourced from `daily_summary`
- **AND** both SHALL be tagged `MEDIUM` controllability in the `CONTROLLABILITY` dict
- **AND** NaN SHALL be used where the daily_summary row is missing

### Requirement: Sport category classifier feature
The builder SHALL classify each exercise day's primary sport into one of four categories: `cardio`, `strength`, `mixed`, `other`, exposed as the `sport_category` column (string, NaN on rest days).

#### Scenario: Sport category assigned
- **WHEN** `build_sleep_features()` is called and the night had exercise
- **THEN** `sport_category` SHALL be one of: `cardio` (running, cycling, swimming, walking, hiking), `strength` (fitness_equipment), `mixed` (basketball, soccer, and other team sports), `other` (all remaining sport types)
- **AND** rest days (no exercise) SHALL have `sport_category = NaN`

#### Scenario: Sport category controllability
- **WHEN** the `CONTROLLABILITY` dict is accessed
- **THEN** `sport_category` SHALL be tagged `HIGH`

### Requirement: Late bedtime flag feature
The builder SHALL expose `is_late_bedtime` (bool) defined as `sleep_start_hour >= 3.0`.

#### Scenario: Late bedtime flag computed
- **WHEN** `build_sleep_features()` is called
- **THEN** the DataFrame SHALL contain `is_late_bedtime` (bool): True if `sleep_start_hour >= 3.0`, False otherwise, NaN if sleep_start is missing
- **AND** `is_late_bedtime` SHALL be tagged `HIGH` in `CONTROLLABILITY`

### Requirement: Same-day workout intensity features
The builder SHALL compute `same_day_vigorous_ratio` and `same_day_vigorous_min` per night from the day's activities, using hrz_4_time + hrz_5_time.

#### Scenario: Intensity features on exercise days
- **WHEN** `build_sleep_features()` is called and the night had exercise
- **THEN** `same_day_vigorous_ratio` SHALL equal (hrz4_min + hrz5_min) / total_workout_duration_min, clamped to [0, 1]
- **AND** `same_day_vigorous_min` SHALL equal the total hrz4+hrz5 minutes for the day
- **AND** rest days SHALL have NaN for both columns
- **AND** both SHALL be tagged `HIGH` in `CONTROLLABILITY`
