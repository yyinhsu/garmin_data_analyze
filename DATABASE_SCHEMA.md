# Garmin Health Database Schema

All databases are located at `./HealthData/DBs/`. There are 5 SQLite databases.

> **Note:** If the schema changes, update both `DATABASE_SCHEMA.md` and `DATABASE_SCHEMA_ZH.md` simultaneously.

---

## garmin.db — Core Daily Health Data

### `daily_summary` — Daily Summary (601 rows)

| Column | Description |
|--------|-------------|
| `day` | Date (PK) |
| `hr_min` / `hr_max` | Daily min/max heart rate (bpm) |
| `rhr` | Resting heart rate (bpm) |
| `stress_avg` | Average stress score (0–100) |
| `step_goal` / `steps` | Step goal / actual steps |
| `moderate_activity_time` | Moderate intensity activity time |
| `vigorous_activity_time` | Vigorous intensity activity time |
| `intensity_time_goal` | Intensity time goal |
| `floors_up` / `floors_down` / `floors_goal` | Floors climbed/descended/goal |
| `distance` | Distance traveled (km) |
| `calories_goal` / `calories_total` | Calorie goal / total burned |
| `calories_bmr` | BMR calories |
| `calories_active` | Active calories burned |
| `calories_consumed` | Calories consumed |
| `hydration_goal` / `hydration_intake` | Hydration goal / intake (oz) |
| `sweat_loss` | Sweat loss |
| `spo2_avg` / `spo2_min` | Average/minimum SpO2 (%) |
| `rr_waking_avg` / `rr_max` / `rr_min` | Waking respiration rate avg/max/min (breaths/min) |
| `bb_charged` / `bb_max` / `bb_min` | Body Battery charged/max/min |
| `description` | Notes |

---

### `sleep` — Daily Sleep (601 rows)

| Column | Description |
|--------|-------------|
| `day` | Date (PK) |
| `start` / `end` | Sleep start/end time |
| `total_sleep` | Total sleep duration |
| `deep_sleep` | Deep sleep duration |
| `light_sleep` | Light sleep duration |
| `rem_sleep` | REM sleep duration |
| `awake` | Awake duration |
| `avg_spo2` | Average SpO2 during sleep (%) |
| `avg_rr` | Average respiration rate during sleep |
| `avg_stress` | Average stress during sleep |
| `score` | Sleep score (0–100) |
| `qualifier` | Sleep quality label (e.g. FAIR, GOOD) |

---

### `resting_hr` — Resting Heart Rate (588 rows)

| Column | Description |
|--------|-------------|
| `day` | Date (PK) |
| `resting_heart_rate` | Daily resting heart rate (bpm) |

---

### `stress` — Stress Time Series (817,388 rows)

| Column | Description |
|--------|-------------|
| `timestamp` | Timestamp (per minute) |
| `stress` | Stress value (0–100; negative = rest/sleep) |

---

### `weight` — Body Weight (4 rows)

| Column | Description |
|--------|-------------|
| `day` | Date |
| `weight` | Weight (kg) |

---

### `devices` — Device Info (6 rows)

| Column | Description |
|--------|-------------|
| `serial_number` | Serial number (PK) |
| `timestamp` | Last sync time |
| `device_type` | Device type (e.g. fitness_tracker) |
| `manufacturer` | Manufacturer |
| `product` | Model (e.g. VivoActive_5) |
| `hardware_version` | Hardware version |

---

### `sleep_events` — Sleep Events (2,317 rows)

| Column | Description |
|--------|-------------|
| `timestamp` | Event timestamp |
| `event` | Event type |
| `duration` | Duration |

---

## garmin_activities.db — Activity Data

### `activities` — Activity Records (615 rows)

| Column | Description |
|--------|-------------|
| `activity_id` | Activity ID (PK) |
| `name` | Activity name (e.g. Running, Stair Stepper) |
| `type` | Type |
| `sport` / `sub_sport` | Sport category / sub-category |
| `laps` | Number of laps |
| `start_time` / `stop_time` | Start/end time |
| `elapsed_time` / `moving_time` | Total time / moving time |
| `distance` | Distance (km) |
| `cycles` | Cycles (steps, pedal strokes, etc.) |
| `avg_hr` / `max_hr` | Average/max heart rate |
| `avg_rr` / `max_rr` | Average/max respiration rate |
| `calories` | Calories burned |
| `avg_cadence` / `max_cadence` | Average/max cadence |
| `avg_speed` / `max_speed` | Average/max speed |
| `ascent` / `descent` | Elevation gain/loss (m) |
| `max_temperature` / `min_temperature` / `avg_temperature` | Temperature (°C) |
| `start_lat` / `start_long` / `stop_lat` / `stop_long` | GPS start/end coordinates |
| `training_load` / `training_effect` / `anaerobic_training_effect` | Training load metrics |
| `hrz_1_hr` ~ `hrz_5_hr` | Heart rate zone thresholds |
| `hrz_1_time` ~ `hrz_5_time` | Time spent in each HR zone |
| `self_eval_feel` / `self_eval_effort` | Subjective feel / effort rating |

---

### `steps_activities` — Walking/Running Details (32 rows)

| Column | Description |
|--------|-------------|
| `activity_id` | Activity ID (FK) |
| `steps` | Total steps |
| `avg_pace` / `avg_moving_pace` / `max_pace` | Avg pace / moving pace / best pace |
| `avg_steps_per_min` / `max_steps_per_min` | Avg/max step rate |
| `avg_step_length` | Average step length |
| `avg_vertical_ratio` / `avg_vertical_oscillation` | Vertical ratio / oscillation |
| `avg_gct_balance` / `avg_ground_contact_time` | Ground contact balance / time |
| `avg_stance_time_percent` | Stance time percentage |
| `vo2_max` | Estimated VO2 max |

---

### `cycle_activities` — Cycling Details (28 rows)

| Column | Description |
|--------|-------------|
| `activity_id` | Activity ID (FK) |
| `strokes` | Pedal strokes |
| `vo2_max` | Estimated VO2 max |

---

### `activity_laps` — Activity Laps (649 rows)

Same columns as `activities`, plus:

| Column | Description |
|--------|-------------|
| `activity_id` | Activity ID (FK) |
| `lap` | Lap number (0-indexed) |

---

### `activity_records` — Per-Second Records (1,348,434 rows)

| Column | Description |
|--------|-------------|
| `activity_id` | Activity ID (FK) |
| `record` | Record sequence number |
| `timestamp` | Timestamp |
| `position_lat` / `position_long` | GPS coordinates |
| `distance` | Cumulative distance |
| `cadence` | Current cadence |
| `altitude` | Altitude (m) |
| `hr` | Current heart rate |
| `rr` | Current respiration rate |
| `speed` | Current speed |
| `temperature` | Temperature |

---

## garmin_monitoring.db — Continuous Background Monitoring

### `monitoring` — Activity Type Monitoring (250,242 rows)

| Column | Description |
|--------|-------------|
| `timestamp` | Timestamp |
| `activity_type` | Activity type (walking, running, sedentary, etc.) |
| `intensity` | Intensity level (0–5) |
| `duration` | Duration of current segment |
| `distance` | Cumulative distance |
| `cum_active_time` | Cumulative active time |
| `active_calories` | Cumulative active calories |
| `steps` | Cumulative steps |
| `strokes` | Cumulative strokes |
| `cycles` | Cumulative cycles |

---

### `monitoring_hr` — Real-time Heart Rate (658,267 rows)

| Column | Description |
|--------|-------------|
| `timestamp` | Timestamp (approx. per minute) |
| `heart_rate` | Heart rate (bpm) |

---

### `monitoring_rr` — Real-time Respiration Rate (558,811 rows)

| Column | Description |
|--------|-------------|
| `timestamp` | Timestamp |
| `rr` | Respiration rate (breaths/min) |

---

### `monitoring_intensity` — Intensity Time Accumulation (6,385 rows)

| Column | Description |
|--------|-------------|
| `timestamp` | Timestamp (every 15 min) |
| `moderate_activity_time` | Cumulative moderate intensity time |
| `vigorous_activity_time` | Cumulative vigorous intensity time |

---

### `monitoring_info` — Monitoring Metadata (7,486 rows)

| Column | Description |
|--------|-------------|
| `timestamp` | Timestamp |
| `file_id` | Source FIT file ID |
| `activity_type` | Activity type |
| `resting_metabolic_rate` | Resting metabolic rate |
| `cycles_to_distance` | Cycles-to-distance conversion factor |
| `cycles_to_calories` | Cycles-to-calories conversion factor |

---

## garmin_summary.db / summary.db — Aggregated Statistics

> `garmin_summary.db` and `summary.db` have identical structures with the following four tables.

### Shared Columns (`days_summary` / `weeks_summary` / `months_summary` / `years_summary`)

| Column | Description |
|--------|-------------|
| `day` / `first_day` | Date key (`day` for daily, `first_day` for others) |
| `hr_avg` / `hr_min` / `hr_max` | Heart rate avg/min/max |
| `rhr_avg` / `rhr_min` / `rhr_max` | Resting heart rate avg/min/max |
| `inactive_hr_avg` / `inactive_hr_min` / `inactive_hr_max` | Inactive heart rate |
| `weight_avg` / `weight_min` / `weight_max` | Weight (kg) |
| `intensity_time` / `moderate_activity_time` / `vigorous_activity_time` | Intensity/moderate/vigorous time |
| `intensity_time_goal` | Intensity time goal |
| `steps` / `steps_goal` | Steps / step goal |
| `floors` / `floors_goal` | Floors / goal |
| `sleep_avg` / `sleep_min` / `sleep_max` | Sleep duration avg/min/max |
| `rem_sleep_avg` / `rem_sleep_min` / `rem_sleep_max` | REM sleep |
| `stress_avg` | Average stress score |
| `calories_avg` / `calories_bmr_avg` / `calories_active_avg` | Calories (total/BMR/active) |
| `calories_goal` / `calories_consumed_avg` | Calorie goal / consumed |
| `activities` / `activities_calories` / `activities_distance` | Activity count / calories / distance |
| `hydration_goal` / `hydration_avg` / `hydration_intake` | Hydration goal/avg/intake |
| `sweat_loss_avg` / `sweat_loss` | Sweat loss |
| `spo2_avg` / `spo2_min` | SpO2 avg/min |
| `rr_waking_avg` / `rr_max` / `rr_min` | Waking respiration rate avg/max/min |
| `bb_max` / `bb_min` | Body Battery max/min |

| Table | Granularity | Rows |
|-------|-------------|------|
| `days_summary` | Daily | 588 |
| `weeks_summary` | Weekly | 112 |
| `months_summary` | Monthly | 20 |
| `years_summary` | Yearly | 3 |

---

## Data Volume Overview

| Database | Table | Rows |
|----------|-------|------|
| garmin.db | daily_summary | 601 |
| garmin.db | sleep | 601 |
| garmin.db | resting_hr | 588 |
| garmin.db | stress | 817,388 |
| garmin.db | weight | 4 |
| garmin_activities.db | activities | 615 |
| garmin_activities.db | activity_records | 1,348,434 |
| garmin_activities.db | steps_activities | 32 |
| garmin_activities.db | cycle_activities | 28 |
| garmin_monitoring.db | monitoring | 250,242 |
| garmin_monitoring.db | monitoring_hr | 658,267 |
| garmin_monitoring.db | monitoring_rr | 558,811 |
| garmin_summary.db | days_summary | 588 |
| garmin_summary.db | weeks_summary | 112 |
| garmin_summary.db | months_summary | 20 |
| garmin_summary.db | years_summary | 3 |
