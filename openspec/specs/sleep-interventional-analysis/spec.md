## ADDED Requirements

### Requirement: Deep analysis notebook

`analysis/sleep_deep_analysis.ipynb` SHALL implement a structured interventional sleep analysis using the feature DataFrame built by `sleep_feature_builder.py`.

#### Scenario: Notebook loads feature DataFrame

- **WHEN** the notebook is run from top to bottom
- **THEN** Section 1 SHALL call `build_sleep_features()` and display shape, date range, and a completeness report
- **AND** the nighttime activity filter SHALL already be applied inside the feature builder (not re-applied in the notebook)

---

### Requirement: Feature completeness section

The notebook SHALL report data completeness before any analysis.

#### Scenario: Completeness report shown

- **WHEN** Section 1 runs
- **THEN** it SHALL display a table showing each feature's non-null count, percentage, and a flag for partial-coverage features (e.g., sleep_events columns)

---

### Requirement: Dual-target correlation analysis

The notebook SHALL compute Spearman correlations of all features against both `score` and `bb_charged`.

#### Scenario: Full correlation tables produced

- **WHEN** Section 2 runs
- **THEN** it SHALL produce a sorted correlation table for target = `score` and a separate table for target = `bb_charged`
- **AND** each table SHALL show feature name, Spearman r, p-value, and significance flag (p < 0.05 after Bonferroni correction)
- **AND** a side-by-side comparison heatmap of top-N features SHALL be shown for both targets

---

### Requirement: Interventional analysis section

The notebook SHALL isolate controllable features and rank them by effect size between good and poor sleep nights.

#### Scenario: Controllable feature ranking produced

- **WHEN** Section 3 runs
- **THEN** it SHALL filter to features tagged HIGH or MEDIUM controllability (from the `CONTROLLABILITY` dict in `sleep_feature_builder.py`)
- **AND** for each controllable feature, it SHALL compute Mann-Whitney U effect size (rank-biserial correlation) between deprived vs adequate sleep nights
- **AND** features SHALL be ranked by |effect size| descending
- **AND** the top 10 controllable features SHALL be shown with group means (deprived vs adequate)

---

### Requirement: Pre-sleep window comparison

The notebook SHALL show how pre-sleep physiological metrics vary across the 1/2/4/6/8h windows.

#### Scenario: Window effect comparison plotted

- **WHEN** Section 4 runs
- **THEN** it SHALL plot correlation strength of `pre_sleep_hr_avg_Nh` vs sleep score for each N on a single chart
- **AND** equivalent plots SHALL be shown for `pre_sleep_stress_avg_Nh` and `pre_sleep_rr_avg_Nh`
- **AND** the chart SHALL make it visually clear which window has the strongest predictive signal

---

### Requirement: Streak and lag feature analysis

The notebook SHALL analyse how accumulated sleep debt and consecutive streaks relate to sleep quality.

#### Scenario: Streak analysis shown

- **WHEN** Section 5 runs
- **THEN** it SHALL plot sleep score vs `consecutive_poor_sleep` (scatter + smoothed line)
- **AND** it SHALL show how `rolling_7d_sleep_avg` correlates with next-night score
- **AND** it SHALL compare sleep score on days with `consecutive_exercise_days` = 1, 2, 3, 4+ nights in a row
