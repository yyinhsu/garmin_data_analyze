## Context

We have 601 days of Garmin health data (2024-07 to 2026-02) in local SQLite databases. Sleep quality skews negative: 26% POOR, 55% FAIR. The goal is to identify which measurable factors correlate with sleep deprivation using statistical analysis and visualizations.

Available data for correlation:
- **Sleep**: duration, deep/light/REM/awake times, sleep score, qualifier, avg stress/SpO2/RR during sleep (garmin.db → `sleep`)
- **Daily metrics**: steps, calories, floors, distance, stress avg, resting HR, body battery, SpO2 (garmin.db → `daily_summary`)
- **Resting HR**: daily resting heart rate (garmin.db → `resting_hr`)
- **Stress**: per-minute stress readings (garmin.db → `stress`)
- **Activities**: sport type, duration, intensity, HR zones, training load/effect, time of day (garmin_activities.db → `activities`)
- **Monitoring HR**: minute-level heart rate (garmin_monitoring.db → `monitoring_hr`)

## Goals / Non-Goals

**Goals:**
- Identify statistically significant correlations between sleep quality and daytime/evening metrics
- Produce clear visualizations (time series, heatmaps, distributions, scatter plots)
- Analyze temporal patterns (day-of-week, exercise timing relative to bedtime)
- Create reusable data loading utilities for future analysis topics
- All analysis runs locally (方案A)

**Non-Goals:**
- Causal inference or medical-grade conclusions (correlation only)
- Real-time monitoring or alerts
- Web app or conversational interface (future phases)
- Predictive modeling / ML (may come later)

## Decisions

### Decision 1: Jupyter Notebook as primary analysis tool

**Choice**: Single notebook `analysis/sleep_analysis.ipynb` with utility module `analysis/garmin_utils.py`

**Rationale**:
- Interactive exploration with inline charts
- Easy to iterate and share findings
- Natural fit for EDA (exploratory data analysis)

**Alternative considered**: Streamlit app
- Better for presentation, but premature — need to discover insights first before building a dashboard

### Decision 2: Project structure

**Choice**:
```
analysis/
  garmin_utils.py       # Reusable data loading + helpers
  sleep_analysis.ipynb  # Main analysis notebook
```

**Rationale**:
- Separating utils from notebook keeps code reusable for future analysis topics
- Flat structure sufficient for now; add subdirectories when more topics are added

### Decision 3: Analysis approach — same-day and previous-day correlation

**Choice**: For each night's sleep, correlate with:
1. **Same-day factors** (the day before that night's sleep): steps, exercise, stress, calories, body battery
2. **Previous-night sleep** → next-day metrics (carry-over effects)
3. **Temporal patterns**: day-of-week, weekend vs weekday, seasonal

**Rationale**:
- Sleep is influenced by what happened during the day (exercise, stress)
- Exercise timing matters: late evening exercise may hurt sleep differently than morning
- Day-of-week captures lifestyle patterns (weekend late nights, Monday stress)

### Decision 4: Statistical methods

**Choice**: Pearson/Spearman correlation, group comparison (t-test/Mann-Whitney), and visual analysis

**Rationale**:
- Correlation coefficients give quick overview of relationships
- Group comparison (e.g., sleep on exercise days vs rest days) is more interpretable
- Visual patterns often reveal non-linear relationships that correlation misses
- Avoid overcomplicating with regression at this stage

### Decision 5: Sleep deprivation definition

**Choice**: Define "sleep deprived" as sleep score < 60 OR qualifier in (POOR) OR total_sleep < 6 hours

**Rationale**:
- Garmin's own POOR qualifier captures their assessment
- Score < 60 adds objective threshold
- < 6 hours is a widely accepted clinical threshold for insufficient sleep
- Using multiple criteria avoids missing edge cases

### Decision 6: Activity timing bucketing

**Choice**: Categorize activities by time relative to sleep:
- Morning (before 12:00)
- Afternoon (12:00–17:00)
- Evening (17:00–20:00)
- Late night (after 20:00)

**Rationale**: Late exercise is commonly cited as a sleep disruptor; bucketing allows group comparison

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Confounding variables (e.g., weekend = both late exercise AND late bedtime) | Note confounds explicitly; don't claim causation |
| Missing data (null scores, gaps in monitoring) | Filter NaN rows per analysis; report data completeness |
| Small sample for some activity types (e.g., only 2 swimming sessions) | Group rare sports together; set minimum sample size threshold (n≥10) |
| Overfitting visual patterns to noise | Use statistical significance tests (p < 0.05) alongside visual inspection |
