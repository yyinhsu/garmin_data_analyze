## 1. Feature Builder — New Features

- [x] 1.1 Add `calories_consumed` and `steps` from `daily_summary` to `build_sleep_features()`, tag both `MEDIUM` in `CONTROLLABILITY`
- [x] 1.2 Add `sport_category` column: classify primary sport into `cardio` / `strength` / `mixed` / `other`, NaN on rest days, tag `HIGH` in `CONTROLLABILITY`
- [x] 1.3 Add `is_late_bedtime` bool column (`sleep_start_hour >= 3.0`), tag `HIGH` in `CONTROLLABILITY`
- [x] 1.4 Add `same_day_vigorous_ratio` and `same_day_vigorous_min` from hrz4+hrz5 time per day, tag `HIGH` in `CONTROLLABILITY`

## 2. Notebook — Setup

- [x] 2.1 Create `analysis/sleep_causal_investigation.ipynb` with imports, sys.path setup, and `build_sleep_features()` call
- [x] 2.2 Add section headers for all 6 investigation sections

## 3. Notebook — Section 1: Bedtime Threshold

- [x] 3.1 Split nights into before-3AM vs at/after-3AM; show n, mean score, deprivation rate, Mann-Whitney p-value
- [x] 3.2 Scatter + LOWESS of `sleep_start_hour` vs `score` with Spearman r annotation

## 4. Notebook — Section 2: Exercise Intensity vs Sport Label

- [x] 4.1 Correlate `same_day_vigorous_ratio` with next-night sleep score; compare r to sport-label correlation
- [x] 4.2 Scatter plots of `vigorous_ratio` vs `score` per sport category (cardio / strength / mixed) with LOWESS and r per group

## 5. Notebook — Section 3: Stress → Bedtime Feedback Loop

- [x] 5.1 Scatter + LOWESS of `pre_sleep_stress_avg_4h` vs `sleep_start_hour`, split by `had_exercise`
- [x] 5.2 Report Spearman r (raw) and partial r controlling for `had_exercise`

## 6. Notebook — Section 4: Deep Sleep Onset Cascading

- [x] 6.1 Shift `time_to_first_deep_min` by -1 night; correlate with next-night score; scatter + LOWESS (n=144 window)
- [x] 6.2 Split by `time_to_first_deep_min > 30 min` vs `<= 30 min`; show mean next-night score and Mann-Whitney p-value

## 7. Notebook — Section 5: Cardio vs Strength

- [x] 7.1 Group nights by `sport_category`; build comparison table: n, mean score, deprivation rate, effect size vs rest
- [x] 7.2 Box plot of sleep score by sport_category with Kruskal-Wallis p-value

## 8. Notebook — Section 6: Calories Consumed & Steps

- [x] 8.1 Report 2×2 Spearman correlation table: {calories_consumed, steps} × {score, total_sleep_hours}
- [x] 8.2 Scatter + LOWESS plots: calories_consumed vs score, steps vs score
