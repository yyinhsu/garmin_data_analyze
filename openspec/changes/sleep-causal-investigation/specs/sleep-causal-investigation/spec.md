## ADDED Requirements

### Requirement: Bedtime threshold analysis
The notebook SHALL test whether a bedtime at or after 3:00 AM (sleep_start_hour >= 3.0) acts as a non-linear threshold for sleep deprivation, using both a proportion comparison and a Spearman correlation of sleep_start_hour with score.

#### Scenario: Threshold comparison
- **WHEN** nights are split into before-3AM and after-3AM groups
- **THEN** the notebook displays mean sleep score, deprivation rate (score<50 OR total_sleep<4.5h), and n for each group, plus a Mann-Whitney p-value

#### Scenario: Continuous relationship
- **WHEN** sleep_start_hour is plotted against score
- **THEN** a scatter plot with LOWESS curve is shown, annotated with Spearman r and p-value

### Requirement: Exercise intensity vs sport label analysis
The notebook SHALL test whether vigorous_ratio (hrz4+hrz5 min / total workout time) explains sleep score variance better than the sport label alone, using Spearman correlation and a scatter plot per sport category.

#### Scenario: Intensity correlation
- **WHEN** same_day_vigorous_ratio is correlated with next-night sleep score
- **THEN** Spearman r and p-value are reported alongside the correlation for sport label

#### Scenario: Per-sport intensity scatter
- **WHEN** vigorous_ratio vs sleep score is plotted separately for cardio vs strength vs mixed
- **THEN** each subplot shows the LOWESS trend and r value

### Requirement: Stress to bedtime feedback loop analysis
The notebook SHALL test whether high pre-sleep stress (pre_sleep_stress_avg_4h) predicts a later bedtime (sleep_start_hour), controlling for whether exercise occurred that day.

#### Scenario: Stress predicts bedtime
- **WHEN** pre_sleep_stress_avg_4h is correlated with sleep_start_hour
- **THEN** Spearman r, p-value, and a scatter+LOWESS plot are shown for exercise and non-exercise days separately

#### Scenario: Mediation check
- **WHEN** the partial correlation of stress→bedtime is computed controlling for had_exercise
- **THEN** the partial r is displayed alongside the raw r

### Requirement: Deep sleep onset cascading analysis
The notebook SHALL test whether time_to_first_deep_min on night N predicts sleep score on night N+1, using the 144-night post-Oct-2025 window.

#### Scenario: Next-night prediction
- **WHEN** time_to_first_deep_min is shifted by -1 and correlated with next-night score
- **THEN** Spearman r, p-value, n, and scatter+LOWESS plot are shown

#### Scenario: Threshold check
- **WHEN** nights are split by time_to_first_deep_min > 30 min vs <= 30 min
- **THEN** mean next-night score for each group is displayed with a Mann-Whitney p-value

### Requirement: Cardio vs strength workout comparison
The notebook SHALL compare sleep outcomes (score, total_sleep_hours, deprivation rate) between nights following cardio workouts, strength workouts, mixed workouts, and rest days, using Kruskal-Wallis and pairwise Mann-Whitney tests.

#### Scenario: Group comparison table
- **WHEN** nights are grouped by sport_category of the day's primary workout
- **THEN** a table shows n, mean score, median score, deprivation rate, and effect size vs rest days for each category

#### Scenario: Box plot
- **WHEN** sleep score distributions are plotted per sport_category
- **THEN** a box plot with Kruskal-Wallis p-value annotation is shown

### Requirement: Calories consumed and steps vs sleep analysis
The notebook SHALL report Spearman correlations of calories_consumed and steps (daily walking) with sleep score and total_sleep_hours, and display scatter plots.

#### Scenario: Correlation table
- **WHEN** calories_consumed and steps are correlated with score and total_sleep_hours
- **THEN** a 2×2 Spearman r table with p-values is shown

#### Scenario: Scatter plots
- **WHEN** calories_consumed and steps are plotted against sleep score
- **THEN** two scatter plots with LOWESS curves and r annotations are shown
